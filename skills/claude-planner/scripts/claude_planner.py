#!/usr/bin/env python3
"""Run Claude as a strict planner and emit an executor-ready handoff object."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


TOP_LEVEL_KEYS = {
    "goal",
    "assumptions",
    "constraints",
    "milestones",
    "open_questions",
    "next_action",
}
MILESTONE_KEYS = {"name", "success_criteria", "steps"}
STEP_KEYS = {"id", "action", "inputs", "outputs", "risks"}
NEXT_ACTION_KEYS = {"id", "action"}


def parse_args() -> argparse.Namespace:
    default_schema = (
        Path(__file__).resolve().parent.parent / "references" / "plan-schema.json"
    )
    parser = argparse.ArgumentParser(
        description="Generate strict planner JSON via Claude and return a handoff object."
    )
    parser.add_argument("--request", required=True, help="User request to plan.")
    parser.add_argument(
        "--constraints",
        default="",
        help="Executor/tool constraints for the downstream execution agent.",
    )
    parser.add_argument(
        "--cmd",
        default=os.environ.get("CLAUDE_PLANNER_CMD", "claude --print"),
        help="Claude CLI command to execute.",
    )
    parser.add_argument(
        "--schema",
        default=str(default_schema),
        help="Path to the JSON schema file included in prompt context.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Subprocess timeout when running Claude.",
    )
    parser.add_argument(
        "--raw-output-file",
        default="",
        help="Optional file path for saving raw Claude stdout for debugging.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def load_schema(schema_path: Path) -> dict[str, Any]:
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_prompt(user_request: str, constraints: str, schema: dict[str, Any]) -> str:
    schema_text = json.dumps(schema, ensure_ascii=True, indent=2)
    return f"""You are a planning engine. Produce a plan ONLY as valid JSON matching the provided schema.
No prose. No markdown. No extra keys.
If you cannot comply, output {{}}

Schema:
{schema_text}

Context:
- The executor is a separate agent that will follow your plan.
- Steps should be small, verifiable, and tool-friendly.
- If you need unknown info, put it in open_questions, but still produce a best-effort plan.

User request:
{user_request}

Executor/tool constraints:
{constraints}
"""


def run_claude(command: str, prompt: str, timeout_seconds: int) -> str:
    cmd = shlex.split(command)
    if not cmd:
        raise ValueError("Claude command resolved to an empty command list.")
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Claude command failed ({result.returncode}): {stderr}")
    return result.stdout.strip()


def extract_first_json_object(raw: str) -> str:
    start = raw.find("{")
    if start < 0:
        return ""

    in_string = False
    escaped = False
    depth = 0
    for index in range(start, len(raw)):
        char = raw[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0:
                return raw[start : index + 1]
    return ""


def parse_plan(raw_output: str) -> dict[str, Any]:
    if not raw_output:
        raise ValueError("Claude output was empty.")

    candidates = [raw_output]
    extracted = extract_first_json_object(raw_output)
    if extracted and extracted != raw_output:
        candidates.append(extracted)

    errors: list[str] = []
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if not isinstance(parsed, dict):
                raise ValueError("JSON root must be an object.")
            return parsed
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))

    joined = "; ".join(errors)
    raise ValueError(f"Unable to parse planner JSON output: {joined}")


def expect_exact_keys(obj: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(obj.keys())
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{context} keys mismatch. missing={missing or []}, extra={extra or []}"
        )


def require_non_empty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


def require_string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list.")
    for idx, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"{name}[{idx}] must be a string.")
    return value


def validate_plan(plan: dict[str, Any]) -> None:
    expect_exact_keys(plan, TOP_LEVEL_KEYS, "plan")
    require_non_empty_string(plan["goal"], "goal")
    require_string_list(plan["assumptions"], "assumptions")
    require_string_list(plan["constraints"], "constraints")
    require_string_list(plan["open_questions"], "open_questions")

    milestones = plan["milestones"]
    if not isinstance(milestones, list) or not milestones:
        raise ValueError("milestones must be a non-empty list.")

    seen_step_ids: set[str] = set()
    for milestone_index, milestone in enumerate(milestones):
        if not isinstance(milestone, dict):
            raise ValueError(f"milestones[{milestone_index}] must be an object.")
        expect_exact_keys(milestone, MILESTONE_KEYS, f"milestones[{milestone_index}]")
        require_non_empty_string(milestone["name"], f"milestones[{milestone_index}].name")
        require_string_list(
            milestone["success_criteria"],
            f"milestones[{milestone_index}].success_criteria",
        )

        steps = milestone["steps"]
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"milestones[{milestone_index}].steps must be a non-empty list.")

        for step_index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(
                    f"milestones[{milestone_index}].steps[{step_index}] must be an object."
                )
            expect_exact_keys(
                step,
                STEP_KEYS,
                f"milestones[{milestone_index}].steps[{step_index}]",
            )
            step_id = require_non_empty_string(
                step["id"],
                f"milestones[{milestone_index}].steps[{step_index}].id",
            )
            if step_id in seen_step_ids:
                raise ValueError(f"Duplicate step id found: {step_id}")
            seen_step_ids.add(step_id)
            require_non_empty_string(
                step["action"],
                f"milestones[{milestone_index}].steps[{step_index}].action",
            )
            require_string_list(
                step["inputs"],
                f"milestones[{milestone_index}].steps[{step_index}].inputs",
            )
            require_string_list(
                step["outputs"],
                f"milestones[{milestone_index}].steps[{step_index}].outputs",
            )
            require_string_list(
                step["risks"],
                f"milestones[{milestone_index}].steps[{step_index}].risks",
            )

    next_action = plan["next_action"]
    if not isinstance(next_action, dict):
        raise ValueError("next_action must be an object.")
    expect_exact_keys(next_action, NEXT_ACTION_KEYS, "next_action")
    require_non_empty_string(next_action["id"], "next_action.id")
    require_non_empty_string(next_action["action"], "next_action.action")


def build_handoff(plan: dict[str, Any]) -> dict[str, Any]:
    return {"type": "plan", "planner": "claude", "plan": plan}


def main() -> int:
    args = parse_args()
    schema = load_schema(Path(args.schema))
    prompt = build_prompt(args.request, args.constraints, schema)

    raw_output = run_claude(args.cmd, prompt, args.timeout_seconds)

    if args.raw_output_file:
        Path(args.raw_output_file).write_text(raw_output, encoding="utf-8")

    plan = parse_plan(raw_output)
    validate_plan(plan)
    handoff = build_handoff(plan)

    if args.pretty:
        print(json.dumps(handoff, ensure_ascii=True, indent=2))
    else:
        print(json.dumps(handoff, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
