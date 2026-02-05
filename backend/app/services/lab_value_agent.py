from __future__ import annotations

import re
from typing import List

from app import config
from app.schemas import LabInsights, LabValues
from app.services.llm import TextLLM


class LabValueAgent:
    def __init__(self) -> None:
        self.llm = TextLLM()

    def interpret(self, values: LabValues) -> LabInsights:
        if not config.ENABLE_TEXT_LLM:
            return LabInsights(summary="Lab Value Agent disabled.", flags=["lab_agent_disabled"])

        prompt = self._prompt(values)
        lines = self.llm.generate_lines(prompt, max_new_tokens=192)
        return self._parse(lines)

    def _prompt(self, values: LabValues) -> str:
        return (
            "You are a lab interpretation assistant for diabetes care. "
            "Given these lab values, produce a concise summary and 2-3 highlights. "
            "Return format: Summary: <sentence> | Highlights: <item1>; <item2>; <item3>.\n"
            f"A1C: {values.a1c}\n"
            f"Fasting glucose: {values.fasting_glucose}\n"
            f"eGFR: {values.egfr}\n"
            f"Creatinine: {values.creatinine}\n"
            f"LDL: {values.ldl}\n"
            f"HDL: {values.hdl}\n"
            f"Triglycerides: {values.triglycerides}\n"
            f"Urine albumin: {values.urine_albumin}\n"
            f"Systolic BP: {values.systolic_bp}\n"
            f"Diastolic BP: {values.diastolic_bp}\n"
        )

    def _parse(self, lines: List[str]) -> LabInsights:
        text = " ".join(lines)
        summary = None
        highlights: List[str] = []

        summary_match = re.search(r"summary\s*[:\-]?\s*([^|]+)", text, re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()

        highlights_match = re.search(r"highlights?\s*[:\-]?\s*(.+)$", text, re.IGNORECASE)
        if highlights_match:
            raw = highlights_match.group(1)
            highlights = [item.strip() for item in raw.split(";") if item.strip()]

        if not summary and lines:
            summary = lines[0].strip()
        return LabInsights(summary=summary, highlights=highlights[:3], flags=[])
