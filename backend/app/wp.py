import os
import json
import base64
import httpx
import logging
from typing import List, Optional, Dict, Any
from .models import Link

WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APPLICATION_PASSWORD = os.getenv("WP_APPLICATION_PASSWORD")
WP_SITES_JSON = os.getenv("WP_SITES")  # JSON map of site_key -> {base_url, username, app_password}


def _load_wp_sites() -> Dict[str, Dict[str, Any]]:
    """Load WP sites mapping from env var `WP_SITES` (JSON).

    Returns a dict of site_key -> site_config. Example:
    {"site_b": {"base_url": "https://siteb.com", "username": "a", "app_password": "p"}}
    """
    if not WP_SITES_JSON:
        return {}
    try:
        data = json.loads(WP_SITES_JSON)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def _resolve_wp_site(wp_site: Optional[Any]) -> Optional[Dict[str, Any]]:
    """Resolve a wp_site parameter that may be:
    - None: use environment defaults
    - dict: already a site config
    - str: a site_key referencing WP_SITES mapping
    Returns a dict or None.
    """
    if wp_site is None:
        return None
    if isinstance(wp_site, dict):
        return wp_site
    if isinstance(wp_site, str):
        sites = _load_wp_sites()
        return sites.get(wp_site)
    return None


def _auth_header(wp_site: Optional[Dict] = None) -> dict:
    """
    Generate WordPress auth header.
    
    Args:
        wp_site: Optional dict with {"base_url", "username", "app_password"}
                If not provided, uses environment variables
    """
    site = _resolve_wp_site(wp_site)
    if site:
        username = site.get("username")
        password = site.get("app_password")
        logging.info(f"[WP] Using site config for auth: base_url={site.get('base_url')}, username={username}")
    else:
        username = WP_USERNAME
        password = WP_APPLICATION_PASSWORD
        logging.info(f"[WP] Using environment for auth: base_url={WP_BASE_URL}, username={username}")
    if not username or not password:
        raise RuntimeError("WordPress credentials not set")
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def _get_wp_base_url(wp_site: Optional[Dict] = None) -> str:
    """Get WordPress base URL from site config or environment."""
    site = _resolve_wp_site(wp_site)
    if site and "base_url" in site:
        logging.info(f"[WP] Using site config for base_url: {site['base_url']}")
        return site["base_url"]
    if not WP_BASE_URL:
        raise RuntimeError("WP_BASE_URL not set")
    logging.info(f"[WP] Using environment for base_url: {WP_BASE_URL}")
    return WP_BASE_URL


def get_configured_wp_sites() -> Dict[str, Dict[str, Any]]:
    """Return configured WP sites (without exposing passwords in API responses).

    Note: This returns full configs; caller should avoid returning credentials to public consumers.
    Use carefully (we will expose only non-secret fields in API).
    """
    return _load_wp_sites()


async def update_post_links_section(post_id: int, links: List[Link], wp_site: Optional[Dict] = None) -> None:
    """
    Update WordPress post by prepending a styled 'Links for Today' section with button-style links.
    Automatically prunes sections older than 5 days to prevent content from piling up.
    
    Args:
        post_id: WordPress post ID
        links: List of links to add
        wp_site: Optional dict with WordPress site config:
                 {"base_url": "https://site.com", "username": "user", "app_password": "pass"}
                 If not provided, uses default from environment variables
    """
    base_url = _get_wp_base_url(wp_site)
    auth_headers = _auth_header(wp_site)

    # Fetch existing content
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{base_url}/wp-json/wp/v2/posts/{post_id}", headers=auth_headers)
        r.raise_for_status()
        post = r.json()
        content = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")

    from datetime import datetime, timedelta
    import pytz
    import re
    
    now = datetime.now(pytz.timezone("UTC"))
    today_date = links[0].published_date_iso if links else now.strftime("%Y-%m-%d")
    
    # Only process if we have new links to add
    if not links:
        return {
            "sections_pruned": 0,
            "links_added": 0,
            "updated": False
        }
    
    # Parse existing content to remove old "links-for-today" sections
    # Keep only sections from the last 5 days
    cutoff_date = now - timedelta(days=5)
    
    # Remove old link sections (older than 5 days)
    # Pattern: Match the complete <div class="links-for-today">...</div> section
    cleaned_content = content
    
    # Find all link sections with dates using a more robust pattern
    # The structure is: <div class="links-for-today"> -> <h4> -> <div class="wp-block-columns">...</div> -> <p>...</p> -> </div>
    # We need to match all of this as one unit
    section_pattern = r'<div class="links-for-today"[^>]*>[\s\S]*?<p[^>]*>.*?</p>\s*</div>'
    date_pattern = r'<h4[^>]*>.*?(\d{2} \w+ \d{4}).*?</h4>'  # Match "26 October 2025" even with extra tags
    
    def should_keep_section(match_text):
        """Check if a section should be kept (within last 5 days)."""
        date_match = re.search(date_pattern, match_text, re.DOTALL)
        if not date_match:
            return True  # Keep if we can't parse the date
        
        date_str = date_match.group(1)
        try:
            # Parse date like "26 October 2025"
            section_date = datetime.strptime(date_str, "%d %B %Y")
            # Compare dates (ignore time)
            return section_date.date() >= cutoff_date.date()
        except:
            return True  # Keep if parsing fails
    
    # Find and filter sections
    sections = re.finditer(section_pattern, content, re.DOTALL)
    sections_to_remove = []
    
    for match in sections:
        if not should_keep_section(match.group(0)):
            sections_to_remove.append(match.group(0))
    
    # Remove old sections
    for old_section in sections_to_remove:
        cleaned_content = cleaned_content.replace(old_section, '', 1)
    
    # Create styled buttons grouped in pairs (2 buttons per column block)
    column_blocks = []
    
    for i in range(0, len(links), 2):
        # Get 2 links at a time
        pair = links[i:i+2]
        
        # Create button HTML for this pair
        buttons_in_pair = []
        for j, link in enumerate(pair, start=i+1):
            button_html = f'''<div class="wp-block-column is-layout-flow wp-block-column-is-layout-flow" style="flex-basis:50%">
    <div style="margin: 15px 0;">
        <a href="{link.url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 15px 30px; border: 3px solid #ff216d; border-radius: 15px; background-color: white; color: #ff216d; text-decoration: none; font-size: 18px; font-weight: bold; text-align: center; transition: all 0.3s; width: 100%; box-sizing: border-box;" onmouseover="this.style.borderColor='#42a2f6'; this.style.color='#42a2f6';" onmouseout="this.style.borderColor='#ff216d'; this.style.color='#ff216d';">{j:02d}. {link.title}</a>
    </div>
</div>'''
            buttons_in_pair.append(button_html)
        
        # Create a column block for this pair
        column_block = f'''<div class="wp-block-columns is-layout-flex wp-block-columns-is-layout-flex" style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 10px;">
{chr(10).join(buttons_in_pair)}
</div>'''
        column_blocks.append(column_block)
    
    buttons_html = "\n".join(column_blocks)
    
    # Format today's date nicely
    try:
        date_obj = datetime.strptime(today_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d %B %Y")  # "26 October 2025"
    except:
        formatted_date = today_date
    
    new_section = f'''
<div class="links-for-today" style="padding: 20px; margin: 20px 0;">
<h4 style="color: #30d612; margin-top: 0; font-size: 20px; text-align: center;">{formatted_date}</h4>
{buttons_html}
<p style="font-size: 12px; color: #999; margin-top: 20px; margin-bottom: 0;"><em>Last updated: {now.strftime("%Y-%m-%d %H:%M:%S")} UTC</em></p>
</div>
'''
    new_content = new_section + cleaned_content
    
    # Update the post
    payload = {"content": new_content}

    # Update the post
    import json
    logging.info(f"[WP] Updating post {post_id} at {base_url}/wp-json/wp/v2/posts/{post_id}")
    logging.info(f"[WP] Payload: {json.dumps(payload)[:500]} ...")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{base_url}/wp-json/wp/v2/posts/{post_id}",
            headers={"Content-Type": "application/json", **auth_headers},
            json=payload,
        )
        logging.info(f"[WP] Response status: {r.status_code}")
        logging.info(f"[WP] Response body: {r.text[:500]} ...")
        r.raise_for_status()
    
    # Return info about what happened
    return {
        "sections_pruned": len(sections_to_remove),
        "links_added": len(links),
        "updated": True
    }
