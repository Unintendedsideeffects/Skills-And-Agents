#!/usr/bin/env bash
# run.sh — delegate a task to Gemini CLI in yolo (auto-approve) mode.
#
# Usage:
#   run.sh "Fix the broken test in src/auth.py"
#   run.sh "Refactor UserService" --model gemini-2.5-pro
#
# Environment:
#   GEMINI_MODEL   override model without passing --model each time

set -euo pipefail

PROMPT="${1:-}"
MODEL="${GEMINI_MODEL:-}"

if [[ -z "$PROMPT" ]]; then
  echo "usage: run.sh <prompt> [--model <model>]" >&2
  exit 1
fi
shift

# Parse optional flags from remaining args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    *) echo "error: unknown argument: $1" >&2; exit 1 ;;
  esac
done

if ! command -v gemini >/dev/null 2>&1; then
  echo "error: gemini CLI not found in PATH. Install with: npm install -g @google/generative-ai-cli" >&2
  exit 127
fi

CMD=(gemini --yolo --prompt "$PROMPT")
if [[ -n "$MODEL" ]]; then
  CMD+=(--model "$MODEL")
fi

exec "${CMD[@]}"
