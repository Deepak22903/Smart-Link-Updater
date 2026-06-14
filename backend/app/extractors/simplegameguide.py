"""
SimpleGameGuide.com Extractor

Handles:
- simplegameguide.com/coin-master-free-spins-links/
- simplegameguide.com/carnival-tycoon-free-spins/
- Similar SimpleGameGuide pages

Extraction Logic:
- Looks for h4 headings containing today's date
- Extracts links from the section following the heading
- Filters out non-button elements
"""

from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
import re
from datetime import datetime, timedelta
from collections import OrderedDict
import logging


logger = logging.getLogger(__name__)


def register_extractor(name):
    """Local registration decorator - will be imported by __init__.py"""
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("simplegameguide")
class SimpleGameGuideExtractor(BaseExtractor):
    """Extractor for SimpleGameGuide.com pages with date-based h4 headings."""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from simplegameguide.com."""
        return "simplegameguide.com" in url.lower()
    
    def extract(self, html: str, date: str) -> List[Link]:
        """
        Extract links from SimpleGameGuide HTML.

        Looks for date headers in formats:
        - <h4>26 October 2025</h4>
        - <div><strong>Oct 26, 2025:</strong></div>

        Extracts links from the section following a matching heading, stopping
        when the next date header is encountered. Matches BOTH today's and
        yesterday's date headers (the source often lags a day before posting
        today's section), tagging each link with the date it was published under.
        """
        logger.info("simplegameguide: starting extraction", extra={"date": date})
        if not html:
            logger.warning("simplegameguide: empty html payload", extra={"date": date})
            return []

        soup = BeautifulSoup(html, 'html.parser')

        try:
            dt = datetime.fromisoformat(date)
        except ValueError:
            logger.error("simplegameguide: invalid date format", extra={"date": date})
            return []

        yesterday = dt - timedelta(days=1)
        today_iso = dt.strftime("%Y-%m-%d")
        yesterday_iso = yesterday.strftime("%Y-%m-%d")

        # Collect all potential date headers in document order so "today" is
        # processed before "yesterday".
        date_elements = self._collect_date_elements(soup)
        logger.debug(
            "simplegameguide: collected date elements",
            extra={"date": date, "count": len(date_elements)}
        )

        today_start = self._find_start_element(date_elements, self._date_formats(dt))
        yesterday_start = self._find_start_element(date_elements, self._date_formats(yesterday))

        if not today_start and not yesterday_start:
            logger.warning(
                "simplegameguide: no matching date header found",
                extra={"date": date, "today_iso": today_iso, "yesterday_iso": yesterday_iso}
            )

        # Combine links from both days, deduplicating by URL (today wins).
        all_links = OrderedDict()
        for start_element, section_iso, label in (
            (today_start, today_iso, "today"),
            (yesterday_start, yesterday_iso, "yesterday"),
        ):
            if not start_element:
                continue
            logger.info(
                "simplegameguide: found date header",
                extra={"date": date, "section": label, "header_text": start_element.get_text(strip=True)}
            )
            for link in self._extract_section(start_element, date_elements, section_iso, date):
                if link.url not in all_links:
                    all_links[link.url] = link

        logger.info(
            "simplegameguide: extraction complete",
            extra={"date": date, "link_count": len(all_links)}
        )
        return list(all_links.values())

    @staticmethod
    def _date_formats(dt: datetime) -> List[str]:
        """Build the display-string variants a date header may use for `dt`."""
        return [
            # "4 November 2025" (full month name, no leading zero)
            f"{dt.day} {dt.strftime('%B %Y')}",
            # "Nov 4, 2025:" (abbreviated month, no leading zero)
            f"{dt.strftime('%b')} {dt.day}, {dt.strftime('%Y')}:",
            # "November 4, 2025:" (full month name, no leading zero)
            f"{dt.strftime('%B')} {dt.day}, {dt.strftime('%Y')}:",
        ]

    @staticmethod
    def _collect_date_elements(soup: BeautifulSoup) -> list:
        """Collect h4 and <div><strong>Date</strong></div> headers in document order."""
        date_elements = []
        for elem in soup.find_all(['h4', 'div']):
            if elem.name == 'h4':
                date_elements.append(elem)
                continue
            # Pattern 2: <div><strong>Date:</strong></div> where the strong tag
            # is the primary content of the div.
            strong = elem.find('strong')
            if strong:
                div_text = elem.get_text(strip=True)
                strong_text = strong.get_text(strip=True)
                if strong_text and len(strong_text) > len(div_text) * 0.7:
                    date_elements.append(elem)
        return date_elements

    @staticmethod
    def _find_start_element(date_elements: list, formats: List[str]):
        """Return the first date element whose text matches one of `formats`."""
        for elem in date_elements:
            elem_text = elem.get_text(strip=True)
            if any(fmt in elem_text for fmt in formats):
                return elem
        return None

    @staticmethod
    def _extract_section(start_element, date_elements: list, section_iso: str, date: str) -> List[Link]:
        """Extract links from siblings after `start_element` until the next date header."""
        links = []
        for sibling in start_element.find_next_siblings():
            # If the sibling is another date header, stop processing.
            if sibling in date_elements:
                logger.debug(
                    "simplegameguide: encountered next date header; stopping",
                    extra={"date": date, "section_iso": section_iso, "header_text": sibling.get_text(strip=True)}
                )
                break

            # Pattern A: Links with class containing "button"
            for a in sibling.find_all('a', class_=lambda c: c and 'button' in c.lower()):
                href = a.get('href')
                title = a.get_text(strip=True) or "Link"
                if href and href.startswith('http'):
                    logger.debug(
                        "simplegameguide: found button link",
                        extra={"date": date, "section_iso": section_iso, "title": title, "url": href}
                    )
                    links.append(Link(title=title, url=href, published_date_iso=section_iso))

            # Pattern B: Divs with data-link attribute (Coin Master / Travel Town style)
            for div in sibling.find_all('div', {'data-link': True}):
                href = div.get('data-link')
                span = div.find('span')
                title = span.get_text(strip=True) if span else "Link"
                if href and href.startswith('http'):
                    logger.debug(
                        "simplegameguide: found data-link",
                        extra={"date": date, "section_iso": section_iso, "title": title, "url": href}
                    )
                    links.append(Link(title=title, url=href, published_date_iso=section_iso))

        return links
