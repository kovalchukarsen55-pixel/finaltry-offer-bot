from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, field_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow",
    )

    bot_token: str = Field(..., env="BOT_TOKEN")
    sheets_id: str = Field(..., env="SHEETS_ID")
    google_service_file: str = Field("credentials.json", env="GOOGLE_SERVICE_FILE")
    refresh_sec: int = Field(300, env="REFRESH_SEC")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    admin_ids: list[int] = Field(default_factory=list, env="ADMIN_IDS")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _normalize_admins(cls, v):
        if v in (None, "", []):
            return []
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v if str(x).strip()]
        raise TypeError("ADMIN_IDS must be str, int or list[int]")

    @field_validator("log_level", mode="after")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return (v or "INFO").upper()

settings = Settings()
