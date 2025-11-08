#!/usr/bin/env python3
"""
Interactive Post Configuration Management Script

Run without arguments for interactive mode:
    python manage_posts.py
"""

import requests
import json
import sys
from typing import Optional, List

# Configuration
API_BASE_URL = "http://localhost:8000"  # Change to your API URL


class PostConfigManager:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
    
    def list_posts(self):
        """List all configured posts"""
        response = requests.get(f"{self.base_url}/config/posts")
        response.raise_for_status()
        
        posts = response.json()["posts"]
        if not posts:
            print("No posts configured.")
            return
        
        print(f"\n{'ID':<8} {'Sources':<8} {'Extractor(s)':<30} {'First Source URL':<50} {'Updated':<25}")
        print("-" * 130)
        for post in posts:
            post_id = post.get("post_id", "N/A")
            source_urls = post.get("source_urls", [])
            extractor = post.get("extractor", "auto")
            extractor_map = post.get("extractor_map", {})
            updated = post.get("updated_at", "N/A")
            
            # Determine extractor display
            if extractor_map:
                unique_extractors = set(extractor_map.values())
                if len(unique_extractors) == 1:
                    extractor_display = list(unique_extractors)[0]
                else:
                    extractor_display = f"{len(unique_extractors)} different"
            else:
                extractor_display = extractor
            
            source_count = len(source_urls)
            source_url = source_urls[0] if source_urls else "N/A"
            
            # Truncate long URLs
            if len(source_url) > 50:
                source_url = source_url[:47] + "..."
            
            print(f"{post_id:<8} {source_count:<8} {extractor_display:<30} {source_url:<50} {updated:<25}")
        print()
    
    def get_post(self, post_id: int):
        """Get configuration for a specific post"""
        response = requests.get(f"{self.base_url}/config/post/{post_id}")
        response.raise_for_status()
        
        config = response.json()
        print(json.dumps(config, indent=2))
    
    def add_post(self, post_id: int, source_urls: List[str], extractor: Optional[str] = None, 
                 extractor_map: Optional[dict] = None, timezone: str = "Asia/Kolkata"):
        """Add a new post configuration with support for multiple sources and extractors"""
        data = {
            "post_id": post_id,
            "source_urls": source_urls if isinstance(source_urls, list) else [source_urls],
            "timezone": timezone
        }
        
        if extractor:
            data["extractor"] = extractor
        
        if extractor_map:
            data["extractor_map"] = extractor_map
        
        response = requests.post(f"{self.base_url}/config/post", json=data)
        response.raise_for_status()
        
        print(f"✓ Successfully added post {post_id}")
        print(json.dumps(response.json(), indent=2))
    
    def update_post(self, post_id: int, extractor: Optional[str] = None, 
                   source_urls: Optional[List[str]] = None, extractor_map: Optional[dict] = None,
                   timezone: Optional[str] = None):
        """Update an existing post configuration with support for multiple sources and extractors"""
        data = {}
        
        if extractor:
            data["extractor"] = extractor
        
        if source_urls:
            data["source_urls"] = source_urls if isinstance(source_urls, list) else [source_urls]
        
        if extractor_map:
            data["extractor_map"] = extractor_map
        
        if timezone:
            data["timezone"] = timezone
        
        if not data:
            print("Error: No update data provided. Use --extractor, --urls, --extractor-map, or --timezone")
            sys.exit(1)
        
        response = requests.put(f"{self.base_url}/config/post/{post_id}", json=data)
        response.raise_for_status()
        
        print(f"✓ Successfully updated post {post_id}")
        print(json.dumps(response.json(), indent=2))
    
    def delete_post(self, post_id: int):
        """Delete a post configuration"""
        response = requests.delete(f"{self.base_url}/config/post/{post_id}")
        response.raise_for_status()
        
        result = response.json()
        print(f"✓ {result.get('message', 'Post deleted successfully')}")
        return result


def print_menu():
    """Display the main menu"""
    print("\n" + "="*60)
    print("  Smart Link Updater - Post Configuration Manager")
    print("="*60)
    print("\n1. List all posts")
    print("2. View post details")
    print("3. Add new post")
    print("4. Update post configuration")
    print("5. Delete post")
    print("6. Exit")
    print("\n" + "-"*60)


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Get user input with optional default value"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("  Error: This field is required. Please enter a value.")


def get_yes_no(prompt: str, default: bool = False) -> bool:
    """Get yes/no input from user"""
    default_str = "Y/n" if default else "y/N"
    while True:
        response = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        if response in ['y', 'yes']:
            return True
        if response in ['n', 'no']:
            return False
        print("  Please enter 'y' or 'n'")


def interactive_list(manager: 'PostConfigManager'):
    """Interactive list posts"""
    print("\n" + "="*60)
    print("  All Configured Posts")
    print("="*60 + "\n")
    manager.list_posts()
    input("\nPress Enter to continue...")


def interactive_get(manager: 'PostConfigManager'):
    """Interactive view post details"""
    print("\n" + "="*60)
    print("  View Post Details")
    print("="*60 + "\n")
    
    try:
        post_id = int(get_input("Enter post ID"))
        print(f"\nConfiguration for post {post_id}:")
        print("-" * 60)
        manager.get_post(post_id)
    except ValueError:
        print("  Error: Invalid post ID. Must be a number.")
    except Exception as e:
        print(f"  Error: {e}")
    
    input("\nPress Enter to continue...")


def interactive_add(manager: 'PostConfigManager'):
    """Interactive add new post"""
    print("\n" + "="*60)
    print("  Add New Post Configuration")
    print("="*60 + "\n")
    
    try:
        post_id = int(get_input("Enter post ID"))
        
        # Collect source URLs
        source_urls = []
        while True:
            source_url = get_input(f"Enter source URL #{len(source_urls) + 1} (e.g., https://example.com/links/)")
            source_urls.append(source_url)
            
            if not get_yes_no("Add another source URL?", default=False):
                break
        
        # Configure extractors
        extractor = None
        extractor_map = {}
        
        if len(source_urls) == 1:
            if get_yes_no("Specify a custom extractor for this source?", default=False):
                extractor = get_input("Enter extractor name (simplegameguide, mosttechs, crazyashwin, techyhigher, default)")
        else:
            print(f"\n{'='*60}")
            print(f"  Configure Extractors for {len(source_urls)} Sources")
            print(f"{'='*60}\n")
            
            use_individual = get_yes_no("Configure different extractors for each source?", default=True)
            
            if use_individual:
                print("\nAvailable extractors: simplegameguide, mosttechs, crazyashwin, techyhigher, default, auto")
                print("(Use 'auto' or leave empty for auto-detection)\n")
                
                for url in source_urls:
                    print(f"Source: {url}")
                    ext = get_input("  Extractor", default="auto").strip()
                    if ext and ext != "auto":
                        extractor_map[url] = ext
            else:
                if get_yes_no("Use same extractor for all sources?", default=False):
                    extractor = get_input("Enter extractor name (simplegameguide, mosttechs, crazyashwin, techyhigher, default)")
        
        timezone = get_input("Enter timezone", default="Asia/Kolkata")
        
        print("\nAdding post configuration...")
        manager.add_post(post_id, source_urls, extractor, extractor_map if extractor_map else None, timezone)
        print("\n✓ Success!")
        
    except ValueError:
        print("  Error: Invalid post ID. Must be a number.")
    except Exception as e:
        print(f"  Error: {e}")
    
    input("\nPress Enter to continue...")


def interactive_update(manager: 'PostConfigManager'):
    """Interactive update post"""
    print("\n" + "="*60)
    print("  Update Post Configuration")
    print("="*60 + "\n")
    
    try:
        post_id = int(get_input("Enter post ID to update"))
        
        # Show current config
        print(f"\nCurrent configuration:")
        print("-" * 60)
        try:
            manager.get_post(post_id)
        except:
            print(f"  Warning: Could not fetch current config for post {post_id}")
        
        print("\n" + "-" * 60)
        print("What would you like to update?")
        print("-" * 60)
        
        extractor = None
        source_urls = None
        extractor_map = None
        timezone = None
        
        if get_yes_no("Update global extractor?", default=False):
            extractor = get_input("Enter new extractor name (simplegameguide, mosttechs, crazyashwin, techyhigher, default)")
        
        if get_yes_no("Update source URLs?", default=False):
            source_urls = []
            while True:
                source_url = get_input(f"Enter source URL #{len(source_urls) + 1}")
                source_urls.append(source_url)
                
                if not get_yes_no("Add another source URL?", default=False):
                    break
        
        if get_yes_no("Configure per-source extractors?", default=False):
            extractor_map = {}
            num_sources = int(get_input("How many source-extractor mappings?"))
            
            print("\nEnter source URL and extractor pairs:")
            print("Available extractors: simplegameguide, mosttechs, crazyashwin, techyhigher, default\n")
            
            for i in range(num_sources):
                url = get_input(f"  Source URL #{i+1}")
                ext = get_input(f"  Extractor for this source")
                extractor_map[url] = ext
        
        if get_yes_no("Update timezone?", default=False):
            timezone = get_input("Enter new timezone", default="Asia/Kolkata")
        
        if not any([extractor, source_urls, extractor_map, timezone]):
            print("\n  No changes made.")
        else:
            print("\nUpdating post configuration...")
            manager.update_post(post_id, extractor, source_urls, extractor_map, timezone)
            print("\n✓ Success!")
        
    except ValueError:
        print("  Error: Invalid post ID. Must be a number.")
    except Exception as e:
        print(f"  Error: {e}")
    
    input("\nPress Enter to continue...")


def interactive_delete(manager: 'PostConfigManager'):
    """Interactive delete post"""
    print("\n" + "="*60)
    print("  Delete Post Configuration")
    print("="*60 + "\n")
    
    try:
        post_id = int(get_input("Enter post ID to delete"))
        
        # Show current config
        print(f"\nConfiguration to delete:")
        print("-" * 60)
        try:
            manager.get_post(post_id)
        except:
            print(f"  Warning: Could not fetch config for post {post_id}")
        
        print("\n" + "-" * 60)
        if get_yes_no("Are you sure you want to delete this post?", default=False):
            manager.delete_post(post_id)
        else:
            print("\n  Deletion cancelled.")
        
    except ValueError:
        print("  Error: Invalid post ID. Must be a number.")
    except Exception as e:
        print(f"  Error: {e}")
    
    input("\nPress Enter to continue...")


def interactive_mode():
    """Run the script in interactive mode"""
    manager = PostConfigManager()
    
    while True:
        try:
            print_menu()
            choice = input("Select an option (1-6): ").strip()
            
            if choice == "1":
                interactive_list(manager)
            elif choice == "2":
                interactive_get(manager)
            elif choice == "3":
                interactive_add(manager)
            elif choice == "4":
                interactive_update(manager)
            elif choice == "5":
                interactive_delete(manager)
            elif choice == "6":
                print("\nGoodbye!\n")
                sys.exit(0)
            else:
                print("\n  Invalid option. Please select 1-6.")
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n  Unexpected error: {e}")
            input("\nPress Enter to continue...")


def main():
    # If no arguments, run in interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    # Otherwise, use command-line mode (kept for backwards compatibility)
    manager = PostConfigManager()
    command = sys.argv[1].lower()
    
    try:
        if command == "list":
            manager.list_posts()
        
        elif command == "get":
            if len(sys.argv) < 3:
                print("Error: Post ID required")
                print("Usage: python manage_posts.py get <post_id>")
                sys.exit(1)
            post_id = int(sys.argv[2])
            manager.get_post(post_id)
        
        elif command == "add":
            if len(sys.argv) < 4:
                print("Error: Post ID and source URL(s) required")
                print("Usage: python manage_posts.py add <post_id> <source_url1> [<source_url2> ...] [--extractor <name>] [--extractor-map <json>] [--timezone <tz>]")
                print("\nExample with multiple sources:")
                print("  python manage_posts.py add 123 https://site1.com https://site2.com --extractor-map '{\"https://site1.com\":\"mosttechs\",\"https://site2.com\":\"crazyashwin\"}'")
                sys.exit(1)
            
            post_id = int(sys.argv[2])
            
            # Collect source URLs (all args before flags)
            source_urls = []
            i = 3
            while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                source_urls.append(sys.argv[i])
                i += 1
            
            if not source_urls:
                print("Error: At least one source URL is required")
                sys.exit(1)
            
            # Parse optional arguments
            extractor = None
            extractor_map = None
            timezone = "Asia/Kolkata"
            
            while i < len(sys.argv):
                if sys.argv[i] == "--extractor" and i + 1 < len(sys.argv):
                    extractor = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--extractor-map" and i + 1 < len(sys.argv):
                    extractor_map = json.loads(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == "--timezone" and i + 1 < len(sys.argv):
                    timezone = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            manager.add_post(post_id, source_urls, extractor, extractor_map, timezone)
        
        elif command == "update":
            if len(sys.argv) < 3:
                print("Error: Post ID required")
                print("Usage: python manage_posts.py update <post_id> [--extractor <name>] [--urls <url1> <url2> ...] [--extractor-map <json>] [--timezone <tz>]")
                print("\nExample with extractor map:")
                print("  python manage_posts.py update 123 --extractor-map '{\"https://site1.com\":\"mosttechs\",\"https://site2.com\":\"crazyashwin\"}'")
                sys.exit(1)
            
            post_id = int(sys.argv[2])
            
            # Parse optional arguments
            extractor = None
            source_urls = None
            extractor_map = None
            timezone = None
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--extractor" and i + 1 < len(sys.argv):
                    extractor = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--urls":
                    source_urls = []
                    i += 1
                    while i < len(sys.argv) and not sys.argv[i].startswith('--'):
                        source_urls.append(sys.argv[i])
                        i += 1
                elif sys.argv[i] == "--extractor-map" and i + 1 < len(sys.argv):
                    extractor_map = json.loads(sys.argv[i + 1])
                    i += 2
                elif sys.argv[i] == "--timezone" and i + 1 < len(sys.argv):
                    timezone = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            manager.update_post(post_id, extractor, source_urls, extractor_map, timezone)
        
        elif command == "delete":
            if len(sys.argv) < 3:
                print("Error: Post ID required")
                print("Usage: python manage_posts.py delete <post_id>")
                sys.exit(1)
            post_id = int(sys.argv[2])
            manager.delete_post(post_id)
        
        else:
            print(f"Error: Unknown command '{command}'")
            print("Run without arguments for interactive mode")
            sys.exit(1)
    
    except requests.exceptions.HTTPError as e:
        print(f"✗ API Error: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(json.dumps(error_detail, indent=2))
            except:
                print(e.response.text)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
