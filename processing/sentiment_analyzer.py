from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from kafka import KafkaConsumer, KafkaProducer
from transformers import pipeline
from datetime import datetime
import logging
import torch
import redis
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from dateutil.parser import parse as parse_date
from database.mongodb_writer import write_to_mongodb_background

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    def __init__(self):
        logger.info("Loading sentiment analysis model...")
        if config.IS_INDONESIAN:
            model_name = config.INDONESIAN_SENTIMENT_MODEL
        else:   
            model_name = config.SENTIMENT_MODEL
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

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
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predictions = torch.argmax(probabilities, dim=-1)
            scores = torch.max(probabilities, dim=-1).values
            if config.IS_INDONESIAN:
                sentiment_map = {0: "positive", 1: "neutral", 2: "negative"}
            else:
                sentiment_map = {0: "negative",1: "negative",2: "neutral", 3: "positive",4: "positive"}
            pred = predictions.item()
            confidence = scores.item()
            return sentiment_map[pred], confidence
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
                    "id": comment_data["id"],
                    "timestamp": comment_data["timestamp"],
                    "username": comment_data["username"],
                    "comment": comment_data["comment"],
                    "video_id": comment_data["video_id"],
                    "sentiment": sentiment,
                    "confidence": confidence,
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
            self.redis_client.set(key, json.dumps(data))

            timestamp = self.parse_iso_timestamp(data["timestamp"])
            self.redis_client.zadd(
                f"{config.SENTIMENT_CACHE_KEY}:timeline", {data["id"]: timestamp}
            )

            sentiment_key = f"{config.SENTIMENT_CACHE_KEY}:counts:{data['sentiment']}"
            self.redis_client.incr(sentiment_key)

            logger.info(f"✅ Redis cache updated for comment: {data['id']}")

            write_to_mongodb_background(data, "comment")
            logger.info(f"📝 MongoDB write scheduled for comment: {data['id']}")

        except Exception as e:
            logger.error(f"Error caching sentiment result: {e}")


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    analyzer.process_comments()
