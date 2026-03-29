import os

from popa.llm_adapter.builder import create_agent
from popa.llm_adapter.gemini import GeminiAdapter
from popa.llm_adapter.openai import OpenAIAdapter

if __name__ == '__main__':
    agent = create_agent(adapter=GeminiAdapter(os.environ['VERTEX_API_KEY']))

    result = agent.ask("A man arrives what do you say to him?")

    print(result)