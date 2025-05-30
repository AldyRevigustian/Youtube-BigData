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

    def remove_repeated_characters(self, text, max_repeats=2):
        pattern = r"(.)\1{" + str(max_repeats) + ",}"
        def replace_func(match):
            char = match.group(1)
            return char * max_repeats

        cleaned_text = re.sub(pattern, replace_func, text)
        return cleaned_text

    def remove_excessive_caps(self, text, threshold=0.7):
        if len(text) < 3:
            return text

        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text)

        if caps_ratio > threshold:
            return text.capitalize()

        return text

    def remove_special_patterns(self, text):
        text = re.sub(r"[!]{3,}", "!", text)
        text = re.sub(r"[?]{3,}", "?", text)
        text = re.sub(r"[.]{3,}", "...", text)

        text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]", "", text)
        text = re.sub(r"\b\d{8,}\b", "", text)
        text = re.sub(r"[~`@#$%^&*()+=\[\]{}|;:,.<>?/]{3,}", "", text)

        return text

    def remove_spam_patterns(self, text):
        spam_patterns = [
            r"\b(first|pertama|1st)\b",
            r"\b(early|early gang)\b",
            r"\b(pin|pinned?)\s*(comment|me|this)\b",
            r"\b(like|love)\s*(if|for)\b",
            r"\b(subscribe|sub)\s*(for|to|me)\b",
            r"\b(check\s*out|visit)\s*(my|our)\s*(channel|page)\b",
            r"\b(free|gratis)\s*(money|uang|bitcoin)\b",
        ]

        for pattern in spam_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    def remove_currency_spam(self, text):
        currency_patterns = [
            r"\$\d+",
            r"rp\.?\s*\d+",
            r"\d+k?\s*(dollar|usd|rupiah)",
            r"\b(bitcoin|btc|crypto|nft)\b",
            r"\b(cashapp|paypal|gopay|ovo|dana)\b",
        ]

        for pattern in currency_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    def remove_superchat_elements(self, text):
        text = re.sub(r"^[\$€£¥₹₽₩]+\s*\d*\.?\d*\s*", "", text)
        text = re.sub(r"(@\w+\s*){2,}", "", text)

        return text

    def remove_mentions_hashtags_links(self, text):
        text = re.sub(r"@[A-Za-z0-9_]+", "", text)
        text = re.sub(r"#[A-Za-z0-9_]+", "", text)
        text = re.sub(r"http[s]?\S+", "", text)
        text = re.sub(r"www\.\S+", "", text)

        return text

    def normalize_whitespace(self, text):
        text = re.sub(r"\s+", " ", text)
        return text.strip()

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
        return cleaned_text

    def clean_comment(self, comment_data):
        try:
            cleaned_data = comment_data.copy()
            original_comment = comment_data.get("comment", "")
            cleaned_comment = original_comment
            cleaned_comment = self.remove_mentions_hashtags_links(cleaned_comment)
            cleaned_comment = self.remove_superchat_elements(cleaned_comment)
            cleaned_comment = self.remove_spam_patterns(cleaned_comment)
            cleaned_comment = self.remove_currency_spam(cleaned_comment)
            cleaned_comment = self.remove_special_patterns(cleaned_comment)
            cleaned_comment = self.remove_emojis(cleaned_comment)
            cleaned_comment = self.remove_repeated_characters(cleaned_comment)
            cleaned_comment = self.remove_excessive_caps(cleaned_comment)
            cleaned_comment = self.normalize_whitespace(cleaned_comment)
            cleaned_data["comment"] = cleaned_comment

            logger.debug(f"Original: {original_comment}")
            logger.debug(f"Cleaned: {cleaned_comment}")

            return cleaned_data

        except Exception as e:
            logger.error(f"Error cleaning comment: {e}")
            return None

    def is_valid_comment(self, cleaned_data):
        cleaned_comment = cleaned_data.get("comment", "")
        username = cleaned_data.get("username", "").lower()

        bot_usernames = [
            "nightbot",
            "streamlabs",
            "streamelements",
            "moobot",
            "fossabot",
        ]
        if username in bot_usernames:
            logger.debug(f"Filtered bot comment from: {username}")
            return False

        if len(cleaned_comment) < 10:
            return False

        if len(set(cleaned_comment.replace(" ", ""))) < 2:
            return False

        if cleaned_comment.replace(" ", "").isdigit():
            return False

        special_chars = sum(1 for c in cleaned_comment if not c.isalnum() and c != " ")
        if len(cleaned_comment) > 0 and special_chars / len(cleaned_comment) > 0.7:
            return False

        return True

    def process_comments(self):
        logger.info("Starting comment cleaning process...")
        processed_count = 0
        filtered_count = 0

        try:
            for message in self.consumer:
                try:
                    raw_comment_data = message.value
                    cleaned_data = self.clean_comment(raw_comment_data)

                    if cleaned_data is None:
                        continue

                    if self.is_valid_comment(cleaned_data):
                        self.producer.send(
                            config.CLEAN_COMMENTS_TOPIC, value=cleaned_data
                        )
                        processed_count += 1
                        logger.info(
                            f"Processed comment: {cleaned_data['comment'][:50]}..."
                        )
                    else:
                        filtered_count += 1
                        logger.info(f"Filtered out comment: {cleaned_data['comment']}")

                    if (processed_count + filtered_count) % 10 == 0:
                        logger.info(
                            f"Statistics - Processed: {processed_count}, Filtered: {filtered_count}"
                        )

                except Exception as e:
                    logger.error(f"Error processing comment: {e}")

        except KeyboardInterrupt:
            logger.info("Shutdown signal received, stopping gracefully...")
        finally:
            self.consumer.close()
            self.producer.close()


if __name__ == "__main__":
    cleaner = CommentCleaner()
    cleaner.process_comments()
