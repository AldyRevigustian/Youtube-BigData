import json
import redis
from transformers import pipeline
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from dateutil.parser import parse as parse_date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self):
        logger.info("Loading sentiment analysis model...")
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis", model=config.SENTIMENT_MODEL, return_all_scores=True
        )

        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True,
        )
        self.consumer = KafkaConsumer(
            config.CLEAN_COMMENTS_TOPIC,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="sentiment-analyzer",
        )

        self.producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        logger.info("Sentiment Analyzer initialized successfully")

    def analyze_sentiment(self, text):
        try:
            results = self.sentiment_pipeline(text)

            best_result = max(results[0], key=lambda x: x["score"])

            label_mapping = {
                "POSITIVE": "positive",
                "NEGATIVE": "negative",
                "NEUTRAL": "neutral",
            }

            sentiment = label_mapping.get(best_result["label"].upper(), "neutral")
            confidence = best_result["score"]

            return sentiment, confidence

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return "neutral", 0.0

    def process_comments(self):
        logger.info("Starting to process comments...")

        for message in self.consumer:
            try:
                comment_data = message.value

                sentiment, confidence = self.analyze_sentiment(comment_data["comment"])

                enriched_data = {
                    "id": f"{comment_data['username']}_{comment_data['timestamp']}",
                    "timestamp": comment_data["timestamp"],
                    "username": comment_data["username"],
                    "comment": comment_data["comment"],
                    "video_id": comment_data["video_id"],
                    "channel_name": comment_data["channel_name"],
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "processed_at": datetime.now().isoformat(),
                }

                self.producer.send(config.SENTIMENT_RESULTS_TOPIC, value=enriched_data)

                self.cache_sentiment_result(enriched_data)

                logger.info(
                    f"Processed comment: {sentiment} ({confidence:.2f}) - {comment_data['comment'][:50]}..."
                )

            except Exception as e:
                logger.error(f"Error processing comment: {e}")

    def parse_iso_timestamp(self, ts_str):
        try:
            if ts_str.endswith("Z"):
                ts_str = ts_str.replace("Z", "+00:00")
            return parse_date(ts_str).timestamp()
        except Exception as e:
            logger.error(f"Error parsing timestamp '{ts_str}': {e}")
            return datetime.now().timestamp()

    def cache_sentiment_result(self, data):
        try:
            key = f"{config.SENTIMENT_CACHE_KEY}:{data['id']}"
            self.redis_client.setex(key, config.CACHE_EXPIRY_SECONDS, json.dumps(data))

            timestamp = self.parse_iso_timestamp(data["timestamp"])
            self.redis_client.zadd(
                f"{config.SENTIMENT_CACHE_KEY}:timeline", {data["id"]: timestamp}
            )

            sentiment_key = f"{config.SENTIMENT_CACHE_KEY}:counts:{data['sentiment']}"
            self.redis_client.incr(sentiment_key)
            self.redis_client.expire(sentiment_key, config.CACHE_EXPIRY_SECONDS)
        except Exception as e:
            logger.error(f"Error caching sentiment result: {e}")


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    analyzer.process_comments()
