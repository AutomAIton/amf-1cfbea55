"""Offline self-check for the listener-feedback settings in generate.py. No network, no API.

Run:  python tests/selfcheck.py      (prints OK, or fails on the first broken assertion)
Each check maps to a settled decision in feedback/LOG.md.
"""
import os
import sys
from pathlib import Path

for k in ("VOICE_A", "TARGET_MINUTES", "MAX_MINUTES", "WORDS_PER_MINUTE"):
    os.environ.pop(k, None)
os.environ["TARGET_MINUTES"] = ""  # CI passes an empty repo variable; must fall back to the default
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import generate as g  # noqa: E402

# Units: metric only (2026-11-17)
assert "Celsius" in g.SYSTEM_PROMPT and "kilomet" in g.SYSTEM_PROMPT
assert "Never say Fahrenheit" in g.SYSTEM_PROMPT
# Weather: short and factual, no tip, no weather-as-hook opening (2026-11-17)
assert "one practical tip" not in g.SYSTEM_PROMPT
assert "two or three plain, factual sentences" in g.SYSTEM_PROMPT
assert not any("weather as the hook" in o for o in g.OPENINGS)
# Voice: Andrew's voices refuse some text ("Muru"), so Brian replaces him in the edge-tts fallback (2026-11-22)
assert g.VOICE_A == "en-US-BrianMultilingualNeural", g.VOICE_A
# Specifics: name exact model, tools, skills in AI-build stories (2026-11-23)
assert "name the exact model, tools, skills and versions" in g.SYSTEM_PROMPT
# Length: 11 real minutes at the measured pace, 15-minute hard stop (2026-11-17)
assert (g.WPM, g.TARGET_MINUTES, g.MAX_MINUTES) == (165, 11, 15), (g.WPM, g.TARGET_MINUTES, g.MAX_MINUTES)
assert f"never more than {15 * 165} words" in g.SYSTEM_PROMPT
# Show notes: Celsius, and a missing forecast must not break the build
empty = {"engineering": [], "security": []}
notes = g.show_notes({"high_c": 12, "low_c": 1, "overall": "clear"}, {}, empty)
assert "12°C" in notes and "F," not in notes, notes
assert g.show_notes(None, {}, empty) == ""
hourly = {"temperature_2m": [1.2, 3.8], "weather_code": [0, 0], "precipitation_probability": [0, None]}
assert g._window(hourly, 0, 2)["temp_c"] == "1 to 4"
# Scheduling: GitHub drops scheduled runs, so attempts must span the whole day (2026-11-18)
import glob, re  # noqa: E402
wf = open(glob.glob(str(Path(__file__).resolve().parent.parent / ".github/workflows/*.yml"))[0], encoding="utf-8").read()
hours = sorted(int(m.group(1)) for m in re.finditer(r'cron: "\d+ (\d+) \* \* \*"', wf))
assert len(hours) >= 10 and hours[-1] >= 22 and hours[0] <= 10, hours
assert max(b - a for a, b in zip(hours, hours[1:])) <= 2, hours  # no gap over 2 h
# Script quality + ending (2026-11-18): natural language kept, plain wording, one Try this, key terms
assert '"Try this"' in g.SYSTEM_PROMPT and "skip the segment" in g.SYSTEM_PROMPT
assert "without stopping to decode" in g.SYSTEM_PROMPT and "playful is welcome" in g.SYSTEM_PROMPT
assert "Do not stop to define terms" in g.SYSTEM_PROMPT
assert not any("practical thing" in s for s in g.SIGNOFFS)
# Private project context stays out of the repo and, when set, never narrows story choice
assert g.LISTENER_CONTEXT == "" and "About the listener" not in g.SYSTEM_PROMPT
assert "LISTENER_CONTEXT" in wf and "Never choose or drop stories" in open(Path(g.__file__), encoding="utf-8").read()
ctx = "I am building an agentic operating system that wraps around my business"
leaky = [("ANDREW", "You said you are building an agentic operating system that wraps around everything."), ("AVA", "Nice and clean.")]
assert g.drop_leaks(leaky, ctx) == [("AVA", "Nice and clean.")]
assert g.drop_leaks(leaky, "") == leaky
assert "never repeat this description" not in g.SYSTEM_PROMPT  # only present when LISTENER_CONTEXT is set
assert "must never repeat this description" in open(Path(g.__file__), encoding="utf-8").read()
# Voices: both hosts have a neural backup before gTTS (2026-11-18)
assert all(len(c) >= 3 for c in g.EDGE_CHAIN.values()) and "en-US-AriaNeural" in g.EDGE_CHAIN[g.VOICE_B]
assert not any("Andrew" in v for c in g.EDGE_CHAIN.values() for v in c)
# 2026-11-22: Google Chirp 3 HD is the primary voice when a key is set; two distinct Chirp voices
assert g.GOOGLE_VOICE_A.startswith("en-US-Chirp3-HD-") and g.GOOGLE_VOICE_B.startswith("en-US-Chirp3-HD-") and g.GOOGLE_VOICE_A != g.GOOGLE_VOICE_B
assert (g.GOOGLE_VOICE_A, g.GOOGLE_VOICE_B) == ("en-US-Chirp3-HD-Charon", "en-US-Chirp3-HD-Aoede")  # listener pick 2026-11-22
assert "GOOGLE_TTS_API_KEY" in wf, "workflow must pass the Google key"
# 2026-11-22: no "my turn" handovers
assert 'Never say "my turn"' in g.SYSTEM_PROMPT
# VPS catch-up trigger exists, targets this repo's workflow, alerts after 09:00 and caps starts (2026-11-18)
cu = (Path(__file__).resolve().parent.parent / "tools" / "vps" / "ai-morning-catchup.sh").read_text(encoding="utf-8")
assert "amf-1cfbea55" in cu and "workflows/daily.yml/dispatches" in cu
assert "ALERT_HOUR=9" in cu and "MAX_STARTS=3" in cu and '"name":"ai-morning-episode"' in cu
# 2026-11-19 feedback: weather retries, stand-alone practical Try this, no short episodes, security fallback
assert g.WEATHER_ROUNDS >= 3
assert "stand alone" in g.SYSTEM_PROMPT and "start today" in g.SYSTEM_PROMPT and "two or three sentences" in g.SYSTEM_PROMPT
assert "Never assume the listener remembers" in g.SYSTEM_PROMPT and "Never finish under" in g.SYSTEM_PROMPT
assert g.security_is_thin({"infosec": {"status": "no new issue since the last episode"}}, {"security": []})
assert not g.security_is_thin({"infosec": {"status": "ok"}}, {"security": []})
assert not g.security_is_thin({}, {"security": [{"title": "x"}]})
_p = {"opening": "o", "tone": "t", "dynamic": "d", "signoff": "s", "security_topic": g.SECURITY_EVERGREEN[0]}
_now = __import__("datetime").datetime(2026, 11, 19, 7, 0)
assert "SECURITY FALLBACK" in g.build_prompt(_now, None, {}, {"engineering": [], "security": []}, _p, {"episodes": []})
assert "SECURITY FALLBACK" not in g.build_prompt(_now, None, {}, {"engineering": [], "security": []}, {k: v for k, v in _p.items() if k != "security_topic"}, {"episodes": []})
# 2026-11-20 feedback: Try this follows the listener's private stack (repo variable, never committed)
_src = open(Path(g.__file__), encoding="utf-8").read()
assert g.LISTENER_STACK == "" and "Listener's stack" not in g.SYSTEM_PROMPT
assert "LISTENER_STACK" in wf and "one Try this item must be about it" in _src and "never list it" in _src
_ls = g.LISTENER_STACK; g.LISTENER_STACK = "PostgreSQL, Python packages, Node.js and npm, Docker containers"
assert g.drop_leaks([("A", "I run PostgreSQL, Python packages, Node.js and npm, Docker containers."), ("B", "PostgreSQL 19 shipped today.")]) == [("B", "PostgreSQL 19 shipped today.")]
g.LISTENER_STACK = _ls
# 2026-11-21 feedback: Try this is a block of two or three short items, with more room
assert "two or three short items" in g.SYSTEM_PROMPT and "two or three practical things" in g.SYSTEM_PROMPT
assert f"{13 * g.WPM} words is ideal" in g.SYSTEM_PROMPT and g.MAX_MINUTES == 15
# 2026-11-22: Google usage is logged per run so a charge can be seen coming
assert g.TTS_FREE_MONTHLY_CHARS == 1_000_000 and callable(g.log_tts_usage) and "tts-usage.csv" in open(Path(g.__file__), encoding="utf-8").read()
assert "last line of the episode is always a plain goodbye" in g.SYSTEM_PROMPT and "no slogans" in g.SYSTEM_PROMPT
assert not any(s.startswith("End with a one-line recap") for s in g.SIGNOFFS)
print("OK")
