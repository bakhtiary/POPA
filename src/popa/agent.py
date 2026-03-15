import asyncio
from collections.abc import AsyncIterator

from popa.agent_config import load_config
from popa.claude_adapter import LlmAdapter
from popa.cot_logic import CotLogic, CotResponse
from popa.message import Message, InstructionMessage, UserMessage, AssistantMessage


class Agent:
    def __init__(self, instruction: str, adapter: LlmAdapter, cot_logic: CotLogic) -> None:
        self.adapter: LlmAdapter = adapter
        self.messages: list[Message] = [InstructionMessage(instruction)]
        self.previous_response: CotResponse = None
        self.cot_logic: CotLogic = cot_logic

    async def ask_stream(self, prompt: str, parser_verifier=None) -> AsyncIterator[str]:
        self.messages.append(UserMessage(prompt))

        chunks = []

        cot_resp = None
        while not cot_resp:
            async for chunk in self.adapter.stream(self.messages):
                chunks.append(chunk)
                yield chunk

            full_text = "".join(chunks)

            self.messages.append(AssistantMessage(full_text))

            cot_resp, cot_message = self.cot_logic.get_response(full_text, parser_verifier)


        self.previous_response = cot_resp

    async def ask_async(self, prompt: str, parser_verifier=None) -> CotResponse:
        parts = []
        async for chunk in self.ask_stream(prompt, parser_verifier):
            parts.append(chunk)
        return self.previous_response

    def ask(self, prompt: str, parser_verifier=None) -> CotResponse:
        return asyncio.run(self.ask_async(prompt, parser_verifier))

def create_simple_agent(system_instructions: str) -> Agent:
    return Agent(system_instructions, load_config().get_adapter(), CotLogic(None))

def create_cot_agent(system_instructions: str) -> Agent:
    return Agent(system_instructions, load_config().get_adapter(), CotLogic("final_answer"))