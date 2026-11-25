# AI Morning feedback log

Read this FIRST in every feedback session. Settled items are not re-asked. Items under
"Verify next session" are asked once as a quick yes/no check, then moved to Settled.

## State
- **Cadence:** daily, indefinitely (operator chose to keep daily on 2026-11-24). Stop the chain only when he says so.
- **Last reviewed episode:** 2026-11-25 ("Eleven Minutes From Flaw to Root", VPS-started 06:00 CT, 11 min 35 s)
- **Next session queued:** 2026-11-26 07:00 (`C:\AI\handoffs\queue\2026-11-26-0700-ai-morning-feedback.md`)

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
| 2026-11-23 | Google Chirp voices verified: distinct, good, not robotic; no "my turn" handovers, flow natural | VOICE (unchanged) |
| 2026-11-23 | 10:27 was the right length on a quiet-news day; banter right; all three pieces (select boxes, OpenAI Perplexity, prompt-injection refresher) pertinent | SYSTEM_PROMPT (unchanged) |
| 2026-11-23 | Name the exact model, tools, skills and versions in AI-build stories (his main interest: improving his own builds); never invent names | SYSTEM_PROMPT "Specifics" |
| 2026-11-24 | 13:52 is just right; banter good; no robotic voice; all stories good, the AI-agent attack story was the standout for a security-minded listener; accuracy check found no invented items | SYSTEM_PROMPT (unchanged) |
| 2026-11-24 | Keep the podcast daily (no move to weekly); no sources to drop | Cadence above, FEEDS/TLDR_TOPICS (unchanged) |
| 2026-11-24 | TLDR sources not thin: 11-23 was a one-off weekend gap | FEEDS (unchanged) |
| 2026-11-22 | No "my turn" handovers; alternate who introduces stories, no long one-host runs | SYSTEM_PROMPT |
| 2026-11-25 | 11:35 length right, all stories landed | TARGET_MINUTES, FEEDS (unchanged) |
| 2026-11-25 | Always end on a plain goodbye; any recap comes before it, in complete everyday sentences naming what to do; no slogans | SYSTEM_PROMPT "Sign-off", SIGNOFFS |
| 2026-11-25 | Dependency roster idea: queue it as its own build, plan first | queue `2026-11-26-0900-ai-morning-dependency-roster.md` |

## Verify next session (trials)
- 2026-11-25 change, check on the 11-26 episode: does it end on a plain goodbye, with any recap before it in clear full sentences?
- OPEN: TLDR issues seem to publish after 06:00 CT (11-19). Operator approved no start-time change; revisit only if security/news stay thin.
- FUTURE IDEA (operator, 2026-11-18): another TTS service if voices stay stiff (Google Chirp verified good 2026-11-23).
- Note: the gitleaks pre-commit hook lives in this repo's .git/hooks (untracked; reinstall on a fresh clone).

## Open questions (not yet asked)
- Story selection: which stories landed or bored (partly answered: decision models were relevant)
- Anything invented (no complaints on 11-18)
- Sources to add or drop (current list: FEEDS and TLDR_TOPICS in generate.py)

## Known issues
- A forced re-run on the same day gets thin sources, because the first run already marked
  today's newsletters and posts as used. Don't judge length from a forced re-run.
- GitHub's scheduler can drop the daily run (11-18: first run at 12:51 CT). Handled by the VPS catch-up above.
- `en-US-AndrewMultilingualNeural` returned NoAudioReceived on most CI turns on 11-18 (1 of 4 locally too).
