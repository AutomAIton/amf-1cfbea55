#!/usr/bin/env python3
"""Build the private dependency roster and (optionally) upload it as the Actions secret LISTENER_ROSTER.

The repo is public, so this file holds no project names or paths. The project list lives outside the repo:
    %USERPROFILE%\\.config\\ai-morning\\roster-projects.txt     one `label=path` per line, `#` comments
    a path of `@tools` means "machine tools" (node, python, git, gh, docker, Chrome, Claude Code)

Roster text (only ever in memory or in the secret):
    projects: 0=label,1=label,...
    eco|name|version|0,3          eco is an OSV ecosystem (npm, PyPI) or `tool`; unknown version is `?`
Packed form: gzip, then base64. The upload goes to `gh secret set` on stdin, never as an argument.

Run:  .venv/Scripts/python tools/roster/build_roster.py            (counts + packed size only, no upload)
      .venv/Scripts/python tools/roster/build_roster.py --upload   (uploads if the roster changed)
Prints counts and sizes only, never names or versions.
"""
import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("AI_MORNING_CONFIG", Path.home() / ".config" / "ai-morning"))
LIMIT = 45_000  # bytes; GitHub caps a secret at 48 KB
SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "env", "dist", "build", "__pycache__", ".next", ".turbo",
             "site-packages", ".worktrees", "worktrees", ".pnpm-store", "out", "coverage"}
MANIFESTS = ("package-lock.json", "pnpm-lock.yaml", "uv.lock", "poetry.lock", "pyproject.toml", "package.json")
TOOLS = {"node": ["node", "--version"], "python": ["python", "--version"], "git": ["git", "--version"],
         "gh": ["gh", "--version"], "docker": ["docker", "--version"], "claude-code": ["claude", "--version"]}
VERSION = re.compile(r"\d+(?:\.\d+)+")


def pypi_norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


# ---------------------------------------------------------------- parsers: each yields (eco, name, version, dev)
def parse_npm_lock(text):
    data = json.loads(text)
    for key, meta in (data.get("packages") or {}).items():
        if not key or meta.get("link") or "node_modules/" not in key:
            continue
        name = meta.get("name") or key.rsplit("node_modules/", 1)[1]
        if meta.get("version"):
            yield "npm", name, meta["version"], bool(meta.get("dev"))


PNPM_KEY = re.compile(r"""^  ['"]?/?((?:@[^/@\s'"]+/)?[^@\s'"(]+)[@/]([0-9][^\s'"(:]*)""")


def parse_pnpm_lock(text):
    section = None
    for line in text.splitlines():
        if line and not line.startswith(" "):
            section = line.rstrip(":").strip()
            continue
        if section == "packages":
            m = PNPM_KEY.match(line)
            if m:
                # SHORTCUT: pnpm v9 marks dev deps only in importers, so everything counts as prod here;
                # upgrade path: walk importers.*.devDependencies and drop packages reachable only from them.
                yield "npm", m.group(1), m.group(2), False


def parse_requirements(text):
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(==|>=|~=|<=|>|<|!=)?\s*([^;,\s]*)", line)
        if not m or line.startswith("-"):
            continue
        version = m.group(3) if m.group(2) == "==" and m.group(3) else "?"
        yield "PyPI", pypi_norm(m.group(1)), version, False


def parse_toml_lock(text):  # uv.lock and poetry.lock share [[package]] name/version
    for p in tomllib.loads(text).get("package", []):
        if p.get("name") and p.get("version"):
            yield "PyPI", pypi_norm(p["name"]), str(p["version"]), False


def parse_pyproject(text):
    data = tomllib.loads(text)
    deps = list(data.get("project", {}).get("dependencies", []))
    for group in (data.get("project", {}).get("optional-dependencies") or {}).values():
        deps += group
    for d in deps:
        m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)", d)
        if m:
            yield "PyPI", pypi_norm(m.group(1)), "?", False
    for name in (data.get("tool", {}).get("poetry", {}).get("dependencies") or {}):
        if name.lower() != "python":
            yield "PyPI", pypi_norm(name), "?", False


def parse_package_json(text):
    data = json.loads(text)
    for field, dev in (("dependencies", False), ("devDependencies", True), ("optionalDependencies", False)):
        for name, spec in (data.get(field) or {}).items():
            if str(spec).startswith(("workspace:", "file:", "link:", "portal:")):
                continue  # a local package, not something on a registry
            exact = spec if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.]+)?", str(spec)) else "?"
            yield "npm", name, exact, dev


PARSERS = {"package-lock.json": parse_npm_lock, "pnpm-lock.yaml": parse_pnpm_lock, "uv.lock": parse_toml_lock,
           "poetry.lock": parse_toml_lock, "pyproject.toml": parse_pyproject, "package.json": parse_package_json}


def find_manifests(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f in MANIFESTS or re.fullmatch(r"requirements[\w.-]*\.txt", f):
                yield Path(dirpath) / f


def scan_project(root):
    """All (eco, name, version, dev) for one project. A lockfile beats its package.json / pyproject in the same dir."""
    found = set()
    by_dir = {}
    for path in find_manifests(root):
        by_dir.setdefault(path.parent, []).append(path)
    for folder, files in by_dir.items():
        names = {p.name for p in files}
        for path in files:
            if path.name == "package.json" and names & {"package-lock.json", "pnpm-lock.yaml"}:
                continue
            if path.name == "pyproject.toml" and names & {"uv.lock", "poetry.lock"}:
                continue
            parser = PARSERS.get(path.name, parse_requirements)
            try:
                found.update(parser(path.read_text(encoding="utf-8", errors="replace")))
            except Exception as exc:  # noqa: BLE001 - one broken manifest must not stop the build
                print(f"  skipped one manifest ({type(exc).__name__})", file=sys.stderr)
    # a pinned version makes the `?` entry for the same package redundant
    pinned = {(e, n) for e, n, v, _ in found if v != "?"}
    return {t for t in found if t[2] != "?" or (t[0], t[1]) not in pinned}


def tool_versions():
    out = set()
    for name, cmd in TOOLS.items():
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            m = VERSION.search(r.stdout + r.stderr)
            out.add(("tool", name, m.group(0) if m else "?", False))
        except Exception:  # noqa: BLE001 - a missing tool is simply absent
            continue
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon") as k:
                out.add(("tool", "chrome", winreg.QueryValueEx(k, "version")[0], False))
        except OSError:
            pass
    return out


# ---------------------------------------------------------------- roster text + packing
def read_projects(path):
    projects = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            label, target = (s.strip() for s in line.split("=", 1))
            projects.append((label, target))
    return projects


def build_text(per_project, include_dev=True):
    """per_project: list of (label, set of (eco, name, version, dev)). Returns roster text."""
    index = {}
    for i, (_, entries) in enumerate(per_project):
        for eco, name, version, dev in entries:
            if dev and not include_dev:
                continue
            index.setdefault((eco, name, version), set()).add(i)
    header = "projects: " + ",".join(f"{i}={label}" for i, (label, _) in enumerate(per_project))
    lines = [f"{e}|{n}|{v}|{','.join(map(str, sorted(p)))}" for (e, n, v), p in sorted(index.items())]
    return "\n".join([header, *lines]) + "\n", len(lines)


def pack(text):
    return base64.b64encode(gzip.compress(text.encode("utf-8"), compresslevel=9, mtime=0)).decode("ascii")


def unpack(packed):
    return gzip.decompress(base64.b64decode(packed)).decode("utf-8")


def build(projects_file, include_dev=None):
    per_project = []
    for label, target in read_projects(projects_file):
        if target == "@tools":
            per_project.append((label, tool_versions()))
        elif Path(target).expanduser().is_dir():
            per_project.append((label, scan_project(Path(target).expanduser())))
        else:
            print(f"  project #{len(per_project)} path missing; kept with no entries", file=sys.stderr)
            per_project.append((label, set()))
    modes = [include_dev] if include_dev is not None else [True, False]
    for dev in modes:
        text, count = build_text(per_project, include_dev=dev)
        packed = pack(text)
        if len(packed) <= LIMIT:
            return text, packed, count, dev, len(per_project)
    raise SystemExit(f"Roster too big: {len(packed):,} bytes packed even without dev deps (limit {LIMIT:,}).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=str(CONFIG_DIR / "roster-projects.txt"))
    ap.add_argument("--upload", action="store_true", help="gh secret set LISTENER_ROSTER (stdin) when changed")
    ap.add_argument("--repo", default="AutomAIton/amf-1cfbea55")
    args = ap.parse_args()
    text, packed, count, dev, n_projects = build(args.projects)
    print(f"Roster: {n_projects} projects, {count} entries, {len(text.encode()):,} bytes raw, "
          f"{len(packed):,} bytes packed (limit {LIMIT:,}){'' if dev else ', dev deps dropped'}")
    if not args.upload:
        return
    digest = hashlib.sha256(packed.encode()).hexdigest()
    stamp = CONFIG_DIR / "roster.sha256"
    if stamp.exists() and stamp.read_text().strip() == digest:
        print("Upload: unchanged, skipped")
        return
    r = subprocess.run(["gh", "secret", "set", "LISTENER_ROSTER", "--repo", args.repo],
                       input=packed, text=True, capture_output=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"Upload: gh exited {r.returncode}")  # stderr not echoed: it could quote input
    stamp.write_text(digest)
    print("Upload: LISTENER_ROSTER updated")


if __name__ == "__main__":
    main()
