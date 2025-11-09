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
        Extracts all links from today's date section until yesterday's date heading is encountered.
        """
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
        
        if not date_obj:
            print(f"[MostTechsExtractor] Could not parse date: {date}")
            return links
        
        # Calculate yesterday's date
        yesterday_obj = date_obj - timedelta(days=1)
        
        # Format variations for today: "9 Nov 2025", "9 November 2025", "09 Nov 2025", "09 November 2025"
        today_short = date_obj.strftime("%d %b %Y").lstrip('0')     # "9 Nov 2025"
        today_long = date_obj.strftime("%d %B %Y").lstrip('0')      # "9 November 2025"
        today_short_padded = date_obj.strftime("%d %b %Y")          # "09 Nov 2025"
        today_long_padded = date_obj.strftime("%d %B %Y")           # "09 November 2025"
        
        # Format variations for yesterday: "8 Nov 2025", "8 November 2025", etc.
        yesterday_short = yesterday_obj.strftime("%d %b %Y").lstrip('0')
        yesterday_long = yesterday_obj.strftime("%d %B %Y").lstrip('0')
        yesterday_short_padded = yesterday_obj.strftime("%d %b %Y")
        yesterday_long_padded = yesterday_obj.strftime("%d %B %Y")
        
        date_iso = date_obj.isoformat()

        # Find the <p> tag containing today's date
        date_heading_p = None
        for p_tag in soup.find_all("p"):
            p_text = p_tag.get_text(strip=True)
            if (today_short in p_text or today_long in p_text or 
                today_short_padded in p_text or today_long_padded in p_text):
                date_heading_p = p_tag
                print(f"[MostTechsExtractor] Found today's date heading: {p_text}")
                break

        if not date_heading_p:
            print(f"[MostTechsExtractor] No heading found for date: '{today_short}' or '{today_long}'")
            return links

        # Extract links from following siblings until we hit yesterday's date heading
        date_pattern = re.compile(
            r"\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|"
            r"Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s+\d{4}", 
            re.IGNORECASE
        )
        
        link_count = 0
        for sibling in date_heading_p.find_next_siblings():
            # Skip non-paragraph elements and divs (like ad blocks)
            if sibling.name not in ["p", "div"]:
                continue
            
            # Check if this sibling contains yesterday's date (stop boundary)
            sibling_text = sibling.get_text(strip=True)
            if (yesterday_short in sibling_text or yesterday_long in sibling_text or
                yesterday_short_padded in sibling_text or yesterday_long_padded in sibling_text):
                print(f"[MostTechsExtractor] Encountered yesterday's date boundary: {sibling_text}")
                break
            
            # Skip if it's another future date heading (shouldn't happen but good safeguard)
            if date_pattern.search(sibling_text):
                matched_date = date_pattern.search(sibling_text).group()
                # Parse the matched date to check if it's before yesterday
                try:
                    matched_obj = datetime.strptime(matched_date, "%d %b %Y")
                except ValueError:
                    try:
                        matched_obj = datetime.strptime(matched_date, "%d %B %Y")
                    except ValueError:
                        matched_obj = None
                
                if matched_obj and matched_obj < yesterday_obj:
                    print(f"[MostTechsExtractor] Encountered older date boundary: {matched_date}")
                    break
            
            # Extract link from this paragraph or div
            a_tag = sibling.find("a")
            if a_tag and a_tag.get("href") and a_tag.get("href").startswith("http"):
                link_count += 1
                link_title = a_tag.get_text(strip=True) or f"Link {link_count}"
                links.append(Link(
                    title=link_title,
                    url=a_tag.get("href"),
                    date=date,
                    published_date_iso=date_iso
                ))
                print(f"[MostTechsExtractor] Extracted link {link_count}: {link_title}")
        
        print(f"[MostTechsExtractor] Total links extracted: {len(links)}")
        return links