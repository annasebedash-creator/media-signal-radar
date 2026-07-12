# Media Signal Radar

An autonomous agent that watches Finnish media for one topic — **"Tekoäly Suomessa", AI in Finnish public discourse** — classifies what it finds the way a communications consultant would, and publishes a daily digest. Zero hosting costs: GitHub Actions runs the pipeline, GitHub Pages serves the result.

**Status: under construction** (July 2026). This README grows as the pieces land.

## How it works

```
GitHub Actions (daily cron, 06:00 Europe/Helsinki)
  → fetch 11 RSS feeds from 7 Finnish outlets (headlines + leads + links only)
  → keyword prefilter for the topic
  → near-duplicate collapse (same story in N outlets = one signal, outlet count kept)
  → LLM classification per signal: relevance, signal type, tone, stakeholders,
    "why should a communications team care"
  → daily markdown digest → committed to the repo → served by GitHub Pages
```

Monitored outlets: Yle, Helsingin Sanomat, Kauppalehti, Tekniikka&Talous, MTV Uutiset, Iltalehti, Ilta-Sanomat.

## Evaluation

Classification quality is measured, not assumed: a hand-labeled test set (native Finnish speaker) with published agreement numbers, including variance. See `EVALS.md` (coming with the eval step).

## Legal & ethical guardrails

- Only what the outlets publish in their **public RSS feeds** — headline, lead, link. Article pages are never fetched; paywalled or full text is never scraped or republished.
- Every digest item links to and credits its source outlet.
- Digest text is the model's *analysis*, not reproduced journalism.
- This is a personal portfolio project. Classification is automated and may contain errors; the digest is not journalism and not affiliated with any of the outlets.

## Running locally

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m radar.run_fetch
```

Output lands in `data/raw/<date>.json`.
