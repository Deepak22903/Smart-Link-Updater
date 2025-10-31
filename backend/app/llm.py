import os
from typing import List, Optional
from .models import Link, ExtractionResult
from .gemini_client import call_gemini
from bs4 import BeautifulSoup

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("GEMINI_MIN_CONFIDENCE", "0.5"))

# Schema for finding relevant headings
HEADING_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "heading_indices": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Array of heading indices that likely contain today's links (max 2)"
        },
        "reasoning": {"type": "string"}
    },
    "required": ["heading_indices"]
}

# Schema for extracting links from selected sections
GEMINI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "title": {"type": "string"},
                    "published_date_iso": {"type": "string"},
                    "section_heading": {"type": "string"},
                    "summary": {"type": "string"}
                },
                "required": ["url", "title", "published_date_iso", "section_heading"]
            }
        },
        "confidence": {"type": "number"},
        "extraction_notes": {"type": "string"}
    },
    "required": ["links", "confidence"]
}


def extract_headings_from_html(html: str) -> List[tuple]:
    """
    Extract all headings (h1-h6, strong, div with date-like text) from HTML.
    Returns list of (index, tag, text, next_content_preview) tuples.
    """
    soup = BeautifulSoup(html, 'html.parser')
    headings = []
    
    # Find h1-h6 tags
    for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        for tag in soup.find_all(tag_name):
            text = tag.get_text(strip=True)
            if text:
                # Get preview of content after this heading
                next_sibling = tag.find_next_sibling()
                preview = ""
                if next_sibling:
                    preview = next_sibling.get_text(strip=True)[:200]
                headings.append((len(headings), tag_name, text, preview, tag))
    
    # Find <strong> tags that look like date headers
    for div in soup.find_all('div'):
        strong = div.find('strong')
        if strong:
            text = strong.get_text(strip=True)
            # Only include if it looks like a date (contains numbers and common date words)
            if text and (any(char.isdigit() for char in text) or 
                        any(month in text.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])):
                next_sibling = div.find_next_sibling()
                preview = ""
                if next_sibling:
                    preview = next_sibling.get_text(strip=True)[:200]
                headings.append((len(headings), 'strong', text, preview, div))
    
    return headings


def build_heading_selection_prompt(headings: List[tuple], today_iso: str) -> str:
    """Build prompt to ask Gemini which headings contain today's links."""
    from datetime import datetime
    try:
        dt = datetime.strptime(today_iso, "%Y-%m-%d")
        date_formats = [
            today_iso,
            dt.strftime("%d %B %Y"),
            dt.strftime("%B %d, %Y"),
            dt.strftime("%b %d, %Y"),
            dt.strftime("%b %d, %Y:"),
        ]
        date_examples = " or ".join([f'"{d}"' for d in date_formats])
    except:
        date_examples = f'"{today_iso}"'
    
    # Format headings for display
    heading_list = []
    for idx, tag, text, preview, _ in headings[:50]:  # Limit to first 50 headings
        heading_list.append(f"{idx}. [{tag}] {text}")
        if preview:
            heading_list.append(f"   Preview: {preview[:150]}...")
    
    headings_text = "\n".join(heading_list)
    
    return f"""You are analyzing headings from a gaming rewards website to find today's reward links.

**Task:** Identify which heading(s) most likely contain reward links for today's date: {date_examples}

**Headings found on the page:**
{headings_text}

**Instructions:**
1. Look for headings that match today's date ({today_iso})
2. Return the indices (0-based) of the TOP 2 most relevant headings
3. If you find an exact match, include it first
4. Consider headings with dates, "today", "latest", "new", etc.

**Return format:** JSON with "heading_indices" array containing max 2 numbers.
"""


def build_extraction_prompt(html_sections: str, today_iso: str) -> str:
    """Build prompt to extract links from selected HTML sections."""
    from datetime import datetime
    try:
        dt = datetime.strptime(today_iso, "%Y-%m-%d")
        date_formats = [
            today_iso,
            dt.strftime("%d %B %Y"),
            dt.strftime("%b %d, %Y:"),
        ]
        date_examples = " or ".join([f'"{d}"' for d in date_formats])
    except:
        date_examples = f'"{today_iso}"'
    
    return f"""Extract reward links from the HTML sections below. These sections were identified as containing today's ({date_examples}) reward links.

**CRITICAL: Look for these link patterns:**
1. <a href="URL">Title</a>
2. <div data-link="URL"><span>Title</span></div>  ← VERY IMPORTANT!
3. Any element with data-link="..." attribute

**For each link found:**
- url: Full URL (from href or data-link)
- title: Link text or span text (e.g., "50 spins")
- published_date_iso: "{today_iso}"
- section_heading: The heading text

**Confidence scoring:**
- 0.9-1.0: Found multiple reward links with clear URLs
- 0.7-0.8: Found some links
- 0.5-0.6: Uncertain
- Below 0.5: No clear links found

**HTML Sections:**
{html_sections}
"""


async def parse_links_with_gemini(html: str, today_iso: str, timezone: str) -> ExtractionResult:
    """
    Two-stage Gemini extraction:
    1. Extract headings and ask Gemini which ones contain today's links
    2. Send only those sections to Gemini for detailed extraction
    
    This is more efficient and accurate than sending all HTML.
    """
    # Check API key at runtime
    if not os.getenv("GEMINI_API_KEY"):
        return ExtractionResult(links=[], only_today=True, confidence=0.0)
    
    try:
        # STAGE 1: Extract all headings from HTML
        headings = extract_headings_from_html(html)
        
        if not headings:
            # No headings found
            return ExtractionResult(links=[], only_today=True, confidence=0.0)
        
        # Ask Gemini which headings are relevant
        heading_prompt = build_heading_selection_prompt(headings, today_iso)
        heading_response = call_gemini(heading_prompt, HEADING_SELECTION_SCHEMA)
        
        selected_indices = heading_response.get("heading_indices", [])
        
        if not selected_indices:
            # Gemini couldn't find relevant headings
            return ExtractionResult(links=[], only_today=True, confidence=0.0)
        
        # STAGE 2: Extract HTML content from selected headings
        soup = BeautifulSoup(html, 'html.parser')
        html_sections = []
        
        for idx in selected_indices[:2]:  # Max 2 sections
            if idx < len(headings):
                _, tag_name, text, _, element = headings[idx]
                
                # Get the heading and its next sibling (the content)
                section_html = f"<{tag_name}>{text}</{tag_name}>\n"
                
                next_sibling = element.find_next_sibling()
                if next_sibling:
                    section_html += str(next_sibling)[:5000]  # Limit section size
                
                html_sections.append(section_html)
        
        combined_sections = "\n\n".join(html_sections)
        
        # Ask Gemini to extract links from these sections
        extraction_prompt = build_extraction_prompt(combined_sections, today_iso)
        response_data = call_gemini(extraction_prompt, GEMINI_RESPONSE_SCHEMA)
        
        # Validate confidence
        confidence = response_data.get("confidence", 0.0)
        if confidence < MIN_CONFIDENCE_THRESHOLD:
            return ExtractionResult(links=[], only_today=True, confidence=confidence)
        
        # Parse links
        links = []
        for link_data in response_data.get("links", []):
            try:
                link = Link(
                    url=link_data["url"],
                    title=link_data["title"],
                    published_date_iso=link_data["published_date_iso"],
                    summary=link_data.get("summary"),
                    category=None
                )
                links.append(link)
            except Exception:
                continue
        
        return ExtractionResult(
            links=links,
            only_today=True,
            confidence=confidence
        )
    
    except Exception as e:
        print(f"Gemini extraction error: {e}")
        return ExtractionResult(links=[], only_today=True, confidence=0.0)

