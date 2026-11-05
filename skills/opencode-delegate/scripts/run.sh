#!/usr/bin/env bash
# Dispatch one bounded task to OpenCode while preserving logs and the real exit code.
# Run this script in the foreground; the surrounding harness may yield/poll it.

set -euo pipefail

MODE="read"
CWD=""
LOG=""
PROMPT=""
BRIEF=""
MODEL="opencode/big-pickle"
AGENT=""
TIMEOUT="50m"
TITLE="opencode-delegate"
INSTRUCTION=""

usage() {
  cat <<'EOF'
Usage:
  run.sh --cwd DIR --log FILE (--prompt TEXT | --brief FILE) [options]

Options:
  --mode read|write       Delegation posture (default: read)
  --model PROVIDER/MODEL  OpenCode model (default: opencode/big-pickle)
  --agent NAME            OpenCode agent (default: plan for read, build for write)
  --timeout DURATION      GNU timeout duration (default: 50m)
  --title TEXT            OpenCode session title
  --instruction TEXT      Additional bounded instruction appended to the prompt
  -h, --help              Show this help
EOF
}

need_value() {
  if [ "$#" -lt 2 ] || [ -z "$2" ]; then
    echo "$1 requires a value" >&2
    exit 2
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode) need_value "$@"; MODE="$2"; shift 2 ;;
    --cwd) need_value "$@"; CWD="$2"; shift 2 ;;
    --log) need_value "$@"; LOG="$2"; shift 2 ;;
    --prompt) need_value "$@"; PROMPT="$2"; shift 2 ;;
    --brief) need_value "$@"; BRIEF="$2"; shift 2 ;;
    --model) need_value "$@"; MODEL="$2"; shift 2 ;;
    --agent) need_value "$@"; AGENT="$2"; shift 2 ;;
    --timeout) need_value "$@"; TIMEOUT="$2"; shift 2 ;;
    --title) need_value "$@"; TITLE="$2"; shift 2 ;;
    --instruction) need_value "$@"; INSTRUCTION="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if ! command -v opencode >/dev/null 2>&1; then
  echo "opencode is not on PATH" >&2
  exit 1
fi
if ! command -v timeout >/dev/null 2>&1; then
  echo "GNU timeout is required" >&2
  exit 1
fi
if [ "$MODE" != "read" ] && [ "$MODE" != "write" ]; then
  echo "--mode must be read or write (got: $MODE)" >&2
  exit 2
fi
if [ -z "$CWD" ] || [ ! -d "$CWD" ]; then
  echo "--cwd must name an existing directory (got: $CWD)" >&2
  exit 2
fi
if [ -z "$LOG" ]; then
  echo "--log is required" >&2
  exit 2
fi
if [ -n "$PROMPT" ] && [ -n "$BRIEF" ]; then
  echo "use exactly one of --prompt or --brief" >&2
  exit 2
fi
if [ -z "$PROMPT" ] && [ -z "$BRIEF" ]; then
  echo "one of --prompt or --brief is required" >&2
  exit 2
fi
if [ -n "$BRIEF" ] && [ ! -f "$BRIEF" ]; then
  echo "--brief must name an existing file (got: $BRIEF)" >&2
  exit 2
fi
if [ -e "$LOG" ] && [ ! -f "$LOG" ]; then
  echo "--log must be a regular file path (got: $LOG)" >&2
  exit 2
fi

LOG_DIR=$(dirname "$LOG")
if [ ! -d "$LOG_DIR" ]; then
  echo "log directory does not exist: $LOG_DIR" >&2
  exit 2
fi

if [ -z "$AGENT" ]; then
  if [ "$MODE" = "read" ]; then
    AGENT="plan"
  else
    AGENT="build"
  fi
fi

COMMON="You are a delegated executor with zero prior context. Work only on the bounded task below. You are not alone in the codebase: preserve all unrelated and pre-existing work, and never revert edits made by others. Follow every applicable AGENTS.md or repository instruction. Do not run git commit, git push, publish, deploy, open issues, or perform external writes. Stop and explain instead of expanding ambiguous scope. End with a SUMMARY listing files read or changed, verification performed, and unresolved limits."

if [ "$MODE" = "read" ]; then
  POSTURE="This is a read-only task. Do not edit, create, delete, rename, or format files. Do not run mutating shell commands. Support conclusions with precise file references."
else
  POSTURE="This is an implementation task. Modify only the files or modules explicitly placed in scope. Do not stage changes. Run only the authorized verification commands, and report any out-of-scope finding without fixing it."
fi

if [ -n "$BRIEF" ]; then
  TASK="The complete task brief is attached as a file. Read it fully and follow it exactly."
else
  TASK="$PROMPT"
fi

FULL_PROMPT="$COMMON $POSTURE $TASK"
if [ -n "$INSTRUCTION" ]; then
  FULL_PROMPT="$FULL_PROMPT Additional instruction: $INSTRUCTION"
fi

CMD=(
  timeout --foreground "$TIMEOUT"
  opencode run
  "$FULL_PROMPT"
  --model "$MODEL"
  --agent "$AGENT"
  --format json
  --title "$TITLE"
)
# opencode run has no --dir (and no --pure) since 2026-11: it works in the
# current directory, so the command runs from $CWD in a subshell below.
if [ -n "$BRIEF" ]; then
  CMD+=(--file "$BRIEF")
fi

BEFORE_STATUS=""
if git -C "$CWD" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BEFORE_STATUS=$(git -C "$CWD" status --porcelain=v1)
fi

echo "opencode-delegate: mode=$MODE model=$MODEL agent=$AGENT" >&2
echo "opencode-delegate: cwd=$CWD timeout=$TIMEOUT log=$LOG" >&2

set +e
# A pipeline (not `> >(tee ...)`) so the log is complete before anything reads
# it; PIPESTATUS keeps opencode's own exit code.
# stdin is closed on purpose: given a non-TTY stdin that stays open (e.g. an agent
# harness), `opencode run` waits for it to append it to the prompt, i.e. forever.
( cd "$CWD" && "${CMD[@]}" < /dev/null ) 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
set -e

AFTER_STATUS=""
if git -C "$CWD" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  AFTER_STATUS=$(git -C "$CWD" status --porcelain=v1)
  if [ "$BEFORE_STATUS" = "$AFTER_STATUS" ]; then
    STATUS_NOTE="unchanged"
  else
    STATUS_NOTE="changed; inspect the diff and concurrent processes"
  fi
else
  STATUS_NOTE="not a Git worktree"
fi

# Usage tracking (agent-usage skill): the log is opencode's --format json
# stream; its sessionID leads to the token counts in opencode's database.
AGENT_USAGE_PY="${AGENT_USAGE_PY:-$HOME/.claude/skills/agent-usage/scripts/agent_usage.py}"
if [ "${AGENT_USAGE:-1}" != 0 ] && [ -f "$AGENT_USAGE_PY" ]; then
  # opencode flushes its database shortly after exit
  sleep 1
  python3 "$AGENT_USAGE_PY" record opencode "$LOG" --label "opencode:$TITLE" >&2 \
    || echo "opencode-delegate: usage not recorded" >&2
fi

echo "opencode-delegate: exit=$STATUS git_status=$STATUS_NOTE" >&2
echo "opencode-delegate: verify the output, diff, and gates independently" >&2
exit "$STATUS"
