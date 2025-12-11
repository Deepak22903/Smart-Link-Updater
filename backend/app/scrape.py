import os
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

SCRAPER_API_URL = os.getenv("SCRAPER_API_URL")  # e.g., https://api.scraperapi.com
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def fetch_html(url: str, timeout: float = 30.0) -> str:
    """
    Fetch HTML from URL with retry logic.
    Raises the last exception if all retries fail.
    """
    # If configured, use ScraperAPI-like service; else fetch directly
    if SCRAPER_API_URL and SCRAPER_API_KEY:
        params = {"api_key": SCRAPER_API_KEY, "url": url, "render": "true"}
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(SCRAPER_API_URL, params=params)
            r.raise_for_status()
            return r.text
    else:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
