from __future__ import annotations

from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from popa.message import InstructionMessage


class LlmAdapter:
    async def stream(self, messages: list[InstructionMessage]) -> None:
        raise NotImplementedError()


class ClaudeAdapter(LlmAdapter):
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def stream(self, messages: list[InstructionMessage]) -> AsyncIterator[str]:
        payload = translate_to_claude(messages)

        async with self.client.messages.stream(
            max_tokens=1024,
            messages=payload["messages"],
            model="claude-opus-4-6",
            system=payload["system"],
        ) as stream:
            async for text in stream.text_stream:
                yield text


def translate_to_claude(chat_history):
    system_parts = []
    messages = []

    for message in chat_history:
        if message.role == "system":
            system_parts.append(message.content)
            continue

        if message.role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported message role: {message.role}")

        messages.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    return {
        "system": "\n\n".join(system_parts),
        "messages": messages,
    }
