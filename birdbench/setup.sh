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
