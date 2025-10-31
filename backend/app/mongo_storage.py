"""
MongoDB Storage Layer

Replaces JSON file-based storage with MongoDB for all data operations.
"""

from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
import os
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
            
            # Fingerprints collection
            self._db.fingerprints.create_index([("post_id", ASCENDING), ("date_iso", ASCENDING)], unique=True)
            self._db.fingerprints.create_index("post_id")
            self._db.fingerprints.create_index("date_iso")
            
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
    """Get post configuration by post_id"""
    try:
        result = _get_storage().db.posts.find_one({"post_id": post_id})
        if result:
            # Convert ObjectId to string for JSON serialization
            result["_id"] = str(result["_id"])
        return result
    except Exception as e:
        print(f"Database error in get_post_config: {e}")
        return None


def set_post_config(post_config: Dict[str, Any]) -> bool:
    """Save or update post configuration"""
    try:
        _get_storage().db.posts.update_one(
            {"post_id": post_config["post_id"]},
            {"$set": post_config},
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


# ==================== Fingerprint Operations ====================

def get_known_fingerprints(post_id: int, date_iso: str) -> Set[str]:
    """Get known fingerprints for a post and date"""
    try:
        result = _get_storage().db.fingerprints.find_one({"post_id": post_id, "date_iso": date_iso})
        if result and "fingerprints" in result:
            return set(result["fingerprints"])
        return set()
    except Exception as e:
        print(f"Database error in get_known_fingerprints: {e}")
        return set()


def save_new_links(post_id: int, date_iso: str, fingerprints: Set[str]) -> None:
    """Save new link fingerprints (merge with existing)"""
    existing = get_known_fingerprints(post_id, date_iso)
    merged = list(existing.union(fingerprints))
    
    _get_storage().db.fingerprints.update_one(
        {"post_id": post_id, "date_iso": date_iso},
        {
            "$set": {
                "fingerprints": merged,
                "updated_at": datetime.utcnow().isoformat()
            },
            "$setOnInsert": {"created_at": datetime.utcnow().isoformat()}
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


# ==================== Utility Functions ====================

def get_database():
    """Get database instance for direct access if needed"""
    return _get_storage().db


def close_connection():
    """Close MongoDB connection"""
    _get_storage().close()
