import re
from dataclasses import dataclass

from popa.message import CotMessage
from popa.response_parser import VerificationException


@dataclass
class CotResponse:
    content: str
    cot_answer: str


class CotLogic:
    def __init__(self, answer_tag_name):
        self.answer_tag_name = answer_tag_name

    def get_response(self, full_text, parser_verifier):
        if self.answer_tag_name:
            match = re.findall(rf"<{self.answer_tag_name}>(.*?)</{self.answer_tag_name}>", full_text, re.DOTALL)
            if match:
                try:
                    res = parser_verifier.parse(match[-1]) if parser_verifier else match[-1]
                except VerificationException as e:
                    return None, CotMessage(str(e))
                return CotResponse(full_text, res), None
            else:
                return None, None
        else:
            return CotResponse(full_text, None), None
