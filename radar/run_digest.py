"""Step 3 of the daily pipeline: data/classified/<date>.json → data/digests/<date>.json.

Usage: python -m radar.run_digest [YYYY-MM-DD]
Requires OPENAI_API_KEY in the environment.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import digest

ROOT = Path(__file__).resolve().parent.parent
HELSINKI = ZoneInfo("Europe/Helsinki")


def run(date=None):
    date = date or datetime.now(HELSINKI).strftime("%Y-%m-%d")
    src = ROOT / "data" / "classified" / f"{date}.json"
    if not src.exists():
        print(f"no classified data for {date} — run radar.run_classify first")
        return 1

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    model = config.get("digest", {}).get("model", digest.DIGEST_MODEL)

    payload = json.loads(src.read_text(encoding="utf-8"))
    result = digest.build_digest(payload, model)

    out_dir = ROOT / "data" / "digests"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{date}.json"
    out_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Media Signal Radar — digest {date}")
    for b in result["summary"]:
        print(f"  • {b}")
    print(
        f"  {len(result['top_signals'])} top signals, "
        f"{len(result['other_signals'])} muut havainnot"
    )
    print(f"  wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else None))
