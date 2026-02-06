from __future__ import annotations
from typing import Dict
from dataclasses import dataclass
from app.errors import ValidationError


@dataclass(frozen=True)
class GenerateRequest:
    user_input: str

    @staticmethod
    def from_dict(data: Dict[str, any]) -> GenerateRequest:
        user_input = data.get("user_input")

        if not isinstance(user_input, str) or not user_input.strip():
            raise ValidationError("user_input is required and must be a non-empty string")

        return GenerateRequest(user_input=user_input.strip())