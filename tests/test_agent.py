from popa.agent import Agent
from popa.claude_adapter import LlmAdapter


class FakeAdapter(LlmAdapter):
    async def stream(self, messages):
        for text in ["Hello"]:
            yield text


def test_agent_uses_hello_instruction() -> None:
    agent = Agent("you are an agent designed to say hello to people", adapter=FakeAdapter())

    result = agent.ask("A man arrives what do you say to him?")

    assert result == "Hello"
