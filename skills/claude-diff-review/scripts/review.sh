#!/usr/bin/env bash
set -euo pipefail

RANGE="${1:-master...fork-drift}"
FOCUS="${2:-correctness regressions, i18n/UX regressions, CI/release risks, and repo hygiene risks}"

if ! command -v claude >/dev/null 2>&1; then
  echo "error: claude CLI not found in PATH" >&2
  exit 127
fi

PROMPT=$(cat <<EOF
You are reviewing a git branch diff in the current repository.
Compare ${RANGE} and produce a concise code review findings list ordered by severity.
Focus on: ${FOCUS}
Output requirements:
- findings first, ordered by severity
- include concrete file references with line numbers when possible
- include a brief "Open questions" section only if needed
- no praise, no filler
EOF
)

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

tracked_run claude "claude-diff-review:${RANGE}" --output-format json -- claude -p "$PROMPT"
