from popa.agent import Agent, create_simple_agent

agent = create_simple_agent("You are a helpful greeter. Great incoming people.")

result = agent.ask("A man arrives what do you say to him?")

print(result)