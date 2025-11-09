#!/usr/bin/env python3
"""
MongoDB Index Migration Script

Drops the old unique index (post_id, date_iso) and creates the new 
site-specific index (post_id, date_iso, site_key) for multi-site support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def migrate_indexes():
    """Drop old index and create new site-specific indexes"""
    
    # Get MongoDB connection details from environment
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "SmartLinkUpdater")
    
    print(f"Connecting to MongoDB: {mongodb_uri}")
    print(f"Database: {db_name}")
    
    # Connect to MongoDB
    client = MongoClient(mongodb_uri)
    db = client[db_name]
    fingerprints = db["fingerprints"]
    
    # Get current indexes
    print("\n📋 Current indexes:")
    for index in fingerprints.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")
    
    # Drop old index if it exists
    old_index_name = "post_id_1_date_iso_1"
    try:
        print(f"\n🗑️  Dropping old index: {old_index_name}")
        fingerprints.drop_index(old_index_name)
        print(f"✅ Successfully dropped index: {old_index_name}")
    except Exception as e:
        if "index not found" in str(e).lower():
            print(f"ℹ️  Index {old_index_name} doesn't exist (already dropped or never created)")
        else:
            print(f"❌ Error dropping index: {e}")
            raise
    
    # Create new indexes
    print("\n🔨 Creating new indexes:")
    
    # 1. Unique compound index with site_key
    print("  Creating unique index: (post_id, date_iso, site_key)")
    fingerprints.create_index(
        [
            ("post_id", ASCENDING),
            ("date_iso", ASCENDING),
            ("site_key", ASCENDING)
        ],
        unique=True,
        name="post_id_1_date_iso_1_site_key_1"
    )
    print("  ✅ Created unique compound index")
    
    # 2. Individual field indexes for query optimization
    print("  Creating index: post_id")
    fingerprints.create_index([("post_id", ASCENDING)])
    print("  ✅ Created post_id index")
    
    print("  Creating index: date_iso")
    fingerprints.create_index([("date_iso", ASCENDING)])
    print("  ✅ Created date_iso index")
    
    print("  Creating index: site_key")
    fingerprints.create_index([("site_key", ASCENDING)])
    print("  ✅ Created site_key index")
    
    # Show final indexes
    print("\n📋 Final indexes:")
    for index in fingerprints.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")
    
    # Count documents
    doc_count = fingerprints.count_documents({})
    print(f"\n📊 Total fingerprints in collection: {doc_count}")
    
    # Show sample of documents without site_key (need migration)
    docs_without_site_key = fingerprints.count_documents({"site_key": {"$exists": False}})
    if docs_without_site_key > 0:
        print(f"⚠️  Warning: {docs_without_site_key} documents don't have site_key field")
        print("   These documents may need site_key added for proper deduplication")
    
    client.close()
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    try:
        migrate_indexes()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        exit(1)
