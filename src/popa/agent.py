from __future__ import annotations


class Agent:
    """Minimal plain agent with an instruction and an ask method."""

    def __init__(self, instruction: str) -> None:
        self.instruction = instruction

    def ask(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        instruction_lower = self.instruction.lower()

        if "hello" in instruction_lower or "say hello" in prompt_lower:
            return "Hello."

        return f"{self.instruction}\n\nUser: {prompt}"
