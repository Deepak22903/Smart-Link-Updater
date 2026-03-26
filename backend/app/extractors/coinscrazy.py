"""
Extractor for CoinsCrazy.com
Extracts daily links from dated sections with button-style links.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import List
import logging
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link


logger = logging.getLogger(__name__)


def register_extractor(name):
    """Local registration decorator - will be imported by __init__.py"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("coinscrazy")
class CoinsCrazyExtractor(BaseExtractor):
    """Extract links from CoinsCrazy.com daily reward sections."""
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        return "coinscrazy.com" in url.lower()
    
    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from the daily section matching target_date.
        
        HTML structure:
        - h4 with date like "Updated On: 06 February 2026"
        - Multiple wp-block-columns divs with button links
        - Links are in <a> tags within ub-button-container divs
        - Button text is in <span class="ub-button-block-btn">
        
        Args:
            html: HTML content from the source page
            date: Target date in YYYY-MM-DD format (e.g., "2026-02-06")
            
        Returns:
            List of Link objects matching the date
        """
        logger.info("[COINSCRAZY] Starting extraction for date=%s, html_size=%d", date, len(html or ""))
        soup = BeautifulSoup(html, 'html.parser')
        
        # Parse the date string (YYYY-MM-DD format)
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            logger.warning("[COINSCRAZY] Invalid date format received: %s", date)
            return []

        yesterday_date = target_date - timedelta(days=1)

        def _date_strings(d: datetime) -> tuple[str, str, str, str]:
            # Support both zero-padded and non-padded day formats.
            # Examples: "06 February 2026" and "6 February 2026"
            padded = d.strftime("%d %B %Y")
            non_padded = f"{d.day} {d.strftime('%B %Y')}"
            return padded, f"Updated On: {padded}", non_padded, f"Updated On: {non_padded}"

        (
            target_date_str,
            target_updated_on_str,
            target_date_str_no_pad,
            target_updated_on_str_no_pad,
        ) = _date_strings(target_date)
        (
            yesterday_date_str,
            yesterday_updated_on_str,
            yesterday_date_str_no_pad,
            yesterday_updated_on_str_no_pad,
        ) = _date_strings(yesterday_date)

        target_date_iso = target_date.strftime("%Y-%m-%d")
        yesterday_date_iso = yesterday_date.strftime("%Y-%m-%d")

        # Keep insertion order and avoid duplicate URLs (today first, then yesterday)
        links_map = OrderedDict()
        duplicate_count = 0

        # Find all h4 headings and extract sections for today + yesterday
        h4_tags = soup.find_all('h4', class_='wp-block-heading')
        logger.info("[COINSCRAZY] Found %d h4 date headings", len(h4_tags))

        for h4 in h4_tags:
            # Keep spaces between nested text nodes (<strong> inside <strong>)
            # and normalize repeated whitespace for stable matching.
            h4_text = " ".join(h4.get_text(" ", strip=True).split())

            section_date_iso = None
            if (
                target_updated_on_str in h4_text
                or target_date_str in h4_text
                or target_updated_on_str_no_pad in h4_text
                or target_date_str_no_pad in h4_text
            ):
                section_date_iso = target_date_iso
            elif (
                yesterday_updated_on_str in h4_text
                or yesterday_date_str in h4_text
                or yesterday_updated_on_str_no_pad in h4_text
                or yesterday_date_str_no_pad in h4_text
            ):
                section_date_iso = yesterday_date_iso

            if not section_date_iso:
                continue

            logger.info("[COINSCRAZY] Processing section heading='%s' mapped_date=%s", h4_text, section_date_iso)

            # Collect links after this heading until next heading
            current_element = h4.find_next_sibling()
            while current_element:
                # Stop at next date header
                if current_element.name == 'h4' and 'wp-block-heading' in current_element.get('class', []):
                    break

                if current_element.name == 'div' and 'wp-block-columns' in current_element.get('class', []):
                    anchors = current_element.find_all('a', href=True)
                    logger.debug("[COINSCRAZY] Found %d anchors in wp-block-columns section", len(anchors))
                    for anchor in anchors:
                        href = anchor.get('href', '').strip()

                        # Skip empty or invalid links
                        if not href or href.startswith('#'):
                            continue

                        button_span = anchor.find('span', class_='ub-button-block-btn')
                        button_text = button_span.get_text(strip=True) if button_span else "Link"

                        # Prefer today's version if same URL appears in both sections
                        if href not in links_map:
                            links_map[href] = Link(
                                url=href,
                                title=button_text,
                                published_date_iso=section_date_iso
                            )
                        else:
                            duplicate_count += 1
                            logger.debug("[COINSCRAZY] Duplicate URL skipped: %s", href)

                current_element = current_element.find_next_sibling()

        logger.info(
            "[COINSCRAZY] Extraction complete. unique_links=%d duplicates_skipped=%d",
            len(links_map),
            duplicate_count,
        )
        return list(links_map.values())

