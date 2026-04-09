import asyncio
from collections.abc import AsyncIterator

from popa.llm_adapter.interface import LlmAdapter
from popa.cot_logic import CotLogic
from popa.message import Message, UserMessage, AssistantMessage, ToolUseMessage, ToolResponseMessage
from popa.tool import ToolDescription


class Agent:
    def __init__(self, instruction: str, adapter: LlmAdapter, cot_logic: CotLogic, tools: list[ToolDescription]) -> None:
        self.adapter: LlmAdapter = adapter
        self.system_instruction = instruction
        self.messages: list[Message] = []
        self.previous_response = None
        self.previous_messages = []
        self.cot_logic: CotLogic = cot_logic
        self.tools = {x.name:x for x in tools}

    async def ask_stream(self, prompt: str, parser_verifier=None) -> AsyncIterator[str]:
        self.previous_messages = []
        self._add_new_message(UserMessage(prompt))

        cot_resp = None
        while not cot_resp:
            async for chunk in self.adapter.stream(self.system_instruction+self.cot_logic.get_cot_system_message(), self.messages, tools=list(self.tools.values())):
                yield chunk

            model_messages = self.adapter.get_previous_response()

            for message in model_messages:
                self._add_new_message(message)
                if isinstance(message, ToolUseMessage):
                    tool_response = self._run_tool(message.name, message.id,message.input)
                    self._add_new_message(tool_response)

            last_message = self.messages[-1]
            if isinstance(last_message, AssistantMessage):
                cot_resp, cot_message = self.cot_logic.get_response(last_message.content, parser_verifier)
                if cot_message:
                    self._add_new_message(cot_message)

        self.previous_response = cot_resp

    def _add_new_message(self, message):
        self.messages.append(message)
        self.previous_messages.append(message)

    async def ask_async(self, prompt: str, parser_verifier=None):
        parts = []
        async for chunk in self.ask_stream(prompt, parser_verifier):
            parts.append(chunk)
        return self.previous_response

    def ask(self, prompt: str, parser_verifier=None):
        return asyncio.run(self.ask_async(prompt, parser_verifier))

    def _run_tool(self, name, id_, input_):
        return ToolResponseMessage(id_, self.tools[name].run(input_))

