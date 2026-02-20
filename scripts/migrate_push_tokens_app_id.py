"""
Migration: Backfill app_id on existing push tokens.

All tokens registered before the per-app targeting feature was added
belong to the Travel Town rewards app (the only app at the time).
This script sets app_id = "travel_town" on every token that is missing
the field. It is safe to re-run — tokens already tagged are not touched.

Usage:
    python scripts/migrate_push_tokens_app_id.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is on the path and .env is loaded
env_path = Path(__file__).parent.parent / ".env"
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path)

from backend.app.mongo_storage import _get_storage

DEFAULT_APP_ID = "travel_town"


def migrate():
    db = _get_storage().db
    collection = db["push_tokens"]

    # Count tokens that need migration
    missing_count = collection.count_documents({"app_id": {"$exists": False}})
    total_count = collection.count_documents({})

    print(f"Total tokens in DB:          {total_count}")
    print(f"Tokens missing app_id:       {missing_count}")

    if missing_count == 0:
        print("Nothing to migrate — all tokens already have app_id set.")
        return

    # Backfill app_id = "travel_town" for all tokens that don't have it yet
    result = collection.update_many(
        {"app_id": {"$exists": False}},
        {
            "$set": {
                "app_id": DEFAULT_APP_ID,
                "app_id_migrated_at": datetime.utcnow().isoformat(),
            }
        },
    )

    print(f"Migrated {result.modified_count} token(s) → app_id='{DEFAULT_APP_ID}'")

    # Verify
    still_missing = collection.count_documents({"app_id": {"$exists": False}})
    if still_missing == 0:
        print("✅ Migration complete — all tokens now have app_id.")
    else:
        print(f"⚠️  {still_missing} token(s) still missing app_id after migration!")


if __name__ == "__main__":
    migrate()
