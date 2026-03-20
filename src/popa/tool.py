from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Protocol


@dataclass
class InputParameter:
    type: str
    name: str
    required: bool
    description: str


@dataclass
class ToolDescription:
    name: str
    description: str
    input_schema: List[InputParameter]
    input_examples: Optional[List[Dict[str, Any]]] = None


import sqlite3

class Tool:
    def __init__(self, name):
        self.name = name
    def get_tool_description(self) -> ToolDescription:
        ...

class DatabaseTool(Tool):

    def __init__(self, conn: sqlite3.Connection, name):
        super().__init__(name)
        self.conn = conn

    def get_tool_description(self) -> ToolDescription:
        return ToolDescription(
            name=self.name,
            description=(
                "Execute a SQL query against a database and return the results. "
                "Use this tool to retrieve structured information from the database. "
                "The query must be a valid SQLite SELECT statement. "
                "Do not use INSERT, UPDATE, DELETE, DROP, ALTER, or other statements that modify the database. "
                "Always limit the number of returned rows when possible."
            ),
            input_schema=[
                InputParameter(name="query", type="string", description="The SQL query", required=True),
            ],
            input_examples=[
                {"query": "SELECT Name FROM Artist LIMIT 5"},
                {"query": "SELECT Title FROM Album WHERE ArtistId = 1"},
                {"query": "SELECT COUNT(*) FROM Track"},
            ],
        )

    def run(self, input_):
        try:
            return str(self.conn.execute(input_["query"]).fetchall())
        except Exception as e:
            return str(e)