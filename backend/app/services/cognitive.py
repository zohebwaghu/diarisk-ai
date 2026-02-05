from __future__ import annotations

import re
from typing import Optional

from app import config
from app.schemas import CognitiveResult
from app.services.llm import TextLLM


class CognitiveAgent:
    def __init__(self) -> None:
        self.llm = TextLLM()

    def score(self, responses: Optional[str]) -> CognitiveResult:
        if not responses:
            return CognitiveResult(score=None, summary=None, flags=["no_cognitive_input"])

        if not config.ENABLE_TEXT_LLM:
            return CognitiveResult(
                score=None,
                summary="Cognitive agent disabled.",
                flags=["cognitive_disabled"],
            )

        prompt = self._prompt(responses)
        lines = self.llm.generate_lines(prompt, max_new_tokens=128)
        return self._parse(lines)

    def _prompt(self, responses: str) -> str:
        return (
            "You are a clinician scoring a brief cognitive screening. "
            "Given the notes below, estimate a Mini-Cog style score from 0 to 5. "
            "Return format: Score: X/5 | Summary: <one sentence>.\n"
            f"Notes: {responses}"
        )

    def _parse(self, lines: list[str]) -> CognitiveResult:
        text = " ".join(lines)
        score = None
        summary = None
        match = re.search(r"score\s*[:\-]?\s*(\d(?:\.\d+)?)\s*/\s*5", text, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
            except ValueError:
                score = None
        summary_match = re.search(r"summary\s*[:\-]?\s*(.+)$", text, re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()
        return CognitiveResult(score=score, summary=summary, flags=[])
