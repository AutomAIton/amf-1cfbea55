"""Private dependency roster: match today's stories against the listener's installed packages.

The roster arrives as the Actions secret LISTENER_ROSTER (gzip + base64, built by tools/roster/build_roster.py).
It names private projects, so nothing from it may reach a public surface:
  - log lines carry counts and exception TYPES only (an exception message could quote a project name);
  - the model sees matched package names only (already public: they are in the story text), never versions,
    projects or verdicts;
  - public_guard() drops any public text that names a project, or that names a matched package and says
    whether "you" are affected;
  - verdicts go only to the operator's private Telegram chat.
Matches only steer the Try this segment; they never change which stories are covered.
"""
import base64
import gzip
import os
import re
import sys
from dataclasses import dataclass, field

OSV = "https://api.osv.dev/v1"
TIMEOUT = 10
VULN_ID = re.compile(r"\b(CVE-\d{4}-\d{4,7}|GHSA(?:-[23456789cfghjmpqrvwx]{4}){3})\b", re.I)
TOKEN = re.compile(r"@?[a-z0-9][a-z0-9._\-/]*[a-z0-9]|[a-z0-9]", re.I)
# A plain-word name (letters only, e.g. "connect", "docker") is an everyday word far more often than a package,
# so it counts only with a strong package cue right next to it, or a version number right after it.
STRONG_CUE = re.compile(r"\b(npm|pypi|pip install|package|library|module|dependency|crate|gem)\b", re.I)
VERSION_AFTER = re.compile(r"^\s*(?:v|version\s+)?\d+\.\d+")
# "binary-parser versions before 2.3.1": names a package and its fix even when no advisory database has it yet
TEXT_FIX = re.compile(r"(?<![\w@/.-])(@?[a-z0-9][\w.\-/]*[a-z0-9])\s+(?:versions?\s+|releases?\s+)?"
                      r"(?:before|prior to|below|older than|earlier than|up to and including|<)\s*v?(\d+(?:\.\d+)+)", re.I)
NOT_A_PACKAGE = {"versions", "version", "releases", "release", "builds", "all", "any", "those", "the", "and", "or"}
VERDICT_WORDS = ("NOT AFFECTED", "NOT IN ANY PROJECT", "PRESENT, VERSION UNKNOWN")  # verdict-only phrases
OSV_ECOSYSTEMS = ("npm", "PyPI")
INSTALL = {"npm": ("npm i", "@^"), "PyPI": ("pip install", ">=")}
SAID_AFFECTED = re.compile(r"\b(you're|you are|you've been|you were|your\b[^.?!]{0,40}?\b(?:is|are|was|were))\s+"
                           r"(?:not\s+|still\s+|already\s+)?(affected|vulnerable|exposed|safe|patched|fine|"
                           r"in the clear|on the fixed|behind)\b", re.I)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


@dataclass
class Roster:
    projects: list
    entries: dict  # (eco, name) -> {version: set(project index)}
    by_lower: dict = field(default_factory=dict)  # lowercase name -> list of (eco, name)

    @property
    def size(self):
        return sum(len(v) for v in self.entries.values())


def parse(text):
    lines = text.splitlines()
    header = lines[0].split(":", 1)[1].strip()
    projects = [p.split("=", 1)[1] for p in header.split(",") if "=" in p]
    entries, by_lower = {}, {}
    for line in lines[1:]:
        if line.count("|") != 3:
            continue
        eco, name, version, idx = line.split("|")
        entries.setdefault((eco, name), {})[version] = {int(i) for i in idx.split(",") if i}
        by_lower.setdefault(name.lower(), []).append((eco, name))
    return Roster(projects, entries, by_lower)


def load(packed):
    """Decode LISTENER_ROSTER. Any failure -> None, logging the exception type only."""
    if not packed:
        return None
    try:
        return parse(gzip.decompress(base64.b64decode(packed)).decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        log(f"Roster: unreadable ({type(exc).__name__})")
        return None


def stories_from(tldr, blogs):
    out = []
    for b in tldr.values():
        for it in b.get("items", []) if b.get("status") == "ok" else []:
            out.append({"title": it.get("title", ""), "text": f"{it.get('title', '')} {it.get('summary', '')}"})
    for cat in ("security", "engineering"):
        for it in blogs.get(cat, []):
            out.append({"title": it.get("title", ""), "text": f"{it.get('title', '')} {it.get('summary', '')}"})
    return out


def _plain(name):
    return re.fullmatch(r"[a-z]+", name) is not None


def _cued(text, start, end):
    return bool(STRONG_CUE.search(text[max(0, start - 25):end + 25]) or VERSION_AFTER.match(text[end:end + 20]))


def text_fixes(text):
    """{lower name: fixed version} from phrases like "X versions before 2.3.1"."""
    out = {}
    for m in TEXT_FIX.finditer(text):
        name = m.group(1).lower()
        if name in NOT_A_PACKAGE or re.fullmatch(r"v?[\d.x*]+", name):  # "3.x before 3.1" names a line, not a package
            continue
        if out.get(name, m.group(2)) != m.group(2):
            out[name] = None  # several release lines ("3.x before 3.1, 2.x before 2.9"): too ambiguous to judge
        else:
            out[name] = m.group(2)
    return out


def names_in(roster, text):
    """Roster packages named in the text, with word boundaries. A letters-only name needs a package cue."""
    hits = set()
    for m in TOKEN.finditer(text):
        tok = m.group(0).lower().rstrip(".")
        for key in roster.by_lower.get(tok, []):
            if (_plain(tok) or len(tok) < 4) and not _cued(text, m.start(), m.end()):
                continue
            hits.add(key)
    return hits


# SHORTCUT: numeric compare of the first 4 parts, pre-release tags ignored; upgrade path: packaging.version / semver
def _vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v.split("-")[0].split("+")[0])[:4])


class OsvClient:
    def __init__(self, session=None):
        import requests
        self.http = session or requests.Session()
        self.cache = {}

    def vuln(self, vid):
        if vid not in self.cache:
            r = self.http.get(f"{OSV}/vulns/{vid}", timeout=TIMEOUT)
            self.cache[vid] = r.json() if r.status_code == 200 else {}
        return self.cache[vid]

    def querybatch(self, queries):
        if not queries:
            return []
        r = self.http.post(f"{OSV}/querybatch", json={"queries": queries}, timeout=TIMEOUT)
        r.raise_for_status()
        return [[v["id"] for v in (res.get("vulns") or [])] for res in r.json().get("results", [])]


def _osv_packages(vuln):
    return {(a["package"].get("ecosystem"), a["package"].get("name"))
            for a in vuln.get("affected", []) if a.get("package")}


def _fixed(vuln, eco, name):
    for a in vuln.get("affected", []):
        p = a.get("package", {})
        if p.get("ecosystem") == eco and p.get("name") == name:
            for rng in a.get("ranges", []):
                for ev in rng.get("events", []):
                    if "fixed" in ev:
                        return ev["fixed"]
    return None


def norm_id(vid):
    """OSV ids: CVE-2026-1234 upper case, GHSA-abcd-... with a lower-case body."""
    vid = vid.strip()
    return "GHSA-" + vid[5:].lower() if vid.upper().startswith("GHSA-") else vid.upper()


def _ids(vuln):
    return {norm_id(vuln.get("id", "")), *(norm_id(a) for a in vuln.get("aliases", []))}


@dataclass
class StoryVerdict:
    title: str
    lines: list  # human text, private
    names: list  # matched roster package names (public: they are in the story)


def verdicts(roster, stories, osv):
    """One StoryVerdict per story that names a roster package or cites an advisory for one. Network errors
    mean no verdict for that story (logged by type only)."""
    out = []
    for story in stories:
        try:
            v = _story_verdict(roster, story, osv)
        except Exception as exc:  # noqa: BLE001
            log(f"Roster: verdict skipped ({type(exc).__name__})")
            continue
        if v:
            out.append(v)
    return out


def _story_verdict(roster, story, osv):
    text = story["text"]
    cited = {norm_id(m) for m in VULN_ID.findall(text)}
    pkgs = names_in(roster, text)
    fixes = text_fixes(text)  # the story's own "X before Y", for advisories no database has yet
    cited_vulns = []
    for c in sorted(cited):
        v = osv.vuln(c)
        cited_vulns.append(v)
        if not _osv_packages(v):  # an NVD-sourced CVE record names no package; its GHSA alias may
            cited_vulns += [osv.vuln(norm_id(a)) for a in v.get("aliases", [])[:3]]
    cited_vulns = [v for v in cited_vulns if v]
    cited |= set().union(*(_ids(v) for v in cited_vulns)) if cited_vulns else set()
    advisory_pkgs = set().union(*(_osv_packages(v) for v in cited_vulns)) if cited_vulns else set()
    absent = {n for e, n in advisory_pkgs if (e, n) not in roster.entries and e in OSV_ECOSYSTEMS}
    pkgs |= {p for p in advisory_pkgs if p in roster.entries}
    for name in fixes:
        at = re.search(r"(?<![\w@/.-])" + re.escape(name) + r"(?![\w-])", text, re.I)
        if (_plain(name) or len(name) < 4) and not (at and _cued(text, at.start(), at.end())):
            continue  # "connect before 3.0" is not a package mention without a cue
        keys = roster.by_lower.get(name, [])
        if keys:
            pkgs |= set(keys)
        else:
            absent.add(name)
    absent -= {n.lower() for _, n in pkgs}
    if not pkgs and not absent:
        return None
    lines = [_package_line(roster, eco, name, cited, cited_vulns, advisory_pkgs, fixes.get(name.lower()), osv)
             for eco, name in sorted(pkgs)]
    absent_lines = [f"{name}: NOT IN ANY PROJECT." for name in sorted(absent)]
    # only names written in the story reach the model: an advisory record's package name may not be public text
    spoken = sorted({n for _, n in pkgs if re.search(r"(?<![\w@/.-])" + re.escape(n) + r"(?![\w-])", text, re.I)})
    return StoryVerdict(story["title"], lines + absent_lines, spoken)


def _package_line(roster, eco, name, cited, cited_vulns, advisory_pkgs, text_fix, osv):
    """Per installed version: AFFECTED / NOT AFFECTED from OSV, else from the story's own fixed version."""
    versions = roster.entries[(eco, name)]
    def label(idx):
        return ", ".join(roster.projects[i] for i in sorted(idx))

    used = set().union(*versions.values())
    parts, fix, affected = [], None, False
    known = sorted((v for v in versions if v != "?"), key=_vkey)
    results = (osv.querybatch([{"package": {"name": name, "ecosystem": eco}, "version": v} for v in known])
               if eco in OSV_ECOSYSTEMS and known else [[] for _ in known])
    in_advisory = (eco, name) in advisory_pkgs
    for version, ids in zip(known, results):
        where = label(versions[version])
        hit = [i for i in ids if _ids(osv.vuln(i)) & cited] if cited else []
        for i in hit:
            fix = fix or _fixed(osv.vuln(i), eco, name)
        if hit:
            affected = True
            parts.append(f"AFFECTED in {where} ({version})")
        elif text_fix:
            below = _vkey(version) < _vkey(text_fix)
            affected |= below
            parts.append(f"{'AFFECTED' if below else 'NOT AFFECTED'} in {where} ({version}, fixed in {text_fix})")
        elif cited and in_advisory:
            parts.append(f"NOT AFFECTED in {where} ({version})")
        elif cited:
            parts.append(f"PRESENT in {where} ({version}; the cited advisory has no package data yet, check by hand)")
        else:
            parts.append(f"PRESENT in {where} ({version}; no advisory in this story)")
    if "?" in versions:
        parts.append(f"PRESENT, VERSION UNKNOWN in {label(versions['?'])}")
    for v in cited_vulns:
        fix = fix or _fixed(v, eco, name)
    fix = fix or text_fix
    others = len(roster.projects) - len(used)
    line = f"{name}: " + ". ".join(parts) + "." + (" Not in other projects." if others else "")
    if fix and affected and eco in INSTALL:
        cmd, op = INSTALL[eco]
        line += f' Fix: {cmd} "{name}{op}{fix}".'
    return line


def message(day, results):
    if not results:
        return None
    lead = "Today's episode has a package story, and below is whether each of your projects is affected."
    body = [lead, f"AI Morning stack check, {day}"]
    for r in results:
        body.append("")
        body.append(f"• {r.title}")
        body.extend(f"  {line}" for line in r.lines)
    text = "\n".join(body)
    return text if len(text) <= 4000 else text[:3990] + "\n…"


def send_telegram(text, token=None, chat=None, http=None):
    """Bot API sendMessage. Logs only 'Telegram: sent' or 'Telegram: HTTP <code>' (never text or body)."""
    token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat = chat or os.getenv("TELEGRAM_CHAT_ID", "")
    if not text:
        return False
    if not (token and chat):
        log("Telegram: not configured")
        return False
    try:
        if http is None:
            import requests as http
        r = http.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text, "disable_web_page_preview": True}, timeout=TIMEOUT)
        log("Telegram: sent" if r.status_code == 200 else f"Telegram: HTTP {r.status_code}")
        return r.status_code == 200
    except Exception as exc:  # noqa: BLE001 - the exception text would include the token URL
        log(f"Telegram: failed ({type(exc).__name__})")
        return False


# ---------------------------------------------------------------- public-surface guard
@dataclass
class Guard:
    projects: list
    matched: list

    def __post_init__(self):
        pats = [r"[-_]".join(map(re.escape, re.split(r"[-_]", p))) for p in self.projects if len(p) >= 3]
        self._proj = re.compile(r"(?<![\w-])(" + "|".join(pats) + r")(?![\w-])", re.I) if pats else None
        names = [re.escape(n) for n in self.matched]
        self._pkg = re.compile(r"(?<![\w-])(" + "|".join(names) + r")(?![\w-])", re.I) if names else None

    def leaks(self, text):
        if self._proj and self._proj.search(text):
            return True
        if any(w in text for w in VERDICT_WORDS):
            return True
        return bool(self._pkg and self._pkg.search(text) and SAID_AFFECTED.search(text))


NO_GUARD = Guard([], [])


@dataclass
class Result:
    names: list
    message: str | None
    guard: Guard
    entries: int = 0


def run(packed, day, tldr, blogs, osv=None):
    """Whole roster step. Never raises; logs counts and exception types only. On a matching failure the
    project-name guard still protects the public text."""
    roster = load(packed)
    if roster is None:
        return Result([], None, NO_GUARD)
    try:
        guard = Guard(roster.projects, [])
    except Exception as exc:  # noqa: BLE001 - a re.error would quote the pattern, which holds project names
        log(f"Roster: guard failed ({type(exc).__name__}); roster ignored today")
        return Result([], None, NO_GUARD)
    try:
        results = verdicts(roster, stories_from(tldr, blogs), osv or OsvClient())
        names = sorted({n for r in results for n in r.names})
        result = Result(names, message(day, results), Guard(roster.projects, names), roster.size)
    except Exception as exc:  # noqa: BLE001
        log(f"Roster: matching failed ({type(exc).__name__})")
        return Result([], None, guard, roster.size)
    log(f"Roster: {roster.size} entries, {len(results)} matches")
    return result
