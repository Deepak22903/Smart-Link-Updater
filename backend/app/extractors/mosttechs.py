from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime, timedelta
import re

@register_extractor("mosttechs")
class MostTechsExtractor(BaseExtractor):
    """Extractor for mosttechs.com pages with date-based headings."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is from mosttechs.com."""
        return "mosttechs.com" in url.lower()

    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from HTML content for a specific date.
        Links are in format: <p>1.<a href="...">4x free credits 25.11.2025</a></p>
        Date is embedded in the link text as DD.MM.YYYY format.
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        # Parse the target date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                print(f"[MostTechsExtractor] Could not parse date: {date}")
                return links
        
        date_iso = date_obj.isoformat()
        
        # Format target date as DD.MM.YYYY (e.g., "25.11.2025")
        target_date_str = date_obj.strftime("%d.%m.%Y")
        
        print(f"[MostTechsExtractor] Looking for links with date: {target_date_str}")
        
        # Pattern to match dates in DD.MM.YYYY format within link text
        date_in_text_pattern = re.compile(r'(\d{1,2})\.(\d{1,2})\.(\d{4})')
        
        link_count = 0
        
        # Find all <p> tags that contain links
        for p_tag in soup.find_all("p"):
            a_tag = p_tag.find("a")
            if not a_tag:
                continue
            
            href = a_tag.get("href", "")
            if not href.startswith("http"):
                continue
            
            # Get the link text
            link_text = a_tag.get_text(strip=True)
            
            # Check if the link text contains a date in DD.MM.YYYY format
            date_match = date_in_text_pattern.search(link_text)
            if not date_match:
                continue
            
            # Parse the date from the link text
            day, month, year = date_match.groups()
            try:
                link_date_obj = datetime(int(year), int(month), int(day))
            except ValueError:
                continue
            
            # Check if this link's date matches our target date
            if link_date_obj.date() == date_obj.date():
                link_count += 1
                
                # Clean up the title (remove number prefix if present)
                clean_title = re.sub(r'^\d+\.\s*', '', link_text)
                
                links.append(Link(
                    title=clean_title,
                    url=href,
                    date=date,
                    published_date_iso=date_iso
                ))
                print(f"[MostTechsExtractor] Extracted link {link_count}: {clean_title} ({href})")
        
        print(f"[MostTechsExtractor] Total links extracted for {target_date_str}: {len(links)}")
        return links