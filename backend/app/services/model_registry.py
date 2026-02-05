from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import torch
from transformers import AutoModel, AutoModelForCausalLM, AutoProcessor, AutoTokenizer

from app import config


@dataclass
class LoadedModels:
    medsiglip_processor: Optional[AutoProcessor] = None
    medsiglip_model: Optional[AutoModel] = None
    medgemma_tokenizer: Optional[AutoTokenizer] = None
    medgemma_model: Optional[AutoModelForCausalLM] = None
    medgemma_processor: Optional[AutoProcessor] = None


class ModelRegistry:
    _instance: Optional["ModelRegistry"] = None

    def __init__(self) -> None:
        self.models = LoadedModels()

    @classmethod
    def instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _resolve_device(self) -> str:
        if config.MODEL_DEVICE != "auto":
            return config.MODEL_DEVICE
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def load_medsiglip(self) -> tuple[AutoProcessor, AutoModel]:
        if self.models.medsiglip_model is not None and self.models.medsiglip_processor is not None:
            return self.models.medsiglip_processor, self.models.medsiglip_model

        device = self._resolve_device()
        processor = AutoProcessor.from_pretrained(
            config.MEDSIGLIP_MODEL_ID,
            local_files_only=config.OFFLINE_ONLY,
        )
        model = AutoModel.from_pretrained(
            config.MEDSIGLIP_MODEL_ID,
            local_files_only=config.OFFLINE_ONLY,
        )
        model.to(device)
        model.eval()

        self.models.medsiglip_processor = processor
        self.models.medsiglip_model = model
        return processor, model

    def load_medgemma_text(self) -> tuple[AutoTokenizer, AutoModelForCausalLM]:
        if self.models.medgemma_model is not None and self.models.medgemma_tokenizer is not None:
            return self.models.medgemma_tokenizer, self.models.medgemma_model

        device = self._resolve_device()
        tokenizer = AutoTokenizer.from_pretrained(
            config.MEDGEMMA_MODEL_ID,
            local_files_only=config.OFFLINE_ONLY,
        )
        model = AutoModelForCausalLM.from_pretrained(
            config.MEDGEMMA_MODEL_ID,
            torch_dtype=torch.float16 if device == "cuda" else None,
            local_files_only=config.OFFLINE_ONLY,
        )
        model.to(device)
        model.eval()

        self.models.medgemma_tokenizer = tokenizer
        self.models.medgemma_model = model
        return tokenizer, model

    def load_medgemma_multimodal(self) -> tuple[AutoProcessor, AutoModelForCausalLM]:
        if self.models.medgemma_model is not None and self.models.medgemma_processor is not None:
            return self.models.medgemma_processor, self.models.medgemma_model

        device = self._resolve_device()
        processor = AutoProcessor.from_pretrained(
            config.MEDGEMMA_MODEL_ID,
            local_files_only=config.OFFLINE_ONLY,
        )
        model = AutoModelForCausalLM.from_pretrained(
            config.MEDGEMMA_MODEL_ID,
            torch_dtype=torch.float16 if device == "cuda" else None,
            local_files_only=config.OFFLINE_ONLY,
        )
        model.to(device)
        model.eval()

        self.models.medgemma_processor = processor
        self.models.medgemma_model = model
        return processor, model
