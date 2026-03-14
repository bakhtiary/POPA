from __future__ import annotations

from anthropic import AsyncAnthropic

from popa.chat_history import ChatHistory
from popa.message import Message


class ClaudeAdapter:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(
            api_key=api_key,
        )

    async def invoke(self, chat_history : ChatHistory) -> Message:

        message = await self.client.messages.create(
            max_tokens=1024,
            messages=translate_to_claude(chat_history),
            model="claude-opus-4-6",
        )
        return message

def translate_to_claude(chat_history):
    return []
