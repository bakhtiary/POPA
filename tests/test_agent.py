from popa.agent import Agent
from popa.claude_adapter import LlmAdapter
from popa.cot_logic import CotLogic
from popa.message import AssistantMessage
from popa.response_parser import ResponseParser, VerificationException


class FakeAdapter(LlmAdapter):
    def __init__(self, messages1, messages2=None):
        self.previous = None
        self.messages1 = messages1
        self.messages2 = messages2
        self.call_count = 0
        self.calls = []
    async def stream(self, system, messages, tools):
        self.calls.append(messages)
        self.call_count += 1
        message = ""
        if self.call_count == 1:
            for text in self.messages1:
                message += text
                yield text
        else:
            for text in self.messages2:
                message += text
                yield text

        self.previous = [AssistantMessage(message)]



    def get_previous_response(self):
        return self.previous


def test_agent_uses_hello_instruction() -> None:
    agent = Agent("you are an agent designed to say hello to people", adapter=FakeAdapter(["Hello"]), cot_logic=CotLogic(None), tools=[])

    result = agent.ask("A man arrives what do you say to him?")

    assert result == "Hello"


def test_agent_cot_logic() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeAdapter(["let me think", "<final_answer>1300</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[],
    )

    result = agent.ask("what is the sum of 1 to 50?")

    assert result == "1300"


def test_all_messages_are_passed_to_adapter_once_and_only_once_everytime_the_adapter_is_called() -> None:
    fake_adapter = FakeAdapter(["let me think"], ["<final_answer>1300</final_answer>"])
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=fake_adapter,
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    agent.ask("what is the sum of 1 to 50?")

    assert len([x for x in fake_adapter.calls[-1] if fake_adapter.messages1[0] in x.content]) == 1


def test_agent_cot_logic_tries_until_it_gets_an_answer() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeAdapter(["let me think", "let me think more"], ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    result = agent.ask("what is the sum of 1 to 50?")

    assert result == "42"

def test_verifier_skips_wrong_answer() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeAdapter(
            ["let me think", "let me think more", "<final_answer>forty two</final_answer>"],
            ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    result = agent.ask("what is the sum of 1 to 50?", IntegerParser("") )

    assert result == 42

def test_verifier_message_is_added_to_messages() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeAdapter(
            ["let me think", "let me think more", "<final_answer>forty two</final_answer>"],
            ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    agent.ask("what is the sum of 1 to 50?", IntegerParser("error_message") )

    forty_two_index = list(filter(lambda i: "forty two" in agent.messages[i].content , range(len(agent.messages))))[0]
    assert agent.messages[forty_two_index+1].content == "error_message"


def test_db_tool() -> None:
    agent = Agent(
        "you are a skillful tool user. the provided tool ",
        adapter=FakeAdapter(
            ["let me think", "let me think more", "<final_answer>forty two</final_answer>"],
            ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    agent.ask("what is the sum of 1 to 50?", IntegerParser("error_message") )

    forty_two_index = list(filter(lambda i: "forty two" in agent.messages[i].content , range(len(agent.messages))))[0]
    assert agent.messages[forty_two_index+1].content == "error_message"


class IntegerParser(ResponseParser):
    def __init__(self, error_message):
        self.error_message = error_message

    def parse(self, message):
        try:
            return int(message)
        except ValueError:
            raise VerificationException(self.error_message)
