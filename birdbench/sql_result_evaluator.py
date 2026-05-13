import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

PREDICTION_DELIMITER = "\t----- bird -----\t"
SKIPPED_PREDICTION = "No sql query generated"


def evaluate_predictions(
    predictions: dict[str, str],
    samples: list[dict[str, Any]],
    db_root: Path,
) -> dict[str, Any]:
    results = []

    for q_id_text, prediction_entry in predictions.items():
        print(q_id_text)
        if  prediction_entry.startswith(SKIPPED_PREDICTION):
            continue

        q_id = int(q_id_text)
        predicted_sql, db_id = parse_prediction_entry(prediction_entry)
        sample = samples[q_id]
        reference_sql = sample["SQL"]
        db_path = db_root / db_id / f"{db_id}.sqlite"

        predicted_result, predicted_error = execute_sql(predicted_sql, db_path)
        reference_result, reference_error = execute_sql(reference_sql, db_path)

        matched = False
        if predicted_error is None and reference_error is None:
            matched = results_match(predicted_result, reference_result)

        results.append(
            {
                "q_id": q_id,
                "question_id": sample["question_id"],
                "db_id": db_id,
                "question": sample["question"],
                "predicted_sql": predicted_sql,
                "reference_sql": reference_sql,
                "predicted_result": rows_to_jsonable(predicted_result),
                "reference_result": rows_to_jsonable(reference_result),
                "predicted_error": predicted_error,
                "reference_error": reference_error,
                "matched": matched,
            }
        )

    matched_count = sum(result["matched"] for result in results)
    evaluated_count = len(results)
    matched_percent = (matched_count / evaluated_count * 100.0) if evaluated_count else 0.0

    return {
        "summary": {
            "evaluated_count": evaluated_count,
            "matched_count": matched_count,
            "matched_percent": matched_percent,
        },
        "results": results,
    }


def write_evaluation_report(report: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def parse_prediction_entry(prediction_entry: str) -> tuple[str, str]:
    sql, separator, db_id = prediction_entry.partition(PREDICTION_DELIMITER)
    if separator != PREDICTION_DELIMITER:
        raise ValueError(f"Invalid prediction entry format: {prediction_entry!r}")
    return sql, db_id


def execute_sql(sql: str, db_path: Path) -> tuple[list[tuple[Any, ...]] | None, str | None]:
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(sql).fetchall()
        return rows, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def results_match(
    left_rows: list[tuple[Any, ...]] | None,
    right_rows: list[tuple[Any, ...]] | None,
) -> bool:
    if left_rows is None or right_rows is None:
        return False
    return Counter(normalize_row(row) for row in left_rows) == Counter(
        normalize_row(row) for row in right_rows
    )


def normalize_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    return tuple(normalize_value(value) for value in row)


def normalize_value(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(normalize_value(item) for item in value)
    return value


def rows_to_jsonable(rows: list[tuple[Any, ...]] | None) -> list[list[Any]] | None:
    if rows is None:
        return None
    return [list(row) for row in rows]
