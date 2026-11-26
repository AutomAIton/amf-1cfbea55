"""Offline checks for the private dependency roster (builder, matching, verdicts, public-surface guards).
Imported by tests/selfcheck.py. No network: OSV and Telegram are mocked. Fake projects are zzproj-*."""
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "roster"))
sys.path.insert(0, str(ROOT))
import build_roster as B  # noqa: E402
import generate as g  # noqa: E402
import roster as R  # noqa: E402

# ---------------------------------------------------------------- Task 1: parsers (small fixture lockfiles)
npm3 = json.dumps({"lockfileVersion": 3, "packages": {
    "": {"name": "root", "version": "1.0.0"},
    "node_modules/binary-parser": {"version": "2.2.0"},
    "node_modules/@scope/kit": {"version": "1.4.0", "dev": True},
    "node_modules/a/node_modules/ms": {"version": "2.1.3"},
    "node_modules/local": {"link": True, "resolved": "packages/local"}}})
assert set(B.parse_npm_lock(npm3)) == {("npm", "binary-parser", "2.2.0", False), ("npm", "@scope/kit", "1.4.0", True),
                                       ("npm", "ms", "2.1.3", False)}
pnpm9 = """lockfileVersion: '9.0'

importers:

  .:
    dependencies:
      left-pad:
        specifier: ^1.3.0
        version: 1.3.0

packages:

  '@adobe/css-tools@4.5.0':
    resolution: {integrity: sha512-x}

  binary-parser@2.3.1:
    resolution: {integrity: sha512-y}

  react-dom@18.2.0(react@18.2.0):
    resolution: {integrity: sha512-z}

snapshots:

  ghost@9.9.9:
    dependencies: {}
"""
assert set(B.parse_pnpm_lock(pnpm9)) == {("npm", "@adobe/css-tools", "4.5.0", False),
                                         ("npm", "binary-parser", "2.3.1", False), ("npm", "react-dom", "18.2.0", False)}
assert set(B.parse_pnpm_lock("lockfileVersion: '6.0'\npackages:\n  /left-pad@1.3.0:\n    x: 1\n")) == {
    ("npm", "left-pad", "1.3.0", False)}
reqs = "requests==2.32.3  # http\nRich>=13\nedge_tts[extra]==7.0.0\n-r other.txt\n\nbs4\n"
assert set(B.parse_requirements(reqs)) == {("PyPI", "requests", "2.32.3", False), ("PyPI", "rich", "?", False),
                                           ("PyPI", "edge-tts", "7.0.0", False), ("PyPI", "bs4", "?", False)}
pyproj = '[project]\nname = "x"\ndependencies = ["httpx>=0.27", "Pydantic_Core"]\n[project.optional-dependencies]\ndev = ["pytest"]\n'
assert set(B.parse_pyproject(pyproj)) == {("PyPI", "httpx", "?", False), ("PyPI", "pydantic-core", "?", False),
                                          ("PyPI", "pytest", "?", False)}
assert set(B.parse_toml_lock('[[package]]\nname = "Anyio"\nversion = "4.6.0"\n')) == {("PyPI", "anyio", "4.6.0", False)}
pkg = json.dumps({"dependencies": {"zod": "3.23.8", "lodash": "^4.17.0", "@zz/internal": "workspace:*"},
                  "devDependencies": {"vitest": "2.1.0"}})
assert set(B.parse_package_json(pkg)) == {("npm", "zod", "3.23.8", False), ("npm", "lodash", "?", False),
                                          ("npm", "vitest", "2.1.0", True)}

with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    (t / "a").mkdir(); (t / "a" / "package-lock.json").write_text(npm3); (t / "a" / "package.json").write_text(pkg)
    (t / "a" / "node_modules" / "x").mkdir(parents=True); (t / "a" / "node_modules" / "x" / "package.json").write_text(pkg)
    (t / "b").mkdir(); (t / "b" / "requirements.txt").write_text("requests==2.32.3\n")
    (t / "b" / "pyproject.toml").write_text('[project]\ndependencies = ["requests"]\n')
    found = B.scan_project(t)
    assert ("npm", "zod", "3.23.8", False) not in found, "package.json beside a lockfile must be skipped"
    assert ("PyPI", "requests", "?", False) not in found and ("PyPI", "requests", "2.32.3", False) in found
    assert not any(n == "vitest" for _, n, _, _ in found), "node_modules must not be walked"
    cfg = t / "roster-projects.txt"
    cfg.write_text(f"# comment\nzzproj-alpha={t / 'a'}\nzzproj-beta={t / 'b'}\nzzproj-gone={t / 'nope'}\n")
    with contextlib.redirect_stderr(io.StringIO()) as err:
        text, packed, count, dev, n = B.build(cfg)
    assert "zzproj" not in err.getvalue() and str(t) not in err.getvalue()
    assert n == 3 and text.startswith("projects: 0=zzproj-alpha,1=zzproj-beta,2=zzproj-gone\n") and dev
    assert "npm|binary-parser|2.2.0|0" in text and B.unpack(packed) == text and count == len(text.splitlines()) - 1
    assert len(packed) < B.LIMIT
    text_nodev, _ = B.build_text([("p", {("npm", "a", "1", False), ("npm", "b", "1", True)})], include_dev=False)
    assert "|b|" not in text_nodev and "|a|" in text_nodev
assert B.LIMIT == 45_000
# the builder's upload goes to gh on stdin, never as an argument
_bsrc = (ROOT / "tools" / "roster" / "build_roster.py").read_text(encoding="utf-8")
assert "input=packed" in _bsrc and "--body" not in _bsrc

# ---------------------------------------------------------------- fake roster + mocked OSV
FAKE = ("projects: 0=zzproj-alpha,1=zzproj-beta,2=zzproj-gamma\n"
        "npm|binary-parser|2.2.0|0\nnpm|binary-parser|2.3.1|1\nnpm|next|14.2.3|0,1\nnpm|zzpkg-secretlib|9.9.9|2\n"
        "PyPI|requests|?|2\ntool|chrome|131.0.1|0\n")
PACKED = B.pack(FAKE)
CVE = "CVE-2026-41234"
VULN = {"id": "GHSA-2c3f-4g5h-6j7m", "aliases": [CVE], "affected": [{"package": {"ecosystem": "npm", "name": "binary-parser"},
        "ranges": [{"type": "SEMVER", "events": [{"introduced": "0"}, {"fixed": "2.3.1"}]}]}]}
# like the real CVE-2026-134814: the CVE record names no package, its GHSA alias does
NVD_CVE = {"id": CVE, "aliases": [VULN["id"]], "affected": [{"ranges": [{"events": [{"introduced": "0"}]}]}]}
OTHER = {"id": "CVE-2026-50000", "aliases": [], "affected": [{"package": {"ecosystem": "npm", "name": "zzz-notours"},
         "ranges": [{"events": [{"introduced": "0"}, {"fixed": "1.0.1"}]}]}]}


class FakeOsv:
    def __init__(self, boom=None):
        self.boom, self.queries = boom, []

    def vuln(self, vid):
        if self.boom:
            raise self.boom
        return {CVE: NVD_CVE, VULN["id"]: VULN, OTHER["id"]: OTHER}.get(vid, {})

    def querybatch(self, queries):
        self.queries += queries
        return [[VULN["id"]] if q["package"]["name"] == "binary-parser" and q["version"] == "2.2.0" else [] for q in queries]


STORY = {"title": "binary-parser Flaw Enables JavaScript Injection via Malicious Parser Definitions",
         "summary": f"A critical flaw ({CVE}, CVSS 9.2) in the npm package binary-parser lets attacker-shaped parser "
                    "definitions run code. Version 2.3.1 fixes it."}
TLDR = {"infosec": {"status": "ok", "issue_date": "2026-11-25", "items": [{**STORY, "url": "https://x/1", "section": ""}]}}
BLOGS = {"engineering": [{"title": "What's next for agents", "url": "https://x/2", "summary": "The next step is evals."}],
         "security": []}

rs = R.load(PACKED)
assert rs.projects == ["zzproj-alpha", "zzproj-beta", "zzproj-gamma"] and rs.size == 6
# word boundaries + cue rule: "next" (everyday word) needs a nearby package cue; binary-parser counts alone
assert R.names_in(rs, "What's next for agents? The next step is evals.") == set()
assert R.names_in(rs, "The npm package next 15.1 has a CVE") == {("npm", "next")}
assert R.names_in(rs, "binary-parserX and xbinary-parser") == set()
assert R.names_in(rs, "a bug in binary-parser.") == {("npm", "binary-parser")}

# ---------------------------------------------------------------- Task 3: verdicts (worked example)
res = R.verdicts(rs, R.stories_from(TLDR, BLOGS), FakeOsv())
assert len(res) == 1 and res[0].names == ["binary-parser"], res
line = res[0].lines[0]
assert "AFFECTED in zzproj-alpha (2.2.0)" in line and "NOT AFFECTED in zzproj-beta (2.3.1)" in line, line
assert "Not in other projects." in line and 'npm i "binary-parser@^2.3.1"' in line, line
absent = R.verdicts(rs, [{"title": "t", "text": "OTHER bug CVE-2026-50000 in a package"}], FakeOsv())
assert absent[0].lines == ["zzz-notours: NOT IN ANY PROJECT."], absent[0].lines
unknown = R.verdicts(rs, [{"title": "t", "text": "requests 2.33 released for the PyPI package requests"}], FakeOsv())
assert "PRESENT, VERSION UNKNOWN in zzproj-gamma" in unknown[0].lines[0], unknown[0].lines
# only matched packages' installed versions go to OSV
q = FakeOsv(); R.verdicts(rs, R.stories_from(TLDR, BLOGS), q)
assert {x["package"]["name"] for x in q.queries} == {"binary-parser"}
msg = R.message("2026-11-25", res)

# the real 2026-11-24 TLDR text: no database maps CVE-2026-134814 to a package yet (OSV 404, GitHub lists none),
# so the story's own "versions before 2.3.1" decides
REAL = {"title": "Critical binary-parser Flaw Enables JavaScript Injection via Malicious Parser Definitions",
        "text": "Critical binary-parser Flaw Enables JavaScript Injection binary-parser versions before 2.3.1 contain "
                "CVE-2026-134814, a code-injection flaw with CVSS scores of 9.2 and 8.1. Parsing untrusted binary "
                "data with a trusted definition is unaffected. Update to 2.3.1 or later."}


class EmptyOsv(FakeOsv):
    def vuln(self, vid):
        return {}

    def querybatch(self, queries):
        return [[] for _ in queries]


got = R.verdicts(rs, [REAL], EmptyOsv())[0].lines[0]
assert "AFFECTED in zzproj-alpha (2.2.0, fixed in 2.3.1)" in got and "NOT AFFECTED in zzproj-beta (2.3.1, fixed in 2.3.1)" in got, got
assert 'npm i "binary-parser@^2.3.1"' in got
no_bp = R.parse("projects: 0=zzproj-alpha\nnpm|binary|0.3.0|0\nnpm|connect|3.7.0|0\ntool|docker|29.0.0|0\n")
assert R.verdicts(no_bp, [REAL], EmptyOsv())[0].lines == ["binary-parser: NOT IN ANY PROJECT."]
# everyday words seen in the 2026-11-24 replay are not package mentions
for txt in ("Sandboxing AI Coding Agents: nono vs Docker Sandboxes", "Backdoors Six WP Connect Plugins after a release",
            "untrusted binary data with a trusted definition, CVE-2026-1"):
    assert R.names_in(no_bp, txt) == set(), txt
assert R.names_in(no_bp, "the npm package connect is deprecated") == {("npm", "connect")}
assert R.names_in(no_bp, "Docker 29.1 fixes a runc escape") == {("tool", "docker")}
assert msg.splitlines()[0].endswith(".") and not msg[0].isdigit() and "|" not in msg.splitlines()[0]

# ---------------------------------------------------------------- Actions log guard: nothing private is printed
SECRET_STRINGS = ["zzproj", "2.2.0", "2.3.1", "14.2.3", "zzpkg-secretlib", "131.0.1"]


def captured(fn):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        value = fn()
    return value, out.getvalue() + err.getvalue()


for osv in (FakeOsv(), FakeOsv(boom=KeyError("zzproj-alpha 2.2.0")), FakeOsv(boom=RuntimeError("zzpkg-secretlib"))):
    result, printed = captured(lambda: R.run(PACKED, "2026-11-25", TLDR, BLOGS, osv))
    assert not any(s in printed for s in SECRET_STRINGS), printed
    assert result.guard.leaks("zzproj-alpha is fine"), "project guard must hold even when OSV fails"
assert "Roster: 6 entries, 1 matches" in captured(lambda: R.run(PACKED, "d", TLDR, BLOGS, FakeOsv()))[1]
_, printed = captured(lambda: R.load(B.pack("garbage") [:-4] + "!!!!"))
assert printed.startswith("Roster: unreadable (") and "garbage" not in printed
assert R.run("", "d", TLDR, BLOGS, FakeOsv()).message is None  # no roster: no verdict, no crash


class Resp:
    def __init__(self, code):
        self.status_code = code


class Http:
    def __init__(self, code=200, boom=False):
        self.code, self.boom, self.sent = code, boom, None

    def post(self, url, json, timeout):
        if self.boom:
            raise ConnectionError(f"failed to reach {url}")  # message would contain the token
        self.sent = json
        return Resp(self.code)


h = Http()
ok, printed = captured(lambda: R.send_telegram(msg, "123:SECRETTOKEN", "42", h))
assert ok and printed.strip() == "Telegram: sent" and h.sent["text"] == msg
_, printed = captured(lambda: R.send_telegram(msg, "123:SECRETTOKEN", "42", Http(403)))
assert printed.strip() == "Telegram: HTTP 403"
_, printed = captured(lambda: R.send_telegram(msg, "123:SECRETTOKEN", "42", Http(boom=True)))
assert printed.strip() == "Telegram: failed (ConnectionError)" and "SECRET" not in printed
assert captured(lambda: R.send_telegram(None, "t", "c", Http()))[0] is False  # nothing on a no-match day

# workflow: every private value is a secret, never a repo variable (variables print in clear)
wf = (ROOT / ".github" / "workflows" / "daily.yml").read_text(encoding="utf-8")
for k in ("LISTENER_CONTEXT", "LISTENER_STACK", "LISTENER_ROSTER", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
    assert f"{k}: ${{{{ secrets.{k} }}}}" in wf and f"vars.{k}" not in wf, k

# ---------------------------------------------------------------- Task 4: spoken script, notes, prompt
run, _ = captured(lambda: R.run(PACKED, "2026-11-25", TLDR, BLOGS, FakeOsv()))
guard = run.guard
turns = [("ANDREW", "Our zzproj-alpha build uses it."), ("AVA", "ZZPROJ_ALPHA again."),
         ("ANDREW", "Good news, you're not affected by binary-parser."), ("AVA", "Your setup is vulnerable: binary-parser."),
         ("ANDREW", "If you run binary-parser below 2.3.1, run npm ls binary-parser and upgrade."),
         ("AVA", "Your agents are vulnerable to prompt injection, so scope their tools.")]
kept = g.drop_leaks(turns, context="", guard=guard)
assert kept == turns[4:], kept
assert g.drop_leaks(turns[4:], context="") == turns[4:]  # no roster: unchanged
# commits: script, title, notes, feed item and history entry are all built from guarded text
_gsrc = (ROOT / "generate.py").read_text(encoding="utf-8")
assert "drop_leaks(parse_turns(body), guard=stack.guard)" in _gsrc and "stack.guard.leaks(title)" in _gsrc
assert "show_notes(weather, tldr, blogs, stack.guard)" in _gsrc
leaky_blogs = {"engineering": [{"title": "zzproj-beta release notes", "url": "https://x/3"}], "security": []}
notes = g.show_notes(None, TLDR, leaky_blogs, guard)
assert "binary-parser Flaw" in notes and "zzproj" not in notes
assert not any(w in notes for w in R.VERDICT_WORDS), notes
# prompt: names only; the never-say-affected rule appears only on a match day
_p = {"opening": "o", "tone": "t", "dynamic": "d", "signoff": "s"}
_now = __import__("datetime").datetime(2026, 11, 25, 7, 0)
with_m = g.build_prompt(_now, None, TLDR, BLOGS, _p, {"episodes": []}, stack_names=run.names)
without = g.build_prompt(_now, None, TLDR, BLOGS, _p, {"episodes": []})
assert "Never say whether the listener is affected" in with_m and "Never say whether the listener is affected" not in without
assert "binary-parser" in with_m.split("<source_data>")[0]
assert not any(s in with_m for s in ("zzproj", "2.2.0", "14.2.3", "zzpkg", "AFFECTED"))
# story choice: the roster never changes which stories the model sees
src = lambda p: p[p.index("<source_data>"):]  # noqa: E731
assert src(with_m) == src(without)
assert "This never changes which stories" in with_m
assert "Telegram" not in g.SYSTEM_PROMPT and "R.send_telegram(stack.message)" in _gsrc

# ---------------------------------------------------------------- no roster/config path is tracked by git
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
assert not re.search(r"roster-projects|roster\.sha256|LISTENER_[A-Z]+\.txt|\.config/ai-morning", tracked), "private file tracked"
assert "zzproj" not in (ROOT / "roster.py").read_text(encoding="utf-8")
print("roster checks OK")
# a label written with spaces is ordinary speech ("the AI Morning podcast"), not a leak: only - and _ interchange
assert not R.Guard(["ai-morning-podcast"], []).leaks("Welcome back to the AI Morning podcast.")
assert R.Guard(["ai-morning-podcast"], []).leaks("see ai_morning_podcast")
print("roster guard spacing OK")
# review fixes (2026-11-26)
assert R.verdicts(no_bp, [{"title": "t", "text": "Reconnect before 3.0 is gone; connect before 3.0 ends."}], EmptyOsv()) == []
assert R.text_fixes("lib-x before 3.1.0 and lib-x before 2.9.4; 3.x before 3.1") == {"lib-x": None}  # ambiguous: no text verdict
rel = R.verdicts(rs, [{"title": "t", "text": "binary-parser 3.0 released with a new API"}], EmptyOsv())[0].lines[0]
assert "PRESENT in zzproj-alpha (2.2.0; no advisory in this story)" in rel and "AFFECTED" not in rel, rel
adv_only = R.verdicts(rs, [{"title": "t", "text": f"A flaw, {CVE}, in a parser library."}], FakeOsv())[0]
assert adv_only.names == [] and "AFFECTED in zzproj-alpha" in adv_only.lines[0]  # name not in the story: not spoken
_, printed = captured(lambda: R.run(B.pack("projects: 0=" + "(" * 3 + "\n"), "d", TLDR, BLOGS, FakeOsv()))
assert "(((" not in printed
print("roster review fixes OK")
