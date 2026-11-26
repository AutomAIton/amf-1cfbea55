"""Offline checks for the private roster builder (tools/roster/build_roster.py): parsers on small fixture
lockfiles, packing, size limit, stdin upload. Imported by tests/selfcheck.py. Fake projects are zzproj-*."""
import contextlib
import io
import json
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "roster"))
import build_roster as B  # noqa: E402

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

print("builder checks OK")
