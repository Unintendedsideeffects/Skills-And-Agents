---
name: claude-diff-review
description: Run Claude CLI in non-interactive mode to review git diffs between branches or commits and return severity-ordered findings with file references. Use when a user asks for a "Claude review", wants a second-opinion code review from Claude, or needs fast triage of a large branch diff like master...feature.
---

# Claude Diff Review

Use Claude as a local review engine for branch/commit diffs, then verify top findings before reporting them.

## Workflow

1. Confirm review scope and default range:
- Default to `master...fork-drift` when the user does not specify.
- Accept any explicit git range from the user, for example `main...feature-x` or `abc123..def456`.

2. Inspect scope before asking Claude:
```bash
git diff --shortstat <range>
git diff --name-only <range> | sed -n '1,200p'
```

3. Run Claude review:
```bash
scripts/review.sh "<range>"
```
- Optional focus override:
```bash
scripts/review.sh "<range>" "correctness, security, test gaps"
```

4. Verify high-severity findings locally:
```bash
git diff <range> -- <path>
```
- Confirm each referenced issue is in the current diff.
- Drop stale or unsupported findings before reporting.

5. Report results in review format:
- Findings first, ordered by severity.
- Include concrete file references with line numbers when possible.
- Add short open questions only when blocking uncertainty exists.

## Notes

- Keep prompts concise and explicit; ask for severity ordering and file references every time.
- For huge diffs, ask Claude for high-risk triage first, then drill down manually on flagged files.
- If `claude` is not installed or authenticated, fail fast and report the blocker.

## Files

- `scripts/review.sh`: run non-interactive Claude review for a git diff range.
