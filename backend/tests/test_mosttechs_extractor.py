from backend.app.extractors.mosttechs import MostTechsExtractor
from bs4 import BeautifulSoup

# Sample HTML for testing
sample_html = """
<p><span style="font-size: 14pt; font-family: georgia, palatino, serif;"><strong>30 Oct 2025</strong></span></p>
<div class="code-block code-block-2" style="margin: 8px auto; text-align: center; display: block; clear: both;">
<script async="" crossorigin="anonymous" data-type="lazy" data-src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6083127936669475" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6083127936669475"></script>
<!-- demo -->
<ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-6083127936669475" data-ad-slot="5607431116" data-ad-format="auto" data-full-width-responsive="true" data-adsbygoogle-status="done"><iframe id="aswift_1" style="height: 1px !important; max-height: 1px !important; max-width: 1px !important; width: 1px !important;"><iframe id="google_ads_frame1"></iframe></iframe></ins>
<script>
     (adsbygoogle = window.adsbygoogle || []).push({});
</script></div>
<p>6.<a href="https://traveltown-lp.onelink.me/nmEz/qfp5oroo">25 energy link</a></p>
<p>5.<a href="https://api.traveltowngame.net/public/rewardLinks/getLink/XCXJF4dz_TRADING">25 energy link</a></p>
<p><span style="font-size: 14pt; font-family: georgia, palatino, serif;"><strong>29 Oct 2025</strong></span></p>
"""

def test_mosttechs_extractor():
    extractor = MostTechsExtractor()
    date = "30 Oct 2025"

    # Parse the HTML
    soup = BeautifulSoup(sample_html, 'html.parser')
    html = str(soup)

    # Extract links
    links = extractor.extract(html, date)

    # Print results for debugging
    print("Extracted Links:")
    for link in links:
        print(f"Title: {link.title}, URL: {link.url}, Date: {link.published_date_iso}")

if __name__ == "__main__":
    test_mosttechs_extractor()