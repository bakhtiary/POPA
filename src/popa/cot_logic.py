import re
from dataclasses import dataclass

from popa.message import CotLogicMessage
from popa.response_parser import VerificationException


class ParserVerifier:
    def parse(self, answer):
        raise NotImplementedError()

class CotLogic:
    def __init__(self, answer_tag_name: str| None):
        self.answer_tag_name = answer_tag_name

    def get_response(self, full_text, parser_verifier):
        if self.answer_tag_name:
            match = re.findall(rf"<{self.answer_tag_name}>(.*?)</{self.answer_tag_name}>", full_text, re.DOTALL)
            if match:
                return self.parse_and_verify(match[-1], parser_verifier)
            else:
                return None, CotLogicMessage(f""" 
Some message was provided but it did not match the {self.answer_tag_name} regex.
If a final answer is being provided, please give it in the <{self.answer_tag_name}>(.*?)</{self.answer_tag_name}> tags."
""")
        else:
            return self.parse_and_verify(full_text, parser_verifier)

    def parse_and_verify(self, message_to_parse: str, parser_verifier) -> tuple:
        try:
            res = parser_verifier.parse(message_to_parse) if parser_verifier else message_to_parse
            return res, None
        except VerificationException as e:
            return None, CotLogicMessage(str(e))

    def get_cot_system_message(self):
        if self.answer_tag_name:
            return f" Provide the final response inside a <{self.answer_tag_name}> </{self.answer_tag_name}> tag."
        else:
            return ""
