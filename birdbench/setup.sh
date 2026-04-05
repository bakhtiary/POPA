#!/usr/bin/env bash
# setup.sh — BIRD-Bench Mini-Dev evaluation setup
# Usage: bash setup.sh

set -euo pipefail

EVAL_REPO_DIR="mini_dev"
DATA_REPO_DIR="bird_mini_dev_data"
HF_DATA_REPO="https://huggingface.co/datasets/birdsql/bird_mini_dev"

# ── 1. Dependency check ───────────────────────────────────────────────────────
echo ">>> Checking dependencies..."
for cmd in git; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "ERROR: '$cmd' not found. Please install it and retry."
    exit 1
  fi
done

if ! git lfs &>/dev/null; then
  echo "ERROR: git-lfs not found."
  echo "  Install with: brew install git-lfs  OR  sudo apt install git-lfs"
  echo "  Then run:     git lfs install"
  exit 1
fi

# ── 2. Clone the eval code repo ───────────────────────────────────────────────
if [ -d "$EVAL_REPO_DIR" ]; then
  echo ">>> '$EVAL_REPO_DIR' already exists — skipping clone."
else
  echo ">>> Cloning bird-bench/mini_dev (eval code)..."
  git clone https://github.com/bird-bench/mini_dev.git "$EVAL_REPO_DIR"
fi

# ── 3. Clone the HuggingFace dataset repo (databases + JSON files) ────────────
if [ -d "$DATA_REPO_DIR" ]; then
  echo ">>> '$DATA_REPO_DIR' already exists — skipping clone."
  echo "    To update, run: cd $DATA_REPO_DIR && git pull"
else
  echo ">>> Cloning HuggingFace dataset (this will download ~1-2 GB via git-lfs)..."
  GIT_LFS_SKIP_SMUDGE=0 git clone "$HF_DATA_REPO" "$DATA_REPO_DIR"
fi

# ── 4. Link data into the expected directory layout ───────────────────────────
echo ">>> Linking data into eval repo layout..."

mkdir -p "$EVAL_REPO_DIR/mini_dev_data"
mkdir -p "$EVAL_REPO_DIR/llm/mini_dev_data"

DATA_SRC="$(pwd)/$DATA_REPO_DIR/mini_dev_data"

for item in dev_databases mini_dev_sqlite.json mini_dev_mysql.json mini_dev_postgresql.json; do
  TARGET="$EVAL_REPO_DIR/mini_dev_data/$item"
  if [ -e "$TARGET" ] || [ -L "$TARGET" ]; then
    echo "    '$item' already linked — skipping."
  else
    ln -s "$DATA_SRC/$item" "$TARGET"
    echo "    Linked $item"
  fi
done

GOLD_TARGET="$EVAL_REPO_DIR/llm/mini_dev_data/mini_dev_sqlite_gold.sql"
if [ -e "$GOLD_TARGET" ] || [ -L "$GOLD_TARGET" ]; then
  echo "    gold SQL already linked — skipping."
else
  ln -s "$DATA_SRC/mini_dev_sqlite_gold.sql" "$GOLD_TARGET"
  echo "    Linked mini_dev_sqlite_gold.sql"
fi

# ── 5. Done ───────────────────────────────────────────────────────────────────
echo ""
echo "✅ Setup complete. Directory layout:"
echo "   $EVAL_REPO_DIR/                          ← eval code"
echo "   ├── mini_dev_data/"
echo "   │   ├── dev_databases/ -> ...            ← SQLite .db files (symlink)"
echo "   │   └── mini_dev_sqlite.json -> ...      ← questions + evidence (symlink)"
echo "   └── llm/mini_dev_data/"
echo "       └── mini_dev_sqlite_gold.sql -> ...  ← gold SQL (symlink)"
echo "   $DATA_REPO_DIR/                          ← raw HF clone (source of truth)"
echo ""
echo "Next steps:"
echo "  1. Generate predictions from your text-to-SQL model"
echo "     Format: <sql>\t----- bird -----\t<db_id>  (one per line)"
echo "     Save to: $EVAL_REPO_DIR/llm/exp_result/your_predictions.json"
echo ""
echo "  2. Run EX evaluation:"
echo "     cd $EVAL_REPO_DIR"
echo "     python llm/src/evaluation_ex.py \\"
echo "       --predicted_sql_path llm/exp_result/your_predictions.json \\"
echo "       --ground_truth_path llm/mini_dev_data/mini_dev_sqlite_gold.sql \\"
echo "       --db_root_path mini_dev_data/dev_databases \\"
echo "       --data_mode dev"