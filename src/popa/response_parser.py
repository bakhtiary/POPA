from typing import Protocol


class VerificationException(Exception):
    def __init__(self, message):
        super().__init__(message)

class ResponseParser(Protocol):
    def parse(self, message: str):
        ...