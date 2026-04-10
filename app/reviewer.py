from __future__ import annotations

from pathlib import Path

from app.codebase import CodeIndex
from app.llm import build_reviewer
from app.models import RetrievalHit, ReviewResponse


REVIEW_SCHEMA = """Return valid JSON with this shape:
{
  "summary": "short overall assessment",
  "findings": [
    "finding one with impact and suggestion",
    "finding two with impact and suggestion"
  ]
}
"""


def _format_context(index: CodeIndex, query: str) -> tuple[str, list[RetrievalHit]]:
    chunks = index.search(query)
    hits: list[RetrievalHit] = []
    blocks: list[str] = []

    for chunk, score in chunks:
        hits.append(
            RetrievalHit(
                path=chunk.path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                score=score,
                snippet=chunk.content,
            )
        )
        blocks.append(
            f"FILE: {chunk.path}:{chunk.start_line}-{chunk.end_line}\n{chunk.content}"
        )

    return "\n\n".join(blocks), hits


def _normalize_repo_path(repo_path: str | Path) -> Path:
    return Path(repo_path).resolve()


def _load_or_build_index(repo_path: str | Path) -> CodeIndex:
    repo_path = _normalize_repo_path(repo_path)
    try:
        return CodeIndex.load(repo_path)
    except FileNotFoundError:
        from app.models import IngestRequest

        request = IngestRequest(repo_path=repo_path)
        return CodeIndex.build(
            repo_path=request.repo_path,
            include_extensions=request.include_extensions,
            exclude_dirs=request.exclude_dirs,
        )


def review_file(repo_path: str | Path, file_path: str, question: str) -> ReviewResponse:
    repo_path = _normalize_repo_path(repo_path)
    target_path = (repo_path / file_path).resolve()
    contents = target_path.read_text(encoding="utf-8", errors="ignore")
    index = _load_or_build_index(repo_path)
    query = f"{file_path}\n{question}\n{contents}"
    context_text, hits = _format_context(index, query)
    prompt = _build_prompt(
        question=question,
        review_target=f"File under review: {file_path}\n\n{contents}",
        retrieved_context=context_text,
    )
    llm_used, payload = build_reviewer().review(prompt)
    return ReviewResponse(
        summary=payload.get("summary", "Review completed."),
        findings=payload.get("findings", []),
        retrieved_context=hits,
        prompt_preview=prompt[:2000],
        llm_used=llm_used,
    )


def review_diff(repo_path: str | Path, diff: str, question: str) -> ReviewResponse:
    index = _load_or_build_index(repo_path)
    query = f"{question}\n{diff}"
    context_text, hits = _format_context(index, query)
    prompt = _build_prompt(
        question=question,
        review_target=f"Diff under review:\n\n{diff}",
        retrieved_context=context_text,
    )
    llm_used, payload = build_reviewer().review(prompt)
    return ReviewResponse(
        summary=payload.get("summary", "Review completed."),
        findings=payload.get("findings", []),
        retrieved_context=hits,
        prompt_preview=prompt[:2000],
        llm_used=llm_used,
    )


def _build_prompt(question: str, review_target: str, retrieved_context: str) -> str:
    return f"""You are a senior engineer performing code review.

Focus on:
- correctness issues
- likely regressions
- security problems
- missing edge cases
- missing tests

Only report concrete findings. If something looks good, keep the summary brief.

{REVIEW_SCHEMA}

User request:
{question}

Target:
{review_target}

Retrieved repository context:
{retrieved_context if retrieved_context else "No additional repository context was retrieved."}
"""
