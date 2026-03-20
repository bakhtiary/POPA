from collections.abc import AsyncIterator
from typing import Protocol

from anthropic import AsyncAnthropic
from anthropic.types import ToolParam

from popa.message import Message, ToolUseMessage, AssistantMessage, ToolResponseMessage
from popa.tool import ToolDescription, Tool


class LlmAdapter(Protocol):
    def stream(self, system, messages: list[Message], tools: list[ToolDescription]) -> AsyncIterator[str]:
        ...

    def get_previous_response(self):
        ...


class ClaudeAdapter:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.previous_response=None

    def get_previous_response(self):
        return self.previous_response

    async def stream(self, system, messages: list[Message], tools:list[Tool]) -> AsyncIterator[str]:
        cl_msg = popa_messages_to_claude_mapper(messages)
        cl_tools = all_tools_to_claude(tools)

        async with self.client.messages.stream(
            max_tokens=1024,
            model="claude-opus-4-6",
            messages=cl_msg,
            system=system,
            tools=cl_tools,
        ) as stream:
            async for text in stream.text_stream:
                yield text

        final_messages = await stream.get_final_message()

        self.previous_response=[]

        for block in final_messages.content:
            self.previous_response.append(
                claude_to_popa_messages_mapper(block)
            )

from typing import Any

def all_tools_to_claude(tools: list[Tool]) -> list[ToolParam]:
    return [_to_claude_tool(x.get_tool_description()) for x in tools]

def _to_claude_tool(tool: ToolDescription) -> ToolParam:
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
        "name": tool.name,
        "description": tool.description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }

def popa_messages_to_claude_mapper(chat_history):
    messages = []

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
            {   "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": message.id,
                        "name": message.name,
                        "caller": message.caller,
                        "input": message.input,
                    }
                ]
            })

        elif isinstance(message, ToolResponseMessage):
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.id,
                            "content": message.result,
                        }
                    ],
                }
            )


    return messages

def claude_to_popa_messages_mapper(block):
    match block.type:
        case "tool_use":
            return ToolUseMessage(block.name, block.input, block.id, block.caller)
        case "text":
            return AssistantMessage(block.text)
        case _:
            raise NotImplementedError()



