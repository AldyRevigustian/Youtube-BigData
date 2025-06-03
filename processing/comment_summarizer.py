import json
import schedule
import time
from kafka import KafkaConsumer
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict
import logging
from google import genai
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from database.mongodb_writer import write_to_mongodb_background

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommentSummarizer:
    def __init__(self, max_retries=3, retry_delay=2):
        self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.consumer = KafkaConsumer(
            config.SENTIMENT_RESULTS_TOPIC,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="comment-summarizer",
        )
        self.comment_buffer = []
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logger.info("Comment Summarizer initialized successfully")

    def collect_comments(self):
        logger.info("Starting comment collection...")
        for message in self.consumer:
            try:
                comment_data = message.value
                self.comment_buffer.append(comment_data)
                if len(self.comment_buffer) % 10 == 0:
                    logger.info(f"Collected {len(self.comment_buffer)} comments")
            except Exception as e:
                logger.error(f"Error collecting comment: {e}")

    def generate_summary(self, comments):
        try:
            if not comments:
                return "No comments to summarize"

            stats = self._calculate_sentiment_stats(comments)

            comment_texts = [
                f"[{comment['sentiment'].upper()}] {comment['username']}: {comment['comment']}"
                for comment in comments
            ]

            return self._generate_gemini_summary(comment_texts, stats)

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"

    def analyze_sentiment_distribution(self, comments):
        sentiment_counts = defaultdict(int)
        total_confidence = defaultdict(list)

        for comment in comments:
            sentiment = comment["sentiment"]
            confidence = comment["confidence"]

            sentiment_counts[sentiment] += 1
            total_confidence[sentiment].append(confidence)

        sentiment_stats = {}
        for sentiment, confidences in total_confidence.items():
            sentiment_stats[sentiment] = {
                "count": sentiment_counts[sentiment],
                "avg_confidence": (
                    sum(confidences) / len(confidences) if confidences else 0
                ),
            }
        return sentiment_stats

    def process_batch_summary(self):
        if not self.comment_buffer:
            logger.info("No comments to process")
            return

        logger.info(f"Processing batch summary for {len(self.comment_buffer)} comments")
        try:
            summary = self.generate_summary(self.comment_buffer)
            sentiment_stats = self.analyze_sentiment_distribution(self.comment_buffer)
            summary_data = {
                "timestamp": datetime.now().isoformat(),
                "window_start": (
                    datetime.now() - timedelta(minutes=config.SUMMARY_WINDOW_MINUTES)
                ).isoformat(),
                "window_end": datetime.now().isoformat(),
                "total_comments": len(self.comment_buffer),
                "summary": summary,
                "sentiment_distribution": sentiment_stats,
                "video_id": config.VIDEO_ID,
            }
            self.save_to_mongodb(summary_data)
            self.comment_buffer.clear()

            logger.info("Batch summary processed successfully")

        except Exception as e:
            logger.error(f"Error processing batch summary: {e}")

    def save_to_mongodb(self, summary_data):
        try:
            write_to_mongodb_background(summary_data, "summary")
            logger.info(
                f"📝 MongoDB write scheduled for summary at {summary_data['timestamp']}"
            )

        except Exception as e:
            logger.error(f"Error saving summary to MongoDB: {e}")

    def schedule_summaries(self):
        schedule.every(config.SUMMARY_WINDOW_MINUTES).minutes.do(
            self.process_batch_summary
        )

        logger.info(
            f"Scheduled summaries every {config.SUMMARY_WINDOW_MINUTES} minutes"
        )

        while True:
            schedule.run_pending()
            time.sleep(1)

    def _calculate_sentiment_stats(self, comments):
        total = len(comments)
        if total == 0:
            return {
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "positive_pct": 0,
                "negative_pct": 0,
                "neutral_pct": 0,
            }

        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

        for comment in comments:
            sentiment = comment.get("sentiment", "neutral").lower()
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1

        return {
            "positive": sentiment_counts["positive"],
            "negative": sentiment_counts["negative"],
            "neutral": sentiment_counts["neutral"],
            "positive_pct": (sentiment_counts["positive"] / total) * 100,
            "negative_pct": (sentiment_counts["negative"] / total) * 100,
            "neutral_pct": (sentiment_counts["neutral"] / total) * 100,
        }

    def _generate_gemini_summary(self, comment_texts, stats):
        for attempt in range(self.max_retries):
            try:
                max_comments = 2000
                if len(comment_texts) > max_comments:
                    comment_texts = comment_texts[:max_comments]

                comments_str = "\n".join(comment_texts)

                prompt = f"""
Berikut ini adalah data hasil analisis komentar dari live streaming YouTube:

Statistik Sentimen:
- Positif: {stats['positive']} komentar ({stats.get('positive_pct', 0):.1f}%)
- Negatif: {stats['negative']} komentar ({stats.get('negative_pct', 0):.1f}%)
- Netral: {stats['neutral']} komentar ({stats.get('neutral_pct', 0):.1f}%)

Total komentar: {len(comment_texts)}

Komentar:
{comments_str}

Buatkan ringkasan dengan format teks naratif biasa (bukan poin-poin atau bullet list), tanpa menggunakan simbol seperti tanda bintang (*), tanda pagar (#), atau format markdown lainnya.

Struktur ringkasan harus mencakup lima aspek berikut ini:

1. Sentimen umum: Jelaskan apakah mayoritas komentar bersifat positif, negatif, atau netral.
2. Topik utama: Sebutkan topik atau isu yang paling banyak dibahas oleh penonton.
3. Komentar menarik: Soroti satu atau dua komentar yang dianggap paling menonjol atau penting.
4. Reaksi penonton: Jelaskan bagaimana audiens bereaksi terhadap konten secara umum.
5. Pola atau tren: Ungkapkan jika ada tren atau pola yang terlihat dari interaksi penonton, misalnya peningkatan komentar di momen tertentu.

Gunakan bahasa Indonesia yang lugas dan mudah dipahami. Panjang ringkasan maksimal 300 kata. Tulis ringkasan dengan gaya deskriptif yang konsisten dan rapi agar mudah dianalisis lebih lanjut.
"""

                response = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash", contents=prompt
                )

                if response and hasattr(response, "text"):
                    logger.info(f"Gemini API call successful on attempt {attempt + 1}")
                    return response.text.strip()
                else:
                    logger.warning(f"No valid response from Gemini API on attempt {attempt + 1}")
                    if attempt == self.max_retries - 1:
                        logger.error("All Gemini API attempts failed, using fallback summary")
                        return self._fallback_summary(stats)

            except genai.errors.ServerError as e:
                if "503" in str(e) and "overloaded" in str(e).lower():
                    logger.warning(f"Gemini API overloaded (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("Max retries reached for Gemini API, using fallback summary")
                        return self._fallback_summary(stats)
                else:
                    logger.error(f"Non-recoverable Gemini API error: {e}")
                    return self._fallback_summary(stats)
            except Exception as e:
                logger.error(f"Unexpected error calling Gemini API (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error("All attempts failed, using fallback summary")
                    return self._fallback_summary(stats)
                else:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        return self._fallback_summary(stats)

    def _fallback_summary(self, stats):
        total_comments = stats["positive"] + stats["negative"] + stats["neutral"]

        if total_comments == 0:
            return "Tidak ada komentar untuk diringkas dalam periode ini."
        
        dominant_sentiment = "netral"
        max_count = stats["neutral"]

        if stats["positive"] > max_count:
            dominant_sentiment = "positif"
            max_count = stats["positive"]
        elif stats["negative"] > max_count:
            dominant_sentiment = "negatif"
            max_count = stats["negative"]

        summary = f"""
RINGKASAN KOMENTAR LIVE STREAMING

📊 Statistik Sentimen:
• Positif: {stats['positive']} komentar ({stats['positive_pct']:.1f}%)
• Negatif: {stats['negative']} komentar ({stats['negative_pct']:.1f}%)
• Netral: {stats['neutral']} komentar ({stats['neutral_pct']:.1f}%)

🎯 Analisis Umum:
Dari total {total_comments} komentar yang dianalisis, sentimen {dominant_sentiment} mendominasi dengan {max_count} komentar ({(max_count/total_comments)*100:.1f}%).

💡 Insight:
Penonton menunjukkan reaksi yang {dominant_sentiment} terhadap konten live streaming ini. 
Tingkat engagement cukup {'tinggi' if total_comments > 50 else 'sedang'} dengan {total_comments} interaksi.

*Ringkasan ini dibuat secara otomatis karena layanan AI sedang tidak tersedia.*
"""
        return summary.strip()


if __name__ == "__main__":
    import threading
    summarizer = CommentSummarizer(max_retries=3, retry_delay=2)

    collection_thread = threading.Thread(
        target=summarizer.collect_comments, daemon=True
    )
    collection_thread.start()

    summarizer.schedule_summaries()