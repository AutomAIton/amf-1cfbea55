# AI Morning feedback log

Read this FIRST in every feedback session. Settled items are not re-asked. Items under
"Verify next session" are asked once as a quick yes/no check, then moved to Settled.

## State
- **Cadence:** daily, through 2026-11-24. The 11-24 session asks: keep daily, or go weekly?
- **Last reviewed episode:** 2026-11-18 ("Cheaper Frontiers and Poisoned Model Files", the scheduled build)
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
| 2026-11-18 | Weather is short and factual: good | SYSTEM_PROMPT (unchanged) |
| 2026-11-18 | 14 min is fine (target 11, hard stop 15 unchanged) | TARGET_MINUTES (unchanged) |
| 2026-11-18 | Security segment depth is fine | SYSTEM_PROMPT (unchanged) |
| 2026-11-18 | Topic mix, light tone and jargon level are good; keep repeating key terms lightly, never teach vocabulary | SYSTEM_PROMPT "Jargon" |
| 2026-11-18 | Strange wording: fix with a light touch, keep natural and playful language | SYSTEM_PROMPT "Language" |
| 2026-11-18 | "Try this" segment at the end: one practical thing, skipped if nothing fits | SYSTEM_PROMPT, SIGNOFFS |
| 2026-11-18 | Project context may be mentioned only generically and must never limit topic breadth; stays private (repo is public) | LISTENER_CONTEXT repo variable, drop_leaks |
| 2026-11-18 | Neural backup voice for each host before the robotic gTTS fallback | VOICE_A_BACKUP, VOICE_B_BACKUP |
| 2026-11-18 | Delivery: the daily build can be dropped by GitHub's scheduler; VPS cron starts it from 06:00 CT and alerts at 09:00 CT | tools/vps, VPS /etc/cron.d/ai-morning-catchup |

## Verify next session (trials)
- Andrew is still stiff and robotic on AndrewMultilingualNeural (and it often fails in CI). Voice samples are in
  `feedback/voice-samples/` (local only, not committed). Ask which male voice he prefers, then change VOICE_A.
- PENDING operator nod: the 1-2 sentence project description for the LISTENER_CONTEXT repo variable (draft it with him).
- Did the robotic fallback voice disappear after the backup voices? Check `engine` in data/history.json (no "via gtts").
- Is the new "Try this" ending useful and short? Any strange wording left?
- Did the VPS catch-up fire if the schedule dropped a run? Check `heartbeat.monitors` row `ai-morning-episode`.

## Open questions (not yet asked)
- Story selection: which stories landed or bored (partly answered: decision models were relevant)
- Anything invented (no complaints on 11-18)
- Sources to add or drop (current list: FEEDS and TLDR_TOPICS in generate.py)

## Known issues
- A forced re-run on the same day gets thin sources, because the first run already marked
  today's newsletters and posts as used. Don't judge length from a forced re-run.
- GitHub's scheduler can drop the daily run (11-18: first run at 12:51 CT). Handled by the VPS catch-up above.
- `en-US-AndrewMultilingualNeural` returned NoAudioReceived on most CI turns on 11-18 (1 of 4 locally too).
