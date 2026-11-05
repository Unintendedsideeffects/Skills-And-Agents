---
name: opencode-delegate
description: Delegate a bounded analysis or implementation task to the OpenCode CLI, then review its output, diff, and verification independently. Use when the user asks to delegate to OpenCode or Big Pickle, or explicitly wants OpenCode used as an executor. Defaults to opencode/big-pickle and supports read-only and write-enabled modes without granting blanket auto-approval.
---

# OpenCode delegate

Use OpenCode as a bounded executor. The parent agent remains responsible for scope,
authorization, reviewing every change, and running the decisive verification gates.
OpenCode's exit code and final summary are evidence, not a success verdict.

## Prepare the delegation

Write a self-contained prompt or brief that states:

- the concrete outcome and done criteria;
- the exact working directory and owned files/modules;
- known pre-existing changes that must be preserved;
- allowed side effects and whether the task is read-only or may edit files;
- verification commands OpenCode should run, plus any gates reserved for the parent;
- `git commit`, `git push`, publishing, and external writes are forbidden unless the
  user separately authorized them.

If the task is ambiguous enough that different interpretations would produce
materially different changes, resolve that ambiguity before dispatch.

## Preflight

Before the first dispatch on a machine, or after an authentication/model error:

```bash
opencode --version
opencode models opencode
opencode providers list
```

Use the provider listing; never print or read `~/.local/share/opencode/auth.json`.
The default model is `opencode/big-pickle`. Override it only when the user requests a
different model, Big Pickle is unavailable, or the task has a clear model-specific
requirement.

Capture `git status --short` in every affected repository before dispatch. A dirty
tree is not automatically a blocker, but the prompt must identify unrelated work and
the final review must distinguish it from delegated edits.

## Dispatch

Use the bundled runner. It runs in the foreground intentionally; let the execution
harness track its real lifetime instead of wrapping it in `nohup` or a detached shell.

Read-only task from a prompt:

```bash
scripts/run.sh \
  --mode read \
  --cwd /absolute/working/directory \
  --log /tmp/opencode-read.jsonl \
  --prompt "Inspect the named files and report findings with file references."
```

Implementation from a maintained brief:

```bash
scripts/run.sh \
  --mode write \
  --cwd /absolute/working/directory \
  --brief /absolute/path/to/brief.md \
  --log /tmp/opencode-write.jsonl
```

Useful overrides are `--model provider/model`, `--agent name`, `--timeout 50m`,
`--title text`, and `--instruction text`. Use exactly one of `--prompt` or `--brief`.
The runner attaches a brief with OpenCode's `--file` flag rather than interpolating
its contents through the shell.

- `read` defaults to the `plan` agent and forbids file mutation in the generated
  instruction.
- `write` defaults to the `build` agent, but limits edits to the scope in the brief.
- The runner deliberately does not pass `--auto`. Do not add it merely to bypass a
  permission failure; determine what permission is requested and whether the user
  authorized that side effect.
- Timeout exit `124` means the process was stopped by the runner. Inspect the log and
  working tree before deciding whether a retry is safe.

For parallel write tasks, assign disjoint ownership and use isolated worktrees or
clones. Serialize tasks that share files, generated manifests, build directories, or
global tool caches. Tell every executor it is not alone and must not revert others.

When you create an isolated tree, seed it before dispatching:

- **Machine-local build config.** It is gitignored, so a fresh worktree/clone lacks it,
  and the build tool then falls back to writing its cache *inside the tree*. On
  crosspoint-reader that is a 3.7 GB SCons mirror per tree — 19 GB across 22 stale trees
  filled the root filesystem to 0 bytes on 2026-08-26. Run
  `scripts/seed-agent-tree.sh /abs/agent-tree [--link-libdeps] [--no-hooks]`, which gives
  the tree a private prunable `build_dir` and points `build_cache_dir` at the shared
  content-addressed cache.
- **Submodules.** A worktree does not inherit them, and git rejects a symlinked submodule
  path outright (`expected submodule path '<name>' not to be a symbolic link`). Run
  `git -C <tree> submodule update --init --recursive` — it resolves against the local
  object store and is fast.
- **Gitignored briefs or fixtures** the task depends on, copied in explicitly.

## Review and verify

After every run:

1. Read the JSONL log's final text and tool events. Confirm the executor used only
   tools appropriate to the assigned mode.
2. Compare the current status and diff with the preflight snapshot. Never revert or
   stage unrelated work.
3. Inspect every delegated edit locally. Check scope, error paths, tests, generated
   files, and repository instructions.
4. Run the decisive gates yourself. Do not rely solely on gates reported by OpenCode.
5. Report the model, exit status, files changed, gates run, and any unresolved limits.

If status changes during a read-only run, investigate timestamps, tool events, and
concurrent processes before attributing the change. Do not automatically discard it.

## Failure handling

- Missing credentials: stop and ask the user to authenticate with
  `opencode providers login`; never request the credential value in chat.
- Missing model: refresh with `opencode models opencode --refresh`, then select an
  available model or report the blocker.
- Empty/incomplete output: inspect the JSONL log and working tree; do not blindly
  redispatch a write task.
- Unexpected edits or external access: stop, preserve evidence, and review the exact
  diff/tool event before any cleanup.
