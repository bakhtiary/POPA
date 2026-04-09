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
        metavar="START:END",
        help="Run only the sample range specified as start:end, for example 0:10.",
    )
    return parser.parse_args()


def parse_selected_sample_range(raw_value: str | None) -> slice | None:
    if not raw_value:
        return None

    start_text, separator, end_text = raw_value.partition(":")
    if separator != ":":
        raise ValueError(f"Invalid sample range '{raw_value}'. Expected format start:end.")

    try:
        start = int(start_text) if start_text else None
        end = int(end_text) if end_text else None
    except ValueError as exc:
        raise ValueError(f"Invalid sample range '{raw_value}'. Expected format start:end.") from exc

    if start is None and end is None:
        raise ValueError(f"Invalid sample range '{raw_value}'. At least one boundary is required.")
    if start is not None and end is not None and start > end:
        raise ValueError(f"Invalid sample range '{raw_value}'. Start must be less than or equal to end.")

    return slice(start, end)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    samples = json.loads(Path(QUERY_DATABASE).read_text())
    selected_range = parse_selected_sample_range(args.select_samples)

    if selected_range is not None:
        samples = samples[selected_range]

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
