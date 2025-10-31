#!/usr/bin/env python3
"""
Test HTML Structure Monitoring System

Tests:
1. HTML fingerprint generation
2. Structure change detection
3. Extraction history tracking
4. Alert generation
5. Zero-link detection
6. Health status monitoring
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.html_monitor import get_monitor
from backend.app.scrape import fetch_html


# Sample HTML structures for testing
ORIGINAL_HTML = """
<html>
<body>
    <h1>Daily Rewards</h1>
    <h2>26 October 2025</h2>
    <div class="reward-links">
        <a href="https://example.com/link1" class="reward-link">Reward 1</a>
        <a href="https://example.com/link2" class="reward-link">Reward 2</a>
        <a href="https://example.com/link3" class="reward-link">Reward 3</a>
    </div>
    <h2>25 October 2025</h2>
    <div class="reward-links">
        <a href="https://example.com/old1">Old Reward</a>
    </div>
</body>
</html>
"""

CHANGED_HTML = """
<html>
<body>
    <h1>Daily Rewards - New Layout</h1>
    <div class="header">
        <h3>Today's Links - 26 October 2025</h3>
    </div>
    <section class="links-container">
        <div data-link="https://example.com/link1"><span>Reward 1</span></div>
        <div data-link="https://example.com/link2"><span>Reward 2</span></div>
    </section>
</body>
</html>
"""

EMPTY_HTML = """
<html>
<body>
    <h1>Daily Rewards</h1>
    <h2>26 October 2025</h2>
    <p>No rewards available today.</p>
</body>
</html>
"""


async def test_fingerprinting():
    """Test HTML fingerprint generation"""
    print("\n" + "=" * 80)
    print("TEST 1: HTML Fingerprint Generation")
    print("=" * 80)
    
    monitor = get_monitor()
    
    # Generate fingerprint for original HTML
    fp1 = monitor.compute_fingerprint(ORIGINAL_HTML)
    print(f"\n✓ Generated fingerprint:")
    print(f"  DOM Hash: {fp1.dom_hash}")
    print(f"  HTML Size: {fp1.html_size} bytes")
    print(f"  Heading Count: {fp1.heading_count}")
    print(f"  Link Count: {fp1.link_count}")
    print(f"  Critical Selectors: {fp1.critical_selectors}")
    print(f"  First 5 Headings:")
    for heading in fp1.heading_structure[:5]:
        print(f"    - {heading}")
    
    # Generate fingerprint for changed HTML
    fp2 = monitor.compute_fingerprint(CHANGED_HTML)
    print(f"\n✓ Changed HTML fingerprint:")
    print(f"  DOM Hash: {fp2.dom_hash}")
    print(f"  HTML Size: {fp2.html_size} bytes")
    print(f"  Heading Count: {fp2.heading_count}")
    print(f"  Link Count: {fp2.link_count}")
    
    # Compare
    if fp1.dom_hash != fp2.dom_hash:
        print(f"\n✓ DOM hashes are different (structure changed detected)")
    else:
        print(f"\n✗ DOM hashes are the same (no change detected)")


async def test_structure_change_detection():
    """Test structure change detection"""
    print("\n" + "=" * 80)
    print("TEST 2: Structure Change Detection")
    print("=" * 80)
    
    monitor = get_monitor()
    test_url = "https://test-site.example.com/rewards"
    
    # First extraction - establish baseline
    print(f"\n1. Recording baseline extraction...")
    monitor.record_extraction(
        source_url=test_url,
        date="2025-10-26",
        links_found=3,
        confidence=0.9,
        success=True,
        html=ORIGINAL_HTML
    )
    print(f"✓ Baseline fingerprint recorded")
    
    # Second extraction - same structure
    print(f"\n2. Testing with same structure...")
    has_changed, reasons = monitor.check_structure_change(test_url, ORIGINAL_HTML)
    if not has_changed:
        print(f"✓ No change detected (correct)")
    else:
        print(f"✗ Change detected when there shouldn't be")
        print(f"  Reasons: {reasons}")
    
    # Third extraction - changed structure
    print(f"\n3. Testing with changed structure...")
    has_changed, reasons = monitor.check_structure_change(test_url, CHANGED_HTML)
    if has_changed:
        print(f"✓ Change detected (correct)")
        print(f"  Reasons:")
        for reason in reasons:
            print(f"    - {reason}")
    else:
        print(f"✗ No change detected when structure was changed")


async def test_extraction_history():
    """Test extraction history tracking"""
    print("\n" + "=" * 80)
    print("TEST 3: Extraction History Tracking")
    print("=" * 80)
    
    monitor = get_monitor()
    test_url = "https://test-history.example.com/rewards"
    
    # Simulate multiple days of extractions
    print(f"\nSimulating 5 days of extractions...")
    
    for i in range(5):
        date = f"2025-10-{22+i:02d}"
        links = 8 if i < 4 else 0  # Last day has zero links
        confidence = 0.95 if links > 0 else 0.0
        
        monitor.record_extraction(
            source_url=test_url,
            date=date,
            links_found=links,
            confidence=confidence,
            success=links > 0,
            html=ORIGINAL_HTML if links > 0 else EMPTY_HTML
        )
        print(f"  Day {i+1} ({date}): {links} links, confidence {confidence}")
    
    # Check health status
    health = monitor.get_source_health(test_url)
    print(f"\n✓ Health Status:")
    print(f"  Status: {health['status']}")
    print(f"  Consecutive Failures: {health['consecutive_failures']}")
    print(f"  Recent Stats:")
    print(f"    - Avg Links: {health['recent_stats']['avg_links']}")
    print(f"    - Avg Confidence: {health['recent_stats']['avg_confidence']}")
    print(f"    - Success Rate: {health['recent_stats']['success_rate']}%")


async def test_alert_generation():
    """Test alert generation"""
    print("\n" + "=" * 80)
    print("TEST 4: Alert Generation")
    print("=" * 80)
    
    monitor = get_monitor()
    test_url = "https://test-alerts.example.com/rewards"
    
    # Establish baseline with successful extractions
    print(f"\n1. Establishing baseline (5 successful days)...")
    for i in range(5):
        date = f"2025-10-{21+i:02d}"
        monitor.record_extraction(
            source_url=test_url,
            date=date,
            links_found=10,
            confidence=0.9,
            success=True,
            html=ORIGINAL_HTML
        )
    print(f"✓ Baseline established")
    
    # Simulate structure change
    print(f"\n2. Simulating structure change...")
    monitor.record_extraction(
        source_url=test_url,
        date="2025-10-27",
        links_found=2,
        confidence=0.4,
        success=True,
        html=CHANGED_HTML
    )
    
    # Simulate zero links (after 12 PM, so alert should trigger)
    from datetime import datetime
    import os
    print(f"\n3. Simulating zero-link extraction...")
    monitor.record_extraction(
        source_url=test_url,
        date=datetime.now().strftime("%Y-%m-%d"),  # Today
        links_found=0,
        confidence=0.0,
        success=False,
        html=EMPTY_HTML
    )
    
    # Check alerts
    alerts = monitor.get_recent_alerts(hours=24)
    print(f"\n✓ Generated {len(alerts)} alerts:")
    for i, alert in enumerate(alerts, 1):
        print(f"\n  Alert {i}:")
        print(f"    Type: {alert.alert_type}")
        print(f"    Severity: {alert.severity}")
        print(f"    Message: {alert.message}")
        if alert.details:
            print(f"    Details: {alert.details}")


async def test_real_site():
    """Test with a real website"""
    print("\n" + "=" * 80)
    print("TEST 5: Real Website Monitoring")
    print("=" * 80)
    
    monitor = get_monitor()
    test_url = "https://simplegameguide.com/coin-master-free-spins-links/"
    
    print(f"\nFetching HTML from {test_url}...")
    try:
        html = await fetch_html(test_url)
        print(f"✓ Fetched {len(html)} bytes")
        
        # Generate fingerprint
        fp = monitor.compute_fingerprint(html)
        print(f"\n✓ Generated fingerprint:")
        print(f"  DOM Hash: {fp.dom_hash}")
        print(f"  HTML Size: {fp.html_size} bytes")
        print(f"  Heading Count: {fp.heading_count}")
        print(f"  Link Count: {fp.link_count}")
        print(f"  Critical Selectors: {fp.critical_selectors}")
        
        # Record extraction
        monitor.record_extraction(
            source_url=test_url,
            date="2025-10-27",
            links_found=10,  # Assume we extracted 10 links
            confidence=0.9,
            success=True,
            html=html
        )
        print(f"\n✓ Recorded extraction")
        
        # Get health status
        health = monitor.get_source_health(test_url)
        print(f"\n✓ Health Status: {health['status']}")
        
    except Exception as e:
        print(f"✗ Error: {e}")


async def test_health_dashboard():
    """Test health dashboard"""
    print("\n" + "=" * 80)
    print("TEST 6: Health Dashboard")
    print("=" * 80)
    
    monitor = get_monitor()
    
    all_health = monitor.get_all_health()
    
    print(f"\n✓ Monitoring {len(all_health)} sources:")
    
    for url, health in all_health.items():
        status_icon = {
            "healthy": "✅",
            "warning": "⚠️",
            "failing": "🚨",
            "unknown": "❓"
        }
        icon = status_icon.get(health['status'], "?")
        
        print(f"\n{icon} {url}")
        print(f"  Status: {health['status']}")
        print(f"  Consecutive Failures: {health['consecutive_failures']}")
        if 'recent_stats' in health:
            print(f"  Avg Links: {health['recent_stats']['avg_links']}")
            print(f"  Success Rate: {health['recent_stats']['success_rate']}%")


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("HTML STRUCTURE MONITORING SYSTEM - TEST SUITE")
    print("=" * 80)
    
    try:
        await test_fingerprinting()
        await test_structure_change_detection()
        await test_extraction_history()
        await test_alert_generation()
        await test_real_site()
        await test_health_dashboard()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80)
        
        print("\n📊 Check generated files:")
        print("  - backend/data/monitoring.json (monitoring data)")
        print("  - backend/data/alerts.json (alert history)")
        
        print("\n🌐 API Endpoints to test:")
        print("  - GET  /health/extractors (all health statuses)")
        print("  - GET  /health/extractors/<url> (specific source)")
        print("  - GET  /alerts (recent alerts)")
        print("  - GET  /alerts/unnotified (pending alerts)")
        print("  - POST /alerts/send (send notifications)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
