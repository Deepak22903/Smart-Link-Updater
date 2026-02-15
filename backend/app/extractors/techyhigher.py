"""
TechyHigher.com Extractor

Handles link extraction from techyhigher.com pages with specific patterns:
- "Today" sections with date in format like "Today Coin Master Free Spins & Coins 6 Nov 2025"
- Date-based headings like "5 november 2025" or "Coin Master Free Spins & Coins 5 Nov 2025"
- Numbered links (1., 2., 3., etc.)
- Reward URLs from various domains (rewards.coinmaster.com, d10xl.com, travel-town-app.com, etc.)
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime
import re


@register_extractor("techyhigher")
class TechyHigherExtractor(BaseExtractor):
    """Extractor for techyhigher.com pages with date-based sections."""

    def can_handle(self, url: str) -> bool:
        """Check if URL is from techyhigher.com."""
        return "techyhigher.com" in url.lower()

    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from HTML content for a specific date.
        
        Looks for:
        1. <p> tags with "Today" + date (e.g., "Today Coin Master Free Spins & Coins 6 Nov 2025")
        2. <p> tags with just date (e.g., "5 november 2025")
        3. Extracts numbered links following the date heading until next date section
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        # Parse the target date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return links

        # Create multiple date format variations for matching (today and yesterday only)
        date_formats_today = self._generate_date_formats(date_obj)
        
        # Calculate yesterday's date
        from datetime import timedelta
        yesterday_obj = date_obj - timedelta(days=1)
        date_formats_yesterday = self._generate_date_formats(yesterday_obj)
        
        # Combine today and yesterday formats
        date_formats = date_formats_today + date_formats_yesterday
        date_iso = date_obj.strftime("%Y-%m-%d")
        
        print(f"[TechyHigherExtractor] Looking for date patterns (today/yesterday): {', '.join(date_formats_today[:2])} and {', '.join(date_formats_yesterday[:2])}...")

        # Strategy 1: DISABLED - Don't use "Today" sections as they extract all links regardless of date
        # today_links = self._extract_from_today_section(soup, date_formats, date_iso)
        # if today_links:
        #     links.extend(today_links)
        #     print(f"[TechyHigherExtractor] Found {len(today_links)} links in 'Today' section")

        # Strategy 2: DISABLED - Don't use standalone date headings as they extract all links regardless of date
        # date_links = self._extract_from_date_heading(soup, date_formats, date_iso)
        # if date_links:
        #     links.extend(date_links)
        #     print(f"[TechyHigherExtractor] Found {len(date_links)} links in date heading section")

        # Strategy 3: Look for inline date patterns in anchor tags (e.g., "energy gifts links 15.2.2026")
        # This is the ONLY strategy used now - it validates the date in the link text itself
        inline_links = self._extract_from_inline_dates(soup, date_formats, date_iso)
        if inline_links:
            links.extend(inline_links)
            print(f"[TechyHigherExtractor] Found {len(inline_links)} links with inline date patterns")

        # Remove duplicates based on URL
        seen_urls = set()
        unique_links = []
        for link in links:
            if str(link.url) not in seen_urls:
                seen_urls.add(str(link.url))
                unique_links.append(link)

        print(f"[TechyHigherExtractor] Total unique links found: {len(unique_links)}")
        return unique_links

    def _generate_date_formats(self, date_obj: datetime) -> List[str]:
        """Generate various date format strings for matching."""
        formats = [
            date_obj.strftime("%d %b %Y").lstrip('0'),        # "6 Nov 2025"
            date_obj.strftime("%d %B %Y").lstrip('0'),        # "6 November 2025"
            date_obj.strftime("%d %b %Y"),                    # "06 Nov 2025"
            date_obj.strftime("%d %B %Y"),                    # "06 November 2025"
            date_obj.strftime("%d %b").lstrip('0'),           # "6 Nov"
            date_obj.strftime("%d %B").lstrip('0'),           # "6 November"
            date_obj.strftime("%d %b"),                       # "06 Nov"
            date_obj.strftime("%d %B"),                       # "06 November"
            date_obj.strftime("%-d %b %Y"),                   # "6 Nov 2025" (Unix)
            date_obj.strftime("%-d %B %Y"),                   # "6 November 2025" (Unix)
            date_obj.strftime("%d %b %Y").lower().lstrip('0'),# "6 nov 2025"
            date_obj.strftime("%d %B %Y").lower().lstrip('0'),# "6 november 2025"
            date_obj.strftime("%d %b %Y").lower(),            # "06 nov 2025"
            date_obj.strftime("%d %B %Y").lower(),            # "06 november 2025"
            date_obj.strftime("%d.%-m.%Y"),                   # "15.2.2026" (Unix)
            date_obj.strftime("%d.%m.%Y"),                    # "15.02.2026"
            date_obj.strftime("%-d.%-m.%Y"),                  # "15.2.2026" without leading zeros (Unix)
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_formats = []
        for fmt in formats:
            if fmt not in seen:
                seen.add(fmt)
                unique_formats.append(fmt)
        
        return unique_formats

    def _extract_from_today_section(self, soup: BeautifulSoup, date_formats: List[str], date_iso: str) -> List[Link]:
        """
        Extract links from sections with 'Today' in the heading.
        Format: "Today Coin Master Free Spins & Coins 6 Nov 2025"
        """
        links = []
        
        # First, try to find <strong> tags containing "Today"
        for strong_tag in soup.find_all('strong'):
            strong_text = strong_tag.get_text()
            
            # Check if this contains "Today" and one of our date formats
            if 'today' in strong_text.lower():
                # Check if any of our date formats appear in this text
                if any(date_fmt in strong_text for date_fmt in date_formats):
                    print(f"[TechyHigherExtractor] Found 'Today' section in <strong>: {strong_text[:80]}")
                    
                    # Get the parent <p> tag to extract links from siblings
                    parent_p = strong_tag.find_parent('p')
                    if parent_p:
                        section_links = self._extract_links_after_heading(parent_p, date_iso)
                        links.extend(section_links)
                        break  # Usually only one "Today" section
        
        # If not found in <strong>, try <p> tags directly
        if not links:
            for p_tag in soup.find_all('p'):
                p_text = p_tag.get_text()
                
                # Check if this contains "Today" and one of our date formats
                if 'today' in p_text.lower():
                    # Check if any of our date formats appear in this text
                    if any(date_fmt in p_text for date_fmt in date_formats):
                        print(f"[TechyHigherExtractor] Found 'Today' section in <p>: {p_text[:80]}")
                        
                        # Extract links from following siblings
                        section_links = self._extract_links_after_heading(p_tag, date_iso)
                        links.extend(section_links)
                        break  # Usually only one "Today" section
        
        return links

    def _extract_from_date_heading(self, soup: BeautifulSoup, date_formats: List[str], date_iso: str) -> List[Link]:
        """
        Extract links from sections with just date headings.
        Formats: "5 november 2025", "Coin Master Free Spins & Coins 5 Nov 2025"
        """
        links = []
        
        # Find all <p> tags
        for p_tag in soup.find_all('p'):
            p_text = p_tag.get_text()
            
            # Skip if it's a "Today" heading (already handled)
            if 'today' in p_text.lower():
                continue
            
            # Check if any of our date formats appear in this text
            if any(date_fmt in p_text for date_fmt in date_formats):
                # Check if this looks like a date heading (contains <strong> or <span> styling)
                if p_tag.find(['strong', 'span']) or len(p_text.strip()) < 100:
                    print(f"[TechyHigherExtractor] Found date heading: {p_text[:80]}")
                    
                    # Extract links from following siblings until next date heading
                    section_links = self._extract_links_after_heading(p_tag, date_iso)
                    links.extend(section_links)
        
        return links

    def _extract_from_inline_dates(self, soup: BeautifulSoup, date_formats: List[str], date_iso: str) -> List[Link]:
        """
        Extract links that have dates embedded in the anchor tag text.
        Format: <p>2<a href="...">energy gifts links 15.2.2026</a></p>
        Only extracts links where the date matches today or yesterday.
        """
        links = []
        
        # Find all <p> tags containing <a> tags
        for p_tag in soup.find_all('p'):
            # Find all anchor tags in this paragraph
            a_tags = p_tag.find_all('a', href=True)
            
            for a_tag in a_tags:
                href = a_tag.get('href', '')
                link_text = a_tag.get_text(strip=True)
                
                # Check if the link text contains any of our date formats (today or yesterday)
                for date_fmt in date_formats:
                    if date_fmt in link_text:
                        # Validate it's a reward link
                        if self._is_valid_reward_link(href):
                            # Extract title from link text (remove date part if needed)
                            title = self._clean_inline_date_title(link_text, date_fmt)
                            
                            links.append(Link(
                                title=title,
                                url=href,
                                published_date_iso=date_iso
                            ))
                            print(f"[TechyHigherExtractor] Found inline date link (today/yesterday): {title} with date {date_fmt}")
                            break  # Found matching date, move to next link
        
        return links

    def _clean_inline_date_title(self, link_text: str, date_format: str) -> str:
        """
        Clean up link text that contains inline dates.
        Removes the date portion and cleans up the title.
        """
        # Remove the date part
        title = link_text.replace(date_format, '').strip()
        
        # Remove common prefixes/suffixes
        title = re.sub(r'^[\d\.]+\s*', '', title)  # Remove leading numbers like "1." or "2"
        title = re.sub(r'\s*links?\s*$', '', title, flags=re.IGNORECASE)  # Remove trailing "links" or "link"
        title = title.strip('. ')
        
        # Capitalize if needed
        if title and not title[0].isupper():
            title = title.capitalize()
        
        # Fallback to generic title
        if not title or len(title) < 3:
            title = "Energy Gift Link"
        
        return title

    def _extract_links_after_heading(self, heading: BeautifulSoup, date_iso: str) -> List[Link]:
        """
        Extract numbered links that appear after a date heading.
        Continues until hitting another date heading or major section break.
        """
        links = []
        
        # Pattern to detect date headings (to know when to stop)
        date_pattern = re.compile(
            r'\d{1,2}\s+(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|'
            r'jul|july|aug|august|sep|september|oct|october|nov|november|dec|december)\s+\d{4}',
            re.IGNORECASE
        )
        
        # Go through following siblings
        for sibling in heading.find_next_siblings():
            # Stop at next date heading
            if sibling.name == 'p':
                sibling_text = sibling.get_text()
                
                # Check if this is another date heading (stop boundary)
                if date_pattern.search(sibling_text) and (sibling.find(['strong', 'span']) or len(sibling_text.strip()) < 100):
                    break
                
                # Extract links from this paragraph
                a_tags = sibling.find_all('a', href=True)
                for a_tag in a_tags:
                    href = a_tag.get('href', '')
                    
                    # Filter valid reward links
                    if self._is_valid_reward_link(href):
                        title = self._extract_title(a_tag, sibling_text)
                        links.append(Link(
                            title=title,
                            url=href,
                            published_date_iso=date_iso
                        ))
            
            # Stop at major section breaks (h2, h3, etc.)
            elif sibling.name in ['h2', 'h3', 'h4']:
                break
        
        return links

    def _is_valid_reward_link(self, url: str) -> bool:
        """
        Check if URL is a valid reward link (not ads, social media, etc.).
        """
        url_lower = url.lower()
        
        # Exclude known non-reward URLs
        exclude_patterns = [
            'googlesyndication.com',
            'adsbygoogle',
            'facebook.com',
            'twitter.com',
            'instagram.com',
            'youtube.com',
            'telegram.me',
        ]
        
        if any(pattern in url_lower for pattern in exclude_patterns):
            return False
        
        # Include known reward domains
        reward_patterns = [
            'rewards.coinmaster.com',
            'd10xl.com',
            'travel-town-app.com',
            'traveltown.onelink.me',
            'coinmaster.com/rewards',
            '.onelink.me',
            'cashfrenzy',
            'grandharvest',
            'hititrich',
        ]
        
        # Accept if it's a known reward domain
        if any(pattern in url_lower for pattern in reward_patterns):
            return True
        
        # Accept if it has reward-like query parameters
        if any(param in url_lower for param in ['reward', 'gift', 'bonus', 'c=', 'af_dp=']):
            return True
        
        return False

    def _extract_title(self, a_tag: BeautifulSoup, context_text: str) -> str:
        """
        Extract a clean title from an anchor tag.
        Uses link text, or constructs from context if needed.
        """
        # Get link text
        title = a_tag.get_text(strip=True)
        
        # If title is just a number (like "1." or "2."), enhance it with context
        if re.match(r'^\d+\.?$', title):
            # Try to extract game name from context
            context_lower = context_text.lower()
            if 'coin master' in context_lower:
                title = f"Coin Master Link {title}"
            elif 'travel town' in context_lower or 'traveltown' in context_lower:
                title = f"Travel Town Link {title}"
            elif 'cash frenzy' in context_lower:
                title = f"Cash Frenzy Link {title}"
            else:
                title = f"Reward Link {title}"
        
        # Fallback to generic title
        if not title:
            title = "Reward Link"
        
        return title

    @property
    def name(self) -> str:
        return "TechyHigher Extractor"

    @property
    def description(self) -> str:
        return "Extracts reward links from techyhigher.com with 'Today' and date-based sections"
