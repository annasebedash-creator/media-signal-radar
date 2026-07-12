import re


def build_matcher(keywords_cfg):
    """Compile the keyword prefilter from config.

    Substrings match case-insensitively. Patterns that contain an
    uppercase letter (e.g. \\bAI\\b) are treated as case-sensitive so
    that 'AI' matches 'AI-malli' but not 'kaislikko'.
    """
    substrings = [s.lower() for s in keywords_cfg.get("substrings", [])]
    patterns = []
    for p in keywords_cfg.get("patterns", []):
        flags = 0 if any(c.isupper() for c in p) else re.IGNORECASE
        patterns.append((p, re.compile(p, flags)))

    def match(item):
        """Return the matching keyword/pattern, or None."""
        text = f"{item.title} {item.lead}"
        lowered = text.lower()
        for sub in substrings:
            if sub in lowered:
                return sub
        for raw, rx in patterns:
            if rx.search(text):
                return raw
        return None

    return match


def apply(items, keywords_cfg):
    """Keep only items matching the topic prefilter; tag each with its keyword."""
    match = build_matcher(keywords_cfg)
    kept = []
    for item in items:
        hit = match(item)
        if hit:
            item.keyword = hit
            kept.append(item)
    return kept
