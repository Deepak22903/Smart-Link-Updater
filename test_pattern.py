import re

# Test pattern matching
test_content = '''<!-- wp:group {"className":"smartlink-updater-section","metadata":{"name":"SmartLink Links Section"}} -->
<div class="wp-block-group smartlink-updater-section links-for-today">
<h4>13 November 2025</h4>
<p>Test content</p>
</div>
<!-- /wp:group -->

<!-- wp:group {"className":"smartlink-updater-section","metadata":{"name":"SmartLink Links Section"}} -->
<div class="wp-block-group smartlink-updater-section links-for-today">
<h4>13 November 2025</h4>
<p>More test content</p>
</div>
<!-- /wp:group -->'''

# Current pattern from wp.py
pattern = r'<!-- wp:group \{"className":"smartlink-updater-section"[^>]*?\} -->.*?<!-- /wp:group -->'

matches = list(re.finditer(pattern, test_content, re.DOTALL))
print(f"Found {len(matches)} matches")
for i, match in enumerate(matches):
    print(f"\nMatch {i+1}: {match.start()}-{match.end()}")
    print(match.group(0)[:150] + "...")
    
print("\n" + "="*60)
print("Testing if pattern matches duplicate sections correctly")
print("="*60)

# Expected: Should find both sections
if len(matches) == 2:
    print("✅ PASS: Pattern found both sections")
else:
    print(f"❌ FAIL: Expected 2 sections, found {len(matches)}")
