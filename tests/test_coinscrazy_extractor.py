"""
Test script for CoinsCrazy extractor
Fetches live HTML from https://coinscrazy.com/bingo-blitz-free-credits/
and tests the extraction logic.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.extractors.coinscrazy import CoinsCrazyExtractor
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def test_coinscrazy_extractor_live():
    """Test the extractor with live HTML from CoinsCrazy.com"""
    
    url = "https://coinscrazy.com/bingo-blitz-free-credits/"
    
    print(f"🔍 Fetching HTML from: {url}")
    print("-" * 80)
    
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        print(f"✅ Successfully fetched HTML ({len(html)} bytes)")
        print("-" * 80)
        
        # Parse to check structure
        soup = BeautifulSoup(html, 'html.parser')
        h4_tags = soup.find_all('h4', class_='wp-block-heading')
        
        print(f"📋 Found {len(h4_tags)} h4 headings:")
        for i, h4 in enumerate(h4_tags[:5], 1):  # Show first 5
            print(f"  {i}. {h4.get_text(strip=True)[:80]}")
        print("-" * 80)
        
        # Test with today's date
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        
        print(f"🎯 Testing extraction for date: {date_str} ({today.strftime('%d %B %Y')})")
        print("-" * 80)
        
        # Create extractor and test
        extractor = CoinsCrazyExtractor()
        
        # Verify it can handle the URL
        print(f"✓ Can handle URL: {extractor.can_handle(url)}")
        
        # Extract links
        links = extractor.extract(html, date_str)
        
        print(f"\n🎉 Extracted {len(links)} links:")
        print("-" * 80)
        
        if links:
            for i, link in enumerate(links, 1):
                print(f"\n{i}. URL: {link.url}")
                print(f"   Title: {link.title}")
                print(f"   Date: {link.published_date_iso}")
        else:
            print("⚠️  No links found. Possible reasons:")
            print("   - Today's date section doesn't exist yet")
            print("   - HTML structure changed")
            print("   - Date format mismatch")
            
            print("\n💡 Try checking for yesterday's date:")
            from datetime import timedelta
            yesterday = today - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            links_yesterday = extractor.extract(html, yesterday_str)
            
            if links_yesterday:
                print(f"   Found {len(links_yesterday)} links for {yesterday.strftime('%d %B %Y')}")
                for i, link in enumerate(links_yesterday[:3], 1):
                    print(f"   {i}. {link.title}: {link.url[:60]}...")
            else:
                print("   No links found for yesterday either.")
        
        print("\n" + "=" * 80)
        print("✅ Test completed successfully!")
        
    except requests.RequestException as e:
        print(f"❌ Failed to fetch URL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_with_sample_html():
    """Test with sample HTML structure"""
    
    sample_html = """
    <h4 class="wp-block-heading has-text-align-center has-text-color has-link-color wp-elements-fd24d5c69e23d00b95335b6a51629287" style="color:#30d612">
        <strong>Updated On: 06 February 2026</strong>
    </h4>
    
    <div class="wp-block-columns is-layout-flex wp-container-core-columns-is-layout-2 wp-block-columns-is-layout-flex">
        <div class="wp-block-column is-layout-flow wp-block-column-is-layout-flow" style="flex-basis:33.33%">
            <div class="ub-button-container">
                <a href="https://bingo-app-dsa.playtika.com/bingo2-v2-bingoblitz/incentive/?incentive=53dbdb1d0d5994e5ad227468f060ecf0241ea5f36f223d7670198c1e6c17000d" target="_blank">
                    <div class="ub-button-content-holder">
                        <span class="ub-button-block-btn">01. 1+ Free Credits</span>
                    </div>
                </a>
            </div>
        </div>
        
        <div class="wp-block-column is-layout-flow wp-block-column-is-layout-flow" style="flex-basis:33.33%">
            <div class="ub-button-container">
                <a href="https://bingo-app-dsa.playtika.com/bingo2-v2-bingoblitz/incentive/?incentive=1ee3028016fd4d8d9b34f5ec559e3fb753ce7b73e6fbc5334b9144de88a53a71" target="_blank">
                    <div class="ub-button-content-holder">
                        <span class="ub-button-block-btn">02. 1+ Free Credits</span>
                    </div>
                </a>
            </div>
        </div>
    </div>
    
    <h4 class="wp-block-heading">
        <strong>05 February 2026</strong>
    </h4>
    """
    
    print("\n" + "=" * 80)
    print("🧪 Testing with sample HTML")
    print("=" * 80)
    
    extractor = CoinsCrazyExtractor()
    date_str = "2026-02-06"
    
    links = extractor.extract(sample_html, date_str)
    
    print(f"\n🎉 Extracted {len(links)} links from sample HTML:")
    print("-" * 80)
    
    for i, link in enumerate(links, 1):
        print(f"\n{i}. URL: {link.url}")
        print(f"   Title: {link.title}")
        print(f"   Date: {link.published_date_iso}")
    
    assert len(links) == 2, f"Expected 2 links, got {len(links)}"
    assert links[0].title == "01. 1+ Free Credits"
    assert links[1].title == "02. 1+ Free Credits"
    
    print("\n✅ Sample HTML test passed!")


if __name__ == "__main__":
    print("=" * 80)
    print("CoinsCrazy Extractor Test Suite")
    print("=" * 80)
    
    # Test with sample HTML first
    print("\n1️⃣ Testing with sample HTML structure...")
    test_with_sample_html()
    
    # Test with live HTML
    print("\n2️⃣ Testing with live HTML from CoinsCrazy.com...")
    test_coinscrazy_extractor_live()
