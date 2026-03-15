import asyncio
from collections.abc import AsyncIterator

from popa.claude_adapter import LlmAdapter
from popa.cot_logic import CotLogic
from popa.message import Message, InstructionMessage, UserMessage, AssistantMessage


class Agent:
    def __init__(self, instruction: str, adapter: LlmAdapter, cot_logic: CotLogic) -> None:
        self.adapter: LlmAdapter = adapter
        self.messages: list[Message] = [InstructionMessage(instruction)]
        self.previous_response = None
        self.cot_logic = cot_logic

    async def ask_stream(self, prompt: str) -> AsyncIterator[str]:
        self.messages.append(UserMessage(prompt))

        chunks = []

        async for chunk in self.adapter.stream(self.messages):
            chunks.append(chunk)
            yield chunk

        full_text = "".join(chunks)
        assistantMessage = AssistantMessage(full_text)
        self.messages.append(assistantMessage)

        self.previous_response = self.cot_logic.get_response(full_text)

    async def ask_async(self, prompt: str) -> str:
        parts = []
        async for chunk in self.ask_stream(prompt):
            parts.append(chunk)
        return self.previous_response

    def ask(self, prompt: str) -> str:
        return asyncio.run(self.ask_async(prompt))