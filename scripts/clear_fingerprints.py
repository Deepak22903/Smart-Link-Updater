"""
Script to clear fingerprints for a specific post and date range.
Usage: python scripts/clear_fingerprints.py
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.mongo_storage import _get_storage

POST_ID = 2260
DATES = ["2026-02-19", "2026-02-18"]  # today and yesterday

def clear_fingerprints(post_id: int, dates: list):
    db = _get_storage().db

    for date_iso in dates:
        result = db.fingerprints.delete_many({"post_id": post_id, "date_iso": date_iso})
        print(f"Deleted {result.deleted_count} fingerprint record(s) for post {post_id} on {date_iso}")

if __name__ == "__main__":
    print(f"Clearing fingerprints for post {POST_ID} on dates: {DATES}")
    clear_fingerprints(POST_ID, DATES)
    print("Done.")
