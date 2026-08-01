from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ExtratoAI"
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    database_url: str = ""
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @property
    def inbox_dir(self) -> Path:
        return self.data_dir / "inbox"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def uploads_dir(self) -> Path:
        """UI uploads land here to avoid racing with the inbox watcher."""
        return self.data_dir / "uploads"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "extratoai.db"

    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.db_path}"


settings = Settings()
