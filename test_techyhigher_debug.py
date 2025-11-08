#!/usr/bin/env python3
"""
Debug script to test TechyHigher extractor with actual HTML structure.
"""

from backend.app.extractors.techyhigher import TechyHigherExtractor
from datetime import date

# Sample HTML matching the actual techyhigher.com structure
sample_html = """
<html>
<body>
<p><strong>Today Coin Master Free Spins &amp; Coins 6 Nov 2025</strong></p>
<p>2. <a href="https://rewards.coinmaster.com/rewards/somelink1">Coin Master Daily Bonus</a></p>
<p>1. <a href="https://d10xl.com/freecoins">D10XL Free Coins</a></p>

<p><strong>Yesterday Coin Master Free Spins 5 Nov 2025</strong></p>
<p>3. <a href="https://rewards.coinmaster.com/rewards/somelink2">Yesterday Link</a></p>
</body>
</html>
"""

def test_extractor():
    print("=" * 80)
    print("Testing TechyHigher Extractor")
    print("=" * 80)
    
    extractor = TechyHigherExtractor()
    today = date.today()
    
    print(f"\nTesting with date: {today}")
    print(f"HTML sample:\n{sample_html[:300]}...")
    
    # Extract links
    links = extractor.extract(sample_html, date=today.isoformat())
    
    print(f"\n✅ Extraction complete!")
    print(f"Found {len(links)} links:\n")
    
    for i, link in enumerate(links, 1):
        print(f"{i}. Title: {link.title}")
        print(f"   URL: {link.url}")
        print(f"   Date: {link.published_date_iso}")
        print()
    
    if not links:
        print("⚠️  WARNING: No links extracted! This indicates a bug.")
    
    return links

if __name__ == '__main__':
    test_extractor()
