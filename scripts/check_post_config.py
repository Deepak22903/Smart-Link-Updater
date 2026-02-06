"""
Quick script to check what post IDs are configured in MongoDB
and their content_slugs for multi-site mapping.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.mongo_storage import list_configured_posts

def main():
    # Get all post configs
    posts = list_configured_posts()
    
    print("=" * 80)
    print("All Configured Posts in MongoDB")
    print("=" * 80)
    
    for post in posts:
        print(f"\nPost ID: {post.get('post_id')}")
        print(f"  Content Slug: {post.get('content_slug', 'N/A')}")
        print(f"  Source URLs: {post.get('source_urls', [])}")
        print(f"  Extractor: {post.get('extractor_map', {})}")
        
        if 'site_post_ids' in post:
            print(f"  Site Post IDs:")
            for site_key, site_post_id in post['site_post_ids'].items():
                print(f"    - {site_key}: {site_post_id}")
    
    # Search for bingo-blitz specifically
    print("\n" + "=" * 80)
    print("Searching for 'bingo-blitz' content...")
    print("=" * 80)
    
    bingo_posts = [p for p in posts if 'bingo' in str(p.get('source_urls', [])).lower() 
                   or p.get('content_slug') == 'bingo-blitz']
    
    if bingo_posts:
        for post in bingo_posts:
            print(f"\n✓ Found Bingo Blitz Post:")
            print(f"  MongoDB post_id: {post.get('post_id')}")
            print(f"  Content Slug: {post.get('content_slug', 'N/A')}")
            print(f"  Source URLs: {post.get('source_urls', [])}")
            
            if 'site_post_ids' in post:
                print(f"  Mapped to sites:")
                for site_key, site_post_id in post['site_post_ids'].items():
                    print(f"    - {site_key}: WP post_id = {site_post_id}")
    else:
        print("\n✗ No bingo-blitz posts found in MongoDB")
        print("\nYou may need to add this post configuration first!")

if __name__ == "__main__":
    main()
