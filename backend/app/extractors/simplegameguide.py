"""
SimpleGameGuide.com Extractor

Handles:
- simplegameguide.com/coin-master-free-spins-links/
- simplegameguide.com/carnival-tycoon-free-spins/
- Similar SimpleGameGuide pages

Extraction Logic:
- Looks for h4 headings containing today's date
- Extracts links from the section following the heading
- Filters out non-button elements
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


@register_extractor("simplegameguide")
class SimpleGameGuideExtractor(BaseExtractor):
    """Extractor for SimpleGameGuide.com pages with date-based h4 headings."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from simplegameguide.com."""
        return "simplegameguide.com" in url.lower()
    
    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from SimpleGameGuide HTML.
        
        Looks for date headers in formats:
        - <h4>26 October 2025</h4>
        - <div><strong>Oct 26, 2025:</strong></div>
        
        Then extracts links from the section following the heading.
        Stops when it encounters the previous day's date.
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Convert ISO date (2025-11-04) to various display formats
        try:
            dt = datetime.fromisoformat(date)
            
            # Format 1: "4 November 2025" (full month name, no leading zero)
            format1 = f"{dt.day} {dt.strftime('%B %Y')}"
            
            # Format 2: "Nov 4, 2025:" (abbreviated month, no leading zero)
            format2 = f"{dt.strftime('%b')} {dt.day}, {dt.strftime('%Y')}:"

        except ValueError:
            return links
        
        # Find all potential date headers (h4 or div/strong combinations)
        date_elements = []
        
        # Pattern 1: <h4>Date</h4>
        for h4 in soup.find_all('h4'):
            date_elements.append(h4)
        
        # Pattern 2: <div><strong>Date:</strong></div>
        # Only collect divs where strong tag is the primary/only content
        for div in soup.find_all('div'):
            strong = div.find('strong')
            if strong:
                # Check if the div's text is mostly just the strong tag's text
                div_text = div.get_text(strip=True)
                strong_text = strong.get_text(strip=True)
                # Only add if strong tag contains most of the div's content
                if strong_text and len(strong_text) > len(div_text) * 0.7:
                    date_elements.append(div)
        
        # Find the start element for today's date
        start_element = None
        for elem in date_elements:
            elem_text = elem.get_text(strip=True)
            if format1 in elem_text or format2 in elem_text:
                start_element = elem
                break

        # If today's date header is found, process all subsequent siblings
        # until the next date header is encountered.
        if start_element:
            for sibling in start_element.find_next_siblings():
                # If the sibling is another date header, stop processing.
                if sibling in date_elements:
                    break

                # Find links within the current sibling element
                
                # Pattern A: Links with class containing "button"
                for a in sibling.find_all('a', class_=lambda c: c and 'button' in c.lower()):
                    href = a.get('href')
                    title = a.get_text(strip=True) or "Link"
                    
                    if href and href.startswith('http'):
                        links.append(Link(
                            title=title,
                            url=href,
                            published_date_iso=date
                        ))
                
                # Pattern B: Divs with data-link attribute (Coin Master style)
                for div in sibling.find_all('div', {'data-link': True}):
                    href = div.get('data-link')
                    span = div.find('span')
                    title = span.get_text(strip=True) if span else "Link"
                    
                    if href and href.startswith('http'):
                        links.append(Link(
                            title=title,
                            url=href,
                            published_date_iso=date
                        ))
        
        return links
