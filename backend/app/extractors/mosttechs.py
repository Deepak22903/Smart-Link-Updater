from typing import List
from collections import OrderedDict
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime, timedelta
import re
import logging

@register_extractor("mosttechs")
class MostTechsExtractor(BaseExtractor):
    """
    Extractor for mosttechs.com pages with date-based headings.
    
    Supports TWO HTML patterns:
    1. OLD: Date embedded in link text - <p>1.<a href="...">4x free credits 25.11.2025</a></p>
    2. NEW: Date as heading above links - <p><span><strong>30 December 2025</strong></span></p>
    """

    def can_handle(self, url: str) -> bool:
        """Check if URL is from mosttechs.com."""
        return "mosttechs.com" in url.lower()

    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from HTML content for today AND yesterday.
        Automatically detects and handles both old and new HTML patterns.
        
        Like WSOP, this extractor searches for both today's and yesterday's date headings
        to prevent missing late additions and avoid duplicates through fingerprinting.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Parse the target date (today)
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                logging.warning(f"[MostTechsExtractor] Could not parse date: {date}")
                return []
        
        # Calculate yesterday's date
        yesterday_obj = date_obj - timedelta(days=1)
        
        date_iso = date_obj.strftime("%Y-%m-%d")
        yesterday_iso = yesterday_obj.strftime("%Y-%m-%d")
        
        logging.info(f"[MostTechsExtractor] Looking for TODAY ({date_obj.strftime('%d %B %Y')}) and YESTERDAY ({yesterday_obj.strftime('%d %B %Y')})")
        logging.info(f"[MostTechsExtractor] Today's links will be marked with: {date_iso}")
        logging.info(f"[MostTechsExtractor] Yesterday's links will be marked with: {yesterday_iso}")
        
        # Try NEW pattern first (date headings)
        today_links = self._extract_with_date_headings(soup, date_obj, date, date_iso)
        yesterday_links = self._extract_with_date_headings(soup, yesterday_obj, date, yesterday_iso)
        
        # If no links found with NEW pattern, try OLD pattern
        if not today_links and not yesterday_links:
            logging.info(f"[MostTechsExtractor] No links found with date headings, trying old pattern (date in text)")
            today_links = self._extract_with_date_in_text(soup, date_obj, date, date_iso)
            yesterday_links = self._extract_with_date_in_text(soup, yesterday_obj, date, yesterday_iso)
        
        # Combine links from both days (deduplicate by URL)
        all_links = OrderedDict()
        
        # Add today's links first
        for link in today_links:
            all_links[link.url] = link
        
        # Add yesterday's links (skip if URL already exists from today)
        for link in yesterday_links:
            if link.url not in all_links:
                all_links[link.url] = link
        
        logging.info(f"[MostTechsExtractor] Total links: {len(today_links)} today + {len(yesterday_links)} yesterday = {len(all_links)} unique")
        return list(all_links.values())

    def _extract_with_date_headings(self, soup: BeautifulSoup, date_obj: datetime, date: str, date_iso: str) -> List[Link]:
        """
        NEW PATTERN: Extract links grouped under date headings.
        Format: <p><span><strong>30 December 2025</strong></span></p>
        """
        links = OrderedDict()
        
        # Generate date format variations
        date_patterns = self._generate_date_patterns(date_obj)
        
        logging.info(f"[MostTechsExtractor] Looking for date headings: {date_patterns[:3]}...")
        
        # Find all <p> tags to locate date headings
        for p_tag in soup.find_all("p"):
            # Check if this <p> contains a date heading (via span/strong or direct text)
            heading_text = self._extract_heading_text(p_tag)
            
            if not heading_text:
                continue
            
            # Normalize heading text to fix common typos
            normalized_heading = self._normalize_date_text(heading_text)
            
            if normalized_heading not in date_patterns:
                continue
            
            logging.info(f"[MostTechsExtractor] Found date heading: '{heading_text}'")
            
            # Extract links from siblings following this heading
            self._extract_links_after_heading(p_tag, links, date, date_iso)
        
        return list(links.values())

    def _extract_with_date_in_text(self, soup: BeautifulSoup, date_obj: datetime, date: str, date_iso: str) -> List[Link]:
        """
        OLD PATTERN: Extract links with dates embedded in link text.
        Format: <p>1.<a href="...">4x free credits 25.11.2025</a></p>
        """
        links = []
        target_date_str = date_obj.strftime("%d.%m.%Y")
        date_in_text_pattern = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})')
        
        logging.info(f"[MostTechsExtractor] Looking for date in link text: {target_date_str}")
        
        for p_tag in soup.find_all("p"):
            a_tag = p_tag.find("a")
            if not a_tag:
                continue
            
            href = a_tag.get("href", "")
            if not href.startswith("http"):
                continue
            
            link_text = a_tag.get_text(strip=True)
            date_match = date_in_text_pattern.search(link_text)
            
            if not date_match:
                continue
            
            # Parse date from link text
            day, month, year = date_match.groups()
            try:
                link_date_obj = datetime(int(year), int(month), int(day))
            except ValueError:
                continue
            
            # Check if dates match
            if link_date_obj.date() == date_obj.date():
                clean_title = re.sub(r'^\d+\.\s*', '', link_text)
                links.append(Link(
                    title=clean_title,
                    url=href,
                    date=date,
                    published_date_iso=date_iso
                ))
                logging.info(f"[MostTechsExtractor] Extracted link (old pattern): {clean_title}")
        
        return links

    def _normalize_date_text(self, text: str) -> str:
        """
        Normalize date text by fixing common typos in month names.
        Handles case-insensitive replacements.
        """
        # Common month name typos (case-insensitive)
        typo_map = {
            r'\bjanuray\b': 'January',
            r'\bfebuary\b': 'February',
            r'\bfeburary\b': 'February',
            r'\bmarch\b': 'March',
            r'\bapril\b': 'April',
            r'\bmay\b': 'May',
            r'\bjune\b': 'June',
            r'\bjuly\b': 'July',
            r'\baugust\b': 'August',
            r'\bseptember\b': 'September',
            r'\boctober\b': 'October',
            r'\bnovember\b': 'November',
            r'\bdecember\b': 'December',
        }
        
        normalized = text
        for typo_pattern, correct in typo_map.items():
            normalized = re.sub(typo_pattern, correct, normalized, flags=re.IGNORECASE)
        
        return normalized
    
    def _generate_date_patterns(self, date_obj: datetime) -> List[str]:
        """Generate all possible date format variations."""
        day = date_obj.day
        month = date_obj.strftime('%B')  # Full month name (December)
        month_short = date_obj.strftime('%b')  # Short month name (Dec)
        year = date_obj.year
        
        return [
            f"{day} {month} {year}",              # "30 December 2025"
            f"{day:02d} {month} {year}",          # "30 December 2025" (with leading zero)
            f"{day} {month_short} {year}",        # "30 Dec 2025"
            f"{day:02d} {month_short} {year}",    # "30 Dec 2025" (with leading zero)
            f"{month} {day}, {year}",             # "December 30, 2025"
            f"{month_short} {day}, {year}",       # "Dec 30, 2025"
        ]

    def _extract_heading_text(self, p_tag) -> str:
        """
        Extract text from potential date heading, handling multiple formats:
        - <p><span><strong>30 December 2025</strong></span></p>
        - <p><strong>30 December 2025</strong></p>
        - <p>30 December 2025</p>
        """
        # Try span > strong
        span = p_tag.find("span")
        if span:
            strong = span.find("strong")
            if strong:
                return strong.get_text(strip=True)
        
        # Try direct strong
        strong = p_tag.find("strong")
        if strong:
            return strong.get_text(strip=True)
        
        # Try direct text (only if no links present)
        if not p_tag.find("a"):
            text = p_tag.get_text(strip=True)
            # Basic validation: should look like a date (contains month name or numbers)
            if re.search(r'\d{4}', text):  # Contains year
                return text
        
        return None

    def _extract_links_after_heading(self, heading_tag, links_dict: OrderedDict, date: str, date_iso: str):
        """
        Extract all links from siblings following the date heading.
        Stops when encountering the next date heading or end of content.
        """
        for sibling in heading_tag.find_next_siblings():
            # Stop at next date heading
            if sibling.name == "p" and self._extract_heading_text(sibling):
                break
            
            # Skip ad blocks and code blocks
            if sibling.name == "div":
                div_classes = ' '.join(sibling.get('class', [])).lower()
                if 'code-block' in div_classes or 'ad' in div_classes:
                    continue
            
            # Extract links from this sibling
            self._extract_links_from_tag(sibling, links_dict, date, date_iso)

    def _extract_links_from_tag(self, tag, links_dict: OrderedDict, date: str, date_iso: str):
        """
        Extract links from a single tag (p, li, div, etc.).
        Handles numbered prefixes (e.g., "5.Free dice link").
        """
        for a_tag in tag.find_all("a", href=True):
            href = a_tag.get("href", "")
            
            if not href.startswith("http"):
                continue
            
            # Get link text and clean it
            raw_text = a_tag.get_text(strip=True)
            
            # Remove number prefix (e.g., "5." or "4.")
            clean_title = re.sub(r'^\d+\.\s*', '', raw_text)
            
            # Skip if title is empty after cleaning
            if not clean_title:
                clean_title = href
            
            # Deduplicate by URL
            if href not in links_dict:
                links_dict[href] = Link(
                    title=clean_title,
                    url=href,
                    date=date,
                    published_date_iso=date_iso
                )
                logging.info(f"[MostTechsExtractor] Extracted link: {clean_title} ({href})")