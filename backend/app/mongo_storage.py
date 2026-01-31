"""
MongoDB Storage Layer

Replaces JSON file-based storage with MongoDB for all data operations.
"""

from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

from .mongo_models import (
    PostConfig,
    LinkFingerprint,
    SourceMonitoring,
    Alert,
    BatchUpdateRequest,
    PostUpdateState,
    LinkUpdateHistory
)

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class MongoDBStorage:
    """MongoDB storage manager with connection pooling"""
    
    _instance = None
    _client = None
    _db = None
    _connected = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBStorage, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Don't connect immediately - use lazy connection
        pass
    
    def _ensure_connection(self):
        """Lazy connection to MongoDB"""
        if self._connected and self._client:
            return
            
        try:
            self._connect()
            self._connected = True
        except Exception as e:
            print(f"Warning: MongoDB connection failed: {e}")
            print("Application will continue without database connectivity")
            self._connected = False
            raise
    
    def _connect(self):
        """Initialize MongoDB connection"""
        connection_string = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://deepakshitole4_db_user:6KiH8syvWCTNhh2D@smartlinkupdater.rpo4hmt.mongodb.net/SmartLinkUpdater?appName=SmartLinkUpdater"
        )
        database_name = os.getenv("MONGODB_DATABASE", "SmartLinkUpdater")
        
        # Connection options for better reliability
        self._client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=10000,         # 10 second connect timeout
            socketTimeoutMS=10000,          # 10 second socket timeout
            maxPoolSize=10,                 # Connection pool size
            retryWrites=True,
            retryReads=True
        )
        
        # Test the connection
        self._client.admin.command('ping')
        
        self._db = self._client[database_name]
        print(f"Connected to MongoDB database: {database_name}")
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create all necessary indexes"""
        try:
            # Posts collection
            self._db.posts.create_index("post_id", unique=True)
            self._db.posts.create_index("wp_site.base_url")
            self._db.posts.create_index("content_slug", unique=True, sparse=True)  # NEW: Universal identifier
            
            # Fingerprints collection - site-specific tracking
            # Note: Removed old unique index on (post_id, date_iso) to allow multiple entries per site
            self._db.fingerprints.create_index([("post_id", ASCENDING), ("date_iso", ASCENDING), ("site_key", ASCENDING)], unique=True)
            self._db.fingerprints.create_index("post_id")
            self._db.fingerprints.create_index("date_iso")
            self._db.fingerprints.create_index("site_key")
            
            # Monitoring collection
            self._db.monitoring.create_index("url", unique=True)
            self._db.monitoring.create_index("last_checked")
            
            # Alerts collection
            self._db.alerts.create_index("alert_type")
            self._db.alerts.create_index("timestamp")
            self._db.alerts.create_index("url")
            
            # Batch requests collection
            self._db.batch_requests.create_index("request_id", unique=True)
            self._db.batch_requests.create_index("created_at")
            
            # Update history collection
            self._db.update_history.create_index("post_id")
            self._db.update_history.create_index("date_iso")
            self._db.update_history.create_index("timestamp")
            
            # WordPress sites collection
            self._db.wp_sites.create_index("site_key", unique=True)
            self._db.wp_sites.create_index("created_at")
            
            # Settings collection
            self._db.settings.create_index("setting_key", unique=True)
            
            print("Database indexes created successfully")
        except Exception as e:
            print(f"Warning: Failed to create indexes: {e}")
            # Don't raise - allow app to continue without indexes
    
    @property
    def db(self):
        """Get database instance"""
        self._ensure_connection()
        return self._db
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()


# Lazy singleton instance
_storage = None

def _get_storage() -> MongoDBStorage:
    """Get MongoDB storage instance with lazy initialization"""
    global _storage
    if _storage is None:
        _storage = MongoDBStorage()
    return _storage


# ==================== Post Configuration Operations ====================

def get_post_config(post_id: int) -> Optional[Dict[str, Any]]:
    """Get post configuration by post_id (legacy method)"""
    try:
        result = _get_storage().db.posts.find_one({"post_id": post_id})
        if result:
            # Convert ObjectId to string for JSON serialization
            result["_id"] = str(result["_id"])
        return result
    except Exception as e:
        print(f"Database error in get_post_config: {e}")
        return None


def get_post_config_by_slug(content_slug: str) -> Optional[Dict[str, Any]]:
    """Get post configuration by content_slug (NEW: multi-site support)"""
    try:
        result = _get_storage().db.posts.find_one({"content_slug": content_slug})
        if result:
            # Convert ObjectId to string for JSON serialization
            result["_id"] = str(result["_id"])
        return result
    except Exception as e:
        print(f"Database error in get_post_config_by_slug: {e}")
        return None


def set_post_config(post_config: Dict[str, Any]) -> bool:
    """Save or update post configuration"""
    try:
        # Strategy for updating:
        # 1. If content_slug is provided, try to find by content_slug first
        # 2. If not found by content_slug, try to find by post_id
        # 3. This allows migration from post_id-based to content_slug-based configs
        
        query = None
        
        if "content_slug" in post_config and post_config["content_slug"]:
            # Try to find by content_slug first
            existing = _get_storage().db.posts.find_one({"content_slug": post_config["content_slug"]})
            if existing:
                query = {"content_slug": post_config["content_slug"]}
            else:
                # If not found by slug, try by post_id (for migration)
                existing = _get_storage().db.posts.find_one({"post_id": post_config["post_id"]})
                if existing:
                    query = {"post_id": post_config["post_id"]}
                else:
                    # New document, use content_slug as primary key
                    query = {"content_slug": post_config["content_slug"]}
        else:
            # No content_slug, use post_id (backward compatibility)
            query = {"post_id": post_config["post_id"]}
        
        # Remove _id from post_config to avoid modifying immutable field
        update_data = {k: v for k, v in post_config.items() if k != '_id'}
            
        _get_storage().db.posts.update_one(
            query,
            {"$set": update_data},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Database error in set_post_config: {e}")
        return False


def list_configured_posts() -> List[Dict[str, Any]]:
    """Get all configured posts"""
    try:
        posts = list(_get_storage().db.posts.find({}).sort("post_id", ASCENDING))
        # Convert ObjectId to string for JSON serialization
        for post in posts:
            if "_id" in post:
                post["_id"] = str(post["_id"])
        return posts
    except Exception as e:
        print(f"Database error in list_configured_posts: {e}")
        return []


def delete_post_config(post_id: int) -> bool:
    """Delete post configuration"""
    result = _get_storage().db.posts.delete_one({"post_id": post_id})
    return result.deleted_count > 0


# ==================== WordPress Sites Operations ====================

def get_all_wp_sites() -> Dict[str, Dict[str, Any]]:
    """Get all configured WordPress sites from MongoDB"""
    try:
        sites = {}
        for site_doc in _get_storage().db.wp_sites.find({}):
            site_key = site_doc.get("site_key")
            if site_key:
                sites[site_key] = {
                    "base_url": site_doc.get("base_url"),
                    "username": site_doc.get("username"),
                    "app_password": site_doc.get("app_password"),
                    "display_name": site_doc.get("display_name"),
                    "button_style": site_doc.get("button_style", "default"),
                    "created_at": site_doc.get("created_at"),
                    "updated_at": site_doc.get("updated_at")
                }
        return sites
    except Exception as e:
        print(f"Database error in get_all_wp_sites: {e}")
        return {}


def get_wp_site(site_key: str) -> Optional[Dict[str, Any]]:
    """Get a specific WordPress site configuration"""
    try:
        result = _get_storage().db.wp_sites.find_one({"site_key": site_key})
        if result:
            result.pop("_id", None)  # Remove MongoDB ID
        return result
    except Exception as e:
        print(f"Database error in get_wp_site: {e}")
        return None


def set_wp_site(site_key: str, site_config: Dict[str, Any]) -> bool:
    """Save or update WordPress site configuration"""
    try:
        site_data = {
            "site_key": site_key,
            "base_url": site_config.get("base_url"),
            "username": site_config.get("username"),
            "app_password": site_config.get("app_password"),
            "display_name": site_config.get("display_name", site_key),
            "button_style": site_config.get("button_style", "default"),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add created_at only for new documents
        existing = _get_storage().db.wp_sites.find_one({"site_key": site_key})
        if not existing:
            site_data["created_at"] = datetime.utcnow().isoformat()
        
        _get_storage().db.wp_sites.update_one(
            {"site_key": site_key},
            {"$set": site_data},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Database error in set_wp_site: {e}")
        return False


def delete_wp_site(site_key: str) -> bool:
    """Delete WordPress site configuration"""
    try:
        result = _get_storage().db.wp_sites.delete_one({"site_key": site_key})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Database error in delete_wp_site: {e}")
        return False


# ==================== Fingerprint Operations ====================

def get_known_fingerprints(post_id: int, date_iso: str, site_key: str = None) -> Set[str]:
    """
    Get known fingerprints for a post and date, optionally filtered by site.
    
    Args:
        post_id: The post ID
        date_iso: The date in ISO format
        site_key: Optional site key to get site-specific fingerprints
        
    Returns:
        Set of known fingerprints
    """
    try:
        query = {"post_id": post_id, "date_iso": date_iso}
        if site_key:
            query["site_key"] = site_key
            
        result = _get_storage().db.fingerprints.find_one(query)
        if result and "fingerprints" in result:
            return set(result["fingerprints"])
        return set()
    except Exception as e:
        print(f"Database error in get_known_fingerprints: {e}")
        return set()


def save_new_links(post_id: int, date_iso: str, fingerprints: Set[str], site_key: str = None) -> None:
    """
    Save new link fingerprints (merge with existing) for a specific site.
    
    Args:
        post_id: The post ID
        date_iso: The date in ISO format
        fingerprints: Set of fingerprints to save
        site_key: Optional site key for site-specific tracking
    """
    existing = get_known_fingerprints(post_id, date_iso, site_key)
    merged = list(existing.union(fingerprints))
    
    query = {"post_id": post_id, "date_iso": date_iso}
    if site_key:
        query["site_key"] = site_key
    
    _get_storage().db.fingerprints.update_one(
        query,
        {
            "$set": {
                "fingerprints": merged,
                "updated_at": datetime.utcnow().isoformat()
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow().isoformat(),
                "site_key": site_key
            }
        },
        upsert=True
    )


def get_post_fingerprints_history(post_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    """Get fingerprint history for a post"""
    results = list(
        _get_storage().db.fingerprints
        .find({"post_id": post_id})
        .sort("date_iso", DESCENDING)
        .limit(limit)
    )
    for result in results:
        result.pop("_id", None)
    return results


# ==================== Promo Code Fingerprint Operations ====================

def get_known_promo_fingerprints(post_id: int, date_iso: str, site_key: str = None) -> Set[str]:
    """
    Get known promo code fingerprints for a post/date/site combination.
    
    Args:
        post_id: The post ID
        date_iso: The date in ISO format
        site_key: Optional site key to get site-specific fingerprints
        
    Returns:
        Set of known promo code fingerprints
    """
    try:
        query = {"post_id": post_id, "date_iso": date_iso, "type": "promo_code"}
        if site_key:
            query["site_key"] = site_key
            
        result = _get_storage().db.fingerprints.find_one(query)
        if result and "fingerprints" in result:
            return set(result["fingerprints"])
        return set()
    except Exception as e:
        print(f"Database error in get_known_promo_fingerprints: {e}")
        return set()


def save_new_promo_codes(post_id: int, date_iso: str, fingerprints: Set[str], site_key: str = None) -> None:
    """
    Save new promo code fingerprints (merge with existing) for a specific site.
    
    Args:
        post_id: The post ID
        date_iso: The date in ISO format
        fingerprints: Set of promo code fingerprints to save
        site_key: Optional site key for site-specific tracking
    """
    existing = get_known_promo_fingerprints(post_id, date_iso, site_key)
    merged = list(existing.union(fingerprints))
    
    query = {"post_id": post_id, "date_iso": date_iso, "type": "promo_code"}
    if site_key:
        query["site_key"] = site_key
    
    _get_storage().db.fingerprints.update_one(
        query,
        {
            "$set": {
                "fingerprints": merged,
                "updated_at": datetime.utcnow().isoformat()
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow().isoformat(),
                "site_key": site_key,
                "type": "promo_code"
            }
        },
        upsert=True
    )


# ==================== Monitoring Operations ====================

def get_source_monitoring(source_url: str) -> Optional[Dict[str, Any]]:
    """Get monitoring data for a source URL"""
    result = _get_storage().db.monitoring.find_one({"source_url": source_url})
    if result:
        result.pop("_id", None)
        return result
    return None


def save_source_monitoring(monitoring_data: Dict[str, Any]) -> None:
    """Save or update monitoring data for a source URL"""
    source_url = monitoring_data["source_url"]
    monitoring_data["last_check"] = datetime.utcnow().isoformat()
    
    _get_storage().db.monitoring.update_one(
        {"source_url": source_url},
        {"$set": monitoring_data},
        upsert=True
    )


def get_all_source_monitoring() -> Dict[str, Dict[str, Any]]:
    """Get all monitoring data"""
    results = _get_storage().db.monitoring.find({})
    monitoring = {}
    for result in results:
        result.pop("_id", None)
        monitoring[result["source_url"]] = result
    return monitoring


# ==================== Alert Operations ====================

def save_alert(alert_data: Dict[str, Any]) -> None:
    """Save a new alert"""
    alert_data["timestamp"] = datetime.utcnow().isoformat()
    _get_storage().db.alerts.insert_one(alert_data)


def get_alerts(
    source_url: Optional[str] = None,
    notified: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get alerts with optional filters"""
    query = {}
    if source_url:
        query["source_url"] = source_url
    if notified is not None:
        query["notified"] = notified
    
    results = list(
        _get_storage().db.alerts
        .find(query)
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    for result in results:
        result.pop("_id", None)
    return results


def mark_alerts_notified(alert_ids: List[str]) -> int:
    """Mark alerts as notified"""
    from bson import ObjectId
    object_ids = [ObjectId(aid) for aid in alert_ids if ObjectId.is_valid(aid)]
    result = _get_storage().db.alerts.update_many(
        {"_id": {"$in": object_ids}},
        {"$set": {"notified": True}}
    )
    return result.modified_count


def get_unnotified_alerts() -> List[Dict[str, Any]]:
    """Get all unnotified alerts"""
    return get_alerts(notified=False)


# ==================== Batch Update Operations ====================

def save_batch_request(batch_data: Dict[str, Any]) -> None:
    """Save batch update request"""
    _get_storage().db.batch_requests.update_one(
        {"request_id": batch_data["request_id"]},
        {"$set": batch_data},
        upsert=True
    )


def get_batch_request(request_id: str) -> Optional[Dict[str, Any]]:
    """Get batch request by ID"""
    result = _get_storage().db.batch_requests.find_one({"request_id": request_id})
    if result:
        result.pop("_id", None)
        return result
    return None


def get_recent_batch_requests(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent batch requests"""
    results = list(
        _get_storage().db.batch_requests
        .find({})
        .sort("created_at", DESCENDING)
        .limit(limit)
    )
    for result in results:
        result.pop("_id", None)
    return results


def cleanup_old_batch_requests(keep_count: int = 100) -> int:
    """Clean up old batch requests, keeping only the most recent ones"""
    # Get the created_at timestamp of the keep_count-th most recent request
    requests = list(
        _get_storage().db.batch_requests
        .find({}, {"created_at": 1})
        .sort("created_at", DESCENDING)
        .limit(keep_count)
    )
    
    if len(requests) < keep_count:
        return 0  # Not enough requests to clean up
    
    cutoff_date = requests[-1]["created_at"]
    result = _get_storage().db.batch_requests.delete_many({"created_at": {"$lt": cutoff_date}})
    return result.deleted_count


# ==================== Update History Operations ====================

def save_update_history(history_data: Dict[str, Any]) -> None:
    """Save link update history"""
    history_data["timestamp"] = datetime.utcnow().isoformat()
    _get_storage().db.update_history.insert_one(history_data)


def get_update_history(
    post_id: Optional[int] = None,
    date_iso: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get update history with optional filters"""
    query = {}
    if post_id:
        query["post_id"] = post_id
    if date_iso:
        query["date_iso"] = date_iso
    
    results = list(
        _get_storage().db.update_history
        .find(query)
        .sort("timestamp", DESCENDING)
        .limit(limit)
    )
    for result in results:
        result.pop("_id", None)
    return results


# ==================== Cron Settings Functions ====================

def get_cron_settings() -> Optional[Dict[str, Any]]:
    """
    Get cron/scheduled update settings from MongoDB.
    
    Returns:
        Dict with cron settings or None if not found
    """
    try:
        storage = _get_storage()
        result = storage.db.settings.find_one({"setting_key": "cron_config"})
        
        if result:
            result.pop("_id", None)
            result.pop("setting_key", None)
            return result
        
        return None
    except Exception as e:
        logging.error(f"Failed to get cron settings: {e}")
        return None


def set_cron_settings(settings: Dict[str, Any]) -> bool:
    """
    Save cron/scheduled update settings to MongoDB.
    
    Args:
        settings: Dict with enabled, schedule, target_sites, etc.
        
    Returns:
        True if successful, False otherwise
    """
    try:
        storage = _get_storage()
        
        # Add metadata
        settings["setting_key"] = "cron_config"
        settings["updated_at"] = datetime.utcnow().isoformat()
        
        # Upsert the settings
        storage.db.settings.update_one(
            {"setting_key": "cron_config"},
            {"$set": settings},
            upsert=True
        )
        
        logging.info(f"[CRON] Saved cron settings: enabled={settings.get('enabled')}, sites={settings.get('target_sites')}")
        return True
    except Exception as e:
        logging.error(f"Failed to save cron settings: {e}")
        return False


# ==================== Utility Functions ====================

def get_database():
    """Get database instance for direct access if needed"""
    return _get_storage().db


def close_connection():
    """Close MongoDB connection"""
    _get_storage().close()
