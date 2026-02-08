"""AuraSQL endpoints for schema contexts and SQL generation."""

from __future__ import annotations

import json
import logging
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from llama_index.core.schema import TextNode
from app.api.deps import get_current_user
from app.config import settings
from app.db.database import get_db
from app.db.models import AuraSqlConnection, AuraSqlConnectionSecret, AuraSqlContext, AuraSqlQueryHistory, User
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
    if not parsed:
        logging.warning("AuraSQL recommendations JSON parse failed")
    return AuraSqlRecommendationsResponse(recommendations=parsed.get("recommendations", []))


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
        raise HTTPException(status_code=502, detail="Failed to parse SQL from model response")

    log_entry = AuraSqlQueryHistory(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        connection_id=context.connection_id,
        context_id=context.id,
        natural_language_query=payload.query,
        generated_sql=sql,
        status="generated",
    )
    db.add(log_entry)
    db.commit()

    return AuraSqlQueryResponse(sql=sql, explanation=explanation, source_tables=source_tables)


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

    try:
        columns, rows = await execute_sql(config, payload.sql)
        log_entry = AuraSqlQueryHistory(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            connection_id=connection.id,
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
            context_id=row.context_id,
            natural_language_query=row.natural_language_query,
            generated_sql=row.generated_sql,
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else "",
            error_message=row.error_message,
        )
        for row in rows
    ]
