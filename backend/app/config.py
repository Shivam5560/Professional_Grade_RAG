"""
Configuration management for the RAG system.
Handles environment variables and application settings.
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Groq Configuration
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-20b", alias="GROQ_MODEL")
    
    # Ollama Configuration (for embeddings only)
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_embedding_model: str = Field(default="embeddinggemma", alias="OLLAMA_EMBEDDING_MODEL")
    ollama_reranker_model: str = Field(default="bge-reranker-v2-m3", alias="OLLAMA_RERANKER_MODEL")

    # Embedding & Reranker Provider Selection
    embedding_provider: str = Field(default="ollama", alias="EMBEDDING_PROVIDER")
    reranker_provider: str = Field(default="local", alias="RERANKER_PROVIDER")

    # Cohere Configuration
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    cohere_embedding_model: str = Field(default="embed-english-v3.0", alias="COHERE_EMBEDDING_MODEL")
    cohere_rerank_model: str = Field(default="rerank-english-v3.0", alias="COHERE_RERANK_MODEL")
    
    # Remote Embedding Service Configuration (Lightning.ai)
    use_remote_embedding_service: bool = Field(default=False, alias="USE_REMOTE_EMBEDDING_SERVICE")
    use_remote_reranker_service: bool = Field(default=False, alias="USE_REMOTE_RERANKER_SERVICE")
    remote_embedding_service_url: str = Field(
        default="https://8001-01kcxs65eap7vtj55ymz4r6xag.cloudspaces.litng.ai",
        alias="REMOTE_EMBEDDING_SERVICE_URL"
    )
    embedding_batch_size: int = Field(default=10, alias="EMBEDDING_BATCH_SIZE")
    embedding_request_timeout: int = Field(default=120, alias="EMBEDDING_REQUEST_TIMEOUT")  # 2 minutes for large batches
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="public", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_table_name: str = Field(default="rag_embeddings", alias="POSTGRES_TABLE_NAME")
    aurasql_table_name: str = Field(default="aurasql_embeddings", alias="AURASQL_TABLE_NAME")

    # Auth & Encryption Configuration
    jwt_secret: str = Field(default="dev-secret", alias="JWT_SECRET")
    jwt_refresh_secret: str = Field(default="dev-refresh-secret", alias="JWT_REFRESH_SECRET")
    jwt_access_exp_minutes: int = Field(default=15, alias="JWT_ACCESS_EXP_MINUTES")
    jwt_refresh_exp_days: int = Field(default=30, alias="JWT_REFRESH_EXP_DAYS")
    aurasql_master_key: str = Field(default="", alias="AURASQL_MASTER_KEY")
    
    # Data Storage Configuration
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=True, alias="API_RELOAD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # File Upload Configuration
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")  # 50 MB default
    allowed_file_extensions: List[str] = Field(
        default=[".txt", ".md", ".pdf", ".docx"],
        alias="ALLOWED_FILE_EXTENSIONS"
    )
    
    # RAG Configuration
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=128, alias="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=15, alias="TOP_K_RETRIEVAL")  # Retrieve top 15 nodes from all selected documents
    top_k_rerank: int = Field(default=5, alias="TOP_K_RERANK")  # Rerank to top 5 most relevant
    similarity_threshold: float = Field(default=0.3, alias="SIMILARITY_THRESHOLD")  # Lower threshold - let reranker filter quality
    
    # Chat Configuration
    max_chat_history: int = Field(default=10, alias="MAX_CHAT_HISTORY")
    max_tokens: int = Field(default=3000, alias="MAX_TOKENS")

    # AuraSQL Configuration
    aurasql_max_tokens: int = Field(default=1024, alias="AURASQL_MAX_TOKENS")
    aurasql_top_k: int = Field(default=3, alias="AURASQL_TOP_K")
    
    # PageIndex / Think Mode Configuration
    pageindex_max_pages_per_chunk: int = Field(default=15, alias="PAGEINDEX_MAX_PAGES_PER_CHUNK")
    pageindex_auto_generate: bool = Field(default=False, alias="PAGEINDEX_AUTO_GENERATE")  # Auto-generate trees on PDF upload
    
    # Confidence Scoring Weights
    # Increased retrieval weight since it's the most reliable signal
    weight_retrieval: float = Field(default=0.55, alias="WEIGHT_RETRIEVAL")
    weight_coherence: float = Field(default=0.25, alias="WEIGHT_COHERENCE")
    weight_coverage: float = Field(default=0.15, alias="WEIGHT_COVERAGE")
    weight_clarity: float = Field(default=0.05, alias="WEIGHT_CLARITY")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], 
        alias="CORS_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
