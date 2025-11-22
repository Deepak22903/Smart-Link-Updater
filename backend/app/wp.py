import os
import json
import base64
import httpx
import asyncio
import logging
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from .models import Link

WP_BASE_URL = os.getenv("WP_BASE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APPLICATION_PASSWORD = os.getenv("WP_APPLICATION_PASSWORD")
WP_SITES_JSON = os.getenv("WP_SITES")  # JSON map of site_key -> {base_url, username, app_password}


def get_link_target(url: str) -> str:
    """
    Determine whether a link should open in a new tab or same tab.
    
    Default: _blank (new tab) for external reward links
    Override: _self (same tab) for specific patterns
    
    Customize this function based on your requirements.
    Examples:
    - telegram.org or t.me links -> _self (same tab)
    - All others -> _blank (new tab)
    """
    url_lower = str(url).lower()
    
    # Add patterns here for links that should open in same tab
    same_tab_patterns = [
        # Example: 't.me/', 'telegram.org'
    ]
    
    for pattern in same_tab_patterns:
        if pattern in url_lower:
            return '_self'
    
    # Default: open in new tab
    return '_blank'


def _load_wp_sites() -> Dict[str, Dict[str, Any]]:
    """Load WP sites mapping from config file or env var `WP_SITES` (JSON).

    Returns a dict of site_key -> site_config. Example:
    {"site_b": {"base_url": "https://siteb.com", "username": "a", "app_password": "p"}}
    """
    # Priority 1: Check for config file (dynamic updates)
    config_file = "/tmp/wp_sites_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    logging.debug(f"[WP] Loaded sites from {config_file}")
                    return data
        except Exception as e:
            logging.error(f"[WP] Failed to load sites from {config_file}: {e}")
    
    # Priority 2: Fallback to environment variable
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


async def update_post_links_section(post_id: int, links: List[Link], wp_site: Optional[Dict] = None, post_config: Optional[Dict] = None) -> None:
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
        post_config: Optional post configuration dict containing ad_codes and other settings
    """
    base_url = _get_wp_base_url(wp_site)
    auth_headers = _auth_header(wp_site)

    # Fetch existing content with increased timeout for WordPress
    # Use longer timeouts and add retry logic for unstable connections
    timeout = httpx.Timeout(30.0, connect=20.0)  # 30s read, 20s connect (increased from 10s)
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.get(f"{base_url}/wp-json/wp/v2/posts/{post_id}", headers=auth_headers)
                r.raise_for_status()
                post = r.json()
                content = post.get("content", {}).get("raw") or post.get("content", {}).get("rendered", "")
                break  # Success, exit retry loop
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 2s, 4s, 6s
                logging.warning(f"[WP] Timeout on attempt {attempt + 1}/{max_retries} for GET post {post_id}: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"[WP] Failed to GET post {post_id} after {max_retries} attempts: {e}")
                raise HTTPException(status_code=504, detail=f"WordPress connection timeout after {max_retries} attempts")
        except httpx.HTTPStatusError as e:
            logging.error(f"[WP] HTTP error getting post {post_id}: {e}")
            raise
        except Exception as e:
            logging.error(f"[WP] Unexpected error getting post {post_id}: {e}")
            raise
    
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
    # Keep only sections from the last 5 days (including today = days 0-4)
    cutoff_date = now - timedelta(days=4)  # Changed from 5 to 4 to get exactly 5 days
    
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
            logging.info(f"[WP PRUNING] Section '{section_date_str}' is today - will be rebuilt")
            return False  # We'll rebuild today's section with new links
        
        try:
            # Parse date like "26 October 2025"
            section_date = datetime.strptime(section_date_str, "%d %B %Y")
            days_old = (now.date() - section_date.date()).days
            should_keep = section_date.date() >= cutoff_date.date()
            
            if should_keep:
                logging.info(f"[WP PRUNING] KEEPING section '{section_date_str}' ({days_old} days old)")
            else:
                logging.info(f"[WP PRUNING] REMOVING section '{section_date_str}' ({days_old} days old - older than 5 days)")
            
            return should_keep
        except Exception as e:
            logging.warning(f"[WP PRUNING] Failed to parse date '{section_date_str}': {e} - keeping section")
            return True  # Keep if parsing fails
    
    # Find and filter sections (check both new block format and old format)
    sections_to_remove = []
    existing_links = []
    
    # Check new block format first
    new_block_matches = list(re.finditer(new_block_pattern, content, re.DOTALL))
    
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
    
    # Remove old sections and today's section (we'll recreate it with all links)
    if sections_to_remove:
        logging.info(f"[WP] Removing {len(sections_to_remove)} old sections (keeping last 5 days)")
    
    # Sort by position (reverse order to maintain correct positions during removal)
    sections_to_remove.sort(key=lambda x: x[0], reverse=True)
    for start, end, section_text in sections_to_remove:
        cleaned_content = cleaned_content[:start] + cleaned_content[end:]
    
    # Merge new links with existing links from today (avoid duplicates)
    # New links are inserted BEFORE existing links
    all_links_map = {}  # Use dict to track by URL
    
    # Add new links FIRST (they'll have lower order numbers)
    for idx, link in enumerate(links, start=1):
        url = str(link.url)
        if url not in all_links_map:
            # Get target from link object or determine from URL
            target = getattr(link, 'target', None) or get_link_target(url)
            all_links_map[url] = {
                'url': url,
                'title': link.title,
                'target': target,
                'order': idx
            }
    
    # Add existing links AFTER new links (skip duplicates)
    next_order = len(all_links_map) + 1
    for existing_link in existing_links:
        url = existing_link['url']
        if url not in all_links_map:
            all_links_map[url] = {
                'url': url,
                'title': existing_link['title'],
                'target': get_link_target(url),  # Determine target based on URL
                'order': next_order
            }
            next_order += 1
    
    # Convert back to list and sort by order
    merged_links = sorted(all_links_map.values(), key=lambda x: x['order'])
    
    # Update targets: all links open in same tab (_self) except the last one (_blank)
    total_links = len(merged_links)
    for idx, link in enumerate(merged_links):
        if idx == total_links - 1:
            # Last link opens in new tab
            link['target'] = '_blank'
        else:
            # All other links open in same tab
            link['target'] = '_self'
    
    # Create styled buttons grouped in threes (3 buttons per column block)
    # Using proper WordPress block format with block comments
    column_blocks = []
    
    for i in range(0, len(merged_links), 3):
        # Get 3 links at a time
        group = merged_links[i:i+3]
        
        # Create button HTML for this group
        buttons_in_group = []
        for link in group:
            # Get target attribute (default to _blank for new tab)
            target = link.get('target', '_blank')
            rel_attr = ' rel="noopener noreferrer"' if target == '_blank' else ''
            
            button_html = f'''<!-- wp:column {{"width":"33.33%"}} -->
<div class="wp-block-column" style="flex-basis:33.33%">
    <div style="margin: 15px 0;">
        <a href="{link['url']}" target="{target}"{rel_attr} style="display: inline-block; padding: 15px 30px; border: 3px solid #ff216d; border-radius: 15px; background-color: white; color: #ff216d; text-decoration: none; font-size: 18px; font-weight: bold; text-align: center; transition: all 0.3s; width: 100%; box-sizing: border-box;" onmouseover="this.style.borderColor='#42a2f6'; this.style.color='#42a2f6';" onmouseout="this.style.borderColor='#ff216d'; this.style.color='#ff216d';">{link['order']:02d}. {link['title']}</a>
    </div>
</div>
<!-- /wp:column -->'''
            buttons_in_group.append(button_html)
        
        # Create a column block for this group with proper block comments
        column_block = f'''<!-- wp:columns -->
<div class="wp-block-columns">
{chr(10).join(buttons_in_group)}
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
    # 1. Find our existing SmartLink blocks if they exist
    # 2. Insert new section after the first H2 (it becomes the top/newest section)
    # 3. Old sections remain below (they were already pruned)
    
    # Use the same pattern - match to the "Last updated" timestamp as anchor
    smartlink_block_pattern = r'<div class="wp-block-group smartlink-updater-section[^>]*>.*?<p class="has-text-color"[^>]*>.*?Last updated:.*?</p>\s*</div>\s*</div>'
    
    # REMOVE OLD AD CODES FIRST (before inserting new sections)
    # Pattern to match ad code blocks inserted by our system
    # Match with flexible whitespace and line breaks
    # Pattern 1: Standard format with wp:html block
    ad_code_pattern_1 = r'<!--\s*wp:html\s*-->\s*<div\s+class="smartlink-ad-placement"[^>]*>.*?</div>\s*<!--\s*/wp:html\s*-->'
    # Pattern 2: In case WordPress adds extra formatting
    ad_code_pattern_2 = r'<div\s+class="smartlink-ad-placement"[^>]*>.*?</div>'
    
    # Log ad_codes configuration
    configured_ad_codes = post_config.get('ad_codes', []) if post_config else []
    
    # Try both patterns
    existing_ad_matches = []
    
    # Try pattern 1 (with wp:html blocks)
    matches_p1 = list(re.finditer(ad_code_pattern_1, cleaned_content, re.DOTALL | re.IGNORECASE))
    existing_ad_matches.extend(matches_p1)
    
    # Try pattern 2 (just the div) - but only if pattern 1 didn't match
    if not matches_p1:
        matches_p2 = list(re.finditer(ad_code_pattern_2, cleaned_content, re.DOTALL | re.IGNORECASE))
        existing_ad_matches.extend(matches_p2)
    
    if len(existing_ad_matches) > 0:
        # Remove using the appropriate pattern
        if matches_p1:
            cleaned_content = re.sub(ad_code_pattern_1, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
        else:
            cleaned_content = re.sub(ad_code_pattern_2, '', cleaned_content, flags=re.DOTALL | re.IGNORECASE)
        
        logging.info(f"[WP] Removed {len(existing_ad_matches)} existing ad code blocks")
        
        # Verify removal - check both patterns
        remaining_ads_p1 = list(re.finditer(ad_code_pattern_1, cleaned_content, re.DOTALL | re.IGNORECASE))
        remaining_ads_p2 = list(re.finditer(ad_code_pattern_2, cleaned_content, re.DOTALL | re.IGNORECASE))
        total_remaining = len(remaining_ads_p1) + len(remaining_ads_p2)
        
        if total_remaining > 0:
            logging.warning(f"[WP] WARNING: {total_remaining} ad blocks still remain after removal!")
    
    # Check if any SmartLink sections exist
    existing_sections = list(re.finditer(smartlink_block_pattern, cleaned_content, re.DOTALL))
    
    if existing_sections:
        # Insert new section before the first existing section (at the top)
        first_section = existing_sections[0]
        new_content = cleaned_content[:first_section.start()] + new_section + "\n\n" + cleaned_content[first_section.start():]
        logging.info(f"[WP] Inserted new SmartLink section before existing sections")
    else:
        # No SmartLink sections exist, insert after first H2 block (WordPress heading block)
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
    
    # Insert ad codes if configured
    ad_codes = post_config.get('ad_codes', []) if post_config else []
    
    if ad_codes and isinstance(ad_codes, list):
        logging.info(f"[WP] Inserting {len(ad_codes)} ad codes")
        
        # Find all sections in the content to determine insertion points
        all_sections = list(re.finditer(smartlink_block_pattern, new_content, re.DOTALL))
        
        # Process ad codes in reverse order to maintain correct positions
        ad_codes_sorted = sorted(ad_codes, key=lambda x: x.get('position', 'after_today'), reverse=True)
        
        for ad_code_config in ad_codes_sorted:
            position = ad_code_config.get('position', 'after_today')
            code = ad_code_config.get('code', '')
            
            if not code:
                continue
            
            # Determine which section to insert after based on position
            # after_today = after 1st section (index 0)
            # after_1_day = after 2nd section (index 1)
            # after_2_days = after 3rd section (index 2), etc.
            section_index = 0
            if position == 'after_today':
                section_index = 0
            elif position == 'after_1_day':
                section_index = 1
            elif position == 'after_2_days':
                section_index = 2
            elif position == 'after_3_days':
                section_index = 3
            elif position == 'after_4_days':
                section_index = 4
            elif position == 'after_5_days':
                section_index = 5
            elif position == 'after_6_days':
                section_index = 6
            
            # Check if section exists
            if section_index < len(all_sections):
                section = all_sections[section_index]
                # Insert after this section
                insertion_point = section.end()
                
                # Wrap ad code in a div with class for styling
                ad_html = f'''
<!-- wp:html -->
<div class="smartlink-ad-placement" style="margin: 20px 0; padding: 20px; text-align: center; background-color: #f8f9fa;">
{code}
</div>
<!-- /wp:html -->
'''
                
                new_content = new_content[:insertion_point] + ad_html + new_content[insertion_point:]
                logging.info(f"[WP] Inserted ad after section {section_index} ({position})")
                
                # Re-find sections after insertion (positions have changed)
                all_sections = list(re.finditer(smartlink_block_pattern, new_content, re.DOTALL))
            else:
                logging.warning(f"[WP] Cannot insert ad at position {position} - section {section_index} not found")
    
    # Update the post
    payload = {"content": new_content}

    # Update the post with increased timeout and retry logic for WordPress
    import json
    timeout = httpx.Timeout(60.0, connect=20.0)  # 60s read for POST (can be slow), 20s connect (increased from 10s)
    max_retries = 3
    
    logging.info(f"[WP] Updating post {post_id}: {len(merged_links)} links, {len(configured_ad_codes)} ads")
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.post(
                    f"{base_url}/wp-json/wp/v2/posts/{post_id}",
                    headers={"Content-Type": "application/json", **auth_headers},
                    json=payload,
                )
                logging.debug(f"[WP] Response status: {r.status_code}")
                logging.debug(f"[WP] Response body: {r.text[:500]} ...")
                r.raise_for_status()
                break  # Success, exit retry loop
        except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3  # 3s, 6s, 9s (longer waits for POST)
                logging.warning(f"[WP] Timeout on attempt {attempt + 1}/{max_retries} for POST post {post_id}: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logging.error(f"[WP] Failed to POST post {post_id} after {max_retries} attempts: {e}")
                raise HTTPException(status_code=504, detail=f"WordPress connection timeout after {max_retries} attempts")
        except httpx.HTTPStatusError as e:
            logging.error(f"[WP] HTTP error posting to {post_id}: {e}")
            raise
        except Exception as e:
            logging.error(f"[WP] Unexpected error posting to {post_id}: {e}")
            raise
    
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
