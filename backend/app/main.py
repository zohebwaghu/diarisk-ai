from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.schemas import AnalysisResponse, LabParseResult
from app.services.orchestrator import OrchestratorAgent
from app.storage import SQLiteStore

app = FastAPI(title="DiaRisk AI Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()
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
    cognitive_notes: Optional[str] = Form(None),
) -> AnalysisResponse:
    lab_bytes = await _read_file(lab_report)
    retinal_bytes = await _read_file(retinal_image) if retinal_image else None
    result = orchestrator.run(
        lab_filename=lab_report.filename or "lab_report",
        lab_bytes=lab_bytes,
        retinal_bytes=retinal_bytes,
        cognitive_notes=cognitive_notes,
    )

    response = AnalysisResponse(
        labs=result.labs,
        lab_insights=result.lab_insights,
        retinal=result.retinal,
        cognitive=result.cognitive,
        risk_scores=result.risk_scores,
        recommendations=result.recommendations,
        agent_trace=result.agent_trace,
        warnings=result.warnings,
    )
    store.insert_analysis(
        labs=response.labs.model_dump(),
        lab_insights=response.lab_insights.model_dump() if response.lab_insights else None,
        retinal=response.retinal.model_dump() if response.retinal else None,
        cognitive=response.cognitive.model_dump() if response.cognitive else None,
        risks=response.risk_scores.model_dump(),
        recommendations=[rec.model_dump() for rec in response.recommendations],
        agent_trace=[item.model_dump() for item in response.agent_trace],
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
