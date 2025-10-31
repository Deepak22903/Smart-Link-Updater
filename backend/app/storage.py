from typing import Set, List, Optional
import json
from pathlib import Path

# Simple file-backed storage for configs and fingerprints.
# This keeps things portable and easy to test. For production, replace with MongoDB.

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
POSTS_FILE = DATA_DIR / "posts.json"
FINGERPRINTS_FILE = DATA_DIR / "fingerprints.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _read_json_file(path: Path, default):
    try:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json_file(path: Path, data) -> None:
    _ensure_data_dir()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_post_config(post_id: int) -> Optional[dict]:
    posts = _read_json_file(POSTS_FILE, {})
    post = posts.get(str(post_id))
    return post


def set_post_config(
    post_id: int, 
    source_urls: List[str], 
    timezone: str = "Asia/Kolkata",
    wp_site: Optional[dict] = None
) -> None:
    """
    Configure a post with source URLs and optional WordPress site credentials.
    
    Args:
        post_id: WordPress post ID
        source_urls: List of URLs to scrape
        timezone: Timezone for date calculation
        wp_site: Optional dict with WordPress site config:
                 {"base_url": "https://site.com", "username": "user", "app_password": "pass"}
                 If not provided, uses default from environment variables
    """
    posts = _read_json_file(POSTS_FILE, {})
    config = {
        "post_id": int(post_id),
        "source_urls": source_urls,
        "timezone": timezone,
    }
    if wp_site:
        config["wp_site"] = wp_site
    posts[str(post_id)] = config
    _write_json_file(POSTS_FILE, posts)


def get_known_fingerprints(post_id: int, date_iso: str) -> Set[str]:
    fps = _read_json_file(FINGERPRINTS_FILE, {})
    key = f"{post_id}_{date_iso}"
    return set(fps.get(key, []))


def save_new_links(post_id: int, date_iso: str, fingerprints: Set[str]) -> None:
    fps = _read_json_file(FINGERPRINTS_FILE, {})
    key = f"{post_id}_{date_iso}"
    existing = set(fps.get(key, []))
    fps[key] = list(existing.union(fingerprints))
    _write_json_file(FINGERPRINTS_FILE, fps)


def list_configured_posts() -> List[dict]:
    posts = _read_json_file(POSTS_FILE, {})
    return [posts[k] for k in sorted(posts.keys(), key=lambda x: int(x))]
