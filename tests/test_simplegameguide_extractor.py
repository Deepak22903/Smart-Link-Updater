"""
Test for SimpleGameGuide Extractor
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.extractors.simplegameguide import SimpleGameGuideExtractor


# Sample HTML from simplegameguide.com
SAMPLE_HTML = """
<div><strong>June 4, 2026:</strong></div>
<div class="reward-box">
  <div data-link="https://api.traveltowngame.net/public/rewardLinks/getLink/jjHtDMn4_TWI" onclick="showLink(this);">
    3. <span>10 Energy Gift</span><div class="msg"></div>
  </div>
  <div data-link="https://api.traveltowngame.net/public/rewardLinks/getLink/VuJUQBI3_WA" onclick="showLink(this);">
    2. <span>20 Energy Gift</span><div class="msg"></div>
  </div>
  <div data-link="https://api.traveltowngame.net/public/rewardLinks/getLink/qUO0j7yV_FCB" onclick="showLink(this);">
    1. <span>25 Energy Gift</span><div class="msg"></div>
  </div>
</div>
<div><strong>June 3, 2026:</strong></div>
"""

def test_simplegameguide_extractor_format3():
    """Test extracting links using the new 'Month Day, Year:' format."""
    extractor = SimpleGameGuideExtractor()
    links = extractor.extract(SAMPLE_HTML, "2026-06-04")
    
    assert len(links) == 3
    
    assert str(links[0].url) == "https://api.traveltowngame.net/public/rewardLinks/getLink/jjHtDMn4_TWI"
    assert links[0].title == "10 Energy Gift"
    assert links[0].published_date_iso == "2026-06-04"

    assert str(links[1].url) == "https://api.traveltowngame.net/public/rewardLinks/getLink/VuJUQBI3_WA"
    assert links[1].title == "20 Energy Gift"
    assert links[1].published_date_iso == "2026-06-04"

    assert str(links[2].url) == "https://api.traveltowngame.net/public/rewardLinks/getLink/qUO0j7yV_FCB"
    assert links[2].title == "25 Energy Gift"
    assert links[2].published_date_iso == "2026-06-04"

def test_simplegameguide_extractor_no_match():
    """Test extracting links when the date doesn't match."""
    extractor = SimpleGameGuideExtractor()
    # Try a date that isn't in the HTML
    links = extractor.extract(SAMPLE_HTML, "2026-06-05")
    
    assert len(links) == 0

def test_simplegameguide_extractor_empty_html():
    """Test extracting links with empty HTML."""
    extractor = SimpleGameGuideExtractor()
    links = extractor.extract("", "2026-06-04")
    assert len(links) == 0
