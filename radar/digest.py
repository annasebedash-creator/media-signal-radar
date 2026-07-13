"""Build the daily digest from classified signals.

Ranking and grouping are deterministic code; the LLM writes only the
three-bullet radar summary. Output is structured JSON — the site
generator renders it to HTML.
"""

import json
import time

from openai import OpenAI

DIGEST_MODEL = "gpt-4o"
MAX_RETRIES = 3

SUMMARY_SYSTEM_PROMPT = """\
Olet media-analyytikko. Kirjoitat aamukatsauksen aiheesta "Tekoäly Suomessa"
päivän uutissignaalien pohjalta.

Kirjoita TÄSMÄLLEEN KOLME ytimekästä bullet-virkettä suomeksi:
- Jokainen bullet on yksi virke, enintään noin 25 sanaa.
- Konkreettisia havaintoja päivän signaaleista — ei yleisluontoista
  pohdintaa tekoälystä, ei hypeä, ei "tekoäly kehittyy nopeasti" -täytettä.
- Neutraali analyytikon ääni, kuten viestintätoimiston asiakaskatsauksessa.
- Jos päivässä on selvä pääsignaali, aloita siitä.
- Älä keksi mitään, mitä signaaleissa ei ole.
"""

SUMMARY_SCHEMA = {
    "name": "radar_summary",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "bullets": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 3,
            }
        },
        "required": ["bullets"],
        "additionalProperties": False,
    },
}


def _rank_key(signal):
    c = signal["classification"]
    return (
        c["relevance"],
        c["finland_link"],
        signal["outlet_count"],
    )


def _signal_brief(signal):
    c = signal["classification"]
    return {
        "otsikko": signal["title"],
        "tyyppi": c["signal_type"],
        "sävy": c["tone"],
        "toimijat": c["stakeholders"],
        "miksi": c["why_care"],
        "medioita": signal["outlet_count"],
    }


def write_summary(signals, model=DIGEST_MODEL):
    """One LLM call: three Finnish bullets summarizing the day."""
    briefs = [_signal_brief(s) for s in signals]
    client = OpenAI()
    user_msg = "Päivän signaalit:\n" + json.dumps(briefs, ensure_ascii=False, indent=1)
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_schema", "json_schema": SUMMARY_SCHEMA},
            )
            return json.loads(resp.choices[0].message.content)["bullets"]
        except Exception as exc:  # noqa: BLE001 — retry transient API errors
            last_err = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"summary failed after {MAX_RETRIES} tries: {last_err}")


def build_digest(payload, summary_model=DIGEST_MODEL):
    """Classified day payload → digest dict. Relevance 0 items are dropped
    (kept in data/classified for transparency); 2–3 are top signals, 1 is
    the compact 'also noted' list."""
    classified = [s for s in payload["signals"] if s.get("classification")]
    relevant = [s for s in classified if s["classification"]["relevance"] >= 1]
    relevant.sort(key=_rank_key, reverse=True)

    top = [s for s in relevant if s["classification"]["relevance"] >= 2]
    other = [s for s in relevant if s["classification"]["relevance"] == 1]

    bullets = write_summary(relevant, summary_model) if relevant else []

    return {
        "date": payload["date"],
        "topic": payload["topic"],
        "summary": bullets,
        "top_signals": [_export(s) for s in top],
        "other_signals": [_export(s) for s in other],
        "stats": {
            "feeds": len(payload["feeds"]),
            "items_fetched": payload["totals"]["items_fetched"],
            "signals": len(relevant),
            "classifier_model": payload.get("model", ""),
            "summary_model": summary_model,
        },
    }


def _export(signal):
    c = signal["classification"]
    return {
        "title": signal["title"],
        "lead": signal["lead"],
        "link": signal["link"],
        "outlet": signal["outlet"],
        "outlets": signal["outlets"],
        "outlet_count": signal["outlet_count"],
        "relevance": c["relevance"],
        "finland_link": c["finland_link"],
        "signal_type": c["signal_type"],
        "tone": c["tone"],
        "stakeholders": c["stakeholders"],
        "why_care": c["why_care"],
    }
