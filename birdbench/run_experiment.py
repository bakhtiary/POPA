import argparse
import json
import sqlite3
from pathlib import Path

from popa.llm_adapter.builder import create_agent
from popa.response_parser import VerificationException
from popa.tool import DatabaseTool

DATASET_ROOT = Path(__file__).parent

QUERY_DATABASE = DATASET_ROOT / "bird-minidev-XXXXXX/minidev/MINIDEV/mini_dev_sqlite.json"
DB_ROOT   = DATASET_ROOT / "bird-minidev-XXXXXX/minidev/MINIDEV/dev_databases"
OUT_PATH  = DATASET_ROOT / "mini_dev/llm/exp_result/my_predictions.json"

class DatabaseVerifier(object):
    def __init__(self, db_conn: sqlite3.Connection):
        self.db_conn = db_conn

    def parse(self, answer: str):
        try:
            self.db_conn.execute(answer)
            return answer
        except Exception as e:
            raise VerificationException(e)


def my_model(question: str, schema: str, db_conn: sqlite3.Connection) -> str:

    agent = create_agent(system_instructions="""
    You are a database assistant that has access to a sqlite database. 
    Provide concise answers to the questions that you are asked.
    Use the provided database tool to query the database when needed.
    """, tools=[DatabaseTool(db_conn, "sqlite3")]
    )

    agent.ask(f"can you answer this question using the available database tool:{question}")
    result = agent.ask("please give the sql query that provides the correct answer.", parser_verifier=DatabaseVerifier(db_conn))

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BirdBench experiment.")
    parser.add_argument(
        "--select-samples",
        action="append",
        default=[],
        metavar="QUESTION_ID",
        help="Run only the specified question_id values. Repeat the flag or pass a comma-separated list.",
    )
    return parser.parse_args()


def parse_selected_question_ids(raw_values: list[str]) -> set[str]:
    selected_ids: set[str] = set()
    for value in raw_values:
        for item in value.split(","):
            stripped = item.strip()
            if stripped:
                selected_ids.add(stripped)
    return selected_ids


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    samples = json.loads(Path(QUERY_DATABASE).read_text())
    selected_ids = parse_selected_question_ids(args.select_samples)

    if selected_ids:
        samples = [sample for sample in samples if str(sample["question_id"]) in selected_ids]
        missing_ids = selected_ids.difference({str(sample["question_id"]) for sample in samples})
        if missing_ids:
            print(
                "Warning: question_id values not found: "
                + ", ".join(sorted(missing_ids))
            )

    predictions = {}

    for sample in samples:
        db_id    = sample["db_id"]
        q_id     = sample["question_id"]
        question = sample["question"]

        db_path  = f"{DB_ROOT}/{db_id}/{db_id}.sqlite"
        print(db_path)
        conn     = sqlite3.connect(db_path)

        sql = my_model(question, None, conn)
        conn.close()

        predictions[str(q_id)] = f"{sql}\t----- bird -----\t{db_id}"
        print(f"[{q_id}] {db_id}: {sql[:80]}")

    Path(OUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT_PATH).write_text(json.dumps(predictions, indent=2))
    print(f"\nSaved {len(predictions)} predictions to {OUT_PATH}")

if __name__ == "__main__":
    main()
