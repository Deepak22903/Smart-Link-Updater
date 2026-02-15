import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.extractors.techyhigher import TechyHigherExtractor
from bs4 import BeautifulSoup

# Sample HTML for testing with inline date patterns
sample_html_inline_dates = """
<h3>Travel Town Free Energy Links 15 February 2026</h3>
<p>2<a href="http://d10xl.com/Animals_Coins/0YsKCwdmx2602" target="_blank" rel="noopener">.energy gifts links 15.2.2026</a></p>
<p>1<a href="https://d10xl.com/Animals_Coins/2wxwp" target="_blank" rel="noopener">.energy gifts links 15.2.2026</a></p>
<p>3.<a href="https://d10xl.com/Animals_Coins/0YsGMLgVp2602" target="_blank" rel="noopener">energy gifts links 14.2.2026</a></p>
<p>2<a href="https://d10xl.com/Animals_Coins/WTQ4j" target="_blank" rel="noopener">.energy gifts links 14.2.2026</a></p>
"""

# Sample HTML with "Today" section
sample_html_today = """
<p><strong>Today Coin Master Free Spins &amp; Coins 15 Feb 2026</strong></p>
<p>1.<a href="https://rewards.coinmaster.com/rewards/v1/reward123" target="_blank">Collect 25 Spins</a></p>
<p>2.<a href="https://rewards.coinmaster.com/rewards/v1/reward456" target="_blank">Collect 50 Coins</a></p>
<p>3.<a href="https://rewards.coinmaster.com/rewards/v1/reward789" target="_blank">Collect Free Energy</a></p>
"""

# Sample HTML with date heading
sample_html_date_heading = """
<p><strong>Coin Master Free Spins &amp; Coins 15 February 2026</strong></p>
<p>1.<a href="https://d10xl.com/CoinMaster/abc123" target="_blank">Spin Link 1</a></p>
<p>2.<a href="https://d10xl.com/CoinMaster/def456" target="_blank">Spin Link 2</a></p>
<p><strong>Travel Town Links 15 February 2026</strong></p>
<p>1.<a href="https://traveltown.onelink.me/xyz789" target="_blank">Energy Link</a></p>
"""

# Sample HTML with mixed formats
sample_html_mixed = """
<h2>Daily Rewards - 15 Feb 2026</h2>
<p><strong>Today Coin Master Free Spins &amp; Coins 15 Feb 2026</strong></p>
<p>1.<a href="https://rewards.coinmaster.com/rewards/v1/today1" target="_blank">Today Spin 1</a></p>
<p>2.<a href="https://rewards.coinmaster.com/rewards/v1/today2" target="_blank">Today Spin 2</a></p>

<p><strong>Travel Town Energy Links</strong></p>
<p>1<a href="https://d10xl.com/Animals_Coins/link1" target="_blank" rel="noopener">.energy gifts links 15.2.2026</a></p>
<p>2<a href="https://d10xl.com/Animals_Coins/link2" target="_blank" rel="noopener">.energy gifts links 15.2.2026</a></p>

<p><strong>15 February 2026</strong></p>
<p>1.<a href="https://d10xl.com/CashFrenzy/bonus1" target="_blank">Cash Frenzy Bonus</a></p>
"""

def test_inline_date_extraction():
    """Test extraction of links with inline dates in anchor text (dd.m.yyyy format)"""
    print("\n" + "="*80)
    print("TEST 1: Inline Date Pattern Extraction (15.2.2026)")
    print("="*80)
    
    extractor = TechyHigherExtractor()
    date = "2026-02-15"  # ISO format
    
    links = extractor.extract(sample_html_inline_dates, date)
    
    print(f"\nFound {len(links)} links for date {date}:")
    for i, link in enumerate(links, 1):
        print(f"{i}. Title: {link.title}")
        print(f"   URL: {link.url}")
        print(f"   Date: {link.published_date_iso}\n")
    
    # Assertions
    assert len(links) >= 2, f"Expected at least 2 links for 15.2.2026, got {len(links)}"
    assert any("d10xl.com" in str(link.url) for link in links), "Should find d10xl.com links"
    print("✓ Test passed: Inline date extraction working")

def test_today_section_extraction():
    """Test extraction from 'Today' sections"""
    print("\n" + "="*80)
    print("TEST 2: 'Today' Section Extraction")
    print("="*80)
    
    extractor = TechyHigherExtractor()
    date = "2026-02-15"  # ISO format
    
    links = extractor.extract(sample_html_today, date)
    
    print(f"\nFound {len(links)} links for date {date}:")
    for i, link in enumerate(links, 1):
        print(f"{i}. Title: {link.title}")
        print(f"   URL: {link.url}")
        print(f"   Date: {link.published_date_iso}\n")
    
    # Assertions
    assert len(links) >= 3, f"Expected at least 3 links from Today section, got {len(links)}"
    assert any("rewards.coinmaster.com" in str(link.url) for link in links), "Should find Coin Master reward links"
    print("✓ Test passed: 'Today' section extraction working")

def test_date_heading_extraction():
    """Test extraction from date headings"""
    print("\n" + "="*80)
    print("TEST 3: Date Heading Extraction")
    print("="*80)
    
    extractor = TechyHigherExtractor()
    date = "2026-02-15"  # ISO format
    
    links = extractor.extract(sample_html_date_heading, date)
    
    print(f"\nFound {len(links)} links for date {date}:")
    for i, link in enumerate(links, 1):
        print(f"{i}. Title: {link.title}")
        print(f"   URL: {link.url}")
        print(f"   Date: {link.published_date_iso}\n")
    
    # Assertions
    assert len(links) >= 3, f"Expected at least 3 links from date headings, got {len(links)}"
    print("✓ Test passed: Date heading extraction working")

def test_mixed_format_extraction():
    """Test extraction with mixed formats in one HTML"""
    print("\n" + "="*80)
    print("TEST 4: Mixed Format Extraction (All Strategies Combined)")
    print("="*80)
    
    extractor = TechyHigherExtractor()
    date = "2026-02-15"  # ISO format
    
    links = extractor.extract(sample_html_mixed, date)
    
    print(f"\nFound {len(links)} links for date {date}:")
    for i, link in enumerate(links, 1):
        print(f"{i}. Title: {link.title}")
        print(f"   URL: {link.url}")
        print(f"   Date: {link.published_date_iso}\n")
    
    # Assertions
    assert len(links) >= 5, f"Expected at least 5 links from mixed formats, got {len(links)}"
    print("✓ Test passed: Mixed format extraction working")

def test_url_filtering():
    """Test that non-reward URLs are filtered out"""
    print("\n" + "="*80)
    print("TEST 5: URL Filtering (Exclude Ads/Social)")
    print("="*80)
    
    html_with_ads = """
    <p><strong>15 Feb 2026</strong></p>
    <p>1.<a href="https://rewards.coinmaster.com/rewards/v1/reward1" target="_blank">Valid Link</a></p>
    <p>2.<a href="https://facebook.com/share" target="_blank">Facebook Link</a></p>
    <p>3.<a href="https://googlesyndication.com/ads" target="_blank">Ad Link</a></p>
    <p>4.<a href="https://d10xl.com/valid" target="_blank">Another Valid Link</a></p>
    """
    
    extractor = TechyHigherExtractor()
    date = "2026-02-15"
    
    links = extractor.extract(html_with_ads, date)
    
    print(f"\nFound {len(links)} links (after filtering):")
    for i, link in enumerate(links, 1):
        print(f"{i}. URL: {link.url}")
    
    # Assertions
    assert len(links) == 2, f"Expected 2 valid links after filtering, got {len(links)}"
    assert not any("facebook.com" in str(link.url) for link in links), "Should filter out Facebook"
    assert not any("googlesyndication.com" in str(link.url) for link in links), "Should filter out ads"
    print("✓ Test passed: URL filtering working correctly")

def test_deduplication():
    """Test that duplicate URLs are removed"""
    print("\n" + "="*80)
    print("TEST 6: Deduplication")
    print("="*80)
    
    html_with_dupes = """
    <p><strong>15 Feb 2026</strong></p>
    <p>1.<a href="https://d10xl.com/same/link123" target="_blank">Link 1</a></p>
    <p>2.<a href="https://d10xl.com/same/link123" target="_blank">Same Link</a></p>
    <p>3.<a href="https://d10xl.com/different/link456" target="_blank">Link 2</a></p>
    """
    
    extractor = TechyHigherExtractor()
    date = "2026-02-15"
    
    links = extractor.extract(html_with_dupes, date)
    
    print(f"\nFound {len(links)} unique links:")
    for i, link in enumerate(links, 1):
        print(f"{i}. URL: {link.url}")
    
    # Assertions
    assert len(links) == 2, f"Expected 2 unique links after deduplication, got {len(links)}"
    print("✓ Test passed: Deduplication working correctly")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("TECHYHIGHER EXTRACTOR TEST SUITE")
    print("="*80)
    
    try:
        test_inline_date_extraction()
        test_today_section_extraction()
        test_date_heading_extraction()
        test_mixed_format_extraction()
        test_url_filtering()
        test_deduplication()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED!")
        print("="*80 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        raise

if __name__ == "__main__":
    run_all_tests()
