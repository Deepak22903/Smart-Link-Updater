"""
Test for Gamesbie Promo Code Extractor
"""

import pytest
from bs4 import BeautifulSoup
from backend.app.extractors.gamesbie import GamesbieExtractor


# Sample HTML from gamesbie.com
SAMPLE_HTML = """
<h2 class="wp-block-heading">Top Heroes Gift Codes: Active (January)</h2>
<ul class="wp-block-list">
<li><strong>5045BB1614</strong>–<em>(Valid until: 5th January 2026)</em></li>
<li><strong>9AC5D3369B</strong>&nbsp;–<em>(Valid until: 31st January 2026)</em></li>
<li><strong>5777F1FDC0</strong>&nbsp;–<em>(Valid until: 29th January 2026)</em></li>
<li><strong>843955BEE</strong>&nbsp;–<em>(Valid until: 23rd January 2026)</em></li>
<li><strong>9399F9834</strong>–<em>(Valid until: 22nd January 2026)</em></li>
<li><strong>5446C3EA</strong> –<em>(Valid until: 15th January 2026)</em></li>
<li><strong>D7EF4423</strong> –<em>(Valid until: 8th January 2026)</em></li>
</ul>
<p><strong>Expired Codes</strong></p>
<ul class="wp-block-list">
<li><strong>DB70EAC6B</strong> – <em><em><em>Expired</em></em></em></li>
<li><strong>71FD831C6</strong> – <em><em>Expired</em></em></li>
<li><strong>D1E74B056F</strong>–<em>Expired</em> </li>
<li><strong>1BF6F5CA</strong> – <em>Expired</em></li>
</ul>
"""


@pytest.fixture
def extractor():
    return GamesbieExtractor()


class TestGamesbieExtractor:
    
    def test_can_handle_gamesbie_url(self, extractor):
        """Test that extractor handles gamesbie.com URLs."""
        assert extractor.can_handle("https://gamesbie.com/top-heroes-gift-codes/")
        assert extractor.can_handle("https://www.gamesbie.com/some-page")
        assert not extractor.can_handle("https://example.com/page")
    
    def test_supports_promo_codes(self, extractor):
        """Test that extractor supports promo codes."""
        assert extractor.supports_promo_codes() is True
        assert "promo_codes" in extractor.supported_extraction_modes()
    
    def test_extract_active_codes_only(self, extractor):
        """Test that only active (non-expired) codes are extracted."""
        # Test with a date where some codes are still valid
        result = extractor.extract_promo_codes(
            SAMPLE_HTML,
            "2026-01-20"  # Date where codes expiring after this are still valid
        )
        
        # Should have promo codes (returns List[PromoCode])
        assert len(result) > 0
        
        # Get all extracted code values
        codes = [pc.code for pc in result]
        
        # Codes valid after Jan 20 should be included
        assert "9AC5D3369B" in codes  # Valid until 31st Jan
        assert "5777F1FDC0" in codes  # Valid until 29th Jan
        assert "843955BEE" in codes   # Valid until 23rd Jan
        assert "9399F9834" in codes   # Valid until 22nd Jan
        
        # Codes expired before Jan 20 should NOT be included
        assert "5045BB1614" not in codes  # Valid until 5th Jan - expired
        assert "5446C3EA" not in codes    # Valid until 15th Jan - expired
        assert "D7EF4423" not in codes    # Valid until 8th Jan - expired
        
        # Expired codes section should never be included
        assert "DB70EAC6B" not in codes
        assert "71FD831C6" not in codes
    
    def test_extract_all_codes_early_date(self, extractor):
        """Test extraction when all active codes are still valid."""
        result = extractor.extract_promo_codes(
            SAMPLE_HTML,
            "2026-01-01"  # Early date - all active codes should be valid
        )
        
        codes = [pc.code for pc in result]
        
        # All codes in active section should be present
        assert "5045BB1614" in codes
        assert "9AC5D3369B" in codes
        assert "5777F1FDC0" in codes
        assert "843955BEE" in codes
        assert "9399F9834" in codes
        assert "5446C3EA" in codes
        assert "D7EF4423" in codes
        
        # Total should be 7 active codes
        assert len(result) == 7
    
    def test_expiry_date_parsing(self, extractor):
        """Test that expiry dates are correctly parsed."""
        result = extractor.extract_promo_codes(
            SAMPLE_HTML,
            "2026-01-01"
        )
        
        # Find a specific code and check its expiry
        code_5045 = next((pc for pc in result if pc.code == "5045BB1614"), None)
        assert code_5045 is not None
        assert code_5045.expiry_date == "2026-01-05"
        
        code_9ac5 = next((pc for pc in result if pc.code == "9AC5D3369B"), None)
        assert code_9ac5 is not None
        assert code_9ac5.expiry_date == "2026-01-31"
    
    def test_promo_code_structure(self, extractor):
        """Test that extracted promo codes have correct structure."""
        result = extractor.extract_promo_codes(
            SAMPLE_HTML,
            "2026-01-01"
        )
        
        # Check first promo code structure
        pc = result[0]
        assert pc.code is not None and len(pc.code) > 0
        assert pc.published_date_iso == "2026-01-01"
        assert pc.category == "gift_code"
    
    def test_no_active_header(self, extractor):
        """Test handling of HTML without active header."""
        html = """
        <h2>Some Other Header</h2>
        <ul><li><strong>CODE123</strong></li></ul>
        """
        result = extractor.extract_promo_codes(html, "2026-01-01")
        assert len(result) == 0
    
    def test_empty_html(self, extractor):
        """Test handling of empty HTML."""
        result = extractor.extract_promo_codes("", "2026-01-01")
        assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
