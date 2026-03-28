run-01-example:
	docker build -f examples/Dockerfile -t popa-example .
	docker run --rm -e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" popa-example

run-02-example:
	docker build -f examples/Dockerfile -t popa-example .
	docker run --rm -e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" popa-example python examples/02_fastapi.py

run-03-example:
	docker build -f examples/Dockerfile -t popa-example .
	docker run --rm -e ANTHROPIC_API_KEY="$${ANTHROPIC_API_KEY}" popa-example python examples/03_db_tool.py

