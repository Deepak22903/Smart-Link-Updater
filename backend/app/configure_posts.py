#!/usr/bin/env python3
"""
CLI tool to configure target URLs for WordPress posts.
Usage: python -m backend.app.configure_posts
"""
import sys
import json
from .storage import set_post_config, get_post_config, list_configured_posts


def main():
    if len(sys.argv) < 2:
        print("SmartLinkUpdater - Post Configuration")
        print()
        print("Usage:")
        print("  python -m backend.app.configure_posts add <post_id> <url1> [url2] ...")
        print("  python -m backend.app.configure_posts list")
        print("  python -m backend.app.configure_posts get <post_id>")
        print()
        print("Examples:")
        print("  # Configure post 123 to scrape Hacker News")
        print("  python -m backend.app.configure_posts add 123 https://news.ycombinator.com/")
        print()
        print("  # Configure post 456 to scrape multiple sources")
        print("  python -m backend.app.configure_posts add 456 \\")
        print("    https://news.ycombinator.com/ \\")
        print("    https://lobste.rs/")
        print()
        print("  # List all configured posts")
        print("  python -m backend.app.configure_posts list")
        print()
        print("  # Get config for specific post")
        print("  python -m backend.app.configure_posts get 123")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 4:
            print("Error: add requires <post_id> and at least one URL")
            sys.exit(1)
        
        post_id = int(sys.argv[2])
        source_urls = sys.argv[3:]
        
        set_post_config(post_id, source_urls)
        print(f"✅ Configured post {post_id}")
        print(f"   Source URLs: {', '.join(source_urls)}")
        print(f"   Timezone: Asia/Kolkata (default)")
    
    elif command == "list":
        posts = list_configured_posts()
        if not posts:
            print("No posts configured yet.")
            print("Use 'add' command to configure posts.")
        else:
            print(f"Configured Posts ({len(posts)}):")
            print()
            for post in posts:
                print(f"  Post ID: {post['post_id']}")
                print(f"  Timezone: {post['timezone']}")
                print(f"  Sources:")
                for url in post['source_urls']:
                    print(f"    - {url}")
                print()
    
    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: get requires <post_id>")
            sys.exit(1)
        
        post_id = int(sys.argv[2])
        config = get_post_config(post_id)
        
        if not config:
            print(f"❌ Post {post_id} not configured")
            sys.exit(1)
        
        print(json.dumps(config, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: add, list, get")
        sys.exit(1)


if __name__ == "__main__":
    main()
