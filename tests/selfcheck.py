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
# Voice: Andrew on the newer conversational model (2026-11-17)
assert g.VOICE_A == "en-US-AndrewMultilingualNeural", g.VOICE_A
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
print("OK")
