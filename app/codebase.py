from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from app.config import settings


TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{1,}")


@dataclass
class CodeChunk:
    path: str
    start_line: int
    end_line: int
    content: str
    embedding: list[float]


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]


def _embed(text: str) -> np.ndarray:
    vector = np.zeros(settings.embedding_dim, dtype=np.float32)
    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "little") % settings.embedding_dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector /= norm
    return vector


def _iter_files(repo_path: Path, include_extensions: list[str], exclude_dirs: list[str]) -> list[Path]:
    files: list[Path] = []
    excluded = set(exclude_dirs)
    allowed = {ext.lower() for ext in include_extensions}

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in excluded for part in path.parts):
            continue
        if path.suffix.lower() in allowed:
            files.append(path)
    return files


def _chunk_file(repo_path: Path, file_path: Path) -> list[CodeChunk]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

    lines = text.splitlines()
    if not lines:
        return []

    chunks: list[CodeChunk] = []
    step = max(1, settings.chunk_size - settings.chunk_overlap)

    for start in range(0, len(lines), step):
        end = min(start + settings.chunk_size, len(lines))
        snippet = "\n".join(lines[start:end]).strip()
        if not snippet:
            continue
        relative_path = file_path.relative_to(repo_path).as_posix()
        chunks.append(
            CodeChunk(
                path=relative_path,
                start_line=start + 1,
                end_line=end,
                content=snippet,
                embedding=_embed(f"{relative_path}\n{snippet}").tolist(),
            )
        )
        if end == len(lines):
            break

    return chunks


class CodeIndex:
    def __init__(self, repo_path: Path, chunks: list[CodeChunk]) -> None:
        self.repo_path = repo_path.resolve()
        self.chunks = chunks
        self._matrix = np.array([chunk.embedding for chunk in chunks], dtype=np.float32) if chunks else np.zeros((0, settings.embedding_dim), dtype=np.float32)

    @property
    def repo_id(self) -> str:
        return hashlib.sha256(str(self.repo_path).encode("utf-8")).hexdigest()[:16]

    @property
    def storage_path(self) -> Path:
        settings.index_dir.mkdir(parents=True, exist_ok=True)
        return settings.index_dir / f"{self.repo_id}.json"

    def save(self) -> None:
        payload = {
            "repo_path": str(self.repo_path),
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }
        self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def search(self, query: str, top_k: int | None = None) -> list[tuple[CodeChunk, float]]:
        if not self.chunks:
            return []

        query_embedding = _embed(query)
        scores = self._matrix @ query_embedding
        limit = top_k or settings.top_k
        top_indices = np.argsort(scores)[::-1][:limit]
        return [
            (self.chunks[index], float(scores[index]))
            for index in top_indices
            if scores[index] > 0
        ]

    @classmethod
    def build(cls, repo_path: Path, include_extensions: list[str], exclude_dirs: list[str]) -> "CodeIndex":
        repo_path = repo_path.resolve()
        chunks: list[CodeChunk] = []
        for file_path in _iter_files(repo_path, include_extensions, exclude_dirs):
            chunks.extend(_chunk_file(repo_path, file_path))
        index = cls(repo_path=repo_path, chunks=chunks)
        index.save()
        return index

    @classmethod
    def load(cls, repo_path: Path) -> "CodeIndex":
        repo_path = repo_path.resolve()
        repo_id = hashlib.sha256(str(repo_path).encode("utf-8")).hexdigest()[:16]
        storage_path = settings.index_dir / f"{repo_id}.json"
        payload = json.loads(storage_path.read_text(encoding="utf-8"))
        chunks = [CodeChunk(**chunk) for chunk in payload["chunks"]]
        return cls(repo_path=Path(payload["repo_path"]), chunks=chunks)
