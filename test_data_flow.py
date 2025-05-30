#!/usr/bin/env python3
"""
Quick test script to verify end-to-end data flow in the YouTube sentiment analysis system
"""

import json
import time
from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC

def send_test_comments():
    """Send test comments to Kafka to verify the data flow"""
    
    # Test comments with different sentiments
    test_comments = [
        {
            "comment_id": "test_001",
            "text": "This is an amazing stream! Love it! 😍",
            "author": "TestUser1",
            "timestamp": time.time(),
            "video_id": "test_video_123"
        },
        {
            "comment_id": "test_002", 
            "text": "This is terrible content, waste of time 😡",
            "author": "TestUser2",
            "timestamp": time.time(),
            "video_id": "test_video_123"
        },
        {
            "comment_id": "test_003",
            "text": "The content is okay, nothing special",
            "author": "TestUser3", 
            "timestamp": time.time(),
            "video_id": "test_video_123"
        },
        {
            "comment_id": "test_004",
            "text": "¡Excelente contenido! Me encanta mucho",
            "author": "TestUser4",
            "timestamp": time.time(),
            "video_id": "test_video_123"
        },
        {
            "comment_id": "test_005",
            "text": "Sehr gut! Das ist fantastisch!",
            "author": "TestUser5",
            "timestamp": time.time(),
            "video_id": "test_video_123"
        }
    ]
    
    try:        # Initialize Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        print("🚀 Sending test comments to Kafka...")
        
        for i, comment in enumerate(test_comments, 1):
            # Send to raw comments topic
            producer.send(RAW_COMMENTS_TOPIC, comment)
            print(f"✅ Sent test comment {i}/5: {comment['text'][:50]}...")
            time.sleep(1)  # Small delay between messages
        
        producer.flush()
        print("\n🎉 All test comments sent successfully!")
        print("📊 Check the Streamlit dashboard to see real-time processing:")
        print("   - http://localhost:8501")
        print("⚡ Check Storm UI for processing topology:")
        print("   - http://localhost:8080")
        
    except Exception as e:
        print(f"❌ Error sending test comments: {e}")

if __name__ == "__main__":
    send_test_comments()
