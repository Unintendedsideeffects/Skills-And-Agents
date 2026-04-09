---
name: gh-request-copilot-review
description: Request or re-request GitHub Copilot review on the open PR for the current branch, or on a specified PR number, using gh CLI; verify gh auth first, trigger the reviewer request, and confirm GitHub recorded a fresh review request event.
---

# GitHub Copilot Review Request

Use this skill when the user asks to ask Copilot to review a PR, re-run Copilot review after new commits, or confirm that a Copilot review request was sent.

Prerequisites:
- Run from inside the target Git repository.
- `gh auth status` must succeed.
- The current branch must have an open PR unless the user gives a PR number.

## Workflow

1. Check GitHub CLI auth with `gh auth status`.
2. Run `scripts/request_copilot_review.py`.
   - Default target: the open PR for the current branch.
   - Explicit PR: `--pr 123`.
   - Preview only: `--dry-run`.
   - Wait for a fresh Copilot review after requesting: `--wait-seconds 120`.
3. Summarize the result with the PR URL, whether a fresh review-request event was confirmed, and whether a new Copilot review appeared while polling.

## Command

From the repository checkout, run:

```bash
scripts/request_copilot_review.py
```

Useful variants:

```bash
scripts/request_copilot_review.py --pr 123
scripts/request_copilot_review.py --dry-run
scripts/request_copilot_review.py --wait-seconds 180
```

## Notes

- GitHub Copilot review does not automatically re-run after every push. Re-requesting Copilot as a reviewer is the supported way to trigger another review.
- If the request succeeds but no new review appears immediately, report that the request landed and Copilot is still queued.
- If `gh auth status` fails, stop and tell the user to authenticate with `gh auth login`.
