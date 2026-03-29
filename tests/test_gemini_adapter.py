from google.genai import types

from popa.llm_adapter.gemini import (
    all_tools_to_gemini,
    gemini_to_popa_messages_mapper,
    popa_messages_to_gemini_mapper,
)
from popa.message import AssistantMessage, ToolResponseMessage, ToolUseMessage, UserMessage
from popa.tool import InputParameter, ToolDescription


def test_popa_messages_to_gemini_mapper_includes_tool_call_and_response() -> None:
    messages = popa_messages_to_gemini_mapper(
        [
            UserMessage("hello"),
            AssistantMessage("working"),
            ToolUseMessage("search", {"query": "weather"}, "call_123", None),
            ToolResponseMessage("call_123", "sunny"),
        ]
    )

    assert messages[0].role == "user"
    assert messages[0].parts[0].text == "hello"
    assert messages[1].role == "model"
    assert messages[1].parts[0].text == "working"
    assert messages[2].role == "model"
    assert messages[2].parts[0].function_call.name == "search"
    assert messages[2].parts[0].function_call.args == {"query": "weather"}
    assert messages[3].role == "user"
    assert messages[3].parts[0].function_response.id == "call_123"
    assert messages[3].parts[0].function_response.name == "search"
    assert messages[3].parts[0].function_response.response == {"result": "sunny"}


def test_gemini_to_popa_messages_mapper_restores_text_and_tool_calls() -> None:
    result = gemini_to_popa_messages_mapper(
        {
            "text": "I will use a tool.",
            "function_calls": [
                {
                    "id": "call_456",
                    "name": "search",
                    "args": {"query": "restaurants"},
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


def test_all_tools_to_gemini_uses_function_declarations() -> None:
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

    result = all_tools_to_gemini([FakeTool()])

    assert len(result) == 1
    assert isinstance(result[0], types.Tool)
    assert len(result[0].function_declarations) == 1
    declaration = result[0].function_declarations[0]
    assert declaration.name == "lookup_weather"
    assert declaration.description == "Look up weather data."
    assert declaration.parameters_json_schema == {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name",
            }
        },
        "required": ["city"],
    }
