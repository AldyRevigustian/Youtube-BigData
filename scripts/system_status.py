import redis
import json
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import *


def check_system_status():

    print("🔍 YOUTUBE SENTIMENT ANALYSIS SYSTEM STATUS")
    print("=" * 60)

    try:
        r = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
        )
        r.ping()
        print("✅ Redis: Connected and operational")

        sentiment_count = r.llen(SENTIMENT_CACHE_KEY)
        print(f"   📊 Cached sentiment results: {sentiment_count}")

        summary_count = r.llen(SUMMARY_CACHE_KEY)
        print(f"   📝 Cached summaries: {summary_count}")

    except Exception as e:
        print(f"❌ Redis: Connection failed - {e}")

    try:
        consumer = KafkaConsumer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, consumer_timeout_ms=1000
        )
        topics = consumer.list_consumer_group_offsets()
        print("✅ Kafka: Connected and operational")
        consumer.close()

    except Exception as e:
        print(f"❌ Kafka: Connection failed - {e}")
    print()
    print("🚀 ACTIVE SERVICES:")
    print("   📺 YouTube API: Fetching live comments")
    print("   🧹 Comment Cleaner: Cleaning and filtering comments")
    print("   🧠 Sentiment Analyzer: Processing comments")
    print("   📄 Comment Summarizer: Generating summaries")
    print("   📊 Streamlit Dashboard: Real-time visualization")

    print()
    print("🌐 ACCESS POINTS:")
    print("   Dashboard: http://localhost:8501")
    print("   Redis: localhost:6379")
    print("   Kafka: localhost:9092")
    print()
    print("📋 SYSTEM ARCHITECTURE:")
    print("   YouTube API → Kafka → raw-comments-topic")
    print("   ├─ Comment Cleaner → clean-comments-topic")
    print("   ├─ Sentiment Analyzer → sentiment-results-topic → Redis")
    print("   └─ Comment Summarizer → Tumbling Window (3 min) → Summary → Redis")
    print("   Dashboard ← Redis (Real-time visualization)")


def show_recent_activity():

    try:
        r = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
        )

        print("\n📈 RECENT SENTIMENT ANALYSIS:")
        print("-" * 40)

        recent_results = r.lrange(SENTIMENT_CACHE_KEY, -5, -1)

        if recent_results:
            for result in recent_results:
                data = json.loads(result)
                sentiment = data.get("sentiment", "Unknown")
                confidence = data.get("confidence", 0)
                text = data.get("text", "")[:50]

                print(f"   {sentiment:<12} ({confidence:.2f}) - {text}...")
        else:
            print("   No recent sentiment analysis results found")

        print("\n📰 RECENT SUMMARIES:")
        print("-" * 40)

        recent_summaries = r.lrange(SUMMARY_CACHE_KEY, -2, -1)

        if recent_summaries:
            for summary in recent_summaries:
                data = json.loads(summary)
                timestamp = data.get("timestamp", "Unknown")
                content = data.get("summary", "")[:100]

                print(f"   [{timestamp}] {content}...")
        else:
            print("   No recent summaries found")

    except Exception as e:
        print(f"❌ Error retrieving recent activity: {e}")


if __name__ == "__main__":
    check_system_status()
    show_recent_activity()

    print("\n🎯 NEXT STEPS:")
    print("   1. Monitor the Streamlit dashboard for real-time metrics")
    print("   2. Wait for 5-minute intervals to see comment summaries")
    print("   3. Test with live YouTube streams for best results")
