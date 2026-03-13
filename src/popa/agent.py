from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentConfig:
    model_name: str = "gpt-4o"
    temperature: float = 0.7

CONFIG_PATH = Path.home() / ".popaagent_config.yaml"

def load_config() -> AgentConfig:
    if not CONFIG_PATH.exists():
        raise RuntimeError(
            "Agent config not found. Run `agent setup` to create it."
        )

    with open(CONFIG_PATH) as f:
        data = json.load(f)

    return AgentConfig(**data)

class Agent:
    """Minimal plain agent with an instruction and an ask method."""

    def __init__(self, instruction: str, config: AgentConfig | None = None) -> None:
        self.instruction = instruction
        self.config = config or load_config()

    def ask(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        instruction_lower = self.instruction.lower()

        if "hello" in instruction_lower or "say hello" in prompt_lower:
            return "Hello."

        return f"{self.instruction}\n\nUser: {prompt}"
