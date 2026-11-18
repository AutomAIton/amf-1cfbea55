# AI Morning feedback log

Read this FIRST in every feedback session. Settled items are not re-asked. Items under
"Verify next session" are asked once as a quick yes/no check, then moved to Settled.

## State
- **Cadence:** daily, through 2026-11-24. The 11-24 session asks: keep daily, or go weekly?
- **Last reviewed episode:** 2026-11-17 (the seed version, "Agents Without Permission Slips")
- **Next session queued:** 2026-11-19 07:00 (`C:\AI\handoffs\queue\2026-11-19-0700-ai-morning-feedback.md`)

## Settled decisions
| Date | Decision | Lands in |
|---|---|---|
| 2026-11-17 | Metric only: Celsius, km, km/h; convert imperial figures in news | SYSTEM_PROMPT, fetch_weather, show_notes |
| 2026-11-17 | Weather: 2-3 factual sentences, no tip or banter; no "weather as hook" opening | SYSTEM_PROMPT, OPENINGS |
| 2026-11-17 | Playful tone in the news segments is fine | TONES (unchanged) |
| 2026-11-17 | Ava's voice is good | VOICE_B (unchanged) |
| 2026-11-17 | Length: 10-12 min target (11), over 10 is fine, 15 min hard stop | TARGET_MINUTES, MAX_MINUTES, WPM=165 |
| 2026-11-17 | Feedback sessions run in the morning right after listening | this loop |
| 2026-11-17 | Feedback daily for the first 7 days, then reconsider (maybe weekly) | Cadence above |

## Verify next session (trials)
- Andrew now uses `en-US-AndrewMultilingualNeural`. Does he sound less stiff? Keep or try another?
- Does the weather now feel short and factual, in Celsius?
- Did the episode land at 10-12 min? Check `seconds` in data/history.json first, then ask.

## Open questions (not yet asked)
- Story selection: which stories landed or bored
- AI-security segment depth
- Anything wrong or invented
- Sources to add or drop (current list: FEEDS and TLDR_TOPICS in generate.py)

## Known issues
- A forced re-run on the same day gets thin sources, because the first run already marked
  today's newsletters and posts as used. Don't judge length from a forced re-run.
