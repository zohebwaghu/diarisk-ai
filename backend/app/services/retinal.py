from __future__ import annotations

import re
from typing import List, Optional

from PIL import Image

from app import config
from app.schemas import RetinalResult
from app.services.model_registry import ModelRegistry


class RetinalAnalyzer:
    def __init__(self) -> None:
        self.registry = ModelRegistry.instance()

    def analyze(self, image: Image.Image) -> RetinalResult:
        if not config.ENABLE_RETINAL:
            return RetinalResult(
                grade="Not Analyzed",
                findings=[],
                summary="Retinal analysis disabled.",
                model_metadata={"enabled": False},
            )

        embedding_summary = self._medsiglip_embedding_summary(image)
        grade, confidence, findings, narrative = self._medgemma_grade(image)

        summary = narrative or embedding_summary
        model_metadata = {
            "medsiglip": config.MEDSIGLIP_MODEL_ID,
            "medgemma": config.MEDGEMMA_MODEL_ID,
        }
        return RetinalResult(
            grade=grade,
            confidence=confidence,
            findings=findings,
            summary=summary,
            model_metadata=model_metadata,
        )

    def _medsiglip_embedding_summary(self, image: Image.Image) -> str:
        try:
            processor, model = self.registry.load_medsiglip()
            inputs = processor(images=image, return_tensors="pt")
            device = next(model.parameters()).device
            inputs = {key: value.to(device) for key, value in inputs.items()}
            outputs = model(**inputs)
            embedding = getattr(outputs, "pooler_output", None)
            if embedding is None:
                return "Unable to derive embedding from MedSigLIP output."
            return "Retinal embedding generated locally."
        except Exception as exc:  # pragma: no cover - demo safety
            return f"MedSigLIP embedding failed: {exc}"

    def _medgemma_grade(
        self, image: Image.Image
    ) -> tuple[str, Optional[float], List[str], Optional[str]]:
        try:
            processor, model = self.registry.load_medgemma_multimodal()
            device = next(model.parameters()).device
            prompt = self._build_prompt(processor)
            inputs = processor(text=prompt, images=image, return_tensors="pt")
            inputs = {key: value.to(device) for key, value in inputs.items()}
            output_ids = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                temperature=0.0,
            )
            decoded = processor.tokenizer.decode(output_ids[0], skip_special_tokens=True)
            return self._parse_response(decoded)
        except Exception as exc:  # pragma: no cover - demo safety
            return "Unknown", None, [], f"MedGemma grading failed: {exc}"

    def _build_prompt(self, processor) -> str:
        prompt = (
            "You are a retinal imaging specialist using MedGemma. Analyze this fundus "
            "photograph for signs of diabetic retinopathy. Identify and describe: "
            "microaneurysms, hemorrhages, hard exudates, cotton wool spots, "
            "venous beading, neovascularization, and macular involvement. "
            "Provide: overall grade (None / Mild NPDR / Moderate NPDR / Severe NPDR / PDR), "
            "confidence score (0-100%), and a patient-friendly summary. "
            "Output format: Grade: <grade> | Confidence: <0-100> | Summary: <text>."
        )

        tokenizer = getattr(processor, "tokenizer", processor)
        apply_chat_template = getattr(tokenizer, "apply_chat_template", None)
        if callable(apply_chat_template):
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image"},
                    ],
                }
            ]
            try:
                return apply_chat_template(messages, add_generation_prompt=True)
            except TypeError:
                return apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

        return f"<image>\n{prompt}"

    def _parse_response(
        self, text: str
    ) -> tuple[str, Optional[float], List[str], Optional[str]]:
        grade = "Unknown"
        confidence = None
        findings: List[str] = []
        summary = None

        grade_match = re.search(
            r"(None|Mild NPDR|Moderate NPDR|Severe NPDR|PDR)",
            text,
            re.IGNORECASE,
        )
        if grade_match:
            grade = grade_match.group(1)

        conf_match = re.search(r"confidence\s*[:\-]?\s*(\d{1,3})", text, re.IGNORECASE)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except ValueError:
                confidence = None

        for keyword in [
            "microaneurysm",
            "hemorrhage",
            "hard exudate",
            "cotton wool",
            "venous beading",
            "neovascularization",
            "macular",
        ]:
            if re.search(keyword, text, re.IGNORECASE):
                findings.append(keyword)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            summary = lines[-1]

        return grade, confidence, findings[:5], summary
