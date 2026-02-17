---
name: gemini
description: Run tasks through the Gemini CLI and then review, verify, and evaluate the resulting changes. Use when the user asks to delegate work to Gemini (or says "use gemini") and expects a follow-up review of the edits, diffs, or outputs.
---

# Gemini

## Overview

Delegate a task to Gemini using the provided CLI command, then validate and evaluate the resulting changes before reporting back.

## Workflow

### 1) Prepare the prompt

- Restate the task in a single, focused prompt.
- Include any constraints, file paths, or expected outputs.

### 2) Run Gemini

Use the exact command format:

```bash
gemini --yolo "{prompt}"
```

Replace `{prompt}` with the prepared prompt text.

### 3) Review the result

- Check for file changes and scope: `git status -sb`
- Inspect diffs: `git diff --stat` and `git diff`
- Verify that changes match the request and follow project conventions.
- Identify risks, regressions, or missing tests.

### 4) Evaluate and report

- Summarize what changed and whether it meets the request.
- Flag any concerns or follow-up actions.
- If changes are unexpected or out of scope, ask the user how to proceed before reverting.
