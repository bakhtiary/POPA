from fastapi import FastAPI
from pydantic import BaseModel

from popa.agent import Agent, create_simple_agent

app = FastAPI(title="POPA FastAPI Example")


class AskRequest(BaseModel):
    prompt: str


class AskResponse(BaseModel):
    result: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    agent = create_simple_agent("you are an agent designed to say hello to people")
    return AskResponse(result=agent.ask(request.prompt).content)
