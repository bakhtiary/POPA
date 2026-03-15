import re
from dataclasses import dataclass


@dataclass
class CotResponse:
    content: str
    cot_answer: str

class CotLogic:
    def __init__(self, answer_tag_name):
        self.answer_tag_name = answer_tag_name

    def get_response(self, full_text):
        match = re.search(rf"<{self.answer_tag_name}>(.*?)</{self.answer_tag_name}>", full_text, re.DOTALL)
        answer = match.group(1) if match else None

        return CotResponse(full_text, answer)
