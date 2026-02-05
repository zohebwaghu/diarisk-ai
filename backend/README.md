# DiaRisk AI Backend

FastAPI backend for the DiaRisk AI competition demo. This is built to run fully local and offline after model downloads.

## Setup

1) Create a virtual environment and install requirements:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Install system dependencies for OCR (macOS):

```
brew install tesseract poppler
```

3) Run the API:

```
uvicorn app.main:app --reload
```

## Environment Variables

- `MODEL_DEVICE` (default: `auto`) — `cuda`, `mps`, `cpu`, or `auto`
- `MEDGEMMA_MODEL_ID` (default: `google/medgemma-1.5-4b-it`)
- `MEDSIGLIP_MODEL_ID` (default: `google/medsiglip`)
- `ENABLE_RETINAL` (default: `true`) — load multimodal retinal pipeline
- `ENABLE_TEXT_LLM` (default: `true`) — generate recommendations with MedGemma
- `OFFLINE_ONLY` (default: `true`) — disables remote calls at runtime
- `DB_PATH` (default: `backend/data/diarisk.db`) — SQLite path for demo history

## API Endpoints

- `GET /health` — service health
- `POST /api/labs/parse` — parse lab report from PDF/JPG
- `POST /api/analyze` — full analysis (labs + optional retinal)
- `GET /api/history` — last N analysis runs

## Notes

- This backend favors a deterministic risk scoring baseline with LLM-generated recommendations.
- If model weights are not present locally, the API returns a clear error message indicating which model is missing.
