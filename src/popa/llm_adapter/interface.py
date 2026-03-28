from typing import Protocol, AsyncIterator

from popa.message import Message
from popa.tool import ToolDescription


class LlmAdapter(Protocol):
    def stream(self, system, messages: list[Message], tools: list[ToolDescription]) -> AsyncIterator[str]:
        ...

    def get_previous_response(self):
        ...
