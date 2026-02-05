from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Optional

from app.schemas import AgentTraceItem, CognitiveResult, LabInsights, LabParseResult, RetinalResult, RiskScores
from app.services.cognitive import CognitiveAgent
from app.services.lab_parser import LabParser
from app.services.lab_value_agent import LabValueAgent
from app.services.recommendations import RecommendationService
from app.services.retinal import RetinalAnalyzer
from app.services.risk import RiskScorer


@dataclass
class OrchestratorOutput:
    labs: LabParseResult
    lab_insights: LabInsights | None
    retinal: Optional[RetinalResult]
    cognitive: Optional[CognitiveResult]
    risk_scores: RiskScores
    recommendations: list
    agent_trace: list[AgentTraceItem]
    warnings: list[str]


class OrchestratorAgent:
    def __init__(self) -> None:
        self.intake_agent = LabParser()
        self.lab_value_agent = LabValueAgent()
        self.retinal_agent = RetinalAnalyzer()
        self.cognitive_agent = CognitiveAgent()
        self.risk_agent = RiskScorer()
        self.recommendation_agent = RecommendationService()

    def run(
        self,
        lab_filename: str,
        lab_bytes: bytes,
        retinal_bytes: Optional[bytes],
        cognitive_notes: Optional[str],
    ) -> OrchestratorOutput:
        warnings: list[str] = []
        trace: list[AgentTraceItem] = []

        labs = self._run_with_trace(
            trace,
            "Intake Agent",
            lambda: self.intake_agent.parse(lab_filename, lab_bytes),
        )
        lab_insights = self._run_with_trace(
            trace,
            "Lab Value Agent",
            lambda: self.lab_value_agent.interpret(labs.values),
        )
        retinal = None
        if retinal_bytes:
            retinal = self._run_with_trace(
                trace,
                "Retinal Agent",
                lambda: self._analyze_retinal(retinal_bytes, warnings),
            )
        else:
            trace.append(
                AgentTraceItem(
                    agent="Retinal Agent",
                    status="skipped",
                    duration_ms=0,
                    notes="No retinal image provided.",
                )
            )

        cognitive = self._run_with_trace(
            trace,
            "Cognitive Agent",
            lambda: self.cognitive_agent.score(cognitive_notes),
        )
        risk_scores = self._run_with_trace(
            trace,
            "Risk Scoring Agent",
            lambda: self.risk_agent.score(labs.values, retinal, cognitive),
        )
        recommendations = self._run_with_trace(
            trace,
            "Recommendation Agent",
            lambda: self.recommendation_agent.generate(risk_scores),
        )

        return OrchestratorOutput(
            labs=labs,
            lab_insights=lab_insights,
            retinal=retinal,
            cognitive=cognitive,
            risk_scores=risk_scores,
            recommendations=recommendations,
            agent_trace=trace,
            warnings=warnings,
        )

    def _analyze_retinal(self, file_bytes: bytes, warnings: list[str]) -> RetinalResult:
        from PIL import Image
        import io

        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            return self.retinal_agent.analyze(image)
        except Exception as exc:  # pragma: no cover - safety net for demo
            warnings.append(f"Retinal analysis failed: {exc}")
            return RetinalResult(
                grade="Unknown",
                findings=[],
                summary="Retinal analysis failed.",
                model_metadata={"error": str(exc)},
            )

    def _run_with_trace(self, trace: list[AgentTraceItem], agent: str, fn):
        started = perf_counter()
        try:
            result = fn()
            duration_ms = int((perf_counter() - started) * 1000)
            trace.append(AgentTraceItem(agent=agent, status="ok", duration_ms=duration_ms))
            return result
        except Exception as exc:  # pragma: no cover - safety net for demo
            duration_ms = int((perf_counter() - started) * 1000)
            trace.append(
                AgentTraceItem(
                    agent=agent,
                    status="error",
                    duration_ms=duration_ms,
                    notes=str(exc),
                )
            )
            raise
