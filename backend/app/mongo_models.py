"""
MongoDB Models for SmartLinkUpdater

All data models designed for MongoDB storage with proper indexing.
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(str):
    """Custom ObjectId type for Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])
    
    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
        raise ValueError("Invalid ObjectId")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema, handler):
        return {"type": "string"}


class MongoBaseModel(BaseModel):
    """Base model with MongoDB _id field"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# ==================== Post Configuration Models ====================

class PostConfig(MongoBaseModel):
    """
    Post configuration stored in 'posts' collection.
    
    Indexes:
    - post_id (unique) - DEPRECATED: Use content_slug as primary identifier
    - wp_site.base_url
    - content_slug (unique) - NEW: Universal identifier across all sites
    
    Multi-Site Support:
    - content_slug: Unique identifier for the content (e.g., "coin-master-free-spins")
    - site_post_ids: Maps site_key -> post_id for each WordPress site
      Example: {"minecraft": 105, "casino": 89, "this": 105}
    - When updating, system uses site_post_ids[site_key] to get the correct post ID
    
    New in v2: extractor_map for per-source extractor configuration
    - extractor_map: {"url": "extractor_name"} - Maps each source URL to its extractor
    - URLs not in extractor_map will default to Gemini extractor
    
    New in v2.3: Simplified link insertion
    - Links are automatically inserted after the first <h2> tag
    - Falls back to prepending if no <h2> found
    """
    post_id: int  # DEPRECATED: Kept for backward compatibility, use site_post_ids instead
    content_slug: Optional[str] = None  # NEW: Universal identifier (e.g., "coin-master-free-spins")
    site_post_ids: Optional[Dict[str, int]] = None  # NEW: Maps site_key -> post_id
    source_urls: List[str]
    timezone: str = "Asia/Kolkata"
    extractor: Optional[str] = None  # Deprecated: kept for backward compatibility
    extractor_map: Optional[Dict[str, str]] = None  # Per-source extractor mapping (manual or smart match)
    wp_site: Optional[Dict[str, str]] = None  # {"base_url": "...", "username": "...", "app_password": "..."}
    insertion_point: Optional[Dict[str, str]] = None  # Deprecated: kept for backward compatibility
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== Fingerprint Models ====================

class LinkFingerprint(MongoBaseModel):
    """
    Link fingerprints for deduplication stored in 'fingerprints' collection.
    
    Indexes:
    - post_id + date_iso (compound, unique)
    - post_id
    - date_iso
    """
    post_id: int
    date_iso: str  # YYYY-MM-DD
    fingerprints: List[str]  # List of link fingerprint hashes
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== Monitoring Models ====================

class HTMLFingerprint(BaseModel):
    """Tracks HTML structure for change detection"""
    dom_hash: str
    heading_structure: List[str]
    critical_selectors: List[str]
    html_size: int
    last_updated: str
    heading_count: int
    link_count: int


class ExtractionHistory(BaseModel):
    """Single extraction attempt record"""
    date: str  # YYYY-MM-DD
    links_found: int
    confidence: float
    timestamp: str
    success: bool
    error: Optional[str] = None


class SourceMonitoring(MongoBaseModel):
    """
    HTML monitoring data stored in 'monitoring' collection.
    
    Indexes:
    - source_url (unique)
    - status
    - last_check
    """
    source_url: str
    fingerprint: Optional[HTMLFingerprint] = None
    extraction_history: List[ExtractionHistory] = []
    last_check: str
    status: str = "healthy"  # healthy, warning, failing
    consecutive_failures: int = 0


# ==================== Alert Models ====================

class Alert(MongoBaseModel):
    """
    Alert/notification records stored in 'alerts' collection.
    
    Indexes:
    - source_url
    - alert_type
    - timestamp
    - notified
    """
    alert_type: str  # structure_changed, zero_links, low_confidence, size_anomaly, link_count_drop
    source_url: str
    severity: str  # info, warning, critical
    message: str
    timestamp: str
    notified: bool = False
    details: Optional[Dict[str, Any]] = None


# ==================== Batch Update Models ====================

class PostUpdateState(BaseModel):
    """State for a single post update within a batch"""
    post_id: int
    status: str  # queued, running, success, no_changes, failed
    progress: int = 0  # 0-100
    message: str = "Queued"
    links_found: int = 0
    links_added: int = 0
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    logs: List[str] = []


class BatchUpdateRequest(MongoBaseModel):
    """
    Batch update request stored in 'batch_requests' collection.
    
    Indexes:
    - request_id (unique)
    - created_at
    - overall_status
    - initiator
    """
    request_id: str
    post_ids: List[int]
    initiator: str = "unknown"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    overall_status: str = "queued"  # queued, running, success, no_changes, partial, failed
    posts: Dict[str, PostUpdateState] = {}  # key: post_id as string


# ==================== Update History Models ====================

class LinkUpdateHistory(MongoBaseModel):
    """
    Historical record of link updates stored in 'update_history' collection.
    
    Indexes:
    - post_id + date_iso (compound)
    - post_id
    - date_iso
    - timestamp
    """
    post_id: int
    date_iso: str  # YYYY-MM-DD
    links_found: int
    links_added: int
    source_urls: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None  # Link to batch request if applicable
    success: bool = True
    error: Optional[str] = None
