from typing import List
from collections import OrderedDict
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from datetime import datetime
import re
import requests

@register_extractor("wsop")
class WSOPExtractor(BaseExtractor):
    """Extractor for wsopga.me links grouped by date headings."""

    def can_handle(self, url: str) -> bool:
        url_lower = url.lower()
        return any(domain in url_lower for domain in ["wsopga.me", "freechipswsop.com", "wsopchipsfree.com"])
    
    # Note: Using default check_previous_days() which returns 1 (today + yesterday)
    # This is the standard behavior for all extractors now

    def _generate_date_patterns(self, date_obj: datetime) -> List[str]:
        """Generate all possible date format variations for matching headings."""
        patterns = []
        day = date_obj.day
        month = date_obj.strftime('%B')
        year = date_obj.year
        
        # Generate ordinal suffix
        if 10 <= day % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
        patterns.extend([
            date_obj.strftime("%d %B %Y").lstrip('0'),  # "8 December 2025"
            date_obj.strftime("%d %B %Y"),               # "08 December 2025"
            f"{day}{suffix} {month} {year}",             # "8th December 2025"
            f"{day}{suffix} {month.lower()} {year}",     # "8th december 2025"
        ])
        
        # Also add ID-style pattern for h3 id matching: "h-30th-january-2026"
        id_pattern = f"h-{day}{suffix}-{month.lower()}-{year}"
        patterns.append(id_pattern)
        
        return patterns

    def _extract_url_from_onclick(self, onclick: str) -> str:
        """Extract wsopga.me URL from onclick attribute like showWsopOverlay('https://...')"""
        match = re.search(r"showWsopOverlay\(['\"]([^'\"]+)['\"]\)", onclick)
        if match:
            return match.group(1)
        return ""

    def _extract_links_from_new_structure(self, soup: BeautifulSoup, today_patterns: List[str], 
                                          yesterday_patterns: List[str], date_iso: str, 
                                          yesterday_iso: str, logging) -> tuple:
        """Extract links from new HTML structure with h3 headings and wsop-link-block divs."""
        today_links = OrderedDict()
        yesterday_links = OrderedDict()
        found_today = False
        found_yesterday = False
        
        # Find all h3 headings that could be date headers
        h3_headings = soup.find_all('h3', class_=lambda c: c and 'wp-block-heading' in c)
        
        if not h3_headings:
            logging.debug("[WSOPExtractor] No h3.wp-block-heading found, new structure not detected")
            return None, None, False
        
        logging.info(f"[WSOPExtractor] Found {len(h3_headings)} h3.wp-block-heading elements")
        
        for h3 in h3_headings:
            h3_text = h3.get_text(strip=True).lower()
            h3_id = (h3.get('id') or '').lower()
            
            logging.debug(f"[WSOPExtractor] Checking h3: text='{h3_text}', id='{h3_id}'")
            
            # Check if this is today's heading
            is_today = any(p.lower() in h3_text or p.lower() == h3_id for p in today_patterns)
            is_yesterday = any(p.lower() in h3_text or p.lower() == h3_id for p in yesterday_patterns)
            
            if is_today:
                found_today = True
                logging.info(f"[WSOPExtractor] Found TODAY's h3 heading: {h3_text}")
                self._extract_links_after_heading(h3, today_links, date_iso, logging)
            elif is_yesterday:
                found_yesterday = True
                logging.info(f"[WSOPExtractor] Found YESTERDAY's h3 heading: {h3_text}")
                self._extract_links_after_heading(h3, yesterday_links, yesterday_iso, logging)
        
        if found_today or found_yesterday:
            logging.info(f"[WSOPExtractor] New structure: {len(today_links)} today links, {len(yesterday_links)} yesterday links")
            return today_links, yesterday_links, True
        
        return None, None, False
    
    def _extract_links_after_heading(self, heading, target_dict: OrderedDict, target_date_iso: str, logging):
        """Extract links from elements following a date heading until next h3."""
        for sibling in heading.find_next_siblings():
            # Stop at next h3 (next date section)
            if sibling.name == 'h3':
                break
            
            # Handle wsop-link-block divs (new structure)
            if sibling.name == 'div' and 'wsop-link-block' in ' '.join(sibling.get('class', [])):
                # Get title from inner h3
                title_h3 = sibling.find('h3')
                title = title_h3.get_text(strip=True) if title_h3 else "Free Chips"
                
                # Find anchor with onclick
                anchor = sibling.find('a', onclick=True)
                if anchor:
                    onclick = anchor.get('onclick', '')
                    url = self._extract_url_from_onclick(onclick)
                    if url and 'wsopga.me' in url:
                        if url not in target_dict:
                            logging.info(f"[WSOPExtractor] Extracted from onclick: {url} | Title: {title}")
                            target_dict[url] = Link(title=title, url=url, date=target_date_iso, published_date_iso=target_date_iso)
                
                # Also check for regular href links
                for a in sibling.find_all('a', href=True):
                    href = a.get('href', '')
                    if href.startswith('http') and 'wsopga.me' in href:
                        if href not in target_dict:
                            logging.info(f"[WSOPExtractor] Extracted from href: {href} | Title: {title}")
                            target_dict[href] = Link(title=title, url=href, date=target_date_iso, published_date_iso=target_date_iso)
            
            # Also handle any direct anchors with onclick
            for a in sibling.find_all('a', onclick=True):
                onclick = a.get('onclick', '')
                url = self._extract_url_from_onclick(onclick)
                if url and 'wsopga.me' in url and url not in target_dict:
                    title = a.get_text(strip=True) or "Free Chips"
                    logging.info(f"[WSOPExtractor] Extracted from nested onclick: {url} | Title: {title}")
                    target_dict[url] = Link(title=title, url=url, date=target_date_iso, published_date_iso=target_date_iso)

    def extract(self, html: str, date: str) -> List[Link]:
        import logging
        soup = BeautifulSoup(html, 'html.parser')
        # Use ordered dict to dedupe by href while preserving insertion order
        url_map = OrderedDict()

        # Parse the date in long format (e.g., "25 November 2025")
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%d %b %Y")
            except ValueError:
                logging.warning(f"[WSOPExtractor] Could not parse date: {date}")
                return []
        
        # Calculate yesterday's date (for late additions on source site)
        from datetime import timedelta
        yesterday_obj = date_obj - timedelta(days=1)
        
        # Generate date format variations for today and yesterday
        today_patterns = self._generate_date_patterns(date_obj)
        yesterday_patterns = self._generate_date_patterns(yesterday_obj)
        
        # Use appropriate dates: today's links get today's date, yesterday's links keep yesterday's date
        date_iso = date_obj.strftime("%Y-%m-%d")
        yesterday_iso = yesterday_obj.strftime("%Y-%m-%d")
        
        logging.info(f"[WSOPExtractor] Looking for links for TODAY ({date_obj.strftime('%d %B %Y')}) and YESTERDAY ({yesterday_obj.strftime('%d %B %Y')})")
        logging.info(f"[WSOPExtractor] Today's links will be marked with: {date_iso}")
        logging.info(f"[WSOPExtractor] Yesterday's links will be marked with: {yesterday_iso}")
        logging.debug(f"[WSOPExtractor] Today patterns: {today_patterns}")
        logging.debug(f"[WSOPExtractor] Yesterday patterns: {yesterday_patterns}")
        
        # Try new HTML structure first (h3 headings + wsop-link-block divs)
        today_links, yesterday_links, found_new_structure = self._extract_links_from_new_structure(
            soup, today_patterns, yesterday_patterns, date_iso, yesterday_iso, logging
        )
        
        if found_new_structure:
            # Combine today's links with yesterday's links
            url_map = OrderedDict()
            for href, link in today_links.items():
                url_map[href] = link
            for href, link in yesterday_links.items():
                if href not in url_map:
                    url_map[href] = link
            
            total = len(url_map)
            logging.info(f"[WSOPExtractor] Total links extracted from new structure (deduped): {total}")
            return list(url_map.values())
        
        # Fall back to old HTML structure (p > strong headings)
        logging.info("[WSOPExtractor] New structure not found, trying legacy structure...")
        
        # Debug: log all <p><strong> tags found
        all_headings = []
        for p in soup.find_all("p"):
            strong = p.find("strong")
            if strong:
                all_headings.append(strong.get_text(strip=True))
        if all_headings:
            logging.info(f"[WSOPExtractor] Found {len(all_headings)} <p><strong> headings: {all_headings[:10]}")  # Log first 10
        else:
            logging.warning(f"[WSOPExtractor] No <p><strong> headings found in HTML")

        found_today_headings = []
        found_yesterday_headings = []
        today_links = OrderedDict()
        yesterday_links = OrderedDict()
        
        # Helper to extract anchors from a tag (p, li, div, etc.)
        # The target_date_iso parameter allows us to set different dates for today vs yesterday sections
        def _extract_anchors_from_tag(tag, target_dict, target_date_iso):
            for a in tag.find_all('a', href=True):
                href = a.get('href') or ''
                if not href.startswith('http'):
                    continue
                if 'www.wsopga.me/' in href:
                    title = a.get_text(strip=True) or href
                    if href not in target_dict:
                        # If the anchor text is just the href, treat as placeholder and log at debug level
                        if title == href:
                            logging.debug(f"[WSOPExtractor] Extracted placeholder link (no title): {href}")
                        else:
                            logging.info(f"[WSOPExtractor] Extracted link: {href} | Title: {title}")
                        target_dict[href] = Link(title=title, url=href, date=date, published_date_iso=target_date_iso)
                    else:
                        # Decide if we should update existing title
                        existing = target_dict[href]
                        existing_title = str(existing.title or '')
                        # Prefer descriptive titles over href-only titles
                        if existing_title == href or existing_title.strip() == '':
                            logging.info(f"[WSOPExtractor] Updated title for {href} from '{existing_title}' to '{title}'")
                            existing.title = title
                        elif title != href and len(title) > len(existing_title):
                            logging.info(f"[WSOPExtractor] Replaced shorter title for {href} ('{existing_title}') with longer '{title}'")
                            existing.title = title
                else:
                    logging.debug(f"[WSOPExtractor] Skipped non-matching link: {href}")

        # Process all <p> tags to find today's and yesterday's sections
        for p in soup.find_all("p"):
            strong = p.find("strong")
            strong_text = strong.get_text(strip=True).rstrip(':') if strong else None
            
            # Check if this is today's heading
            if strong and strong_text in today_patterns:
                found_today_headings.append(strong_text)
                logging.info(f"[WSOPExtractor] Found TODAY's heading: {strong_text}")

                # Extract any anchors in the heading paragraph itself
                _extract_anchors_from_tag(p, today_links, date_iso)

                # Walk subsequent siblings until the next date heading
                for sibling in p.find_next_siblings():
                    if sibling.name == 'p' and sibling.find('strong'):
                        # Reached next date heading; stop
                        break
                    # Skip ad/code blocks
                    if sibling.name == 'div':
                        div_classes = ' '.join(sibling.get('class', [])).lower()
                        if 'code-block' in div_classes or 'ad' in div_classes:
                            continue
                    if sibling.name == 'ol' or sibling.name == 'ul':
                        items = sibling.find_all('li')
                        logging.info(f"[WSOPExtractor] Found {len(items)} list items in {sibling.name} after TODAY's heading")
                        for li in items:
                            _extract_anchors_from_tag(li, today_links, date_iso)
                        continue
                    if sibling.name == 'p':
                        _extract_anchors_from_tag(sibling, today_links, date_iso)
                        continue
                    # For other tags, still try to extract anchors
                    _extract_anchors_from_tag(sibling, today_links, date_iso)
            
            # Check if this is yesterday's heading
            elif strong and strong_text in yesterday_patterns:
                found_yesterday_headings.append(strong_text)
                logging.info(f"[WSOPExtractor] Found YESTERDAY's heading: {strong_text}")

                # Extract any anchors in the heading paragraph itself
                _extract_anchors_from_tag(p, yesterday_links, yesterday_iso)

                # Walk subsequent siblings until the next date heading
                for sibling in p.find_next_siblings():
                    if sibling.name == 'p' and sibling.find('strong'):
                        # Reached next date heading; stop
                        break
                    # Skip ad/code blocks
                    if sibling.name == 'div':
                        div_classes = ' '.join(sibling.get('class', [])).lower()
                        if 'code-block' in div_classes or 'ad' in div_classes:
                            continue
                    if sibling.name == 'ol' or sibling.name == 'ul':
                        items = sibling.find_all('li')
                        logging.info(f"[WSOPExtractor] Found {len(items)} list items in {sibling.name} after YESTERDAY's heading")
                        for li in items:
                            _extract_anchors_from_tag(li, yesterday_links, yesterday_iso)
                        continue
                    if sibling.name == 'p':
                        _extract_anchors_from_tag(sibling, yesterday_links, yesterday_iso)
                        continue
                    # For other tags, still try to extract anchors
                    _extract_anchors_from_tag(sibling, yesterday_links, yesterday_iso)
        
        logging.info(f"[WSOPExtractor] Found {len(today_links)} links under TODAY's section (marked with {date_iso})")
        logging.info(f"[WSOPExtractor] Found {len(yesterday_links)} links under YESTERDAY's section (marked with {yesterday_iso})")
        
        # IMPORTANT: Deduplication strategy for yesterday's links
        # - Today's links are marked with today's date (will be fingerprinted as "url|||today_iso")
        # - Yesterday's links are marked with YESTERDAY'S date (will be fingerprinted as "url|||yesterday_iso")
        # - In main.py, we check fingerprints against BOTH today and yesterday dates
        # - This ensures:
        #   1. Links already processed yesterday (fingerprint exists) are NOT added again
        #   2. NEW links added to yesterday's section (no fingerprint) ARE added with yesterday's date
        #   3. Today's new links are added with today's date
        
        # Combine today's links with yesterday's links (keeping their respective dates)
        url_map = OrderedDict()
        
        # Add today's links first (marked with date_iso)
        for href, link in today_links.items():
            url_map[href] = link
        
        # Add yesterday's links (marked with yesterday_iso for proper fingerprinting)
        for href, link in yesterday_links.items():
            if href not in url_map:  # Don't duplicate if same link appears in both sections
                url_map[href] = link
        
        if not found_today_headings and not found_yesterday_headings:
            logging.warning(f"[WSOPExtractor] No heading found for today or yesterday")
        else:
            logging.info(f"[WSOPExtractor] Found {len(found_today_headings)} TODAY heading(s): {found_today_headings}")
            logging.info(f"[WSOPExtractor] Found {len(found_yesterday_headings)} YESTERDAY heading(s): {found_yesterday_headings}")
        
        total = len(url_map)
        logging.info(f"[WSOPExtractor] Total links extracted (deduped): {total}")
        return list(url_map.values())

   