from __future__ import annotations

import io
import re
from typing import Tuple

from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract

from app.schemas import LabParseResult, LabValues


class LabParser:
    def parse(self, filename: str, file_bytes: bytes) -> LabParseResult:
        text = self._extract_text(filename, file_bytes)
        values, missing, flags = self._extract_values(text)
        return LabParseResult(values=values, raw_text=text, missing_fields=missing, quality_flags=flags)

    def _extract_text(self, filename: str, file_bytes: bytes) -> str:
        lowered = filename.lower()
        if lowered.endswith(".pdf"):
            pages = convert_from_bytes(file_bytes)
            return "\n".join(self._ocr_image(page) for page in pages)
        image = Image.open(io.BytesIO(file_bytes))
        return self._ocr_image(image)

    def _ocr_image(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image)

    def _extract_values(self, text: str) -> Tuple[LabValues, list[str], list[str]]:
        values = LabValues()
        missing: list[str] = []
        flags: list[str] = []

        lines = [self._normalize_line(line) for line in text.splitlines() if line.strip()]

        def find_value(labels: list[str], value_pattern: str, units: list[str] | None = None) -> float | None:
            for line in lines:
                if not any(re.search(label, line, re.IGNORECASE) for label in labels):
                    continue
                pattern = value_pattern
                if units:
                    unit_pattern = r"(?:\s*(?:" + "|".join(units) + r"))?"
                    pattern = value_pattern + unit_pattern
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return float(match.group(1))
            return None

        def find_bp() -> tuple[float | None, float | None]:
            for line in lines:
                if not re.search(r"\b(bp|blood pressure)\b", line, re.IGNORECASE):
                    continue
                match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", line)
                if match:
                    return float(match.group(1)), float(match.group(2))
            return None, None

        values.a1c = find_value(
            labels=[r"\ba1c\b", r"hemoglobin a1c", r"hba1c"],
            value_pattern=r"(\d+(?:\.\d+)?)\s*%?",
            units=[r"%"],
        )
        values.fasting_glucose = find_value(
            labels=[r"fasting glucose", r"glucose, fasting", r"\bfpg\b"],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"mg/dl", r"mmol/l"],
        )
        values.egfr = find_value(
            labels=[r"\begfr\b", r"estimated gfr"],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"ml/min", r"ml/min/1\.73", r"ml/min/1\.73m2"],
        )
        values.creatinine = find_value(
            labels=[r"creatinine", r"serum creatinine"],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"mg/dl", r"umol/l"],
        )
        values.ldl = find_value(
            labels=[r"\bldl\b", r"ldl cholesterol"],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"mg/dl", r"mmol/l"],
        )
        values.hdl = find_value(
            labels=[r"\bhdl\b", r"hdl cholesterol"],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"mg/dl", r"mmol/l"],
        )
        values.triglycerides = find_value(
            labels=[r"triglycerides", r"\btg\b"],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"mg/dl", r"mmol/l"],
        )
        values.urine_albumin = find_value(
            labels=[
                r"albumin/creatinine ratio",
                r"urine albumin",
                r"\bacr\b",
            ],
            value_pattern=r"(\d+(?:\.\d+)?)",
            units=[r"mg/g", r"mg\/g", r"mg/mmol"],
        )

        systolic, diastolic = find_bp()
        values.systolic_bp = systolic
        values.diastolic_bp = diastolic

        self._add_range_flags(values, flags)

        for field_name, value in values.model_dump().items():
            if value is None:
                missing.append(field_name)

        if len(text.strip()) < 50:
            flags.append("low_text_confidence")

        return values, missing, flags

    def _normalize_line(self, line: str) -> str:
        return re.sub(r"\s+", " ", line).strip()

    def _add_range_flags(self, values: LabValues, flags: list[str]) -> None:
        ranges = {
            "a1c": (3.0, 15.0),
            "fasting_glucose": (40.0, 500.0),
            "egfr": (5.0, 200.0),
            "creatinine": (0.2, 15.0),
            "ldl": (20.0, 400.0),
            "hdl": (10.0, 120.0),
            "triglycerides": (20.0, 1000.0),
            "urine_albumin": (0.0, 1000.0),
            "systolic_bp": (70.0, 250.0),
            "diastolic_bp": (40.0, 150.0),
        }
        for field, bounds in ranges.items():
            value = getattr(values, field)
            if value is None:
                continue
            lower, upper = bounds
            if value < lower or value > upper:
                flags.append(f"out_of_range_{field}")
