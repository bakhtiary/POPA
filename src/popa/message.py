class Message:
    def __init__(self, role: str):
        self.role = role

class CotLogicMessage:
    def __init__(self, text):
        super().__init__("cot_logic")
        self.content = text


class UserMessage(Message):
    def __init__(self, text):
        super().__init__("user")
        self.content = text


class AssistantMessage(Message):
    def __init__(self, text):
        super().__init__("assistant")
        self.content = text


class ToolUseMessage(Message):
    def __init__(self, name_, input_, id_, caller):
        super().__init__("tool_use")
        self.name = name_
        self.input = input_
        self.id = id_
        self.caller = caller

class ToolResponseMessage(Message):
    def __init__(self, tool_use_id: str, result: str):
        super().__init__("tool_response")
        self.id = tool_use_id
        self.result = result
