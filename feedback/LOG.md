# AI Morning feedback log

Read this FIRST in every feedback session. Settled items are not re-asked. Items under
"Verify next session" are asked once as a quick yes/no check, then moved to Settled.

## State
- **Cadence:** daily, through 2026-11-24. The 11-24 session asks: keep daily, or go weekly?
- **Last reviewed episode:** 2026-11-22 ("Rust Servers, Reasoning Dials, Agent Logs", VPS-started 06:00 CT, 11 min 18 s)
- **Next session queued:** 2026-11-23 07:00 (`C:\AI\handoffs\queue\2026-11-23-0700-ai-morning-feedback.md`)

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
| 2026-11-18 | Repo stays public; hosts stay generic about the listener (private Pages needs Enterprise Cloud). Revisit: private repo plus VPS hosting if he wants more personal hosts | LISTENER_CONTEXT, drop_leaks |
| 2026-11-18 | Voice: keep AndrewMultilingual (his pick); revisit a different TTS service if still stiff | VOICE_A (unchanged) |
| 2026-11-18 | Delivery: the daily build can be dropped by GitHub's scheduler; VPS cron starts it from 06:00 CT and alerts at 09:00 CT | tools/vps, VPS /etc/cron.d/ai-morning-catchup |
| 2026-11-19 | "Try this": 3-5 sentences, a concrete step startable today, stand-alone (name every item, never "the four layers" unexplained) | SYSTEM_PROMPT |
| 2026-11-19 | Never finish under 10 min: on thin-news days go deeper on the best stories | SYSTEM_PROMPT |
| 2026-11-19 | Weather API timeout: 3 rounds of retries before saying "unavailable" | WEATHER_ROUNDS |
| 2026-11-19 | Empty security sources: short "no fresh news" line plus a 2-3 min evergreen refresher (rotating topics) | SECURITY_EVERGREEN, build_prompt |
| 2026-11-20 | 11-19 changes verified good: weather short, Try this stand-alone and practical, length 12:45, no voice glitches | SYSTEM_PROMPT (unchanged) |
| 2026-11-20 | Try this follows the listener's whole stack (PostgreSQL, Python/PyPI, Node/npm, Docker, Linux VPS, Claude/Anthropic API): stack release, vulnerability or upgrade news wins the Try this; private repo variable, "if you run it" | LISTENER_STACK, STACK_RULE |
| 2026-11-21 | 11-20 stack change verified (macOS tip was fine); all three themes landed, nothing wrong, no source changes | SYSTEM_PROMPT (unchanged) |
| 2026-11-21 | Try this is a block of 2-3 short items (~2 min), stack item first when there is stack news; ideal length 10-13 min | SYSTEM_PROMPT |
| 2026-11-22 | 11-21 Try this change verified: 2-3 items, useful and short enough. Decision-log story (Muru) landed as pertinent | SYSTEM_PROMPT (unchanged) |
| 2026-11-22 | Andrew voices (both) refuse some text ("Muru"), causing 4 robotic gTTS turns; Andrew replaced by Brian in the edge-tts fallback chain (neural chain per host before gTTS) | VOICE_A, EDGE_CHAIN |
| 2026-11-22 | Leave Microsoft for the primary voices: Google Cloud TTS Chirp 3 HD (free 1M chars/month, ~90 episodes), edge-tts becomes the fallback; free or near-free only | GOOGLE_TTS_API_KEY, GOOGLE_VOICE_A/B, _google_one; voices picked: Charon (Andrew) and Aoede (Ava), key stored as GitHub secret, project ai-morning-tts-32015, $1 budget alert |
| 2026-11-22 | No "my turn" handovers; alternate who introduces stories, no long one-host runs | SYSTEM_PROMPT |

## Verify next session (trials)
- 2026-11-22 voice change: did Google Chirp voices go live (`engine` "google-chirp" in data/history.json)? Are the two voices distinct and good? Any robotic turn left? Did the "my turn" wording stop? (If the Google key was not yet added, tomorrow still uses the Brian/Ava edge-tts chain.)
- Andrew voice DECIDED 2026-11-18: keep en-US-AndrewMultilingualNeural (his pick from the samples); plain Andrew is the backup after 3 failed tries.
  Still stiff, so revisit. FUTURE IDEA (operator, 2026-11-18): if the voices stay stiff, consider a different TTS service for reading the script.
- Project description approved and set as the LISTENER_CONTEXT repo variable (2026-11-18). Ask if the hosts' references to it feel right.
- Did the robotic fallback voice disappear after the backup voices? Check `engine` in data/history.json (no "via gtts").
- Is the new "Try this" ending useful and short? Any strange wording left?
- Did the VPS catch-up fire if the schedule dropped a run? Check `heartbeat.monitors` row `ai-morning-episode`.

- 2026-11-19 changes, check on the 11-20 episode: weather present? Try this stand-alone and practical? Length at least 10 min? If security was thin, was the evergreen refresher OK?
- OPEN: TLDR issues seem to publish after 06:00 CT (11-19 issues were live later in the day; the 06:00 build fell back to the used 11-18 issue). Operator approved no start-time change; revisit if security/news stay thin.

- 2026-11-21 change, check on the 11-22 episode: Try this is 2-3 short items, each stand-alone and startable today; one follows the stack if there was stack news; length still under 15 min.
- OPEN (operator idea, 2026-11-20): a full roster of dependencies and tools per project, checked against the news. Needs a private roster file built from his project manifests; propose it next session.

## Open questions (not yet asked)
- Story selection: which stories landed or bored (partly answered: decision models were relevant)
- Anything invented (no complaints on 11-18)
- Sources to add or drop (current list: FEEDS and TLDR_TOPICS in generate.py)

## Known issues
- A forced re-run on the same day gets thin sources, because the first run already marked
  today's newsletters and posts as used. Don't judge length from a forced re-run.
- GitHub's scheduler can drop the daily run (11-18: first run at 12:51 CT). Handled by the VPS catch-up above.
- `en-US-AndrewMultilingualNeural` returned NoAudioReceived on most CI turns on 11-18 (1 of 4 locally too).
