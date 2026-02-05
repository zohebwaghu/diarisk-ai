from __future__ import annotations

from typing import List

from app import config
from app.schemas import Recommendation, RiskScores
from app.services.llm import TextLLM


class RecommendationService:
    def __init__(self) -> None:
        self.llm = TextLLM()

    def generate(self, risk_scores: RiskScores) -> List[Recommendation]:
        if not config.ENABLE_TEXT_LLM:
            return self._fallback()

        prompt = self._prompt(risk_scores)
        lines = self.llm.generate_lines(prompt, max_new_tokens=256)
        recommendations = self._parse(lines)
        return recommendations if recommendations else self._fallback()

    def _prompt(self, risk_scores: RiskScores) -> str:
        return (
            "You are a clinical risk assistant. Generate 3 concise, actionable "
            "recommendations for a patient with diabetes based on these risk scores:\n"
            f"- Dementia: {risk_scores.dementia.score:.1f} ({risk_scores.dementia.level})\n"
            f"- Cardiovascular: {risk_scores.cardiovascular.score:.1f} ({risk_scores.cardiovascular.level})\n"
            f"- Retinopathy: {risk_scores.retinopathy.score:.1f} ({risk_scores.retinopathy.level})\n"
            f"- Nephropathy: {risk_scores.nephropathy.score:.1f} ({risk_scores.nephropathy.level})\n"
            f"- Neuropathy: {risk_scores.neuropathy.score:.1f} ({risk_scores.neuropathy.level})\n"
            "Format each item as: Title | Expected impact | Rationale."
        )

    def _parse(self, lines: List[str]) -> List[Recommendation]:
        results: List[Recommendation] = []
        for line in lines:
            if "|" not in line:
                continue
            parts = [part.strip(" -") for part in line.split("|")]
            if len(parts) < 3:
                continue
            results.append(
                Recommendation(
                    title=parts[0],
                    expected_impact=parts[1],
                    rationale=parts[2],
                )
            )
        return results[:3]

    def _fallback(self) -> List[Recommendation]:
        return [
            Recommendation(
                title="Lower A1C toward 7%",
                expected_impact="Reduce multi-complication risk",
                rationale="Better glycemic control lowers vascular and cognitive risk.",
            ),
            Recommendation(
                title="Optimize blood pressure",
                expected_impact="Lower heart and kidney risk",
                rationale="BP control reduces microvascular damage.",
            ),
            Recommendation(
                title="Keep annual eye and kidney screening",
                expected_impact="Early detection of complications",
                rationale="Screening catches silent progression before symptoms.",
            ),
        ]
