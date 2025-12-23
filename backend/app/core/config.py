"""
Application configuration using pydantic-settings.
"""
from typing import List

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Personal Knowledge Assistant"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: str | List[str] = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Database (PostgreSQL)
    database_url: PostgresDsn
    postgres_user: str = "postgres"
    postgres_db: str = "knowledge_assistant"

    # Vector Database (ChromaDB)
    chroma_persist_directory: str = "./chroma_data"
    chroma_collection_name: str = "knowledge_base"

    # Ollama (Local LLMs)
    ollama_base_url: str = "http://localhost:11434"
    ollama_primary_model: str = "qwen2.5:14b"
    ollama_reasoning_model: str = "phi4:14b"
    ollama_fast_model: str = "llama3.2:3b"
    ollama_request_timeout: int = 300

    # Google Gemini API
    gemini_api_key: str | None = None
    gemini_default_model: str = "gemini-2.5-flash"  # Free tier models available

    # Embeddings Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    use_local_embeddings: bool = True

    # RAG Configuration
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_retrieval_chunks: int = 10  # Initial retrieval (before re-ranking)
    max_final_chunks: int = 3  # After re-ranking
    max_context_tokens: int = 5000
    rerank_enabled: bool = True  # Enable re-ranking for better relevance
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    web_search_confidence_threshold: float = 0.7  # Only use web if best match < this

    # File Upload Configuration
    max_upload_size_mb: int = 50  # Maximum file size in MB
    allowed_file_types: List[str] = ["txt", "md", "markdown", "pdf", "doc", "docx"]
    upload_directory: str = "./uploads"

    # Document Archive Configuration (External Drive)
    archive_enabled: bool = False  # Enable archiving original documents to external drive
    archive_base_path: str = "/Volumes/Knowledge-Drive"  # Base path for external drive
    archive_documents_path: str = "documents"  # Subdirectory for documents within archive
    archive_backups_path: str = "backups"  # Subdirectory for backups within archive
    archive_fallback_to_local: bool = True  # If external drive unavailable, save locally

    # Security (for future authentication)
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30


# Global settings instance
settings = Settings()
