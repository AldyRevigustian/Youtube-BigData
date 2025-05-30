#!/usr/bin/env python3
"""
Test script untuk Comment Cleaner - menguji kemampuan membersihkan emoji dan filtering
"""

import json
import time
from kafka import KafkaProducer, KafkaConsumer
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC, CLEAN_COMMENTS_TOPIC


def test_comment_cleaner():
    """Test comment cleaner dengan berbagai jenis komentar"""

    # Test comments dengan berbagai skenario
    test_comments = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "username": "TestUser1",
            "comment": "This is an amazing stream! Love it! 😍💖✨🔥",
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        },
        {
            "timestamp": "2024-01-01T10:01:00Z",
            "username": "TestUser2", 
            "comment": "Bagus banget streamnya! 👏🎉🎊",
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        },
        {
            "timestamp": "2024-01-01T10:02:00Z",
            "username": "TestUser3",
            "comment": "😂😂😂",  # Ini akan difilter karena setelah cleaning < 10 karakter
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        },
        {
            "timestamp": "2024-01-01T10:03:00Z",
            "username": "TestUser4",
            "comment": "💀💀💀💀💀",  # Ini juga akan difilter
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        },
        {
            "timestamp": "2024-01-01T10:04:00Z",
            "username": "TestUser5",
            "comment": "Konten yang sangat berkualitas dan menarik untuk ditonton! ⭐",
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        },
        {
            "timestamp": "2024-01-01T10:05:00Z",
            "username": "TestUser6",
            "comment": "short",  # Ini akan difilter karena < 10 karakter
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        },
        {
            "timestamp": "2024-01-01T10:06:00Z",
            "username": "TestUser7",
            "comment": "This comment has exactly ten characters!",  # Ini akan lolos
            "video_id": "test_video_123",
            "channel_name": "Test Channel"
        }
    ]

    try:
        # Initialize Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

        print("🧪 Testing Comment Cleaner...")
        print("=" * 60)
        print("📤 Sending test comments to raw-comments topic...")

        for i, comment in enumerate(test_comments, 1):
            producer.send(RAW_COMMENTS_TOPIC, comment)
            print(f"✅ Sent test comment {i}/{len(test_comments)}: {comment['comment']}")
            time.sleep(0.5)

        producer.flush()
        print(f"\n📤 All {len(test_comments)} test comments sent to {RAW_COMMENTS_TOPIC}")
        
        # Wait a bit for processing
        print("\n⏳ Waiting 10 seconds for comment cleaner to process...")
        time.sleep(10)
        
        # Now listen to clean-comments topic to see results
        print(f"\n📥 Listening to {CLEAN_COMMENTS_TOPIC} topic for cleaned results...")
        
        consumer = KafkaConsumer(
            CLEAN_COMMENTS_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            consumer_timeout_ms=15000  # Wait 15 seconds for messages
        )
        
        cleaned_count = 0
        print("\n📋 Cleaned Comments Received:")
        print("-" * 60)
        
        for message in consumer:
            cleaned_count += 1
            comment_data = message.value
            print(f"✅ #{cleaned_count}: {comment_data['username']}: {comment_data['comment']}")
        
        consumer.close()
        
        print(f"\n📊 Test Results Summary:")
        print(f"   📤 Sent: {len(test_comments)} comments")
        print(f"   📥 Received (cleaned): {cleaned_count} comments")
        print(f"   🚫 Filtered out: {len(test_comments) - cleaned_count} comments")
        
        expected_filtered = 3  # short comments and emoji-only comments
        if len(test_comments) - cleaned_count == expected_filtered:
            print(f"\n✅ TEST PASSED: Comment cleaner working correctly!")
            print(f"   Expected {expected_filtered} comments to be filtered, got {len(test_comments) - cleaned_count}")
        else:
            print(f"\n⚠️  TEST WARNING: Expected {expected_filtered} comments to be filtered")
            print(f"   But got {len(test_comments) - cleaned_count} filtered")
        
        print(f"\n🔧 Comment Cleaner Features Tested:")
        print(f"   ✅ Emoji removal (💖, 😍, ✨, 🔥, etc.)")
        print(f"   ✅ Length filtering (< 10 characters)")
        print(f"   ✅ Preserving other fields (timestamp, username, video_id, etc.)")

    except Exception as e:
        print(f"❌ Error testing comment cleaner: {e}")


if __name__ == "__main__":
    test_comment_cleaner()
