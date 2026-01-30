from typing import List
from collections import OrderedDict
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime, timedelta
import logging

@register_extractor("wsop")
class WSOPExtractor(BaseExtractor):
    """Extractor for wsopga.me links grouped by date headings."""

    def can_handle(self, url: str) -> bool:
        url_lower = url.lower()
        return any(domain in url_lower for domain in ["wsopga.me", "freechipswsop.com", "wsopchipsfree.com"])
    
    # Note: Using default check_previous_days() which returns 1 (today + yesterday)

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
        
        # Calculate yesterday's date
        yesterday_obj = date_obj - timedelta(days=1)
        
        # Generate date patterns
        today_patterns = self._generate_date_patterns(date_obj)
        yesterday_patterns = self._generate_date_patterns(yesterday_obj)
        
        date_iso = date_obj.strftime("%Y-%m-%d")
        yesterday_iso = yesterday_obj.strftime("%Y-%m-%d")
        
        logging.info(f"[WSOPExtractor] Looking for TODAY ({date_iso}) and YESTERDAY ({yesterday_iso})")
        logging.debug(f"[WSOPExtractor] Today patterns: {today_patterns}")
        logging.debug(f"[WSOPExtractor] Yesterday patterns: {yesterday_patterns}")

        today_links = OrderedDict()
        yesterday_links = OrderedDict()
        
        # Find all <p><strong>DATE</strong></p> headings
        for p in soup.find_all("p"):
            strong = p.find("strong")
            if not strong:
                continue
            
            strong_text = strong.get_text(strip=True).rstrip(':')
            
            # Determine if this is today's or yesterday's heading
            is_today = any(pattern.lower() == strong_text.lower() for pattern in today_patterns)
            is_yesterday = any(pattern.lower() == strong_text.lower() for pattern in yesterday_patterns)
            
            if not is_today and not is_yesterday:
                continue
            
            target_dict = today_links if is_today else yesterday_links
            target_date_iso = date_iso if is_today else yesterday_iso
            day_label = "TODAY" if is_today else "YESTERDAY"
            
            logging.info(f"[WSOPExtractor] Found {day_label}'s heading: {strong_text}")
            
            # Walk subsequent siblings to find <ol> or <ul> lists
            for sibling in p.find_next_siblings():
                # Stop at next <p><strong> (next date heading)
                if sibling.name == 'p' and sibling.find('strong'):
                    break
                
                # Process ordered/unordered lists
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
        
        logging.info(f"[WSOPExtractor] Found {len(today_links)} TODAY links, {len(yesterday_links)} YESTERDAY links")
        
        # Combine: today's links first, then yesterday's (without duplicates)
        for href, link in today_links.items():
            url_map[href] = link
        for href, link in yesterday_links.items():
            if href not in url_map:
                url_map[href] = link
        
        total = len(url_map)
        logging.info(f"[WSOPExtractor] Total links extracted (deduped): {total}")
        return list(url_map.values())
