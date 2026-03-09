#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: scripts/launch-tmux.sh --session NAME --repo PATH --tasks FILE [options]

Required:
  --session NAME         tmux session name
  --repo PATH            Repository root for worker windows
  --tasks FILE           Tab-separated file: <window_name><TAB><prompt_file>

Optional:
  --log-dir PATH         Directory for per-window logs
  --model MODEL          Pass through --model <MODEL> to each worker
  --attach               Attach after launch
  -h, --help             Show this help

Example:
  scripts/launch-tmux.sh \
    --session copilot-next5 \
    --repo /abs/repo \
    --tasks /abs/tasks.tsv \
    --log-dir /abs/logs
USAGE
}

session=""
repo=""
tasks_file=""
log_dir=""
model=""
attach_after=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --session)
            session="${2:-}"
            shift 2
            ;;
        --repo)
            repo="${2:-}"
            shift 2
            ;;
        --tasks)
            tasks_file="${2:-}"
            shift 2
            ;;
        --log-dir)
            log_dir="${2:-}"
            shift 2
            ;;
        --model)
            model="${2:-}"
            shift 2
            ;;
        --attach)
            attach_after=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if ! command -v tmux >/dev/null 2>&1; then
    echo "tmux not found on PATH" >&2
    exit 1
fi

if [[ -z "$session" || -z "$repo" || -z "$tasks_file" ]]; then
    usage >&2
    exit 1
fi

if [[ ! -d "$repo" ]]; then
    echo "Repo not found: $repo" >&2
    exit 1
fi

if [[ ! -f "$tasks_file" ]]; then
    echo "Tasks file not found: $tasks_file" >&2
    exit 1
fi

if tmux has-session -t "$session" 2>/dev/null; then
    echo "tmux session already exists: $session" >&2
    exit 1
fi

script_dir="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
runner="$script_dir/run.sh"

if [[ -z "$log_dir" ]]; then
    log_dir="$repo/.copilot-logs/$session"
fi
mkdir -p "$log_dir"

sanitize_name() {
    printf '%s' "$1" | tr ' /:\t' '_' | tr -cd 'A-Za-z0-9._-'
}

build_command() {
    local prompt_file="$1"
    local log_file="$2"
    local command=("$runner" --repo "$repo" --prompt-file "$prompt_file" --log "$log_file")
    local raw_command=""
    if [[ -n "$model" ]]; then
        command+=(--model "$model")
    fi
    printf -v raw_command '%q ' "${command[@]}"
    printf '%q' "$raw_command"
}

created=0
while IFS=$'\t' read -r window_name prompt_file || [[ -n "$window_name" || -n "$prompt_file" ]]; do
    if [[ -z "${window_name// }" ]]; then
        continue
    fi
    if [[ "$window_name" == \#* ]]; then
        continue
    fi
    if [[ -z "${prompt_file:-}" ]]; then
        echo "Missing prompt file for task: $window_name" >&2
        exit 1
    fi
    if [[ ! -f "$prompt_file" ]]; then
        echo "Prompt file not found: $prompt_file" >&2
        exit 1
    fi

    safe_name="$(sanitize_name "$window_name")"
    if [[ -z "$safe_name" ]]; then
        echo "Invalid window name: $window_name" >&2
        exit 1
    fi
    log_file="$log_dir/$safe_name.log"
    tmux_cmd="$(build_command "$prompt_file" "$log_file")"

    if [[ "$created" -eq 0 ]]; then
        tmux new-session -d -s "$session" -n "$safe_name" -c "$repo" "bash -lc $tmux_cmd"
    else
        tmux new-window -d -t "$session" -n "$safe_name" -c "$repo" "bash -lc $tmux_cmd"
    fi
    created=1
done <"$tasks_file"

if [[ "$created" -eq 0 ]]; then
    echo "No tasks found in $tasks_file" >&2
    exit 1
fi

echo "Started tmux session: $session"
echo "Log directory: $log_dir"
echo "Attach with: tmux attach -t $session"

if [[ "$attach_after" -eq 1 ]]; then
    tmux attach -t "$session"
fi
