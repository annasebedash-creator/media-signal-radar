"""Step 4 of the daily pipeline: render docs/ from all digests.

Usage: python -m radar.run_site
"""

import sys
from pathlib import Path

from .site import render_site

ROOT = Path(__file__).resolve().parent.parent


def run():
    n = render_site(ROOT / "data" / "digests", ROOT / "docs")
    print(f"Media Signal Radar — site rendered: {n} digest(s) → docs/")
    return 0


if __name__ == "__main__":
    sys.exit(run())
