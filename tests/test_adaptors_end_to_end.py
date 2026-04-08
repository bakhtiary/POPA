import os
import sqlite3
import unittest
from pathlib import Path
from unittest import mock

from popa.llm_adapter.builder import create_agent
from popa.tool import DatabaseTool


def read_env_vars_file():
    env_file_text = (Path(__file__).parent.parent / ".env").read_text()
    env_lines = [x.split("=") for x in env_file_text.split("\n")]
    return {x[0]:x[1] for x in env_lines }

@mock.patch.dict(os.environ, read_env_vars_file(), clear=True)
class TestAdaptersEndToEnd(unittest.TestCase):

    def test_happy_path(self):
        agent = create_agent(system_instructions="You are a helpful greeter. What ever the question answer with one word: hello")
        result = agent.ask("A man arrives what do you say to him?")
        self.assertIn("hello", result)

    def test_thinking_before_tool_use(self):
        conn = create_and_fill_memory_database()

        agent = create_agent(system_instructions="""
        You are a database assistant. Provide accurate answers regarding the database provided.
        Always think before you use the tool.
        """, tools=[DatabaseTool(conn, "sqlite3")])
        result = agent.ask("What tables does the database have?")

        self.assertIn("users", result)

    def test_multiple_sql_uses(self):
        conn = create_and_fill_memory_database()

        agent = create_agent(system_instructions="""You are a database assistant. Provide accurate answers regarding the database provided.
        """, tools=[DatabaseTool(conn, "sqlite3")]
        )
        agent.ask("What tables does the database have?")
        result = agent.ask("Which table has a postcode column?")

        self.assertIn("address", result)
        self.assertNotIn("users", result)


def create_and_fill_memory_database():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, login TEXT)")
    conn.execute("CREATE TABLE address (id INTEGER PRIMARY KEY, postcode TEXT)")
    conn.commit()
    return conn
