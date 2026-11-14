from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Bug Fixer & Code Reviewer"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    workspace_root: Path = Path("./workspaces")
    max_files_per_scan: int = 500
    max_file_size_bytes: int = 262_144
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_timeout_seconds: float = 120.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
