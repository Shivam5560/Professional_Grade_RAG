"""Pydantic models for AuraSQL endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AuraSqlConnectionCreate(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database: str
    schema_name: Optional[str] = None
    ssl_required: bool = True


class AuraSqlConnectionUpdate(BaseModel):
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    schema_name: Optional[str] = None
    ssl_required: Optional[bool] = None


class AuraSqlConnectionResponse(BaseModel):
    id: str
    name: str
    db_type: str
    host: str
    port: int
    username: str
    database: str
    schema_name: Optional[str] = None
    ssl_required: bool


class AuraSqlConnectionListResponse(BaseModel):
    connections: List[AuraSqlConnectionResponse]


class AuraSqlContextCreate(BaseModel):
    connection_id: str
    name: str
    table_names: List[str] = Field(min_items=1)
    is_temporary: bool = False


class AuraSqlContextResponse(BaseModel):
    id: str
    connection_id: str
    name: str
    table_names: List[str]
    is_temporary: bool = False


class AuraSqlContextDetailResponse(AuraSqlContextResponse):
    schema_snapshot: dict


class AuraSqlContextUpdate(BaseModel):
    name: Optional[str] = None
    table_names: Optional[List[str]] = None
    is_temporary: Optional[bool] = None


class AuraSqlContextListResponse(BaseModel):
    contexts: List[AuraSqlContextResponse]


class AuraSqlRecommendationsRequest(BaseModel):
    context_id: str


class AuraSqlRecommendationsResponse(BaseModel):
    recommendations: List[str]


class AuraSqlQueryRequest(BaseModel):
    context_id: str
    query: str
    session_id: Optional[str] = None
    output_dialect: Optional[str] = None


class AuraSqlQueryResponse(BaseModel):
    sql: str
    explanation: str
    source_tables: List[str]
    session_id: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    validation_errors: Optional[List[str]] = None


class AuraSqlExecuteRequest(BaseModel):
    connection_id: str
    sql: str
    session_id: Optional[str] = None


class AuraSqlExecuteResponse(BaseModel):
    columns: List[str]
    rows: List[dict]


class AuraSqlLogResponse(BaseModel):
    id: str
    connection_id: str
    session_id: Optional[str] = None
    context_id: Optional[str] = None
    natural_language_query: Optional[str] = None
    generated_sql: Optional[str] = None
    source_tables: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    status: str
    created_at: str
    error_message: Optional[str] = None


class AuraSqlSessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    connection_id: Optional[str] = None
    context_id: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
