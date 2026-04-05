# generate_predictions.py
import json
import sqlite3
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH = "mini_dev/mini_dev_data/mini_dev_sqlite.json"
DB_ROOT   = "mini_dev/mini_dev_data/dev_databases"
OUT_PATH  = "mini_dev/llm/exp_result/my_predictions.json"

# ── Your model (fill this in) ─────────────────────────────────────────────────
def my_model(question: str, schema: str, db_conn: sqlite3.Connection) -> str:

    raise NotImplementedError

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
    schema = "\n".join(row[0] for row in cursor.fetchall())
    conn.close()
    return schema

# ── Main ──────────────────────────────────────────────────────────────────────
samples = json.loads(Path(DATA_PATH).read_text())
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