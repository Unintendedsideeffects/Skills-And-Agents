---
name: scrum-master
description: Convert execution plans into a delivery-ready scrum backlog with atomic tasks, relative weights, dependency trees, and agent-ready prompts. Use when a user has a structured plan (especially claude-planner JSON) and needs work packets that can be distributed across Codex, Claude, Gemini, or other agents.
---

# Scrum Master

Turn structured plans into assignable work. The generated backlog is deterministic and machine-readable so downstream executors can ingest it directly.

## Workflow

1. Start from a plan:
- Preferred input: claude-planner handoff object (`{"type":"plan","planner":"claude","plan":{...}}`)
- Also supported: raw plan object with the same fields.
2. Run the backlog builder:
```bash
scripts/build_backlog.sh \
  --input-file /path/to/plan.json \
  --pretty
```
3. Distribute by `agent_packets`:
- Each packet includes task metadata + a ready-to-send prompt per agent.

## Output Contract

The script emits:
- `tasks`: atomic units with `task_id`, `weight`, dependencies, milestone context, and acceptance criteria.
- `dependency_tree`: roots, directed edges, and Mermaid graph.
- `agent_packets`: prompt bundles keyed by agent (`codex`, `claude`, `gemini`, or custom list).

See `references/backlog-schema.json` for the full JSON structure.

## Decomposition Rules

- Split each plan step into atomic actions when the action contains sequencing phrases (`then`, `and then`, `;`).
- Preserve ordering inside each milestone.
- Link milestones in sequence (first task of milestone N depends on final task of milestone N-1).
- Add explicit dependencies when step inputs reference earlier step IDs.

## Weighting Model

Weights are relative effort scores (1-13) based on:
- Action length/complexity.
- Number of inputs and outputs.
- Risk count.
- Dependency count.

Use weights for agent load balancing, sprint slicing, and prioritization.

## Prompt Generation

Each prompt packet includes:
- Goal and milestone context.
- Exact task action.
- Inputs, expected outputs, risks.
- Dependency prerequisites.
- Definition of done and expected response format.

Use these prompts directly when launching agent work sessions.

## Files

- `scripts/scrum_master.py`: convert plan JSON to backlog JSON.
- `scripts/build_backlog.sh`: shell wrapper.
- `references/backlog-schema.json`: expected output schema.
