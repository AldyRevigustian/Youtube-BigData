import sys
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Tambahkan path ke config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.config as config


def get_db():
    try:
        client = MongoClient(config.MONGODB_CONNECTION_STRING)
        db = client[config.MONGODB_DATABASE]
        client.admin.command('ping')  # Test koneksi
        return db
    except ConnectionFailure as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        return None


def delete_collection(db, collection_name):
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        print(f"   ✅ Deleted collection: {collection_name}")
        return True
    else:
        print(f"   ℹ️  Collection not found: {collection_name}")
        return False


def clear_comments(video_id):
    db = get_db()
    if db is not None:
        delete_collection(db, f"{video_id}_comments")


def clear_summaries(video_id):
    db = get_db()
    if db is not None:
        delete_collection(db, f"{video_id}_summaries")


def clear_both(video_id):
    db = get_db()
    if db is not None:
        delete_collection(db, f"{video_id}_comments")
        delete_collection(db, f"{video_id}_summaries")


def main():
    print("🔧 MongoDB Collection Management Tool")
    print("=" * 45)

    video_id = config.VIDEO_ID
    print(f"Video ID from config: {video_id}")

    while True:
        print("\nOptions:")
        print("1. Delete comments collection")
        print("2. Delete summaries collection")
        print("3. Delete both")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            clear_comments(video_id)
        elif choice == "2":
            clear_summaries(video_id)
        elif choice == "3":
            clear_both(video_id)
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("   ❌ Invalid option. Please select 1-4.")


if __name__ == "__main__":
    main()
