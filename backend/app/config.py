import os


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None and value != "" else default


MODEL_DEVICE = _get_env("MODEL_DEVICE", "auto")
MEDGEMMA_MODEL_ID = _get_env("MEDGEMMA_MODEL_ID", "google/medgemma-1.5-4b-it")
MEDSIGLIP_MODEL_ID = _get_env("MEDSIGLIP_MODEL_ID", "google/medsiglip")

ENABLE_RETINAL = _get_env("ENABLE_RETINAL", "true").lower() == "true"
ENABLE_TEXT_LLM = _get_env("ENABLE_TEXT_LLM", "true").lower() == "true"
OFFLINE_ONLY = _get_env("OFFLINE_ONLY", "true").lower() == "true"

MAX_UPLOAD_MB = int(_get_env("MAX_UPLOAD_MB", "25"))
DB_PATH = _get_env("DB_PATH", "backend/data/diarisk.db")
