import json
import re
from pathlib import Path
from typing import Any

LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) "
    r"(?P<level>[A-Z]+) "
    r"\[(?P<logger>[^\]]+)\] "
    r"(?P<message>.*)$"
)


def build_viewer(results_root: Path, output_path: Path) -> dict[str, Any]:
    payload = {"runs": load_runs(results_root)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_html(payload), encoding="utf-8")
    return payload


def load_runs(results_root: Path) -> list[dict[str, Any]]:
    runs_root = results_root / "runs"
    run_entries = []

    if runs_root.exists():
        for run_dir in sorted((path for path in runs_root.iterdir() if path.is_dir()), reverse=True):
            metadata_path = run_dir / "metadata.json"
            results_path = run_dir / "results.json"
            log_path = run_dir / "run.log"
            if not metadata_path.exists() or not results_path.exists() or not log_path.exists():
                continue
            run_entries.append(load_run_entry(metadata_path, results_path, log_path))

    if not run_entries:
        latest_results = results_root / "predict_mini_dev_sqlite_results.json"
        latest_log = results_root / "run_experiment.log"
        if latest_results.exists() and latest_log.exists():
            run_entries.append(load_latest_run_entry(latest_results, latest_log))

    return run_entries


def load_run_entry(metadata_path: Path, results_path: Path, log_path: Path) -> dict[str, Any]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    results_payload = json.loads(results_path.read_text(encoding="utf-8"))
    return {
        "run_id": metadata["run_id"],
        "title": metadata["run_id"],
        "created_at": metadata.get("created_at"),
        "selected_samples": metadata.get("selected_samples"),
        "summary": results_payload.get("summary", metadata.get("summary", {})),
        "results": results_payload.get("results", []),
        "logs": parse_log_lines(log_path.read_text(encoding="utf-8")),
    }


def load_latest_run_entry(results_path: Path, log_path: Path) -> dict[str, Any]:
    results_payload = json.loads(results_path.read_text(encoding="utf-8"))
    created_at = results_path.stat().st_mtime
    return {
        "run_id": "latest",
        "title": "latest",
        "created_at": created_at,
        "selected_samples": None,
        "summary": results_payload.get("summary", {}),
        "results": results_payload.get("results", []),
        "logs": parse_log_lines(log_path.read_text(encoding="utf-8")),
    }


def parse_log_lines(log_text: str) -> list[dict[str, str]]:
    entries = []
    for line in log_text.splitlines():
        match = LOG_PATTERN.match(line)
        if match:
            entries.append(match.groupdict())
        else:
            entries.append(
                {
                    "timestamp": "",
                    "level": "",
                    "logger": "",
                    "message": line,
                }
            )
    return entries


def render_html(payload: dict[str, Any]) -> str:
    data_json = json.dumps(payload).replace("</", "<\\/")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BirdBench Run Viewer</title>
  <style>
    :root {{
      --bg: #f3efe4;
      --panel: rgba(255, 252, 247, 0.9);
      --panel-strong: #fffaf2;
      --ink: #102542;
      --muted: #6d7a8a;
      --accent: #e85d04;
      --accent-soft: rgba(232, 93, 4, 0.12);
      --line: rgba(16, 37, 66, 0.12);
      --ok: #2a9d8f;
      --bad: #b42318;
      --shadow: 0 22px 60px rgba(30, 41, 59, 0.10);
      --radius: 20px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(232, 93, 4, 0.16), transparent 28%),
        radial-gradient(circle at bottom right, rgba(16, 37, 66, 0.14), transparent 24%),
        linear-gradient(180deg, #f6f1e7 0%, #ece5d8 100%);
      color: var(--ink);
      min-height: 100vh;
    }}
    .app {{
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: 100vh;
    }}
    .sidebar {{
      padding: 28px 22px;
      border-right: 1px solid var(--line);
      background: rgba(255, 248, 237, 0.74);
      backdrop-filter: blur(12px);
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
    }}
    .brand {{
      margin-bottom: 20px;
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 12px;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 8px;
    }}
    h1 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 32px;
      line-height: 1.05;
    }}
    .subtle {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.5;
      margin-top: 10px;
    }}
    .run-list {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-top: 22px;
    }}
    .run-button {{
      border: 1px solid transparent;
      background: var(--panel);
      border-radius: 18px;
      padding: 14px;
      text-align: left;
      cursor: pointer;
      box-shadow: var(--shadow);
      transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
    }}
    .run-button:hover {{
      transform: translateY(-1px);
      border-color: rgba(232, 93, 4, 0.25);
    }}
    .run-button.active {{
      background: linear-gradient(180deg, rgba(232, 93, 4, 0.16), rgba(255,255,255,0.92));
      border-color: rgba(232, 93, 4, 0.44);
    }}
    .run-button strong {{
      display: block;
      font-size: 15px;
    }}
    .run-meta {{
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .content {{
      padding: 28px;
      overflow: auto;
    }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.4fr) repeat(3, minmax(0, 1fr));
      gap: 18px;
      margin-bottom: 22px;
    }}
    .card {{
      background: var(--panel-strong);
      border: 1px solid rgba(255, 255, 255, 0.7);
      border-radius: var(--radius);
      padding: 20px;
      box-shadow: var(--shadow);
      min-width: 0;
    }}
    .metric-value {{
      font-size: 34px;
      font-weight: 800;
      margin-top: 8px;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .hero-title {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 14px;
    }}
    .hero-title h2 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 34px;
    }}
    .question-strip {{
      margin-bottom: 22px;
    }}
    .question-list {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 12px;
      margin-top: 14px;
      max-height: 260px;
      overflow: auto;
      padding-right: 4px;
    }}
    .question-chip {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.78);
      cursor: pointer;
      text-align: left;
    }}
    .question-chip.active {{
      border-color: rgba(232, 93, 4, 0.44);
      background: rgba(232, 93, 4, 0.08);
    }}
    .question-chip .topline {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .status.ok {{ color: var(--ok); }}
    .status.bad {{ color: var(--bad); }}
    .panel-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 14px;
    }}
    .panel-header h3 {{
      margin: 0;
      font-size: 18px;
    }}
    .panel-header span {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .detail-list {{
      display: grid;
      grid-template-columns: 140px 1fr;
      gap: 10px 14px;
      font-size: 14px;
    }}
    .detail-list dt {{
      font-weight: 700;
      color: var(--muted);
    }}
    .detail-list dd {{
      margin: 0;
      line-height: 1.55;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: #13233b;
      color: #f7f1e8;
      border-radius: 16px;
      padding: 16px;
      font-size: 13px;
      line-height: 1.55;
      font-family: "SFMono-Regular", "Consolas", monospace;
      overflow: auto;
      max-height: 320px;
    }}
    .results-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .result-box {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255,255,255,0.72);
      min-width: 0;
    }}
    .result-box h4 {{
      margin: 0 0 10px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .result-box code {{
      display: block;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "SFMono-Regular", "Consolas", monospace;
      font-size: 12px;
      line-height: 1.55;
    }}
    .log-stream {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 420px;
      overflow: auto;
      padding-right: 4px;
    }}
    .log-line {{
      border-left: 3px solid transparent;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255,255,255,0.66);
      font-size: 13px;
      line-height: 1.45;
    }}
    .log-line.highlight {{
      border-left-color: var(--accent);
      background: rgba(232, 93, 4, 0.08);
    }}
    .log-meta {{
      color: var(--muted);
      font-size: 11px;
      margin-bottom: 4px;
      font-family: "SFMono-Regular", "Consolas", monospace;
    }}
    .empty {{
      color: var(--muted);
      font-style: italic;
    }}
    @media (max-width: 1100px) {{
      .app {{ grid-template-columns: 1fr; }}
      .sidebar {{
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }}
      .hero, .panel-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside class="sidebar">
      <div class="brand">
        <div class="eyebrow">BirdBench</div>
        <h1>Run Observatory</h1>
        <div class="subtle">Select a run on the left. The right side shows question details, SQL, execution results, and the ordered log stream.</div>
      </div>
      <div id="run-list" class="run-list"></div>
    </aside>
    <main class="content">
      <section id="hero" class="hero"></section>
      <section class="card question-strip">
        <div class="panel-header">
          <h3>Questions</h3>
          <span id="question-count"></span>
        </div>
        <div id="question-list" class="question-list"></div>
      </section>
      <section class="panel-grid">
        <article class="card">
          <div class="panel-header">
            <h3>Question Details</h3>
            <span id="detail-status"></span>
          </div>
          <dl id="question-details" class="detail-list"></dl>
        </article>
        <article class="card">
          <div class="panel-header">
            <h3>SQL</h3>
            <span>Predicted vs Reference</span>
          </div>
          <div class="results-grid">
            <div>
              <div class="metric-label" style="margin-bottom:8px;">Predicted SQL</div>
              <pre id="predicted-sql"></pre>
            </div>
            <div>
              <div class="metric-label" style="margin-bottom:8px;">Reference SQL</div>
              <pre id="reference-sql"></pre>
            </div>
          </div>
        </article>
        <article class="card">
          <div class="panel-header">
            <h3>Results</h3>
            <span>Query Output</span>
          </div>
          <div class="results-grid">
            <div class="result-box">
              <h4>Predicted Result</h4>
              <code id="predicted-result"></code>
            </div>
            <div class="result-box">
              <h4>Reference Result</h4>
              <code id="reference-result"></code>
            </div>
          </div>
          <div class="results-grid" style="margin-top:12px;">
            <div class="result-box">
              <h4>Predicted Error</h4>
              <code id="predicted-error"></code>
            </div>
            <div class="result-box">
              <h4>Reference Error</h4>
              <code id="reference-error"></code>
            </div>
          </div>
        </article>
        <article class="card">
          <div class="panel-header">
            <h3>Logs In Order</h3>
            <span id="log-context"></span>
          </div>
          <div id="log-stream" class="log-stream"></div>
        </article>
      </section>
    </main>
  </div>
  <script id="viewer-data" type="application/json">{data_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById("viewer-data").textContent);
    const state = {{
      runs: payload.runs || [],
      runIndex: 0,
      resultIndex: 0,
    }};

    const runListEl = document.getElementById("run-list");
    const heroEl = document.getElementById("hero");
    const questionCountEl = document.getElementById("question-count");
    const questionListEl = document.getElementById("question-list");
    const questionDetailsEl = document.getElementById("question-details");
    const detailStatusEl = document.getElementById("detail-status");
    const predictedSqlEl = document.getElementById("predicted-sql");
    const referenceSqlEl = document.getElementById("reference-sql");
    const predictedResultEl = document.getElementById("predicted-result");
    const referenceResultEl = document.getElementById("reference-result");
    const predictedErrorEl = document.getElementById("predicted-error");
    const referenceErrorEl = document.getElementById("reference-error");
    const logStreamEl = document.getElementById("log-stream");
    const logContextEl = document.getElementById("log-context");

    function formatCreatedAt(value) {{
      if (!value) return "unknown";
      if (typeof value === "number") {{
        return new Date(value * 1000).toLocaleString();
      }}
      const date = new Date(value);
      if (!Number.isNaN(date.valueOf())) {{
        return date.toLocaleString();
      }}
      return String(value);
    }}

    function stringifyBlock(value) {{
      if (value === null || value === undefined || value === "") return "None";
      return typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }}

    function renderRunList() {{
      runListEl.innerHTML = "";
      if (!state.runs.length) {{
        runListEl.innerHTML = '<div class="empty">No archived runs found.</div>';
        return;
      }}

      state.runs.forEach((run, index) => {{
        const button = document.createElement("button");
        button.className = "run-button" + (index === state.runIndex ? " active" : "");
        button.innerHTML = `
          <strong>${{run.title}}</strong>
          <div class="run-meta">
            <span>${{formatCreatedAt(run.created_at)}}</span>
            <span>${{run.summary?.matched_percent?.toFixed ? run.summary.matched_percent.toFixed(2) : run.summary?.matched_percent || 0}}%</span>
            <span>${{run.summary?.evaluated_count || 0}} eval</span>
          </div>
        `;
        button.addEventListener("click", () => {{
          state.runIndex = index;
          state.resultIndex = 0;
          render();
        }});
        runListEl.appendChild(button);
      }});
    }}

    function renderHero(run) {{
      const summary = run.summary || {{}};
      const matchedPercent = Number(summary.matched_percent || 0);
      heroEl.innerHTML = `
        <section class="card hero-title">
          <div>
            <div class="eyebrow">Selected Run</div>
            <h2>${{run.title}}</h2>
          </div>
          <div class="subtle">
            Created: ${{formatCreatedAt(run.created_at)}}<br>
            Sample selection: ${{run.selected_samples || "all generated samples"}}
          </div>
        </section>
        <section class="card">
          <div class="metric-label">Matched</div>
          <div class="metric-value">${{summary.matched_count || 0}}</div>
        </section>
        <section class="card">
          <div class="metric-label">Evaluated</div>
          <div class="metric-value">${{summary.evaluated_count || 0}}</div>
        </section>
        <section class="card">
          <div class="metric-label">Match Rate</div>
          <div class="metric-value">${{matchedPercent.toFixed(2)}}%</div>
        </section>
      `;
    }}

    function renderQuestionList(run) {{
      const results = run.results || [];
      questionCountEl.textContent = `${{results.length}} questions`;
      questionListEl.innerHTML = "";

      if (!results.length) {{
        questionListEl.innerHTML = '<div class="empty">This run has no evaluated questions.</div>';
        return;
      }}

      results.forEach((result, index) => {{
        const button = document.createElement("button");
        button.className = "question-chip" + (index === state.resultIndex ? " active" : "");
        button.innerHTML = `
          <div class="topline">
            <span>q_id ${{result.q_id}} · ${{result.db_id}}</span>
            <span class="status ${{result.matched ? "ok" : "bad"}}">${{result.matched ? "match" : "mismatch"}}</span>
          </div>
          <div>${{result.question}}</div>
        `;
        button.addEventListener("click", () => {{
          state.resultIndex = index;
          renderQuestionPanels(run);
        }});
        questionListEl.appendChild(button);
      }});
    }}

    function renderQuestionPanels(run) {{
      const results = run.results || [];
      if (!results.length) {{
        questionDetailsEl.innerHTML = '<div class="empty">No question selected.</div>';
        predictedSqlEl.textContent = "";
        referenceSqlEl.textContent = "";
        predictedResultEl.textContent = "";
        referenceResultEl.textContent = "";
        predictedErrorEl.textContent = "";
        referenceErrorEl.textContent = "";
        logStreamEl.innerHTML = '<div class="empty">No logs available.</div>';
        return;
      }}

      const result = results[state.resultIndex] || results[0];
      detailStatusEl.innerHTML = `<span class="status ${{result.matched ? "ok" : "bad"}}">${{result.matched ? "match" : "mismatch"}}</span>`;
      questionDetailsEl.innerHTML = `
        <dt>Question</dt><dd>${{result.question}}</dd>
        <dt>Question ID</dt><dd>${{result.question_id}}</dd>
        <dt>Run q_id</dt><dd>${{result.q_id}}</dd>
        <dt>Database</dt><dd>${{result.db_id}}</dd>
        <dt>Matched</dt><dd>${{result.matched ? "Yes" : "No"}}</dd>
      `;
      predictedSqlEl.textContent = stringifyBlock(result.predicted_sql);
      referenceSqlEl.textContent = stringifyBlock(result.reference_sql);
      predictedResultEl.textContent = stringifyBlock(result.predicted_result);
      referenceResultEl.textContent = stringifyBlock(result.reference_result);
      predictedErrorEl.textContent = stringifyBlock(result.predicted_error);
      referenceErrorEl.textContent = stringifyBlock(result.reference_error);
      renderLogs(run, result);
      renderQuestionList(run);
    }}

    function renderLogs(run, result) {{
      const logs = run.logs || [];
      logStreamEl.innerHTML = "";
      logContextEl.textContent = `highlighting q_id ${{result.q_id}} / question_id ${{result.question_id}}`;

      if (!logs.length) {{
        logStreamEl.innerHTML = '<div class="empty">No logs available for this run.</div>';
        return;
      }}

      const terms = [
        `question_id=${{result.q_id}}`,
        `question_id=${{result.question_id}}`,
        `q_id=${{result.q_id}}`,
        result.question,
      ];

      logs.forEach((entry) => {{
        const fullText = `${{entry.timestamp}} ${{entry.level}} ${{entry.logger}} ${{entry.message}}`;
        const highlight = terms.some((term) => term && fullText.includes(term));
        const line = document.createElement("div");
        line.className = "log-line" + (highlight ? " highlight" : "");
        line.innerHTML = `
          <div class="log-meta">${{entry.timestamp || ""}} ${{entry.level || ""}} ${{entry.logger ? "[" + entry.logger + "]" : ""}}</div>
          <div>${{entry.message || ""}}</div>
        `;
        logStreamEl.appendChild(line);
      }});
    }}

    function render() {{
      renderRunList();
      const run = state.runs[state.runIndex];
      if (!run) {{
        heroEl.innerHTML = '<section class="card"><div class="empty">No run data available.</div></section>';
        return;
      }}
      renderHero(run);
      renderQuestionList(run);
      renderQuestionPanels(run);
    }}

    render();
  </script>
</body>
</html>
"""
