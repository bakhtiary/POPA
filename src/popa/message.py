class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class UserMessage(Message):
    def __init__(self, text):
        super().__init__("user", text)


class AssistantMessage(Message):
    def __init__(self, text):
        super().__init__("assistant", text)


class InstructionMessage(Message):
    def __init__(self, text):
        super().__init__("system", text)
