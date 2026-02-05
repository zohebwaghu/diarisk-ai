from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LabValues(BaseModel):
    a1c: Optional[float] = None
    fasting_glucose: Optional[float] = None
    egfr: Optional[float] = None
    creatinine: Optional[float] = None
    ldl: Optional[float] = None
    hdl: Optional[float] = None
    triglycerides: Optional[float] = None
    urine_albumin: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None


class LabParseResult(BaseModel):
    values: LabValues
    raw_text: str
    missing_fields: List[str] = Field(default_factory=list)
    quality_flags: List[str] = Field(default_factory=list)


class LabInsights(BaseModel):
    summary: Optional[str] = None
    flags: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)


class RetinalResult(BaseModel):
    grade: str
    confidence: Optional[float] = None
    findings: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    model_metadata: Dict[str, Any] = Field(default_factory=dict)


class CognitiveResult(BaseModel):
    score: Optional[float] = None
    summary: Optional[str] = None
    flags: List[str] = Field(default_factory=list)


class ComplicationRisk(BaseModel):
    score: float
    level: str
    key_factors: List[str] = Field(default_factory=list)
    protective_factors: List[str] = Field(default_factory=list)


class RiskScores(BaseModel):
    dementia: ComplicationRisk
    cardiovascular: ComplicationRisk
    retinopathy: ComplicationRisk
    nephropathy: ComplicationRisk
    neuropathy: ComplicationRisk


class Recommendation(BaseModel):
    title: str
    expected_impact: str
    rationale: str


class AgentTraceItem(BaseModel):
    agent: str
    status: str
    duration_ms: Optional[int] = None
    notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    labs: LabParseResult
    lab_insights: Optional[LabInsights] = None
    retinal: Optional[RetinalResult] = None
    cognitive: Optional[CognitiveResult] = None
    risk_scores: RiskScores
    recommendations: List[Recommendation]
    agent_trace: List[AgentTraceItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
