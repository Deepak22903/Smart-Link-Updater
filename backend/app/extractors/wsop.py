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
        
        # Calculate yesterday's date (for late additions on source site)
        from datetime import timedelta
        yesterday_obj = date_obj - timedelta(days=1)
        
        # Generate date format variations for today
        today_patterns = []
        day = date_obj.day
        month = date_obj.strftime('%B')
        year = date_obj.year
        
        # Generate ordinal suffix
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        today_patterns.extend([
            date_obj.strftime("%d %B %Y").lstrip('0'),  # "8 December 2025"
            date_obj.strftime("%d %B %Y"),               # "08 December 2025"
            f"{day}{suffix} {month} {year}",             # "8th December 2025"
        ])
        
        # Generate date format variations for yesterday
        yesterday_patterns = []
        day_y = yesterday_obj.day
        month_y = yesterday_obj.strftime('%B')
        year_y = yesterday_obj.year
        
        if 10 <= day_y % 100 <= 20:
            suffix_y = 'th'
        else:
            suffix_y = {1: 'st', 2: 'nd', 3: 'rd'}.get(day_y % 10, 'th')
        
        yesterday_patterns.extend([
            yesterday_obj.strftime("%d %B %Y").lstrip('0'),  # "7 December 2025"
            yesterday_obj.strftime("%d %B %Y"),               # "07 December 2025"
            f"{day_y}{suffix_y} {month_y} {year_y}",         # "7th December 2025"
        ])
        
        # Use today's date for all links
        date_iso = date_obj.strftime("%Y-%m-%d")
        yesterday_iso = yesterday_obj.strftime("%Y-%m-%d")
        
        logging.info(f"[WSOPExtractor] Looking for links for TODAY ({date_obj.strftime('%d %B %Y')}) and YESTERDAY ({yesterday_obj.strftime('%d %B %Y')})")
        logging.info(f"[WSOPExtractor] All new links will be marked with today's date: {date_iso}")
        logging.debug(f"[WSOPExtractor] Today patterns: {today_patterns}")
        logging.debug(f"[WSOPExtractor] Yesterday patterns: {yesterday_patterns}")
        
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

        found_today_headings = []
        found_yesterday_headings = []
        today_links = OrderedDict()
        yesterday_links = OrderedDict()
        
        # Helper to extract anchors from a tag (p, li, div, etc.)
        def _extract_anchors_from_tag(tag, target_dict):
            for a in tag.find_all('a', href=True):
                href = a.get('href') or ''
                if not href.startswith('http'):
                    continue
                if 'www.wsopga.me/' in href:
                    title = a.get_text(strip=True) or href
                    if href not in target_dict:
                        # If the anchor text is just the href, treat as placeholder and log at debug level
                        if title == href:
                            logging.debug(f"[WSOPExtractor] Extracted placeholder link (no title): {href}")
                        else:
                            logging.info(f"[WSOPExtractor] Extracted link: {href} | Title: {title}")
                        target_dict[href] = Link(title=title, url=href, date=date, published_date_iso=date_iso)
                    else:
                        # Decide if we should update existing title
                        existing = target_dict[href]
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

        # Process all <p> tags to find today's and yesterday's sections
        for p in soup.find_all("p"):
            strong = p.find("strong")
            strong_text = strong.get_text(strip=True).rstrip(':') if strong else None
            
            # Check if this is today's heading
            if strong and strong_text in today_patterns:
                found_today_headings.append(strong_text)
                logging.info(f"[WSOPExtractor] Found TODAY's heading: {strong_text}")

                # Extract any anchors in the heading paragraph itself
                _extract_anchors_from_tag(p, today_links)

                # Walk subsequent siblings until the next date heading
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
                        logging.info(f"[WSOPExtractor] Found {len(items)} list items in {sibling.name} after TODAY's heading")
                        for li in items:
                            _extract_anchors_from_tag(li, today_links)
                        continue
                    if sibling.name == 'p':
                        _extract_anchors_from_tag(sibling, today_links)
                        continue
                    # For other tags, still try to extract anchors
                    _extract_anchors_from_tag(sibling, today_links)
            
            # Check if this is yesterday's heading
            elif strong and strong_text in yesterday_patterns:
                found_yesterday_headings.append(strong_text)
                logging.info(f"[WSOPExtractor] Found YESTERDAY's heading: {strong_text}")

                # Extract any anchors in the heading paragraph itself
                _extract_anchors_from_tag(p, yesterday_links)

                # Walk subsequent siblings until the next date heading
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
                        logging.info(f"[WSOPExtractor] Found {len(items)} list items in {sibling.name} after YESTERDAY's heading")
                        for li in items:
                            _extract_anchors_from_tag(li, yesterday_links)
                        continue
                    if sibling.name == 'p':
                        _extract_anchors_from_tag(sibling, yesterday_links)
                        continue
                    # For other tags, still try to extract anchors
                    _extract_anchors_from_tag(sibling, yesterday_links)
        
        logging.info(f"[WSOPExtractor] Found {len(today_links)} links under TODAY's section")
        logging.info(f"[WSOPExtractor] Found {len(yesterday_links)} links under YESTERDAY's section")
        
        # IMPORTANT: The deduplication against yesterday's already-processed links
        # happens at the fingerprint level in main.py, NOT here.
        # We just need to return today's links + yesterday's links (both marked with today's date).
        # The fingerprint system will automatically filter out links that were already
        # added yesterday because they'll have fingerprints like "url|||yesterday_iso".
        
        # Combine today's links with yesterday's links (yesterday's links get today's date)
        url_map = OrderedDict()
        
        # Add today's links first
        for href, link in today_links.items():
            url_map[href] = link
        
        # Add yesterday's links (these will be deduplicated by fingerprint system)
        for href, link in yesterday_links.items():
            if href not in url_map:  # Don't duplicate if same link appears in both sections
                url_map[href] = link
        
        if not found_today_headings and not found_yesterday_headings:
            logging.warning(f"[WSOPExtractor] No heading found for today or yesterday")
        else:
            logging.info(f"[WSOPExtractor] Found {len(found_today_headings)} TODAY heading(s): {found_today_headings}")
            logging.info(f"[WSOPExtractor] Found {len(found_yesterday_headings)} YESTERDAY heading(s): {found_yesterday_headings}")
        
        total = len(url_map)
        logging.info(f"[WSOPExtractor] Total links extracted (deduped): {total}")
        return list(url_map.values())

   