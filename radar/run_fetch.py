"""Step 1 of the daily pipeline: fetch → prefilter → dedupe → data/raw/<date>.json.

Usage: python -m radar.run_fetch
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import dedupe, fetch, prefilter

ROOT = Path(__file__).resolve().parent.parent
HELSINKI = ZoneInfo("Europe/Helsinki")


def run(config_path=ROOT / "config.yaml", out_dir=ROOT / "data" / "raw"):
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    items, stats = fetch.fetch_all(config["feeds"])
    matched = prefilter.apply(items, config["keywords"])
    signals = dedupe.dedupe(matched, config["dedupe"]["similarity_threshold"])

    now = datetime.now(HELSINKI)
    payload = {
        "date": now.strftime("%Y-%m-%d"),
        "fetched_at": now.isoformat(timespec="seconds"),
        "topic": config["topic"]["name"],
        "feeds": stats,
        "totals": {
            "items_fetched": len(items),
            "items_matched": len(matched),
            "signals": len(signals),
        },
        "signals": [s.to_dict() for s in signals],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{payload['date']}.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    _print_summary(payload, out_path)
    failures = [k for k, v in stats.items() if not v["ok"]]
    return 1 if len(failures) == len(stats) else 0  # fail run only if ALL feeds died


def _print_summary(payload, out_path):
    print(f"Media Signal Radar — fetch {payload['date']}")
    for key, st in payload["feeds"].items():
        mark = "ok " if st["ok"] else "FAIL"
        detail = f"{st.get('items', 0)} items" if st["ok"] else st.get("error", "")
        print(f"  [{mark}] {key}: {detail}")
    t = payload["totals"]
    print(
        f"  total {t['items_fetched']} items -> {t['items_matched']} matched "
        f"-> {t['signals']} signals after dedupe"
    )
    print(f"  wrote {out_path}")


if __name__ == "__main__":
    sys.exit(run())
