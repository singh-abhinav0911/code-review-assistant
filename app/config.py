from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    app_name: str = "Code Review RAG"
    data_dir: Path = Path("data")
    chunk_size: int = 80
    chunk_overlap: int = 20
    embedding_dim: int = 512
    top_k: int = 6
    google_api_key: str | None = os.getenv("GOOGLE_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "indexes"


settings = Settings()
