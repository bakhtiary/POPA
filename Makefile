run-01-example:
	docker buildx build -f examples/Dockerfile -t popa-example .
	docker run --rm -e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" popa-example

run-02-example:
	docker buildx build -f examples/Dockerfile -t popa-example .
	docker run -it --rm -p 8000:8000 -e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" popa-example python examples/02_fastapi.py

run-03-example:
	docker buildx build -f examples/Dockerfile -t popa-example .
	docker run --rm -e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" popa-example python examples/03_db_tool.py

run-04-example:
	docker buildx build -f examples/Dockerfile -t popa-example .
	docker run --rm -e OPENAI_API_KEY="$${OPENAI_API_KEY}" popa-example python examples/04_chatgpt.py
