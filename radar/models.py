from dataclasses import dataclass, field, asdict


@dataclass
class Item:
    """One RSS entry: headline + lead + link only (see legal guardrails in README)."""

    outlet: str
    feed: str
    title: str
    lead: str
    link: str
    published: str  # ISO 8601, empty if the feed omits it
    keyword: str = ""  # which prefilter keyword matched

    def to_dict(self):
        return asdict(self)


@dataclass
class Signal:
    """A deduplicated story: one representative item plus any duplicates
    from other feeds/outlets. The outlet count is itself a signal."""

    item: Item
    duplicates: list = field(default_factory=list)  # list[Item]

    @property
    def outlets(self):
        seen = []
        for it in [self.item] + self.duplicates:
            if it.outlet not in seen:
                seen.append(it.outlet)
        return seen

    def to_dict(self):
        d = self.item.to_dict()
        d["outlets"] = self.outlets
        d["outlet_count"] = len(self.outlets)
        d["duplicates"] = [
            {"outlet": it.outlet, "title": it.title, "link": it.link}
            for it in self.duplicates
        ]
        return d
