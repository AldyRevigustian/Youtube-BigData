import json
import re
import logging
import emoji
from kafka import KafkaConsumer, KafkaProducer
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommentCleaner:
    def __init__(self):
        self.consumer = KafkaConsumer(
            config.RAW_COMMENTS_TOPIC,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="comment-cleaner",
        )

        self.producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

        logger.info("Comment Cleaner initialized successfully")

    def remove_emojis(self, text):
        text = re.sub(r":[a-zA-Z0-9_+\-]+:", "", text)
        cleaned_text = emoji.replace_emoji(text, replace="")

        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "\U0001f900-\U0001f9ff"
            "\U0001fa70-\U0001faff"
            "\U00002600-\U000026ff"
            "\U00002700-\U000027bf"
            "\U0001f018-\U0001f270"
            "\U0001f300-\U0001f6d0"
            "]+",
            flags=re.UNICODE,
        )

        cleaned_text = emoji_pattern.sub("", cleaned_text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        return cleaned_text

    def clean_comment(self, comment_data):
        try:
            cleaned_data = comment_data.copy()
            original_comment = comment_data.get("comment", "")
            cleaned_comment = self.remove_emojis(original_comment)
            cleaned_data["comment"] = cleaned_comment
            logger.debug(f"Original: {original_comment}")
            logger.debug(f"Cleaned: {cleaned_comment}")

            return cleaned_data

        except Exception as e:
            logger.error(f"Error cleaning comment: {e}")
            return None

    def is_valid_comment(self, cleaned_data):
        cleaned_comment = cleaned_data.get("comment", "")
        if len(cleaned_comment) < 10:
            return False
        return True

    def process_comments(self):
        logger.info("Starting comment cleaning process...")
        processed_count = 0
        filtered_count = 0
        for message in self.consumer:
            try:
                raw_comment_data = message.value
                cleaned_data = self.clean_comment(raw_comment_data)
                if cleaned_data is None:
                    continue
                if self.is_valid_comment(cleaned_data):
                    self.producer.send(config.CLEAN_COMMENTS_TOPIC, value=cleaned_data)
                    processed_count += 1
                    logger.info(f"Processed comment: {cleaned_data['comment'][:50]}...")
                else:
                    filtered_count += 1
                    logger.info(
                        f"Filtered out comment (too short): {cleaned_data['comment']}"
                    )
                if (processed_count + filtered_count) % 10 == 0:
                    logger.info(
                        f"Statistics - Processed: {processed_count}, Filtered: {filtered_count}"
                    )
            except Exception as e:
                logger.error(f"Error processing comment: {e}")


if __name__ == "__main__":
    cleaner = CommentCleaner()
    cleaner.process_comments()
