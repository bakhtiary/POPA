from fastapi import FastAPI
from pydantic import BaseModel

from popa import Agent, AgentConfig


app = FastAPI(title="POPA FastAPI Example")
agent = Agent(
    "you are an agent designed to say hello to people",
    config=AgentConfig(model_name="demo", temperature=0.0),
)


class AskRequest(BaseModel):
    prompt: str


class AskResponse(BaseModel):
    result: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    return AskResponse(result=agent.ask(request.prompt))
