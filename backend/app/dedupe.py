from typing import Iterable, List, Set
from .models import Link
from .constants import FINGERPRINT_DELIMITER


def fingerprint(link: Link) -> str:
    return f"{link.url}{FINGERPRINT_DELIMITER}{link.published_date_iso}"


def filter_only_today(links: Iterable[Link], today_iso: str) -> List[Link]:
    return [l for l in links if l.published_date_iso == today_iso]


def dedupe_by_fingerprint(links: Iterable[Link], known_fingerprints: Set[str]) -> List[Link]:
    out: List[Link] = []
    seen = set()
    for l in links:
        fp = fingerprint(l)
        if fp in known_fingerprints or fp in seen:
            continue
        seen.add(fp)
        out.append(l)
    return out
