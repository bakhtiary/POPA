from popa.llm_adapter.interface import LlmAdapter
from popa.message import AssistantMessage


class FakeStreamingAdapter(LlmAdapter):
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


class FakeSimpleStreamingAdapter(LlmAdapter):
    def __init__(self, messages):
        self.previous = None
        self.messages = messages
        self.last_received_messages = None
        self.call_count = 0

    async def stream(self, system, messages, tools):
        self.last_received_messages = messages
        for text in ["some", "random", "text"]:
            yield text

        self.previous = [self.messages[self.call_count]]

        self.call_count += 1

    def get_previous_response(self):
        return self.previous

