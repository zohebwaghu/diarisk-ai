from __future__ import annotations

import io
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from app import config
from app.schemas import AnalysisResponse, LabParseResult, RetinalResult
from app.services.lab_parser import LabParser
from app.services.recommendations import RecommendationService
from app.services.retinal import RetinalAnalyzer
from app.services.risk import RiskScorer
from app.storage import SQLiteStore

app = FastAPI(title="DiaRisk AI Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

lab_parser = LabParser()
retinal_analyzer = RetinalAnalyzer()
risk_scorer = RiskScorer()
recommendation_service = RecommendationService()
store = SQLiteStore()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/labs/parse", response_model=LabParseResult)
async def parse_labs(lab_report: UploadFile = File(...)) -> LabParseResult:
    file_bytes = await _read_file(lab_report)
    return lab_parser.parse(lab_report.filename or "lab_report", file_bytes)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    lab_report: UploadFile = File(...),
    retinal_image: Optional[UploadFile] = File(None),
) -> AnalysisResponse:
    warnings = []
    lab_bytes = await _read_file(lab_report)
    lab_result = lab_parser.parse(lab_report.filename or "lab_report", lab_bytes)

    retinal_result: Optional[RetinalResult] = None
    if retinal_image is not None:
        retinal_bytes = await _read_file(retinal_image)
        retinal_result = _analyze_retinal(retinal_bytes, warnings)

    risk_scores = risk_scorer.score(lab_result.values, retinal_result)
    recommendations = recommendation_service.generate(risk_scores)

    response = AnalysisResponse(
        labs=lab_result,
        retinal=retinal_result,
        risk_scores=risk_scores,
        recommendations=recommendations,
        warnings=warnings,
    )
    store.insert_analysis(
        labs=response.labs.model_dump(),
        retinal=response.retinal.model_dump() if response.retinal else None,
        risks=response.risk_scores.model_dump(),
        recommendations=[rec.model_dump() for rec in response.recommendations],
        warnings=response.warnings,
    )
    return response


@app.get("/api/history")
def get_history(limit: int = 10) -> dict:
    return {"items": store.fetch_recent(limit=limit)}


async def _read_file(upload: UploadFile) -> bytes:
    file_bytes = await upload.read()
    if len(file_bytes) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large.")
    return file_bytes


def _analyze_retinal(file_bytes: bytes, warnings: list[str]) -> RetinalResult:
    try:
        image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return retinal_analyzer.analyze(image)
    except Exception as exc:  # pragma: no cover - safety net for demo
        warnings.append(f"Retinal analysis failed: {exc}")
        return RetinalResult(
            grade="Unknown",
            findings=[],
            summary="Retinal analysis failed.",
            model_metadata={"error": str(exc)},
        )
