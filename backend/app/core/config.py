"""
AI Proposal Generator - Configuration Management
Using Pydantic Settings for type-safe environment variable handling
"""

from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # =========================================================================
    # Application Settings
    # =========================================================================
    APP_NAME: str = "AI Proposal Generator"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
    )
    
    # =========================================================================
    # Database Settings
    # =========================================================================
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://aipg_user:aipg_secret_2024@postgres-db:5432/ai_proposal_db"
    )
    DATABASE_URL_SYNC: str = Field(
        default="postgresql://aipg_user:aipg_secret_2024@postgres-db:5432/ai_proposal_db"
    )
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    
    # =========================================================================
    # Redis Settings
    # =========================================================================
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    
    # =========================================================================
    # MinIO Settings
    # =========================================================================
    MINIO_ENDPOINT: str = Field(default="minio:9000")
    MINIO_ACCESS_KEY: str = Field(default="aipg_minio_admin")
    MINIO_SECRET_KEY: str = Field(default="aipg_minio_secret_2024")
    MINIO_SECURE: bool = Field(default=False)
    
    # Bucket Names
    BUCKET_TENDER_DOCS: str = "tender-documents"
    BUCKET_PROJECT_ASSETS: str = "project-assets"
    BUCKET_TEMPLATES: str = "templates"
    BUCKET_EXPORTS: str = "exports"
    
    # =========================================================================
    # JWT Settings
    # =========================================================================
    JWT_SECRET_KEY: str = Field(default="your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # =========================================================================
    # AI API Settings
    # =========================================================================
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    GEMINI_DEFAULT_MODEL: str = Field(default="gemini-1.5-pro")
    
    AI_DEFAULT_MAX_TOKENS: int = Field(default=4096)
    AI_DEFAULT_TEMPERATURE: float = Field(default=0.7)
    
    # =========================================================================
    # Token Budget
    # =========================================================================
    DEFAULT_PROJECT_TOKEN_BUDGET: int = Field(default=1_000_000)
    TOKEN_BUDGET_WARNING_THRESHOLD: float = Field(default=0.8)
    
    # =========================================================================
    # File Settings
    # =========================================================================
    MAX_UPLOAD_SIZE_MB: int = Field(default=50)
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = Field(
        default=[".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".gif"]
    )
    
    # =========================================================================
    # Concurrent Editing
    # =========================================================================
    SECTION_LOCK_TIMEOUT_MINUTES: int = Field(default=5)
    
    # =========================================================================
    # Properties
    # =========================================================================
    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"
    
    # =========================================================================
    # Validators
    # =========================================================================
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Export settings instance
settings = get_settings()