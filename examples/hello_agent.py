from popa.agent import create_simple_agent

if __name__ == '__main__':
    agent = create_simple_agent("You are a helpful greeter. Great incoming people.")

    result = agent.ask("A man arrives what do you say to him?")

    print(result)