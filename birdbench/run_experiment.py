import argparse
import json
import logging
import sqlite3
from pathlib import Path

from observability_tools.run_experiment_viewer_api import build_viewer
from popa.llm_adapter.builder import create_agent
from popa.response_parser import VerificationException
from popa.tool import SqliteDatabaseTool
from run_artifact_store import archive_run_artifacts
from sql_result_evaluator import evaluate_predictions, write_evaluation_report

DATASET_ROOT = Path(__file__).parent/"AlibabaResearch-DAMO-ConvAI-main-bird"/"llm"/"data"

QUERY_DATABASE = DATASET_ROOT / "mini_dev_sqlite.json"
DB_ROOT   = DATASET_ROOT / "dev_databases"
RESULTS_DIRECTORY = Path(__file__).parent / "AlibabaResearch-DAMO-ConvAI-main-bird" / "llm" / "exp_result" / "popa"
RUNS_DIRECTORY = RESULTS_DIRECTORY / "runs"
OUT_PATH  = RESULTS_DIRECTORY / "predict_mini_dev_sqlite.json"
RESULTS_PATH = RESULTS_DIRECTORY / "predict_mini_dev_sqlite_results.json"
LOG_PATH  = RESULTS_DIRECTORY / "run_experiment.log"
VIEWER_PATH = Path(__file__).parent / "observability_tools" / "run_experiment_viewer.html"

logger = logging.getLogger(__name__)

class DatabaseVerifier(object):
    def __init__(self, db_conn: sqlite3.Connection):
        self.db_conn = db_conn

    def parse(self, answer: str):
        try:
            res = self.db_conn.execute(answer)
            error_msg = []
            if "ROUND" in answer:
                error_msg.append("Do not ROUND the result. please provide the raw results without extra processing.")
            if len (res.fetchone()) > 1:
                error_msg.append("The provided sql gives a result with more than one column. The expected sql to the question ask requires exactly one column.")
            if error_msg:
                raise VerificationException(" ".join(error_msg))
            return answer
        except Exception as e:
            raise VerificationException(e)


def my_model(question: str, schema: str, evidence: str, db_conn: sqlite3.Connection) -> str:

    agent = create_agent(system_instructions="""
    You are a database assistant that has access to a sqlite database. 
    You are to provide correct answers to the questions that you are asked. There will be a hint that can help disambiguate the question and guide you towards the correct answer.
    Use the provided database tool to query the database when needed.
    """, tools=[SqliteDatabaseTool(db_conn, "sqlite3")]
    )

    agent.ask(f"Can you answer this question using the available database tool: {question}.\n Hint: {evidence}")
    result = agent.ask("Please give the sql query that provides the correct answer.", parser_verifier=DatabaseVerifier(db_conn))

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


def setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8")],
        force=True,
    )
    import popa.agent
    logging.getLogger(popa.agent.__name__).setLevel(logging.DEBUG)



# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    setup_logging()
    args = parse_args()
    logger.info("Starting BirdBench experiment")
    samples = json.loads(Path(QUERY_DATABASE).read_text())
    selected_range = parse_selected_sample_range(args.select_samples)

    for i, s in enumerate(samples):
        s["q_id"] = i

    if selected_range is not None:
        logger.info("Selected sample range %s:%s (%d samples)", selected_range.start, selected_range.stop, len(samples))
    else:
        logger.info("Running all samples (%d samples)", len(samples))

    predictions = {}

    for sample in  samples:
        db_id    = sample["db_id"]
        q_id     = sample["q_id"]
        question = sample["question"]
        evidence = sample["evidence"]

        if sample in samples[selected_range]:
            db_path  = f"{DB_ROOT}/{db_id}/{db_id}.sqlite"
            logger.info("Running sample question_id=%s db_id=%s db_path=%s", q_id, db_id, db_path)
            conn     = sqlite3.connect(db_path)
            sql = my_model(question, None, evidence, conn)
            conn.close()
        else:
            sql = "No sql query generated"
        predictions[str(q_id)] = f"{sql}\t----- bird -----\t{db_id}"
        logger.info("Completed sample question_id=%s db_id=%s sql=%s", q_id, db_id, sql[:80])

    Path(OUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT_PATH).write_text(json.dumps(predictions, indent=2))
    logger.info("Saved %d predictions to %s", len(predictions), OUT_PATH)
    logger.info("Starting SQL result evaluation")

    evaluation_report = evaluate_predictions(predictions=predictions, samples=samples, db_root=DB_ROOT)
    write_evaluation_report(evaluation_report, RESULTS_PATH)

    summary = evaluation_report["summary"]
    logger.info(
        "Evaluation complete: matched %d/%d (%.2f%%). Report written to %s",
        summary["matched_count"],
        summary["evaluated_count"],
        summary["matched_percent"],
        RESULTS_PATH,
    )
    run_dir = archive_run_artifacts(
        runs_root=RUNS_DIRECTORY,
        predictions_path=OUT_PATH,
        results_path=RESULTS_PATH,
        log_path=LOG_PATH,
        selected_samples=args.select_samples,
        summary=summary,
    )
    logger.info("Archived run artifacts to %s", run_dir)
    viewer_payload = build_viewer(RESULTS_DIRECTORY, VIEWER_PATH)
    logger.info("Viewer refreshed at %s with %d runs", VIEWER_PATH, len(viewer_payload["runs"]))
    logger.info("Experiment log written to %s", LOG_PATH)
    print(
        "SQL result match rate: "
        f"{summary['matched_count']}/{summary['evaluated_count']} "
        f"({summary['matched_percent']:.2f}%)"
    )
    print(f"Run viewer: {VIEWER_PATH}")

if __name__ == "__main__":
    main()
