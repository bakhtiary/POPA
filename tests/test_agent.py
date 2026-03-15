from popa.agent import Agent
from popa.claude_adapter import LlmAdapter
from popa.cot_logic import CotLogic


class FakeAdapter(LlmAdapter):
    def __init__(self, messages, messages2=None):
        self.messages = messages
        self.messages2 = messages2
        self.call_count = 0
    async def stream(self, messages):
        self.call_count += 1
        if self.call_count == 1:
            for text in self.messages:
                yield text
        else:
            for text in self.messages2:
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

def test_agent_cot_logic_tries_until_it_gets_an_answer() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeAdapter(["let me think", "let me think more"], ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer")
    )

    result = agent.ask("what is the sum of 1 to 50?")

    assert result.cot_answer == "42"
