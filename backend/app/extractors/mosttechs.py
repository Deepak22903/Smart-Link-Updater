from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime

@register_extractor("mosttechs")
class MostTechsExtractor(BaseExtractor):
    """Extractor for mosttechs.com pages with date-based headings."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is from mosttechs.com."""
        return "mosttechs.com" in url.lower()

    def extract(self, html: str, date: str) -> List[Link]:
        """Extract links from HTML content for a specific date."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        # Parse the date and create multiple format variations
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                date_obj = None
        
        if date_obj:
            # Format variations: "4 Nov 2025", "4 November 2025", "04 Nov 2025", "04 November 2025"
            date_short = date_obj.strftime("%d %b %Y").lstrip('0')  # "4 Nov 2025"
            date_long = date_obj.strftime("%d %B %Y").lstrip('0')   # "4 November 2025"
            date_iso = date_obj.isoformat()
        else:
            date_short = date
            date_long = date
            date_iso = date

        # Find all <p> tags and check if they contain the target date
        date_heading_p = None
        for p_tag in soup.find_all("p"):
            p_text = p_tag.get_text(strip=True)
            if date_short in p_text or date_long in p_text:
                date_heading_p = p_tag
                break

        if not date_heading_p:
            print(f"[MostTechsExtractor] No heading found for date: '{date_short}' or '{date_long}'")
            return links

        # Extract links from following <p> siblings until we hit another date heading
        import re
        date_pattern = re.compile(r"\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s+\d{4}", re.IGNORECASE)
        
        for sibling in date_heading_p.find_next_siblings():
            if sibling.name != "p":
                continue
            
            # Check if this sibling contains another date heading (stop boundary)
            sibling_text = sibling.get_text(strip=True)
            if date_pattern.search(sibling_text):
                # This is another date heading, stop here
                break
            
            # Extract link from this paragraph
            a_tag = sibling.find("a")
            if a_tag and a_tag.get("href") and a_tag.get("href").startswith("http"):
                links.append(Link(
                    title=a_tag.get_text(strip=True) or "Link",
                    url=a_tag.get("href"),
                    date=date,
                    published_date_iso=date_iso
                ))
        
        return links