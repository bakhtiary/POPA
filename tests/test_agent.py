from popa.agent import Agent


def test_agent_uses_hello_instruction() -> None:
    agent = Agent("you are an agent designed to say hello to people")

    result = agent.ask("A man arrives what do you say to him?")

    assert result == "Hello."
