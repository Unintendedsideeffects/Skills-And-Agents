---
name: agent-usage
description: Track token usage, cost and quota of headless agent-CLI runs (codex, claude, agy, cursor-agent, copilot, opencode, gemini) in one ledger. Use when running any agent CLI non-interactively, when the user asks how much an agent run cost, how much quota is left, or for a usage summary across agents.
---

# agent usage

Every agent CLI on this box can write a machine-readable result. Run it that way,
then hand the file to `scripts/agent_usage.py`, which normalizes the usage into one
record and appends it to a shared, append-only ledger
(`~/.local/state/agent-usage/ledger.jsonl`, override `AGENT_USAGE_LEDGER`).

```bash
U=~/.claude/skills/agent-usage/scripts/agent_usage.py
$U record <agent> <output-file> --label <task>   # print + append to the ledger
$U answer <agent> <output-file>                  # the final reply as plain text
$U summary [--days N]                            # totals per day / agent / label
$U quota codex                                   # live 5h/weekly % left (codex /status)
```

## How to run each agent so its usage can be read

Verified on this box 2026-11-05 with a one-line probe each, except gemini (not
authenticated here; reader follows its documented `-o json` schema).

| agent | headless run | usage comes from | final reply |
|---|---|---|---|
| `codex` | `codex exec --json ... > r.jsonl` | sum of `turn.completed.usage`; quota from the thread's `~/.codex/sessions` log | last `agent_message` item |
| `claude` | `claude -p ... --output-format json > r.json` | `usage`, `total_cost_usd` (list price, also on a subscription), `modelUsage` | `.result` |
| `agy` | `agy --print ... --output-format json > r.json` (pty: `script -qec`) | `usage` | `.response` |
| `cursor` | `cursor-agent -p ... --output-format json > r.json` | `usage` | `.result` |
| `copilot` | `copilot -p ... --output-format json > r.jsonl` (JSONL; drop `-s`) | `result.usage.premiumRequests` + `session.usage_checkpoint` tokens and AI credits | last `assistant.message` |
| `opencode` | `opencode run --format json ... > r.jsonl` | `sessionID` from the stream, tokens/cost from `~/.local/share/opencode/opencode.db` | the `text` parts |
| `gemini` | `gemini -p ... -o json > r.json` | `stats.models.*.tokens` (unverified) | `.response` |

`stream-json` output works too for claude, cursor and agy (the reader takes the last
result object).

## Normalized record

`tokens`: `input` (new, uncached prompt), `cache_read`, `cache_write`, `output`,
`reasoning`, `total`; plus what the agent reports beyond tokens: `cost_usd`
(claude, opencode), `premium_requests` and `ai_credits` (copilot), `quota` (codex),
`session`, `models`, `failed`. Costs are each CLI's own figure and are not
comparable across agents.

## Where it is already wired in

The delegate skills record automatically when this skill is installed (each keeps
its old text output for the log and writes the JSON next to it):
`agy-delegate/scripts/run.sh`, `copilot-delegate/scripts/run.sh`,
`gemini/scripts/run.sh`, `claude-diff-review/scripts/review.sh`, and the codex
skill's documented `codex exec --json` command. `AGENT_USAGE=0` turns it off for a
run; `AGENT_USAGE_PY` points at another copy of the script.

## Quota

Only codex exposes live quota without spending it: `$U quota codex` drives its
interactive `/status` in a pty (no model call). Others: agy reports remaining time
only in its quota error ("Resets in …h"); copilot bills premium requests (recorded
per run); claude and cursor show limits in their interactive UIs only.

## Notes

- Fixed overhead per call is large: system prompt + tools + instruction files cost
  roughly 7k (agy) to 34k (claude) tokens before the brief; prefer fewer, larger runs.
- Never put secrets in labels; the ledger is plain text.
