#!/usr/bin/env bash
# agy-delegate: dispatch one agy executor against a brief on disk.
#
# This wraps the CORRECT agy invocation. It deliberately does NOT background the
# process itself — the caller (Claude Code) should launch this via the Bash tool
# with run_in_background:true so the harness tracks agy's REAL lifetime and fires a
# completion event when agy actually exits. Wrapping agy in `nohup … &` would
# double-detach it and the completion event would fire at launch, not at exit.
#
# Usage:
#   scripts/run.sh --brief /abs/brief.md --log /tmp/agy-001.log [--model <tier>]
#                  [--timeout 50m] [--cwd /abs/worktree] [--add-dir /abs/dir]
#                  [--instruction "extra one-liner appended before the brief path"]
#
# The brief file is the source of truth. agy is told to read it and follow it exactly,
# do edits only (no commit/push), and end with a SUMMARY. Run the verification gates
# yourself afterward — agy's exit code is not a verdict.

set -euo pipefail

BRIEF=""
LOG=""
MODEL=""
TIMEOUT="50m"
CWD=""
ADD_DIR=""
INSTRUCTION=""

while [ $# -gt 0 ]; do
  case "$1" in
    --brief) BRIEF="$2"; shift 2 ;;
    --log) LOG="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --cwd) CWD="$2"; shift 2 ;;
    --add-dir) ADD_DIR="$2"; shift 2 ;;
    --instruction) INSTRUCTION="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! command -v agy >/dev/null 2>&1; then
  echo "agy is not on PATH (expected the Antigravity CLI)." >&2
  exit 1
fi
if [ -z "$BRIEF" ] || [ ! -f "$BRIEF" ]; then
  echo "--brief <path> is required and must exist (got: '$BRIEF')." >&2
  exit 2
fi
if [ -z "$LOG" ]; then
  echo "--log <path> is required (where to redirect agy output)." >&2
  exit 2
fi

PROMPT="You are executing a precise implementation plan with zero prior context. \
Read the brief at ${BRIEF} and follow it EXACTLY, step by step, in order. Run every \
verification command and confirm the expected result before moving on. Honor all STOP \
conditions verbatim — if one triggers, STOP and explain rather than improvising. Do \
NOT run 'git commit', 'git push'. When finished, update any status row the brief names. \
End your response with a SUMMARY section listing: (1) every file you created or \
modified, (2) each verification gate and whether it passed with the key output line, \
(3) any STOP condition hit.${INSTRUCTION:+ }${INSTRUCTION}"

CMD=(agy --dangerously-skip-permissions --print-timeout "$TIMEOUT")
[ -n "$MODEL" ] && CMD+=(--model "$MODEL")
[ -n "$ADD_DIR" ] && CMD+=(--add-dir "$ADD_DIR")
CMD+=(--print "$PROMPT")
# Usage tracking (agent-usage skill): agy writes its result as JSON next to the
# log, the log gets the reply as text, and the run's tokens go to the shared
# ledger. AGENT_USAGE=0 restores plain text output.
AGENT_USAGE_PY="${AGENT_USAGE_PY:-$HOME/.claude/skills/agent-usage/scripts/agent_usage.py}"
TRACK=0
if [ "${AGENT_USAGE:-1}" != 0 ] && [ -f "$AGENT_USAGE_PY" ]; then
  TRACK=1
  CMD+=(--output-format json)
fi

if [ -n "$CWD" ]; then
  cd "$CWD"
fi

echo "agy-delegate: dispatching against ${BRIEF}" >&2
echo "agy-delegate: model=${MODEL:-default(Flash)} timeout=${TIMEOUT} log=${LOG}" >&2

# Foreground on purpose — the caller backgrounds this via the harness.
# stdin is closed: an agent CLI left with an open stdin can block reading it.
set +e
if [ "$TRACK" = 1 ]; then
  "${CMD[@]}" </dev/null >"$LOG.json" 2>"$LOG"
  status=$?
  python3 "$AGENT_USAGE_PY" answer agy "$LOG.json" >>"$LOG" 2>/dev/null \
    || echo "agy-delegate: no final reply in $LOG.json (run died early? see the log above)" >>"$LOG"
  python3 "$AGENT_USAGE_PY" record agy "$LOG.json" --label "agy:$(basename "$BRIEF")" >&2 \
    || echo "agy-delegate: usage not recorded" >&2
else
  "${CMD[@]}" </dev/null >"$LOG" 2>&1
  status=$?
fi
set -e
echo "agy-delegate: agy exited status=${status} (NOT a success verdict — verify the diff)" | tee -a "$LOG" >&2
exit "$status"
