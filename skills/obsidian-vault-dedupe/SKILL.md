---
name: obsidian-vault-dedupe
description: Merge duplicate folders (e.g. "X 1", "X copy") and deduplicate notes/attachments in a git-tracked Obsidian vault without touching the owner's uncommitted work. Use when asked to merge, dedupe or clean up duplicate folders or notes in a vault.
---

# Obsidian vault dedupe

Fold numbered/copied folders into their canonical sibling and remove duplicate notes, in
small safe commits, without ever touching the owner's uncommitted changes.

## Hard rules

- Any path in `git status --porcelain -uall` (modified, deleted, untracked) is OFF-LIMITS:
  never stage, move, edit, restore, stash, reset, clean or checkout it. Report it.
- Stage only explicit paths (`git add -- <p>`, `git rm -q -- <p>`, `git mv -- <a> <b>`).
  Never `git add -A`, `.` or `-u`.
- Before each commit, refuse if anything was already staged, and verify
  `git diff --cached --name-only --no-renames` equals exactly the planned set.
- Follow the vault's commit conventions (`--no-verify` if a pre-commit hook has side effects).
  Push after each commit, with retry.
- Exclude `.obsidian/`, `.git`, script folders, folders a sync tool or another agent manages,
  and anything the owner fenced off. Never print secrets found in notes.
- Move file by file, never whole folders: a folder move drags dirty files along.

## Helpers

```bash
S=<this skill dir>/scripts
EXCLUDE="Some/Managed/Folder/,Private/" python3 $S/find_dupes.py <vault> /tmp/dupes.json
NO_VERIFY=1 python3 $S/apply_ops.py <vault> ops.json   # {"msg": "...", "ops": [["rm",p],["mv",src,dst],["add",p]]}
```

`find_dupes.py` lists identical-hash groups, ` N.md` / ` (N).md` / ` copy.md` pairs
(similarity ratio plus unique-line counts) and same-basename notes in different folders, each
with git status per path (`ok` means clean and tracked). `apply_ops.py` re-checks every path,
commits once, pushes, and prunes emptied folders. On a remote machine, scp the scripts to
`/tmp` and run them with `python3` and absolute paths (that avoids zsh glob issues).

## Steps

1. **Inventory:** run `find_dupes.py`, then look for folder duplicates by eye or with `git ls-files`.
   These are basenames matching `^(.*?)( \d+| copy| \(\d+\)| - Copy)$` whose stripped sibling
   exists in the same parent, plus names that collide after folding case or separators.
2. **Folder duplicates:** if the contents are disjoint, `mv` each clean file into the canonical
   folder; dedupe any name clashes as in step 4. Note what stays behind because it's dirty.
3. **Stray copies:** for `*.md_`, `*_`, `*.bak*` and `*.work` files, compare against the
   twin's HEAD (`git show HEAD:<path> | diff`), normalising CRLF (`tr -d '\r'`).
   Also look for doubled names like `Prefix - Prefix - Title (X) (X).md`.
4. **Decide each pair:**
   - Identical, or differing only in frontmatter dates or a title suffix: delete the copy. Keep
     the better-named, better-placed file, i.e. the one other notes reference by path.
   - The copy has unique content: merge it into the canonical note (combine tags and aliases),
     `add` the canonical note, then delete the copy.
   - Substantive divergence, translations, draft-vs-published folders, or identical files
     under deliberately different names: don't merge; list them for the owner.
   - The canonical note is dirty, or a dirty file links to the copy: skip it.
   - Image-format twins (png/jpg vs webp): check which file the notes embed before deleting.
5. **Links:** for each deleted file, grep tracked `*.md` and `*.canvas` for `[[<basename>`,
   `<basename>.md` and the full path. Repoint links in clean files to the canonical note.
   Don't edit dirty index or MOC notes; report the rows that need updating.
6. **Commit per area:** one `apply_ops.py` run per folder family or top-level area, with a
   descriptive message. Record each hash.

## Pitfalls

- The owner may be partway through deduping locally, with hundreds of uncommitted deletions.
  Never stage them.
- Suffix regexes can falsely match years, like `(2026).md`. `find_dupes.py` only matches a single digit after the space.
- `_` copies often differ only in line endings.
- Generic basenames (README, index, notices) repeat legitimately.

## Report back

For each commit: hash, area, what moved, and each dedup decision (kept X, removed Y, merged what), plus links repointed.
Then list:
- items skipped because they're dirty or untracked;
- ambiguous pairs that need the owner's call;
- large classes not attempted, and why.
