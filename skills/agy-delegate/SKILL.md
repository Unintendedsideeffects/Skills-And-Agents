---
name: agy-delegate
description: Delegate a bounded, well-specified coding task to the agy (Antigravity) CLI, then review and verify the result yourself. Use when the user asks to delegate work to agy, says "use agy", or wants one or more agy executors to implement a plan/brief while you supervise and run the gates. Covers dispatch mechanics, model-tier choice, worktree isolation, the edits-only/operator-runs-gates split, and the review checklist.
---

# agy delegate

`agy` is the Antigravity CLI — a cheaper executor you hand a **precise brief** to.
Your job is supervisor, not typist: write (or point at) a self-contained brief,
dispatch agy, then **verify the diff and run the gates yourself**. agy's exit code
is not a verdict; the diff is.

Default model is **Gemini 3.5 Flash (Medium)**. Flash is excellent at mechanical,
well-specified work and weak at numeric/spatial reasoning and recovering from
ambiguity. The more precise the brief, the better Flash does — so the brief is the
product, the same way it is for a handoff plan.

## When to use

- The user says "use agy", "delegate to agy", "have agy fix/implement …", or hands
  you a plan and asks for one executor per item.
- The work is bounded and specifiable: known files, known verification command.
- You want parallelism across **disjoint** write scopes (one agy per scope).

Do NOT use agy for exploratory work, anything where the spec is fuzzy, or tasks where
you can't state a machine-checkable done-criterion. Specify it first (or write an
`improve`-style plan), then delegate.

## Dispatch mechanics

### The one rule that bites: do NOT `nohup … &` inside a tracked background task

Run `agy` **directly** as the background command so the harness tracks agy's real
lifetime and notifies you when **agy** exits:

```bash
# CORRECT — harness completion fires when agy actually finishes:
agy --dangerously-skip-permissions --print-timeout 50m \
    --print "$(cat /abs/brief-or-instruction)" \
    > /tmp/agy-001.log 2>&1
#   ^ launch this via the Bash tool with run_in_background: true
```

```bash
# WRONG — double-detaches: the harness "completed" event fires at LAUNCH,
# not when agy exits, so you lose the completion notification and fly blind:
nohup agy --print "…" > /tmp/agy-001.log 2>&1 &
```

If you've already launched a detached agy (or it's a plain shell, not Claude Code),
bridge the gap with a tracked waiter so you still get one notification on real exit:

```bash
while pgrep -f "agy --dangerously" >/dev/null 2>&1; do sleep 10; done
echo "=== agy exited ==="; tail -25 /tmp/agy-001.log    # + your gate checks here
```

### Flags that matter

- `--print "<prompt>"` (alias `-p`/`--prompt`): non-interactive single run.
- `--dangerously-skip-permissions`: auto-approve agy's tool calls. Required for
  unattended runs (otherwise it blocks on its first edit).
- `--print-timeout 50m`: agy **burns wall-clock polling its own builds** ("I will
  continue waiting" ×10). The default 5m is far too short for any build-verified run.
  Give 50m+. On timeout agy is killed by signal → **exit 144** (this is a timeout,
  NOT a rate limit; rate limits print an error and exit cleanly on their own).
- `--model <tier>`: override per dispatch. `agy models` lists them. Menu includes
  Gemini 3.1 Pro (Low/High), Claude Sonnet/Opus (Thinking), GPT-OSS 120B.
- `--add-dir <dir>`: add a directory to agy's workspace (use when running against a
  worktree whose path differs from cwd).

### Point agy at the brief on disk

Pass a short instruction that **references an absolute brief/plan path**, rather than
inlining the whole brief. The file survives retries, shrinks reading overhead, and
keeps the prompt stable. See "Prompt template" below.

### Watch progress

agy's `--print` buffers — the log/`.output` stays sparse until it flushes. Watch via
the log file size + `git status --short` in the target tree. Note: **Gemini 3.1 Pro
(High) buffers ALL output until exit** (log stays 0 bytes while working) — don't treat
a 0-byte log as a hang for Pro; watch the deliverable file instead.

## Model tier → task

| Tier | Use for |
|---|---|
| Gemini 3.5 Flash (default) | Mechanical, fully-specified edits; adding tests; rote refactors |
| Gemini 3.1 Pro (High) | Geometry/layout arithmetic, concurrency/lock reasoning, architecture, linker-cone debugging |
| Claude / GPT-OSS | When you want a different reasoning style for a cross-check |

Match tier to where the *correction cycles* will come from. Flash that needs three
rounds of geometry fixes is more expensive than one Pro run.

## The edits-only / operator-runs-gates split

agy has two failure modes you must design around:

1. **Silent session death while "waiting"**: agy exits (sometimes exit 0) mid-flight,
   having completed its **edits** but never running/finishing the gates or printing the
   required final SUMMARY. The log ends on a "waiting for build" line.
2. **Instant no-op**: empty log, exits immediately; a retry may also no-op.

So: **never trust an exit code as completion.** Treat agy as doing *edits only* and
**run every verification gate yourself** from the diff. Require a SUMMARY at the end of
the prompt; if it's missing, the run died in mode (1) — re-derive completion from the
gates, don't re-dispatch blindly.

## Decomposition: serial vs parallel

Delegate by **disjoint write scope** — one agy per set of files no other agy touches.

- **agy DOES respect linked `git worktree`s as of v1.1.7** (re-probed live 2026-07-26).
  Launched with cwd set to a linked worktree, `git rev-parse --show-toplevel` resolves to
  the worktree, edits land there, and the main tree stays clean. A worktree **is** valid
  isolation on current versions.
  - **This was NOT true on older builds.** Observed 2026-06-15 (agy ~v1.0.x): it resolved
    the repo via the shared git common-dir and wrote every edit to the **main** tree, so
    two worktree-targeted runs both landed in main and collided. Fixed somewhere between
    v1.0.x and v1.1.7.
  - **Check `agy --version` before relying on this.** Below 1.1.7, or unverified, fall back
    to a separate clone per agent, or serialize in one checkout.
  - **Re-probe rather than trusting this note** — it is a version-dependent claim that has
    already flipped once. Throwaway clone → worktree off it → run agy in the worktree with
    "create WORKTREE_PROBE.txt containing pwd, `git rev-parse --show-toplevel`, and
    `git branch --show-current`" → check which tree the file landed in. Costs one tiny run.
  - Separate clones are still preferable when agents run **heavy builds**, because a
    worktree shares the build dir and package cache regardless. That constraint is about
    the toolchain, not about git.
- **Two agy tasks that edit the same file** (a shared test-runner manifest, a
  registration table) will conflict. Serialize them in one checkout (sequential edits
  stack cleanly) and verify between runs.
- **Two agy tasks that build into the same output dir collide even if their source
  edits are disjoint** — e.g. several "add a host test" tasks each run the same
  `bash test/run_host_tests.sh` which compiles into one shared `build/` and links one
  shared binary. Concurrent runs in the same checkout corrupt those object files / race
  the link. Serialize, or give each agent a separate clone.
- **Never run two heavy builds concurrently** if the toolchain shares a global cache
  (PlatformIO's `~/.platformio`, a shared build dir). If multiple agy runs would each
  build, either serialize, or have agy do *edits + the light gate only* and run the heavy
  build yourself once at integration. **agy also dies silently while polling a long
  build** (15–30 min firmware compiles), so deferring the heavy build to the operator is
  usually right regardless of concurrency — pass it as a per-dispatch instruction
  override: "do NOT run `pio run`; the operator runs that gate."
- An agent in flight is never a reason to idle: with harness-tracked background dispatch,
  you're notified on each exit, so sequence disjoint work and verify between exits.

## Isolation for parallel agy runs — worktree or clone

On **agy ≥ 1.1.7** a linked `git worktree` isolates agy correctly (see Decomposition), so it
is the cheap default: no re-clone, no dep seeding, shares the object store. On **older
builds it does not** — verify with `agy --version`, or re-probe, before relying on it.

Reach for a **separate clone** (`git clone --reference <main> …` for speed) when any of
these holds:

- agy will run **heavy builds** — a worktree shares the build dir and the package cache, so
  concurrent builds still collide. This is a toolchain constraint, not a git one.
- You are on an agy build older than 1.1.7, or cannot verify the version.
- You want the agent to see a pristine base SHA while your main tree carries unrelated
  uncommitted work.

Either way: neutralize hooks, seed build deps if it will build, then integrate the diffs
yourself. **Neutralize hooks in any agent tree** — agy has committed against "do NOT commit"
instructions, and a pre-commit build is expensive.

**Gitignored paths do not exist in a fresh clone.** If briefs live under a gitignored tree
(e.g. `plans/`), copy them in explicitly after cloning, or the agent reads nothing and
improvises the task from its prompt alone. A worktree has the same gap. See
`delegation_clone_setup_gotchas`.

```bash
# Separate CLONE per agent (this is what actually isolates agy):
git clone --reference /abs/main-checkout <repo-url-or-path> /abs/clone-001
git -C /abs/clone-001 config core.hooksPath /tmp/agy-no-hooks   # empty dir — neutralize
# Seed build deps so a cold clone doesn't re-install / touch the shared package cache.
# A symlink to the main checkout's .pio is validated for the host-test path: the
# bootstrap checks `[ -d $ROOT_DIR/.pio/libdeps/... ]` and SKIPS `pio pkg install` when
# present, so it never touches ~/.platformio. libdeps headers are read-only → concurrent
# reads across clones are safe; build OUTPUT goes to each clone's own build/ (not .pio).
ln -sfn /abs/main-checkout/.pio /abs/clone-001/.pio    # or copy .pio/libdeps
```

- Dispatch agy with cwd = the **clone**:
  `scripts/run.sh --cwd /abs/clone-001 --brief … --log … [--model …]` launched with
  `run_in_background:true` so each agy is independently harness-tracked and fires its own
  completion event. (On agy ≥ 1.1.7 `--cwd` isolates correctly for a worktree as well as a
  clone; on older builds only a real clone isolates.)
- Integrate by reading each clone's `git diff` and applying the patch to main yourself
  (you never let agy push). Resolve small overlaps (e.g. each clone appended one line to
  a shared manifest) by hand.
- `git worktree`s are also the right tool for **your own** operator gates — running a
  build/test against a base-SHA tree while agents hold uncommitted work in main. Recipe:
  `git worktree add -b advisor/op /abs/wt <base-sha>`; index-corruption recovery after a
  failed in-hook commit: `rm -f .git/worktrees/<name>/index && git -C <wt> reset`
  (use `rm -f` — interactive `rm` kills non-interactive shells; main object store is
  unaffected).

If instead you neutralize hooks in the **main** checkout (serial dispatch there), save
and restore them:

```bash
git config --get core.hooksPath          # remember it (e.g. scripts/hooks)
git config core.hooksPath /tmp/agy-no-hooks   # neutralize
# … dispatch agy runs …
git config core.hooksPath scripts/hooks   # RESTORE when done — don't leave hooks off
```

## Review checklist (what actually catches things)

- **Re-derive every arithmetic/layout value** agy produced from the source metrics —
  "compiles but wrong" is Flash's dominant failure mode.
- **Diff build-config files even if out of scope** — agy tooling has round-tripped
  `platformio.ini`/INI files through a parser, stripping comments and injecting stray
  overrides. `git checkout -- <config>` in the worktree before integrating if so.
- **Grep new user-facing string literals for missing i18n** (`tr(...)`) — agy hardcodes
  strings despite the rule being in the prompt.
- **Verify agent pushback empirically, not by re-reading the brief.** When agy says a
  brief item is "hallucinated/already done", check the code — sometimes the brief is
  stale (your bug) and agy is right to deviate; sometimes it's wrong. One temporary log
  line beats three rounds of theorizing.
- **Registration-table completeness** — a new entry often needs rows in several tables
  (key + topic/group + schema regen + predicate); agents reliably miss one.
- **Lock graphs** — if agy added locking, trace who calls back into locked methods
  (friends, serializers, callbacks); it has introduced reentry deadlocks.
- **Test edits**: distinguish "updated to assert new intended behavior" (fine) from
  "weakened the assertion to make it pass" (not fine).

## Out-of-scope findings — report, never fix, always record

A narrow write scope is what makes delegation safe, but an agent working inside one
sees things nobody else will: dead code next to the line it is editing, a second
instance of the bug it was sent to fix, a gate nobody runs. **That observation is the
most perishable output of the run.** If it only appears in a log tail, it is gone.

The rule:

- **Do not fix it.** Out-of-scope is out-of-scope; fixing it silently destroys the
  reviewability of the diff, which is the whole point of the scope.
- **Report it in the SUMMARY**, explicitly, under its own heading — not buried in prose.
- **Append it to the shared findings register**, which is common to every agent and
  every human on the project and is the durable record.

Every entry is timestamped and self-contained, because the reader has no session context:

```markdown
## 2026-07-26T14:32Z — <one-line claim>
- **Found by**: agy / codex / claude / human — during plan <NNN>
- **Where**: `path/to/file.cpp:123`
- **What**: what is actually wrong, in one or two sentences.
- **Why not fixed here**: out of scope for plan <NNN> (scope was <files>).
- **Status**: open | planned as <NNN> | fixed in <commit> | wontfix (reason)
```

Append only, newest at the bottom; never rewrite someone else's entry — change its
**Status** line instead. Reviewers sweep the open entries when planning the next wave.

**Register location**: the project's tracked findings file. It MUST be a path that is
committed to the repo — a scratch directory or a gitignored tree does not reach other
clones, worktrees, or humans, which defeats the purpose. Check the project's
`CLAUDE.md` for the path before dispatching, and tell the agent the absolute path in
its brief.

## The regression escalation ladder

When a regression is found, how hard you defend against it depends on how many times
it has now happened — not on how bad it felt this time:

| Occurrence | Required response |
|---|---|
| **1st** | **A test.** Reproduce it in the suite. A fix without a test is not a fix. |
| **2nd** | **Documentation.** The test clearly was not enough to change behaviour, so write down *why* this keeps happening — in the code as a comment at the trap, and in the project docs. |
| **3rd** | **A gate.** Stop relying on people remembering. It becomes a CI leg, a pre-commit check, or a required build matrix entry — something that fails automatically. |

The ladder only ratchets up. Reaching the third rung means the earlier two failed, so
add the gate *in addition to* the test and the docs, never instead of them.

This applies to classes of regression, not literal identical bugs: two different
compile breaks both caused by "no build exercises this compile gate" are the **same**
regression occurring twice, and the second one earns documentation of the gap.

## Prompt template

```text
You are executing a precise implementation plan with zero prior context. Read the
brief at <ABS PATH> and follow it EXACTLY, step by step, in order. Run every
verification command and confirm the expected result before moving on. The primary
gate is <COMMAND> run from <DIR> — it must <EXPECTED>. Honor all STOP conditions
verbatim — if one triggers, STOP and explain rather than improvising. Do NOT run
"git commit", "git push", or <FORBIDDEN BUILD>. Your working directory is <DIR>.
When finished, update <STATUS LOCATION>.

If you notice a problem OUTSIDE your scope, do NOT fix it. Record it: append a
timestamped entry to <FINDINGS REGISTER ABS PATH> using the format already in that
file, and list it in your SUMMARY under "OUT OF SCOPE FINDINGS". An unrecorded
observation is a lost one.

If you fix a regression, add a test that reproduces it — a fix without a test does
not count as complete.

End your response with a SUMMARY section: (1) every file you created/modified,
(2) each gate and whether it passed with the key output line, (3) any STOP condition
hit, (4) OUT OF SCOPE FINDINGS (or "none").
```

State ownership scope and forbidden work explicitly (no unrelated edits, no pushes,
no broad cleanup). For build-heavy parallel runs, add: "do edits + <light gate> only;
do NOT run <heavy build>."

## After the run

1. Read the log tail; confirm it ends with the SUMMARY (not a "waiting for build" line).
2. `git status --short` + `git diff` — confirm scope; nothing out of bounds.
3. Run the real gate yourself (build/test) — agy may have skipped or died before it.
4. Apply the review checklist to the actual diff.
5. **Harvest out-of-scope findings.** Read the SUMMARY's findings section and confirm
   each one actually landed in the findings register. Agents that die mid-run (a
   routine failure mode) never write theirs — transcribe those yourself from the log
   before the log is gone. Anything you spotted during review goes in the same file.
6. Restore any neutralized hooks; remove temp worktrees (`git worktree remove`).
7. Report what changed, gate results, and any concern — do not claim "done" off the
   exit code alone.

## Notes

- `agy --continue` (`-c`) resumes the most recent conversation — good for sequential
  leaves on one branch; a parallel branch needs a fresh dispatch with full context from
  inside its worktree.
- `scripts/run.sh` wraps the correct invocation (validates `agy` on PATH, takes a brief
  file + log path + optional model). Launch it via the Bash tool with
  `run_in_background: true` so the harness tracks the real agy lifetime.

## Files

- `scripts/run.sh`: validate `agy` is installed and run
  `agy --dangerously-skip-permissions --print-timeout <T> [--model M] --print "$(cat BRIEF)"`,
  redirecting to a log. Does NOT background — the caller backgrounds it via the harness.
