"""
Example Promo Code Extractor

This is a template showing how to create an extractor that supports promo code extraction.
Copy this file and modify it for your specific site.

Features demonstrated:
- Extracting promo codes from HTML
- Implementing supports_promo_codes()
- Implementing extract_promo_codes()
- Hybrid extraction (both links and promo codes)

How it works:
- The extractor looks for promo codes in specific HTML patterns
- Common patterns include: <code> tags, .promo-code classes, data attributes
- Codes are deduped using the code + date as a fingerprint
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link, PromoCode
import re
from datetime import datetime


def register_extractor(name):
    """Local registration decorator"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("example_promo")
class ExamplePromoExtractor(BaseExtractor):
    """
    Example extractor demonstrating promo code extraction.
    
    This extractor shows how to extract both links AND promo codes
    from a source page. Use as a template for your own extractors.
    """
    
    def can_handle(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Modify this to match your target domain(s).
        """
        # Example: matches example-promo-site.com
        return "example-promo-site.com" in url.lower()
    
    def supports_promo_codes(self) -> bool:
        """
        Indicate that this extractor supports promo code extraction.
        
        Returns True to enable promo code extraction for posts using this extractor.
        """
        return True
    
    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from HTML content.
        
        This is the standard link extraction method - modify for your site's HTML structure.
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Example: look for links with specific class or data attributes
        for a in soup.find_all('a', class_=lambda c: c and 'reward-link' in c.lower()):
            href = a.get('href')
            title = a.get_text(strip=True) or "Reward Link"
            
            if href and href.startswith('http'):
                links.append(Link(
                    title=title,
                    url=href,
                    published_date_iso=date
                ))
        
        return links
    
    def extract_promo_codes(self, html: str, date: str) -> List[PromoCode]:
        """
        Extract promo codes from HTML content.
        
        This method is called when extraction_mode is "promo_codes" or "both".
        
        Common patterns to look for:
        1. <code> tags containing codes
        2. Elements with class="promo-code" or similar
        3. Data attributes like data-code="..."
        4. Text patterns like "Code: XXXX" or "Use code XXXX"
        
        Args:
            html: HTML content from the source page
            date: Target date in YYYY-MM-DD format
            
        Returns:
            List of PromoCode objects
        """
        soup = BeautifulSoup(html, 'html.parser')
        promo_codes = []
        
        # Convert ISO date to display formats for matching
        try:
            dt = datetime.fromisoformat(date)
            date_formats = [
                f"{dt.day} {dt.strftime('%B %Y')}",  # "4 November 2025"
                f"{dt.strftime('%b')} {dt.day}, {dt.strftime('%Y')}",  # "Nov 4, 2025"
            ]
        except ValueError:
            date_formats = []
        
        # ================================================================
        # PATTERN 1: Look for <code> tags within promo code containers
        # ================================================================
        for container in soup.find_all(['div', 'section'], class_=lambda c: c and 'promo' in c.lower()):
            code_tags = container.find_all('code')
            for code_tag in code_tags:
                code_text = code_tag.get_text(strip=True)
                if code_text and len(code_text) >= 3:  # Min 3 chars for a code
                    # Look for description in nearby elements
                    description = self._find_description(container, code_tag)
                    expiry = self._find_expiry(container)
                    
                    promo_codes.append(PromoCode(
                        code=code_text,
                        description=description,
                        published_date_iso=date,
                        expiry_date=expiry,
                        category="promo"
                    ))
        
        # ================================================================
        # PATTERN 2: Look for elements with data-code attribute
        # ================================================================
        for elem in soup.find_all(attrs={"data-code": True}):
            code_text = elem.get("data-code")
            if code_text:
                description = elem.get("data-description") or elem.get_text(strip=True)
                promo_codes.append(PromoCode(
                    code=code_text,
                    description=description,
                    published_date_iso=date,
                    category="promo"
                ))
        
        # ================================================================
        # PATTERN 3: Look for "Code: XXXX" or "Use code XXXX" text patterns
        # ================================================================
        code_pattern = re.compile(r'(?:code|coupon|promo)[:\s]+([A-Z0-9]{3,20})', re.IGNORECASE)
        
        for text_elem in soup.find_all(text=code_pattern):
            matches = code_pattern.findall(str(text_elem))
            for match in matches:
                # Avoid duplicates
                if not any(pc.code.upper() == match.upper() for pc in promo_codes):
                    promo_codes.append(PromoCode(
                        code=match.upper(),
                        description=None,
                        published_date_iso=date,
                        category="promo"
                    ))
        
        # ================================================================
        # PATTERN 4: Look for copy-button elements (common pattern)
        # ================================================================
        for btn in soup.find_all(['button', 'span'], class_=lambda c: c and 'copy' in c.lower()):
            code_text = btn.get('data-clipboard-text') or btn.get('data-code')
            if code_text and len(code_text) >= 3:
                promo_codes.append(PromoCode(
                    code=code_text,
                    description=None,
                    published_date_iso=date,
                    category="promo"
                ))
        
        return promo_codes
    
    def _find_description(self, container, code_element) -> str:
        """Helper to find description text near a code element."""
        # Look for nearby paragraph or span with description
        for elem in container.find_all(['p', 'span', 'div']):
            text = elem.get_text(strip=True)
            # Skip if it's the code itself
            if text == code_element.get_text(strip=True):
                continue
            # Look for descriptive text (contains common keywords)
            if any(keyword in text.lower() for keyword in ['free', 'bonus', 'discount', '%', 'off', 'spins']):
                return text[:100]  # Limit length
        return None
    
    def _find_expiry(self, container) -> str:
        """Helper to find expiry date near a promo code."""
        expiry_pattern = re.compile(r'(?:expires?|valid\s+until|ends?)[:\s]+(.+?)(?:\.|$)', re.IGNORECASE)
        text = container.get_text()
        match = expiry_pattern.search(text)
        if match:
            return match.group(1).strip()[:50]
        return None
