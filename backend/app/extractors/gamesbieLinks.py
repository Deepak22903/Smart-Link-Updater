"""
GamesbieLinks Extractor

Handles:
- Pages with "Animals & Coins Free Energy" sections
- Date format: "Today, 8th February" or "7th February"

Extraction Logic:
- Looks for <p> tags containing date patterns like "Today, 8th February"
- Extracts links from <ul class="wp-block-list"> following the date header
- Stops when encountering the next date header (previous day)
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
import re
from datetime import datetime


def register_extractor(name):
    """Local registration decorator - will be imported by __init__.py"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("gamesbieLinks")
class GamesbieLinksExtractor(BaseExtractor):
    """Extractor for Gamesbie-style pages with date-based paragraph headings."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from gamesbie domain or similar sites with this structure."""
        # Adjust the domain check based on the actual site
        return "gamesbie" in url.lower() or "gamesbielinks" in url.lower()
    
    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from Gamesbie HTML.
        
        Looks for date headers in formats:
        - <p><strong>Animals & Coins Free Energy: Today, 8th February</strong></p>
        - <p><strong>Animals & Coins Free Energy: 7th February</strong></p>
        
        Then extracts links from <ul class="wp-block-list"> following the heading.
        Stops when it encounters the previous day's date.
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Convert ISO date (2026-02-10) to display format
        try:
            dt = datetime.fromisoformat(date)
            
            # Format: "8th February" or "Today, 8th February"
            day_suffix = self._get_day_suffix(dt.day)
            date_pattern_1 = f"{dt.day}{day_suffix} {dt.strftime('%B')}"  # "8th February"
            date_pattern_2 = f"Today, {dt.day}{day_suffix} {dt.strftime('%B')}"  # "Today, 8th February"
            
        except ValueError:
            return links
        
        # Find all <p> tags that might contain date headers
        date_paragraphs = []
        for p in soup.find_all('p'):
            p_text = p.get_text(strip=True)
            # Look for patterns like "Animals & Coins Free Energy: Today, 8th February"
            if re.search(r':\s*(Today,\s*)?\d{1,2}(st|nd|rd|th)\s+\w+', p_text):
                date_paragraphs.append(p)
        
        # Find the start element for today's date
        start_element = None
        for p in date_paragraphs:
            p_text = p.get_text(strip=True)
            if date_pattern_1 in p_text or date_pattern_2 in p_text:
                start_element = p
                break
        
        # If today's date header is found, process the following <ul> elements
        if start_element:
            for sibling in start_element.find_next_siblings():
                # If we hit another date paragraph, stop
                if sibling in date_paragraphs:
                    break
                
                # Look for <ul class="wp-block-list"> elements
                if sibling.name == 'ul' and 'wp-block-list' in sibling.get('class', []):
                    # Extract all links from the list
                    for li in sibling.find_all('li'):
                        a = li.find('a')
                        if a:
                            href = a.get('href')
                            title = a.get_text(strip=True) or "Collect Energy"
                            
                            if href and href.startswith('http'):
                                links.append(Link(
                                    title=title,
                                    url=href,
                                    published_date_iso=date
                                ))
                
                # Also check if the sibling contains ul elements (nested structure)
                elif sibling.name != 'ul':
                    for ul in sibling.find_all('ul', class_='wp-block-list'):
                        for li in ul.find_all('li'):
                            a = li.find('a')
                            if a:
                                href = a.get('href')
                                title = a.get_text(strip=True) or "Collect Energy"
                                
                                if href and href.startswith('http'):
                                    links.append(Link(
                                        title=title,
                                        url=href,
                                        published_date_iso=date
                                    ))
        
        return links
    
    def _get_day_suffix(self, day: int) -> str:
        """Get the appropriate suffix for a day number (st, nd, rd, th)."""
        if 10 <= day % 100 <= 20:
            return 'th'
        else:
            suffix_map = {1: 'st', 2: 'nd', 3: 'rd'}
            return suffix_map.get(day % 10, 'th')
