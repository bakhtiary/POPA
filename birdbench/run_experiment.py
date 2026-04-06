import argparse
import json
import sqlite3
from pathlib import Path

from popa.llm_adapter.builder import create_agent
from popa.tool import DatabaseTool

dataset_root = Path(__file__).parent


DATA_PATH = dataset_root/"bird_mini_dev_data/data/mini_dev_sqlite-00000-of-00001.json"
DB_ROOT   = dataset_root/"mini_dev/mini_dev_data/dev_databases"
OUT_PATH  = dataset_root/"mini_dev/llm/exp_result/my_predictions.json"

# ── Your model (fill this in) ─────────────────────────────────────────────────
def my_model(question: str, schema: str, db_conn: sqlite3.Connection) -> str:

    agent = create_agent(system_instructions="""
    You are a database assistant that has access to a sqlite database. 
    Provide concise answers to the questions that you are asked.
    Use the provided database tool to query the database when needed.
    """, tools=[DatabaseTool(db_conn, "sqlite3")]
    )

    agent.ask("can you answer this question using the available database tool:", question)
    result = agent.ask("please give the sql query that provides the correct answer.")

    return result

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
    schema = "\n".join(row[0] for row in cursor.fetchall())
    conn.close()
    return schema


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
    samples = json.loads(Path(DATA_PATH).read_text())
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
        schema   = get_schema(db_path)
        conn     = sqlite3.connect(db_path)

        try:
            sql = my_model(question, schema, conn)
        except Exception as e:
            print(f"[{q_id}] ERROR: {e}")
            sql = "SELECT 1"  # fallback so eval doesn't crash
        finally:
            conn.close()

        predictions[str(q_id)] = f"{sql}\t----- bird -----\t{db_id}"
        print(f"[{q_id}] {db_id}: {sql[:80]}")

    Path(OUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT_PATH).write_text(json.dumps(predictions, indent=2))
    print(f"\nSaved {len(predictions)} predictions to {OUT_PATH}")

if __name__ == "__main__":
    main()