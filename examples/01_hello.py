from popa.builder import create_agent

if __name__ == '__main__':
    agent = create_agent(system_instructions="You are a helpful greeter. Greet incoming people.")

    result = agent.ask("A man arrives what do you say to him?")

    print(result)