from popa.llm_adapter.anthropic import add_cache_control_to_messages


def test_add_cache_control_to_messages_marks_only_last_string_message() -> None:
    messages = [
        {"role": "user", "content": "message-1"},
        {"role": "assistant", "content": "message-2"},
        {"role": "user", "content": "message-3"},
    ]

    result = add_cache_control_to_messages(messages)

    assert result[:2] == messages[:2]
    assert result[2] == {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "message-3",
                "cache_control": {"type": "ephemeral"},
            }
        ],
    }
    assert messages[2] == {"role": "user", "content": "message-3"}


def test_add_cache_control_to_messages_marks_only_last_block_message() -> None:
    messages = [
        {"role": "user", "content": "message-1"},
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "message-2"},
            ],
        },
    ]

    result = add_cache_control_to_messages(messages)

    assert result[0] == messages[0]
    assert result[1] == {
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "message-2",
                "cache_control": {"type": "ephemeral"},
            }
        ],
    }
    assert messages[1] == {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "message-2"},
        ],
    }
