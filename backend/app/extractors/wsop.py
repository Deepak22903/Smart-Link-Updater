from typing import List
from collections import OrderedDict
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime
import re
import requests

@register_extractor("wsop")
class WSOPExtractor(BaseExtractor):
    """Extractor for wsopga.me links grouped by date headings."""

    def can_handle(self, url: str) -> bool:
        url_lower = url.lower()
        return any(domain in url_lower for domain in ["wsopga.me", "freechipswsop.com", "wsopchipsfree.com"])

    def extract(self, html: str, date: str) -> List[Link]:
        import logging
        soup = BeautifulSoup(html, 'html.parser')
        # Use ordered dict to dedupe by href while preserving insertion order
        url_map = OrderedDict()

        # Parse the date in long format (e.g., "25 November 2025")
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                logging.warning(f"[WSOPExtractor] Could not parse date: {date}")
                return []
        target_date_str_unpadded = date_obj.strftime("%d %B %Y").lstrip('0')
        target_date_str_padded = date_obj.strftime("%d %B %Y")
        # Also try with ordinal suffix (1st, 2nd, 3rd, etc.)
        day = date_obj.day
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        target_date_str_ordinal = f"{day}{suffix} {date_obj.strftime('%B %Y')}"
        
        date_iso = date_obj.isoformat()

        logging.info(f"[WSOPExtractor] Looking for links for date: {target_date_str_unpadded} (also matches {target_date_str_padded} or {target_date_str_ordinal})")
        
        # Debug: log all <p><strong> tags found
        all_headings = []
        for p in soup.find_all("p"):
            strong = p.find("strong")
            if strong:
                all_headings.append(strong.get_text(strip=True))
        if all_headings:
            logging.info(f"[WSOPExtractor] Found {len(all_headings)} <p><strong> headings: {all_headings[:10]}")  # Log first 10
        else:
            logging.warning(f"[WSOPExtractor] No <p><strong> headings found in HTML")

        found_heading = False
        # Helper to extract anchors from a tag (p, li, div, etc.)
        def _extract_anchors_from_tag(tag):
            nonlocal url_map
            for a in tag.find_all('a', href=True):
                href = a.get('href') or ''
                if not href.startswith('http'):
                    continue
                if 'www.wsopga.me/' in href:
                    title = a.get_text(strip=True) or href
                    if href not in url_map:
                        # If the anchor text is just the href, treat as placeholder and log at debug level
                        if title == href:
                            logging.debug(f"[WSOPExtractor] Extracted placeholder link (no title): {href}")
                        else:
                            logging.info(f"[WSOPExtractor] Extracted link: {href} | Title: {title}")
                        url_map[href] = Link(title=title, url=href, date=date, published_date_iso=date_iso)
                    else:
                        # Decide if we should update existing title
                        existing = url_map[href]
                        existing_title = str(existing.title or '')
                        # Prefer descriptive titles over href-only titles
                        if existing_title == href or existing_title.strip() == '':
                            logging.info(f"[WSOPExtractor] Updated title for {href} from '{existing_title}' to '{title}'")
                            existing.title = title
                        elif title != href and len(title) > len(existing_title):
                            logging.info(f"[WSOPExtractor] Replaced shorter title for {href} ('{existing_title}') with longer '{title}'")
                            existing.title = title
                else:
                    logging.debug(f"[WSOPExtractor] Skipped non-matching link: {href}")

        for p in soup.find_all("p"):
            strong = p.find("strong")
            strong_text = strong.get_text(strip=True).rstrip(':') if strong else None
            if strong and strong_text in (target_date_str_unpadded, target_date_str_padded, target_date_str_ordinal):
                found_heading = True
                logging.info(f"[WSOPExtractor] Found date heading: {strong_text}")

                # Extract any anchors in the heading paragraph itself
                _extract_anchors_from_tag(p)

                # Now walk subsequent siblings until the next date heading
                for sibling in p.find_next_siblings():
                    if sibling.name == 'p' and sibling.find('strong'):
                        # Reached next date heading; stop
                        break
                    # Skip ad/code blocks
                    if sibling.name == 'div':
                        div_classes = ' '.join(sibling.get('class', [])).lower()
                        if 'code-block' in div_classes or 'ad' in div_classes:
                            continue
                    if sibling.name == 'ol' or sibling.name == 'ul':
                        items = sibling.find_all('li')
                        logging.info(f"[WSOPExtractor] Found {len(items)} list items in {sibling.name} after heading {strong_text}")
                        for li in items:
                            _extract_anchors_from_tag(li)
                        # continue scanning after list
                        continue
                    if sibling.name == 'p':
                        _extract_anchors_from_tag(sibling)
                        continue
                    # For other tags, still try to extract anchors unless it's a known skip
                    _extract_anchors_from_tag(sibling)
                # Done extracting for this date heading - break
                break
        if not found_heading:
            logging.warning(f"[WSOPExtractor] No heading found for date: {target_date_str_unpadded}")
        total = len(url_map)
        logging.info(f"[WSOPExtractor] Total links extracted (deduped): {total}")
        return list(url_map.values())

   