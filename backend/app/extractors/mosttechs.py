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

        # Accept both '31 Oct 2025' and '31 October 2025' formats
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                date_obj = None
        if date_obj:
            date_short = date_obj.strftime("%d %b %Y")
            date_long = date_obj.strftime("%d %B %Y")
        else:
            date_short = date
            date_long = date

        def is_date_heading(tag):
            if tag.name != "span":
                return False
            text = tag.get_text(strip=True)
            return (date_short in text) or (date_long in text)

        date_heading = soup.find(is_date_heading)
        if not date_heading:
            print(f"[MostTechsExtractor] No heading found for date: '{date_short}' or '{date_long}'")
            return links

        try:
            date_iso = date_obj.isoformat()
        except Exception:
            date_iso = None

        # Find the parent <p> of the heading, then iterate over next siblings
        parent_p = date_heading.find_parent("p")
        if not parent_p:
            return links
        for sibling in parent_p.find_next_siblings():
            # Stop at the next <p> containing a <span> with any date
            if sibling.name == "p":
                span = sibling.find("span")
                if span:
                    span_text = span.get_text(strip=True)
                    # If the span contains a date (any day/month/year), stop
                    import re
                    if re.search(r"\d{1,2} (?:Oct|October|Nov|November|Sep|September|Aug|August|Jul|July|Jun|June|May|Apr|April|Mar|March|Feb|February|Jan|January) \d{4}", span_text):
                        break
                a_tag = sibling.find("a")
                if a_tag and a_tag.get("href") and a_tag.get("href").startswith("http"):
                    links.append(Link(
                        title=a_tag.get_text(strip=True),
                        url=a_tag.get("href"),
                        date=date,
                        published_date_iso=date_iso
                    ))
        return links