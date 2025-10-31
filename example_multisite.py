#!/usr/bin/env python3
"""
Example: Configure a post for a different WordPress site

This demonstrates how to configure a post to update on a different WordPress site
than the default one configured in .env
"""
import requests
import json

# Configure post 888 for a second WordPress site
config = {
    "post_id": 888,
    "source_urls": [
        "https://simplegameguide.com/coin-master-free-spins-links/"
    ],
    "timezone": "America/New_York",
    "wp_site": {
        "base_url": "https://your-second-site.com",
        "username": "admin@example.com",
        "app_password": "your-app-password-here"
    }
}

print("Configuring post 888 for a different WordPress site...")
print(f"Target site: {config['wp_site']['base_url']}")
print(f"Source URLs: {config['source_urls']}")
print()

response = requests.post(
    "http://localhost:8000/config/post",
    json=config
)

if response.status_code == 200:
    result = response.json()
    print("✅ Configuration successful!")
    print(json.dumps(result, indent=2))
    print()
    print("Now you can update this post with:")
    print(f"  curl -X POST 'http://localhost:8000/update-post/888?sync=true'")
    print()
    print("This will:")
    print(f"  1. Scrape: {config['source_urls'][0]}")
    print("  2. Extract links using simplegameguide extractor")
    print(f"  3. Update post 888 on {config['wp_site']['base_url']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
