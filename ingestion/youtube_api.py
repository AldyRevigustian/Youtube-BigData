from googleapiclient.discovery import build
from kafka import KafkaProducer
import json
import time
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = config.YOUTUBE_API_KEY
VIDEO_ID = config.VIDEO_ID
CHANNEL_NAME = config.CHANNEL_NAME

youtube = build("youtube", "v3", developerKey=API_KEY)

producer = KafkaProducer(
    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


def get_live_chat_id(video_id):
    response = youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()

    items = response.get("items", [])
    if not items:
        raise Exception("Video ID tidak ditemukan atau bukan live stream")

    live_details = items[0].get("liveStreamingDetails", {})
    live_chat_id = live_details.get("activeLiveChatId")

    if not live_chat_id:
        raise Exception("Live Chat ID tidak tersedia (video mungkin tidak sedang live)")

    return live_chat_id

def stream_live_comments(live_chat_id):
    next_page_token = None

    while True:
        response = (
            youtube.liveChatMessages()
            .list(
                liveChatId=live_chat_id,
                part="snippet,authorDetails",
                pageToken=next_page_token,
            )
            .execute()
        )

        for item in response["items"]:
            if "textMessageDetails" not in item["snippet"]:
                continue

            comment_data = {
                "timestamp": item["snippet"]["publishedAt"],
                "username": item["authorDetails"]["displayName"],
                "comment": item["snippet"]["textMessageDetails"]["messageText"],
                "video_id": VIDEO_ID,
                "channel_name": CHANNEL_NAME,
            }

            print(comment_data)
            try:
                producer.send("raw-comments", value=comment_data)
            except Exception as e:
                print(f"Gagal kirim ke Kafka: {e}")

        next_page_token = response.get("nextPageToken")
        polling_interval = int(response["pollingIntervalMillis"]) / 1000.0
        time.sleep(polling_interval)

if __name__ == "__main__":
    live_chat_id = get_live_chat_id(VIDEO_ID)
    print("Live Chat ID:", live_chat_id)
    stream_live_comments(live_chat_id)
