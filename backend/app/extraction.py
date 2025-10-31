from bs4 import BeautifulSoup
from typing import List
from .models import Link


def extract_links_with_heading_filter(html: str, today_iso: str) -> List[Link]:
    """Fallback deterministic extractor for sections labeled 'links for today' or today's date."""
    soup = BeautifulSoup(html, "html.parser")
    anchors: List[Link] = []
    
    # Normalize match terms
    match_terms = {"links for today", today_iso.lower()}
    
    # Add various date formats for matching
    from datetime import datetime
    try:
        dt = datetime.strptime(today_iso, "%Y-%m-%d")
        match_terms.add(dt.strftime("%d %B %Y").lower())  # "26 October 2025"
        match_terms.add(dt.strftime("%B %d, %Y").lower())  # "October 26, 2025"
        match_terms.add(dt.strftime("%b %d, %Y").lower())  # "Oct 26, 2025"
        match_terms.add(dt.strftime("%b %d").lower())  # "Oct 26"
        match_terms.add(dt.strftime("%-d %b").lower())  # "26 Oct" (Linux)
        match_terms.add(dt.strftime("%d %b").lower())  # "26 Oct"
    except ValueError:
        pass
    
    # Helper to check if URL is likely a reward/gift link (not navigation)
    def is_reward_link(url: str) -> bool:
        url_lower = url.lower()
        
        # EXCLUDE first - these are definitely NOT reward links
        exclude_keywords = ['about', 'contact', 'privacy', 'terms', 'policy', 'disclaimer', 
                           'disclosure', 'previous', 'next', 'category', 'tag', 'author',
                           '/page/', 'facebook.com', 'twitter.com', 'instagram.com',
                           'pinterest.com', 'youtube.com', 'linkedin.com']
        
        if any(keyword in url_lower for keyword in exclude_keywords):
            return False
        
        # Must be from a known rewards domain OR have specific reward keywords
        reward_domains = ['rewards.coinmaster.com', 'rewards.', 'gift', 'promo', 'bonus']
        reward_keywords = ['reward', 'spin', 'coin', 'bonus', 'gift', 'promo', 'free']
        
        # If it's a rewards domain, it's definitely a reward link
        if any(domain in url_lower for domain in reward_domains):
            return True
        
        # Or if it has reward keywords AND query params (like ?c=...)
        has_reward_keyword = any(keyword in url_lower for keyword in reward_keywords)
        has_query_params = '?' in url
        
        return has_reward_keyword and has_query_params

    # Strategy 1: Find date in strong tags specifically (like: <strong>Oct 26, 2025:</strong>)
    # First try strong tags (most specific)
    for strong_tag in soup.find_all('strong'):
        text = (strong_tag.get_text() or "").strip().lower()
        
        # Check if this strong tag contains today's date AND is short (not a giant container)
        if any(term in text for term in match_terms) and len(text) < 50:
            # Found today's date! Now collect links from siblings until next date
            
            current = strong_tag.parent if strong_tag.parent else strong_tag
            next_elem = current.find_next_sibling()
            
            # Process siblings until we hit another date header
            while next_elem:
                # Check if this element or its children contain another date header
                elem_text = next_elem.get_text().strip().lower()
                
                # Look for date patterns in this element
                has_date_header = False
                
                # Check all strong tags in this element
                for strong in next_elem.find_all('strong'):
                    strong_text = strong.get_text().strip()
                    # Check if it matches any of our OTHER date patterns (not today)
                    try:
                        # Try to parse as a date
                        from datetime import datetime
                        # Common patterns: "Oct 25, 2025", "25 Oct 2025", etc.
                        for pattern in ["%b %d, %Y", "%d %b, %Y", "%B %d, %Y", "%d %B, %Y", "%b %d", "%d %b"]:
                            try:
                                parsed = datetime.strptime(strong_text.strip(':').strip(), pattern)
                                # If we successfully parsed a date, and it's NOT today, stop
                                if strong_text.strip().lower() not in match_terms:
                                    has_date_header = True
                                    break
                            except ValueError:
                                continue
                        if has_date_header:
                            break
                    except:
                        pass
                
                if has_date_header:
                    break  # Stop - we've reached the next day's section
                
                # Extract data-link attributes from this element
                for data_link_div in next_elem.find_all('div', attrs={'data-link': True}):
                    link_url = data_link_div.get('data-link')
                    if not link_url:
                        continue
                    
                    span = data_link_div.find('span')
                    title = span.get_text().strip() if span else link_url
                    
                    try:
                        anchors.append(
                            Link(
                                url=link_url,
                                title=title,
                                published_date_iso=today_iso,
                                summary=None,
                                category=None,
                            )
                        )
                    except Exception:
                        continue
                
                # Also check regular <a> tags (with filtering)
                for link_tag in next_elem.find_all("a", href=True):
                    href = link_tag.get("href")
                    if not href or href.startswith('#') or href.startswith('javascript:'):
                        continue
                    
                    if not is_reward_link(href):
                        continue
                    
                    try:
                        anchors.append(
                            Link(
                                url=href,
                                title=link_tag.get_text().strip() or href,
                                published_date_iso=today_iso,
                            )
                        )
                    except Exception:
                        continue
                
                next_elem = next_elem.find_next_sibling()
            
            # Found and processed today's section, stop
            break

    # Strategy 2: Traditional heading-based extraction (for other sites)
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = (heading.get_text() or "").strip().lower()
        if any(term in text for term in match_terms):
            for sibling in heading.find_all_next():
                if sibling.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    break
                if sibling.name == "a" and sibling.get("href"):
                    anchors.append(
                        Link(
                            url=sibling["href"],
                            title=sibling.get_text().strip() or sibling["href"],
                            published_date_iso=today_iso,
                            summary=None,
                            category=None,
                        )
                    )
                for link_tag in sibling.find_all("a"):
                    href = link_tag.get("href")
                    if not href or href.startswith('#') or href.startswith('javascript:'):
                        continue
                    try:
                        anchors.append(
                            Link(
                                url=href,
                                title=link_tag.get_text().strip() or href,
                                published_date_iso=today_iso,
                            )
                        )
                    except Exception:
                        # Skip malformed URLs
                        continue
    
    return anchors
