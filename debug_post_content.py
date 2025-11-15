#!/usr/bin/env python3
"""
Debug script to fetch and analyze WordPress post content
to understand why section detection is failing.
"""
import os
import sys
import requests
from requests.auth import HTTPBasicAuth
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://minecraftcirclegenerater.com")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD") or os.getenv("WP_APPLICATION_PASSWORD")

if not WP_USERNAME or not WP_APP_PASSWORD:
    print("ERROR: WP_USERNAME and WP_APPLICATION_PASSWORD environment variables must be set")
    sys.exit(1)

def fetch_post_content(post_id):
    """Fetch raw post content from WordPress API"""
    url = f"{WP_BASE_URL}/wp-json/wp/v2/posts/{post_id}"
    
    print(f"Fetching post {post_id} from {url}")
    print(f"Using auth: {WP_USERNAME} / {'*' * len(WP_APP_PASSWORD)}\n")
    
    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD),
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"ERROR: Failed to fetch post. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR: Request failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    data = response.json()
    return data.get("content", {}).get("raw", "")

def analyze_content(content):
    """Analyze the content to find SmartLink sections"""
    print("=" * 80)
    print("ANALYZING POST CONTENT")
    print("=" * 80)
    
    # Pattern 1: New block format
    new_block_pattern = r'<!-- wp:group \{"className":"smartlink-updater-section"[^>]*?\} -->.*?<!-- /wp:group -->'
    
    # Pattern 2: Check for ANY wp:group blocks
    any_group_pattern = r'<!-- wp:group.*?-->.*?<!-- /wp:group -->'
    
    # Pattern 3: Check for smartlink class in any format
    smartlink_class_pattern = r'smartlink-updater-section'
    
    # Pattern 4: Date headers
    date_pattern = r'<h4[^>]*>.*?(\d{2} \w+ \d{4}).*?</h4>'
    
    print(f"\nContent length: {len(content)} characters\n")
    
    # Check for new block format
    new_matches = list(re.finditer(new_block_pattern, content, re.DOTALL))
    print(f"✓ New block format matches: {len(new_matches)}")
    for i, match in enumerate(new_matches[:3], 1):
        snippet = match.group(0)[:200] + "..." if len(match.group(0)) > 200 else match.group(0)
        print(f"  Match {i}: {snippet}\n")
    
    # Check for ANY wp:group blocks
    any_group_matches = list(re.finditer(any_group_pattern, content, re.DOTALL))
    print(f"\n✓ Total wp:group blocks found: {len(any_group_matches)}")
    if any_group_matches:
        print("  First few wp:group opening tags:")
        for i, match in enumerate(any_group_matches[:5], 1):
            opening_tag = match.group(0).split('\n')[0][:150]
            print(f"  {i}. {opening_tag}")
    
    # Check for smartlink class
    has_smartlink = bool(re.search(smartlink_class_pattern, content))
    print(f"\n✓ Contains 'smartlink-updater-section' class: {has_smartlink}")
    if has_smartlink:
        # Show context around smartlink mentions
        for match in re.finditer(r'.{0,100}smartlink-updater-section.{0,100}', content):
            print(f"  Context: ...{match.group(0)}...")
    
    # Check for date headers
    date_matches = list(re.finditer(date_pattern, content, re.DOTALL))
    print(f"\n✓ Date headers found: {len(date_matches)}")
    for i, match in enumerate(date_matches[:5], 1):
        print(f"  {i}. {match.group(1)} - Full header: {match.group(0)[:100]}")
    
    print("\n" + "=" * 80)
    print("RAW CONTENT SAMPLE (first 2000 characters)")
    print("=" * 80)
    print(content[:2000])
    
    print("\n" + "=" * 80)
    print("RAW CONTENT SAMPLE (searching for 'smartlink' or recent dates)")
    print("=" * 80)
    
    # Try to find sections with recent content
    recent_date_pattern = r'(13|14|15) November 2025'
    for match in re.finditer(r'.{0,500}' + recent_date_pattern + r'.{0,500}', content, re.DOTALL):
        print(match.group(0))
        print("\n" + "-" * 80 + "\n")

if __name__ == "__main__":
    post_id = int(sys.argv[1]) if len(sys.argv) > 1 else 196
    
    content = fetch_post_content(post_id)
    
    if content:
        analyze_content(content)
    else:
        print("Failed to fetch content")
