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
        if self.answer_tag_name:
            match = re.search(rf"<{self.answer_tag_name}>(.*?)</{self.answer_tag_name}>", full_text, re.DOTALL)
            if match:
                return CotResponse(full_text, match.group(1))
            else:
                return None
        else:
            return CotResponse(full_text, None)
