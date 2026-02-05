from __future__ import annotations

from app.schemas import CognitiveResult, ComplicationRisk, LabValues, RetinalResult, RiskScores


class RiskScorer:
    def score(
        self,
        labs: LabValues,
        retinal: RetinalResult | None,
        cognitive: CognitiveResult | None = None,
    ) -> RiskScores:
        dementia = self._score_dementia(labs, cognitive)
        cvd = self._score_cvd(labs)
        nephro = self._score_nephropathy(labs)
        ret = self._score_retinopathy(labs, retinal)
        neuro = self._score_neuropathy(labs)
        return RiskScores(
            dementia=dementia,
            cardiovascular=cvd,
            retinopathy=ret,
            nephropathy=nephro,
            neuropathy=neuro,
        )

    def _score_dementia(self, labs: LabValues, cognitive: CognitiveResult | None) -> ComplicationRisk:
        score = 20.0
        factors = []
        if labs.a1c is not None:
            if labs.a1c >= 8:
                score += 15
                factors.append("A1C above 8%")
            elif labs.a1c >= 7:
                score += 10
                factors.append("A1C above 7%")
        if labs.systolic_bp is not None and labs.systolic_bp >= 140:
            score += 8
            factors.append("Elevated systolic blood pressure")
        if cognitive and cognitive.score is not None:
            if cognitive.score <= 2:
                score += 12
                factors.append("Low cognitive screening score")
            elif cognitive.score <= 3:
                score += 8
                factors.append("Borderline cognitive screening score")
        return self._pack(score, factors)

    def _score_cvd(self, labs: LabValues) -> ComplicationRisk:
        score = 18.0
        factors = []
        if labs.ldl is not None and labs.ldl >= 130:
            score += 10
            factors.append("LDL above 130")
        if labs.systolic_bp is not None and labs.systolic_bp >= 140:
            score += 10
            factors.append("Systolic BP above 140")
        if labs.a1c is not None and labs.a1c >= 7:
            score += 6
            factors.append("A1C above 7%")
        return self._pack(score, factors)

    def _score_nephropathy(self, labs: LabValues) -> ComplicationRisk:
        score = 15.0
        factors = []
        if labs.egfr is not None and labs.egfr < 60:
            score += 12
            factors.append("Reduced eGFR")
        if labs.urine_albumin is not None and labs.urine_albumin >= 30:
            score += 10
            factors.append("Elevated urine albumin")
        if labs.a1c is not None and labs.a1c >= 7.5:
            score += 6
            factors.append("A1C above 7.5%")
        return self._pack(score, factors)

    def _score_retinopathy(self, labs: LabValues, retinal: RetinalResult | None) -> ComplicationRisk:
        score = 10.0
        factors = []
        if labs.a1c is not None and labs.a1c >= 7.5:
            score += 8
            factors.append("A1C above 7.5%")
        if retinal is None or retinal.grade in {"Unknown", "Not Analyzed"}:
            factors.append("Retinal image not graded")
        return self._pack(score, factors)

    def _score_neuropathy(self, labs: LabValues) -> ComplicationRisk:
        score = 12.0
        factors = []
        if labs.a1c is not None and labs.a1c >= 7.5:
            score += 7
            factors.append("A1C above 7.5%")
        return self._pack(score, factors)

    def _pack(self, score: float, factors: list[str]) -> ComplicationRisk:
        score = min(max(score, 0.0), 100.0)
        level = "Low"
        if score >= 35:
            level = "Moderate"
        if score >= 60:
            level = "High"
        return ComplicationRisk(
            score=score,
            level=level,
            key_factors=factors[:3],
            protective_factors=[],
        )
