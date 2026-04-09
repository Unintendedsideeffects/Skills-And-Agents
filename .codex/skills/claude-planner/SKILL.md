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
   - `schema`: load from `references/plan-schema.json`.

2. Choose execution path based on context:

   **Path A — running inside Claude Code (you ARE Claude Code):**
   Do NOT invoke `plan.sh` or any subprocess. `CLAUDECODE` is set, which blocks nested
   CLI invocations.  Instead, act as the planner directly:
   - Load the schema from `references/plan-schema.json`.
   - Apply the Prompt Contract below to generate the plan JSON in your response.
   - Validate the output against the Validation Requirements below.
   - Wrap it in the handoff envelope and return it. Do not wrap in markdown.

   **Path B — running as an external agent (bash, CI, orchestrator, etc.):**
   ```bash
   scripts/plan.sh \
     --request "Implement feature X safely" \
     --constraints "Use only local files, run tests before edits"
   ```
   The script calls `claude --print` as a subprocess and emits the handoff JSON.

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

## CLI Notes (Path B only)

- Default Claude command: `claude --print`.
- Override command with `--cmd "claude-code --print"` or environment variable `CLAUDE_PLANNER_CMD`.
- Use `--pretty` for human-readable output.
- Use `--raw-output-file <path>` to debug malformed model output.

## Files

- `scripts/claude_planner.py`: build prompt, call Claude, parse JSON, validate schema, emit handoff object.
- `scripts/plan.sh`: portable shell wrapper.
- `references/plan-schema.json`: strict plan contract for prompt + validation.
