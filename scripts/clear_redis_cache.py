import redis
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config


def clear_all_cache():
    try:
        print("🧹 Clearing ALL Redis cache...")
        r = redis.Redis(
            host=config.REDIS_HOST, 
            port=config.REDIS_PORT, 
            db=config.REDIS_DB,
            decode_responses=True
        )
        
        r.ping()
        
        keys = r.keys('*')
        if keys:
            deleted_count = r.delete(*keys)
            print(f"   ✅ Cleared {deleted_count} Redis cache entries")
        else:
            print("   ✅ Redis cache already empty")
            
    except redis.ConnectionError as e:
        print(f"   ❌ Could not connect to Redis: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Failed to clear Redis cache: {e}")
        return False
    
    return True


def clear_app_cache():
    try:
        print("🧹 Clearing application Redis cache...")
        r = redis.Redis(
            host=config.REDIS_HOST, 
            port=config.REDIS_PORT, 
            db=config.REDIS_DB,
            decode_responses=True
        )
        
        r.ping()
        
        app_keys = [
            config.SENTIMENT_CACHE_KEY,
            config.SUMMARY_CACHE_KEY,
            "youtube_comments:*",
            "sentiment:*",
            "summary:*"
        ]
        
        total_deleted = 0
        for key_pattern in app_keys:
            if '*' in key_pattern:
                keys = r.keys(key_pattern)
                if keys:
                    deleted = r.delete(*keys)
                    total_deleted += deleted
            else:
                if r.exists(key_pattern):
                    r.delete(key_pattern)
                    total_deleted += 1
        
        if total_deleted > 0:
            print(f"   ✅ Cleared {total_deleted} application cache entries")
        else:
            print("   ✅ No application cache found in Redis")
            
    except redis.ConnectionError as e:
        print(f"   ❌ Could not connect to Redis: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Failed to clear Redis cache: {e}")
        return False
    
    return True


def list_cache_keys():
    try:
        print("📋 Listing Redis cache keys...")
        r = redis.Redis(
            host=config.REDIS_HOST, 
            port=config.REDIS_PORT, 
            db=config.REDIS_DB,
            decode_responses=True
        )
        
        r.ping()
        
        keys = r.keys('*')
        if keys:
            print(f"   Found {len(keys)} keys:")
            for key in sorted(keys):
                key_type = r.type(key)
                ttl = r.ttl(key)
                ttl_info = f" (TTL: {ttl}s)" if ttl > 0 else " (no expiry)" if ttl == -1 else " (expired)"
                print(f"     • {key} [{key_type}]{ttl_info}")
        else:
            print("   ✅ No keys found in Redis")
            
    except redis.ConnectionError as e:
        print(f"   ❌ Could not connect to Redis: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Failed to list Redis keys: {e}")
        return False
    
    return True


def main():
    print("🔧 Redis Cache Management Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Clear application cache only")
        print("2. Clear ALL Redis cache")
        print("3. List cache keys")
        print("4. Exit")
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                clear_app_cache()
            elif choice == "2":
                confirm = input("⚠️  This will delete ALL Redis data. Are you sure? (y/N): ").strip().lower()
                if confirm == 'y':
                    clear_all_cache()
                else:
                    print("   ℹ️  Operation cancelled")
            elif choice == "3":
                list_cache_keys()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("   ❌ Invalid option. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    main()
