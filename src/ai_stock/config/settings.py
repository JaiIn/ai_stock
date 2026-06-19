"""Local-only environment settings with safe defaults."""

from enum import Enum
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ai_stock.utils.masking import sanitize_mapping


class ExecutionMode(str, Enum):
    """Supported local execution modes."""

    MOCK = "mock"
    PAPER = "paper"
    LIVE = "live"


class Settings(BaseSettings):
    """Configuration loaded from environment variables or `.env.local`."""

    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["local"] = "local"
    app_host: Literal["127.0.0.1", "localhost"] = "127.0.0.1"
    app_port: int = Field(default=8501, ge=1, le=65535)
    database_url: str = "sqlite:///data/local/app.db"

    execution_mode: ExecutionMode = ExecutionMode.MOCK
    allow_live_api: bool = False
    allow_real_order: bool = False
    dry_run_only: bool = True

    toss_client_id: SecretStr | None = None
    toss_client_secret: SecretStr | None = None
    toss_access_token: SecretStr | None = None
    toss_account_seq: SecretStr | None = None

    llm_provider: str = "mock"
    openai_api_key: SecretStr | None = None

    log_level: str = "INFO"
    mask_secrets: bool = True

    @model_validator(mode="after")
    def enforce_local_safety(self) -> "Settings":
        """Reject settings that violate the v0.1 local-only policy."""

        if self.allow_real_order:
            raise ValueError("Real orders are disabled in v0.1.")
        if not self.dry_run_only:
            raise ValueError("DRY_RUN_ONLY must remain true in v0.1.")
        if self.execution_mode is ExecutionMode.LIVE and not self.allow_live_api:
            raise ValueError("Live mode requires explicit ALLOW_LIVE_API=true approval.")
        return self

    def to_safe_dict(self) -> dict[str, object]:
        """Return settings suitable for display or structured logging."""

        return sanitize_mapping(self.model_dump(mode="python"))


def load_settings() -> Settings:
    """Load local settings without requiring live credentials."""

    return Settings()
