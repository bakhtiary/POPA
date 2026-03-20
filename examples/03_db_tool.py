import os
import sqlite3
import urllib

from popa.agent import  create_cot_agent
from popa.tool import DatabaseTool


def main():
    conn = _get_chinook_sqlite_db_conn_download_if_it_dont_exist()

    agent = create_cot_agent("""
    You are a database assistant that has access to a chinook sqlite database. 
    Provide concise answers to the questions that you are asked.
    Use the provided database tool to query the database when needed.
    """, tools=[DatabaseTool(conn, "sqlite3")]
    )

    result = agent.ask("how many albums did AC/DC publish?")

    print(result)


def _get_chinook_sqlite_db_conn_download_if_it_dont_exist():
    url = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
    db_path = "chinook.db"

    if not os.path.exists(db_path):
        print("Downloading Chinook database...")
        urllib.request.urlretrieve(url, db_path)

    return sqlite3.connect("chinook.db")



if __name__ == '__main__':
    main()