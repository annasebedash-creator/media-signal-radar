"""Step 2 of the daily pipeline: classify data/raw/<date>.json → data/classified/<date>.json.

Usage: python -m radar.run_classify [YYYY-MM-DD]  (defaults to today, Helsinki time)
Requires OPENAI_API_KEY in the environment.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import classify

ROOT = Path(__file__).resolve().parent.parent
HELSINKI = ZoneInfo("Europe/Helsinki")


def run(date=None):
    date = date or datetime.now(HELSINKI).strftime("%Y-%m-%d")
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    model = config.get("classifier", {}).get("model", classify.MODEL)
    raw_path = ROOT / "data" / "raw" / f"{date}.json"
    if not raw_path.exists():
        print(f"no raw data for {date} — run radar.run_fetch first")
        return 1

    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    signals = payload["signals"]
    print(f"Media Signal Radar — classify {date}: {len(signals)} signals ({model})")

    failures = classify.classify_all(signals, model)

    counts = {}
    for s in signals:
        c = s.get("classification")
        if c:
            counts[c["relevance"]] = counts.get(c["relevance"], 0) + 1

    payload["classified_at"] = datetime.now(HELSINKI).isoformat(timespec="seconds")
    payload["model"] = model
    out_dir = ROOT / "data" / "classified"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date}.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rel_summary = ", ".join(f"rel {k}: {v}" for k, v in sorted(counts.items()))
    print(f"  done ({rel_summary}; {failures} failures)")
    print(f"  wrote {out_path}")
    return 1 if failures == len(signals) else 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else None))
