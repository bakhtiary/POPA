from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from popa.builder import create_agent

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
    agent = create_agent(system_instructions="you are an agent designed to say hello to people")
    return AskResponse(result=agent.ask(request.prompt).content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
