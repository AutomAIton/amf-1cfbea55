# AI Morning feedback session: procedure

The agent reads this when a queue entry says "run the AI Morning feedback session". The
operator has just listened to the morning episode. Memory is fresh, so keep the session short.

## 0. Keep the chain alive (do this before anything else)
Read `feedback/LOG.md` § State for the cadence. Write the NEXT queue file now, with the
**Write tool** (a hook blocks shell writes into the queue):
- daily: `C:\AI\handoffs\queue\<tomorrow>-0700-ai-morning-feedback.md`, `start_after: <tomorrow>T07:00`
- weekly (once LOG.md says so): the next chosen weekday, 07:00
- stopped (LOG.md says so, or the podcast was dropped): write nothing, and say so

Copy the template at the bottom, change only the dates and `created` (from `date +%Y-%m-%dT%H:%M`),
and update "Next session queued" in LOG.md. If today's own queue entry is still in `queue\`
rather than `started\`, leave it alone.

## 1. Load what's settled
`git pull`, then read LOG.md in full. Never re-ask a Settled item. Ask each "Verify next
session" item once.

## 2. Find the unreviewed episodes
Episodes in `data/history.json` dated after "Last reviewed episode". For each date, run
`git log --format="%h %ci %s" -- data/script-<date>.txt`. If a date has more than one
version (a seed plus a forced re-run, say), ask the operator which one they heard (by title
and length), and use that version's script: `git show <hash>:data/script-<date>.txt`.
If nothing is unreviewed (no new episode, or the run failed), say so and stop. The chain is
already queued.

## 3. Interview: one question at a time, newest episode first
Quote 1-2 lines from the script to jog memory. Order: Verify items → overall verdict →
length (state the real `seconds`) → hosts and banter → weather → stories that landed or
bored → security depth → anything wrong or invented → voice glitches (grep the run log:
`gh run view <id> --log | grep -E "gTTS fallback|Audio via|WARNING"`) → sources to add or
drop. Skip anything already settled. If the operator says they can't remember, move on.

## 4. Record
Write `feedback/<today>-session.md` with answers close to verbatim, per episode.

## 5. Land the changes the operator accepts
Propose each change in one line and apply only the ones they accept. Where things live in `generate.py`:
| Feedback about | Knob |
|---|---|
| segment rules, units, accuracy, length wording | SYSTEM_PROMPT |
| openings / tone / host dynamic / endings | OPENINGS / TONES / DYNAMICS / SIGNOFFS |
| length | TARGET_MINUTES, MAX_MINUTES, WPM |
| sources | FEEDS, TLDR_TOPICS |
| voices | VOICE_A, VOICE_B defaults |
For each accepted change, add an assertion to `tests/selfcheck.py`, run
`.venv/Scripts/python tests/selfcheck.py` (it must print OK) and `.venv/Scripts/python generate.py --sources-only`
(free). Then move the item into LOG.md § Settled, set "Last reviewed episode", and commit and push
explicit paths. **No forced workflow run.** Tomorrow's scheduled episode is the proof, and a forced
re-run replaces an episode the operator may already have downloaded.

## 6. Close
End with the status footer: Session done? / Left / Loose ends / Next.

## Queue file template
````
---
kind: handoff
folder: C:\AI\ai-morning-podcast
model: claude-sonnet-5-5
effort: medium
plan_mode: no
name: ai-morning-feedback-<DATE>
created: <YYYY-MM-DDTHH:mm>
start_after: <DATE>T07:00
start_note: after you've listened to the <DATE> episode
---
MODEL:  claude-sonnet-5-5
EFFORT: medium
PLAN MODE: no
Start on or after <Day> <DATE> 07:00: after you've listened to that morning's episode.

```
AI Morning listener-feedback session for the <DATE> episode (and any earlier unreviewed ones).

COLD-START VALIDATION (do first, report drift):
1. Confirm C:\AI\ai-morning-podcast\feedback\SESSION.md and feedback\LOG.md exist; git pull.
2. Re-derive: today's date vs <DATE>; which episodes in data/history.json are dated after
   LOG.md's "Last reviewed episode" (that count is the scope, not this prompt).
3. Restate the goal and next 3 actions; flag ambiguity. Never run destructive git commands,
   never force a workflow run, never delete queue files about other work.

Do: follow feedback\SESSION.md exactly. Step 0 (queue the next session) comes first.

DONE WHEN:
- The next queue file exists in C:\AI\handoffs\queue (or LOG.md says the chain stopped). Proof: the path.
- feedback\<today>-session.md has the operator's answers. Proof: the file.
- Accepted changes are committed with tests\selfcheck.py printing OK, and LOG.md is updated. Proof: the commit.
- Operator symptom: the operator confirms their feedback was captured and nothing settled was re-asked.
```

```claims
path  C:/AI/ai-morning-podcast/feedback/SESSION.md   exists
path  C:/AI/ai-morning-podcast/feedback/LOG.md       exists
git   C:/AI/ai-morning-podcast                       branch=main
date  <DATE>                                         = <Day3>
```
````
