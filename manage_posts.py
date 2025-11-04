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
        
        print(f"\n{'ID':<8} {'Extractor':<20} {'Source URL':<50} {'Updated':<25}")
        print("-" * 110)
        for post in posts:
            post_id = post.get("post_id", "N/A")
            extractor = post.get("extractor", "auto")
            source_url = post.get("source_urls", ["N/A"])[0] if post.get("source_urls") else "N/A"
            updated = post.get("updated_at", "N/A")
            
            # Truncate long URLs
            if len(source_url) > 50:
                source_url = source_url[:47] + "..."
            
            print(f"{post_id:<8} {extractor:<20} {source_url:<50} {updated:<25}")
        print()
    
    def get_post(self, post_id: int):
        """Get configuration for a specific post"""
        response = requests.get(f"{self.base_url}/config/post/{post_id}")
        response.raise_for_status()
        
        config = response.json()
        print(json.dumps(config, indent=2))
    
    def add_post(self, post_id: int, source_url: str, extractor: Optional[str] = None, 
                 timezone: str = "Asia/Kolkata"):
        """Add a new post configuration"""
        data = {
            "post_id": post_id,
            "source_urls": [source_url],
            "timezone": timezone
        }
        
        if extractor:
            data["extractor"] = extractor
        
        response = requests.post(f"{self.base_url}/config/post", json=data)
        response.raise_for_status()
        
        print(f"✓ Successfully added post {post_id}")
        print(json.dumps(response.json(), indent=2))
    
    def update_post(self, post_id: int, extractor: Optional[str] = None, 
                   source_url: Optional[str] = None, timezone: Optional[str] = None):
        """Update an existing post configuration"""
        data = {}
        
        if extractor:
            data["extractor"] = extractor
        
        if source_url:
            data["source_urls"] = [source_url]
        
        if timezone:
            data["timezone"] = timezone
        
        if not data:
            print("Error: No update data provided. Use --extractor, --url, or --timezone")
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
        source_url = get_input("Enter source URL (e.g., https://example.com/links/)")
        
        extractor = None
        if get_yes_no("Specify a custom extractor?", default=False):
            extractor = get_input("Enter extractor name (e.g., simplegameguide, mosttechs)")
        
        timezone = get_input("Enter timezone", default="Asia/Kolkata")
        
        print("\nAdding post configuration...")
        manager.add_post(post_id, source_url, extractor, timezone)
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
        source_url = None
        timezone = None
        
        if get_yes_no("Update extractor?", default=False):
            extractor = get_input("Enter new extractor name")
        
        if get_yes_no("Update source URL?", default=False):
            source_url = get_input("Enter new source URL")
        
        if get_yes_no("Update timezone?", default=False):
            timezone = get_input("Enter new timezone", default="Asia/Kolkata")
        
        if not any([extractor, source_url, timezone]):
            print("\n  No changes made.")
        else:
            print("\nUpdating post configuration...")
            manager.update_post(post_id, extractor, source_url, timezone)
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
                print("Error: Post ID and source URL required")
                print("Usage: python manage_posts.py add <post_id> <source_url> [--extractor <name>] [--timezone <tz>]")
                sys.exit(1)
            
            post_id = int(sys.argv[2])
            source_url = sys.argv[3]
            
            # Parse optional arguments
            extractor = None
            timezone = "Asia/Kolkata"
            
            i = 4
            while i < len(sys.argv):
                if sys.argv[i] == "--extractor" and i + 1 < len(sys.argv):
                    extractor = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--timezone" and i + 1 < len(sys.argv):
                    timezone = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            manager.add_post(post_id, source_url, extractor, timezone)
        
        elif command == "update":
            if len(sys.argv) < 3:
                print("Error: Post ID required")
                print("Usage: python manage_posts.py update <post_id> [--extractor <name>] [--url <url>] [--timezone <tz>]")
                sys.exit(1)
            
            post_id = int(sys.argv[2])
            
            # Parse optional arguments
            extractor = None
            source_url = None
            timezone = None
            
            i = 3
            while i < len(sys.argv):
                if sys.argv[i] == "--extractor" and i + 1 < len(sys.argv):
                    extractor = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--url" and i + 1 < len(sys.argv):
                    source_url = sys.argv[i + 1]
                    i += 2
                elif sys.argv[i] == "--timezone" and i + 1 < len(sys.argv):
                    timezone = sys.argv[i + 1]
                    i += 2
                else:
                    i += 1
            
            manager.update_post(post_id, extractor, source_url, timezone)
        
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
