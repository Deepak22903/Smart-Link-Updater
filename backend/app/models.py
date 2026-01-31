from pydantic import BaseModel, HttpUrl, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class Link(BaseModel):
    url: HttpUrl
    title: str
    published_date_iso: str  # YYYY-MM-DD
    summary: Optional[str] = None
    category: Optional[str] = None
    target: Optional[str] = "_blank"  # "_blank" for new tab, "_self" for same tab

    class Config:
        json_encoders = {
            HttpUrl: str
        }


class PromoCode(BaseModel):
    """Represents a promotional/coupon code extracted from a source"""
    code: str  # The actual promo code (e.g., "SAVE20", "FREESPINS100")
    description: Optional[str] = None  # What the code offers (e.g., "20% off", "100 free spins")
    published_date_iso: str  # YYYY-MM-DD
    expiry_date: Optional[str] = None  # When the code expires (YYYY-MM-DD or descriptive)
    source_url: Optional[str] = None  # Where the code came from
    category: Optional[str] = None  # Type of code (discount, bonus, free spins, etc.)
    
    class Config:
        json_encoders = {
            HttpUrl: str
        }


class ExtractionResult(BaseModel):
    links: List[Link]
    promo_codes: List[PromoCode] = []  # NEW: Extracted promo codes
    only_today: bool
    confidence: float


class HTMLFingerprint(BaseModel):
    """Tracks HTML structure for change detection"""
    dom_hash: str  # Hash of DOM structure
    heading_structure: List[str]  # List of headings like ["h2:Working Links", "h3:26 October"]
    critical_selectors: List[str]  # CSS selectors that must exist
    html_size: int  # Size in bytes
    last_updated: str  # ISO timestamp
    heading_count: int  # Total number of headings
    link_count: int  # Total number of links in page


class ExtractionHistory(BaseModel):
    """Single extraction attempt record"""
    date: str  # YYYY-MM-DD
    links_found: int
    confidence: float
    timestamp: str  # ISO timestamp
    success: bool
    error: Optional[str] = None
    
    @field_validator('success', mode='before')
    @classmethod
    def validate_success(cls, v):
        """Handle various boolean representations and invalid data"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            # If it's HTML or a long string, it's probably an error - treat as False
            if v.lower().strip() in ('true', '1', 'yes'):
                return True
            elif v.lower().strip() in ('false', '0', 'no', ''):
                return False
            # If it contains HTML tags, it's probably an error response
            if '<' in v or len(v) > 100:
                return False
        # Any other type, try to coerce to bool
        return bool(v)


class SourceMonitoring(BaseModel):
    """Complete monitoring data for a source URL"""
    source_url: str
    fingerprint: Optional[HTMLFingerprint] = None
    extraction_history: List[ExtractionHistory] = []
    last_check: str  # ISO timestamp
    status: str = "healthy"  # healthy, warning, failing
    consecutive_failures: int = 0


class Alert(BaseModel):
    """Alert/notification record"""
    alert_type: str  # structure_changed, zero_links, low_confidence, size_anomaly
    source_url: str
    severity: str  # info, warning, critical
    message: str
    timestamp: str  # ISO timestamp
    notified: bool = False
    details: Optional[Dict[str, Any]] = None
