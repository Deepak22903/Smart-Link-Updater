"""
Extractor for CoinsCrazy.com
Extracts daily links from dated sections with button-style links.
"""

import re
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup, Tag
from .base import BaseExtractor, DailyLinks, register_extractor


@register_extractor("coinscrazy")
class CoinsCrazyExtractor(BaseExtractor):
    """Extract links from CoinsCrazy.com daily reward sections."""
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the given URL."""
        return "coinscrazy.com" in url.lower()
    
    def extract(self, html: str, url: str, target_date: datetime) -> Optional[DailyLinks]:
        """
        Extract links from the daily section matching target_date.
        
        HTML structure:
        - h4 with date like "Updated On: 06 February 2026"
        - Multiple wp-block-columns divs with button links
        - Links are in <a> tags within ub-button-container divs
        - Button text is in <span class="ub-button-block-btn">
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Format target date to match site format: "06 February 2026"
        target_date_str = target_date.strftime("%d %B %Y")
        
        # Also try "Updated On: DD Month YYYY" format
        updated_on_str = f"Updated On: {target_date_str}"
        
        # Find all h4 headings
        h4_tags = soup.find_all('h4', class_='wp-block-heading')
        
        target_h4 = None
        for h4 in h4_tags:
            h4_text = h4.get_text(strip=True)
            # Match both "Updated On: 06 February 2026" and "06 February 2026" formats
            if updated_on_str in h4_text or target_date_str in h4_text:
                target_h4 = h4
                break
        
        if not target_h4:
            self.logger.warning(f"No h4 found for date: {target_date_str}")
            return None
        
        # Collect all links after this h4 until the next h4 date header
        links = []
        current_element = target_h4.find_next_sibling()
        
        while current_element:
            # Stop if we hit another h4 heading (next date section)
            if current_element.name == 'h4' and 'wp-block-heading' in current_element.get('class', []):
                break
            
            # Extract links from wp-block-columns divs
            if current_element.name == 'div' and 'wp-block-columns' in current_element.get('class', []):
                # Find all anchor tags within this columns div
                anchors = current_element.find_all('a', href=True)
                
                for anchor in anchors:
                    href = anchor.get('href', '').strip()
                    
                    # Skip empty or invalid links
                    if not href or href.startswith('#') or href == '':
                        continue
                    
                    # Extract button text from span
                    button_span = anchor.find('span', class_='ub-button-block-btn')
                    button_text = button_span.get_text(strip=True) if button_span else None
                    
                    # If we have button text, use it as custom title
                    if button_text:
                        links.append({
                            'url': href,
                            'custom_title': button_text
                        })
                    else:
                        links.append({'url': href})
                    
                    self.logger.debug(f"Extracted link: {href} with title: {button_text}")
            
            current_element = current_element.find_next_sibling()
        
        if not links:
            self.logger.warning(f"No links found for date: {target_date_str}")
            return None
        
        self.logger.info(f"Found {len(links)} links for {target_date_str}")
        
        # Format display date to match site style
        display_date = target_date.strftime("%d %B %Y")
        
        return DailyLinks(
            date=target_date,
            date_display=display_date,
            links=links
        )
