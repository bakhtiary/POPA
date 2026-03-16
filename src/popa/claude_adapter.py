from collections.abc import AsyncIterator
from typing import Protocol

from anthropic import AsyncAnthropic

from popa.message import Message
from popa.tool import Tool


class LlmAdapter(Protocol):
    def stream(self, messages: list[Message]) -> AsyncIterator[str]:
        ...


class ClaudeAdapter:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def stream(self, system, messages: list[Message], tools:list[Tool]) -> AsyncIterator[str]:
        cl_msg = messages_to_claude_mapper(messages)
        cl_tools = tools_claude_mapper(tools)

        async with self.client.messages.stream(
            max_tokens=1024,
            model="claude-opus-4-6",
            messages=cl_msg,
            system=system,
            tools=cl_tools,
        ) as stream:
            async for text in stream.text_stream:
                yield text

def tools_claude_mapper(tools):
    pass

def messages_to_claude_mapper(chat_history):
    messages = []

    for message in chat_history:

        if message.role not in {"user", "assistant"}:
            raise ValueError(f"Unsupported message role: {message.role}")

        messages.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    return messages
