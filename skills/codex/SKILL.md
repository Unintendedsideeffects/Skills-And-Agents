---
name: codex
description: Use when the user asks to run Codex CLI (codex exec, codex resume) or references OpenAI Codex for code analysis, refactoring, or automated editing
---

# Codex Skill Guide

Verified against codex-cli 0.164.0 (2026-11). Re-check `/usr/bin/codex --version`
and `/usr/bin/codex exec --help` if a flag below is rejected.

## Which binary

Always call **`/usr/bin/codex`** by full path:
- `codex` in zsh is an alias that opens a tmux session; it fails without a TTY.
- `~/.local/bin/codex` is the user's wrapper and **always adds
  `--dangerously-bypass-approvals-and-sandbox`**, so any `-s ...` you pass is
  silently ignored. Use it only when the user wants no sandbox.

## Running a Task
1. Ask the user (via `AskUserQuestion`) which model AND which reasoning effort, in a
   **single prompt with two questions**:
   - models: `gpt-6-astra` ("Astra", the config default; usual for implementation
     and review) or `gpt-6-luna` ("6 Luna"; used for doc drafting);
   - effort: `xhigh`, `high`, `medium`, `low` (`high` is the usual default).
2. Pick the sandbox; default `read-only` unless edits are needed:
   - `-s read-only`: analysis and review;
   - `-s workspace-write`: edits inside `-C <dir>` (+ /tmp). **`.git` stays
     read-only** (Codex cannot commit: have it edit only and commit yourself, or
     have it commit in a /tmp clone and hand over a `git bundle`) and **sockets are
     blocked** (tests needing docker, network or a local server fail inside the
     sandbox: rerun those yourself unsandboxed);
   - `-s danger-full-access`: network/broad access; ask the user first.
   There is **no `--full-auto`** any more ("unexpected argument");
   `codex exec` with `-s` already runs non-interactively.
3. Put the task in a brief file and feed it on stdin; always pass `--json` and write stdout
   and stderr to files, then record the run's usage:
   ```bash
   /usr/bin/codex exec --skip-git-repo-check --json -m gpt-6-astra \
     -c model_reasoning_effort=high -s workspace-write -C <dir> \
     < brief.prompt > task.jsonl 2> task.err
   ~/.claude/skills/agent-usage/scripts/agent_usage.py record codex task.jsonl --label <task-name>
   ```
   - Always `--skip-git-repo-check`.
   - `--json` makes stdout a JSONL event stream (`thread.started`, `item.completed`,
     `turn.completed` with a `usage` block: input / cached input / cache-write / output /
     reasoning tokens). Codex's final answer is the last `agent_message` item; add
     `-o <file>` (`--output-last-message`) to also get it as plain text.
   - The stream carries no quota windows. `agent_usage.py record codex` (agent-usage
     skill, shared by every agent CLI) sums the tokens, reads the 5-hour/weekly
     **% left** and reset times from the thread's session log, and appends the run to the
     shared ledger; `agent_usage.py summary` totals it, `agent_usage.py quota codex` shows
     live quota. Every call also pays
     ~27k input tokens of system prompt + AGENTS.md before the brief.
   - Keep stderr in a file rather than `/dev/null`: its header carries the
     **`session id:`** (needed to resume) and confirms model/sandbox/effort; the
     rest is progress you only read when debugging.
   - Long runs: start in the background and wait for completion; do not poll.
4. Keep work copies and briefs outside session scratchpads (they get wiped): e.g. a
   git worktree under the project's agents dir, briefs next to it.
5. When Codex finishes, review its diff yourself (it is a colleague, not the gate),
   run the real gates unsandboxed, then tell the user they can resume the session.

### Resuming
`resume --last` does **not** keep the original model or sandbox (it falls back to
the config default). Resume by session id and repeat every flag *before* `resume`:
```bash
/usr/bin/codex exec --skip-git-repo-check --json -m gpt-6-astra -c model_reasoning_effort=high \
  -s workspace-write -C <dir> resume <session-id> < followup.prompt > task2.jsonl 2> task2.err
~/.claude/skills/agent-usage/scripts/agent_usage.py record codex task2.jsonl --label <task-name>-resume
```
The id is the `thread_id` of the first `--json` event (and in stderr's header); sessions are also logged under
`~/.codex/sessions/YYYY/MM/DD/rollout-*-<session-id>.jsonl`.

### Quick Reference
| Use case | Flags |
| --- | --- |
| Read-only review or analysis | `-s read-only` |
| Apply local edits | `-s workspace-write -C <dir>` |
| Network or broad access (ask first) | `-s danger-full-access` |
| Resume | same flags as the first run, then `resume <session-id>` |

## Following Up
- After every `codex` run, summarise the outcome and use `AskUserQuestion` to
  confirm next steps (resume, fix, or stop) when the next step is not obvious.
- Restate the model, effort and sandbox when proposing a follow-up run.

## Critical Evaluation of Codex Output

Codex is powered by OpenAI models with their own knowledge cutoffs and limitations.
Treat Codex as a **colleague, not an authority**.

### Guidelines
- **Trust your own knowledge** when confident. If Codex claims something you know is
  incorrect, push back directly.
- **Research disagreements** using WebSearch or documentation before accepting
  Codex's claims. Share findings with Codex via resume if needed.
- **Remember knowledge cutoffs**: Codex may not know about recent releases, APIs, or
  changes that occurred after its training data.
- **Don't defer blindly**, especially on model names and capabilities, recent library
  versions or API changes, and best practices that may have evolved.
- **Its gates are not the verdict**: rerun tests yourself, outside its sandbox.

### When Codex is Wrong
1. State your disagreement clearly to the user.
2. Provide evidence (your own knowledge, web search, docs).
3. Optionally resume the session to discuss it. **Identify yourself as Claude**, with
   your actual model name, so Codex knows it is a peer discussion:
   ```bash
   echo "This is Claude (<your model>) following up. I disagree with [X] because [evidence]. What's your take?" \
     | /usr/bin/codex exec --skip-git-repo-check -m <model> -s <sandbox> resume <session-id> > f.out 2> f.err
   ```
4. Frame disagreements as discussions, not corrections: either AI could be wrong.
5. Let the user decide how to proceed if there's genuine ambiguity.

## Error Handling
- Stop and report failures whenever `/usr/bin/codex --version` or a `codex exec`
  exits non-zero; ask for direction before retrying.
- Usage limits: Codex reports when the quota runs out and when it resets; record the
  reset time, keep any partial edits, and tell the user rather than retrying.
- Checking quota before a run: `agent_usage.py quota codex` (agent-usage skill) does the
  following for you. The interactive `/status` command shows the 5-hour and
  weekly limits as **% left** with reset times, plus the plan; it makes no model call.
  It needs a terminal: start `/usr/bin/codex -s read-only` under a pty (e.g. Python
  `pty.fork()`, TERM=xterm-256color), type `/status` + Enter, read the screen, send
  Ctrl-C twice. There is no non-interactive subcommand for it. Session logs
  (`~/.codex/sessions/**/rollout-*.jsonl`, `rate_limits` in `token_count` events) only
  hold the numbers as of the last run.
- Ask the user before `-s danger-full-access` or the bypass wrapper unless they
  already allowed it.
- When output includes warnings or partial results, summarise them and ask how to
  adjust.
