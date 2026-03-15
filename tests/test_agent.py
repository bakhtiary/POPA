from popa.agent import Agent
from popa.claude_adapter import LlmAdapter
from popa.cot_logic import CotLogic


class FakeAdapter(LlmAdapter):
    def __init__(self, messages):
        self.messages = messages
    async def stream(self, messages):
        for text in self.messages:
            yield text


def test_agent_uses_hello_instruction() -> None:
    agent = Agent("you are an agent designed to say hello to people", adapter=FakeAdapter(["Hello"]), cot_logic=CotLogic(None))

    result = agent.ask("A man arrives what do you say to him?")

    assert result.content == "Hello"


def test_agent_cot_logic() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeAdapter(["let me think", "<final_answer>1300</final_answer>"]),
        cot_logic=CotLogic("final_answer")
    )

    result = agent.ask("what is the sum of 1 to 50?")

    assert result.cot_answer == "1300"
