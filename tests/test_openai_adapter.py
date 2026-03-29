from popa.llm_adapter.openai import (
    all_tools_to_openai,
    openai_to_popa_messages_mapper,
    popa_messages_to_openai_mapper,
)
from popa.message import AssistantMessage, ToolResponseMessage, ToolUseMessage, UserMessage
from popa.tool import InputParameter, ToolDescription


def test_popa_messages_to_openai_mapper_includes_system_and_tool_history() -> None:
    messages = popa_messages_to_openai_mapper(
        "system instruction",
        [
            UserMessage("hello"),
            AssistantMessage("working"),
            ToolUseMessage("search", {"query": "weather"}, "call_123", None),
            ToolResponseMessage("call_123", "sunny"),
        ],
    )

    assert messages == [
        {"role": "system", "content": "system instruction"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "working"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "search",
                        "arguments": '{"query": "weather"}',
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_123", "content": "sunny"},
    ]


def test_openai_to_popa_messages_mapper_restores_text_and_tool_calls() -> None:
    result = openai_to_popa_messages_mapper(
        {
            "role": "assistant",
            "content": "I will use a tool.",
            "tool_calls": [
                {
                    "id": "call_456",
                    "type": "function",
                    "function": {
                        "name": "search",
                        "arguments": '{"query":"restaurants"}',
                    },
                }
            ],
        }
    )

    assert len(result) == 2
    assert isinstance(result[0], AssistantMessage)
    assert result[0].content == "I will use a tool."
    assert isinstance(result[1], ToolUseMessage)
    assert result[1].name == "search"
    assert result[1].input == {"query": "restaurants"}
    assert result[1].id == "call_456"


def test_all_tools_to_openai_uses_function_tool_schema() -> None:
    class FakeTool:
        def get_tool_description(self) -> ToolDescription:
            return ToolDescription(
                name="lookup_weather",
                description="Look up weather data.",
                input_schema=[
                    InputParameter(
                        name="city",
                        type="string",
                        required=True,
                        description="City name",
                    )
                ],
            )

    result = all_tools_to_openai([FakeTool()])

    assert result == [
        {
            "type": "function",
            "function": {
                "name": "lookup_weather",
                "description": "Look up weather data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name",
                        }
                    },
                    "required": ["city"],
                },
            },
        }
    ]
