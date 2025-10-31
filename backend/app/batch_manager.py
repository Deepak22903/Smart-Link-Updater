"""
Batch Update Management for WordPress Dashboard

Handles:
- Batch update requests with tracking
- Real-time status updates
- Log streaming
- Request lifecycle management

Now uses MongoDB for persistent storage instead of in-memory storage.
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import pytz

from . import mongo_storage


class UpdateStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    NO_CHANGES = "no_changes"  # No new links found (duplicates)
    PARTIAL = "partial"
    FAILED = "failed"


class PostUpdateState:
    """State for a single post update"""
    def __init__(self, post_id: int):
        self.post_id = post_id
        self.status = UpdateStatus.QUEUED
        self.progress = 0  # 0-100
        self.message = "Queued"
        self.links_found = 0
        self.links_added = 0
        self.error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.logs: List[str] = []
    
    def to_dict(self):
        return {
            "post_id": self.post_id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "links_found": self.links_found,
            "links_added": self.links_added,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "log_count": len(self.logs)
        }
    
    def add_log(self, message: str):
        timestamp = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        # Keep only last 100 log lines
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]


class BatchUpdateRequest:
    """Manages a batch update request"""
    def __init__(self, request_id: str, post_ids: List[int], initiator: str = "unknown"):
        self.request_id = request_id
        self.post_ids = post_ids
        self.initiator = initiator
        self.created_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.posts: Dict[int, PostUpdateState] = {
            post_id: PostUpdateState(post_id)
            for post_id in post_ids
        }
        self.overall_status = UpdateStatus.QUEUED
    
    def start(self):
        self.started_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
        self.overall_status = UpdateStatus.RUNNING
        self._save_to_db()  # Persist to MongoDB
    
    def complete(self):
        self.completed_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
        
        # Determine overall status
        statuses = [p.status for p in self.posts.values()]
        if all(s in [UpdateStatus.SUCCESS, UpdateStatus.NO_CHANGES] for s in statuses):
            # All completed successfully (with or without changes)
            if any(s == UpdateStatus.SUCCESS for s in statuses):
                self.overall_status = UpdateStatus.SUCCESS
            else:
                # All no_changes
                self.overall_status = UpdateStatus.NO_CHANGES
        elif all(s == UpdateStatus.FAILED for s in statuses):
            self.overall_status = UpdateStatus.FAILED
        else:
            self.overall_status = UpdateStatus.PARTIAL
        
        self._save_to_db()  # Persist final state to MongoDB
    
    def to_dict(self):
        return {
            "request_id": self.request_id,
            "initiator": self.initiator,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "overall_status": self.overall_status,
            "total_posts": len(self.post_ids),
            "posts": {
                str(post_id): state.to_dict()  # Convert post_id to string for MongoDB
                for post_id, state in self.posts.items()
            }
        }
    
    def _save_to_db(self):
        """Save current state to MongoDB"""
        mongo_storage.save_batch_request(self.to_dict())


class BatchUpdateManager:
    """Global manager for batch update requests with MongoDB persistence"""
    def __init__(self):
        self._lock = asyncio.Lock()
        # Load recent requests from MongoDB into memory for faster access
        self._cache: Dict[str, BatchUpdateRequest] = {}
        self._load_recent_requests()
    
    def _load_recent_requests(self):
        """Load recent requests from MongoDB into cache"""
        try:
            recent = mongo_storage.get_recent_batch_requests(limit=50)
            for req_data in recent:
                request_id = req_data["request_id"]
                # Reconstruct BatchUpdateRequest from MongoDB data
                request = BatchUpdateRequest(
                    request_id=request_id,
                    post_ids=req_data["post_ids"],
                    initiator=req_data.get("initiator", "unknown")
                )
                request.created_at = req_data["created_at"]
                request.started_at = req_data.get("started_at")
                request.completed_at = req_data.get("completed_at")
                request.overall_status = req_data["overall_status"]
                
                # Reconstruct post states
                for post_id_str, state_data in req_data.get("posts", {}).items():
                    post_id = int(post_id_str)
                    state = PostUpdateState(post_id)
                    state.status = state_data["status"]
                    state.progress = state_data["progress"]
                    state.message = state_data["message"]
                    state.links_found = state_data["links_found"]
                    state.links_added = state_data["links_added"]
                    state.error = state_data.get("error")
                    state.started_at = state_data.get("started_at")
                    state.completed_at = state_data.get("completed_at")
                    state.logs = state_data.get("logs", [])
                    request.posts[post_id] = state
                
                self._cache[request_id] = request
        except Exception as e:
            print(f"Error loading recent requests from MongoDB: {e}")
    
    def create_request(self, post_ids: List[int], initiator: str = "unknown") -> BatchUpdateRequest:
        """Create a new batch update request and persist to MongoDB"""
        request_id = str(uuid.uuid4())
        request = BatchUpdateRequest(request_id, post_ids, initiator)
        self._cache[request_id] = request
        
        # Save to MongoDB
        request._save_to_db()
        
        # Clean up old requests in MongoDB (keep last 100)
        mongo_storage.cleanup_old_batch_requests(keep_count=100)
        
        return request
    
    def get_request(self, request_id: str) -> Optional[BatchUpdateRequest]:
        """Get request by ID (from cache or MongoDB)"""
        # Try cache first
        if request_id in self._cache:
            return self._cache[request_id]
        
        # Try MongoDB
        req_data = mongo_storage.get_batch_request(request_id)
        if req_data:
            # Reconstruct and cache
            request = BatchUpdateRequest(
                request_id=request_id,
                post_ids=req_data["post_ids"],
                initiator=req_data.get("initiator", "unknown")
            )
            request.created_at = req_data["created_at"]
            request.started_at = req_data.get("started_at")
            request.completed_at = req_data.get("completed_at")
            request.overall_status = req_data["overall_status"]
            
            # Reconstruct post states
            for post_id_str, state_data in req_data.get("posts", {}).items():
                post_id = int(post_id_str)
                state = PostUpdateState(post_id)
                state.status = state_data["status"]
                state.progress = state_data["progress"]
                state.message = state_data["message"]
                state.links_found = state_data["links_found"]
                state.links_added = state_data["links_added"]
                state.error = state_data.get("error")
                state.started_at = state_data.get("started_at")
                state.completed_at = state_data.get("completed_at")
                state.logs = state_data.get("logs", [])
                request.posts[post_id] = state
            
            self._cache[request_id] = request
            return request
        
        return None
    
    def get_post_state(self, request_id: str, post_id: int) -> Optional[PostUpdateState]:
        """Get state for a specific post in a request"""
        request = self.get_request(request_id)
        if request:
            return request.posts.get(post_id)
        return None
    
    async def update_post_state(
        self,
        request_id: str,
        post_id: int,
        status: Optional[UpdateStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        links_found: Optional[int] = None,
        links_added: Optional[int] = None,
        error: Optional[str] = None,
        log_message: Optional[str] = None
    ):
        """Update state for a specific post and persist to MongoDB"""
        async with self._lock:
            state = self.get_post_state(request_id, post_id)
            if not state:
                return
            
            request = self.get_request(request_id)
            if not request:
                return
            
            if status is not None:
                state.status = status
                if status == UpdateStatus.RUNNING and not state.started_at:
                    state.started_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
                elif status in [UpdateStatus.SUCCESS, UpdateStatus.NO_CHANGES, UpdateStatus.FAILED] and not state.completed_at:
                    state.completed_at = datetime.now(pytz.timezone("Asia/Kolkata")).isoformat()
            
            if progress is not None:
                state.progress = progress
            if message is not None:
                state.message = message
            if links_found is not None:
                state.links_found = links_found
            if links_added is not None:
                state.links_added = links_added
            if error is not None:
                state.error = error
            if log_message is not None:
                state.add_log(log_message)
            
            # Persist to MongoDB
            request._save_to_db()


# Global instance
_batch_manager = None

def get_batch_manager() -> BatchUpdateManager:
    """Get global batch manager instance"""
    global _batch_manager
    if _batch_manager is None:
        _batch_manager = BatchUpdateManager()
    return _batch_manager
