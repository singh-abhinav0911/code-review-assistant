# Code Review RAG MVP

This project is a minimal retrieval-augmented generation service for code review.

It does four things:

1. Scans a repository and chunks source files.
2. Builds lightweight local embeddings for those chunks.
3. Retrieves the most relevant code context for a review request.
4. Sends the context plus the diff or file contents to an LLM for review.

## Features

- FastAPI API for ingestion and review
- Local hash-based embeddings, so indexing works without extra ML downloads
- Optional Gemini integration through `GOOGLE_API_KEY`
- Persistent JSON index per repository under `data/indexes/`
- File review and diff review endpoints

## Project Layout

```text
app/
  codebase.py
  config.py
  llm.py
  main.py
  models.py
  reviewer.py
```

## Setup

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a `.env` file if you want LLM-backed reviews:

```env
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

You can start from the included example:

```powershell
Copy-Item .env.example .env
```

## Run

```powershell
venv\Scripts\uvicorn.exe app.main:app --reload
```

## API

### Ingest a repository

```http
POST /ingest
Content-Type: application/json

{
  "repo_path": "C:\\path\\to\\repo"
}
```

### Review a file

```http
POST /review/file
Content-Type: application/json

{
  "repo_path": "C:\\path\\to\\repo",
  "file_path": "src/example.py",
  "question": "Find correctness, security, and maintainability issues."
}
```

### Review a diff

```http
POST /review/diff
Content-Type: application/json

{
  "repo_path": "C:\\path\\to\\repo",
  "diff": "diff --git a/app.py b/app.py ...",
  "question": "Focus on regressions and missing tests."
}
```

## Notes

- The local embedding model is intentionally simple so the project runs in this environment without extra downloads.
- For production quality, the next upgrade would be replacing the hash embeddings with a real embedding model and swapping JSON persistence for a vector store.
