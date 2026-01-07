"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App Configuration
    app_name: str = "MindWell AI"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # OpenAI Configuration
    openai_api_key: SecretStr | None = None

    # Azure OpenAI Configuration (alternative to OpenAI)
    azure_openai_api_key: SecretStr | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment_name: str | None = None
    azure_openai_api_version: str = "2024-02-01"

    # LLM Configuration
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=1000, ge=1, le=4096)

    # Database Configuration
    database_url: SecretStr = SecretStr(
        "postgresql+asyncpg://mindwell:mindwell@localhost:5432/mindwell_db"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Security Configuration
    secret_key: SecretStr = SecretStr("change-me-in-production")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Logging Configuration
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"
    log_mask_pii: bool = True

    # Feature Flags
    enable_sentiment_analysis: bool = True
    enable_risk_assessment: bool = True
    enable_session_recording: bool = True

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Crisis Resources
    crisis_hotline_number: str = "988"
    crisis_text_line: str = "Text HOME to 741741"
    emergency_number: str = "911"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def use_azure_openai(self) -> bool:
        """Check if Azure OpenAI should be used."""
        return (
            self.azure_openai_api_key is not None
            and self.azure_openai_endpoint is not None
            and self.azure_openai_deployment_name is not None
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
