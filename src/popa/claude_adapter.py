from __future__ import annotations

from anthropic import AsyncAnthropic

class ClaudeAdapter:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def stream(self, messages):
        async with self.client.messages.stream(
            max_tokens=1024,
            messages=translate_to_claude(messages),
            model="claude-opus-4-6",
        ) as stream:

            async for text in stream.text_stream:
                yield text

def translate_to_claude(chat_history):
    return []
