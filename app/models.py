from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    repo_path: Path
    include_extensions: list[str] = Field(
        default_factory=lambda: [
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".go",
            ".rs",
            ".cpp",
            ".c",
            ".cs",
            ".rb",
            ".php",
            ".swift",
            ".kt",
            ".sql",
            ".md",
            ".yaml",
            ".yml",
            ".json",
        ]
    )
    exclude_dirs: list[str] = Field(
        default_factory=lambda: [
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "__pycache__",
            "dist",
            "build",
            ".next",
            ".idea",
        ]
    )


class ReviewFileRequest(BaseModel):
    repo_path: Path
    file_path: str
    question: str = "Review this file for bugs, regressions, security issues, and missing tests."


class ReviewDiffRequest(BaseModel):
    repo_path: Path
    diff: str
    question: str = "Review this diff for correctness, regressions, security issues, and missing tests."


class RetrievalHit(BaseModel):
    path: str
    start_line: int
    end_line: int
    score: float
    snippet: str


class ReviewResponse(BaseModel):
    summary: str
    findings: list[str]
    retrieved_context: list[RetrievalHit]
    prompt_preview: str
    llm_used: bool
