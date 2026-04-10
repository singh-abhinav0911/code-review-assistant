from __future__ import annotations

import json
import re
from typing import Protocol

from app.config import settings


class ReviewLLM(Protocol):
    def review(self, prompt: str) -> tuple[bool, dict]:
        """Return whether an LLM was used and a parsed review payload."""


class GeminiReviewer:
    def __init__(self) -> None:
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not configured.")
        import google.generativeai as genai

        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)

    def review(self, prompt: str) -> tuple[bool, dict]:
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        return True, _parse_json_response(text)


class HeuristicReviewer:
    def review(self, prompt: str) -> tuple[bool, dict]:
        findings: list[str] = []
        lower = prompt.lower()
        patterns = {
            "bare except": "A bare `except:` can hide real failures and make debugging much harder.",
            "eval(": "Use of `eval` can create code execution risk if any input reaches it.",
            "exec(": "Use of `exec` can create code execution risk and should be justified carefully.",
            "todo": "There are TODO markers in the reviewed content; confirm unfinished work is not shipping unintentionally.",
            "print(": "Debug prints may leak internal state or create noisy logs in production paths.",
            "password": "Possible secret-handling logic detected; confirm secrets are not logged, hard-coded, or returned.",
        }
        for needle, message in patterns.items():
            if needle in lower:
                findings.append(message)

        if "test" not in lower:
            findings.append("No explicit test coverage appears in the request context; validate the changed behavior with focused tests.")

        if not findings:
            findings.append("No obvious rule-based issues were detected, but this fallback reviewer is limited and should be replaced with an LLM-backed review.")

        return False, {
            "summary": "Heuristic review generated because no LLM credentials were configured.",
            "findings": findings[:5],
        }


def build_reviewer() -> ReviewLLM:
    if settings.google_api_key:
        return GeminiReviewer()
    return HeuristicReviewer()


def _parse_json_response(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {
            "summary": "The LLM returned a non-JSON response.",
            "findings": [text],
        }
