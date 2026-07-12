import re

from .models import Signal

_PUNCT_RE = re.compile(r"[^\wäöå]+", re.IGNORECASE)

# Finnish is agglutinative: "tekoälyn" / "tekoälyä" / "tekoälystä" are the
# same word. Comparing 6-char token prefixes is a cheap stemmer that is
# good enough for near-duplicate headlines.
_STEM_LEN = 6
_MIN_TOKEN_LEN = 3


def _canonical_link(link):
    return link.split("?")[0].rstrip("/")


def _title_stems(title):
    tokens = _PUNCT_RE.sub(" ", title.lower()).split()
    return {t[:_STEM_LEN] for t in tokens if len(t) >= _MIN_TOKEN_LEN}


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedupe(items, threshold=0.5):
    """Collapse duplicates into Signals.

    Exact link matches (same story via two feeds of one outlet) merge first;
    then titles whose stem sets overlap >= threshold merge across outlets.
    The representative is the item with the longest lead text.
    """
    signals = []
    seen_links = {}

    for item in items:
        link = _canonical_link(item.link)
        if link in seen_links:
            seen_links[link].duplicates.append(item)
            continue

        stems = _title_stems(item.title)
        merged = False
        for sig in signals:
            if _jaccard(stems, _title_stems(sig.item.title)) >= threshold:
                sig.duplicates.append(item)
                merged = True
                break
        if not merged:
            sig = Signal(item=item)
            signals.append(sig)
            seen_links[link] = sig

    # Promote the most informative item (longest lead) to representative.
    for sig in signals:
        best = max([sig.item] + sig.duplicates, key=lambda it: len(it.lead))
        if best is not sig.item:
            sig.duplicates = [it for it in [sig.item] + sig.duplicates if it is not best]
            sig.item = best

    return signals
