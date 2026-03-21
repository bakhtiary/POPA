import hashlib
import json
import pickle
from collections.abc import AsyncIterator
from pathlib import Path
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

class DiskBasedCacher:
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)

    def get_cached(self, key):
        key_hash = self.md5_of_nested_dict(key)
        if (self.cache_dir/key_hash).exists():
            with open (self.cache_dir/key_hash, "rb") as f:
                return pickle.load(f), key_hash
        return None, key_hash

    def md5_of_nested_dict(self, data: dict) -> str:
        canonical = json.dumps(
            data,
            sort_keys=True,  # ensures dict key order is stable
            separators=(",", ":"),  # removes whitespace differences
            ensure_ascii=False  # optional, but consistent for unicode
        )
        return hashlib.md5(canonical.encode("utf-8")).hexdigest()

    def cache(self, key, text_stream, final_messages):
        with open(self.cache_dir/key, "wb") as f:
            pickle.dump(dict(text_stream= text_stream, final_messages= final_messages), f)

class ClaudeAdapter:
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.previous_response=None
        self.client_cacher = DiskBasedCacher("./cache/claude_adapter")

    def get_previous_response(self):
        return self.previous_response

    async def stream(self, system, messages: list[Message], tools:list[Tool]) -> AsyncIterator[str]:
        cl_msg = popa_messages_to_claude_mapper(messages)
        cl_tools = all_tools_to_claude(tools)

        model_name = "claude-opus-4-6"
        max_tokens = 1024

        cached, key = self.client_cacher.get_cached(dict(max_tokens=max_tokens,
            model=model_name,
            messages=cl_msg,
            system=system,
            tools=cl_tools)
        )

        if not cached:
            text_stream = []
            async with self.client.messages.stream(
                max_tokens=max_tokens,
                model=model_name,
                messages=cl_msg,
                system=system,
                tools=cl_tools,
            ) as stream:
                async for text in stream.text_stream:
                    text_stream.append(text)
                    yield text


            final_messages = await stream.get_final_message()
            self.client_cacher.cache(key, text_stream, final_messages)
        else:
            for text in cached["text_stream"]:
                yield text

            final_messages = cached["final_messages"]

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
                        "caller": {"type":"direct"} if message.caller is None else message.caller,
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
            return ToolUseMessage(block.name, block.input, block.id, None if block.caller.type == "direct" else block.id)
        case "text":
            return AssistantMessage(block.text)
        case _:
            raise NotImplementedError()



