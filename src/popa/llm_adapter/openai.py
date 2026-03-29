import json
from collections.abc import AsyncIterator
from typing import Any

from popa.llm_adapter.local_disk_cache import LocalDiskCache
from popa.message import AssistantMessage, Message, ToolResponseMessage, ToolUseMessage
from popa.tool import Tool, ToolDescription

try:
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover - exercised indirectly by __init__
    AsyncOpenAI = None


class OpenAIAdapter:
    def __init__(self, api_key: str, model_name: str = "gpt-4.1"):
        if AsyncOpenAI is None:
            raise ImportError(
                "openai is not installed. Install it with `pip install openai` "
                "or include it in your project extras."
            )

        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model_name
        self.previous_response = None
        self.client_cacher = LocalDiskCache("./cache/openai_adapter")

    def get_previous_response(self):
        return self.previous_response

    async def stream(self, system, messages: list[Message], tools: list[Tool]) -> AsyncIterator[str]:
        oa_messages = popa_messages_to_openai_mapper(system, messages)
        oa_tools = all_tools_to_openai(tools)
        max_completion_tokens = 1024

        cached, key = self.client_cacher.get_cached(
            dict(
                max_completion_tokens=max_completion_tokens,
                messages=oa_messages,
                model=self.model_name,
                tools=oa_tools,
            )
        )

        if not cached:
            text_stream: list[str] = []
            final_message = {
                "content": "",
                "role": "assistant",
                "tool_calls": [],
            }

            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=oa_messages,
                tools=oa_tools or None,
                max_completion_tokens=max_completion_tokens,
                stream=True,
            )

            async for chunk in stream:
                for choice in chunk.choices:
                    delta = choice.delta

                    if delta.content:
                        text_stream.append(delta.content)
                        final_message["content"] += delta.content
                        yield delta.content

                    if not delta.tool_calls:
                        continue

                    for tool_call_delta in delta.tool_calls:
                        tc = _ensure_tool_call_slot(final_message["tool_calls"], tool_call_delta.index)

                        if tool_call_delta.id:
                            tc["id"] = tool_call_delta.id

                        if tool_call_delta.function and tool_call_delta.function.name:
                            tc["function"]["name"] = tool_call_delta.function.name

                        if tool_call_delta.function and tool_call_delta.function.arguments:
                            tc["function"]["arguments"] += tool_call_delta.function.arguments

            self.client_cacher.cache(key, text_stream, final_message)
        else:
            for text in cached["text_stream"]:
                yield text

            final_message = cached["final_messages"]

        self.previous_response = openai_to_popa_messages_mapper(final_message)


def _ensure_tool_call_slot(tool_calls: list[dict[str, Any]], index: int) -> dict[str, Any]:
    while len(tool_calls) <= index:
        tool_calls.append(
            {
                "id": None,
                "type": "function",
                "function": {"name": "", "arguments": ""},
            }
        )

    return tool_calls[index]


def all_tools_to_openai(tools: list[Tool]) -> list[dict[str, Any]]:
    return [_to_openai_tool(x.get_tool_description()) for x in tools]


def _to_openai_tool(tool: ToolDescription) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for p in tool.input_schema:
        properties[p.name] = {
            "type": p.type,
            "description": p.description,
        }
        if p.required:
            required.append(p.name)

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def popa_messages_to_openai_mapper(system: str, chat_history: list[Message]) -> list[dict[str, Any]]:
    messages = [{"role": "system", "content": system}]

    for message in chat_history:
        if message.role in {"user", "assistant"}:
            messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )
        elif message.role == "cot_logic":
            messages.append(
                {
                    "role": "user",
                    "content": message.content,
                }
            )
        elif isinstance(message, ToolUseMessage):
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": message.id,
                            "type": "function",
                            "function": {
                                "name": message.name,
                                "arguments": json.dumps(message.input),
                            },
                        }
                    ],
                }
            )
        elif isinstance(message, ToolResponseMessage):
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": message.id,
                    "content": message.result,
                }
            )

    return messages


def openai_to_popa_messages_mapper(message: dict[str, Any]) -> list[Message]:
    result: list[Message] = []

    if message.get("content"):
        result.append(AssistantMessage(message["content"]))

    for tool_call in message.get("tool_calls", []):
        arguments = tool_call["function"]["arguments"]
        result.append(
            ToolUseMessage(
                tool_call["function"]["name"],
                json.loads(arguments) if arguments else {},
                tool_call["id"],
                None,
            )
        )

    return result
