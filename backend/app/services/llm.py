from __future__ import annotations

from typing import List

import torch

from app.services.model_registry import ModelRegistry


class TextLLM:
    def __init__(self) -> None:
        self.registry = ModelRegistry.instance()

    def generate(self, prompt: str, max_new_tokens: int = 512) -> str:
        tokenizer, model = self.registry.load_medgemma_text()
        device = next(model.parameters()).device

        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=0.0,
            )
        decoded = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return decoded

    def generate_lines(self, prompt: str, max_new_tokens: int = 512) -> List[str]:
        text = self.generate(prompt, max_new_tokens=max_new_tokens)
        return [line.strip() for line in text.splitlines() if line.strip()]
