#!/usr/bin/env python3
"""Apply a guarded batch of vault moves/removals as ONE commit, then push.

usage: apply_ops.py <vault> <ops.json>
ops.json: {"msg": "commit message", "ops": [["rm", path], ["mv", src, dst], ["add", path]]}
env:   NO_VERIFY=1  pass --no-verify (use when a pre-commit hook has side effects)
       REMOTE=origin BRANCH=<current branch>

Refuses to run if anything is already staged, if any rm/mv source is dirty or untracked,
or if a mv destination exists. After staging, verifies the staged set equals exactly the
planned paths. 'add' is for canonical notes you just edited (merged content into).
"""
import json, os, subprocess, sys

vault, spec_path = sys.argv[1], sys.argv[2]
spec = json.load(open(spec_path)); os.chdir(vault); ops = spec['ops']
def g(*a): return subprocess.run(['git', *a], capture_output=True, text=True)

pre = g('diff', '--cached', '--name-only').stdout.strip()
if pre: sys.exit('PRESTAGED (aborting, unstage nothing yourself):\n' + pre)
for o in ops:
    if o[0] == 'mv' and os.path.exists(o[2]): sys.exit('DEST EXISTS ' + o[2])
    if o[0] in ('rm', 'mv'):
        s = g('status', '--porcelain', '--', o[1]).stdout.strip()
        if s: sys.exit('DIRTY ' + s)
    if g('ls-files', '--error-unmatch', '--', o[1]).returncode: sys.exit('UNTRACKED ' + o[1])

paths = []
for o in ops:
    if o[0] == 'rm': r = g('rm', '-q', '--', o[1]); paths.append(o[1])
    elif o[0] == 'mv':
        os.makedirs(os.path.dirname(o[2]) or '.', exist_ok=True); r = g('mv', '--', o[1], o[2]); paths += [o[1], o[2]]
    elif o[0] == 'add': r = g('add', '--', o[1]); paths.append(o[1])
    else: sys.exit('BAD OP %r' % o)
    if r.returncode: sys.exit('FAIL %s %s' % (o, r.stderr))

staged = set(g('diff', '--cached', '--name-only', '--no-renames').stdout.split('\n')) - {''}
extra = staged - set(paths)
if extra: sys.exit('EXTRA STAGED (not committing) %r' % extra)
print('staged', len(staged))

cmd = ['commit', '-qm', spec['msg']] + (['--no-verify'] if os.environ.get('NO_VERIFY') else [])
r = g(*cmd)
if r.returncode: sys.exit('COMMIT FAIL ' + r.stderr)
remote = os.environ.get('REMOTE', 'origin'); branch = os.environ.get('BRANCH') or g('branch', '--show-current').stdout.strip()
for _ in range(3):
    if g('push', '-q', remote, branch).returncode == 0: break
else: sys.exit('PUSH FAIL (commit is local)')
print('HASH', g('log', '-1', '--format=%h').stdout.strip())

for o in ops:   # prune folders emptied by moves/removals
    if o[0] in ('mv', 'rm'):
        d = os.path.dirname(o[1])
        while d and os.path.isdir(d) and not os.listdir(d): os.rmdir(d); d = os.path.dirname(d)
