import subprocess
import os
import time
import sys
import redis
import asyncio
from config import config


def clear_redis_cache():
    try:
        print("🧹 Clearing Redis cache...")
        r = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True,
        )

        r.ping()
        app_keys = [
            config.SENTIMENT_CACHE_KEY,
            config.SUMMARY_CACHE_KEY,
            "youtube_comments:*",
            "sentiment:*",
            "summary:*",
        ]

        total_deleted = 0
        for key_pattern in app_keys:
            if "*" in key_pattern:

                keys = r.keys(key_pattern)
                if keys:
                    deleted = r.delete(*keys)
                    total_deleted += deleted
            else:

                if r.exists(key_pattern):
                    r.delete(key_pattern)
                    total_deleted += 1

        if total_deleted > 0:
            print(f"   ✅ Cleared {total_deleted} Redis cache entries")
        else:
            print("   ✅ No application cache found in Redis")

    except redis.ConnectionError as e:
        print(f"   ⚠️  Warning: Could not connect to Redis ({e})")
        print("   ℹ️  Redis cache clearing skipped - Redis might not be running yet")
    except Exception as e:
        print(f"   ⚠️  Warning: Failed to clear Redis cache: {e}")


def start_services():
    print("🚀 Starting YouTube Sentiment Analysis System...")
    print("=" * 50)

    clear_redis_cache()
    print()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    services = [
        ("YouTube API", os.path.join(root_dir, "ingestion", "youtube_api.py")),
        ("Comment Cleaner", os.path.join(root_dir, "processing", "comment_cleaner.py")),
        (
            "Sentiment Analyzer",
            os.path.join(root_dir, "processing", "sentiment_analyzer.py"),
        ),
        (
            "Comment Summarizer",
            os.path.join(root_dir, "processing", "comment_summarizer.py"),
        ),
    ]

    processes = []

    for service_name, script_path in services:
        try:
            if os.name == "nt":
                proc = subprocess.Popen(
                    [sys.executable, script_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    cwd=root_dir,
                )
            else:
                proc = subprocess.Popen([sys.executable, script_path], cwd=root_dir)
            processes.append((service_name, proc))
            print(f"   ✅ Started {service_name}")
            time.sleep(2)
        except Exception as e:
            print(f"   ❌ Failed to start {service_name}: {e}")

    try:
        dashboard_path = os.path.join(root_dir, "dashboard", "dashboard.py")
        if os.name == "nt":
            dashboard_proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", dashboard_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=root_dir,
            )
        else:
            dashboard_proc = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", dashboard_path], cwd=root_dir
            )
        processes.append(("Streamlit Dashboard", dashboard_proc))
        print("   ✅ Started Streamlit Dashboard")
    except Exception as e:
        print(f"   ❌ Failed to start Dashboard: {e}")

    print("\n🎯 All services started successfully!")
    print("=" * 50)
    print("📊 Dashboard: http://localhost:8501")
    print("🔧 To stop services, close the console windows or press Ctrl+C")

    return processes

async def initialize_mongodb():
    try:
        print("🗄️  Initializing MongoDB...")
        from database.startup_mongodb import startup_mongodb

        success = await startup_mongodb()
        if success:
            print("✅ MongoDB initialized successfully")
        else:
            print("⚠️  MongoDB initialization failed - continuing without database")
        return success
    except Exception as e:
        print(f"⚠️  MongoDB initialization error: {e} - continuing without database")
        return False

if __name__ == "__main__":
    try:
        clear_redis_cache()
        print("🚀 Starting BigData Analytics System...")
        asyncio.run(initialize_mongodb())

        processes = start_services()

        print("\n⏳ System running... Press Ctrl+C to exit")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        for service_name, proc in processes:
            try:
                proc.terminate()
                print(f"   ✅ Stopped {service_name}")
            except:
                pass
        print("🔴 System shutdown complete")
