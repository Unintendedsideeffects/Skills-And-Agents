---
name: claude-planner
description: Create strict JSON execution plans with Claude Code and return machine-readable handoff objects for planner-executor workflows. Use when a user asks for a 2-step planner to executor pipeline, wants Claude to produce a structured plan schema, or needs validated plan JSON before step-by-step execution.
---

# Claude Planner

Generate deterministic plans with Claude and hand back a strict JSON envelope for downstream execution.

## Workflow

1. Capture inputs:
- `user_request`: the exact task to plan.
- `executor_constraints`: tools, environment limits, and safety constraints for the executor.
- `schema`: default to `references/plan-schema.json`.
2. Run the planner script:
```bash
scripts/plan.sh \
  --request "Implement feature X safely" \
  --constraints "Use only local files, run tests before edits"
```
3. Return the JSON output directly. Do not wrap it in markdown:
```json
{"type":"plan","planner":"claude","plan":{...}}
```

## Prompt Contract

Use these hard constraints when constructing the planner prompt:
- Output valid JSON only.
- Output no markdown, prose, or commentary.
- Use the provided schema as authoritative.
- Include unknown dependencies in `open_questions`.
- Still produce a best-effort plan if some details are unknown.

The script already enforces this and validates the returned structure.

## Validation Requirements

Reject the plan when any check fails:
- Top-level keys do not match the schema exactly.
- `milestones` is missing or empty.
- Any step misses `id`.
- Step IDs are duplicated.
- Required fields have invalid types.

## CLI Notes

- Default Claude command: `claude --print`.
- Override command with `--cmd "claude-code --print"` or environment variable `CLAUDE_PLANNER_CMD`.
- Use `--pretty` for human-readable output.
- Use `--raw-output-file <path>` to debug malformed model output.

## Files

- `scripts/claude_planner.py`: build prompt, call Claude, parse JSON, validate schema, emit handoff object.
- `scripts/plan.sh`: portable shell wrapper.
- `references/plan-schema.json`: strict plan contract for prompt + validation.
