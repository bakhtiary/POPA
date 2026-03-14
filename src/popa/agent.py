import asyncio
from collections.abc import AsyncIterator

from popa.agent_config import AgentConfig, load_config
from popa.message import Message, InstructionMessage, UserMessage, AssistantMessage


class Agent:
    def __init__(self, instruction: str, config: AgentConfig | None = None) -> None:
        self.config = config or load_config()
        self.adapter = self.config.get_adapter()
        self.messages: list[Message] = [InstructionMessage(instruction)]

    async def ask_stream(self, prompt: str) -> AsyncIterator[str]:
        self.messages.append(UserMessage(prompt))

        chunks = []

        async for chunk in self.adapter.invoke(self.messages):
            chunks.append(chunk)
            yield chunk

        full_text = "".join(chunks)
        response = AssistantMessage(full_text)
        self.messages.append(response)

    async def ask_async(self, prompt: str) -> str:
        parts = []
        async for chunk in self.ask_stream(prompt):
            parts.append(chunk)
        return "".join(parts)

    def ask(self, prompt: str) -> str:
        return asyncio.run(self.ask_async(prompt))