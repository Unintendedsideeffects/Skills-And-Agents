#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any

COPILOT_REVIEWER = "copilot-pull-request-reviewer"

TIMELINE_QUERY = """\
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      timelineItems(last:30, itemTypes:[REVIEW_REQUESTED_EVENT, PULL_REQUEST_REVIEW]) {
        nodes {
          __typename
          ... on ReviewRequestedEvent {
            createdAt
            requestedReviewer {
              __typename
            }
          }
          ... on PullRequestReview {
            createdAt
            state
            author {
              login
            }
            commit {
              oid
            }
          }
        }
      }
    }
  }
}
"""


@dataclass
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str
    title: str


def run(cmd: list[str], stdin: str | None = None) -> str:
    proc = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc.stdout


def run_json(cmd: list[str], stdin: str | None = None) -> dict[str, Any]:
    output = run(cmd, stdin=stdin)
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse JSON from command output:\n{output}") from exc


def ensure_gh_auth() -> None:
    run(["gh", "auth", "status"])


def get_pr_ref(pr_number: int | None) -> PullRequestRef:
    cmd = ["gh", "pr", "view"]
    if pr_number is not None:
        cmd.append(str(pr_number))
    cmd.extend(["--json", "number,url,title,headRepositoryOwner,headRepository"])
    payload = run_json(cmd)
    return PullRequestRef(
        owner=payload["headRepositoryOwner"]["login"],
        repo=payload["headRepository"]["name"],
        number=int(payload["number"]),
        url=payload["url"],
        title=payload["title"],
    )


def fetch_timeline(pr: PullRequestRef) -> list[dict[str, Any]]:
    payload = run_json(
        [
            "gh",
            "api",
            "graphql",
            "-F",
            "query=@-",
            "-F",
            f"owner={pr.owner}",
            "-F",
            f"repo={pr.repo}",
            "-F",
            f"number={pr.number}",
        ],
        stdin=TIMELINE_QUERY,
    )
    errors = payload.get("errors") or []
    if errors:
        raise RuntimeError(f"GitHub GraphQL errors: {json.dumps(errors)}")
    return payload["data"]["repository"]["pullRequest"]["timelineItems"]["nodes"]


def latest_review_request(nodes: list[dict[str, Any]]) -> str | None:
    timestamps = [
        node["createdAt"]
        for node in nodes
        if node.get("__typename") == "ReviewRequestedEvent"
    ]
    return max(timestamps) if timestamps else None


def latest_copilot_review(nodes: list[dict[str, Any]]) -> dict[str, Any] | None:
    reviews = [
        {
            "createdAt": node["createdAt"],
            "state": node["state"],
            "commitOid": (node.get("commit") or {}).get("oid"),
        }
        for node in nodes
        if node.get("__typename") == "PullRequestReview"
        and (node.get("author") or {}).get("login") == COPILOT_REVIEWER
    ]
    if not reviews:
        return None
    return max(reviews, key=lambda review: review["createdAt"])


def request_review(pr_number: int) -> None:
    run(["gh", "pr", "edit", str(pr_number), "--add-reviewer", COPILOT_REVIEWER])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Request or re-request GitHub Copilot review on a PR.",
    )
    parser.add_argument("--pr", type=int, help="Explicit pull request number")
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=0,
        help="Poll for a fresh Copilot review for up to this many seconds after requesting",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="Polling interval in seconds when --wait-seconds is used",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve the target PR and print the planned action without requesting review",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        ensure_gh_auth()
        pr = get_pr_ref(args.pr)
        timeline_before = fetch_timeline(pr)
        latest_request_before = latest_review_request(timeline_before)
        latest_review_before = latest_copilot_review(timeline_before)

        result: dict[str, Any] = {
            "pull_request": {
                "owner": pr.owner,
                "repo": pr.repo,
                "number": pr.number,
                "url": pr.url,
                "title": pr.title,
            },
            "requested_reviewer": COPILOT_REVIEWER,
            "dry_run": args.dry_run,
            "latest_review_request_before": latest_request_before,
            "latest_copilot_review_before": latest_review_before,
        }

        if args.dry_run:
            result["status"] = "dry-run"
            print(json.dumps(result, indent=2))
            return 0

        request_review(pr.number)

        request_event_confirmed = False
        request_event_created_at: str | None = None
        timeline_after_request = timeline_before

        for _ in range(6):
            timeline_after_request = fetch_timeline(pr)
            latest_request_after = latest_review_request(timeline_after_request)
            if latest_request_after and latest_request_after != latest_request_before:
                request_event_confirmed = True
                request_event_created_at = latest_request_after
                break
            time.sleep(2)

        latest_review_after = latest_copilot_review(timeline_after_request)
        new_review = None
        if latest_review_after and latest_review_after != latest_review_before:
            new_review = latest_review_after

        waited_seconds = 0
        if args.wait_seconds > 0 and new_review is None:
            deadline = time.time() + args.wait_seconds
            while time.time() < deadline:
                sleep_for = min(args.poll_interval, max(1, int(deadline - time.time())))
                time.sleep(sleep_for)
                waited_seconds += sleep_for
                polled_nodes = fetch_timeline(pr)
                latest_review_after = latest_copilot_review(polled_nodes)
                if latest_review_after and latest_review_after != latest_review_before:
                    new_review = latest_review_after
                    break

        result.update(
            {
                "status": "review-posted" if new_review else "requested",
                "request_command_succeeded": True,
                "request_event_confirmed": request_event_confirmed,
                "request_event_created_at": request_event_created_at,
                "waited_seconds": waited_seconds,
                "new_copilot_review": new_review,
            }
        )
        print(json.dumps(result, indent=2))
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
