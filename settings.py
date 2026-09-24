from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""

    OPENAI_MODEL: str = "gpt-5-mini"
    OPENAI_SUMMARIZATION_MODEL: str = "gpt-4.1-mini"

    MAX_RESEARCH_ITERATIONS: int = 3
    MAX_SEARCH_RESULTS: int = 5

    REPORTS_DIR: str = "./reports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()

Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)
