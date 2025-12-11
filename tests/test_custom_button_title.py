"""
Test script for Custom Button Title Feature
Demonstrates how the feature works with example configurations
"""

# Example 1: Using Default Scraped Titles
config_default = {
    "post_id": 105,
    "content_slug": "coin-master-free-spins",
    "source_urls": ["https://example.com/links/"],
    "timezone": "Asia/Kolkata",
    "use_custom_button_title": False,  # Disabled - uses scraped titles
    "custom_button_title": None,
    "days_to_keep": 5
}

# Example 2: Using Custom Button Title
config_custom = {
    "post_id": 105,
    "content_slug": "coin-master-free-spins",
    "source_urls": ["https://example.com/links/"],
    "timezone": "Asia/Kolkata",
    "use_custom_button_title": True,  # Enabled
    "custom_button_title": "Claim Free Spins Now",  # Custom title
    "days_to_keep": 5
}

# Simulated scraped links from target site
scraped_links = [
    {"url": "https://site1.com", "title": "Get 50 Free Spins - Site1"},
    {"url": "https://site2.com", "title": "Claim Your Bonus - Site2"},
    {"url": "https://site3.com", "title": "Free Spins Here - Site3"},
]

def process_links(config, links):
    """
    Simulates the backend logic in wp.py
    """
    use_custom_title = config.get('use_custom_button_title', False)
    custom_title = config.get('custom_button_title', None)
    
    processed_links = []
    for link in links:
        # Use custom button title if enabled, otherwise use scraped title
        title = custom_title if (use_custom_title and custom_title) else link['title']
        processed_links.append({
            'url': link['url'],
            'title': title
        })
    
    return processed_links

# Test Case 1: Default behavior (scraped titles)
print("=" * 80)
print("TEST CASE 1: Default Behavior (use_custom_button_title = False)")
print("=" * 80)
result1 = process_links(config_default, scraped_links)
for link in result1:
    print(f"Button: '{link['title']}' → {link['url']}")

print("\n")

# Test Case 2: Custom button title
print("=" * 80)
print("TEST CASE 2: Custom Button Title (use_custom_button_title = True)")
print("=" * 80)
print(f"Custom Title: '{config_custom['custom_button_title']}'")
print("-" * 80)
result2 = process_links(config_custom, scraped_links)
for link in result2:
    print(f"Button: '{link['title']}' → {link['url']}")

print("\n")

# Test Case 3: Edge case - toggle enabled but no custom title
config_edge = {
    "use_custom_button_title": True,
    "custom_button_title": None,  # No custom title provided
}
print("=" * 80)
print("TEST CASE 3: Edge Case (toggle ON but no custom title)")
print("=" * 80)
result3 = process_links(config_edge, scraped_links)
for link in result3:
    print(f"Button: '{link['title']}' → {link['url']}")

print("\n")
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("✓ Default mode: Uses unique scraped titles from each site")
print("✓ Custom mode: All buttons use the same custom title")
print("✓ Fallback: If toggle is ON but no custom title, uses scraped titles")
print("=" * 80)
