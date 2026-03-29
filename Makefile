IMAGE ?= popa-example
EXAMPLE ?= 01_hello.py
ENV_FILE ?= .env

.PHONY: run-example

run-example:
	docker buildx build -f examples/Dockerfile -t $(IMAGE) .
	docker run --rm -it -p 8000:8000 \
		--env-file $(ENV_FILE) \
		$(IMAGE) python examples/$(EXAMPLE)
