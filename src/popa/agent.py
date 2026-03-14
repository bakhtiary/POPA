from __future__ import annotations

from popa import AgentConfig
from popa.agent_config import load_config

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
