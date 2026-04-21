from typing import cast
from unittest.mock import Mock

from fake_adapters import FakeStreamingAdapter, FakeSimpleStreamingAdapter
from popa.agent import Agent
from popa.cot_logic import CotLogic
from popa.llm_adapter.interface import LlmAdapter
from popa.message import ToolUseMessage, AssistantMessage, ToolResponseMessage
from popa.response_parser import ResponseParser, VerificationException
from popa.tool import Tool


def test_agent_uses_hello_instruction() -> None:
    agent = Agent("you are an agent designed to say hello to people", adapter=FakeStreamingAdapter(["Hello"]), cot_logic=CotLogic(None), tools=[])

    result = agent.ask("A man arrives what do you say to him?")

    assert result == "Hello"


def test_agent_cot_logic() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeStreamingAdapter(["let me think", "<final_answer>1300</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[],
    )

    result = agent.ask("what is the sum of 1 to 50?")

    assert result == "1300"


def test_all_messages_are_passed_to_adapter_once_and_only_once_everytime_the_adapter_is_called() -> None:
    fake_adapter = FakeStreamingAdapter(["let me think"], ["<final_answer>1300</final_answer>"])
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
        adapter=FakeStreamingAdapter(["let me think", "let me think more"], ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    result = agent.ask("what is the sum of 1 to 50?")

    assert result == "42"

def test_verifier_skips_wrong_answer() -> None:
    agent = Agent(
        "you are a master mathematician. Solve the provided question and provide the final answer.",
        adapter=FakeStreamingAdapter(
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
        adapter=FakeStreamingAdapter(
            ["let me think", "let me think more", "<final_answer>forty two</final_answer>"],
            ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    agent.ask("what is the sum of 1 to 50?", IntegerParser("error_message") )

    forty_two_index = list(filter(lambda i: "forty two" in agent.messages[i].content , range(len(agent.messages))))[0]
    assert agent.messages[forty_two_index+1].content == "error_message"


def test_response_verifier_tool() -> None:
    agent = Agent(
        "you are a skillful tool user. the provided tool ",
        adapter=FakeStreamingAdapter(
            ["let me think", "let me think more", "<final_answer>forty two</final_answer>"],
            ["<final_answer>42</final_answer>"]),
        cot_logic=CotLogic("final_answer"),
        tools=[]
    )

    agent.ask("what is the sum of 1 to 50?", IntegerParser("error_message") )

    forty_two_index = list(filter(lambda i: "forty two" in agent.messages[i].content , range(len(agent.messages))))[0]
    assert agent.messages[forty_two_index+1].content == "error_message"

def test_db_tool_output() -> None:
    fake_tool = Mock(Tool)
    fake_tool.run.return_value = "42"
    fake_tool.name = "the_tool"

    fake_adapter = cast(LlmAdapter, Mock(LlmAdapter))
    fake_adapter.get_previous_response.side_effect = [
            [
                ToolUseMessage("the_tool", {"a": "1"}, "123", None),
                AssistantMessage("<final_answer>42</final_answer>"),
            ]
    ]
    async def stream_func(*args, **kwargs):
        yield "let me think"
    fake_adapter.stream = stream_func


    agent = Agent(
        "you are a skillful tool user. the provided tool ",
        adapter=fake_adapter,
        cot_logic=CotLogic("final_answer"),
        tools=[fake_tool]
    )

    agent.ask("what is the sum of 1 to 50?")

    fake_tool.run.assert_called_once_with({"a": "1"})

def test_db_tool_call_with_large_response_then_the_message_is_trimmed() -> None:
    fake_tool = Mock(Tool)
    fake_tool.run.return_value = "t"*10000
    fake_tool.name = "the_tool"

    fake_adapter = FakeSimpleStreamingAdapter(
                [
                    ToolUseMessage("the_tool", {"a": "1"}, "123", None),
                    AssistantMessage("<final_answer>42</final_answer>"),
                ]
    )

    agent = Agent(
        "you are a skillful tool user. the provided tool ",
        adapter=fake_adapter,
        cot_logic=CotLogic("final_answer"),
        tools=[fake_tool]
    )

    agent.ask("what is the sum of 1 to 50?")

    tool_response_message = [x for x in fake_adapter.last_received_messages if isinstance(x, ToolResponseMessage)]
    assert len(tool_response_message) == 1
    assert len(tool_response_message[0].result) < 10000


class IntegerParser(ResponseParser):
    def __init__(self, error_message):
        self.error_message = error_message

    def parse(self, message):
        try:
            return int(message)
        except ValueError:
            raise VerificationException(self.error_message)


