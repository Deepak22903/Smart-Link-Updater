#!/usr/bin/env python3
"""
Script to delete all push tokens from the MongoDB push_tokens collection.
Run from the project root:
  python3 scripts/clear_push_tokens.py
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://deepakshitole4_db_user:6KiH8syvWCTNhh2D@smartlinkupdater.rpo4hmt.mongodb.net/SmartLinkUpdater?appName=SmartLinkUpdater"
)
DB_NAME = os.getenv("MONGODB_DATABASE", "SmartLinkUpdater")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

collection = db["push_tokens"]
count_before = collection.count_documents({})

if count_before == 0:
    print("No tokens found — collection is already empty.")
else:
    print(f"Found {count_before} token(s):")
    for doc in collection.find({}, {"token_id": 1, "device_type": 1, "app_version": 1}):
        print(f"  • {doc.get('token_id', '?')[:20]}...  device={doc.get('device_type','?')}  v{doc.get('app_version','?')}")

    confirm = input(f"\nDelete all {count_before} token(s)? [y/N]: ").strip().lower()
    if confirm == "y":
        result = collection.delete_many({})
        print(f"✅ Deleted {result.deleted_count} token(s).")
    else:
        print("Aborted — no tokens deleted.")

client.close()
