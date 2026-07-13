"""Render the static site (docs/) from data/digests/*.json.

English frame, Finnish digest content. No frameworks — plain HTML + one
stylesheet, served by GitHub Pages from /docs.
"""

import html
import json
from pathlib import Path

REPO_URL = "https://github.com/annasebedash-creator/media-signal-radar"

TYPE_FI = {
    "launch": "julkistus",
    "crisis": "kriisi",
    "regulation": "sääntely",
    "opinion": "mielipide",
    "research": "tutkimus",
    "trend": "trendi",
}
TONE_FI = {"critical": "kriittinen", "neutral": "neutraali", "positive": "positiivinen"}
WEEKDAYS_FI = [
    "maanantai", "tiistai", "keskiviikko", "torstai",
    "perjantai", "lauantai", "sunnuntai",
]


def _e(text):
    return html.escape(str(text), quote=True)


def _date_fi(iso_date):
    from datetime import date

    d = date.fromisoformat(iso_date)
    return f"{WEEKDAYS_FI[d.weekday()]} {d.day}.{d.month}.{d.year}"


def _page(title, body, root=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)}</title>
<link rel="stylesheet" href="{root}style.css">
</head>
<body>
<header class="site-header">
  <a class="brand" href="{root}index.html">Media Signal Radar</a>
  <span class="tagline">AI in Finnish public discourse — automated daily media monitoring</span>
</header>
<main>
{body}
</main>
<footer class="site-footer">
  <p><strong>About this site.</strong> A personal portfolio project by Anna Sebedach:
  an autonomous agent fetches public RSS headlines from seven Finnish news outlets
  every morning, an LLM classifies topic signals the way a communications consultant
  would, and this site republishes only the analysis — never article text.
  Every item links to and credits its original outlet.
  Classification is automated and may contain errors. Not affiliated with any outlet.
  <a href="{REPO_URL}">Source code &amp; methodology</a>.</p>
</footer>
</body>
</html>
"""


def _signal_card(s):
    badges = f'<span class="badge type-{_e(s["signal_type"])}">{_e(TYPE_FI[s["signal_type"]])}</span>'
    badges += f'<span class="badge tone-{_e(s["tone"])}">{_e(TONE_FI[s["tone"]])}</span>'
    if s["finland_link"]:
        badges += '<span class="badge fi">🇫🇮 kotimainen kytkös</span>'
    if s["outlet_count"] > 1:
        badges += f'<span class="badge multi">{s["outlet_count"]} mediaa</span>'
    stakeholders = ""
    if s["stakeholders"]:
        stakeholders = f'<p class="stakeholders">Toimijat: {_e(", ".join(s["stakeholders"]))}</p>'
    lead = f'<p class="lead">{_e(s["lead"])}</p>' if s["lead"] else ""
    return f"""<article class="signal">
  <div class="badges">{badges}</div>
  <h3><a href="{_e(s["link"])}" rel="noopener">{_e(s["title"])}</a></h3>
  {lead}
  <p class="why-care">{_e(s["why_care"])}</p>
  {stakeholders}
  <p class="source">Lähde: {_e(s["outlet"])}</p>
</article>"""


def _digest_body(d):
    bullets = "\n".join(f"    <li>{_e(b)}</li>" for b in d["summary"])
    top = "\n".join(_signal_card(s) for s in d["top_signals"])
    other = "\n".join(
        f'    <li><a href="{_e(s["link"])}" rel="noopener">{_e(s["title"])}</a> '
        f'<span class="outlet">({_e(s["outlet"])})</span></li>'
        for s in d["other_signals"]
    )
    other_section = ""
    if other:
        other_section = f"""<section>
  <h2>Muut havainnot</h2>
  <ul class="other-signals">
{other}
  </ul>
</section>"""
    st = d["stats"]
    return f"""<h1>Päivän katsaus — {_e(_date_fi(d["date"]))}</h1>
<section class="summary">
  <h2>Tutkan yhteenveto</h2>
  <ul>
{bullets}
  </ul>
</section>
<section>
  <h2>Päivän signaalit</h2>
{top if top else "<p>Ei merkittäviä signaaleja tänään.</p>"}
</section>
{other_section}
<p class="run-stats">{st["items_fetched"]} headlines from {st["feeds"]} feeds →
{st["signals"]} topic signals · classifier {_e(st["classifier_model"])} ·
summary {_e(st["summary_model"])}</p>
"""


def render_site(digest_dir, docs_dir):
    """Render index (latest digest + archive) and one page per day."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "digest").mkdir(exist_ok=True)

    digests = sorted(
        (json.loads(p.read_text(encoding="utf-8")) for p in digest_dir.glob("*.json")),
        key=lambda d: d["date"],
        reverse=True,
    )
    if not digests:
        raise SystemExit("no digests to render")

    for d in digests:
        page = _page(f"Media Signal Radar — {d['date']}", _digest_body(d), root="../")
        (docs_dir / "digest" / f"{d['date']}.html").write_text(page, encoding="utf-8")

    latest = digests[0]
    archive = "\n".join(
        f'    <li><a href="digest/{_e(d["date"])}.html">{_e(_date_fi(d["date"]))}</a>'
        f' <span class="outlet">— {len(d["top_signals"]) + len(d["other_signals"])} signaalia</span></li>'
        for d in digests
    )
    intro = f"""<section class="hero">
  <p>Every morning at 06:00 Helsinki time, this site rebuilds itself: an autonomous
  agent scans the RSS headlines of seven Finnish news outlets, an LLM classifies
  what it finds about one topic — <strong>AI in Finnish public discourse</strong> —
  the way a communications consultant would, and publishes the day's briefing below.
  No servers, no manual steps. <a href="{REPO_URL}">How it works →</a></p>
</section>
{_digest_body(latest).replace("<h1>Päivän katsaus", "<h1>Latest — päivän katsaus", 1)}
<section>
  <h2>Archive</h2>
  <ul class="archive">
{archive}
  </ul>
</section>"""
    (docs_dir / "index.html").write_text(
        _page("Media Signal Radar", intro), encoding="utf-8"
    )
    return len(digests)
