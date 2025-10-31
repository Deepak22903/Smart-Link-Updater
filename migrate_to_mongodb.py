"""
Data Migration Script: JSON to MongoDB

Migrates existing JSON data files to MongoDB:
- posts.json -> posts collection
- fingerprints.json -> fingerprints collection  
- monitoring.json -> monitoring collection
- alerts.json -> alerts collection

Usage:
    python migrate_to_mongodb.py [--dry-run]
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from backend.app import mongo_storage

# Data directory
DATA_DIR = Path(__file__).parent / "backend" / "data"


def load_json_file(file_path: Path, default=None):
    """Load JSON file or return default"""
    try:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            return default if default is not None else {}
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return default if default is not None else {}


def migrate_posts(dry_run=False):
    """Migrate posts.json to posts collection"""
    print("\n📦 Migrating posts.json...")
    
    posts_file = DATA_DIR / "posts.json"
    posts_data = load_json_file(posts_file, {})
    
    if not posts_data:
        print("   No posts to migrate")
        return 0
    
    count = 0
    for post_id_str, config in posts_data.items():
        post_id = int(post_id_str)
        
        if dry_run:
            print(f"   [DRY RUN] Would migrate post {post_id}: {config.get('source_urls', [])}")
        else:
            try:
                mongo_storage.set_post_config(
                    post_id=post_id,
                    source_urls=config.get("source_urls", []),
                    timezone=config.get("timezone", "Asia/Kolkata"),
                    wp_site=config.get("wp_site"),
                    extractor=config.get("extractor")
                )
                print(f"   ✓ Migrated post {post_id}")
                count += 1
            except Exception as e:
                print(f"   ❌ Error migrating post {post_id}: {e}")
    
    return count


def migrate_fingerprints(dry_run=False):
    """Migrate fingerprints.json to fingerprints collection"""
    print("\n🔑 Migrating fingerprints.json...")
    
    fp_file = DATA_DIR / "fingerprints.json"
    fp_data = load_json_file(fp_file, {})
    
    if not fp_data:
        print("   No fingerprints to migrate")
        return 0
    
    count = 0
    for key, fingerprints in fp_data.items():
        # Key format: "post_id_date_iso" where date_iso is YYYY-MM-DD
        try:
            # Split on underscore, expecting format like "105_2025-10-26"
            parts = key.split("_", 1)  # Split on first underscore only
            if len(parts) != 2:
                print(f"   ⚠️  Skipping invalid key format: {key}")
                continue
            
            post_id = int(parts[0])
            date_iso = parts[1]  # Already in YYYY-MM-DD format
            
            if dry_run:
                print(f"   [DRY RUN] Would migrate fingerprints for post {post_id}, date {date_iso}: {len(fingerprints)} items")
            else:
                try:
                    mongo_storage.save_new_links(post_id, date_iso, set(fingerprints))
                    print(f"   ✓ Migrated fingerprints for post {post_id}, date {date_iso}")
                    count += 1
                except Exception as e:
                    print(f"   ❌ Error migrating fingerprints for {key}: {e}")
        except Exception as e:
            print(f"   ❌ Error parsing key {key}: {e}")
    
    return count


def migrate_monitoring(dry_run=False):
    """Migrate monitoring.json to monitoring collection"""
    print("\n📊 Migrating monitoring.json...")
    
    mon_file = DATA_DIR / "monitoring.json"
    mon_data = load_json_file(mon_file, {})
    
    if not mon_data:
        print("   No monitoring data to migrate")
        return 0
    
    count = 0
    for source_url, monitoring_info in mon_data.items():
        if dry_run:
            print(f"   [DRY RUN] Would migrate monitoring for {source_url}")
        else:
            try:
                mongo_storage.save_source_monitoring(monitoring_info)
                print(f"   ✓ Migrated monitoring for {source_url}")
                count += 1
            except Exception as e:
                print(f"   ❌ Error migrating monitoring for {source_url}: {e}")
    
    return count


def migrate_alerts(dry_run=False):
    """Migrate alerts.json to alerts collection"""
    print("\n🚨 Migrating alerts.json...")
    
    alerts_file = DATA_DIR / "alerts.json"
    alerts_data = load_json_file(alerts_file, [])
    
    if not alerts_data:
        print("   No alerts to migrate")
        return 0
    
    count = 0
    for alert in alerts_data:
        if dry_run:
            print(f"   [DRY RUN] Would migrate alert: {alert.get('alert_type')} for {alert.get('source_url')}")
        else:
            try:
                mongo_storage.save_alert(alert)
                print(f"   ✓ Migrated alert: {alert.get('alert_type')} for {alert.get('source_url')}")
                count += 1
            except Exception as e:
                print(f"   ❌ Error migrating alert: {e}")
    
    return count


def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate JSON data to MongoDB")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without making changes")
    args = parser.parse_args()
    
    dry_run = args.dry_run
    
    print("=" * 80)
    print("🚀 SmartLinkUpdater: JSON to MongoDB Migration")
    print("=" * 80)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
    
    print(f"\n📁 Data directory: {DATA_DIR}")
    
    # Run migrations
    posts_count = migrate_posts(dry_run)
    fp_count = migrate_fingerprints(dry_run)
    mon_count = migrate_monitoring(dry_run)
    alerts_count = migrate_alerts(dry_run)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Migration Summary")
    print("=" * 80)
    print(f"Posts migrated:        {posts_count}")
    print(f"Fingerprints migrated: {fp_count}")
    print(f"Monitoring migrated:   {mon_count}")
    print(f"Alerts migrated:       {alerts_count}")
    print(f"Total items:           {posts_count + fp_count + mon_count + alerts_count}")
    
    if dry_run:
        print("\n⚠️  This was a DRY RUN. Run without --dry-run to perform actual migration.")
    else:
        print("\n✅ Migration completed successfully!")
        print("\n💡 Tip: Keep your JSON files as backups. You can delete them later once you verify MongoDB is working.")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
