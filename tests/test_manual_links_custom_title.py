"""
Test script for Manual Links Custom Button Title Feature
Demonstrates how custom button titles work when adding links manually
"""

# Example 1: Manual links with individual titles (default behavior)
manual_links_default = {
    "post_id": 105,
    "links": [
        {"title": "Get 50 Free Spins - Site1", "url": "https://site1.com"},
        {"title": "Claim Your Bonus - Site2", "url": "https://site2.com"},
        {"title": "Free Spins Here - Site3", "url": "https://site3.com"}
    ],
    "date": "2025-12-08",
    "target_sites": ["all"],
    "use_custom_button_title": False,  # Disabled - uses individual titles
    "custom_button_title": None
}

# Example 2: Manual links with custom button title
manual_links_custom = {
    "post_id": 105,
    "links": [
        {"title": "Get 50 Free Spins - Site1", "url": "https://site1.com"},  # Title ignored
        {"title": "Claim Your Bonus - Site2", "url": "https://site2.com"},   # Title ignored
        {"title": "Free Spins Here - Site3", "url": "https://site3.com"}     # Title ignored
    ],
    "date": "2025-12-08",
    "target_sites": ["all"],
    "use_custom_button_title": True,  # Enabled
    "custom_button_title": "Claim Free Spins Now"  # Custom title for all
}

def process_manual_links(request):
    """
    Simulates the backend logic in main.py
    """
    use_custom_title = request.get('use_custom_button_title', False)
    custom_title = request.get('custom_button_title', None)
    
    processed_links = []
    for link in request['links']:
        # Apply custom button title if enabled
        if use_custom_title and custom_title:
            title = custom_title
        else:
            title = link['title']
        
        processed_links.append({
            'url': link['url'],
            'title': title
        })
    
    return processed_links

# Test Case 1: Default behavior (individual titles)
print("=" * 80)
print("TEST CASE 1: Default Behavior (use_custom_button_title = False)")
print("=" * 80)
print("User enters individual titles for each link in the form")
print("-" * 80)
result1 = process_manual_links(manual_links_default)
for i, link in enumerate(result1, 1):
    print(f"Link {i}: Button shows '{link['title']}' → {link['url']}")

print("\n")

# Test Case 2: Custom button title
print("=" * 80)
print("TEST CASE 2: Custom Button Title (use_custom_button_title = True)")
print("=" * 80)
print(f"User toggles ON and sets custom title: '{manual_links_custom['custom_button_title']}'")
print("User still enters URLs but individual titles are ignored")
print("-" * 80)
result2 = process_manual_links(manual_links_custom)
for i, link in enumerate(result2, 1):
    print(f"Link {i}: Button shows '{link['title']}' → {link['url']}")

print("\n")

# Test Case 3: Edge case - toggle enabled but no custom title
manual_links_edge = {
    "post_id": 105,
    "links": [
        {"title": "Get 50 Free Spins - Site1", "url": "https://site1.com"},
        {"title": "Claim Your Bonus - Site2", "url": "https://site2.com"}
    ],
    "date": "2025-12-08",
    "target_sites": ["all"],
    "use_custom_button_title": True,  # Enabled
    "custom_button_title": None  # No custom title provided
}

print("=" * 80)
print("TEST CASE 3: Edge Case (toggle ON but no custom title)")
print("=" * 80)
result3 = process_manual_links(manual_links_edge)
for i, link in enumerate(result3, 1):
    print(f"Link {i}: Button shows '{link['title']}' → {link['url']}")

print("\n")
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("✓ Default mode: Each button uses its individual title from the form")
print("✓ Custom mode: All buttons use the same custom title")
print("✓ Fallback: If toggle is ON but no custom title, uses individual titles")
print("✓ User convenience: Enter URLs only, all buttons get same CTA")
print("=" * 80)
