#!/usr/bin/env python3
"""Convert a structured plan into atomic weighted tasks and agent prompts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_PLAN_KEYS = {
    "goal",
    "assumptions",
    "constraints",
    "milestones",
    "open_questions",
    "next_action",
}

REQUIRED_MILESTONE_KEYS = {"name", "success_criteria", "steps"}
REQUIRED_STEP_KEYS = {"id", "action", "inputs", "outputs", "risks"}

SPLIT_PATTERN = re.compile(r"\s*(?:;|\band then\b|\bthen\b)\s*", re.IGNORECASE)

AGENT_KEYWORDS = {
    "codex": [
        "implement",
        "code",
        "refactor",
        "fix",
        "build",
        "test",
        "script",
        "deploy",
        "run",
        "compile",
        "lint",
        "patch",
    ],
    "claude": [
        "document",
        "readme",
        "spec",
        "plan",
        "review",
        "summarize",
        "analyze",
        "policy",
        "write",
        "explain",
    ],
    "gemini": [
        "research",
        "compare",
        "investigate",
        "discover",
        "triage",
        "benchmark",
        "explore",
        "evaluate",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert planner output into atomic tasks and agent prompts."
    )
    parser.add_argument(
        "--input-file",
        default="-",
        help="Path to plan JSON input. Use '-' for stdin.",
    )
    parser.add_argument(
        "--input-json",
        default="",
        help="Inline plan JSON string (takes precedence over --input-file).",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional path to write resulting backlog JSON.",
    )
    parser.add_argument(
        "--agents",
        default="codex,claude,gemini",
        help="Comma-separated agent names to assign prompts to.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )
    return parser.parse_args()


def load_input(input_file: str, input_json: str) -> dict[str, Any]:
    if input_json.strip():
        data = json.loads(input_json)
        if not isinstance(data, dict):
            raise ValueError("Inline input JSON must be an object.")
        return data

    if input_file == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(input_file).read_text(encoding="utf-8")

    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Plan input must be a JSON object.")
    return data


def normalize_plan(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if (
        isinstance(payload.get("plan"), dict)
        and payload.get("type") == "plan"
        and payload.get("planner")
    ):
        return payload["plan"], "planner_handoff"
    return payload, "raw_plan"


def expect_exact_keys(obj: dict[str, Any], expected: set[str], context: str) -> None:
    actual = set(obj.keys())
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"{context} keys mismatch. missing={missing or []}, extra={extra or []}"
        )


def require_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value.strip()


def require_str_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list.")
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(f"{name}[{index}] must be a string.")
    return value


def validate_plan(plan: dict[str, Any]) -> None:
    expect_exact_keys(plan, REQUIRED_PLAN_KEYS, "plan")
    require_string(plan["goal"], "goal")
    require_str_list(plan["assumptions"], "assumptions")
    require_str_list(plan["constraints"], "constraints")
    require_str_list(plan["open_questions"], "open_questions")

    milestones = plan["milestones"]
    if not isinstance(milestones, list) or not milestones:
        raise ValueError("milestones must be a non-empty list.")

    for milestone_index, milestone in enumerate(milestones):
        if not isinstance(milestone, dict):
            raise ValueError(f"milestones[{milestone_index}] must be an object.")
        expect_exact_keys(
            milestone,
            REQUIRED_MILESTONE_KEYS,
            f"milestones[{milestone_index}]",
        )
        require_string(milestone["name"], f"milestones[{milestone_index}].name")
        require_str_list(
            milestone["success_criteria"],
            f"milestones[{milestone_index}].success_criteria",
        )
        steps = milestone["steps"]
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"milestones[{milestone_index}].steps must be non-empty.")
        for step_index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(
                    f"milestones[{milestone_index}].steps[{step_index}] must be an object."
                )
            expect_exact_keys(
                step,
                REQUIRED_STEP_KEYS,
                f"milestones[{milestone_index}].steps[{step_index}]",
            )
            require_string(
                step["id"],
                f"milestones[{milestone_index}].steps[{step_index}].id",
            )
            require_string(
                step["action"],
                f"milestones[{milestone_index}].steps[{step_index}].action",
            )
            require_str_list(
                step["inputs"],
                f"milestones[{milestone_index}].steps[{step_index}].inputs",
            )
            require_str_list(
                step["outputs"],
                f"milestones[{milestone_index}].steps[{step_index}].outputs",
            )
            require_str_list(
                step["risks"],
                f"milestones[{milestone_index}].steps[{step_index}].risks",
            )

    next_action = plan["next_action"]
    if not isinstance(next_action, dict):
        raise ValueError("next_action must be an object.")
    if set(next_action.keys()) != {"id", "action"}:
        raise ValueError("next_action must only contain 'id' and 'action'.")
    require_string(next_action["id"], "next_action.id")
    require_string(next_action["action"], "next_action.action")


def parse_agents(raw_agents: str) -> list[str]:
    agents = [item.strip() for item in raw_agents.split(",") if item.strip()]
    if not agents:
        raise ValueError("At least one agent must be provided in --agents.")
    return agents


def split_atomic_actions(action: str) -> list[str]:
    parts = [part.strip(" .") for part in SPLIT_PATTERN.split(action.strip()) if part.strip()]
    if not parts:
        return [action.strip()]
    return parts


def unique_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def dependencies_from_input_refs(
    inputs: list[str], step_to_last_task: dict[str, str]
) -> list[str]:
    found: list[str] = []
    for input_item in inputs:
        lowered = input_item.lower()
        for step_id, task_id in step_to_last_task.items():
            if re.search(rf"\b{re.escape(step_id.lower())}\b", lowered):
                found.append(task_id)
    return unique_list(found)


def estimate_weight(
    action: str,
    inputs: list[str],
    outputs: list[str],
    risks: list[str],
    dependency_count: int,
) -> int:
    words = action.split()
    weight = 1
    weight += min(4, max(0, (len(words) - 6) // 6))
    weight += min(2, len(inputs))
    weight += min(2, len(outputs))
    weight += min(2, len(risks))
    if dependency_count >= 2:
        weight += 1
    return max(1, min(13, weight))


def infer_agent(
    action: str,
    inputs: list[str],
    outputs: list[str],
    risks: list[str],
    agents: list[str],
) -> str:
    blob = " ".join([action, *inputs, *outputs, *risks]).lower()
    best_agent = agents[0]
    best_score = -1

    for agent in agents:
        keywords = AGENT_KEYWORDS.get(agent.lower(), [])
        score = 0
        for keyword in keywords:
            score += len(re.findall(rf"\b{re.escape(keyword)}\b", blob))
        if score > best_score:
            best_agent = agent
            best_score = score

    return best_agent


def list_block(values: list[str]) -> str:
    if not values:
        return "- none"
    return "\n".join(f"- {value}" for value in values)


def make_acceptance_criteria(action: str, outputs: list[str]) -> list[str]:
    criteria = [f"Complete action: {action}"]
    for output in outputs:
        criteria.append(f"Produce output: {output}")
    return criteria


def short_title(text: str, max_len: int = 72) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 3].rstrip() + "..."


def build_prompt(
    agent: str,
    goal: str,
    milestone_name: str,
    task_id: str,
    action: str,
    weight: int,
    dependencies: list[str],
    inputs: list[str],
    outputs: list[str],
    risks: list[str],
    acceptance_criteria: list[str],
) -> str:
    deps = ", ".join(dependencies) if dependencies else "none"
    return (
        f"You are {agent}. Execute scrum task {task_id}.\n\n"
        f"Goal: {goal}\n"
        f"Milestone: {milestone_name}\n"
        f"Task ID: {task_id}\n"
        f"Task Action: {action}\n"
        f"Weight: {weight}\n"
        f"Dependencies: {deps}\n\n"
        f"Inputs:\n{list_block(inputs)}\n\n"
        f"Expected Outputs:\n{list_block(outputs)}\n\n"
        f"Risks:\n{list_block(risks)}\n\n"
        f"Definition of Done:\n{list_block(acceptance_criteria)}\n\n"
        "Reply in this format:\n"
        "1. Status: done|blocked\n"
        "2. Artifacts: file paths, commands, or references\n"
        "3. Validation: checks/tests completed\n"
        "4. Blockers: unresolved issues or 'none'\n"
    )


def mermaid_id(task_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", task_id)


def build_dependency_tree(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    edges: list[dict[str, str]] = []
    roots: list[str] = []
    lines = ["graph TD"]

    for task in tasks:
        task_node = mermaid_id(task["task_id"])
        label = short_title(f"{task['task_id']}: {task['title']}", 80).replace('"', "'")
        lines.append(f'  {task_node}["{label}"]')
        if not task["dependencies"]:
            roots.append(task["task_id"])
        for dep in task["dependencies"]:
            edges.append({"from": dep, "to": task["task_id"]})
            lines.append(f"  {mermaid_id(dep)} --> {task_node}")

    return {"roots": roots, "edges": edges, "mermaid": "\n".join(lines)}


def build_backlog(plan: dict[str, Any], source_type: str, agents: list[str]) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []
    step_to_last_task: dict[str, str] = {}
    last_milestone_tail: str | None = None
    task_seq = 1

    for milestone in plan["milestones"]:
        milestone_name = milestone["name"]
        previous_in_milestone: str | None = None

        for step in milestone["steps"]:
            step_id = step["id"]
            atomic_actions = split_atomic_actions(step["action"])
            created_for_step: list[str] = []

            for atomic_action in atomic_actions:
                task_id = f"T{task_seq:03d}"
                task_seq += 1

                dependencies: list[str] = []
                if previous_in_milestone:
                    dependencies.append(previous_in_milestone)
                elif last_milestone_tail:
                    dependencies.append(last_milestone_tail)

                dependencies.extend(
                    dependencies_from_input_refs(step["inputs"], step_to_last_task)
                )
                dependencies = unique_list([dep for dep in dependencies if dep != task_id])

                weight = estimate_weight(
                    atomic_action,
                    step["inputs"],
                    step["outputs"],
                    step["risks"],
                    len(dependencies),
                )
                assigned_agent = infer_agent(
                    atomic_action,
                    step["inputs"],
                    step["outputs"],
                    step["risks"],
                    agents,
                )
                acceptance_criteria = make_acceptance_criteria(
                    atomic_action,
                    step["outputs"],
                )

                task = {
                    "task_id": task_id,
                    "milestone": milestone_name,
                    "source_step_id": step_id,
                    "title": short_title(atomic_action),
                    "action": atomic_action,
                    "weight": weight,
                    "dependencies": dependencies,
                    "inputs": step["inputs"],
                    "outputs": step["outputs"],
                    "risks": step["risks"],
                    "acceptance_criteria": acceptance_criteria,
                    "assigned_agent": assigned_agent,
                    "prompt": build_prompt(
                        agent=assigned_agent,
                        goal=plan["goal"],
                        milestone_name=milestone_name,
                        task_id=task_id,
                        action=atomic_action,
                        weight=weight,
                        dependencies=dependencies,
                        inputs=step["inputs"],
                        outputs=step["outputs"],
                        risks=step["risks"],
                        acceptance_criteria=acceptance_criteria,
                    ),
                }
                tasks.append(task)
                created_for_step.append(task_id)
                previous_in_milestone = task_id

            if created_for_step:
                step_to_last_task[step_id] = created_for_step[-1]

        if previous_in_milestone:
            last_milestone_tail = previous_in_milestone

    dependency_tree = build_dependency_tree(tasks)

    agent_packets: dict[str, list[dict[str, Any]]] = {agent: [] for agent in agents}
    for task in tasks:
        agent_packets[task["assigned_agent"]].append(
            {
                "task_id": task["task_id"],
                "weight": task["weight"],
                "dependencies": task["dependencies"],
                "milestone": task["milestone"],
                "title": task["title"],
                "prompt": task["prompt"],
            }
        )

    non_empty_packets = {agent: packet for agent, packet in agent_packets.items() if packet}
    total_weight = sum(task["weight"] for task in tasks)

    return {
        "type": "scrum_backlog",
        "source_type": source_type,
        "goal": plan["goal"],
        "totals": {
            "task_count": len(tasks),
            "milestone_count": len(plan["milestones"]),
            "agent_count": len(non_empty_packets),
            "total_weight": total_weight,
        },
        "tasks": tasks,
        "dependency_tree": dependency_tree,
        "agent_packets": non_empty_packets,
        "open_questions": plan["open_questions"],
    }


def write_output(backlog: dict[str, Any], output_file: str, pretty: bool) -> None:
    text = json.dumps(backlog, ensure_ascii=True, indent=2 if pretty else None)
    if output_file:
        Path(output_file).write_text(text + "\n", encoding="utf-8")
    print(text)


def main() -> int:
    args = parse_args()
    payload = load_input(args.input_file, args.input_json)
    plan, source_type = normalize_plan(payload)
    validate_plan(plan)
    agents = parse_agents(args.agents)
    backlog = build_backlog(plan, source_type, agents)
    write_output(backlog, args.output_file, args.pretty)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
