import anthropic

if __name__ == '__main__':
    client = anthropic.Anthropic()

    with client.messages.stream(
        max_tokens=1024,
        system="Use the database tool to answer user questions.",
        messages=[
            {"role": "user", "content": "What tables does the database have?"}
        ],
        tools=[
            {
                "name": "query_database",
                "description": "Execute a SQL query against the sales database.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL query to execute"}
                    },
                    "required": ["sql"]
                }
            }
        ],
        model="claude-opus-4-5",
    ) as stream:
        for event in stream:
            # Stream text as it arrives
            if event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)

            # Capture completed tool use blocks
            elif event.type == "content_block_stop":
                block = stream.current_message_snapshot.content[event.index]
                if block.type == "tool_use":
                    print(f"\n[Tool call: {block.name}]")
                    print(f"[Input: {block.input}]")
                    # Execute your tool here and collect result for follow-up turn

        # After stream ends, get the full final message
        final_message = stream.get_final_message()