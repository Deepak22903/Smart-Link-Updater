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
        
        # Convert ISO date (2025-10-26) to various display formats
        try:
            dt = datetime.fromisoformat(date)
            
            # Format 1: "26 October 2025" (full month name)
            format1 = dt.strftime("%d %B %Y").lstrip('0')
            
            # Format 2: "Oct 26, 2025:" (abbreviated month with colon)
            format2 = dt.strftime("%b %d, %Y:").lstrip('0')
            
            # Calculate yesterday for boundary detection
            from datetime import timedelta
            yesterday = dt - timedelta(days=1)
            yesterday_format1 = yesterday.strftime("%d %B %Y").lstrip('0')
            yesterday_format2 = yesterday.strftime("%b %d, %Y:").lstrip('0')
            
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
        
        # Process each date element
        for elem in date_elements:
            elem_text = elem.get_text(strip=True)
            
            # Check if this is yesterday's date (stop boundary)
            if yesterday_format1 in elem_text or yesterday_format2 in elem_text:
                break
            
            # Check if this element contains today's date
            if format1 in elem_text or format2 in elem_text:
                # Find the next sibling element (contains links)
                next_elem = elem.find_next_sibling()
                
                if next_elem:
                    # Pattern A: Links with class containing "button"
                    for a in next_elem.find_all('a', class_=lambda c: c and 'button' in c.lower()):
                        href = a.get('href')
                        title = a.get_text(strip=True) or "Link"
                        
                        if href and href.startswith('http'):
                            links.append(Link(
                                title=title,
                                url=href,
                                published_date_iso=date
                            ))
                    
                    # Pattern B: Divs with data-link attribute (Coin Master style)
                    for div in next_elem.find_all('div', {'data-link': True}):
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
