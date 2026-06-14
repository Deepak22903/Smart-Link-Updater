"""
Popbies Extractor

Handles SmartLink-style pages where dated sections are delimited by HTML
comment markers and each link is wrapped in a smartlink-item block.

HTML structure:
    <!-- smartlink:section:2026-06-14 -->
    <p style="..."><strong>June 14, 2026</strong></p>
    <div class="smartlink-item">
        <span class="smartlink-title">Free Tokens</span>
        <a class="smartlink-btn" href="https://..." target="_blank" rel="noopener noreferrer">Claim</a>
    </div>
    <div class="smartlink-item">
        <span class="smartlink-title">Free Stickers</span>
        <a class="smartlink-btn" href="https://..." ...>Claim</a>
    </div>
    <!-- smartlink:section:2026-06-13 -->
    ...

Extraction Logic:
- Locate the `<!-- smartlink:section:YYYY-MM-DD -->` comment for the target date.
- Walk the following siblings until the next section comment is reached.
- For each `div.smartlink-item`, use `span.smartlink-title` as the title and
  `a.smartlink-btn` href as the URL.
"""

import re
import logging
from typing import List
from bs4 import BeautifulSoup, Comment, Tag

from .base import BaseExtractor
from ..models import Link

logger = logging.getLogger(__name__)


def register_extractor(name):
    """Local registration decorator - will be imported by __init__.py"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


# Matches comments like: smartlink:section:2026-06-14
SECTION_RE = re.compile(r"smartlink:section:(\d{4}-\d{2}-\d{2})")


@register_extractor("popbies")
class PopbiesExtractor(BaseExtractor):
    """Extractor for Popbies SmartLink-style dated comment sections."""

    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        return "popbies" in url.lower()

    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from the smartlink section matching the target date.

        Args:
            html: HTML content from the source page
            date: Target date in YYYY-MM-DD format (e.g., "2026-06-14")

        Returns:
            List of Link objects matching the date
        """
        logger.info("[POPBIES] Starting extraction for date=%s, html_size=%d", date, len(html or ""))
        soup = BeautifulSoup(html, "html.parser")
        links: List[Link] = []

        # Find the section comment matching the target date.
        start_comment = None
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            match = SECTION_RE.search(comment)
            if match and match.group(1) == date:
                start_comment = comment
                break

        if start_comment is None:
            logger.warning("[POPBIES] No smartlink section found for date=%s", date)
            return []

        # Walk siblings after the comment until the next section comment.
        # NOTE: use `.next_siblings` (not `find_next_siblings()`), because the
        # latter yields only Tag elements and silently skips the Comment nodes
        # that mark the section boundaries — which would cause us to bleed into
        # the following dates' items.
        for sibling in start_comment.next_siblings:
            # Stop when we reach the next dated section.
            if isinstance(sibling, Comment) and SECTION_RE.search(sibling):
                break

            if not isinstance(sibling, Tag):
                continue

            # The smartlink-item may be the sibling itself or nested within it.
            items = []
            if "smartlink-item" in sibling.get("class", []):
                items = [sibling]
            else:
                items = sibling.find_all("div", class_="smartlink-item")

            for item in items:
                link = self._parse_item(item, date)
                if link:
                    links.append(link)

        logger.info("[POPBIES] Extraction complete. links=%d", len(links))
        return links

    def _parse_item(self, item: Tag, date: str):
        """Parse a single smartlink-item div into a Link."""
        anchor = item.find("a", class_="smartlink-btn")
        if not anchor:
            anchor = item.find("a", href=True)
        if not anchor:
            return None

        href = (anchor.get("href") or "").strip()
        if not href or not href.startswith("http"):
            return None

        title_span = item.find("span", class_="smartlink-title")
        title = title_span.get_text(strip=True) if title_span else ""
        if not title:
            title = anchor.get_text(strip=True) or "Claim"

        target = anchor.get("target", "_blank") or "_blank"

        return Link(
            url=href,
            title=title,
            published_date_iso=date,
            target=target,
        )
