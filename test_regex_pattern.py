#!/usr/bin/env python3
"""Test regex pattern against actual WordPress content"""
import re

# Actual HTML from WordPress
html_sample = '''<h2 class="wp-block-heading">Domino Dreams Free Coins Links</h2>


<div class="wp-block-group smartlink-updater-section links-for-today" style="padding: 20px; margin: 20px 0;"><div class="wp-block-group__inner-container is-layout-flow wp-block-group-is-layout-flow">

<h4 class="wp-block-heading has-text-align-center" style="color:#30d612;font-size:20px">15 November 2025</h4>



<div class="wp-block-columns is-layout-flex wp-container-core-columns-is-layout-9d6595d7 wp-block-columns-is-layout-flex">

<div class="wp-block-column is-layout-flow wp-block-column-is-layout-flow" style="flex-basis:50%">
    <div style="margin: 15px 0;">
        <a href="https://t.me/+x4q4KjnicT45N2U1" target="_blank">01. domino dreams free gifts</a>
    </div>
</div>


<div class="wp-block-column is-layout-flow wp-block-column-is-layout-flow" style="flex-basis:50%">
    <div style="margin: 15px 0;">
        <a href="https://join.domino-dreams.com/fb?key=test" target="_blank">02. Collect DD free Coins</a>
    </div>
</div>

</div>



<p class="has-text-color" style="color:#999;font-size:12px"><em>Last updated: 2025-11-15 07:31:21 UTC</em></p>

</div></div>

<h2 class="wp-block-heading">Some Other Section</h2>
<p>This should not be matched</p>'''

# Test pattern - use "Last updated" timestamp as anchor point
pattern = r'<div class="wp-block-group smartlink-updater-section[^>]*>.*?<p class="has-text-color"[^>]*>.*?Last updated:.*?</p>\s*</div>\s*</div>'

matches = list(re.finditer(pattern, html_sample, re.DOTALL))

print(f"Number of matches: {len(matches)}")
print()

for i, match in enumerate(matches, 1):
    matched_text = match.group(0)
    print(f"Match {i}:")
    print(f"  Start: {match.start()}, End: {match.end()}")
    print(f"  Length: {len(matched_text)} chars")
    print(f"  First 200 chars: {matched_text[:200]}...")
    print(f"  Last 200 chars: ...{matched_text[-200:]}")
    print()
    
    # Check what comes after the match
    after_match = html_sample[match.end():match.end()+100]
    print(f"  Content after match: {after_match[:100]}")
    print()
    
    # Check if it ends correctly with </div></div>
    if matched_text.rstrip().endswith("</div></div>"):
        print("  ✓ OK: Ends with proper closing tags </div></div>")
    else:
        print(f"  ⚠ WARNING: Ends with: {matched_text[-50:]}")
    
    # Check if it captured too much
    if "Some Other Section" in matched_text:
        print("  ❌ ERROR: Pattern matched too much! Captured content outside our section")
    else:
        print("  ✓ OK: Pattern doesn't capture outside content")
    print()
