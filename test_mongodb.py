"""
Simple test script to verify MongoDB integration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.app import mongo_storage

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("=" * 80)
    print("🧪 Testing MongoDB Integration")
    print("=" * 80)
    
    try:
        # Test 1: Get database instance
        print("\n1️⃣ Testing database connection...")
        db = mongo_storage.get_database()
        print(f"   ✓ Connected to database: {db.name}")
        
        # Test 2: Test post configuration
        print("\n2️⃣ Testing post configuration...")
        mongo_storage.set_post_config(
            post_id=9999,
            source_urls=["https://test.example.com/test"],
            timezone="Asia/Kolkata"
        )
        print("   ✓ Created test post config")
        
        config = mongo_storage.get_post_config(9999)
        print(f"   ✓ Retrieved test post config: {config}")
        
        # Test 3: Test fingerprints
        print("\n3️⃣ Testing fingerprints...")
        mongo_storage.save_new_links(9999, "2025-10-28", {"fp1", "fp2", "fp3"})
        print("   ✓ Saved test fingerprints")
        
        fps = mongo_storage.get_known_fingerprints(9999, "2025-10-28")
        print(f"   ✓ Retrieved fingerprints: {len(fps)} items")
        
        # Test 4: Test list posts
        print("\n4️⃣ Testing list configured posts...")
        posts = mongo_storage.list_configured_posts()
        print(f"   ✓ Retrieved {len(posts)} configured posts")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        mongo_storage.delete_post_config(9999)
        print("   ✓ Deleted test post config")
        
        print("\n" + "=" * 80)
        print("✅ All tests passed! MongoDB integration is working.")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1)
