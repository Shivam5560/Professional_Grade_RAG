"""Database access helpers for AuraSQL."""

from __future__ import annotations

import logging
from typing import Any, List, Tuple

import asyncpg
import aiomysql
import oracledb
import pandas as pd
import numpy as np
import sqlparse
import re

logger = logging.getLogger(__name__)
def _validate_schema_name(schema_name: str | None, db_type: str) -> None:
    if db_type != "postgresql":
        return
    if not schema_name:
        raise ValueError("PostgreSQL schema_name is required")
    if not re.match(r"^[A-Za-z0-9_]+$", schema_name):
        raise ValueError("Schema name must be alphanumeric with underscores")



def _normalize_df(df: pd.DataFrame) -> Tuple[List[str], List[dict]]:
    if df.empty:
        return [], []
    df.replace({np.nan: None, np.inf: None, -np.inf: None}, inplace=True)
    return list(df.columns), df.to_dict(orient="records")


def _split_statements(sql: str) -> List[str]:
    return [stmt.strip() for stmt in sqlparse.split(sql) if stmt.strip()]


async def _connect_postgres(config: dict[str, Any]):
    ssl_mode = "require" if config.get("ssl_required", True) else None
    return await asyncpg.connect(
        host=config["host"],
        port=config["port"],
        user=config["username"],
        password=config["password"],
        database=config["database"],
        ssl=ssl_mode,
    )


async def _connect_mysql(config: dict[str, Any]):
    return await aiomysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["username"],
        password=config["password"],
        db=config["database"],
    )


async def _connect_oracle(config: dict[str, Any]):
    dsn = f"{config['username']}/{config['password']}@{config['host']}:{config['port']}/{config['database']}"
    return await oracledb.connect_async(dsn=dsn)


async def list_tables(config: dict[str, Any]) -> List[str]:
    db_type = config["db_type"].lower()
    schema = config.get("schema_name")

    _validate_schema_name(schema, db_type)

    if db_type == "postgresql":
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 AND table_catalog = $2;"
        params = (schema, config["database"])
    elif db_type == "mysql":
        query = "SHOW TABLES;"
        params = None
    elif db_type == "oracle":
        query = "SELECT table_name FROM all_tables WHERE owner = :1;"
        params = (config["database"].upper(),)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    df = await execute_query_df(config, query, params)
    if df.empty:
        return []
    return df.iloc[:, 0].tolist()


async def get_table_schema(config: dict[str, Any], table_name: str) -> dict[str, list[dict[str, Any]]]:
    db_type = config["db_type"].lower()
    schema = config.get("schema_name")

    _validate_schema_name(schema, db_type)

    if db_type == "postgresql":
        query = """ SELECT
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            tc.constraint_type,
            c.column_default
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
            ON c.table_name = kcu.table_name
            AND c.column_name = kcu.column_name
            AND c.table_schema = kcu.table_schema
        LEFT JOIN information_schema.table_constraints tc
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE c.table_name = $1 AND c.table_schema = $2
        ORDER BY c.ordinal_position;"""
        params = (table_name, schema)
    elif db_type == "mysql":
        query = """SELECT
            COLUMN_NAME,
            COLUMN_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            EXTRA
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = %s;"""
        params = (table_name, config["database"])
    elif db_type == "oracle":
        query = """SELECT
            column_name,
            data_type,
            nullable,
            data_default
        FROM all_tab_columns
        WHERE table_name = :1 AND owner = :2"""
        params = (table_name.upper(), config["database"].upper())
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    df = await execute_query_df(config, query, params)
    df.replace({np.nan: None, np.inf: None, -np.inf: None}, inplace=True)
    return {table_name: df.to_dict(orient="records")}


async def execute_query_df(config: dict[str, Any], query: str, params: Any = None) -> pd.DataFrame:
    db_type = config["db_type"].lower()
    if db_type == "postgresql":
        _validate_schema_name(config.get("schema_name"), db_type)

    if db_type == "postgresql":
        conn = await _connect_postgres(config)
        try:
            statement = await conn.prepare(query)
            columns = [attr.name for attr in statement.get_attributes()]
            results = await statement.fetch(*(params or ()))
            return pd.DataFrame(results, columns=columns)
        finally:
            await conn.close()

    if db_type == "mysql":
        conn = await _connect_mysql(config)
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params or ())
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                results = await cursor.fetchall()
                return pd.DataFrame(results, columns=columns)
        finally:
            conn.close()

    if db_type == "oracle":
        conn = await _connect_oracle(config)
        try:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params or ())
                columns = [desc[0] for desc in cursor.description]
                results = await cursor.fetchall()
                return pd.DataFrame(results, columns=columns)
        finally:
            await conn.close()

    raise ValueError(f"Unsupported database type: {db_type}")


async def execute_sql(config: dict[str, Any], sql: str) -> tuple[list[str], list[dict[str, Any]]]:
    statements = _split_statements(sql)
    if not statements:
        return [], []

    db_type = config["db_type"].lower()

    if db_type == "postgresql":
        conn = await _connect_postgres(config)
        try:
            schema = config.get("schema_name")
            _validate_schema_name(schema, db_type)
            if schema:
                await conn.execute(f"SET search_path TO \"{schema}\";")
            last_columns: list[str] = []
            last_rows: list[dict[str, Any]] = []
            for stmt in statements:
                try:
                    statement = await conn.prepare(stmt)
                    columns = [attr.name for attr in statement.get_attributes()]
                    rows = await statement.fetch()
                    last_columns, last_rows = _normalize_df(pd.DataFrame(rows, columns=columns))
                except Exception:
                    await conn.execute(stmt)
                    last_columns, last_rows = [], []
            return last_columns, last_rows
        finally:
            await conn.close()

    if db_type == "mysql":
        conn = await _connect_mysql(config)
        try:
            last_columns: list[str] = []
            last_rows: list[dict[str, Any]] = []
            async with conn.cursor() as cursor:
                for stmt in statements:
                    await cursor.execute(stmt)
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        results = await cursor.fetchall()
                        last_columns, last_rows = _normalize_df(pd.DataFrame(results, columns=columns))
                    else:
                        last_columns, last_rows = [], []
                await conn.commit()
            return last_columns, last_rows
        finally:
            conn.close()

    if db_type == "oracle":
        conn = await _connect_oracle(config)
        try:
            last_columns: list[str] = []
            last_rows: list[dict[str, Any]] = []
            async with conn.cursor() as cursor:
                for stmt in statements:
                    await cursor.execute(stmt)
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        results = await cursor.fetchall()
                        last_columns, last_rows = _normalize_df(pd.DataFrame(results, columns=columns))
                    else:
                        last_columns, last_rows = [], []
                await conn.commit()
            return last_columns, last_rows
        finally:
            await conn.close()

    raise ValueError(f"Unsupported database type: {db_type}")
