import logging

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Body, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv
import asyncio
from pathlib import Path

# Load environment variables from project root
# Navigate up from backend/app/main.py to project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from .queue_app import celery_app
from . import mongo_storage
from .scrape import fetch_html
from .extraction import extract_links_with_heading_filter
from .dedupe import dedupe_by_fingerprint, fingerprint
from .wp import update_post_links_section, get_configured_wp_sites
from .extractors import get_extractor, list_extractors
from .html_monitor import get_monitor
from .notifications import process_unnotified_alerts
from .batch_manager import get_batch_manager, UpdateStatus
from .analytics import get_analytics_engine
from tenacity import RetryError
import httpx
from datetime import datetime
import pytz

app = FastAPI(title="SmartLinkUpdater API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://minecraftcirclegenerater.com",
        "http://minecraftcirclegenerater.com",
        "https://www.minecraftcirclegenerater.com",
        "http://www.minecraftcirclegenerater.com",
        "http://localhost:3000",  # For local development
        "*",  # Allow all origins (you can restrict this later)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for task status
task_status: Dict[str, dict] = {}


# ==================== Helper Functions ====================


def resolve_post_id_for_site(config: Dict, site_key: str) -> int:
    """
    Resolve the correct post ID for a specific WordPress site.

    Args:
        config: Post configuration dict
        site_key: Site identifier (e.g., "minecraft", "this", "site_b")

    Returns:
        int: The post ID for that specific site

    Examples:
        config = {
            "post_id": 105,  # Legacy field (for "this" site)
            "content_slug": "coin-master-free-spins",
            "site_post_ids": {
                "this": 105,
                "minecraft": 105,
                "casino": 89,
                "blog": 234
            }
        }

        resolve_post_id_for_site(config, "casino") -> 89
        resolve_post_id_for_site(config, "this") -> 105
    """
    # Check if site_post_ids mapping exists
    site_post_ids = config.get("site_post_ids", {})

    if site_post_ids and site_key in site_post_ids:
        return site_post_ids[site_key]

    # Fallback to primary post_id field
    return config.get("post_id")


# ==================== Pydantic Models ====================


class PostConfig(BaseModel):
    post_id: int
    source_urls: List[HttpUrl]
    timezone: Optional[str] = os.getenv("TIMEZONE", "Asia/Kolkata")
    extractor_map: Optional[Dict[str, str]] = (
        None  # Per-source extractor mapping. URLs not mapped default to Gemini.
    )
    wp_site: Optional[Dict[str, str]] = (
        None  # {"base_url": "https://site.com", "username": "user", "app_password": "pass"}
    )
    content_slug: Optional[str] = (
        None  # Universal identifier across sites (e.g., "coin-master-free-spins")
    )
    site_post_ids: Optional[Dict[str, int]] = (
        None  # Maps site_key -> post_id for multi-site support
    )
    ad_codes: Optional[List[Dict[str, Any]]] = (
        None  # NEW: Ad codes to insert between sections
        # Format: [{"code": "<script>...</script>", "position": 1}, ...]
        # Position is integer: 1 = after first button row, 2 = after second row, etc.
    )
    site_ad_codes: Optional[Dict[str, List[Dict[str, Any]]]] = (
        None  # NEW: Per-site ad codes. Maps site_key -> List[AdCode]
        # Format: {"default": [{"position": 1, "code": "..."}], "site1": [...]}
    )
    days_to_keep: Optional[int] = 5  # NEW: Days to keep link sections (default: 5)
    custom_button_title: Optional[str] = (
        None  # NEW: Custom button title to use for all links (when use_custom_button_title=True)
    )
    use_custom_button_title: Optional[bool] = (
        False  # NEW: Toggle to use custom_button_title instead of scraped titles
    )
    auto_update_sites: Optional[List[str]] = (
        None  # NEW: List of site_keys that should auto-update this post via cron
    )


class UpdateJob(BaseModel):
    # Typically you'd pass only post_ids and fetch sources from WP.
    # For MVP, allow directly passing source URLs with the target WP post id.
    post_id: int
    source_urls: Optional[List[HttpUrl]] = None  # Optional, can use stored config
    timezone: Optional[str] = os.getenv("TIMEZONE", "Asia/Kolkata")
    today_iso: Optional[str] = None  # e.g., "2025-10-26"


class BatchUpdateRequest(BaseModel):
    """Batch update request from WordPress dashboard"""

    post_ids: List[int]
    sync: Optional[bool] = False
    initiator: Optional[str] = "wp-plugin"
    target: Optional[str] = None  # site_key or 'all' (sites must be configured in Sites tab)


class PostConfigUpdate(BaseModel):
    """Model for partial updates to post configuration"""

    source_urls: Optional[List[HttpUrl]] = None
    timezone: Optional[str] = None
    extractor_map: Optional[Dict[str, str]] = (
        None  # Per-source extractor mapping. URLs not mapped default to Gemini.
    )
    wp_site: Optional[Dict[str, str]] = None
    content_slug: Optional[str] = None  # Universal identifier for content across sites
    site_post_ids: Optional[Dict[str, int]] = (
        None  # Maps site_key -> post_id for each WordPress site
    )
    site_ad_codes: Optional[Dict[str, List[Dict[str, Any]]]] = (
        None  # Per-site ad codes
    )
    days_to_keep: Optional[int] = None  # Days to keep link sections
    custom_button_title: Optional[str] = None  # Custom button title for all links
    use_custom_button_title: Optional[bool] = None  # Toggle for custom button title
    auto_update_sites: Optional[List[str]] = None  # List of site_keys for auto-update


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/health/extractors")
async def health_extractors():
    """
    Get health status of all monitored source URLs.

    Returns monitoring data including:
    - Status (healthy, warning, failing)
    - Recent extraction statistics
    - Consecutive failures
    - HTML fingerprint info
    """
    monitor = get_monitor()
    return monitor.get_all_health()


@app.get("/health/extractors/{source_url:path}")
async def health_extractor(source_url: str):
    """Get health status for a specific source URL"""
    monitor = get_monitor()
    health = monitor.get_source_health(source_url)

    if health["status"] == "unknown":
        raise HTTPException(status_code=404, detail="Source URL not monitored")

    return health


@app.get("/alerts")
async def get_alerts(hours: int = 24):
    """Get recent alerts from the monitoring system"""
    monitor = get_monitor()
    alerts = monitor.get_recent_alerts(hours=hours)
    return {"alerts": [alert.model_dump() for alert in alerts], "count": len(alerts)}


@app.get("/alerts/unnotified")
async def get_unnotified_alerts():
    """Get alerts that haven't been sent yet"""
    monitor = get_monitor()
    alerts = monitor.get_unnotified_alerts()
    return {"alerts": [alert.model_dump() for alert in alerts], "count": len(alerts)}


@app.post("/alerts/send")
async def send_pending_alerts():
    """
    Process and send all unnotified alerts.

    Useful for:
    - Manual testing of notification system
    - Cron job to periodically check and send alerts
    - Webhook trigger from Cloud Scheduler
    """
    result = await process_unnotified_alerts()
    return result


@app.get("/extractors")
async def list_available_extractors():
    """List all registered extractors."""
    return {"extractors": list_extractors()}


@app.post("/config/post")
async def configure_post(config: PostConfig = Body(...)):
    """Configure target URLs for a WordPress post, optionally with custom WordPress site credentials."""
    post_config = {
        "post_id": config.post_id,
        "source_urls": [str(url) for url in config.source_urls],
        "timezone": config.timezone,
        "extractor": config.extractor,
        "wp_site": config.wp_site,
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # Add days_to_keep (default to 5 if not specified)
    post_config["days_to_keep"] = config.days_to_keep if config.days_to_keep is not None else 5
    logging.info(f"[SAVE CONFIG] Post {config.post_id}: Saving days_to_keep={post_config['days_to_keep']}")

    # Add optional multi-site fields
    if config.content_slug:
        post_config["content_slug"] = config.content_slug
    if config.site_post_ids:
        post_config["site_post_ids"] = config.site_post_ids

    # Add extractor_map if provided
    if config.extractor_map:
        post_config["extractor_map"] = config.extractor_map

    # Add site_ad_codes if provided
    if config.site_ad_codes:
        post_config["site_ad_codes"] = config.site_ad_codes
        logging.info(
            f"[SAVE CONFIG] Saving site_ad_codes for post {config.post_id}: {len(config.site_ad_codes)} sites, keys: {list(config.site_ad_codes.keys())}"
        )
    
    # Save to MongoDB
    save_result = mongo_storage.set_post_config(post_config)
    if not save_result:
        raise HTTPException(status_code=500, detail="Failed to save post configuration to MongoDB")
    
    # Verify the save by reading back
    saved_config = mongo_storage.get_post_config(config.post_id)
    if saved_config and "site_ad_codes" in saved_config:
        logging.info(f"[SAVE CONFIG] Verified site_ad_codes saved: {list(saved_config['site_ad_codes'].keys())}")
    else:
        logging.warning(f"[SAVE CONFIG] Warning: site_ad_codes not found in saved config!")

    response = {
        "success": True,
        "post_id": config.post_id,
        "source_urls": [str(url) for url in config.source_urls],
        "timezone": config.timezone,
        "extractor": config.extractor,
    }

    # Include multi-site fields in response
    if config.content_slug:
        response["content_slug"] = config.content_slug
    if config.site_post_ids:
        response["site_post_ids"] = config.site_post_ids
    if config.extractor_map:
        response["extractor_map"] = config.extractor_map
    if config.site_ad_codes:
        response["site_ad_codes"] = config.site_ad_codes

    if config.wp_site:
        response["wp_site"] = {
            "base_url": config.wp_site.get("base_url"),
            "username": config.wp_site.get("username"),
            # Don't return password in response
        }
    return response


@app.get("/config/posts")
async def list_posts():
    """List all configured posts."""
    return {"posts": mongo_storage.list_configured_posts()}


@app.get("/config/sites")
async def list_configured_sites():
    """Return configured WordPress sites from environment (keys and base URLs).

    This does not expose credentials.
    """
    sites = get_configured_wp_sites()
    result = {}
    for key, conf in sites.items():
        base = conf.get("base_url")
        result[key] = {"base_url": base}
    return {"sites": result}


@app.put("/config/post/{post_id}")
async def update_post_config(post_id: int, config_update: PostConfigUpdate):
    """Update configuration for a specific post."""
    existing_config = mongo_storage.get_post_config(post_id)
    if not existing_config:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not configured")

    # Use exclude_none instead of exclude_unset to allow empty arrays
    update_data = config_update.model_dump(exclude_unset=True, exclude_none=False)

    # Debug logging for ad_codes
    import logging

    logging.info(
        f"[UPDATE CONFIG] Received update_data keys: {list(update_data.keys())}"
    )
    
    if "days_to_keep" in update_data:
        logging.info(f"[UPDATE CONFIG] days_to_keep in update: {update_data['days_to_keep']}")
    
    if "site_ad_codes" in update_data:
        logging.info(f"[UPDATE CONFIG] site_ad_codes in update: {len(update_data['site_ad_codes'])} sites, keys: {list(update_data['site_ad_codes'].keys())}")

    # Convert HttpUrl objects to strings if present
    if "source_urls" in update_data and update_data["source_urls"] is not None:
        update_data["source_urls"] = [str(url) for url in update_data["source_urls"]]

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    # Add/update the updated_at timestamp
    update_data["updated_at"] = datetime.utcnow().isoformat()

    # Create the full updated configuration object to be saved
    # This ensures we don't accidentally remove fields
    final_config = {**existing_config, **update_data}
    
    # Clean up any legacy ad_codes field that might exist
    final_config.pop("ad_codes", None)

    # Remove _id field as it's immutable in MongoDB and managed by the database
    final_config.pop("_id", None)

    if mongo_storage.set_post_config(final_config):
        # Verify save
        updated = mongo_storage.get_post_config(post_id)
        if "site_ad_codes" in update_data and updated:
            if "site_ad_codes" in updated:
                logging.info(f"[UPDATE CONFIG] Verified site_ad_codes saved: {list(updated['site_ad_codes'].keys())}")
            else:
                logging.warning(f"[UPDATE CONFIG] Warning: site_ad_codes not in saved config!")
        
        # Return the complete, updated configuration
        return updated
    else:
        raise HTTPException(
            status_code=500, detail="Failed to update post configuration"
        )


@app.delete("/config/post/{post_id}")
async def delete_post_config(post_id: int):
    """Delete configuration for a specific post."""
    existing_config = mongo_storage.get_post_config(post_id)
    if not existing_config:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not configured")

    if mongo_storage.delete_post_config(post_id):
        return {
            "success": True,
            "message": f"Post {post_id} configuration deleted successfully",
            "post_id": post_id,
        }
    else:
        raise HTTPException(
            status_code=500, detail="Failed to delete post configuration"
        )


@app.get("/config/post/{post_id}")
async def get_post_config_endpoint(post_id: int):
    """Get configuration for a specific post."""
    config = mongo_storage.get_post_config(post_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not configured")

    # Debug logging
    import logging

    logging.info(f"[GET CONFIG] Returning config for post {post_id}")
    if "site_ad_codes" in config:
        logging.info(f"[GET CONFIG] site_ad_codes present with {len(config['site_ad_codes'])} sites: {list(config['site_ad_codes'].keys())}")
    else:
        logging.info(f"[GET CONFIG] No site_ad_codes in config")

    return config


# ============================================================================
# BATCH UPDATE ENDPOINTS (WordPress Dashboard Real-Time Updates)
# ============================================================================


@app.post("/api/batch-update")
async def start_batch_update(
    request: BatchUpdateRequest, background_tasks: BackgroundTasks
):
    """
    Start batch update for multiple posts with progress tracking.

    Returns request_id for polling status endpoint.
    """
    manager = get_batch_manager()
    batch_request = manager.create_request(request.post_ids, request.initiator)

    if request.sync:
        # Synchronous mode: wait for completion
        await process_batch_updates(batch_request.request_id, request.target)
        return {
            "request_id": batch_request.request_id,
            "started_at": batch_request.started_at,
            "total_posts": len(request.post_ids),
            "mode": "sync",
            "status": batch_request.to_dict(),
        }
    else:
        # Asynchronous mode: start background task
        background_tasks.add_task(
            process_batch_updates, batch_request.request_id, request.target
        )
        return {
            "request_id": batch_request.request_id,
            "created_at": batch_request.created_at,
            "total_posts": len(request.post_ids),
            "mode": "background",
        }


@app.get("/api/batch-status/{request_id}")
async def get_batch_status(request_id: str):
    """Get current status of batch update with per-post progress."""
    manager = get_batch_manager()
    batch_request = manager.get_request(request_id)

    if not batch_request:
        raise HTTPException(status_code=404, detail="Request not found")

    batch_dict = batch_request.to_dict()

    # Update status to explicitly show "no_changes" if applicable
    for post_id, post_data in batch_dict["posts"].items():
        if post_data["status"] == UpdateStatus.NO_CHANGES:
            post_data["status"] = "no_changes"

    return batch_dict


@app.get("/api/batch-logs/{request_id}/{post_id}")
async def get_post_logs(request_id: str, post_id: int, tail: int = 50):
    """Get logs for specific post in batch update."""
    manager = get_batch_manager()
    state = manager.get_post_state(request_id, post_id)

    if not state:
        raise HTTPException(status_code=404, detail="Post state not found")

    return {"post_id": post_id, "logs": state.logs[-tail:] if tail > 0 else state.logs}


@app.get("/api/batch-history")
async def get_batch_history(limit: int = 50, skip: int = 0):
    """
    Get paginated batch update history.

    Returns list of batch requests with summary information, sorted by newest first.
    """
    from . import mongo_storage

    # Get batch requests from MongoDB
    all_requests = mongo_storage.get_recent_batch_requests(limit=limit + skip)

    # Apply pagination
    paginated = all_requests[skip : skip + limit]

    # Format response with summary info
    history = []
    for req in paginated:
        # Calculate summary statistics
        posts = req.get("posts", {})
        total = len(posts)
        completed = sum(
            1
            for p in posts.values()
            if p.get("status") in ["success", "no_changes", "failed"]
        )
        successful = sum(1 for p in posts.values() if p.get("status") == "success")
        failed = sum(1 for p in posts.values() if p.get("status") == "failed")
        no_changes = sum(1 for p in posts.values() if p.get("status") == "no_changes")

        history.append(
            {
                "request_id": req.get("request_id"),
                "created_at": req.get("created_at"),
                "started_at": req.get("started_at"),
                "completed_at": req.get("completed_at"),
                "overall_status": req.get("overall_status"),
                "initiator": req.get("initiator", "unknown"),
                "total_posts": total,
                "completed_posts": completed,
                "successful_posts": successful,
                "failed_posts": failed,
                "no_changes_posts": no_changes,
                "post_ids": req.get("post_ids", []),
            }
        )

    return {
        "history": history,
        "total": len(all_requests),
        "limit": limit,
        "skip": skip,
    }


class ManualLink(BaseModel):
    title: str
    url: HttpUrl


class ManualLinkRequest(BaseModel):
    post_id: int
    links: List[ManualLink]
    date: str  # YYYY-MM-DD format
    target: Optional[str] = None  # Deprecated: use target_sites instead
    target_sites: Optional[List[str]] = None  # NEW: Multiple sites to update
    use_custom_button_title: Optional[bool] = False  # NEW: Toggle for custom button title
    custom_button_title: Optional[str] = None  # NEW: Custom title for all buttons


@app.post("/api/manual-links")
async def add_manual_links(request: ManualLinkRequest):
    """
    Add links manually to a post.

    - Performs deduplication against existing links
    - Updates WordPress post with new links
    - Stores fingerprints for future deduplication
    """
    from .models import Link

    # Get post configuration
    config = mongo_storage.get_post_config(request.post_id)
    if not config:
        raise HTTPException(
            status_code=404, detail=f"Post {request.post_id} not configured"
        )

    wp_site = config.get("wp_site")

    # Convert manual links to Link objects
    # Apply custom button title if enabled
    if request.use_custom_button_title and request.custom_button_title:
        logging.info(f"[MANUAL LINKS] Using custom button title: '{request.custom_button_title}'")
        manual_links = [
            Link(title=request.custom_button_title, url=str(link.url), published_date_iso=request.date)
            for link in request.links
        ]
    else:
        logging.info(f"[MANUAL LINKS] Using individual titles from each link")
        manual_links = [
            Link(title=link.title, url=str(link.url), published_date_iso=request.date)
            for link in request.links
        ]

    if not manual_links:
        return {"success": False, "message": "No links provided", "links_added": 0}

    # Determine target sites (must use target_sites, no default)
    target_sites_list = request.target_sites if request.target_sites else []
    
    if not target_sites_list:
        raise HTTPException(
            status_code=400,
            detail="No target sites specified. Please select sites from the Sites tab."
        )
    
    logging.info(f"[MANUAL LINKS] Target sites: {target_sites_list}")

    # Determine targets to process
    targets_to_process = []
    
    # Expand target sites
    for target_site in target_sites_list:
        if target_site == "all":
            # Fetch all configured sites from MongoDB
            sites = mongo_storage.get_all_wp_sites()
            logging.info(f"[MANUAL LINKS] Expanding 'all' - found {len(sites)} configured sites")
            
            # Add all configured sites
            if sites:
                for site_key in sites:
                    site_post_id = resolve_post_id_for_site(config, site_key)
                    if site_post_id:
                        targets_to_process.append({"site_key": site_key, "post_id": site_post_id})
                        logging.info(f"[MANUAL LINKS] Added target: site={site_key}, post_id={site_post_id}")
                    else:
                        logging.warning(f"[MANUAL LINKS] No post ID for site {site_key} on post {request.post_id}")
            
            if not targets_to_process:
                raise HTTPException(
                    status_code=400,
                    detail="No sites configured. Please add sites in the Sites tab first."
                )
            break  # 'all' means all sites, don't process other selections
                
        else:
            # User selected a specific site
            resolved_id = resolve_post_id_for_site(config, target_site)
            if not resolved_id:
                logging.warning(f"[MANUAL LINKS] No post ID mapping for site {target_site}, skipping")
                continue
            targets_to_process.append({"site_key": target_site, "post_id": resolved_id})
            logging.info(f"[MANUAL LINKS] Added target: site={target_site}, post_id={resolved_id}")
    
    if not targets_to_process:
        raise HTTPException(
            status_code=400,
            detail="No valid targets found. Check your site configuration and post ID mappings."
        )
    
    # Remove duplicates based on site_key+post_id combination
    seen = set()
    unique_targets = []
    for target in targets_to_process:
        key = (target["site_key"], target["post_id"])
        if key not in seen:
            seen.add(key)
            unique_targets.append(target)
    targets_to_process = unique_targets
    
    logging.info(f"[MANUAL LINKS] Total unique targets to process: {len(targets_to_process)}")

    total_links_added = 0
    total_sections_pruned = 0
    sites_updated_count = 0
    duplicates_count = 0
    
    # Process each target
    for target_info in targets_to_process:
        target_site_key = target_info["site_key"]
        target_post_id = target_info["post_id"]
        
        logging.info(f"[MANUAL LINKS] Processing site={target_site_key or 'default'}, post_id={target_post_id}")
        
        # Deduplicate against known links for this specific site
        known_fps = mongo_storage.get_known_fingerprints(
            target_post_id, request.date, target_site_key
        )
        new_links = dedupe_by_fingerprint(manual_links, known_fps)
        
        logging.info(f"[MANUAL LINKS] Site {target_site_key}: {len(manual_links)} provided, {len(new_links)} new after dedup")
        
        if not new_links:
            duplicates_count += len(manual_links)
            logging.info(f"[MANUAL LINKS] All links were duplicates for site {target_site_key}")
            continue

        # Load site configuration from MongoDB
        site_config = mongo_storage.get_wp_site(target_site_key)
        if not site_config:
            logging.warning(f"[MANUAL LINKS] Site config not found for {target_site_key}, using default")
            site_config = None
        else:
            logging.info(f"[MANUAL LINKS] Loaded site config for {target_site_key}, button_style: {site_config.get('button_style', 'default')}")

        # Update WordPress
        try:
            wp_result = await update_post_links_section(
                target_post_id, new_links, target_site_key, config, site_config
            )
            
            if not wp_result.get("error"):
                total_links_added += wp_result.get("links_added", 0)
                total_sections_pruned += wp_result.get("sections_pruned", 0)
                sites_updated_count += 1
                
                logging.info(f"[MANUAL LINKS] Successfully updated site {target_site_key}: {len(new_links)} links added")
                
                # Store fingerprints for deduplication
                new_fps = {fingerprint(link) for link in new_links}
                mongo_storage.save_new_links(
                    target_post_id, request.date, new_fps, target_site_key
                )
            else:
                error_msg = wp_result.get('error', 'Unknown error')
                logging.error(f"[MANUAL LINKS] Error result from WordPress for site {target_site_key}: {error_msg}")
                # Raise error for authentication issues so user knows to fix credentials
                if target_site_key and len(targets_to_process) == 1:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to update site '{target_site_key}': {error_msg}. Check site credentials in Sites tab."
                    )
        except HTTPException:
            raise  # Re-raise HTTP exceptions
        except Exception as e:
            error_str = str(e)
            logging.error(f"[MANUAL LINKS] Exception updating site {target_site_key}: {error_str}")
            import traceback
            logging.error(traceback.format_exc())
            
            # For authentication errors, provide clear message
            if "401" in error_str or "Unauthorized" in error_str:
                site_name = target_site_key or "default"
                raise HTTPException(
                    status_code=401,
                    detail=f"WordPress authentication failed for site '{site_name}'. Please check the username and Application Password in the Sites tab."
                )
            
            # For single site operations, raise the error
            if len(targets_to_process) == 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to update site '{target_site_key}': {error_str}"
                )
            # For multi-site, continue to next site

    if sites_updated_count == 0 and len(targets_to_process) > 0:
        # If we tried to update but everything was a duplicate or failed
        return {
            "success": True,
            "message": "All links were duplicates or updates failed",
            "links_provided": len(manual_links),
            "links_added": 0,
            "duplicates": len(manual_links),
            "sites_updated": 0,
        }

    # Build success message
    if sites_updated_count > 1:
        message = f"Successfully added {total_links_added} manual links across {sites_updated_count} sites"
    else:
        message = f"Successfully added {total_links_added} manual links"

    return {
        "success": True,
        "message": message,
        "links_provided": len(manual_links),
        "links_added": total_links_added,
        "duplicates": len(manual_links) * len(targets_to_process) - total_links_added,
        "sections_pruned": total_sections_pruned,
        "sites_updated": sites_updated_count,
    }




@app.get("/api/extractors/list")
async def list_available_extractors_detailed():
    """Get detailed list of registered extractors with priorities."""
    extractor_names = list_extractors()

    extractors_info = []
    for name in extractor_names:
        try:
            extractor = get_extractor(name)
            extractors_info.append(
                {
                    "name": name,
                    "priority": getattr(extractor.__class__, "priority", 0),
                    "can_handle": ["*"] if name == "default" else [name],
                    "description": extractor.__class__.__doc__
                    or f"Extractor for {name}",
                }
            )
        except Exception as e:
            # Log error but continue
            print(f"Error loading extractor {name}: {e}")

    return {"extractors": extractors_info}


@app.get("/api/posts/list")
async def list_posts_detailed():
    """Get detailed list of configured posts with health status."""
    posts = mongo_storage.list_configured_posts()
    monitor = get_monitor()

    detailed_posts = []
    for post in posts:
        # Get health status for first source URL
        health = None
        if post.get("source_urls"):
            source_url = post["source_urls"][0]
            health = monitor.get_source_health(source_url)

        # Normalize timestamp fields
        last_updated = post.get("last_updated") or post.get("updated_at")

        detailed_posts.append(
            {
                **post,
                "health_status": health.get("status") if health else "unknown",
                "last_check": health.get("last_check") if health else None,
                "last_updated": last_updated,
                "extractor": post.get("extractor") or "default",
            }
        )

    return {"posts": detailed_posts}


@app.get("/api/sites/list")
async def list_wordpress_sites():
    """Get list of configured WordPress sites from MongoDB only."""
    # Load sites directly from MongoDB (no fallback to files or env vars)
    sites = mongo_storage.get_all_wp_sites()
    
    # Log what we're returning
    for site_key, site_data in sites.items():
        logging.info(f"[SITES LIST] {site_key}: button_style={site_data.get('button_style', 'NOT SET')}")

    # Return sites with all info including credentials for management UI
    return {"sites": sites}


@app.get("/api/cron/settings")
async def get_cron_settings():
    """Get cron/scheduled update settings from MongoDB."""
    settings = mongo_storage.get_cron_settings()
    
    if not settings:
        # Return default settings
        return {
            "enabled": False,
            "schedule": "hourly",
            "target_sites": []
        }
    
    return settings


@app.post("/api/cron/settings")
async def save_cron_settings(settings: dict):
    """Save cron/scheduled update settings to MongoDB."""
    
    # Validate required fields
    if "enabled" not in settings:
        raise HTTPException(status_code=400, detail="Missing 'enabled' field")
    
    if "schedule" not in settings:
        raise HTTPException(status_code=400, detail="Missing 'schedule' field")
    
    # Default target_sites if not provided
    if "target_sites" not in settings or not settings["target_sites"]:
        settings["target_sites"] = []
    
    if mongo_storage.set_cron_settings(settings):
        logging.info(f"[CRON] Saved settings: enabled={settings['enabled']}, sites={settings['target_sites']}")
        return {
            "success": True,
            "message": "Cron settings saved successfully"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save cron settings to database")


@app.post("/api/sites/add")
async def add_wordpress_site(site_data: dict):
    """Add a new WordPress site to configuration."""
    
    site_key = site_data.get("site_key", "").strip()
    base_url = site_data.get("base_url", "").strip()
    username = site_data.get("username", "").strip()
    app_password = site_data.get("app_password", "").strip()
    display_name = site_data.get("display_name", site_key).strip()
    button_style = site_data.get("button_style", "default").strip()
    
    if not all([site_key, base_url, username, app_password]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Check if site_key already exists
    existing = mongo_storage.get_wp_site(site_key)
    if existing:
        raise HTTPException(status_code=400, detail=f"Site key '{site_key}' already exists")
    
    # Save to MongoDB
    site_config = {
        "base_url": base_url,
        "username": username,
        "app_password": app_password,
        "display_name": display_name,
        "button_style": button_style
    }
    
    if mongo_storage.set_wp_site(site_key, site_config):
        logging.info(f"[SITES] Added new site: {site_key} ({display_name}) with button_style: {button_style}")
        return {
            "message": "Site added successfully",
            "site_key": site_key,
            "display_name": display_name,
            "button_style": button_style
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to save site to database")


@app.put("/api/sites/{site_key}")
async def update_wordpress_site(site_key: str, site_data: dict):
    """Update an existing WordPress site configuration."""
    
    base_url = site_data.get("base_url", "").strip()
    username = site_data.get("username", "").strip()
    app_password = site_data.get("app_password", "").strip()
    display_name = site_data.get("display_name", site_key).strip()
    button_style = site_data.get("button_style", "default").strip()
    
    if not all([base_url, username, app_password]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    
    # Check if site exists
    existing = mongo_storage.get_wp_site(site_key)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Site key '{site_key}' not found")
    
    # Update site in MongoDB
    site_config = {
        "base_url": base_url,
        "username": username,
        "app_password": app_password,
        "display_name": display_name,
        "button_style": button_style
    }
    
    if mongo_storage.set_wp_site(site_key, site_config):
        logging.info(f"[SITES] Updated site: {site_key} ({display_name}) with button_style: {button_style}")
        return {
            "message": "Site updated successfully",
            "site_key": site_key,
            "display_name": display_name,
            "button_style": button_style
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to update site in database")


@app.delete("/api/sites/{site_key}")
async def delete_wordpress_site(site_key: str):
    """Delete a WordPress site from configuration."""
    
    # Check if site exists
    existing = mongo_storage.get_wp_site(site_key)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Site key '{site_key}' not found")
    
    # Delete from MongoDB
    if mongo_storage.delete_wp_site(site_key):
        logging.info(f"[SITES] Deleted site: {site_key}")
        return {
            "message": "Site deleted successfully",
            "site_key": site_key
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete site from database")


@app.put("/api/posts/{post_id}/config")
async def update_post_config_api(post_id: int, config: PostConfig):
    """Update configuration for a post (posts.json editor)."""
    # Validate extractor exists if specified
    if hasattr(config, "extractor") and config.extractor:
        try:
            get_extractor(config.extractor)
        except:
            raise HTTPException(
                status_code=400, detail=f"Extractor '{config.extractor}' not found"
            )

    # Prepare post configuration dictionary
    post_config = {
        "post_id": post_id,
        "source_urls": [str(url) for url in config.source_urls],
        "timezone": config.timezone,
        "extractor": getattr(config, "extractor", None),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Save config
    mongo_storage.set_post_config(post_config)

    return {"success": True, "post_id": post_id, "message": "Configuration updated"}


@app.post("/trigger")
async def trigger_update(job: UpdateJob = Body(...)):
    """Trigger link update for a post (with optional source URLs override)."""
    # Use provided URLs or fetch from config
    source_urls = [str(url) for url in job.source_urls] if job.source_urls else None

    if not source_urls:
        # Try to get from stored config
        config = mongo_storage.get_post_config(job.post_id)
        if not config:
            raise HTTPException(
                status_code=400,
                detail=f"Post {job.post_id} not configured. Use /config/post to set source URLs first.",
            )
        source_urls = config["source_urls"]
        timezone = config.get("timezone", job.timezone)
    else:
        timezone = job.timezone

    task = celery_app.send_task(
        "tasks.update_post_task",
        kwargs={
            "post_id": job.post_id,
            "source_urls": source_urls,
            "timezone": timezone,
            "today_iso": job.today_iso,
        },
    )
    return JSONResponse(
        {"enqueued": True, "task_id": task.id, "source_urls": source_urls}
    )


@app.post("/update-post/{post_id}")
async def update_post_now(
    post_id: int,
    background_tasks: BackgroundTasks,
    sync: bool = False,
    target: Optional[str] = None,
):
    """
    Trigger link update for a post.

    By default (sync=False): Returns immediately and runs in background (parallel processing)
    With sync=True: Waits for completion and returns full results (for WordPress plugin)

    Multiple posts can be updated in parallel using background mode.
    Target must be a configured site key from the Sites tab, or 'all' for all sites.
    """
    # Get post configuration
    config = mongo_storage.get_post_config(post_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Post {post_id} not configured. Use /config/post to set it up first.",
        )

    source_urls = config["source_urls"]
    timezone = config.get("timezone", "Asia/Kolkata")
    extractor_name = config.get("extractor")
    extractor_map = config.get("extractor_map", {})  # New: per-source extractor mapping

    if isinstance(extractor_name, str):
        pass
    elif extractor_name is not None:
        extractor_name = str(extractor_name)
    else:
        extractor_name = None
    wp_site = (
        config.get("wp_site") if "wp_site" in config else None
    )  # Ensure wp_site is always defined

    # Helper function to get extractor for a URL
    def get_extractor_for_source(url: str):
        """Get extractor for a source URL, checking extractor_map first, then defaulting to Gemini"""
        print(f"[DEBUG] get_extractor_for_source called with url: {url}")
        print(f"[DEBUG] extractor_map: {extractor_map}")

        # Priority 1: Check extractor_map for this specific URL (manual or smart match)
        if extractor_map:
            # Normalize URL for comparison (handle trailing slash)
            url_normalized = url.rstrip("/")
            for map_url, map_extractor in extractor_map.items():
                map_url_normalized = map_url.rstrip("/")
                if url_normalized == map_url_normalized:
                    if map_extractor:
                        print(
                            f"[DEBUG] Using mapped extractor '{map_extractor}' for {url}"
                        )
                        return get_extractor(map_extractor)

        # Priority 2: Default to the default extractor (Gemini-based)
        print(f"[DEBUG] No mapping found for {url}, using default extractor")
        return get_extractor("default")

    # If sync mode (for WordPress), run immediately and return results
    if sync:
        # Calculate today's date in the configured timezone
        tz = pytz.timezone(timezone)
        today = datetime.now(tz)
        today_iso = today.strftime("%Y-%m-%d")

        # target: site_key (string) or 'all'
        if not target:
            raise HTTPException(
                status_code=400,
                detail="Target site must be specified. Use a site key from Sites tab or 'all'."
            )
        
        if target == "all":
            # Get all configured sites
            sites = mongo_storage.get_all_wp_sites()
            if not sites:
                raise HTTPException(
                    status_code=400,
                    detail="No sites configured. Please add sites in the Sites tab."
                )
            
            all_links = []
            errors = []

            # Step 1: Extract links from all sources
            for url in source_urls:
                try:
                    html = await fetch_html(url)
                    extractor = get_extractor_for_source(url)
                    print(
                        f"Extractor: {extractor.__class__.__name__}, Params: html_length={len(html)}, today_iso={today_iso}"
                    )
                    extracted_links = extractor.extract(html, today_iso)
                    print(
                        f"Extracted {len(extracted_links)} links from {url}: {extracted_links}"
                    )
                    all_links.extend(extracted_links)
                except RetryError as e:
                    # RetryError wraps the last exception
                    last_exception = e.last_attempt.exception() if e.last_attempt else None
                    error_msg = f"Failed after 3 retries: {str(last_exception) if last_exception else 'Connection error'}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"RetryError for {url}: {error_msg}")
                except httpx.TimeoutException as e:
                    error_msg = f"Request timeout: {str(e)}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"Timeout error for {url}: {error_msg}")
                except httpx.HTTPStatusError as e:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"HTTP error for {url}: {error_msg}")
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"Unexpected error for {url}: {error_msg}")

            # Step 2: Check if we have any links
            if not all_links:
                return JSONResponse(
                    {
                        "success": True,
                        "post_id": post_id,
                        "message": "No links found for today",
                        "links_found": 0,
                        "links_added": 0,
                        "errors": errors,
                    }
                )

            # Determine the target site key and post ID for fingerprint tracking
            target_site_key = None
            target_post_id = post_id  # Default to config's post_id

            if wp_site:
                if isinstance(wp_site, str):
                    target_site_key = wp_site
                    # Resolve the site-specific post ID
                    resolved_id = resolve_post_id_for_site(config, wp_site)
                    if resolved_id:
                        target_post_id = resolved_id
                elif isinstance(wp_site, dict) and "url" in wp_site:
                    sites = get_configured_wp_sites()
                    if sites:
                        target_site_key = list(sites.keys())[0]
                        # Resolve the site-specific post ID
                        resolved_id = resolve_post_id_for_site(config, target_site_key)
                        if resolved_id:
                            target_post_id = resolved_id

            # Step 3: Deduplicate against known links for this specific site using the correct post ID
            # For WSOP extractor, also check yesterday's fingerprints to avoid re-adding old links
            known_fps = mongo_storage.get_known_fingerprints(
                target_post_id, today_iso, target_site_key
            )
            
            # Check if this is a WSOP post (extractor returns links with both today and yesterday dates)
            from datetime import timedelta
            extractor_name = extractor.__class__.__name__.lower()
            if 'wsop' in extractor_name:
                yesterday_date = datetime.strptime(today_iso, "%Y-%m-%d") - timedelta(days=1)
                yesterday_iso = yesterday_date.strftime("%Y-%m-%d")
                yesterday_fps = mongo_storage.get_known_fingerprints(
                    target_post_id, yesterday_iso, target_site_key
                )
                known_fps = known_fps.union(yesterday_fps)
                print(f"[DEBUG] WSOP extractor: checking fingerprints for both {today_iso} and {yesterday_iso}")
            
            new_links = dedupe_by_fingerprint(all_links, known_fps)

            print(
                f"[DEBUG] Site: {target_site_key}, Post ID: {target_post_id}, Total extracted: {len(all_links)}, After dedup: {len(new_links)}"
            )

            # Step 4: Update WordPress (wp_site can be None to use environment defaults, or explicit config)
            if new_links:
                try:
                    # Determine which site to update and resolve correct post ID
                    if isinstance(wp_site, str):
                        # wp_site is a site key - resolve post ID for this site
                        site_post_id = resolve_post_id_for_site(config, wp_site)
                        if not site_post_id:
                            wp_result = {
                                "error": f"No post ID configured for site '{wp_site}'"
                            }
                        else:
                            # Load actual site configuration from MongoDB
                            site_config = mongo_storage.get_wp_site(wp_site)
                            if not site_config:
                                logging.warning(f"[TRIGGER] Site config not found for {wp_site}, using default")
                                site_config = None
                            else:
                                logging.info(f"[TRIGGER] Loaded site config for {wp_site}, button_style: {site_config.get('button_style', 'default')}")
                            
                            wp_result = await update_post_links_section(
                                site_post_id, new_links, wp_site, config, site_config
                            )
                    elif isinstance(wp_site, dict) and "url" in wp_site:
                        # wp_site is the actual site config - use first configured site
                        sites = get_configured_wp_sites()
                        if sites:
                            first_site_key = list(sites.keys())[0]
                            site_post_id = resolve_post_id_for_site(
                                config, first_site_key
                            )
                            if not site_post_id:
                                wp_result = {
                                    "error": f"No post ID configured for site '{first_site_key}'"
                                }
                            else:
                                # Load actual site configuration from MongoDB
                                site_config = mongo_storage.get_wp_site(first_site_key)
                                if not site_config:
                                    logging.warning(f"[TRIGGER] Site config not found for {first_site_key}, using default")
                                    site_config = None
                                else:
                                    logging.info(f"[TRIGGER] Loaded site config for {first_site_key}, button_style: {site_config.get('button_style', 'default')}")
                                
                                wp_result = await update_post_links_section(
                                    site_post_id, new_links, first_site_key, config, site_config
                                )
                        else:
                            wp_result = {"error": "No WordPress sites configured"}
                    elif wp_site is None:
                        # No wp_site specified - use environment variables (default site)
                        wp_result = await update_post_links_section(
                            target_post_id, new_links, None, config, None
                        )
                    else:
                        wp_result = {"error": "Invalid wp_site configuration"}

                    # Step 5: Save fingerprints for deduplication (site-specific with correct post ID)
                    # Group links by their date to save fingerprints correctly
                    if new_links and not wp_result.get("error"):
                        from collections import defaultdict
                        fps_by_date = defaultdict(set)
                        for link in new_links:
                            fp = fingerprint(link)
                            fps_by_date[link.published_date_iso].add(fp)
                        
                        # Save fingerprints for each date
                        for date_iso, fps in fps_by_date.items():
                            mongo_storage.save_new_links(
                                target_post_id, date_iso, fps, target_site_key
                            )
                            logging.info(f"[TRIGGER] Saved {len(fps)} fingerprints for date {date_iso}")

                        # Update last_updated timestamp
                        config["last_updated"] = datetime.utcnow().isoformat()
                        mongo_storage.set_post_config(config)

                    return JSONResponse(
                        {
                            "success": True,
                            "post_id": post_id,
                            "links_found": len(all_links),
                            "links_added": wp_result.get("links_added", len(new_links)),
                            "wordpress_updated": not wp_result.get("error"),
                            "wp_result": wp_result,
                            "errors": errors,
                        }
                    )
                except Exception as e:
                    print(f"[ERROR] WordPress update failed: {e}")
                    return JSONResponse(
                        {
                            "success": False,
                            "post_id": post_id,
                            "error": f"WordPress update failed: {str(e)}",
                            "links_found": len(all_links),
                            "errors": errors,
                        }
                    )
            else:
                # No new links after deduplication
                return JSONResponse(
                    {
                        "success": True,
                        "post_id": post_id,
                        "message": "No new links after deduplication - all links already exist",
                        "links_found": len(all_links),
                        "new_links": 0,
                        "links_added": 0,
                        "sections_pruned": 0,
                        "errors": errors,
                    }
                )

        # If target is 'all', extract once and update all configured sites
        if target == "all":
            # Determine today's date
            tz = pytz.timezone(timezone)
            today = datetime.now(tz)
            today_iso = today.strftime("%Y-%m-%d")

            # Step 1: Scrape and extract
            all_links = []
            errors = []
            for url in source_urls:
                try:
                    html = await fetch_html(url)
                    extractor = get_extractor_for_source(url)
                    print(
                        f"Extractor: {extractor.__class__.__name__}, Params: html_length={len(html)}, today_iso={today_iso}"
                    )
                    extracted_links = extractor.extract(html, today_iso)
                    print(
                        f"Extracted {len(extracted_links)} links from {url}: {extracted_links}"
                    )
                    links = extracted_links
                    all_links.extend(links)
                except RetryError as e:
                    # RetryError wraps the last exception
                    last_exception = e.last_attempt.exception() if e.last_attempt else None
                    error_msg = f"Failed after 3 retries: {str(last_exception) if last_exception else 'Connection error'}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"RetryError for {url}: {error_msg}")
                except httpx.TimeoutException as e:
                    error_msg = f"Request timeout: {str(e)}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"Timeout error for {url}: {error_msg}")
                except httpx.HTTPStatusError as e:
                    error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"HTTP error for {url}: {error_msg}")
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    errors.append({"url": url, "error": error_msg})
                    print(f"Error processing URL {url}: {error_msg}")

            if not all_links:
                return JSONResponse(
                    {
                        "success": True,
                        "post_id": post_id,
                        "message": "No links found for today",
                        "links_found": 0,
                        "links_added": 0,
                        "sections_pruned": 0,
                        "errors": errors,
                    }
                )

            # Step 2: Update each configured site with site-specific deduplication
            sites = get_configured_wp_sites()
            results = {}
            for site_key, site_conf in sites.items():
                try:
                    # Resolve the correct post ID for this specific site
                    site_post_id = resolve_post_id_for_site(config, site_key)
                    if not site_post_id:
                        results[site_key] = {
                            "error": f"No post ID configured for site '{site_key}'"
                        }
                        continue

                    # Deduplicate against known links for THIS specific site using the correct post ID
                    # For WSOP extractor, also check yesterday's fingerprints
                    known_fps = mongo_storage.get_known_fingerprints(
                        site_post_id, today_iso, site_key
                    )
                    
                    # Check if this is a WSOP post
                    from datetime import timedelta
                    extractor_name = extractor.__class__.__name__.lower()
                    if 'wsop' in extractor_name:
                        yesterday_date = datetime.strptime(today_iso, "%Y-%m-%d") - timedelta(days=1)
                        yesterday_iso = yesterday_date.strftime("%Y-%m-%d")
                        yesterday_fps = mongo_storage.get_known_fingerprints(
                            site_post_id, yesterday_iso, site_key
                        )
                        known_fps = known_fps.union(yesterday_fps)
                        print(f"[DEBUG] WSOP extractor: checking fingerprints for both {today_iso} and {yesterday_iso}")
                    
                    new_links = dedupe_by_fingerprint(all_links, known_fps)

                    print(
                        f"[DEBUG] Site '{site_key}': Post ID={site_post_id}, Total={len(all_links)}, After dedup={len(new_links)}"
                    )

                    if not new_links:
                        results[site_key] = {
                            "message": "No new links for this site",
                            "links_added": 0,
                        }
                        continue

                    # Load site configuration from MongoDB
                    site_config = mongo_storage.get_wp_site(site_key)
                    if not site_config:
                        logging.warning(f"[BATCH] Site config not found for {site_key}, using default")
                        site_config = None
                    else:
                        logging.info(f"[BATCH] Loaded site config for {site_key}, button_style: {site_config.get('button_style', 'default')}")

                    # Update this site with resolved post ID
                    wp_result = await update_post_links_section(
                        site_post_id, new_links, site_key, config, site_config
                    )
                    results[site_key] = wp_result

                    # Save fingerprints for this specific site using the correct post ID
                    # Group links by their date to save fingerprints correctly
                    if not wp_result.get("error"):
                        from collections import defaultdict
                        fps_by_date = defaultdict(set)
                        for link in new_links:
                            fp = fingerprint(link)
                            fps_by_date[link.published_date_iso].add(fp)
                        
                        # Save fingerprints for each date
                        for date_iso, fps in fps_by_date.items():
                            mongo_storage.save_new_links(
                                site_post_id, date_iso, fps, site_key
                            )
                            logging.info(f"[MULTI-SITE] Saved {len(fps)} fingerprints for site {site_key}, date {date_iso}")

                except Exception as e:
                    results[site_key] = {"error": str(e)}

            return JSONResponse(
                {
                    "success": True, 
                    "post_id": post_id, 
                    "results": results,
                    "errors": errors if errors else []
                }
            )

        # If target is a specific site key, pass it through
        if target and target != "all":
            # Pass the site key through with config - run_update_sync will resolve it
            return await run_update_sync(
                post_id, source_urls, timezone, extractor_name, target, config
            )

        # Should not reach here - target validation should have caught this
        raise HTTPException(
            status_code=400,
            detail="Invalid target. Must be a site key or 'all'."
        )

    # Background mode (for Cloud Scheduler parallel updates)
    task_id = f"task_{post_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Initialize task status
    task_status[task_id] = {
        "post_id": post_id,
        "status": "running",
        "started_at": datetime.now().isoformat(),
    }

    # Add to background tasks
    background_tasks.add_task(
        run_update_task,
        task_id=task_id,
        post_id=post_id,
        source_urls=source_urls,
        timezone=timezone,
        extractor_name=extractor_name,
        extractor_map=extractor_map,
        wp_site=wp_site,
    )

    return JSONResponse(
        {
            "success": True,
            "message": f"Update started for post {post_id}",
            "task_id": task_id,
            "post_id": post_id,
            "status_url": f"/task-status/{task_id}",
        }
    )


async def run_update_sync(
    post_id: int,
    source_urls: List[str],
    timezone: str,
    extractor_name: Optional[str] = None,
    wp_site: Optional[dict] = None,
    config: Optional[dict] = None,
):
    """
    Synchronous update function that returns full results immediately.
    Used when WordPress plugin needs immediate response.

    Args:
        post_id: WordPress post ID (legacy - used as fallback)
        source_urls: List of URLs to scrape
        timezone: Timezone for date calculation
        extractor_name: Optional name of specific extractor to use
        wp_site: Optional WordPress site config or site key string
        config: Optional post configuration (needed for site_post_ids mapping)
    """
    # Determine today's date
    tz = pytz.timezone(timezone)
    today = datetime.now(tz)
    today_iso = today.strftime("%Y-%m-%d")

    monitor = get_monitor()

    try:
        # Step 1: Scrape and extract
        all_links = []
        for url in source_urls:
            html = await fetch_html(url)

            # Choose extractor: mapped > default
            if extractor_name:
                extractor = get_extractor(extractor_name)
            else:
                # Default to the default extractor (Gemini-based)
                extractor = get_extractor("default")

            # Extract links using the chosen extractor
            print(
                f"Extractor: {extractor.__class__.__name__}, Params: html_length={len(html)}, today_iso={today_iso}"
            )
            extracted_links = extractor.extract(html, today_iso)
            print(f"Extracted {len(extracted_links)} links: {extracted_links}")
            links = extracted_links
            all_links.extend(links)

            # Record extraction for monitoring (with HTML for fingerprinting)
            monitor.record_extraction(
                source_url=url,
                date=today_iso,
                links_found=len(links),
                confidence=0.9 if links else 0.0,  # Simple confidence for now
                success=True,
                html=html,
            )

        if not all_links:
            return JSONResponse(
                {
                    "success": True,
                    "post_id": post_id,
                    "message": "No links found for today",
                    "links_found": 0,
                    "links_added": 0,
                    "sections_pruned": 0,
                }
            )

        # Determine target site key and resolve correct post ID
        target_site_key = None
        target_post_id = post_id  # Default fallback

        if wp_site:
            if isinstance(wp_site, str):
                target_site_key = wp_site
                # Resolve site-specific post ID if config is available
                if config:
                    resolved_id = resolve_post_id_for_site(config, wp_site)
                    if resolved_id:
                        target_post_id = resolved_id
            elif isinstance(wp_site, dict):
                # Try to find the site key from the config
                sites = get_configured_wp_sites()
                for key, conf in sites.items():
                    if conf.get("base_url") == wp_site.get("base_url"):
                        target_site_key = key
                        # Resolve site-specific post ID
                        if config:
                            resolved_id = resolve_post_id_for_site(config, key)
                            if resolved_id:
                                target_post_id = resolved_id
                        break

        # Step 2: Deduplicate against known links for this specific site using correct post ID
        # For WSOP extractor, also check yesterday's fingerprints
        known_fps = mongo_storage.get_known_fingerprints(
            target_post_id, today_iso, target_site_key
        )
        
        # Check if this is a WSOP post
        from datetime import timedelta
        if extractor_name and 'wsop' in extractor_name.lower():
            yesterday_date = datetime.strptime(today_iso, "%Y-%m-%d") - timedelta(days=1)
            yesterday_iso = yesterday_date.strftime("%Y-%m-%d")
            yesterday_fps = mongo_storage.get_known_fingerprints(
                target_post_id, yesterday_iso, target_site_key
            )
            known_fps = known_fps.union(yesterday_fps)
            logging.info(f"[SYNC UPDATE] WSOP extractor: checking fingerprints for both {today_iso} and {yesterday_iso}")
        
        new_links = dedupe_by_fingerprint(all_links, known_fps)

        # Load site configuration if target_site_key is available
        site_config = None
        if target_site_key:
            site_config = mongo_storage.get_wp_site(target_site_key)
            if site_config:
                logging.info(f"[SCRAPE ENDPOINT] Loaded site config for {target_site_key}, button_style: {site_config.get('button_style', 'default')}")

        # Step 3: Update WordPress using the resolved post ID
        wp_result = await update_post_links_section(
            target_post_id, new_links, target_site_key, config, site_config
        )

        # Step 4: Save fingerprints for new links (site-specific with correct post ID)
        # Group links by their date to save fingerprints correctly
        if new_links:
            from collections import defaultdict
            fps_by_date = defaultdict(set)
            for link in new_links:
                fp = fingerprint(link)
                fps_by_date[link.published_date_iso].add(fp)
            
            # Save fingerprints for each date
            for date_iso, fps in fps_by_date.items():
                mongo_storage.save_new_links(
                    target_post_id, date_iso, fps, target_site_key
                )
                logging.info(f"[SYNC UPDATE] Saved {len(fps)} fingerprints for date {date_iso}")

        # Build response message
        message_parts = []
        if wp_result["links_added"] > 0:
            message_parts.append(f"Added {wp_result['links_added']} new links")
        elif all_links:
            message_parts.append("All links already exist - no duplicates added")
        else:
            message_parts.append("No new links found for today")

        if wp_result["sections_pruned"] > 0:
            message_parts.append(f"pruned {wp_result['sections_pruned']} old sections")

        return JSONResponse(
            {
                "success": True,
                "post_id": post_id,
                "message": ", ".join(message_parts),
                "links_found": len(all_links),
                "links_added": wp_result["links_added"],
                "sections_pruned": wp_result["sections_pruned"],
                "date": today_iso,
                "links": [
                    {"title": link.title, "url": str(link.url)} for link in new_links
                ]
                if new_links
                else [],
            }
        )

    except Exception as e:
        # Record failed extraction for each source URL
        monitor = get_monitor()
        for url in source_urls:
            monitor.record_extraction(
                source_url=url,
                date=today_iso,
                links_found=0,
                confidence=0.0,
                success=False,
                error=str(e),
            )
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Check the status of a background task.
    Includes detailed processing status for each source URL.
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_status[task_id]
    detailed_status = {
        "post_id": task.get("post_id"),
        "status": task.get("status"),
        "success": task.get("success"),
        "results": task.get("results", []),
        "errors": task.get("errors", []),
        "completed_at": task.get("completed_at"),
    }

    print("DEBUG: detailed_status:", detailed_status)  # Debug statement

    return JSONResponse(detailed_status)


async def run_update_task(
    task_id: str,
    post_id: int,
    source_urls: List[str],
    timezone: str,
    extractor_name: Optional[str] = None,
    extractor_map: Optional[dict] = None,
    wp_site: Optional[dict] = None,
):
    """
    Background task that runs the update pipeline.
    Updates task_status with progress and results.
    """
    try:
        # Determine today's date
        tz = pytz.timezone(timezone)
        today = datetime.now(tz)
        today_iso = today.strftime("%Y-%m-%d")

        # Initialize results and errors
        results = []
        errors = []

        # Helper function to get extractor for a URL
        def get_extractor_for_source(url: str):
            """Get extractor for a source URL, checking extractor_map first, then defaulting to Gemini"""
            print(f"[DEBUG] BG get_extractor_for_source called with url: {url}")
            print(f"[DEBUG] BG extractor_map: {extractor_map}")

            # Priority 1: Check extractor_map for this specific URL (manual or smart match)
            if extractor_map:
                # Normalize URL for comparison (handle trailing slash)
                url_normalized = url.rstrip("/")
                for map_url, map_extractor in extractor_map.items():
                    map_url_normalized = map_url.rstrip("/")
                    if url_normalized == map_url_normalized:
                        if map_extractor:
                            print(
                                f"[DEBUG] BG Using mapped extractor '{map_extractor}' for {url}"
                            )
                            return get_extractor(map_extractor)

            # Priority 2: Default to the default extractor (Gemini-based)
            print(f"[DEBUG] BG No mapping found for {url}, using default extractor")
            return get_extractor("default")

        # Step 1: Scrape and extract
        for url in source_urls:
            try:
                html = await fetch_html(url)

                # Get extractor using priority logic
                extractor = get_extractor_for_source(url)

                # Extract links using the chosen extractor
                print(
                    f"Extractor: {extractor.__class__.__name__}, Params: html_length={len(html)}, today_iso={today_iso}"
                )
                extracted_links = extractor.extract(html, today_iso)
                print(f"Extracted {len(extracted_links)} links: {extracted_links}")
                links = [
                    {
                        "title": link.title,
                        "url": str(link.url),
                        "published_date_iso": link.published_date_iso,
                    }
                    for link in extracted_links
                ]
                results.append({"url": url, "links": links})
            except Exception as e:
                errors.append({"url": url, "error": str(e)})

        # Update task status
        task_status[task_id] = {
            "post_id": post_id,
            "status": "completed",
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "completed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        task_status[task_id] = {
            "post_id": post_id,
            "status": "failed",
            "success": False,
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
        }


# ============================================================================
# BATCH UPDATE PROCESSOR (Background Task for Dashboard)
# ============================================================================


async def process_batch_updates(request_id: str, target: str = "all"):
    """
    Process all posts in a batch update request.
    Runs in background with progress tracking.
    """
    manager = get_batch_manager()
    batch_request = manager.get_request(request_id)

    if not batch_request:
        return

    batch_request.start()

    # Process posts with concurrency limit (3 at a time to avoid overwhelming WordPress)
    # WordPress can be slow with large content updates, so we keep concurrency low
    semaphore = asyncio.Semaphore(3)

    async def process_single_post(post_id: int):
        async with semaphore:
            await process_post_update(request_id, post_id, target)

    # Start all post updates
    tasks = [process_single_post(post_id) for post_id in batch_request.post_ids]
    await asyncio.gather(*tasks, return_exceptions=True)

    batch_request.complete()


async def process_post_update(request_id: str, post_id: int, target: str = "all"):
    """
    Update a single post with progress tracking and logging.
    Calls the same extraction logic as /trigger but with state management.
    """
    manager = get_batch_manager()

    try:
        # Update to running
        await manager.update_post_state(
            request_id,
            post_id,
            status=UpdateStatus.RUNNING,
            progress=0,
            message="Starting update",
            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Starting update for post {post_id}",
        )

        # Get post config
        config = mongo_storage.get_post_config(post_id)
        if not config:
            raise Exception(f"Post {post_id} not configured")
        
        logging.info(f"[BATCH] Post {post_id} config loaded: days_to_keep={config.get('days_to_keep', 'not set')}, full_config_keys={list(config.keys())}")

        source_urls = config.get("source_urls", [])
        timezone = config.get("timezone", "Asia/Kolkata")
        extractor_name = config.get("extractor")
        extractor_map = config.get(
            "extractor_map", {}
        )  # NEW: per-source extractor mapping
        insertion_point = config.get(
            "insertion_point"
        )  # NEW v2.3: Custom link placement
        if isinstance(extractor_name, str):
            pass
        elif extractor_name is not None:
            extractor_name = str(extractor_name)
        else:
            extractor_name = None
        wp_site = config.get("wp_site") if "wp_site" in config else None

        # Helper function to get extractor for a URL
        def get_extractor_for_source(url: str):
            """Get extractor for a source URL, checking extractor_map first, then defaulting to Gemini"""
            # Priority 1: Check extractor_map for this specific URL (manual or smart match)
            if extractor_map:
                # Normalize URL for comparison (handle trailing slash)
                url_normalized = url.rstrip("/")
                for map_url, map_extractor in extractor_map.items():
                    map_url_normalized = map_url.rstrip("/")
                    if url_normalized == map_url_normalized:
                        if map_extractor:
                            print(
                                f"[BATCH] Using mapped extractor '{map_extractor}' for {url}"
                            )
                            return get_extractor(map_extractor)

            # Priority 2: Default to the default extractor (Gemini-based)
            print(f"[BATCH] No mapping found for {url}, using default extractor")
            return get_extractor("default")

        await manager.update_post_state(
            request_id,
            post_id,
            progress=10,
            message="Configuration loaded",
            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Source URLs: {', '.join(source_urls)}",
        )

        # Determine today's date
        tz = pytz.timezone(timezone)
        today = datetime.now(tz)
        today_iso = today.strftime("%Y-%m-%d")

        # Extract links
        await manager.update_post_state(
            request_id,
            post_id,
            progress=20,
            message="Fetching HTML",
            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Fetching HTML from source URLs...",
        )

        all_links = []
        for url in source_urls:
            html = await fetch_html(url)

            await manager.update_post_state(
                request_id,
                post_id,
                progress=40,
                message=f"Extracting links from {url[:50]}...",
                log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Fetched {len(html)} bytes from {url}",
            )

            # Choose extractor using the helper function (checks extractor_map first)
            extractor = get_extractor_for_source(url)

            # Extract with monitoring
            monitor = get_monitor()

            # Extract links using the extractor's extract method
            links = extractor.extract(html, today_iso)
            all_links.extend(links)

            # Record extraction for monitoring
            monitor.record_extraction(url, today_iso, len(links), 1.0, html)

            await manager.update_post_state(
                request_id,
                post_id,
                progress=60,
                message=f"Extracted {len(links)} links",
                log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Extracted {len(links)} links using {extractor.__class__.__name__} extractor",
            )

        if not all_links:
            await manager.update_post_state(
                request_id,
                post_id,
                status=UpdateStatus.SUCCESS,
                progress=100,
                message="No new links found",
                links_found=0,
                links_added=0,
                log_message=f"[{datetime.now().strftime('%H:%M:%S')}] No links found for today",
            )
            return

        # Deduplicate against known links for this specific site
        await manager.update_post_state(
            request_id,
            post_id,
            progress=70,
            message="Deduplicating links",
            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Deduplicating {len(all_links)} links for site '{target}'...",
        )

        # Resolve the correct post ID for the target site
        targets_to_process = []
        
        if target == "all":
            # Fetch all configured sites
            sites = get_configured_wp_sites()
            if not sites:
                # If no sites configured, maybe fallback to default env? 
                # For now, let's assume at least one site or default env
                targets_to_process.append({"site_key": None, "post_id": post_id})
            else:
                for site_key in sites:
                    site_post_id = resolve_post_id_for_site(config, site_key)
                    if site_post_id:
                        targets_to_process.append({"site_key": site_key, "post_id": site_post_id})
                    else:
                        print(f"[BATCH] Warning: No post ID for site {site_key} on post {post_id}")
        else:
            # For specific sites, resolve the site-specific post ID
            target_post_id = resolve_post_id_for_site(config, target)
            if not target_post_id:
                raise Exception(f"No post ID configured for site '{target}'")
            targets_to_process.append({"site_key": target, "post_id": target_post_id})

        total_links_added = 0
        total_sections_pruned = 0
        sites_updated_count = 0
        sites_failed = []
        
        for target_info in targets_to_process:
            target_site_key = target_info["site_key"]
            target_post_id = target_info["post_id"]
            
            try:
                # Deduplicate against known links for this specific site
                # For WSOP extractor, also check yesterday's fingerprints to avoid re-adding old links
                known_fps = mongo_storage.get_known_fingerprints(
                    target_post_id, today_iso, target_site_key
                )
                
                # Check if this is a WSOP post (extractor returns links with both today and yesterday dates)
                from datetime import timedelta
                extractor_name = extractor.__class__.__name__.lower()
                if 'wsop' in extractor_name:
                    yesterday_date = datetime.strptime(today_iso, "%Y-%m-%d") - timedelta(days=1)
                    yesterday_iso = yesterday_date.strftime("%Y-%m-%d")
                    yesterday_fps = mongo_storage.get_known_fingerprints(
                        target_post_id, yesterday_iso, target_site_key
                    )
                    known_fps = known_fps.union(yesterday_fps)
                    logging.info(f"[BATCH UPDATE] WSOP extractor: checking fingerprints for both {today_iso} and {yesterday_iso}")
                
                new_links = dedupe_by_fingerprint(all_links, known_fps)

                await manager.update_post_state(
                    request_id,
                    post_id,
                    progress=80,
                    message=f"Updating {target_site_key or 'default'} ({len(new_links)} new)",
                    log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Site '{target_site_key or 'default'}': Found {len(new_links)} new links",
                )

                # Load site configuration if target_site_key is available
                site_config = None
                if target_site_key:
                    site_config = mongo_storage.get_wp_site(target_site_key)
                    if site_config:
                        logging.info(f"[BATCH UPDATE] Loaded site config for {target_site_key}, button_style: {site_config.get('button_style', 'default')}")

                # Update WordPress
                wp_result = await update_post_links_section(
                    target_post_id, new_links, target_site_key, config, site_config
                )
                
                if not wp_result.get("error"):
                    total_links_added += wp_result.get("links_added", 0)
                    total_sections_pruned += wp_result.get("sections_pruned", 0)
                    sites_updated_count += 1
                    
                    await manager.update_post_state(
                        request_id,
                        post_id,
                        log_message=f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Site '{target_site_key or 'default'}' updated successfully: {wp_result.get('links_added', 0)} links added",
                    )
                    
                    # Save fingerprints for this specific site
                    # Group links by their date to save fingerprints correctly
                    if new_links:
                        from collections import defaultdict
                        fps_by_date = defaultdict(set)
                        for link in new_links:
                            fp = fingerprint(link)
                            fps_by_date[link.published_date_iso].add(fp)
                        
                        # Save fingerprints for each date
                        total_fps_saved = 0
                        for date_iso, fps in fps_by_date.items():
                            mongo_storage.save_new_links(
                                target_post_id, date_iso, fps, target_site_key
                            )
                            total_fps_saved += len(fps)
                            logging.info(f"[BATCH UPDATE] Saved {len(fps)} fingerprints for date {date_iso}")
                        
                        await manager.update_post_state(
                            request_id,
                            post_id,
                            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] Saved {total_fps_saved} fingerprints for site {target_site_key or 'default'}",
                        )
                else:
                    sites_failed.append(target_site_key or 'default')
                    await manager.update_post_state(
                        request_id,
                        post_id,
                        log_message=f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Site '{target_site_key or 'default'}' update failed: {wp_result.get('error')}",
                    )
            except Exception as site_error:
                # Log the error but continue processing other sites
                sites_failed.append(target_site_key or 'default')
                await manager.update_post_state(
                    request_id,
                    post_id,
                    log_message=f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Site '{target_site_key or 'default'}' update failed: {repr(site_error)}",
                )

        # Determine status based on results
        if sites_failed and sites_updated_count == 0:
            # All sites failed
            status = UpdateStatus.FAILED
            message = f"Failed to update all {len(sites_failed)} sites"
        elif sites_failed and sites_updated_count > 0:
            # Some sites succeeded, some failed
            status = UpdateStatus.SUCCESS
            message = f"Updated {sites_updated_count} sites ({len(sites_failed)} failed: {', '.join(sites_failed)})"
        elif total_links_added > 0:
            # All sites succeeded with new links
            status = UpdateStatus.SUCCESS
            if target == "all":
                message = f"Added {total_links_added} links across {sites_updated_count} sites"
            else:
                message = f"Added {total_links_added} links"
        elif len(all_links) > 0:
            # Links were found but all were duplicates
            status = UpdateStatus.NO_CHANGES
            message = f"No new links (found {len(all_links)} duplicates)"
        else:
            # No links found at all
            status = UpdateStatus.NO_CHANGES
            message = "No links found"

        # Success or No Changes
        await manager.update_post_state(
            request_id,
            post_id,
            status=status,
            progress=100,
            message=message,
            links_found=len(all_links),
            links_added=total_links_added,
            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Update completed: {total_links_added} links added across {sites_updated_count} sites, {len(sites_failed)} failed",
        )

    except Exception as e:
        # Failed
        await manager.update_post_state(
            request_id,
            post_id,
            status=UpdateStatus.FAILED,
            progress=0,
            message=f"Error: {str(e)[:100]}",
            error=str(e),
            log_message=f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Update failed: {repr(e)}",
        )


# Remove the hardcoded endpoint for configuring post 114
@app.post("/config/post/114")
async def configure_post_114():
    pass  # This endpoint is no longer needed as configurations should be updated dynamically


# ==================== Analytics Endpoints ====================


@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard(days: int = 30):
    """
    Get dashboard summary with key metrics

    Query params:
    - days: Number of days to analyze (default 30)

    Returns high-level metrics including:
    - Total updates, success rate
    - Total links added
    - Active posts
    - Health distribution
    """
    analytics = get_analytics_engine()
    return analytics.get_dashboard_summary(days=days)


@app.get("/api/analytics/timeline")
async def get_analytics_timeline(days: int = 30, granularity: str = "daily"):
    """
    Get timeline of updates over period

    Query params:
    - days: Number of days to analyze (default 30)
    - granularity: 'hourly', 'daily', or 'weekly' (default 'daily')

    Returns timeline data with success/failure counts per time period
    """
    analytics = get_analytics_engine()
    return {
        "timeline": analytics.get_update_timeline(days=days, granularity=granularity),
        "period_days": days,
        "granularity": granularity,
    }


@app.get("/api/analytics/posts")
async def get_post_analytics(days: int = 30):
    """
    Get performance metrics per post

    Query params:
    - days: Number of days to analyze (default 30)

    Returns performance data for each post including:
    - Total updates, success rate
    - Links added
    - Last update time
    """
    analytics = get_analytics_engine()
    return {"posts": analytics.get_post_performance(days=days), "period_days": days}


@app.get("/api/analytics/sources")
async def get_source_analytics(days: int = 30):
    """
    Get performance metrics per source URL

    Query params:
    - days: Number of days to analyze (default 30)

    Returns metrics for each source including:
    - Extraction success rate
    - Links extracted
    - Current health status
    """
    analytics = get_analytics_engine()
    return {"sources": analytics.get_source_performance(days=days), "period_days": days}


@app.get("/api/analytics/extractors")
async def get_extractor_analytics(days: int = 30):
    """
    Get performance metrics per extractor type

    Query params:
    - days: Number of days to analyze (default 30)

    Returns metrics for each extractor including:
    - Total updates, success rate
    - Links extracted
    - Posts using this extractor
    """
    analytics = get_analytics_engine()
    return {
        "extractors": analytics.get_extractor_performance(days=days),
        "period_days": days,
    }


@app.get("/api/analytics/sites")
async def get_site_analytics(days: int = 30):
    """
    Get performance metrics per WordPress site

    Query params:
    - days: Number of days to analyze (default 30)

    Returns metrics for each site including:
    - Total links added
    - Unique posts updated
    - Average links per post
    """
    analytics = get_analytics_engine()
    return {"sites": analytics.get_site_performance(days=days), "period_days": days}


@app.get("/api/analytics/hourly-pattern")
async def get_hourly_pattern_analytics(days: int = 7):
    """
    Get update patterns by hour of day

    Query params:
    - days: Number of days to analyze (default 7)

    Returns 24 data points showing update activity by hour
    """
    analytics = get_analytics_engine()
    return {
        "hourly_pattern": analytics.get_hourly_pattern(days=days),
        "period_days": days,
    }


@app.get("/api/analytics/links-trend")
async def get_links_trend_analytics(days: int = 30):
    """
    Get daily trend of links added

    Query params:
    - days: Number of days to analyze (default 30)

    Returns daily data points with links added per site
    """
    analytics = get_analytics_engine()
    return {"trend": analytics.get_links_added_trend(days=days), "period_days": days}


# ==================== Button Styles API ====================


@app.get("/api/button-styles")
async def get_all_button_styles():
    """
    Get all available button style templates.
    
    Returns:
        Dict with all button styles, including name, description, and CSS properties
    """
    from . import button_styles
    return {"styles": button_styles.get_all_button_styles()}


@app.get("/api/button-styles/{style_name}")
async def get_button_style(style_name: str):
    """
    Get a specific button style by name.
    
    Args:
        style_name: Name of the style (e.g., 'default', 'gradient_blue')
        
    Returns:
        Button style configuration with CSS and hover properties
    """
    from . import button_styles
    style = button_styles.get_button_style(style_name)
    if not style:
        raise HTTPException(status_code=404, detail=f"Button style '{style_name}' not found")
    return {"style_name": style_name, "style": style}


@app.get("/api/button-styles/preview/{style_name}")
async def preview_button_style(style_name: str):
    """
    Generate preview HTML for a button style.
    
    Args:
        style_name: Name of the style to preview
        
    Returns:
        HTML snippet showing the button in action
    """
    from . import button_styles
    
    # Sample link for preview
    sample_link = {
        "url": "#",
        "title": "Sample Link",
        "order": 1,
        "target": "_blank"
    }
    
    button_html = button_styles.generate_button_html(sample_link, style_name)
    return {"style_name": style_name, "html": button_html}

