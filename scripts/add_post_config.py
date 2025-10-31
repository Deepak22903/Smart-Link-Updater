#!/usr/bin/env python3
"""Add a post configuration for SmartLinkUpdater.

Tries to call the running API at http://localhost:8000/config/post. If the API
is not reachable, falls back to calling mongo_storage.set_post_config directly.

Usage:
    python scripts/add_post_config.py
"""
import json
import sys
from urllib.parse import urljoin

POST_ID = 135
SOURCE_URLS = ["https://mosttechs.com/bingo-bash-free-chips/"]
EXTRACTOR = "mosttechs"
TIMEZONE = "Asia/Kolkata"

API_BASE = "http://localhost:8000"

payload = {
    "post_id": POST_ID,
    "source_urls": SOURCE_URLS,
    "timezone": TIMEZONE,
    "extractor": EXTRACTOR
}

try:
    import requests
    url = urljoin(API_BASE, "/config/post")
    print(f"Trying API at {url} ...")
    r = requests.post(url, json=payload, timeout=5)
    print("Status:", r.status_code)
    print(r.text)
    if r.status_code == 200:
        sys.exit(0)
except Exception as e:
    print("API call failed, falling back to direct DB write:", e)

# Fallback: direct write using mongo_storage
try:
    import os
    import pathlib
    # Ensure project root is on sys.path so we can import backend.app.mongo_storage
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from backend.app import mongo_storage

    post_config = {
        "post_id": POST_ID,
        "source_urls": SOURCE_URLS,
        "timezone": TIMEZONE,
        "extractor": EXTRACTOR,
        "updated_at": None
    }

    ok = mongo_storage.set_post_config(post_config)
    if ok:
        print(f"Post config for post_id={POST_ID} written to storage.")
    else:
        print("Failed to write post config via mongo_storage.set_post_config")
except Exception as e:
    print("Direct DB fallback failed:", e)
    sys.exit(2)
