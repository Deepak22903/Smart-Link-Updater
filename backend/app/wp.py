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
    Update WordPress post by inserting a styled 'Links for Today' section using proper WordPress block format.
    
    **Robust Block-Based Insertion:**
    - Uses proper WordPress block comments (<!-- wp:group -->, <!-- wp:columns -->, etc.)
    - Creates a unique block with className "smartlink-updater-section" for easy identification
    - Only modifies the SmartLink block, leaving other content and plugin elements untouched
    - Replaces existing SmartLink block if found, otherwise inserts after first <h2>
    - Backward compatible with old div-based format (will upgrade to block format)
    
    **Automatic Cleanup:**
    - Automatically prunes sections older than 5 days to prevent content from piling up
    - Preserves existing links from today's section when adding new links
    
    **Insertion Logic:**
    1. If SmartLink block exists → Replace it with updated content
    2. If not found → Insert after first <h2> block
    3. Fallback → Prepend to content (rare case)
    
    Args:
        post_id: WordPress post ID
        links: List of links to add
        wp_site: Optional dict with WordPress site config:
                 {"base_url": "https://site.com", "username": "user", "app_password": "pass"}
                 If not provided, uses default from environment variables
    """
    base_url = _get_wp_base_url(wp_site)
    auth_headers = _auth_header(wp_site)

    # Fetch existing content with increased timeout for WordPress
    timeout = httpx.Timeout(30.0, connect=10.0)  # 30s read, 10s connect
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{base_url}/wp-json/wp/v2/posts/{post_id}", headers=auth_headers)
        r.raise_for_status()
        post = r.json()
        content = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")
    
    # DEBUG: Save content to file for analysis
    try:
        with open(f"/tmp/wp_post_{post_id}_content.txt", "w") as f:
            f.write(content)
        logging.info(f"[WP DEBUG] Saved post {post_id} content to /tmp/wp_post_{post_id}_content.txt")
    except Exception as e:
        logging.warning(f"[WP DEBUG] Failed to save content: {e}")

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
    
    # Format today's date nicely
    try:
        # Handle both "YYYY-MM-DD" and "YYYY-MM-DDTHH:MM:SS" formats
        if 'T' in today_date:
            date_obj = datetime.strptime(today_date.split('T')[0], "%Y-%m-%d")
        else:
            date_obj = datetime.strptime(today_date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d %B %Y")  # "10 November 2025"
    except Exception as e:
        print(f"Error parsing date '{today_date}': {e}")
        formatted_date = today_date
    
    # Remove old link sections (older than 5 days) and check if today's section exists
    cleaned_content = content
    today_section_exists = False
    today_section_content = ""
    
    # Find all link sections with dates using patterns for both old and new formats
    # Pattern 1: New WordPress block format - NOTE: WordPress strips block comments from raw content
    # Match from outer div with smartlink-updater-section to the "Last updated" timestamp paragraph and closing tags
    # This is more reliable than trying to match nested divs
    new_block_pattern = r'<div class="wp-block-group smartlink-updater-section[^>]*>.*?<p class="has-text-color"[^>]*>.*?Last updated:.*?</p>\s*</div>\s*</div>'
    # Pattern 2: Old div-based format (for backward compatibility)
    old_section_pattern = r'<div class="links-for-today"[^>]*>[\s\S]*?<p[^>]*>.*?</p>\s*</div>'
    # Date pattern works for both formats
    date_pattern = r'<h4[^>]*>.*?(\d{2} \w+ \d{4}).*?</h4>'
    
    def should_keep_section(match_text, section_date_str):
        """Check if a section should be kept (within last 5 days)."""
        # Check if this is today's section
        if section_date_str == formatted_date:
            return False  # We'll rebuild today's section with new links
        
        try:
            # Parse date like "26 October 2025"
            section_date = datetime.strptime(section_date_str, "%d %B %Y")
            # Compare dates (ignore time)
            return section_date.date() >= cutoff_date.date()
        except:
            return True  # Keep if parsing fails
    
    # Find and filter sections (check both new block format and old format)
    sections_to_remove = []
    existing_links = []
    
    logging.info(f"[WP DEBUG] Searching for sections with patterns:")
    logging.info(f"[WP DEBUG]   - New block pattern: {new_block_pattern[:100]}...")
    logging.info(f"[WP DEBUG]   - Old section pattern: {old_section_pattern[:100]}...")
    logging.info(f"[WP DEBUG]   - Content length: {len(content)} chars")
    logging.info(f"[WP DEBUG]   - Looking for today's date: {formatted_date}")
    
    # Check new block format first
    new_block_matches = list(re.finditer(new_block_pattern, content, re.DOTALL))
    logging.info(f"[WP DEBUG] Found {len(new_block_matches)} matches with new_block_pattern")
    
    for match in new_block_matches:
        section_text = match.group(0)
        date_match = re.search(date_pattern, section_text, re.DOTALL)
        
        if date_match:
            section_date_str = date_match.group(1)
            
            # Check if this is today's section
            if section_date_str == formatted_date:
                today_section_exists = True
                # Extract existing links from today's section to avoid duplicates
                link_pattern = r'<a href="([^"]+)"[^>]*>(\d+)\.\s*([^<]+)</a>'
                for link_match in re.finditer(link_pattern, section_text):
                    existing_links.append({
                        'url': link_match.group(1),
                        'title': link_match.group(3).strip()
                    })
                sections_to_remove.append((match.start(), match.end(), section_text))
            elif not should_keep_section(section_text, section_date_str):
                sections_to_remove.append((match.start(), match.end(), section_text))
    
    # Also check old format for backward compatibility
    old_format_matches = list(re.finditer(old_section_pattern, content, re.DOTALL))
    logging.info(f"[WP DEBUG] Found {len(old_format_matches)} matches with old_section_pattern")
    
    for match in old_format_matches:
        section_text = match.group(0)
        date_match = re.search(date_pattern, section_text, re.DOTALL)
        
        if date_match:
            section_date_str = date_match.group(1)
            
            # Check if this is today's section
            if section_date_str == formatted_date:
                if not today_section_exists:  # Only process if not already found in new format
                    today_section_exists = True
                    # Extract existing links
                    link_pattern = r'<a href="([^"]+)"[^>]*>(\d+)\.\s*([^<]+)</a>'
                    for link_match in re.finditer(link_pattern, section_text):
                        existing_links.append({
                            'url': link_match.group(1),
                            'title': link_match.group(3).strip()
                        })
                sections_to_remove.append((match.start(), match.end(), section_text))
            elif not should_keep_section(section_text, section_date_str):
                sections_to_remove.append((match.start(), match.end(), section_text))
    
    # Log what we found
    logging.info(f"[WP] Found {len(sections_to_remove)} sections to remove")
    logging.info(f"[WP] Today's section exists: {today_section_exists}, existing links: {len(existing_links)}")
    
    # Remove old sections and today's section (we'll recreate it with all links)
    # Sort by position (reverse order to maintain correct positions during removal)
    sections_to_remove.sort(key=lambda x: x[0], reverse=True)
    for start, end, section_text in sections_to_remove:
        # Log each section being removed
        date_match = re.search(date_pattern, section_text, re.DOTALL)
        section_date = date_match.group(1) if date_match else "unknown date"
        logging.info(f"[WP] Removing section with date: {section_date} at position {start}-{end}")
        cleaned_content = cleaned_content[:start] + cleaned_content[end:]
    
    # Merge new links with existing links from today (avoid duplicates)
    all_links_map = {}  # Use dict to track by URL
    
    # Add existing links from today
    for idx, existing_link in enumerate(existing_links, start=1):
        all_links_map[existing_link['url']] = {
            'url': existing_link['url'],
            'title': existing_link['title'],
            'order': idx
        }
    
    # Add new links (skip duplicates)
    for link in links:
        if link.url not in all_links_map:
            all_links_map[link.url] = {
                'url': link.url,
                'title': link.title,
                'order': len(all_links_map) + 1
            }
    
    # Convert back to list and sort by order
    merged_links = sorted(all_links_map.values(), key=lambda x: x['order'])
    
    # Create styled buttons grouped in pairs (2 buttons per column block)
    # Using proper WordPress block format with block comments
    column_blocks = []
    
    for i in range(0, len(merged_links), 2):
        # Get 2 links at a time
        pair = merged_links[i:i+2]
        
        # Create button HTML for this pair
        buttons_in_pair = []
        for link in pair:
            button_html = f'''<!-- wp:column {{"width":"50%"}} -->
<div class="wp-block-column" style="flex-basis:50%">
    <div style="margin: 15px 0;">
        <a href="{link['url']}" target="_blank" rel="noopener noreferrer" style="display: inline-block; padding: 15px 30px; border: 3px solid #ff216d; border-radius: 15px; background-color: white; color: #ff216d; text-decoration: none; font-size: 18px; font-weight: bold; text-align: center; transition: all 0.3s; width: 100%; box-sizing: border-box;" onmouseover="this.style.borderColor='#42a2f6'; this.style.color='#42a2f6';" onmouseout="this.style.borderColor='#ff216d'; this.style.color='#ff216d';">{link['order']:02d}. {link['title']}</a>
    </div>
</div>
<!-- /wp:column -->'''
            buttons_in_pair.append(button_html)
        
        # Create a column block for this pair with proper block comments
        column_block = f'''<!-- wp:columns -->
<div class="wp-block-columns">
{chr(10).join(buttons_in_pair)}
</div>
<!-- /wp:columns -->'''
        column_blocks.append(column_block)
    
    buttons_html = "\n".join(column_blocks)
    
    # Create a proper WordPress group block that wraps our links section
    # This ensures the entire section is treated as a single block
    new_section = f'''<!-- wp:group {{"className":"smartlink-updater-section","metadata":{{"name":"SmartLink Links Section"}}}} -->
<div class="wp-block-group smartlink-updater-section links-for-today" style="padding: 20px; margin: 20px 0;">
<!-- wp:heading {{"level":4,"style":{{"color":{{"text":"#30d612"}},"typography":{{"fontSize":"20px"}}}},"textAlign":"center"}} -->
<h4 class="wp-block-heading has-text-align-center" style="color:#30d612;font-size:20px">{formatted_date}</h4>
<!-- /wp:heading -->

{buttons_html}

<!-- wp:paragraph {{"style":{{"typography":{{"fontSize":"12px"}},"color":{{"text":"#999"}}}}}} -->
<p class="has-text-color" style="color:#999;font-size:12px"><em>Last updated: {now.strftime("%Y-%m-%d %H:%M:%S")} UTC</em></p>
<!-- /wp:paragraph -->
</div>
<!-- /wp:group -->'''
    
    # ROBUST INSERTION LOGIC:
    # 1. Find our existing SmartLink block if it exists
    # 2. If found, replace only that block
    # 3. If not found, insert after first H2 block
    # 4. This ensures we don't break other plugin content
    
    # Use the same pattern - match to the "Last updated" timestamp as anchor
    smartlink_block_pattern = r'<div class="wp-block-group smartlink-updater-section[^>]*>.*?<p class="has-text-color"[^>]*>.*?Last updated:.*?</p>\s*</div>\s*</div>'
    existing_block_match = re.search(smartlink_block_pattern, cleaned_content, re.DOTALL)
    
    if existing_block_match:
        # Replace existing SmartLink block
        new_content = cleaned_content[:existing_block_match.start()] + new_section + cleaned_content[existing_block_match.end():]
        logging.info(f"[WP] Replaced existing SmartLink block")
    else:
        # Insert after first H2 block (WordPress heading block)
        # Look for either block comment format or plain H2
        h2_block_pattern = r'(<!-- wp:heading.*?-->.*?<h2[^>]*>.*?</h2>.*?<!-- /wp:heading -->|<h2[^>]*>.*?</h2>)'
        h2_match = re.search(h2_block_pattern, cleaned_content, re.DOTALL | re.IGNORECASE)
        
        if h2_match:
            # Insert after the first H2 block
            h2_end = h2_match.end()
            new_content = cleaned_content[:h2_end] + "\n\n" + new_section + "\n\n" + cleaned_content[h2_end:]
            logging.info(f"[WP] Inserted SmartLink block after first <h2> block")
        else:
            # Fallback: prepend to content (rare case)
            new_content = new_section + "\n\n" + cleaned_content
            logging.warning(f"[WP] No <h2> block found, prepending SmartLink block to beginning")
    
    # Update the post
    payload = {"content": new_content}

    # Update the post with increased timeout for WordPress
    import json
    timeout = httpx.Timeout(60.0, connect=10.0)  # 60s read for POST (can be slow), 10s connect
    logging.info(f"[WP] Updating post {post_id} at {base_url}/wp-json/wp/v2/posts/{post_id}")
    logging.info(f"[WP] Payload: {json.dumps(payload)[:500]} ...")
    async with httpx.AsyncClient(timeout=timeout) as client:
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
        "total_links_in_section": len(merged_links),
        "existing_links_preserved": len(existing_links),
        "new_links_added": len([url for url in [link.url for link in links] if url not in [el['url'] for el in existing_links]]),
        "section_updated": today_section_exists,
        "updated": True
    }
