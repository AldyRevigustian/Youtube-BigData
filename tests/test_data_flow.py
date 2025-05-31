import json
import time
from kafka import KafkaProducer
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import KAFKA_BOOTSTRAP_SERVERS, RAW_COMMENTS_TOPIC


def main():
    test_comments = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "username": "TestUser1",
            "comment": "This is an amazing stream! Love it! 😍💖✨",
            "video_id": "test_video_123",
        },
        {
            "timestamp": "2024-01-01T10:01:00Z",
            "username": "TestUser2",
            "comment": "This is terrible content, waste of time 😡💀👎",
            "video_id": "test_video_123",
        },
        {
            "timestamp": "2024-01-01T10:02:00Z",
            "username": "TestUser3",
            "comment": "The content is okay, nothing special here really",
            "video_id": "test_video_123",
        },
        {
            "timestamp": "2024-01-01T10:03:00Z",
            "username": "TestUser4",
            "comment": "¡Excelente contenido! Me encanta mucho 🎉🔥❤️",
            "video_id": "test_video_123",
        },
        {
            "timestamp": "2024-01-01T10:04:00Z",
            "username": "TestUser5",
            "comment": "Sehr gut! Das ist fantastisch! 👏🎊🌟",
            "video_id": "test_video_123",
        },
        {
            "timestamp": "2024-01-01T10:05:00Z",
            "username": "TestUser6",
            "comment": "😂😂😂",
            "video_id": "test_video_123",
        },
    ]

    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
        )

        print("🚀 Sending test comments to Kafka...")
        for i, comment in enumerate(test_comments, 1):

            producer.send(RAW_COMMENTS_TOPIC, comment)
            print(
                f"✅ Sent test comment {i}/{len(test_comments)}: {comment['comment'][:50]}..."
            )
            time.sleep(1)

        producer.flush()
        print("\n🎉 All test comments sent successfully!")
        print("📊 Check the Streamlit dashboard to see real-time processing:")
        print("   - http://localhost:8501")

    except Exception as e:
        print(f"❌ Error sending test comments: {e}")


if __name__ == "__main__":
    main()
