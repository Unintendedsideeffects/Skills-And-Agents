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

claude -p "$PROMPT"
