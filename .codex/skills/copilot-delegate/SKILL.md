---
name: copilot-delegate
description: Delegate a bounded local coding task to the Copilot CLI, either as a single non-interactive run or as multiple tmux workers with per-task logs. Use when the user explicitly wants local `copilot --yolo` execution with strict file ownership, prompt files, and post-run review.
---

# Copilot Delegate

Use the local `copilot` CLI for bounded delegation, not `gh copilot`.

## When To Use

- The user explicitly asks to use Copilot or wants a second local coding worker.
- The task is narrow enough to hand off with explicit file ownership.
- You want tmux-backed parallel workers with logs you can inspect afterward.

## Workflow

1. Bound the task before delegation:
- List the exact files or directories Copilot may edit.
- State forbidden work explicitly: no unrelated edits, no pushes, no broad cleanup.
- For parallel work, say not to run heavy builds/tests in every worker.

2. Choose a launch mode:
- Single task: `scripts/run.sh --repo /abs/repo --prompt-file /abs/prompt.txt`
- Parallel tmux batch: `scripts/launch-tmux.sh --session copilot-batch --repo /abs/repo --tasks /abs/tasks.tsv`

3. Prompt contract:
- Tell Copilot the ownership scope first.
- Tell it which validations are allowed.
- Tell it to report changed files and any blockers at the end.

4. Review after it finishes:
- Check `git status` and `git diff`.
- Read the tmux logs before trusting the changes.
- Run the relevant build or test yourself; do not assume Copilot verified enough.

## Prompt Template

Use this shape for each prompt file:

```text
Task: <one concrete objective>

Allowed files:
- /abs/path/one
- /abs/path/two

Constraints:
- Do not edit other files.
- Do not push.
- Do not run broad formatting or unrelated cleanup.
- <project-specific build/test constraint>

Deliverable:
- Implement the change.
- Summarize what changed.
- List any follow-up or unresolved issue.
```

## Parallel tmux Format

`scripts/launch-tmux.sh` expects a tab-separated task file:

```text
lane-a	/abs/prompts/lane-a.txt
lane-b	/abs/prompts/lane-b.txt
lane-c	/abs/prompts/lane-c.txt
```

Each row creates one tmux window and one log file.

## Notes

- The scripts assume `copilot`, `tmux`, and `python3` are installed.
- `run.sh` uses `copilot --yolo --no-ask-user -s -p ...`.
- `launch-tmux.sh` keeps all prompt text in files to avoid shell quoting errors.
- Prefer one worker per disjoint write scope.

## Files

- `scripts/run.sh`: one bounded non-interactive Copilot run
- `scripts/launch-tmux.sh`: start one tmux window per prompt file
- `agents/openai.yaml`: UI metadata for skill discovery
