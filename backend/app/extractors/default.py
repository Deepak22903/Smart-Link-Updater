"""
Default/Generic Extractor

Fallback extractor for unknown sites.
Uses Gemini AI to intelligently extract links.

This extractor is used when no specific extractor matches the URL.
"""

import asyncio
from typing import List
from .base import BaseExtractor
from ..llm import parse_links_with_gemini


def register_extractor(name):
    """Local registration decorator - will be imported by __init__.py"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("default")
class DefaultExtractor(BaseExtractor):
    """
    Generic extractor using Gemini AI.
    Handles any website format by using AI to identify relevant links.
    
    This is the most powerful extractor that can handle any site structure,
    but uses AI tokens so it's slower and has rate limits.
    """
    
    def can_handle(self, url: str) -> bool:
        """Default extractor handles everything as fallback."""
        return True
    
    def extract(self, html: str, date: str) -> List:
        """
        Use Gemini AI to intelligently extract links from HTML.
        
        Gemini is instructed to:
        - Find sections matching today's date in any format
        - Extract URLs from <a> tags, data-link attributes, etc.
        - Return structured JSON with titles and URLs
        - Filter out navigation/non-reward links
        
        Falls back to empty list if:
        - GEMINI_API_KEY not set
        - Confidence below threshold
        - API error occurs
        """
        # Gemini function is async, so we need to run it
        # Create a new event loop for this synchronous context
        try:
            # Try to get existing loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context - this shouldn't happen in extractors
                # Create a new loop in a thread instead
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        parse_links_with_gemini(html, date, "UTC")
                    )
                    result = future.result(timeout=30)
                    return result.links if result else []
            else:
                # No running loop - we can use asyncio.run
                result = asyncio.run(parse_links_with_gemini(html, date, "UTC"))
                return result.links if result else []
        except Exception as e:
            # If anything goes wrong, return empty list
            print(f"Gemini extraction error: {e}")
            return []
