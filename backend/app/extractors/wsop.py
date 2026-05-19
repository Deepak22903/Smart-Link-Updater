from typing import List
from collections import OrderedDict
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime, timedelta
import os
import logging

@register_extractor("wsop")
class WSOPExtractor(BaseExtractor):
    """Extractor for wsopga.me links grouped by date headings."""

    def can_handle(self, url: str) -> bool:
        url_lower = url.lower()
        return any(domain in url_lower for domain in ["wsopga.me", "freechipswsop.com", "wsopchipsfree.com"])

    def check_previous_days(self) -> int:
        """
        Number of historical days to include along with the target date.

        Controlled via env var `WSOP_PREVIOUS_DAYS` (fallback: `WSOP_LOOKBACK_DAYS`).
        Example: 3 means fetch target date + previous 3 days (4 days total).
        """
        raw_value = os.getenv("WSOP_PREVIOUS_DAYS", os.getenv("WSOP_LOOKBACK_DAYS", "1"))
        try:
            return max(0, min(int(raw_value), 30))
        except (TypeError, ValueError):
            logging.warning(
                f"[WSOPExtractor] Invalid WSOP_PREVIOUS_DAYS value '{raw_value}', defaulting to 1"
            )
            return 1

    def _generate_date_patterns(self, date_obj: datetime) -> List[str]:
        """Generate all possible date format variations for matching headings."""
        patterns = []
        day = date_obj.day
        month = date_obj.strftime('%B')
        year = date_obj.year
        
        # Generate ordinal suffix
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        patterns.extend([
            f"{day} {month} {year}",                     # "8 December 2025"
            f"{day:02d} {month} {year}",                 # "08 December 2025"
            f"{day}{suffix} {month} {year}",             # "8th December 2025"
            f"{day}{suffix} {month.lower()} {year}",     # "8th december 2025"
        ])
        
        return patterns

    def extract(self, html: str, date: str) -> List[Link]:
        soup = BeautifulSoup(html, 'html.parser')
        url_map = OrderedDict()

        # Parse the date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                logging.warning(f"[WSOPExtractor] Could not parse date: {date}")
                return []

        lookback_days = self.check_previous_days()

        # Build target dates: day 0 (target date), day 1 (yesterday), ... day N
        target_dates = [date_obj - timedelta(days=i) for i in range(0, lookback_days + 1)]
        date_configs = []
        for i, target_date_obj in enumerate(target_dates):
            target_iso = target_date_obj.strftime("%Y-%m-%d")
            patterns = self._generate_date_patterns(target_date_obj)
            date_configs.append({
                "offset": i,
                "iso": target_iso,
                "patterns": [p.lower() for p in patterns],
                "links": OrderedDict()
            })

        logging.info(
            f"[WSOPExtractor] Looking for target date + previous {lookback_days} day(s) "
            f"({target_dates[0].strftime('%Y-%m-%d')} back to {target_dates[-1].strftime('%Y-%m-%d')})"
        )
        
        def _match_heading_to_config(heading_text: str):
            heading_text_lower = heading_text.lower()
            for cfg in date_configs:
                if heading_text_lower in cfg["patterns"]:
                    return cfg
            return None

        def _extract_links_after_heading(heading_tag, heading_text: str, stop_on_tag_names):
            matched_config = _match_heading_to_config(heading_text)
            if not matched_config:
                return

            target_dict = matched_config["links"]
            target_date_iso = matched_config["iso"]
            day_label = f"DAY-{matched_config['offset']}"

            logging.info(f"[WSOPExtractor] Found {day_label} heading: {heading_text}")

            for sibling in heading_tag.find_next_siblings():
                if sibling.name in stop_on_tag_names:
                    break

                if sibling.name in ('ol', 'ul'):
                    for li in sibling.find_all('li'):
                        for a in li.find_all('a', href=True):
                            href = a.get('href', '')
                            if not href.startswith('http'):
                                continue
                            if 'wsopga.me' not in href:
                                continue

                            title = a.get_text(strip=True) or "Free Chips"
                            if href not in target_dict:
                                logging.info(f"[WSOPExtractor] Extracted: {href} | Title: {title}")
                                target_dict[href] = Link(
                                    title=title,
                                    url=href,
                                    date=target_date_iso,
                                    published_date_iso=target_date_iso
                                )

        # Find all <p><strong>DATE</strong></p> headings
        for p in soup.find_all("p"):
            strong = p.find("strong")
            if not strong:
                continue

            strong_text = strong.get_text(strip=True).rstrip(':')
            _extract_links_after_heading(
                heading_tag=p,
                heading_text=strong_text,
                stop_on_tag_names={'p', 'h3'}
            )

        # Find all <h3 class="wp-block-heading">DATE</h3> headings
        for h3 in soup.find_all("h3"):
            heading_text = h3.get_text(strip=True).rstrip(':')
            _extract_links_after_heading(
                heading_tag=h3,
                heading_text=heading_text,
                stop_on_tag_names={'p', 'h3'}
            )

        per_day_counts = [f"DAY-{cfg['offset']}={len(cfg['links'])}" for cfg in date_configs]
        logging.info(f"[WSOPExtractor] Found links by day: {', '.join(per_day_counts)}")

        # Combine links newest to oldest, deduped by URL
        for cfg in date_configs:
            for href, link in cfg["links"].items():
                if href not in url_map:
                    url_map[href] = link
        
        total = len(url_map)
        logging.info(f"[WSOPExtractor] Total links extracted (deduped): {total}")
        return list(url_map.values())
