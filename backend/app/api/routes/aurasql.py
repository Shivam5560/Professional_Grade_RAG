"""AuraSQL endpoints for schema contexts and SQL generation."""

from __future__ import annotations

import json
import logging
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from llama_index.core.schema import TextNode
from sqlglot import exp, parse_one, transpile
from sqlglot.errors import ParseError
from app.api.deps import get_current_user
from app.config import settings
from app.db.database import get_db
from app.db.models import AuraSqlConnection, AuraSqlConnectionSecret, AuraSqlContext, AuraSqlQueryHistory, AuraSqlChatSession, User
from app.models.aurasql_schemas import (
    AuraSqlConnectionCreate,
    AuraSqlConnectionUpdate,
    AuraSqlConnectionResponse,
    AuraSqlConnectionListResponse,
    AuraSqlContextCreate,
    AuraSqlContextUpdate,
    AuraSqlContextResponse,
    AuraSqlContextDetailResponse,
    AuraSqlContextListResponse,
    AuraSqlRecommendationsRequest,
    AuraSqlRecommendationsResponse,
    AuraSqlQueryRequest,
    AuraSqlQueryResponse,
    AuraSqlExecuteRequest,
    AuraSqlExecuteResponse,
    AuraSqlLogResponse,
    AuraSqlSessionResponse,
)
from app.services.aurasql_db import list_tables, get_table_schema, execute_sql
from app.services.aurasql_vector_store import get_aurasql_vector_store
from app.services.groq_service import get_groq_service
from app.utils.aurasql_prompts import system_prompt, recommendations_prompt
from app.utils.crypto import encrypt_secret, decrypt_secret
def _validate_schema_for_connection(payload) -> None:
    if payload.db_type == "postgresql" and not payload.schema_name:
        raise HTTPException(status_code=400, detail="PostgreSQL schema_name is required")


router = APIRouter(prefix="/aurasql", tags=["AuraSQL"])


def _connection_to_config(connection: AuraSqlConnection, password: str) -> dict:
    return {
        "db_type": connection.db_type,
        "host": connection.host,
        "port": connection.port,
        "username": connection.username,
        "password": password,
        "database": connection.database,
        "schema_name": connection.schema_name,
        "ssl_required": connection.ssl_required,
    }


def _parse_json_payload(payload: str) -> dict:
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def _parse_toon_payload(payload: str) -> dict:
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?|```$", "", cleaned, flags=re.MULTILINE).strip()

    list_keys = {"source_tables", "recommendations"}
    scalar_buffers: dict[str, list[str]] = {"sql": [], "explanation": []}
    list_buffers: dict[str, list[str]] = {"source_tables": [], "recommendations": []}
    current_key: str | None = None

    for raw_line in cleaned.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        match = re.match(r"^(sql|explanation|source_tables|recommendations)(\[[^\]]*\])?\s*:\s*(.*)$", stripped, flags=re.IGNORECASE)
        if match:
            key = match.group(1).lower()
            rest = match.group(3).strip()
            current_key = key
            if key in list_keys:
                if rest:
                    if key == "source_tables":
                        list_buffers[key].extend([value.strip() for value in rest.split(",") if value.strip()])
                    else:
                        list_buffers[key].append(rest)
            else:
                scalar_buffers[key] = []
                if rest:
                    scalar_buffers[key].append(rest)
            continue

        if not current_key:
            continue

        if current_key in list_keys:
            value = stripped
            if value.startswith("-"):
                value = value[1:].strip()
            if not value:
                continue
            if current_key == "source_tables":
                list_buffers[current_key].extend([val.strip() for val in value.split(",") if val.strip()])
            else:
                list_buffers[current_key].append(value)
        else:
            scalar_buffers[current_key].append(stripped)

    result: dict[str, object] = {}
    for key, buffer in scalar_buffers.items():
        if buffer:
            result[key] = "\n".join(buffer).strip()
    for key, items in list_buffers.items():
        if items:
            result[key] = items
    return result


def _parse_structured_payload(payload: str) -> dict:
    parsed = _parse_json_payload(payload)
    if parsed:
        return parsed
    return _parse_toon_payload(payload)


def _extract_recommendations_fallback(payload: str) -> list[str]:
    cleaned = payload.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?|```$", "", cleaned, flags=re.MULTILINE).strip()
    lines = []
    for raw_line in cleaned.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        stripped = re.sub(r"^[-*\d]+[.)]?\s*", "", stripped)
        if stripped:
            lines.append(stripped)
    return lines


def _fallback_recommendations_from_tables(table_names: list[str]) -> list[str]:
    templates = [
        "Show recent rows from {table}.",
        "How many records are in {table}?",
        "What are the top 10 entries in {table} by date?",
        "Summarize key metrics for {table}.",
    ]
    recommendations: list[str] = []
    for table in table_names:
        for template in templates:
            recommendations.append(template.format(table=table))
            if len(recommendations) >= 12:
                return recommendations
    return recommendations


def _extract_tables_from_sql(sql: str) -> list[str]:
    matches = re.findall(r"\bfrom\s+([\w\.\"`]+)|\bjoin\s+([\w\.\"`]+)", sql, flags=re.IGNORECASE)
    tables: list[str] = []
    for from_table, join_table in matches:
        raw = from_table or join_table
        raw = raw.strip("`\"")
        if "." in raw:
            raw = raw.split(".")[-1]
        if raw:
            tables.append(raw)
    return tables


_DB_TO_SQLGLOT_DIALECT = {
    "postgresql": "postgres",
    "mysql": "mysql",
    "oracle": "oracle",
}

_SQLGLOT_DIALECT_ALIASES = {
    "postgresql": "postgres",
}


def _normalize_identifier(identifier: str) -> str:
    return identifier.strip("`\"").lower()


def _build_retrieved_schema_sets(schema_snapshot: dict) -> tuple[set[str], set[str], set[str]]:
    tables: set[str] = set()
    qualified_columns: set[str] = set()
    column_names: set[str] = set()

    for table_name, columns in (schema_snapshot or {}).items():
        table = _normalize_identifier(str(table_name))
        tables.add(table)
        for column in columns or []:
            raw_column = (
                column.get("column_name")
                or column.get("COLUMN_NAME")
                or column.get("name")
            )
            if not raw_column:
                continue
            col = _normalize_identifier(str(raw_column))
            qualified_columns.add(f"{table}.{col}")
            column_names.add(col)
    return tables, qualified_columns, column_names


def _collect_table_aliases(ast: exp.Expression) -> dict[str, str]:
    alias_to_table: dict[str, str] = {}
    for table_expr in ast.find_all(exp.Table):
        table_name = _normalize_identifier(table_expr.name)
        if not table_name:
            continue
        alias_name = _normalize_identifier(table_expr.alias) if table_expr.alias else ""
        if alias_name:
            alias_to_table[alias_name] = table_name
    return alias_to_table


def _collect_cte_names(ast: exp.Expression) -> set[str]:
    cte_names: set[str] = set()
    for cte_expr in ast.find_all(exp.CTE):
        alias_name = _normalize_identifier(cte_expr.alias_or_name or "")
        if alias_name:
            cte_names.add(alias_name)
    return cte_names


def _collect_projection_aliases(ast: exp.Expression) -> set[str]:
    projection_aliases: set[str] = set()
    for alias_expr in ast.find_all(exp.Alias):
        alias_name = _normalize_identifier(alias_expr.alias or "")
        if alias_name:
            projection_aliases.add(alias_name)
    return projection_aliases


def _validate_sql_with_schema(
    sql: str,
    db_type: str,
    schema_snapshot: dict,
) -> tuple[list[str], list[str], list[str]]:
    dialect = _DB_TO_SQLGLOT_DIALECT.get((db_type or "").lower(), "postgres")
    try:
        ast = parse_one(sql, dialect=dialect)
    except ParseError as exc:
        details = []
        for err in exc.errors:
            message = err.get("description") or str(err)
            details.append(message)
        return details or [str(exc)], [], []

    retrieved_tables, retrieved_qualified_columns, retrieved_column_names = _build_retrieved_schema_sets(schema_snapshot)
    alias_to_table = _collect_table_aliases(ast)
    cte_names = _collect_cte_names(ast)
    projection_aliases = _collect_projection_aliases(ast)

    used_tables: set[str] = set()
    for table_expr in ast.find_all(exp.Table):
        table_name = _normalize_identifier(table_expr.name)
        if table_name:
            used_tables.add(table_name)

    hallucinated_tables = sorted(used_tables - retrieved_tables - cte_names)

    hallucinated_columns: set[str] = set()
    for col_expr in ast.find_all(exp.Column):
        col_name = _normalize_identifier(col_expr.name or "")
        if not col_name:
            continue
        table_name = _normalize_identifier(col_expr.table) if col_expr.table else ""
        if table_name:
            resolved_table_name = alias_to_table.get(table_name, table_name)
            if resolved_table_name in cte_names:
                continue
            qualified = f"{resolved_table_name}.{col_name}"
            if qualified not in retrieved_qualified_columns:
                hallucinated_columns.add(qualified)
        elif col_name not in retrieved_column_names and col_name not in projection_aliases:
            hallucinated_columns.add(col_name)

    return [], hallucinated_tables, sorted(hallucinated_columns)


def _render_sql_validation_message(
    syntax_errors: list[str],
    hallucinated_tables: list[str],
    hallucinated_columns: list[str],
) -> str:
    messages: list[str] = []
    if syntax_errors:
        messages.append(f"SQL syntax validation failed: {syntax_errors[0]}")
    if hallucinated_tables:
        messages.append(f"Referenced tables not found in retrieved schema: {', '.join(hallucinated_tables)}.")
    if hallucinated_columns:
        messages.append(f"Referenced columns not found in retrieved schema: {', '.join(hallucinated_columns)}.")
    return " ".join(messages).strip()


def _transpile_sql_for_output(sql: str, source_db_type: str, output_dialect: str | None) -> str:
    if not output_dialect:
        return sql
    source_dialect = _DB_TO_SQLGLOT_DIALECT.get((source_db_type or "").lower(), "postgres")
    target_dialect = _SQLGLOT_DIALECT_ALIASES.get(output_dialect.lower(), output_dialect.lower())
    transpiled = transpile(sql, read=source_dialect, write=target_dialect)
    return transpiled[0] if transpiled else sql


def _calculate_sql_confidence(
    sql: str,
    explanation: str,
    source_tables: list[str],
    context_tables: list[str],
) -> tuple[float, str]:
    if not sql:
        return 0.0, "low"

    score = 60.0
    context_set = {table.lower() for table in context_tables}
    source_set = {table.lower() for table in source_tables}
    if source_set:
        match_ratio = len(source_set & context_set) / max(len(source_set), 1)
        score += match_ratio * 30.0
    else:
        score -= 10.0

    if explanation:
        score += 5.0

    if "select *" in sql.lower():
        score -= 5.0

    if " limit " not in sql.lower() and "count(" not in sql.lower():
        score -= 5.0

    score = max(0.0, min(100.0, score))
    if score >= 80.0:
        level = "high"
    elif score >= 60.0:
        level = "medium"
    else:
        level = "low"
    return score, level


def _extract_sql_fallback(payload: str) -> str:
    if "```" in payload:
        fenced = re.search(r"```sql\s*(.*?)```", payload, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1).strip()
    inline = re.search(r"(?i)sql\s*[:\n]+(.+)", payload, flags=re.DOTALL)
    if inline:
        return inline.group(1).strip()
    return ""


@router.post("/connections", response_model=AuraSqlConnectionResponse)
def create_connection(
    payload: AuraSqlConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_schema_for_connection(payload)
    connection_id = str(uuid.uuid4())
    connection = AuraSqlConnection(
        id=connection_id,
        user_id=current_user.id,
        name=payload.name,
        db_type=payload.db_type,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        database=payload.database,
        schema_name=payload.schema_name,
        ssl_required=payload.ssl_required,
    )
    db.add(connection)

    secret = AuraSqlConnectionSecret(
        id=str(uuid.uuid4()),
        connection_id=connection_id,
        encrypted_password=encrypt_secret(payload.password),
    )
    db.add(secret)
    db.commit()

    return AuraSqlConnectionResponse(
        id=connection.id,
        name=connection.name,
        db_type=connection.db_type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        database=connection.database,
        schema_name=connection.schema_name,
        ssl_required=connection.ssl_required,
    )


@router.get("/connections", response_model=AuraSqlConnectionListResponse)
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connections = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.user_id == current_user.id)
        .order_by(AuraSqlConnection.created_at.desc())
        .all()
    )
    @router.get("/connections/{connection_id}", response_model=AuraSqlConnectionResponse)
    def get_connection(
        connection_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        connection = (
            db.query(AuraSqlConnection)
            .filter(AuraSqlConnection.id == connection_id, AuraSqlConnection.user_id == current_user.id)
            .first()
        )
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        return AuraSqlConnectionResponse(
            id=connection.id,
            name=connection.name,
            db_type=connection.db_type,
            host=connection.host,
            port=connection.port,
            username=connection.username,
            database=connection.database,
            schema_name=connection.schema_name,
            ssl_required=connection.ssl_required,
        )


    @router.patch("/connections/{connection_id}", response_model=AuraSqlConnectionResponse)
    def update_connection(
        connection_id: str,
        payload: AuraSqlConnectionUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        connection = (
            db.query(AuraSqlConnection)
            .filter(AuraSqlConnection.id == connection_id, AuraSqlConnection.user_id == current_user.id)
            .first()
        )
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        update_data = payload.model_dump(exclude_unset=True)
        if update_data.get("db_type") == "postgresql" and not update_data.get("schema_name") and not connection.schema_name:
            raise HTTPException(status_code=400, detail="PostgreSQL schema_name is required")
        password = update_data.pop("password", None)
        for key, value in update_data.items():
            setattr(connection, key, value)

        if password:
            if not connection.secret:
                connection.secret = AuraSqlConnectionSecret(
                    id=str(uuid.uuid4()),
                    connection_id=connection.id,
                    encrypted_password=encrypt_secret(password),
                )
            else:
                connection.secret.encrypted_password = encrypt_secret(password)

        db.add(connection)
        db.commit()

        return AuraSqlConnectionResponse(
            id=connection.id,
            name=connection.name,
            db_type=connection.db_type,
            host=connection.host,
            port=connection.port,
            username=connection.username,
            database=connection.database,
            schema_name=connection.schema_name,
            ssl_required=connection.ssl_required,
        )

    return AuraSqlConnectionListResponse(
        connections=[
            AuraSqlConnectionResponse(
                id=conn.id,
                name=conn.name,
                db_type=conn.db_type,
                host=conn.host,
                port=conn.port,
                username=conn.username,
                database=conn.database,
                schema_name=conn.schema_name,
                ssl_required=conn.ssl_required,
            )
            for conn in connections
        ]
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == connection_id, AuraSqlConnection.user_id == current_user.id)
        .first()
    )
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    db.delete(connection)
    db.commit()


@router.get("/connections/{connection_id}/tables")
async def get_tables(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == connection_id, AuraSqlConnection.user_id == current_user.id)
        .first()
    )
    if not connection or not connection.secret:
        raise HTTPException(status_code=404, detail="Connection not found")

    config = _connection_to_config(connection, decrypt_secret(connection.secret.encrypted_password))
    tables = await list_tables(config)
    return {"tables": tables}


@router.post("/contexts", response_model=AuraSqlContextDetailResponse)
async def create_context(
    payload: AuraSqlContextCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == payload.connection_id, AuraSqlConnection.user_id == current_user.id)
        .first()
    )
    if not connection or not connection.secret:
        raise HTTPException(status_code=404, detail="Connection not found")

    config = _connection_to_config(connection, decrypt_secret(connection.secret.encrypted_password))

    schema_snapshot: dict = {}
    for table in payload.table_names:
        schema_snapshot.update(await get_table_schema(config, table))

    context_id = str(uuid.uuid4())
    vector_context_id = f"ctx_{context_id}"

    nodes = []
    for table_name, schema_rows in schema_snapshot.items():
        node_text = f"Table `{table_name}`: {json.dumps(schema_rows)}"
        nodes.append(
            TextNode(
                text=node_text,
                metadata={
                    "context_id": vector_context_id,
                    "user_id": str(current_user.id),
                    "connection_id": connection.id,
                    "table_name": table_name,
                },
            )
        )

    vector_store = get_aurasql_vector_store()
    vector_store.add_schema_nodes(nodes)

    context = AuraSqlContext(
        id=context_id,
        user_id=current_user.id,
        connection_id=connection.id,
        name=payload.name,
        table_names=payload.table_names,
        schema_snapshot=schema_snapshot,
        vector_context_id=vector_context_id,
        is_temporary=payload.is_temporary,
    )
    db.add(context)
    db.commit()

    return AuraSqlContextDetailResponse(
        id=context.id,
        connection_id=context.connection_id,
        name=context.name,
        table_names=context.table_names,
        is_temporary=context.is_temporary,
        schema_snapshot=context.schema_snapshot,
    )


@router.get("/contexts", response_model=AuraSqlContextListResponse)
def list_contexts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contexts = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.user_id == current_user.id, AuraSqlContext.is_temporary.is_(False))
        .order_by(AuraSqlContext.created_at.desc())
        .all()
    )
    return AuraSqlContextListResponse(
        contexts=[
            AuraSqlContextResponse(
                id=context.id,
                connection_id=context.connection_id,
                name=context.name,
                table_names=context.table_names,
                is_temporary=context.is_temporary,
            )
            for context in contexts
        ]
    )


@router.get("/contexts/{context_id}", response_model=AuraSqlContextDetailResponse)
def get_context(
    context_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.id == context_id, AuraSqlContext.user_id == current_user.id)
        .first()
    )
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return AuraSqlContextDetailResponse(
        id=context.id,
        connection_id=context.connection_id,
        name=context.name,
        table_names=context.table_names,
        is_temporary=context.is_temporary,
        schema_snapshot=context.schema_snapshot,
    )


@router.patch("/contexts/{context_id}", response_model=AuraSqlContextDetailResponse)
async def update_context(
    context_id: str,
    payload: AuraSqlContextUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.id == context_id, AuraSqlContext.user_id == current_user.id)
        .first()
    )
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == context.connection_id, AuraSqlConnection.user_id == current_user.id)
        .first()
    )
    if not connection or not connection.secret:
        raise HTTPException(status_code=404, detail="Connection not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data:
        context.name = update_data["name"] or context.name
    if "is_temporary" in update_data:
        context.is_temporary = bool(update_data["is_temporary"])

    if "table_names" in update_data and update_data["table_names"]:
        config = _connection_to_config(connection, decrypt_secret(connection.secret.encrypted_password))
        schema_snapshot: dict = {}
        for table in update_data["table_names"]:
            schema_snapshot.update(await get_table_schema(config, table))

        context.table_names = update_data["table_names"]
        context.schema_snapshot = schema_snapshot
        context.vector_context_id = f"ctx_{uuid.uuid4()}"

        nodes = []
        for table_name, schema_rows in schema_snapshot.items():
            node_text = f"Table `{table_name}`: {json.dumps(schema_rows)}"
            nodes.append(
                TextNode(
                    text=node_text,
                    metadata={
                        "context_id": context.vector_context_id,
                        "user_id": str(current_user.id),
                        "connection_id": connection.id,
                        "table_name": table_name,
                    },
                )
            )

        vector_store = get_aurasql_vector_store()
        vector_store.add_schema_nodes(nodes)

    db.add(context)
    db.commit()

    return AuraSqlContextDetailResponse(
        id=context.id,
        connection_id=context.connection_id,
        name=context.name,
        table_names=context.table_names,
        is_temporary=context.is_temporary,
        schema_snapshot=context.schema_snapshot,
    )


@router.delete("/contexts/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_context(
    context_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.id == context_id, AuraSqlContext.user_id == current_user.id)
        .first()
    )
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    db.delete(context)
    db.commit()


@router.post("/contexts/{context_id}/refresh", response_model=AuraSqlContextDetailResponse)
async def refresh_context(
    context_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.id == context_id, AuraSqlContext.user_id == current_user.id)
        .first()
    )
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == context.connection_id, AuraSqlConnection.user_id == current_user.id)
        .first()
    )
    if not connection or not connection.secret:
        raise HTTPException(status_code=404, detail="Connection not found")

    config = _connection_to_config(connection, decrypt_secret(connection.secret.encrypted_password))
    schema_snapshot: dict = {}
    for table in context.table_names:
        schema_snapshot.update(await get_table_schema(config, table))

    context.schema_snapshot = schema_snapshot
    db.add(context)

    nodes = []
    for table_name, schema_rows in schema_snapshot.items():
        node_text = f"Table `{table_name}`: {json.dumps(schema_rows)}"
        nodes.append(
            TextNode(
                text=node_text,
                metadata={
                    "context_id": context.vector_context_id,
                    "user_id": str(current_user.id),
                    "connection_id": connection.id,
                    "table_name": table_name,
                },
            )
        )

    vector_store = get_aurasql_vector_store()
    vector_store.add_schema_nodes(nodes)

    db.commit()

    return AuraSqlContextDetailResponse(
        id=context.id,
        connection_id=context.connection_id,
        name=context.name,
        table_names=context.table_names,
        schema_snapshot=context.schema_snapshot,
    )


@router.post("/recommendations", response_model=AuraSqlRecommendationsResponse)
async def get_recommendations(
    payload: AuraSqlRecommendationsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.id == payload.context_id, AuraSqlContext.user_id == current_user.id)
        .first()
    )
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    groq_service = get_groq_service()
    from llama_index.core import Settings
    Settings.llm = groq_service.get_aurasql_llm()

    vector_store = get_aurasql_vector_store()
    query_engine = vector_store.get_query_engine(context.vector_context_id)
    result = await query_engine.aquery(recommendations_prompt)

    parsed = _parse_structured_payload(result.response)
    recommendations = parsed.get("recommendations", []) if parsed else []
    if not recommendations:
        recommendations = _extract_recommendations_fallback(result.response)
    if not recommendations:
        recommendations = _fallback_recommendations_from_tables(context.table_names)
    if not recommendations:
        logging.warning("AuraSQL recommendations JSON parse failed")
    return AuraSqlRecommendationsResponse(recommendations=recommendations)


@router.post("/query", response_model=AuraSqlQueryResponse)
async def generate_query(
    payload: AuraSqlQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    context = (
        db.query(AuraSqlContext)
        .filter(AuraSqlContext.id == payload.context_id, AuraSqlContext.user_id == current_user.id)
        .first()
    )
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == context.connection_id)
        .first()
    )

    groq_service = get_groq_service()
    from llama_index.core import Settings
    Settings.llm = groq_service.get_aurasql_llm()

    prompt = f"{system_prompt}\nUser Query:\n{payload.query}\nDB Type: {connection.db_type}"

    session_id = payload.session_id
    session = None
    if session_id:
        session = (
            db.query(AuraSqlChatSession)
            .filter(AuraSqlChatSession.id == session_id, AuraSqlChatSession.user_id == current_user.id)
            .first()
        )
    if not session:
        session_id = str(uuid.uuid4())
        session = AuraSqlChatSession(
            id=session_id,
            user_id=current_user.id,
            title=payload.query[:120],
            connection_id=context.connection_id,
            context_id=context.id,
        )
    else:
        session.context_id = context.id
        session.connection_id = context.connection_id
    db.add(session)

    vector_store = get_aurasql_vector_store()
    query_engine = vector_store.get_query_engine(context.vector_context_id)
    result = await query_engine.aquery(prompt)

    parsed = _parse_structured_payload(result.response)
    sql = parsed.get("sql", "")
    explanation = parsed.get("explanation", "")
    source_tables = parsed.get("source_tables", [])
    if not sql:
        sql = _extract_sql_fallback(result.response)
        if sql and not explanation:
            explanation = "Generated from model output."
    if not sql:
        logging.warning("AuraSQL query JSON parse failed")
        explanation = "Unable to parse SQL from model response."
        return AuraSqlQueryResponse(
            sql="",
            explanation=explanation,
            source_tables=[],
            session_id=session_id,
            confidence_score=0.0,
            confidence_level="low",
            validation_errors=["Unable to parse SQL from model response."],
        )

    syntax_errors, hallucinated_tables, hallucinated_columns = _validate_sql_with_schema(
        sql=sql,
        db_type=connection.db_type,
        schema_snapshot=context.schema_snapshot or {},
    )
    validation_errors = syntax_errors + hallucinated_tables + hallucinated_columns
    if syntax_errors or hallucinated_tables or hallucinated_columns:
        explanation = _render_sql_validation_message(
            syntax_errors=syntax_errors,
            hallucinated_tables=hallucinated_tables,
            hallucinated_columns=hallucinated_columns,
        ) or "SQL validation failed."
        return AuraSqlQueryResponse(
            sql="",
            explanation=explanation,
            source_tables=[],
            session_id=session_id,
            confidence_score=0.0,
            confidence_level="low",
            validation_errors=validation_errors,
        )

    try:
        sql = _transpile_sql_for_output(sql, connection.db_type, payload.output_dialect)
    except Exception as exc:
        logging.warning("AuraSQL output dialect transpile failed: %s", exc)

    confidence_score, confidence_level = _calculate_sql_confidence(
        sql,
        explanation,
        source_tables,
        context.table_names,
    )

    log_entry = AuraSqlQueryHistory(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        connection_id=context.connection_id,
        session_id=session_id,
        context_id=context.id,
        natural_language_query=payload.query,
        generated_sql=sql,
        source_tables=source_tables,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        status="generated",
    )
    db.add(log_entry)
    db.commit()

    return AuraSqlQueryResponse(
        sql=sql,
        explanation=explanation,
        source_tables=source_tables,
        session_id=session_id,
        confidence_score=confidence_score,
        confidence_level=confidence_level,
        validation_errors=[],
    )


@router.post("/execute", response_model=AuraSqlExecuteResponse)
async def execute_sql_query(
    payload: AuraSqlExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = (
        db.query(AuraSqlConnection)
        .filter(AuraSqlConnection.id == payload.connection_id, AuraSqlConnection.user_id == current_user.id)
        .first()
    )
    if not connection or not connection.secret:
        raise HTTPException(status_code=404, detail="Connection not found")

    config = _connection_to_config(connection, decrypt_secret(connection.secret.encrypted_password))

    session_id = payload.session_id
    try:
        columns, rows = await execute_sql(config, payload.sql)
        log_entry = AuraSqlQueryHistory(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            connection_id=connection.id,
            session_id=session_id,
            context_id=None,
            natural_language_query=None,
            generated_sql=payload.sql,
            status="executed",
        )
        db.add(log_entry)
        db.commit()
    except Exception as exc:
        log_entry = AuraSqlQueryHistory(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            connection_id=connection.id,
            session_id=session_id,
            context_id=None,
            natural_language_query=None,
            generated_sql=payload.sql,
            status="failed",
            error_message=str(exc),
        )
        db.add(log_entry)
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AuraSqlExecuteResponse(columns=columns, rows=rows)


@router.get("/history", response_model=list[AuraSqlLogResponse])
def list_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(AuraSqlQueryHistory)
        .filter(AuraSqlQueryHistory.user_id == current_user.id)
        .order_by(AuraSqlQueryHistory.created_at.desc())
        .all()
    )
    return [
        AuraSqlLogResponse(
            id=row.id,
            connection_id=row.connection_id,
            session_id=row.session_id,
            context_id=row.context_id,
            natural_language_query=row.natural_language_query,
            generated_sql=row.generated_sql,
            source_tables=row.source_tables,
            confidence_score=row.confidence_score,
            confidence_level=row.confidence_level,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else "",
            error_message=row.error_message,
        )
        for row in rows
    ]


@router.get("/history/sessions", response_model=list[AuraSqlSessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = (
        db.query(AuraSqlChatSession)
        .filter(AuraSqlChatSession.user_id == current_user.id)
        .order_by(AuraSqlChatSession.updated_at.desc().nullslast(), AuraSqlChatSession.created_at.desc())
        .all()
    )
    return [
        AuraSqlSessionResponse(
            id=session.id,
            title=session.title,
            connection_id=session.connection_id,
            context_id=session.context_id,
            created_at=session.created_at.isoformat() if session.created_at else "",
            updated_at=session.updated_at.isoformat() if session.updated_at else None,
        )
        for session in sessions
    ]


@router.get("/history/sessions/{session_id}", response_model=list[AuraSqlLogResponse])
def get_session_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(AuraSqlQueryHistory)
        .filter(
            AuraSqlQueryHistory.user_id == current_user.id,
            AuraSqlQueryHistory.session_id == session_id,
        )
        .order_by(AuraSqlQueryHistory.created_at.asc())
        .all()
    )
    return [
        AuraSqlLogResponse(
            id=row.id,
            connection_id=row.connection_id,
            session_id=row.session_id,
            context_id=row.context_id,
            natural_language_query=row.natural_language_query,
            generated_sql=row.generated_sql,
            source_tables=row.source_tables,
            confidence_score=row.confidence_score,
            confidence_level=row.confidence_level,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else "",
            error_message=row.error_message,
        )
        for row in rows
    ]
