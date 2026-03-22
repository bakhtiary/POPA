
# POPAgent

POPA stands for **Plain Old Procedural Agents**.

The project is inspired by the idea behind **POJOs**: Plain Old Java Objects. POJOs became useful because they pushed back against heavyweight frameworks, hidden conventions, and unnecessary abstractions. Instead of forcing developers to model everything through special containers or framework-specific base classes, POJOs let code stay close to the language itself.

POPA applies the same instinct to agents. In short POPA is an attempt to build agents the way
POJOs encouraged people to build software: with simple, explicit, language-native code first, 
and only as much abstraction as the problem actually needs.

## Installation

POPA requires Python 3.11 or newer.

Install it with `pip`:

```bash
pip install git+https://github.com/bakhtiary/POPA.git@v0.1.0
```

Or install it with `uv`:

```bash
uv add git+https://github.com/bakhtiary/POPA.git@v0.1.0
```

## Examples

See the [examples](./examples) directory for small scripts that show how to define and run POPA agents with normal Python functions.

## Why POPA

A lot of agent tooling starts by introducing a new DSL, a custom runtime model, or a framework-specific abstraction layer. That can make simple things look clever, but it often makes real systems harder to inspect, test, refactor, and maintain.

POPA proposes a more pythonic approach:

- agents should be written as normal Python code
- control flow should be procedural and explicit
- state should be represented with regular Python data structures
- composition should come from functions and modules, not a separate language
- debugging should work with normal Python tools

## The Core Idea

Instead of creating an extra DSL for defining agents, POPA treats an agent as a Plain Old Python Object that can:

1. answer questions asked from it procedurally
2. call different tools or even agents
3. verify and fix tool responses 
4. verify and fix llm responses

That means the agent logic lives where developers already know how to work: in Python files, with Python functions, using Python control flow.

## Why This Matters

Keeping agents "plain old procedural" has practical advantages:

- debug using normal python tools
- less framework lock-in
- better integration with the rest of the code base
- lower cognitive overhead
- easier local reasoning about behavior
- simpler testing and mocking
- easier onboarding for engineers who already know Python
