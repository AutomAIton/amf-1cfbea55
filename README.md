# AI Morning

A private daily two-host podcast on AI. Every morning GitHub Actions:

1. gathers the Chicago weather (Open-Meteo), TLDR AI and TLDR InfoSec, new posts from AI engineering
   blogs (Simon Willison, OpenAI, Anthropic, Latent Space) and AI security blogs (Embrace The Red,
   Simon Willison's prompt-injection tag);
2. makes one Claude API call that writes a ~10-minute script for two hosts, Andrew and Ava;
3. voices each line with Google Cloud Chirp 3 HD when GOOGLE_TTS_API_KEY is set, else Microsoft neural voices (edge-tts); a chain of neural voices then gTTS covers any line that fails;
4. commits the MP3 and `docs/feed.xml`, which GitHub Pages serves to Apple Podcasts.

Design modelled on a personal "TLDL" podcast pipeline; code written fresh.

## Settings

Secrets: `ANTHROPIC_API_KEY`. Variables: `BASE_URL` (the Pages URL, no trailing slash) and, optionally,
`LISTENER_NAME`, `CLAUDE_MODEL` (default `claude-opus-5-5`), `TARGET_MINUTES` (11 real minutes; hard stop `MAX_MINUTES` 15 in generate.py), `TLDR_TOPICS` (`ai,infosec`).
Feeds are the `FEEDS` list at the top of `generate.py`.

## Listener feedback

`feedback/` holds the loop: `SESSION.md` (the interview procedure, which queues the next session),
`LOG.md` (settled decisions, read first), one `<date>-session.md` per interview. `python tests/selfcheck.py`
checks that the settled decisions are still in `generate.py`.

## Run by hand

```
pip install -r requirements.txt
python generate.py --sources-only          # what was gathered; free
python generate.py --force --no-audio      # writes only the script; one API call
```

Actions > Daily episode > Run workflow (tick "Rebuild") rebuilds today's episode.

## Notes

- The repo is public, so the feed and audio are public to anyone with the URL. Only public news goes in.
  The feed is marked `itunes:block` so it stays out of podcast directories.
- Scraped text is passed to Claude as untrusted data inside `<source_data>`; the model has no tools.
- If Claude declines (a security story can trip a safety filter) the request falls back to another
  model; if that also declines, the episode is rebuilt without the security segment.
- Only the last 14 episodes are kept.
- A failed run emails the repo owner (GitHub's default). No episode in the feed by 7:30 AM = check Actions.
