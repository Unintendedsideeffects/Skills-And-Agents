---
name: dead-code
description: Detect and remove dead/unused code using language-appropriate static analysis tools (ruff+vulture, knip, cargo clippy, golangci-lint, etc.). Use when cleaning up after vibe-coding, AI-generated code, or any session that may have left unused imports, dead functions, or unreachable exports.
---

# Dead Code Detection

## How to run

```bash
~/.claude/skills/dead-code/scripts/run.sh [--fix] [--dir <path>] [--lang <python|ts|js|rust|go|php|ruby>]
```

- No flags → detect only, no writes
- `--fix` → apply safe auto-fixes (ruff, cargo clippy); never deletes files
- `--dir` → target a specific directory instead of cwd
- `--lang` → skip auto-detection and force a language

## After running

1. Summarize findings grouped by category: unused imports, dead functions, dead files, unused deps.
2. If `--fix` was passed, show `git diff --stat` to confirm what changed.
3. For **dead files** and **unused dependencies**: list them and ask the user to confirm before removing — never delete automatically.

## Tool matrix

| Language | Tools used | Auto-fixable |
|----------|-----------|-------------|
| Python | ruff (F401/F811/F841) + vulture | ruff only |
| TypeScript / JS | knip | No — manual |
| Rust | cargo clippy | `--fix --allow-dirty` |
| Go | staticcheck → go vet fallback | No |
| PHP | phpstan level 5 | No |
| Ruby | rubocop Lint/Unused* | No |

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Clean — no dead code |
| 1 | Findings present |
| 2 | Argument / setup error |
| 3 | No supported language detected |
