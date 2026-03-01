from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os
import yaml

DEFAULT_CONFIG_PATH = os.getenv("API_CONFIG_PATH", "/app/config")
DEFAULT_CONFIG_NAME = os.getenv("API_CONFIG_NAME", "config")  # config.yaml

class DBConfigModel(BaseSettings):
    Host: str
    Port: str = "5432"
    Username: str
    Password: str
    Name: str
    MaxOpenConn: int = 4
    MaxConnLifeTime: int = 300

    def dsn_asyncpg(self) -> str:
        # async SQLAlchemy driver
        return f"postgresql+asyncpg://{self.Username}:{self.Password}@{self.Host}:{self.Port}/{self.Name}"

class Settings(BaseSettings):
    app_name: str = Field(default="yt-clipper-api")
    env: str = Field(default=os.getenv("ENV", "local"))
    DBConfig: Optional[DBConfigModel] = None

def load_settings() -> Settings:
    candidates = [
        os.path.join(DEFAULT_CONFIG_PATH, f"{DEFAULT_CONFIG_NAME}.yaml"),
        os.path.join("app", "config", f"{DEFAULT_CONFIG_NAME}.yaml"),
    ]

    for path in candidates:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return Settings(**data)

    return Settings()