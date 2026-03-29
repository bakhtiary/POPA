from collections.abc import AsyncIterator
from typing import Any

from popa.llm_adapter.local_disk_cache import LocalDiskCache
from popa.message import AssistantMessage, Message, ToolResponseMessage, ToolUseMessage, CotLogicMessage
from popa.tool import Tool, ToolDescription

try:
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover - exercised indirectly by __init__
    genai = None
    types = None


class GeminiAdapter:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-pro"):
        if genai is None or types is None:
            raise ImportError(
                "google-genai is not installed. Install it with "
                "`pip install google-genai` or include it in your project extras."
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.previous_response = None
        self.client_cacher = LocalDiskCache("./cache/gemini_adapter")

    def get_previous_response(self):
        return self.previous_response

    async def stream(self, system, messages: list[Message], tools: list[Tool]) -> AsyncIterator[str]:
        gm_messages = popa_messages_to_gemini_mapper(messages)
        gm_tools = all_tools_to_gemini(tools)
        config = _build_generation_config(system, gm_tools)

        cached, key = self.client_cacher.get_cached(
            dict(
                config=config.model_dump(exclude_none=True),
                contents=[x.model_dump(exclude_none=True) for x in gm_messages],
                model=self.model_name,
            )
        )

        if not cached:
            text_stream: list[str] = []
            final_response = {
                "text": "",
                "function_calls": [],
            }

            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=gm_messages,
                config=config,
            )

            async for chunk in stream:
                if chunk.text:
                    text_stream.append(chunk.text)
                    final_response["text"] += chunk.text
                    yield chunk.text

                for function_call in chunk.function_calls or []:
                    _add_function_call(final_response["function_calls"], function_call)

            self.client_cacher.cache(key, text_stream, final_response)
        else:
            for text in cached["text_stream"]:
                yield text

            final_response = cached["final_messages"]

        self.previous_response = gemini_to_popa_messages_mapper(final_response)


def _build_generation_config(system: str, tools_: list[Any]):
    return types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=1024,
        tools=tools_,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )


def _add_function_call(function_calls: list[dict[str, Any]], function_call: Any) -> None:
    function_call_id = getattr(function_call, "id", None)
    function_call_name = getattr(function_call, "name", None)
    function_call_args = getattr(function_call, "args", None) or {}

    key = (
        function_call_id,
        function_call_name,
        tuple(sorted(function_call_args.items())),
    )
    existing = {
        (
            item.get("id"),
            item.get("name"),
            tuple(sorted((item.get("args") or {}).items())),
        )
        for item in function_calls
    }

    if key not in existing:
        function_calls.append(
            {
                "id": function_call_id,
                "name": function_call_name,
                "args": function_call_args,
            }
        )


def all_tools_to_gemini(tools: list[Tool]) -> list[Any]:
    if not tools:
        return []

    return [
        types.Tool(
            function_declarations=[_to_gemini_tool(x.get_tool_description()) for x in tools]
        )
    ]


def _to_gemini_tool(tool: ToolDescription):
    properties: dict[str, Any] = {}
    required: list[str] = []

    for p in tool.input_schema:
        properties[p.name] = {
            "type": p.type,
            "description": p.description,
        }
        if p.required:
            required.append(p.name)

    return types.FunctionDeclaration(
        name=tool.name,
        description=tool.description,
        parameters_json_schema={
            "type": "object",
            "properties": properties,
            "required": required,
        },
    )


def popa_messages_to_gemini_mapper(chat_history: list[Message]) -> list[Any]:
    messages = []
    tool_use_ids_to_names: dict[str, str] = {}

    for message in chat_history:
        if message.role in {"user", "assistant"}:
            messages.append(
                types.Content(
                    role="model" if message.role == "assistant" else "user",
                    parts=[types.Part.from_text(text=message.content)],
                )
            )
        elif isinstance(message, CotLogicMessage):
            messages.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message.content)],
                )
            )
        elif isinstance(message, ToolUseMessage):
            tool_use_ids_to_names[message.id] = message.name
            messages.append(
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_function_call(
                            name=message.name,
                            args=message.input,
                        )
                    ],
                )
            )
        elif isinstance(message, ToolResponseMessage):
            tool_name = tool_use_ids_to_names.get(message.id)
            if tool_name is None:
                raise ValueError(f"Could not find tool name for tool response id {message.id}")

            messages.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                id=message.id,
                                name=tool_name,
                                response={"result": message.result},
                            )
                        )
                    ],
                )
            )

    return messages


def gemini_to_popa_messages_mapper(response: dict[str, Any]) -> list[Message]:
    result: list[Message] = []

    if response.get("text"):
        result.append(AssistantMessage(response["text"]))

    for index, function_call in enumerate(response.get("function_calls", [])):
        tool_call_id = function_call.get("id") or f"gemini-tool-call-{index}"
        result.append(
            ToolUseMessage(
                function_call["name"],
                function_call.get("args") or {},
                tool_call_id,
                None,
            )
        )

    return result
