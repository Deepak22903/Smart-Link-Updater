"""
Base Extractor Interface

All extractors must inherit from BaseExtractor and implement:
- can_handle(url): Returns True if this extractor can handle the URL
- extract(html, date): Extracts links from HTML for the given date

Optional methods for promo code extraction:
- extract_promo_codes(html, date): Extracts promo codes from HTML for the given date
- supports_promo_codes(): Returns True if this extractor can extract promo codes
"""

from abc import ABC, abstractmethod
from typing import List, Literal
from ..models import Link, PromoCode


# Extraction mode type hint
ExtractionMode = Literal["links", "promo_codes", "both"]


class BaseExtractor(ABC):
    """Base class for all link extractors."""
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Args:
            url: The source URL to check
            
        Returns:
            True if this extractor should be used for this URL
        """
        pass
    
    @abstractmethod
    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from HTML content for a specific date.
        
        Args:
            html: HTML content from the source page
            date: Target date in YYYY-MM-DD format
            
        Returns:
            List of Link objects matching the date
        """
        pass
    
    def extract_promo_codes(self, html: str, date: str) -> List[PromoCode]:
        """
        Extract promo codes from HTML content for a specific date.
        
        Override this method in extractors that support promo code extraction.
        
        Args:
            html: HTML content from the source page
            date: Target date in YYYY-MM-DD format
            
        Returns:
            List of PromoCode objects matching the date
        """
        return []  # Default: no promo codes
    
    def supports_promo_codes(self) -> bool:
        """
        Check if this extractor supports promo code extraction.
        
        Override and return True if extract_promo_codes() is implemented.
        
        Returns:
            True if promo codes can be extracted
        """
        return False
    
    def supported_extraction_modes(self) -> List[ExtractionMode]:
        """
        Return the extraction modes this extractor supports.
        
        Returns:
            List of supported modes: "links", "promo_codes", or "both"
        """
        modes: List[ExtractionMode] = ["links"]
        if self.supports_promo_codes():
            modes.append("promo_codes")
        return modes
    
    @property
    def name(self) -> str:
        """Human-readable name of this extractor."""
        return self.__class__.__name__
    
    @property
    def description(self) -> str:
        """Description of what this extractor does."""
        return self.__class__.__doc__ or "No description available"
    
    def check_previous_days(self) -> int:
        """
        Number of previous days to check when deduplicating links.
        
        DEFAULT BEHAVIOR: Checks today + yesterday to prevent duplicate links.
        Most sites include previous days' links in their updates, so this is
        the safest default to prevent re-adding old links.
        
        Override this method and return 0 if your site ONLY shows today's links.
        Override and return 2, 3, etc. if your site shows more historical days.
        
        Returns:
            Number of previous days to check:
            - 1 = today + yesterday (DEFAULT - prevents most duplicates)
            - 0 = today only (use only if site never shows old links)
            - 2 = today + last 2 days, etc.
        """
        return 1  # Default: check today + yesterday to prevent duplicates
