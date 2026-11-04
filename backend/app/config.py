from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    hosted_llm_provider: Literal["anthropic", "openai_compat"] | None = None
    hosted_llm_model: str = ""
    hosted_llm_api_key: str = ""
    hosted_llm_base_url: str = ""  # only for hosted openai_compat, e.g. https://api.openai.com/v1
    open_model_endpoint: str = ""  # OpenAI-compatible base URL, e.g. http://localhost:11434/v1
    open_model_name: str = ""
    llm_max_retries: int = 3
    llm_timeout_s: float = 120.0

    audit_data_dir: Path = REPO_ROOT / "backend" / "data" / "audits"
    max_upload_mb: float = 100.0
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()


def get_settings() -> Settings:
    return settings
