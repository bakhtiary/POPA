from typing import Protocol, AsyncIterator

from popa.message import Message
from popa.tool import Tool


class LlmAdapter(Protocol):
    def stream(self, system: str, messages: list[Message], tools: list[Tool]) -> AsyncIterator[str]:
        ...

    def get_previous_response(self):
        ...
