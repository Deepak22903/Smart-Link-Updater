"""
Test script for custom insertion point feature
Tests the regex patterns for finding headings
"""
import re

# Your example heading HTML (simplified)
test_html = '''
<div class="content">
<p>Some intro content here</p>

<h2 class="wp-block-heading"><span class="ez-toc-section" id="Coin_Master_Free_Spins_Coins_Links" ez-toc-data-id="#Coin_Master_Free_Spins_Coins_Links"></span>Coin Master Free Spins &amp; Coins Links<span class="ez-toc-section-end"></span></h2>

<p>More content after the heading</p>
</div>
'''

print("="*80)
print("TEST 1: Find heading by ID 'Coin_Master_Free_Spins_Coins_Links'")
print("="*80)

insertion_value = "Coin_Master_Free_Spins_Coins_Links"
heading_pattern = rf'(<h[1-6][^>]*(?:id="{re.escape(insertion_value)}"|id=\'{re.escape(insertion_value)}\'|ez-toc-data-id="#{re.escape(insertion_value)}").*?</h[1-6]>)'

match = re.search(heading_pattern, test_html, re.DOTALL | re.IGNORECASE)

if match:
    print("✅ FOUND heading!")
    print(f"Matched text: {match.group(0)[:200]}...")
    print(f"Match position: {match.start()} - {match.end()}")
    
    # Simulate insertion
    new_section = "\n<div>INSERTED LINKS SECTION HERE</div>\n"
    heading_end = match.end()
    new_content = test_html[:heading_end] + new_section + test_html[heading_end:]
    
    print("\n" + "="*80)
    print("RESULT after insertion:")
    print("="*80)
    print(new_content)
else:
    print("❌ NOT FOUND - would fallback to prepend")

print("\n" + "="*80)
print("TEST 2: Find heading by text 'Coin Master Free Spins'")
print("="*80)

insertion_value_text = "Coin Master Free Spins"
heading_pattern_text = rf'(<h[1-6][^>]*>.*?{re.escape(insertion_value_text)}.*?</h[1-6]>)'

match_text = re.search(heading_pattern_text, test_html, re.DOTALL | re.IGNORECASE)

if match_text:
    print("✅ FOUND heading by text!")
    print(f"Matched text: {match_text.group(0)[:200]}...")
else:
    print("❌ NOT FOUND by text")

print("\n" + "="*80)
print("TEST 3: Simpler heading (without ez-toc spans)")
print("="*80)

simple_html = '''
<div>
<p>Intro</p>
<h2 id="my_heading">My Simple Heading</h2>
<p>Content</p>
</div>
'''

insertion_value_simple = "my_heading"
heading_pattern_simple = rf'(<h[1-6][^>]*(?:id="{re.escape(insertion_value_simple)}"|id=\'{re.escape(insertion_value_simple)}\'|ez-toc-data-id="#{re.escape(insertion_value_simple)}").*?</h[1-6]>)'

match_simple = re.search(heading_pattern_simple, simple_html, re.DOTALL | re.IGNORECASE)

if match_simple:
    print("✅ FOUND simple heading!")
    print(f"Matched text: {match_simple.group(0)}")
else:
    print("❌ NOT FOUND simple heading")

print("\n" + "="*80)
print("All tests complete!")
print("="*80)
