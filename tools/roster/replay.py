#!/usr/bin/env python3
"""Replay a past day's TLDR stories through the private roster step, locally, with the real roster.

    .venv/Scripts/python tools/roster/replay.py --issue 2026-11-24 --day 2026-11-25            dry: counts only
    ... --print            also show the private Telegram text in this terminal (never in CI)
    ... --send             send it to Telegram (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID from the environment
                           or %USERPROFILE%\\.config\\ai-morning\\telegram.env)
    ... --script OUT.txt   also write the episode script (one Claude API call) to OUT.txt, outside the repo
Nothing is written to data/ or docs/. Builds the roster in memory; does not upload it.
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tools" / "roster")]
import build_roster as B  # noqa: E402
import generate as g  # noqa: E402
import roster as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", required=True, help="TLDR issue date, YYYY-MM-DD")
    ap.add_argument("--day", help="episode date shown in the message (default: issue date)")
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--script")
    args = ap.parse_args()
    day = args.day or args.issue
    tldr = {}
    for topic in g.TLDR_TOPICS:
        r = g.http_get(f"https://tldr.tech/{topic}/{args.issue}")
        items = g.parse_tldr(r.text) if r.status_code == 200 else []
        tldr[topic] = {"newsletter": f"TLDR {topic}", "issue_date": args.issue, "items": items, "status": "ok"}
    blogs = {"engineering": [], "security": []}
    _, packed, *_ = B.build(B.CONFIG_DIR / "roster-projects.txt")
    stack = R.run(packed, day, tldr, blogs)
    print(f"Matched package names (public, from story text): {', '.join(stack.names) or 'none'}")
    print(f"Telegram message: {'yes' if stack.message else 'none (no match)'}")
    if args.print and stack.message:
        print("----- private -----\n" + stack.message + "\n-------------------")
    if args.send:
        env_file = B.CONFIG_DIR / "telegram.env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        R.send_telegram(stack.message)
    if args.script:
        out = Path(args.script).resolve()
        if ROOT in out.parents:
            sys.exit("Write the replay script outside the repo.")
        now = datetime.fromisoformat(day).replace(hour=7, tzinfo=g.TZ)
        picks = {"opening": g.OPENINGS[0], "tone": g.TONES[0], "dynamic": g.DYNAMICS[0], "signoff": g.SIGNOFFS[1]}
        title, body = g.write_script(g.build_prompt(now, None, tldr, blogs, picks, {"episodes": []},
                                                    stack_names=stack.names))
        turns = g.drop_leaks(g.parse_turns(body), guard=stack.guard)
        if stack.guard.leaks(title):
            title = "Your AI morning"
        out.write_text(f"{title}\n\n" + "\n".join(f"{w}: {s}" for w, s in turns) + "\n", encoding="utf-8")
        print(f"Script: {len(turns)} turns written to {out}")


if __name__ == "__main__":
    main()
