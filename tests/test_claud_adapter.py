from popa.agent import Agent
from popa.claude_adapter import translate_to_claude
from popa.message import AssistantMessage, InstructionMessage, UserMessage


def test_translate_to_claude_separates_system_from_messages() -> None:
    payload = translate_to_claude(
        [
            InstructionMessage("You are concise."),
            UserMessage("Hello"),
            AssistantMessage("Hi"),
        ]
    )

    assert payload == {
        "system": "You are concise.",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ],
    }
