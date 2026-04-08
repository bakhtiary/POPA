#!/usr/bin/env bash
# setup.sh — BIRD-Bench Mini-Dev evaluation setup
# Usage: bash setup.sh

set -euo pipefail

EVAL_REPO_DIR="mini_dev"
COMPLETE_PACKAGE_URL="https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip"

if [ -d "$EVAL_REPO_DIR" ]; then
  echo ">>> '$EVAL_REPO_DIR' already exists — skipping clone."
else
  echo ">>> Cloning bird-bench/mini_dev (eval code)..."
  git clone https://github.com/bird-bench/mini_dev.git "$EVAL_REPO_DIR"
fi

echo ">>> Downloading complete BIRD Mini-Dev package..."
PACKAGE_ZIP="./bird-minidev-XXXXXX.zip"
EXTRACT_DIR="./bird-minidev-XXXXXX"
curl -L "$COMPLETE_PACKAGE_URL" -o "$PACKAGE_ZIP" -C -

echo ">>> Extracting complete package..."
unzip -q "$PACKAGE_ZIP" -d "$EXTRACT_DIR"
