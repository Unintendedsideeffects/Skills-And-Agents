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

# Usage tracking (agent-usage skill): run with JSON output into a temp file,
# print the reply as text as before, and record the run's tokens in the shared
# ledger. AGENT_USAGE=0 (or no tracker installed) keeps the plain call.
AGENT_USAGE_PY="${AGENT_USAGE_PY:-$HOME/.claude/skills/agent-usage/scripts/agent_usage.py}"
tracked_run() {  # tracked_run <agent> <label> <json-flag...> -- <command...>
  local agent="$1" label="$2" flags=() json status
  shift 2
  while [[ "$1" != "--" ]]; do flags+=("$1"); shift; done
  shift
  if [[ "${AGENT_USAGE:-1}" == 0 || ! -f "$AGENT_USAGE_PY" ]]; then
    "$@"
    return
  fi
  json="$(mktemp "${TMPDIR:-/tmp}/${agent}-run-XXXXXX.json")"
  set +e
  "$@" "${flags[@]}" >"$json"
  status=$?
  set -e
  python3 "$AGENT_USAGE_PY" answer "$agent" "$json" 2>/dev/null || cat "$json"
  python3 "$AGENT_USAGE_PY" record "$agent" "$json" --label "$label" >&2 || echo "usage not recorded ($json)" >&2
  return "$status"
}

tracked_run gemini "gemini:run" -o json -- "${CMD[@]}"
