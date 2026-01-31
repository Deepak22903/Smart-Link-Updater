"""
Gamesbie Promo Code Extractor

Extracts promo codes from gamesbie.com pages with structure:
- Active codes under h2 containing "Active" with expiry dates
- Expired codes section to be skipped

Example HTML structure:
<h2 class="wp-block-heading">Top Heroes Gift Codes: Active (January)</h2>
<ul class="wp-block-list">
    <li><strong>5045BB1614</strong>–<em>(Valid until: 5th January 2026)</em></li>
    ...
</ul>
<p><strong>Expired Codes</strong></p>
<ul class="wp-block-list">
    <li><strong>DB70EAC6B</strong> – <em>Expired</em></li>
    ...
</ul>
"""

import re
import logging
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup, Tag

from .base import BaseExtractor
from ..models import PromoCode, ExtractionResult

logger = logging.getLogger(__name__)


def register_extractor(name):
    """Local registration decorator - will be imported by __init__.py"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("gamesbie")
class GamesbieExtractor(BaseExtractor):
    """Extractor for gamesbie.com promo code pages."""

    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        return "gamesbie.com" in url.lower()

    def supports_promo_codes(self) -> bool:
        """This extractor supports promo code extraction."""
        return True

    def supported_extraction_modes(self) -> List[str]:
        """This extractor only supports promo codes."""
        return ["promo_codes"]

    def extract(self, html: str, url: str, today_str: str) -> ExtractionResult:
        """
        Extract method - not used for this extractor as it only supports promo codes.
        Returns empty result.
        """
        return ExtractionResult(links=[], published_date_iso=today_str, only_today=False, confidence=0.0)

    def extract_promo_codes(self, html: str, url: str, today_str: str) -> ExtractionResult:
        """
        Extract active promo codes from gamesbie.com pages.
        
        Strategy:
        1. Find h2 heading containing "Active" to identify the active codes section
        2. Get the next ul element after the heading
        3. Stop when we hit "Expired Codes" marker
        4. Parse each li for code (in <strong>) and expiry date (in <em>)
        5. Filter out already expired codes based on expiry date
        """
        soup = BeautifulSoup(html, "html.parser")
        promo_codes: List[PromoCode] = []
        
        # Find the active codes section header
        active_header = None
        for h2 in soup.find_all("h2"):
            if "active" in h2.get_text().lower():
                active_header = h2
                break
        
        if not active_header:
            logger.warning(f"[Gamesbie] No 'Active' header found in {url}")
            return ExtractionResult(links=[], promo_codes=[], published_date_iso=today_str, only_today=False, confidence=0.0)
        
        logger.info(f"[Gamesbie] Found active header: {active_header.get_text()[:50]}")
        
        # Find the ul element after the active header
        active_ul = None
        for sibling in active_header.find_next_siblings():
            if sibling.name == "ul":
                active_ul = sibling
                break
            # Stop if we hit the expired codes marker
            if sibling.name == "p" and "expired" in sibling.get_text().lower():
                break
        
        if not active_ul:
            logger.warning(f"[Gamesbie] No ul found after active header in {url}")
            return ExtractionResult(links=[], promo_codes=[], published_date_iso=today_str, only_today=False, confidence=0.0)
        
        # Parse today's date for expiry comparison
        try:
            today_date = datetime.strptime(today_str, "%Y-%m-%d")
        except ValueError:
            today_date = datetime.now()
        
        # Extract codes from list items
        for li in active_ul.find_all("li", recursive=False):
            code_data = self._parse_code_item(li, url, today_str, today_date)
            if code_data:
                promo_codes.append(code_data)
        
        logger.info(f"[Gamesbie] Extracted {len(promo_codes)} active promo codes from {url}")
        
        return ExtractionResult(
            links=[],
            promo_codes=promo_codes,
            published_date_iso=today_str,
            only_today=False,  # Promo codes have expiry dates, not published dates
            confidence=1.0 if len(promo_codes) > 0 else 0.5
        )

    def _parse_code_item(
        self, li: Tag, url: str, today_str: str, today_date: datetime
    ) -> Optional[PromoCode]:
        """
        Parse a single list item to extract code and expiry date.
        
        Expected format:
        <li><strong>CODE</strong> – <em>(Valid until: DATE)</em></li>
        """
        # Get the code from <strong> tag
        strong_tag = li.find("strong")
        if not strong_tag:
            return None
        
        code = strong_tag.get_text().strip()
        if not code:
            return None
        
        # Get expiry date from <em> tag
        em_tag = li.find("em")
        expiry_date = None
        expiry_str = None
        
        if em_tag:
            em_text = em_tag.get_text().strip()
            
            # Skip if marked as expired
            if "expired" in em_text.lower():
                logger.debug(f"[Gamesbie] Skipping expired code: {code}")
                return None
            
            # Parse expiry date from formats like "(Valid until: 5th January 2026)"
            expiry_date = self._parse_expiry_date(em_text)
            if expiry_date:
                expiry_str = expiry_date.strftime("%Y-%m-%d")
                
                # Skip if already expired
                if expiry_date < today_date:
                    logger.debug(f"[Gamesbie] Skipping expired code {code} (expired: {expiry_str})")
                    return None
        
        # Build description
        description = f"Promo code: {code}"
        if expiry_str:
            description = f"Valid until {expiry_str}"
        
        return PromoCode(
            code=code,
            description=description,
            published_date_iso=today_str,
            expiry_date=expiry_str,
            source_url=url,
            category="gift_code"
        )

    def _parse_expiry_date(self, text: str) -> Optional[datetime]:
        """
        Parse expiry date from text like "(Valid until: 5th January 2026)"
        
        Handles ordinal suffixes (1st, 2nd, 3rd, 4th, etc.)
        """
        # Remove parentheses and "Valid until:" prefix
        text = text.strip("()").strip()
        text = re.sub(r"valid until:?\s*", "", text, flags=re.IGNORECASE).strip()
        
        # Remove ordinal suffixes (st, nd, rd, th)
        text = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text)
        
        # Try parsing common date formats
        date_formats = [
            "%d %B %Y",      # 5 January 2026
            "%d %b %Y",      # 5 Jan 2026
            "%B %d, %Y",     # January 5, 2026
            "%b %d, %Y",     # Jan 5, 2026
            "%d/%m/%Y",      # 05/01/2026
            "%m/%d/%Y",      # 01/05/2026
            "%Y-%m-%d",      # 2026-01-05
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                continue
        
        logger.debug(f"[Gamesbie] Could not parse expiry date: {text}")
        return None
