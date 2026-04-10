from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.codebase import CodeIndex
from app.config import settings
from app.models import IngestRequest, ReviewDiffRequest, ReviewFileRequest
from app.reviewer import review_diff, review_file


app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ingest")
def ingest_repository(request: IngestRequest) -> dict:
    if not request.repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository path does not exist.")
    if not request.repo_path.is_dir():
        raise HTTPException(status_code=400, detail="Repository path must be a directory.")

    index = CodeIndex.build(
        repo_path=request.repo_path,
        include_extensions=request.include_extensions,
        exclude_dirs=request.exclude_dirs,
    )
    return {
        "repo_path": str(index.repo_path),
        "chunk_count": len(index.chunks),
        "index_path": str(index.storage_path),
    }


@app.post("/review/file")
def review_repository_file(request: ReviewFileRequest):
    target_path = request.repo_path / request.file_path
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Target file does not exist.")
    return review_file(
        repo_path=request.repo_path,
        file_path=request.file_path,
        question=request.question,
    )


@app.post("/review/diff")
def review_repository_diff(request: ReviewDiffRequest):
    if not request.diff.strip():
        raise HTTPException(status_code=400, detail="Diff cannot be empty.")
    return review_diff(
        repo_path=request.repo_path,
        diff=request.diff,
        question=request.question,
    )
