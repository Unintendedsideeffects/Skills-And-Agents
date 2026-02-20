---
name: gemini
description: Run tasks through the Gemini CLI and then review, verify, and evaluate the resulting changes. Use when the user asks to delegate work to Gemini (or says "use gemini") and expects a follow-up review of the edits, diffs, or outputs.
---

# Gemini

Delegate a task to Gemini CLI in yolo (auto-approve) mode, then validate and evaluate the resulting changes before reporting back.

## Workflow

### 1) Prepare the prompt

- Restate the task as a single, focused instruction.
- Include relevant file paths, constraints, and expected outputs.
- Keep the prompt concrete — Gemini will act on it directly without further confirmation.

### 2) Choose execution path

**Path A — running inside Claude Code (you ARE Claude Code):**
Do NOT spawn a nested claude process. Use the Bash tool to run the script directly:
```bash
skills/gemini/scripts/run.sh "Your task prompt here"
```
Optional model override:
```bash
skills/gemini/scripts/run.sh "Your task prompt here" --model gemini-2.5-pro
```
Or set `GEMINI_MODEL` in the environment to avoid repeating the flag.

**Path B — running as an external agent (bash, CI, orchestrator):**
```bash
scripts/run.sh "Your task prompt here"
```
The script validates that `gemini` is on PATH and runs `gemini --yolo "<prompt>"`.

### 3) Review the result

After Gemini finishes, inspect what changed:

```bash
git status -sb
git diff --stat
git diff
```

- Verify changes match the requested scope.
- Look for unintended file deletions, renames, or edits outside the target area.
- Check that project conventions (formatting, naming, test coverage) are preserved.

### 4) Evaluate and report

- Summarize what Gemini changed and whether it satisfies the request.
- Flag any concerns: regressions, missing tests, out-of-scope edits.
- If changes are unexpected or destructive, ask the user before reverting.

## Model Selection

| Model | Best for |
|---|---|
| `gemini-2.5-pro` (default) | Complex multi-file refactors, reasoning-heavy tasks |
| `gemini-2.0-flash` | Fast, focused edits; simple one-file tasks |

Override via `--model` flag or `GEMINI_MODEL` env var.

## Safety Notes

- `--yolo` skips all confirmation prompts. Gemini will write files immediately.
- Always run in a clean git state so changes are easy to inspect and revert.
- If the working tree is dirty before the run, stash first: `git stash`.

## Files

- `scripts/run.sh`: validate gemini is installed and invoke `gemini --yolo`.
