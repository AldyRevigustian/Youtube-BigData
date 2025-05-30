#!/usr/bin/env python3
"""
Demo script untuk menunjukkan alur kerja Comment Cleaner
Mengirim komentar dengan emoji dan melihat hasilnya setelah dibersihkan
"""

import json
import time
import threading
from kafka import KafkaProducer, KafkaConsumer
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC, CLEAN_COMMENTS_TOPIC


def listen_to_clean_comments():
    """Listen to clean comments topic and display results"""
    consumer = KafkaConsumer(
        CLEAN_COMMENTS_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id='demo-listener'
    )
    
    print("🎧 Listening to clean-comments topic...")
    
    for message in consumer:
        comment_data = message.value
        print(f"📥 CLEANED: {comment_data['username']}: '{comment_data['comment']}'")


def send_demo_comments():
    """Send demo comments with emojis to raw-comments topic"""
    
    demo_comments = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "username": "EmojiLover",
            "comment": "Wow amazing stream! 😍✨💖🔥🎉",
            "video_id": "demo_video",
            "channel_name": "Demo Channel"
        },
        {
            "timestamp": "2024-01-01T10:01:00Z",
            "username": "ShortComment",
            "comment": "😂",  # Will be filtered out
            "video_id": "demo_video", 
            "channel_name": "Demo Channel"
        },
        {
            "timestamp": "2024-01-01T10:02:00Z",
            "username": "NormalUser",
            "comment": "This is a normal comment without any emojis",
            "video_id": "demo_video",
            "channel_name": "Demo Channel"
        },
        {
            "timestamp": "2024-01-01T10:03:00Z",
            "username": "MixedContent", 
            "comment": "Great content! Keep it up! 👍👏 Really enjoying this stream",
            "video_id": "demo_video",
            "channel_name": "Demo Channel"
        },
        {
            "timestamp": "2024-01-01T10:04:00Z",
            "username": "OnlyEmojis",
            "comment": "💀💀💀💀",  # Will be filtered out
            "video_id": "demo_video",
            "channel_name": "Demo Channel"
        },
        {
            "timestamp": "2024-01-01T10:05:00Z",
            "username": "TooShort",
            "comment": "short",  # Will be filtered out (< 10 chars)
            "video_id": "demo_video",
            "channel_name": "Demo Channel"
        }
    ]
    
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda x: json.dumps(x).encode("utf-8"),
    )
    
    print("📤 Sending demo comments to raw-comments topic...\n")
    
    for i, comment in enumerate(demo_comments, 1):
        print(f"📤 ORIGINAL #{i}: {comment['username']}: '{comment['comment']}'")
        producer.send(RAW_COMMENTS_TOPIC, comment)
        time.sleep(2)  # Wait 2 seconds between messages
    
    producer.flush()
    producer.close()
    print(f"\n✅ Sent {len(demo_comments)} demo comments")


def main():
    """Run the demo"""
    print("🎬 Comment Cleaner Demo")
    print("=" * 60)
    print("This demo shows how comments flow through the cleaning process:")
    print("1. Raw comments (with emojis) → raw-comments topic")
    print("2. Comment Cleaner processes them")
    print("3. Clean comments (emoji-free, filtered) → clean-comments topic")
    print()
    
    # Start listener in background thread
    listener_thread = threading.Thread(target=listen_to_clean_comments, daemon=True)
    listener_thread.start()
    
    # Wait a moment for listener to start
    time.sleep(2)
    
    # Send demo comments
    send_demo_comments()
    
    # Wait for processing
    print("\n⏳ Waiting 10 seconds for comment cleaner to process...")
    time.sleep(10)
    
    print("\n📊 Demo Complete!")
    print("Expected behavior:")
    print("   ✅ Comments with emojis should appear cleaned")
    print("   🚫 Very short comments and emoji-only comments should be filtered out")
    print("   ✅ Normal comments should pass through unchanged")


if __name__ == "__main__":
    main()
