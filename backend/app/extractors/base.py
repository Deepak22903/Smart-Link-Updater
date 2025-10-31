"""
Base Extractor Interface

All extractors must inherit from BaseExtractor and implement:
- can_handle(url): Returns True if this extractor can handle the URL
- extract(html, date): Extracts links from HTML for the given date
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import Link


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
    
    @property
    def name(self) -> str:
        """Human-readable name of this extractor."""
        return self.__class__.__name__
    
    @property
    def description(self) -> str:
        """Description of what this extractor does."""
        return self.__class__.__doc__ or "No description available"
