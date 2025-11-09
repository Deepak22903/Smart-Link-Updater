#!/usr/bin/env python3
"""
Migrate Existing Fingerprints to Add site_key

Adds a default site_key to all fingerprint documents that don't have one.
This is needed for backward compatibility after migrating to multi-site support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def migrate_fingerprints(default_site_key="this"):
    """Add default site_key to fingerprints that don't have one"""
    
    # Get MongoDB connection details from environment
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "SmartLinkUpdater")
    
    print(f"Connecting to MongoDB: {mongodb_uri}")
    print(f"Database: {db_name}")
    print(f"Default site_key: '{default_site_key}'")
    
    # Connect to MongoDB
    client = MongoClient(mongodb_uri)
    db = client[db_name]
    fingerprints = db["fingerprints"]
    
    # Count documents without site_key
    docs_without_site_key = fingerprints.count_documents({"site_key": {"$exists": False}})
    print(f"\n📊 Found {docs_without_site_key} fingerprints without site_key")
    
    if docs_without_site_key == 0:
        print("✅ No migration needed - all documents already have site_key")
        client.close()
        return
    
    # Show sample of documents to migrate
    print("\n📋 Sample documents to migrate:")
    for doc in fingerprints.find({"site_key": {"$exists": False}}).limit(3):
        post_id = doc.get('post_id', 'N/A')
        date_iso = doc.get('date_iso', 'N/A')
        fingerprint = doc.get('fingerprint', '')
        fingerprint_preview = fingerprint[:20] + "..." if fingerprint else 'N/A'
        print(f"  - post_id: {post_id}, date_iso: {date_iso}, fingerprint: {fingerprint_preview}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will update {docs_without_site_key} documents")
    print(f"   Setting site_key = '{default_site_key}' for all documents without site_key")
    
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Migration cancelled")
        client.close()
        return
    
    # Perform the update
    print(f"\n🔄 Updating documents...")
    result = fingerprints.update_many(
        {"site_key": {"$exists": False}},
        {"$set": {"site_key": default_site_key}}
    )
    
    print(f"✅ Updated {result.modified_count} documents")
    
    # Verify
    remaining = fingerprints.count_documents({"site_key": {"$exists": False}})
    if remaining == 0:
        print("✅ Migration complete - all documents now have site_key")
    else:
        print(f"⚠️  Warning: {remaining} documents still don't have site_key")
    
    # Show distribution by site_key
    print("\n📊 Fingerprints by site_key:")
    pipeline = [
        {"$group": {"_id": "$site_key", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    for result in fingerprints.aggregate(pipeline):
        site = result['_id'] or "(null)"
        count = result['count']
        print(f"  - {site}: {count} fingerprints")
    
    client.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    import sys
    
    # Allow passing site_key as argument
    default_site = "this"
    if len(sys.argv) > 1:
        default_site = sys.argv[1]
    
    try:
        migrate_fingerprints(default_site_key=default_site)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        exit(1)
