import json
import time

from openai import OpenAI

from . import prompts

MODEL = "gpt-4o-mini"
MAX_RETRIES = 3


def classify_signal(client, signal, model=MODEL):
    """Classify one signal dict (from data/raw). Returns the classification dict."""
    user_msg = prompts.USER_TEMPLATE.format(
        title=signal["title"],
        lead=signal["lead"] or "(ei ingressiä)",
        outlet=signal["outlet"],
        outlet_count=signal["outlet_count"],
    )
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0,
                messages=[
                    {"role": "system", "content": prompts.SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": prompts.CLASSIFICATION_SCHEMA,
                },
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001 — retry transient API errors
            last_err = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"classification failed after {MAX_RETRIES} tries: {last_err}")


def classify_all(signals, model=MODEL):
    """Classify every signal, attaching results under the 'classification' key.

    A signal that repeatedly fails gets classification=None rather than
    aborting the run; the digest step skips unclassified signals.
    """
    client = OpenAI()
    failures = 0
    for signal in signals:
        try:
            signal["classification"] = classify_signal(client, signal, model)
        except RuntimeError as exc:
            print(f"  WARN: {exc} — {signal['title'][:60]}")
            signal["classification"] = None
            failures += 1
    return failures
