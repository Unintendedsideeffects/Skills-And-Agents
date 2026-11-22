#!/usr/bin/env python3
"""Find duplicate-note candidates in a git-tracked Obsidian vault.

usage: find_dupes.py <vault> [out.json]
env:   EXCLUDE="dir1/,dir2/"   extra path prefixes to skip (.obsidian/ and .git always skipped)

Reports three kinds: 'hash' (identical clean tracked files), 'suffix' (`X 1.md`, `X (2).md`,
`X copy.md` with `X.md` present, with similarity ratio and unique-line counts) and 'samename'
(same basename in different folders, with min similarity among clean copies).
Each entry carries git status per path: 'ok' = clean and tracked; anything else is off-limits.
"""
import collections, difflib, json, os, re, subprocess, sys

vault = sys.argv[1]; out_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/vault-dupes.json'
os.chdir(vault)
EX = tuple(['.obsidian/', '.git/'] + [p for p in os.environ.get('EXCLUDE', '').split(',') if p])
GENERIC = {'readme.md', 'index.md', 'todo.md', 'changelog.md', 'license.md', 'agents.md', 'claude.md', 'notices.md'}

def git(*a): return subprocess.run(['git', *a], capture_output=True).stdout

st = {}; recs = git('status', '--porcelain', '-uall', '-z').split(b'\0'); i = 0
while i < len(recs):
    r = recs[i]
    if r: st[r[3:].decode()] = r[:2].decode(); i += 2 if r[:1] in b'RC' else 1
    else: i += 1

blobs = {}
for rec in git('ls-files', '-s', '-z').split(b'\0'):
    if not rec: continue
    meta, path = rec.split(b'\t', 1); path = path.decode()
    if not path.startswith(EX): blobs[path] = meta.split()[1].decode()
allp = set(blobs) | {p for p in st if not p.startswith(EX)}
status = lambda p: st.get(p, 'ok')

def rd(p):
    try: return open(p, encoding='utf-8', errors='replace').read()
    except Exception: return None
def ratio(a, b): return round(difflib.SequenceMatcher(None, a, b, autojunk=False).quick_ratio(), 3)

out = []
groups = collections.defaultdict(list)
for p, h in blobs.items():
    if status(p) == 'ok': groups[h].append(p)
for h, ps in groups.items():
    if len(ps) > 1: out.append(dict(kind='hash', paths=sorted(ps)))

for p in sorted(allp):
    m = re.match(r'^(.*?)(?: \d| \(\d+\)| copy)\.md$', p)   # single digit: avoids "(2026).md" style false hits
    if not m or (m.group(1) + '.md') not in allp: continue
    s = m.group(1) + '.md'; a, b = rd(s) or '', rd(p) or ''
    la, lb = set(a.splitlines()), set(b.splitlines())
    out.append(dict(kind='suffix', canon=s, dup=p, st=[status(s), status(p)], ratio=ratio(a, b),
                    onlyDup=sum(1 for l in lb - la if l.strip()), onlyCanon=sum(1 for l in la - lb if l.strip())))

bn = collections.defaultdict(list)
for p in allp:
    if p.endswith('.md') and os.path.basename(p).lower() not in GENERIC: bn[os.path.basename(p)].append(p)
for k, v in bn.items():
    if len(v) < 2: continue
    v = sorted(v); sts = [status(x) for x in v]; clean = [rd(x) or '' for x, s in zip(v, sts) if s == 'ok']
    r = min((ratio(clean[0], u) for u in clean[1:]), default=None)
    out.append(dict(kind='samename', paths=v, st=sts, minRatio=r))

json.dump(out, open(out_path, 'w'), indent=1)
print(f'{len(out)} candidates -> {out_path}', collections.Counter(x['kind'] for x in out))
