# Listener-feedback loop: design (approved 2026-11-17)

## Intent
The operator gives feedback right after listening, in the morning, while memory is fresh. That
feedback has to change the next episodes and must not be asked twice.

## Goals / non-goals
- Goal: a feedback session waits in the handoff queue each morning, with no manual setup.
- Goal: changes the operator accepts land in `generate.py` the same session and get committed.
- Goal: settled questions are never re-asked.
- Non-goal: detecting a "listened" signal. Nothing reaches this PC, so the queue entry waits
  until 07:00 and the operator opens it after listening.
- Anti-goal: a new scheduled job. Net scheduled jobs added: **0**.

## Approaches considered
1. **Each session queues the next one (picked).** The session writes tomorrow's queue file
   (`start_after` 07:00 next day) as its first step. 0 jobs. Trade-off: if the entry is
   deleted unopened, the chain stops until it is re-queued.
2. A step in an existing PC morning job drops a queue file when an episode is unreviewed. It
   can't silently stop, but it couples podcast logic to an unrelated job.
3. A "leave feedback" link in the show notes. It needs a GitHub issue plus a PC poller, so a
   new job and the most moving parts.
4. A standing weekly session. Rejected: the operator wants feedback right after listening.

## Design
- `feedback/SESSION.md`: the interview procedure. Queue files just point at it.
- `feedback/LOG.md`: cadence, last reviewed episode, settled decisions, open questions. Read first.
- `feedback/<date>-session.md`: one per session, answers close to verbatim.
- **Cadence:** daily through 2026-11-24. The 11-24 session asks whether to switch to weekly
  and writes the answer into LOG.md.
- **Same-date republish:** a date can be published more than once (the 11-17 seed was replaced
  by a forced run). The session finds every version in git and asks which one was heard.

## Today's changes to generate.py (from the 11-17 session)
1. Metric: Open-Meteo in Celsius and km/h, prompt rule "metric only", show notes in °C.
2. Weather: two or three factual sentences with no tip or banter. Drop the "weather as the
   hook" opening.
3. VOICE_A default changes to en-US-AndrewMultilingualNeural. The log names which host fell
   back to gTTS.
4. Length: target 11 real minutes (10-12) at 165 wpm, a 15-minute hard cap in the prompt,
   and a warning in the log if the audio comes out longer.

## Left to the builder
How the cap is expressed in words, and the exact wording of the rules.
