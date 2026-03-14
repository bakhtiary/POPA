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
            messages=translateToClaude(chat_history),
            model="claude-opus-4-6",
        )
        return message

def translateToClaude(chat_history):
    pass
