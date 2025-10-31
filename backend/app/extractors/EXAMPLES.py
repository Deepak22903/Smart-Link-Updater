"""
EXAMPLE: How to Add a New Extractor

This file shows various patterns for creating extractors.
Copy this template and modify for your needs!
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor, ExtractedLink
from ..extractors import register_extractor
import re


# ============================================================================
# PATTERN 1: Simple CSS Selector Extractor
# ============================================================================

@register_extractor("example_css")
class CssSelectorExtractor(BaseExtractor):
    """
    Extract links using CSS selectors.
    Good for: Sites with consistent HTML structure.
    """
    
    def can_handle(self, url: str) -> bool:
        return "example.com" in url
    
    def extract(self, html: str, date: str) -> List[ExtractedLink]:
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Find all links with class="reward-link"
        for a in soup.select('.reward-link'):
            href = a.get('href')
            title = a.get_text(strip=True)
            
            if href and href.startswith('http'):
                links.append(ExtractedLink(
                    title=title,
                    url=href,
                    date=date
                ))
        
        return links


# ============================================================================
# PATTERN 2: Date-Based Section Extractor
# ============================================================================

@register_extractor("example_date_section")
class DateSectionExtractor(BaseExtractor):
    """
    Extract links from sections marked with today's date.
    Good for: Daily reward pages with date headers.
    """
    
    def can_handle(self, url: str) -> bool:
        return "rewards.example.com" in url
    
    def extract(self, html: str, date: str) -> List[ExtractedLink]:
        from datetime import datetime
        
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Convert date to various formats to match
        dt = datetime.fromisoformat(date)
        date_formats = [
            dt.strftime("%Y-%m-%d"),        # 2025-10-26
            dt.strftime("%B %d, %Y"),       # October 26, 2025
            dt.strftime("%d %B %Y"),        # 26 October 2025
            dt.strftime("%m/%d/%Y"),        # 10/26/2025
        ]
        
        # Find all headings
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            heading_text = heading.get_text(strip=True)
            
            # Check if heading contains today's date
            if any(date_str in heading_text for date_str in date_formats):
                # Get the section following this heading
                section = heading.find_next_sibling()
                
                if section:
                    for a in section.find_all('a', href=True):
                        href = a['href']
                        title = a.get_text(strip=True) or "Link"
                        
                        if href.startswith('http'):
                            links.append(ExtractedLink(
                                title=title,
                                url=href,
                                date=date
                            ))
        
        return links


# ============================================================================
# PATTERN 3: Regex-Based Extractor
# ============================================================================

@register_extractor("example_regex")
class RegexExtractor(BaseExtractor):
    """
    Extract links using regex patterns.
    Good for: Links embedded in JavaScript or JSON.
    """
    
    def can_handle(self, url: str) -> bool:
        return "api.example.com" in url
    
    def extract(self, html: str, date: str) -> List[ExtractedLink]:
        links = []
        
        # Pattern to match reward URLs in JavaScript
        pattern = r'rewardUrl:\s*["\']([^"\']+)["\']'
        
        for match in re.finditer(pattern, html):
            url = match.group(1)
            
            # Extract title from nearby text
            title_pattern = r'title:\s*["\']([^"\']+)["\']'
            title_match = re.search(title_pattern, html[max(0, match.start()-200):match.start()+200])
            title = title_match.group(1) if title_match else "Reward Link"
            
            links.append(ExtractedLink(
                title=title,
                url=url,
                date=date
            ))
        
        return links


# ============================================================================
# PATTERN 4: Multi-Site Extractor
# ============================================================================

@register_extractor("gaming_network")
class GamingNetworkExtractor(BaseExtractor):
    """
    Handle multiple sites from the same network.
    Good for: Sites with similar structure under different domains.
    """
    
    SUPPORTED_DOMAINS = [
        "site1.example.com",
        "site2.example.com",
        "site3.example.com"
    ]
    
    def can_handle(self, url: str) -> bool:
        return any(domain in url for domain in self.SUPPORTED_DOMAINS)
    
    def extract(self, html: str, date: str) -> List[ExtractedLink]:
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # All sites in network use this structure
        for container in soup.select('.daily-rewards'):
            date_elem = container.select_one('.reward-date')
            
            if date_elem and date in date_elem.get_text():
                for a in container.select('a.reward-button'):
                    href = a.get('href')
                    title = a.get_text(strip=True)
                    
                    if href:
                        links.append(ExtractedLink(
                            title=title,
                            url=href,
                            date=date
                        ))
        
        return links


# ============================================================================
# PATTERN 5: API-Based Extractor
# ============================================================================

@register_extractor("example_api")
class ApiExtractor(BaseExtractor):
    """
    Extract links from JSON API responses.
    Good for: Sites that load content via AJAX/API calls.
    """
    
    def can_handle(self, url: str) -> bool:
        return "api.rewards.example.com" in url
    
    def extract(self, html: str, date: str) -> List[ExtractedLink]:
        import json
        
        links = []
        
        try:
            # Parse JSON response
            data = json.loads(html)
            
            # Extract links from JSON structure
            for reward in data.get('rewards', []):
                if reward.get('date') == date:
                    links.append(ExtractedLink(
                        title=reward.get('title', 'Reward'),
                        url=reward.get('url'),
                        date=date
                    ))
        
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from HTML
            json_match = re.search(r'var\s+rewards\s*=\s*(\{.*?\});', html, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                # ... process data
        
        return links


# ============================================================================
# HOW TO USE:
# ============================================================================
# 
# 1. Copy one of the patterns above that matches your needs
# 2. Create a new file: backend/app/extractors/your_site.py
# 3. Change the @register_extractor("name") to something unique
# 4. Modify can_handle() to match your URL
# 5. Update extract() logic for your HTML structure
# 6. Add to posts.json:
#    {
#      "1234": {
#        "post_id": 1234,
#        "source_urls": ["https://your-site.com/page"],
#        "timezone": "Asia/Kolkata",
#        "extractor": "your_name"
#      }
#    }
#
# That's it! No changes to main.py needed!
