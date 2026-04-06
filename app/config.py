from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

DEFAULT_CONFIG_PATH = os.getenv("API_CONFIG_PATH", "/app/config")
DEFAULT_CONFIG_NAME = os.getenv("API_CONFIG_NAME", "config")


class DBConfigModel(BaseModel):
    Host: str = Field(default_factory=lambda: os.getenv("DB_HOST", ""))
    Port: str = Field(default_factory=lambda: os.getenv("DB_PORT", "5432"))
    Username: str = Field(default_factory=lambda: os.getenv("DB_USERNAME", ""))
    Password: str = Field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    Name: str = Field(default_factory=lambda: os.getenv("DB_NAME", ""))
    MaxOpenConn: int = Field(default_factory=lambda: int(os.getenv("DB_MAX_OPEN_CONN", "4")))
    MaxConnLifeTime: int = Field(default_factory=lambda: int(os.getenv("DB_MAX_CONN_LIFETIME", "300")))

    def dsn_asyncpg(self) -> str:
        return (
            f"postgresql+asyncpg://{self.Username}:{self.Password}"
            f"@{self.Host}:{self.Port}/{self.Name}"
        )


class MinioConfig(BaseModel):
    endpoint: str = Field(default_factory=lambda: os.getenv("MINIO_ENDPOINT", ""))
    region: str = Field(default_factory=lambda: os.getenv("MINIO_REGION", "us-east-1"))
    bucket: str = Field(
        default_factory=lambda: os.getenv("STORAGE_BUCKET_NAME", os.getenv("MINIO_BUCKET", "yt-clips"))
    )
    accessKey: str = Field(default_factory=lambda: os.getenv("MINIO_ACCESS_KEY", ""))
    secretKey: str = Field(default_factory=lambda: os.getenv("MINIO_SECRET_KEY", ""))


class OpenAIConfig(BaseModel):
    apiKey: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    modelChat: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_CHAT", "gpt-4o-mini"))
    modelTTS: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_TTS", "gpt-4o-mini-tts"))
    modelSTT: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL_STT", "gpt-4o-mini-transcribe"))


class CoreConfig(BaseModel):
    publicBaseURL: str = Field(
        default_factory=lambda: os.getenv(
            "PUBLIC_BASE_URL",
            os.getenv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8080"),
        )
    )
    nextPublicApiBaseURL: str = Field(
        default_factory=lambda: os.getenv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8080")
    )
    sessionSecret: str = Field(default_factory=lambda: os.getenv("SESSION_SECRET", "dev-session-secret"))
    defaultLocale: str = Field(default_factory=lambda: os.getenv("APP_LOCALE", "en"))
    compatibilityUseLatestSession: bool = True


class LineConfig(BaseModel):
    liffId: str = Field(default_factory=lambda: os.getenv("NEXT_PUBLIC_LIFF_ID", ""))
    channelId: str = Field(default_factory=lambda: os.getenv("LINE_CHANNEL_ID", ""))
    channelSecret: str = Field(default_factory=lambda: os.getenv("LINE_CHANNEL_SECRET", ""))
    loginRedirectURI: str = Field(default_factory=lambda: os.getenv("LINE_LOGIN_REDIRECT_URI", ""))
    botChannelAccessToken: str = Field(
        default_factory=lambda: os.getenv("LINE_BOT_CHANNEL_ACCESS_TOKEN", "")
    )


class OptionalInfraConfig(BaseModel):
    databaseURL: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    redisURL: str = Field(default_factory=lambda: os.getenv("REDIS_URL", ""))
    storageBucketName: str = Field(default_factory=lambda: os.getenv("STORAGE_BUCKET_NAME", ""))
    youtubeApiKey: str = Field(default_factory=lambda: os.getenv("YOUTUBE_API_KEY", ""))


class Settings(BaseSettings):
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "yt-clipper-api"))
    env: str = Field(default_factory=lambda: os.getenv("ENV", "local"))

    DBConfig: DBConfigModel | None = None
    Minio: MinioConfig | None = None
    OpenAI: OpenAIConfig | None = None
    Core: CoreConfig | None = None
    Line: LineConfig | None = None
    Optional: OptionalInfraConfig | None = None

    BaseURL: str | None = Field(default_factory=lambda: os.getenv("BASE_URL", ""))
    prefixTTSVoice: str = Field(default_factory=lambda: os.getenv("PREFIX_TTS_VOICE", "youtube"))

    def database_url(self) -> str | None:
        if self.Optional and self.Optional.databaseURL:
            return self._normalize_database_url(self.Optional.databaseURL)
        if self.DBConfig and self.DBConfig.Host:
            return self.DBConfig.dsn_asyncpg()
        return None

    def public_base_url(self) -> str:
        if self.Core and self.Core.publicBaseURL:
            return self.Core.publicBaseURL
        if self.BaseURL:
            return self.BaseURL
        return "http://localhost:8080"

    @staticmethod
    def _normalize_database_url(value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+asyncpg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value


def _load_yaml_settings() -> dict:
    candidates = [
        Path(DEFAULT_CONFIG_PATH) / f"{DEFAULT_CONFIG_NAME}.yaml",
        Path("app") / "config" / f"{DEFAULT_CONFIG_NAME}.yaml",
    ]
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
    return {}


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings(**_load_yaml_settings())
