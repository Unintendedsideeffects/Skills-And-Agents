#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: scripts/run.sh [options] [-- extra copilot args]

Required:
  --prompt TEXT           Inline prompt text
  --prompt-file PATH      Read prompt text from file

Optional:
  --repo PATH             Working directory for the Copilot run
  --log PATH              Write combined output to a log file
  --model MODEL           Pass through --model <MODEL>
  -h, --help              Show this help

Examples:
  scripts/run.sh --repo /abs/repo --prompt-file /abs/task.txt
  scripts/run.sh --repo /abs/repo --prompt "Fix parser bug" --model gpt-5.4
USAGE
}

repo=""
log_path=""
model=""
prompt=""
prompt_file=""
extra_args=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)
            repo="${2:-}"
            shift 2
            ;;
        --log)
            log_path="${2:-}"
            shift 2
            ;;
        --model)
            model="${2:-}"
            shift 2
            ;;
        --prompt)
            prompt="${2:-}"
            shift 2
            ;;
        --prompt-file)
            prompt_file="${2:-}"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        --)
            shift
            extra_args=("$@")
            break
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if ! command -v copilot >/dev/null 2>&1; then
    echo "copilot not found on PATH" >&2
    exit 1
fi

if [[ -n "$prompt" && -n "$prompt_file" ]]; then
    echo "Use either --prompt or --prompt-file, not both" >&2
    exit 1
fi

if [[ -z "$prompt" && -z "$prompt_file" ]]; then
    echo "One of --prompt or --prompt-file is required" >&2
    exit 1
fi

if [[ -n "$prompt_file" ]]; then
    if [[ ! -f "$prompt_file" ]]; then
        echo "Prompt file not found: $prompt_file" >&2
        exit 1
    fi
    prompt="$(<"$prompt_file")"
fi

if [[ -z "$prompt" ]]; then
    echo "Prompt is empty" >&2
    exit 1
fi

if [[ -n "$repo" ]]; then
    cd "$repo"
fi

cmd=(copilot --yolo --no-ask-user -s -p "$prompt")
if [[ -n "$model" ]]; then
    cmd+=(--model "$model")
fi
if [[ ${#extra_args[@]} -gt 0 ]]; then
    cmd+=("${extra_args[@]}")
fi

if [[ -n "$log_path" ]]; then
    mkdir -p "$(dirname "$log_path")"
    "${cmd[@]}" 2>&1 | tee "$log_path"
else
    "${cmd[@]}"
fi
