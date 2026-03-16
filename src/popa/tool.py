
class Tool:
    pass

import sqlite3

class DatabaseTool:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn


