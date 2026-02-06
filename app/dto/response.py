from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

@dataclass(frozen=True)
class GenerateResponse:
    agent_output: str

    def to_dict(self) -> Dict[str, Any]:
        return{
            "agent_output": self.agent_output
        }