import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def archive_run_artifacts(
    runs_root: Path,
    predictions_path: Path,
    results_path: Path,
    log_path: Path,
    selected_samples: str | None,
    summary: dict[str, Any],
) -> Path:
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    archived_predictions = run_dir / "predictions.json"
    archived_results = run_dir / "results.json"
    archived_log = run_dir / "run.log"
    metadata_path = run_dir / "metadata.json"

    shutil.copy2(predictions_path, archived_predictions)
    shutil.copy2(results_path, archived_results)
    shutil.copy2(log_path, archived_log)

    metadata = {
        "run_id": run_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "selected_samples": selected_samples,
        "summary": summary,
        "artifacts": {
            "predictions": archived_predictions.name,
            "results": archived_results.name,
            "log": archived_log.name,
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return run_dir
