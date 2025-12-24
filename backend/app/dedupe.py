from typing import Iterable, List, Set, TYPE_CHECKING
from .models import Link
from .constants import FINGERPRINT_DELIMITER
from datetime import datetime, timedelta
import logging

if TYPE_CHECKING:
    from .extractors.base import BaseExtractor


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


def get_fingerprints_with_lookback(
    extractor: 'BaseExtractor',
    post_id: int,
    today_iso: str,
    site_key: str = None,
    storage_module = None
) -> Set[str]:
    """
    Get fingerprints for today and previous days based on extractor's requirements.
    
    This function checks the extractor's check_previous_days() method to determine
    how many days back to load fingerprints. This prevents duplicate links from being
    re-added when extractors include links from previous days in their output.
    
    Args:
        extractor: The extractor instance being used
        post_id: The WordPress post ID
        today_iso: Today's date in YYYY-MM-DD format
        site_key: Optional site key for multi-site setups
        storage_module: The storage module with get_known_fingerprints method
        
    Returns:
        Set of fingerprints from today and previous days (if applicable)
    """
    if storage_module is None:
        from . import mongo_storage as storage_module
    
    # Start with today's fingerprints
    known_fps = storage_module.get_known_fingerprints(post_id, today_iso, site_key)
    
    # Check if extractor needs previous days' fingerprints
    lookback_days = extractor.check_previous_days()
    
    if lookback_days > 0:
        today_date = datetime.strptime(today_iso, "%Y-%m-%d")
        
        for i in range(1, lookback_days + 1):
            prev_date = today_date - timedelta(days=i)
            prev_iso = prev_date.strftime("%Y-%m-%d")
            prev_fps = storage_module.get_known_fingerprints(post_id, prev_iso, site_key)
            known_fps = known_fps.union(prev_fps)
        
        logging.info(
            f"[DEDUPE] {extractor.__class__.__name__}: Checking fingerprints for {lookback_days + 1} days "
            f"({today_iso} back to {(today_date - timedelta(days=lookback_days)).strftime('%Y-%m-%d')})"
        )
    
    return known_fps
