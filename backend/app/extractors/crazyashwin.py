"""
CrazyAshwin.com Extractor

Handles link extraction from crazyashwin.com pages with specific patterns:
- "Today" sections with <h2> headers
- Date-based headings in various formats (DD.MM.YY, DD.MM.YYYY)
- Links with reward URLs (hititrich.com, cashfrenzy.co, etc.)
- Links in maxbutton format with onelink URLs
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime
import re


@register_extractor("crazyashwin")
class CrazyAshwinExtractor(BaseExtractor):
    """Extractor for crazyashwin.com pages with date-based and 'Today' sections."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is from crazyashwin.com."""
        return "crazyashwin.com" in url.lower()

    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from HTML content for a specific date.
        
        Looks for:
        1. <h2> with "Today" keyword
        2. <h3> with date patterns like "06.11.25" or "05.11.2025"
        3. Extracts all links between today's section and the next date section
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        # Parse the target date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return links

        # Create date format variations for matching
        # DD.MM.YY format: "06.11.25"
        date_short = date_obj.strftime("%d.%m.%y")
        # DD.MM.YYYY format: "06.11.2025"
        date_long = date_obj.strftime("%d.%m.%Y")
        # Alternative formats
        date_iso = date_obj.strftime("%Y-%m-%d")
        
        print(f"[CrazyAshwinExtractor] Looking for dates: {date_short}, {date_long}")

        # Strategy 1: Look for "Today" section first
        today_section = self._extract_from_today_section(soup, date_obj, date_iso)
        if today_section:
            links.extend(today_section)
            print(f"[CrazyAshwinExtractor] Found {len(today_section)} links in 'Today' section")

        # Strategy 2: Look for specific date headings (h3 with date patterns)
        date_section = self._extract_from_date_heading(soup, date_short, date_long, date_iso)
        if date_section:
            links.extend(date_section)
            print(f"[CrazyAshwinExtractor] Found {len(date_section)} links in date heading section")

        # Remove duplicates based on URL
        seen_urls = set()
        unique_links = []
        for link in links:
            if str(link.url) not in seen_urls:
                seen_urls.add(str(link.url))
                unique_links.append(link)

        print(f"[CrazyAshwinExtractor] Total unique links found: {len(unique_links)}")
        return unique_links

    def _extract_from_today_section(self, soup: BeautifulSoup, date_obj: datetime, date_iso: str) -> List[Link]:
        """
        Extract links from sections with 'Today' in the heading.
        Looks for <h2> tags containing 'Today' keyword.
        """
        links = []
        
        # Find all h2 tags that contain "Today"
        for h2 in soup.find_all('h2'):
            if 'today' in h2.get_text().lower():
                print(f"[CrazyAshwinExtractor] Found 'Today' section: {h2.get_text()[:50]}")
                
                # Extract links from subsequent elements until we hit another h2/h3 date marker
                for sibling in h2.find_next_siblings():
                    # Stop at next major heading or date marker
                    if sibling.name in ['h2', 'h3']:
                        # Check if this is a date heading (stop boundary)
                        if self._is_date_heading(sibling.get_text()):
                            break
                    
                    # Extract all links from this element
                    a_tags = sibling.find_all('a', href=True)
                    for a_tag in a_tags:
                        href = a_tag.get('href', '')
                        
                        # Filter out non-reward links
                        if self._is_valid_reward_link(href):
                            title = self._extract_title(a_tag)
                            links.append(Link(
                                title=title,
                                url=href,
                                published_date_iso=date_iso
                            ))
        
        return links

    def _extract_from_date_heading(self, soup: BeautifulSoup, date_short: str, date_long: str, date_iso: str) -> List[Link]:
        """
        Extract links from sections with specific date headings.
        Looks for <h3> tags with date patterns like "06.11.25" or "↟ 06.11.25 ↟".
        """
        links = []
        
        # Date patterns to match in headings
        date_patterns = [
            date_short,      # "06.11.25"
            date_long,       # "06.11.2025"
        ]
        
        # Find all h3 tags
        for h3 in soup.find_all('h3'):
            h3_text = h3.get_text()
            
            # Check if this h3 contains our target date
            if any(pattern in h3_text for pattern in date_patterns):
                print(f"[CrazyAshwinExtractor] Found date heading: {h3_text[:80]}")
                
                # Look backwards from this h3 to collect links until we hit previous date heading
                links_before_h3 = self._extract_links_before_heading(h3, date_iso)
                links.extend(links_before_h3)
        
        return links

    def _extract_links_before_heading(self, heading: BeautifulSoup, date_iso: str) -> List[Link]:
        """
        Extract links that appear BEFORE a date heading (going backwards).
        Stops when hitting another h3 date heading.
        """
        links = []
        
        # Go backwards through previous siblings
        for sibling in heading.find_previous_siblings():
            # Stop at previous h3 date heading
            if sibling.name == 'h3' and self._is_date_heading(sibling.get_text()):
                break
            
            # Stop at h2 (new major section)
            if sibling.name == 'h2':
                break
            
            # Extract links from this element
            a_tags = sibling.find_all('a', href=True)
            for a_tag in a_tags:
                href = a_tag.get('href', '')
                
                if self._is_valid_reward_link(href):
                    title = self._extract_title(a_tag)
                    links.append(Link(
                        title=title,
                        url=href,
                        published_date_iso=date_iso
                    ))
        
        return links

    def _is_date_heading(self, text: str) -> bool:
        """Check if text looks like a date heading."""
        # Pattern for DD.MM.YY or DD.MM.YYYY
        date_pattern = re.compile(r'\d{1,2}\.\d{1,2}\.(\d{2}|\d{4})')
        return bool(date_pattern.search(text))

    def _is_valid_reward_link(self, url: str) -> bool:
        """
        Check if URL is a valid reward link (not ads, social media, etc.).
        """
        url_lower = url.lower()
        
        # Exclude known non-reward URLs
        exclude_patterns = [
            'telegram.me',
            'bit.ly',  # Often just promo links, not actual rewards
            'googlesyndication.com',
            'adsbygoogle',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'youtube.com',
        ]
        
        if any(pattern in url_lower for pattern in exclude_patterns):
            return False
        
        # Include known reward domains
        reward_patterns = [
            'hititrich.com',
            'cashfrenzy.co',
            'grandharvest.onelink.me',
            'coinmaster.com',
            '.onelink.me',  # Generic onelink domains
        ]
        
        # Accept if it's a known reward domain
        if any(pattern in url_lower for pattern in reward_patterns):
            return True
        
        # Accept if it has reward-like query parameters
        if any(param in url_lower for param in ['rewardkey', 'reward', 'gift', 'bonus']):
            return True
        
        return False

    def _extract_title(self, a_tag: BeautifulSoup) -> str:
        """
        Extract a clean title from an anchor tag.
        Handles both regular text and maxbutton spans.
        """
        # Try to get text from mb-text span (maxbutton format)
        mb_text = a_tag.find('span', class_='mb-text')
        if mb_text:
            return mb_text.get_text(strip=True)
        
        # Otherwise get regular text
        title = a_tag.get_text(strip=True)
        
        # Fallback to a generic title
        if not title:
            title = "Reward Link"
        
        return title

    @property
    def name(self) -> str:
        return "CrazyAshwin Extractor"

    @property
    def description(self) -> str:
        return "Extracts reward links from crazyashwin.com with 'Today' and date-based sections"
