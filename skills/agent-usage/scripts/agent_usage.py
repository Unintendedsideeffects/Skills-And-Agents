#!/usr/bin/env python3
"""Token usage, cost and quota of headless agent-CLI runs, in one ledger.

Each agent CLI can write a machine-readable result; the readers below turn
that file into one normalized record:

  agent     run it with                                 usage comes from
  codex     codex exec --json ... > run.jsonl           turn.completed.usage (+ quota
                                                        from the thread's session log)
  claude    claude -p ... --output-format json > r.json usage, total_cost_usd, modelUsage
  agy       agy --print ... --output-format json        usage
  cursor    cursor-agent -p ... --output-format json    usage
  copilot   copilot -p ... --output-format json         result.usage.premiumRequests +
            (JSONL)                                     session.usage_checkpoint tokens/credits
  opencode  opencode run --format json ... (JSONL)      sessionID -> opencode.db message tokens
  gemini    gemini -p ... -o json                       stats.models.*.tokens (schema not
                                                        verified on this box: no gemini auth)

    agent_usage.py record <agent> <file> [--label NAME] [--no-ledger] [--json]
    agent_usage.py answer <agent> <file>   # the final reply as text (for logs)
    agent_usage.py summary [--days N]      # ledger totals per day / agent / label
    agent_usage.py quota codex             # live 5h/weekly % left via codex /status

Ledger: ~/.local/state/agent-usage/ledger.jsonl (override AGENT_USAGE_LEDGER),
one JSON object per run, append-only. Standard library only.

Normalized tokens: input (uncached prompt), cache_read, cache_write, output,
reasoning. Costs are what the CLI reports (claude: list price, also on a
subscription; opencode: provider cost) and are not comparable across agents.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sqlite3
import sys

LEDGER = os.environ.get("AGENT_USAGE_LEDGER",
                        os.path.expanduser("~/.local/state/agent-usage/ledger.jsonl"))
TOKENS = ("input", "cache_read", "cache_write", "output", "reasoning")
ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07")


class UsageError(Exception):
    pass


def _objects(path):
    """Every JSON object in a file: one document, or one per line (JSONL),
    tolerating ANSI codes and CRs from a pty wrapper."""
    text = ANSI.sub("", open(path, encoding="utf-8", errors="replace").read()).replace("\r", "")
    text = text.strip()
    if not text:
        raise UsageError("%s is empty" % path)
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, list) else [doc]
    except ValueError:
        pass
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    if not out:
        start = text.find("{")
        if start >= 0:
            try:
                out.append(json.loads(text[start:]))
            except ValueError:
                pass
    if not out:
        raise UsageError("no JSON found in %s" % path)
    return out


def _tokens(**kw):
    return {k: int(kw.get(k) or 0) for k in TOKENS}


def _add(a, b):
    return {k: a.get(k, 0) + b.get(k, 0) for k in TOKENS}


# ── readers: file -> partial record ──────────────────────────────────────────

def read_codex(path):
    thread, tok, turns, failed = None, _tokens(), 0, False
    for ev in _objects(path):
        kind = ev.get("type")
        if kind == "thread.started":
            thread = ev.get("thread_id")
        elif kind == "turn.completed":
            u = ev.get("usage") or {}
            turns += 1
            cached = int(u.get("cached_input_tokens") or 0)
            tok = _add(tok, _tokens(input=int(u.get("input_tokens") or 0) - cached, cache_read=cached,
                                    cache_write=u.get("cache_write_input_tokens"),
                                    output=u.get("output_tokens"), reasoning=u.get("reasoning_output_tokens")))
        elif kind in ("turn.failed", "error"):
            failed = True
    return {"session": thread, "tokens": tok, "turns": turns, "failed": failed, "quota": codex_quota(thread)}


def read_claude(path):
    res = [o for o in _objects(path) if o.get("type") == "result" or "total_cost_usd" in o]
    if not res:
        raise UsageError("no claude result object (use --output-format json or stream-json)")
    r = res[-1]
    u = r.get("usage") or {}
    return {"session": r.get("session_id"), "models": sorted((r.get("modelUsage") or {}).keys()),
            "tokens": _tokens(input=u.get("input_tokens"), cache_read=u.get("cache_read_input_tokens"),
                              cache_write=u.get("cache_creation_input_tokens"), output=u.get("output_tokens"),
                              reasoning=(u.get("output_tokens_details") or {}).get("thinking_tokens")),
            "cost_usd": r.get("total_cost_usd"), "turns": r.get("num_turns"), "failed": bool(r.get("is_error"))}


def read_agy(path):
    objs = [o for o in _objects(path) if isinstance(o.get("usage"), dict)]
    if not objs:
        raise UsageError("no agy usage object (use --output-format json)")
    u = objs[-1]["usage"]
    return {"session": objs[-1].get("session_id") or objs[-1].get("conversation_id"),
            "tokens": _tokens(input=int(u.get("input_tokens") or 0) - int(u.get("cache_read_tokens") or 0),
                              cache_read=u.get("cache_read_tokens"), output=u.get("output_tokens"),
                              reasoning=u.get("thinking_tokens")),
            "seconds": objs[-1].get("duration_seconds")}


def read_cursor(path):
    objs = [o for o in _objects(path) if isinstance(o.get("usage"), dict)]
    if not objs:
        raise UsageError("no cursor-agent usage object (use --output-format json)")
    o = objs[-1]
    u = o["usage"]
    return {"session": o.get("session_id"),
            "tokens": _tokens(input=int(u.get("inputTokens") or 0) - int(u.get("cacheReadTokens") or 0),
                              cache_read=u.get("cacheReadTokens"), cache_write=u.get("cacheWriteTokens"),
                              output=u.get("outputTokens")),
            "failed": bool(o.get("is_error"))}


def read_copilot(path):
    objs = _objects(path)
    result = next((o for o in reversed(objs) if o.get("type") == "result"), {})
    snap = next((o for o in reversed(objs) if o.get("type") == "session.usage_checkpoint"), {})
    acct = (snap.get("data") or {}).get("accountingSnapshot") or {}
    tok, models, nano = _tokens(), [], 0
    for model, m in (acct.get("modelMetrics") or {}).items():
        models.append(model)
        u = m.get("usage") or {}
        tok = _add(tok, _tokens(input=int(u.get("inputTokens") or 0) - int(u.get("cacheReadTokens") or 0)
                                - int(u.get("cacheWriteTokens") or 0),
                                cache_read=u.get("cacheReadTokens"), cache_write=u.get("cacheWriteTokens"),
                                output=u.get("outputTokens"), reasoning=u.get("reasoningTokens")))
        nano += int(m.get("totalNanoAiu") or 0)
    usage = result.get("usage") or {}
    if not result and not acct:
        raise UsageError("no copilot result/usage_checkpoint events (use --output-format json)")
    return {"session": result.get("sessionId"), "models": sorted(models), "tokens": tok,
            "premium_requests": usage.get("premiumRequests", acct.get("totalPremiumRequestCost")),
            "ai_credits": round(nano / 1e9, 4) if nano else None}


def read_opencode(path, db=None):
    session = next((o.get("sessionID") for o in _objects(path) if o.get("sessionID")), None)
    if not session:
        raise UsageError("no sessionID in the opencode stream (use run --format json)")
    db = db or os.path.expanduser("~/.local/share/opencode/opencode.db")
    tok, cost, models = _tokens(), 0.0, set()
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    try:
        rows = con.execute("select data from session_message where session_id=? and type='assistant'", (session,))
        for (data,) in rows:
            d = json.loads(data)
            t = d.get("tokens") or {}
            cache = t.get("cache") or {}
            tok = _add(tok, _tokens(input=t.get("input"), cache_read=cache.get("read"), cache_write=cache.get("write"),
                                    output=t.get("output"), reasoning=t.get("reasoning")))
            cost += float(d.get("cost") or 0)
            m = d.get("model") or {}
            if m.get("id"):
                models.add("%s/%s" % (m.get("providerID"), m["id"]))
    finally:
        con.close()
    return {"session": session, "models": sorted(models), "tokens": tok, "cost_usd": round(cost, 6)}


def read_gemini(path):
    objs = [o for o in _objects(path) if isinstance(o.get("stats"), dict)]
    if not objs:
        raise UsageError("no gemini stats object (use -o json)")
    tok, models = _tokens(), []
    for model, m in ((objs[-1]["stats"].get("models")) or {}).items():
        models.append(model)
        t = m.get("tokens") or {}
        tok = _add(tok, _tokens(input=int(t.get("prompt") or 0) - int(t.get("cached") or 0), cache_read=t.get("cached"),
                                output=t.get("candidates"), reasoning=t.get("thoughts")))
    return {"session": objs[-1].get("session_id"), "models": sorted(models), "tokens": tok, "unverified_schema": True}


def answer(agent, path):
    """The agent's final reply as plain text, so logs stay readable with JSON output."""
    objs = _objects(path)
    if agent in ("claude", "cursor"):
        hits = [o.get("result") for o in objs if o.get("type") == "result" and isinstance(o.get("result"), str)]
    elif agent == "agy":
        hits = [o.get("response") for o in objs if isinstance(o.get("response"), str)]
    elif agent == "codex":
        hits = [(o.get("item") or {}).get("text") for o in objs
                if o.get("type") == "item.completed" and (o.get("item") or {}).get("type") == "agent_message"]
    elif agent == "copilot":
        hits = [(o.get("data") or {}).get("content") for o in objs if o.get("type") == "assistant.message"]
    elif agent == "opencode":
        hits = ["".join((o.get("part") or {}).get("text") or "" for o in objs if o.get("type") == "text")]
    elif agent == "gemini":
        hits = [o.get("response") for o in objs if isinstance(o.get("response"), str)]
    else:
        raise UsageError("unknown agent %r" % agent)
    hits = [h for h in hits if h]
    if not hits:
        raise UsageError("no final reply found in %s" % path)
    return hits[-1]


READERS = {"codex": read_codex, "claude": read_claude, "agy": read_agy, "cursor": read_cursor,
           "copilot": read_copilot, "opencode": read_opencode, "gemini": read_gemini}


# ── quota ────────────────────────────────────────────────────────────────────

def codex_quota(thread):
    """5h/weekly % left as of a codex thread, from its session log."""
    if not thread:
        return None
    best = None
    for path in glob.glob(os.path.expanduser("~/.codex/sessions/**/rollout-*%s.jsonl" % thread), recursive=True):
        for line in open(path):
            if '"rate_limits"' not in line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            p = ev.get("payload") or {}
            rl = p.get("rate_limits") or (p.get("info") or {}).get("rate_limits")
            if rl and (rl.get("primary") or rl.get("secondary")):
                best = rl
    if not best:
        return None
    out = {"plan": best.get("plan_type")}
    for name, key in (("5h", "primary"), ("weekly", "secondary")):
        w = best.get(key) or {}
        if w:
            r = w.get("resets_at")
            out[name] = {"left_percent": None if w.get("used_percent") is None else round(100 - float(w["used_percent"]), 1),
                         "resets": datetime.datetime.fromtimestamp(r).astimezone().isoformat(timespec="minutes")
                         if isinstance(r, (int, float)) else r}
    return out


def live_codex_status(binary="/usr/bin/codex"):
    """Drive codex's interactive /status in a pty (no model call) and parse it."""
    import fcntl
    import pty
    import select
    import struct
    import termios
    import time
    pid, fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.chdir(os.path.expanduser("~"))
        os.execv(binary, ["codex", "-s", "read-only"])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 160, 0, 0))
    buf = b""

    def pump(sec):
        nonlocal buf
        end = time.time() + sec
        while time.time() < end:
            if select.select([fd], [], [], 0.2)[0]:
                try:
                    buf += os.read(fd, 65536)
                except OSError:
                    return
    pump(6)
    os.write(fd, b"/status")
    pump(1)
    os.write(fd, b"\r")
    pump(5)
    os.write(fd, b"\x03")
    pump(1)
    os.write(fd, b"\x03")
    pump(1)
    try:
        os.kill(pid, 9)
    except OSError:
        pass
    text = buf.decode("utf-8", "replace")
    text = re.sub(r"\x1b\[(\d+)C", lambda m: " " * int(m.group(1)), text)
    text = re.sub(r"\s+", " ", ANSI.sub(" ", text))
    out = {}
    plan = re.search(r"\(([A-Za-z]+)\)\s+Collaboration", text) or re.search(r"Account: \S+ \(([^)]+)\)", text)
    if plan:
        out["plan"] = plan.group(1)
    for name, label in (("5h", "5h limit"), ("weekly", "Weekly limit")):
        m = re.search(re.escape(label) + r":.*?(\d+(?:\.\d+)?)% left \(resets ([^)]+)\)", text)
        if m:
            out[name] = {"left_percent": float(m.group(1)), "resets": m.group(2)}
    if "5h" not in out and "weekly" not in out:
        raise UsageError("could not read codex /status (logged in? interface changed?)")
    return out


# ── record / ledger ──────────────────────────────────────────────────────────

def record(agent, path, label=None):
    if agent not in READERS:
        raise UsageError("unknown agent %r (one of %s)" % (agent, ", ".join(sorted(READERS))))
    rec = {"at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "agent": agent,
           "label": label or os.path.basename(path), "file": os.path.abspath(path)}
    rec.update(READERS[agent](path))
    rec["tokens"]["total"] = sum(rec["tokens"][k] for k in TOKENS)
    return rec


def show(rec):
    t = rec["tokens"]
    extra = []
    for key, fmt in (("cost_usd", "cost $%s"), ("premium_requests", "premium requests %s"),
                     ("ai_credits", "AI credits %s"), ("turns", "turns %s")):
        if rec.get(key) is not None:
            extra.append(fmt % rec[key])
    print("%s  %s  session %s%s" % (rec["agent"], rec["label"], rec.get("session"),
                                   "  (FAILED)" if rec.get("failed") else ""))
    print("  input %d  cache-read %d  cache-write %d  output %d  reasoning %d  = %d%s" % (
        t["input"], t["cache_read"], t["cache_write"], t["output"], t["reasoning"], t["total"],
        ("  | " + ", ".join(extra)) if extra else ""))
    if rec.get("models"):
        print("  models: %s" % ", ".join(rec["models"]))
    for name in ("5h", "weekly"):
        q = (rec.get("quota") or {}).get(name)
        if q:
            print("  quota %-6s %s%% left, resets %s" % (name, q["left_percent"], q["resets"]))
    if rec.get("unverified_schema"):
        print("  note: this agent's JSON schema was not verified on this box")


def append(rec):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def summary(days=None):
    if not os.path.exists(LEDGER):
        raise UsageError("no ledger yet at %s" % LEDGER)
    cutoff = None
    if days is not None:
        cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    groups = {}
    for line in open(LEDGER):
        rec = json.loads(line)
        day = rec["at"][:10]
        if cutoff and day < cutoff:
            continue
        g = groups.setdefault((day, rec["agent"], rec.get("label") or ""), {"runs": 0, "cost": 0.0, "premium": 0,
                                                                          **dict.fromkeys(TOKENS + ("total",), 0)})
        g["runs"] += 1
        for k in TOKENS + ("total",):
            g[k] += rec["tokens"].get(k, 0)
        g["cost"] += float(rec.get("cost_usd") or 0)
        g["premium"] += int(rec.get("premium_requests") or 0)
    print("%-10s %-8s %-24s %4s %10s %9s %9s %10s %8s %4s" % (
        "day", "agent", "label", "runs", "input", "output", "reason", "total", "cost$", "prem"))
    for (day, agent, label), g in sorted(groups.items()):
        print("%-10s %-8s %-24s %4d %10d %9d %9d %10d %8.2f %4d" % (
            day, agent, label[:24], g["runs"], g["input"], g["output"], g["reasoning"], g["total"],
            g["cost"], g["premium"]))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="read one run's output file (and append it to the ledger)")
    r.add_argument("agent", choices=sorted(READERS))
    r.add_argument("file")
    r.add_argument("--label")
    r.add_argument("--no-ledger", action="store_true")
    r.add_argument("--json", action="store_true")
    s = sub.add_parser("summary", help="ledger totals per day / agent / label")
    s.add_argument("--days", type=int)
    t = sub.add_parser("answer", help="print the agent's final reply from its JSON output")
    t.add_argument("agent", choices=sorted(READERS))
    t.add_argument("file")
    q = sub.add_parser("quota", help="live quota where the CLI exposes it")
    q.add_argument("agent", choices=["codex"])
    a = ap.parse_args(argv)
    try:
        if a.cmd == "record":
            rec = record(a.agent, a.file, a.label)
            print(json.dumps(rec)) if a.json else show(rec)
            if not a.no_ledger:
                append(rec)
        elif a.cmd == "summary":
            summary(a.days)
        elif a.cmd == "answer":
            print(answer(a.agent, a.file))
        else:
            print(json.dumps(live_codex_status(), indent=1))
    except (UsageError, OSError, sqlite3.Error) as exc:
        sys.exit("agent_usage: %s" % exc)


if __name__ == "__main__":
    main()
