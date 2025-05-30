import json
import redis
import schedule
import time
from kafka import KafkaConsumer
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from google import genai
import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommentSummarizer:
    def __init__(self):
        # Initialize Gemini client
        self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            decode_responses=True
        )
        
        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            config.SENTIMENT_RESULTS_TOPIC,
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='comment-summarizer'
        )
        
        # Store comments in memory for batch processing
        self.comment_buffer = []
        
        logger.info("Comment Summarizer initialized successfully")
    
    def collect_comments(self):
        """Collect comments for batch processing"""
        logger.info("Starting comment collection...")
        
        for message in self.consumer:
            try:
                comment_data = message.value
                self.comment_buffer.append(comment_data)
                
                # Log every 10 comments
                if len(self.comment_buffer) % 10 == 0:
                    logger.info(f"Collected {len(self.comment_buffer)} comments")
                    
            except Exception as e:
                logger.error(f"Error collecting comment: {e}")
    
    def generate_summary(self, comments):
        """Generate summary using Gemini API"""
        try:
            if not comments:
                return "No comments to summarize"
            
            # Prepare comments text
            comments_text = "\n".join([
                f"[{comment['sentiment'].upper()}] {comment['username']}: {comment['comment']}"
                for comment in comments
            ])
            
            # Create prompt for Gemini
            prompt = f"""
            Berikut adalah komentar-komentar dari live streaming YouTube dalam 5 menit terakhir:

            {comments_text}

            Buatkan ringkasan yang mencakup:
            1. Tema utama yang dibicarakan
            2. Sentimen umum penonton
            3. Pertanyaan atau permintaan utama
            4. Highlight menarik dari komentar

            Buat ringkasan dalam bahasa Indonesia, maksimal 200 kata.
            """
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def analyze_sentiment_distribution(self, comments):
        """Analyze sentiment distribution in comments"""
        sentiment_counts = defaultdict(int)
        total_confidence = defaultdict(list)
        
        for comment in comments:
            sentiment = comment['sentiment']
            confidence = comment['confidence']
            
            sentiment_counts[sentiment] += 1
            total_confidence[sentiment].append(confidence)
        
        # Calculate average confidence for each sentiment
        sentiment_stats = {}
        for sentiment, confidences in total_confidence.items():
            sentiment_stats[sentiment] = {
                'count': sentiment_counts[sentiment],
                'avg_confidence': sum(confidences) / len(confidences) if confidences else 0
            }
        
        return sentiment_stats
    
    def process_batch_summary(self):
        """Process and generate summary for collected comments"""
        if not self.comment_buffer:
            logger.info("No comments to process")
            return
        
        logger.info(f"Processing batch summary for {len(self.comment_buffer)} comments")
        
        try:
            # Generate summary
            summary = self.generate_summary(self.comment_buffer)
            
            # Analyze sentiment distribution
            sentiment_stats = self.analyze_sentiment_distribution(self.comment_buffer)
            
            # Create summary data
            summary_data = {
                'timestamp': datetime.now().isoformat(),
                'window_start': (datetime.now() - timedelta(minutes=config.SUMMARY_WINDOW_MINUTES)).isoformat(),
                'window_end': datetime.now().isoformat(),
                'total_comments': len(self.comment_buffer),
                'summary': summary,
                'sentiment_distribution': sentiment_stats,
                'video_id': config.VIDEO_ID,
                'channel_name': config.CHANNEL_NAME
            }
            
            # Cache summary in Redis
            self.cache_summary(summary_data)
            
            # Clear buffer
            self.comment_buffer.clear()
            
            logger.info("Batch summary processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing batch summary: {e}")
    
    def cache_summary(self, summary_data):
        """Cache summary in Redis"""
        try:
            # Store latest summary
            self.redis_client.setex(
                f"{config.SUMMARY_CACHE_KEY}:latest",
                config.CACHE_EXPIRY_SECONDS * 2,  # Keep summaries longer
                json.dumps(summary_data)
            )
            
            # Store in timeline
            timestamp = datetime.now().timestamp()
            summary_id = f"summary_{int(timestamp)}"
            
            self.redis_client.setex(
                f"{config.SUMMARY_CACHE_KEY}:{summary_id}",
                config.CACHE_EXPIRY_SECONDS * 2,
                json.dumps(summary_data)
            )
            
            # Add to sorted set for timeline queries
            self.redis_client.zadd(
                f"{config.SUMMARY_CACHE_KEY}:timeline", 
                {summary_id: timestamp}
            )
            
        except Exception as e:
            logger.error(f"Error caching summary: {e}")
    
    def schedule_summaries(self):
        """Schedule summary generation every 5 minutes"""
        schedule.every(config.SUMMARY_WINDOW_MINUTES).minutes.do(self.process_batch_summary)
        
        logger.info(f"Scheduled summaries every {config.SUMMARY_WINDOW_MINUTES} minutes")
        
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    import threading
    
    summarizer = CommentSummarizer()
    
    # Start comment collection in a separate thread
    collection_thread = threading.Thread(target=summarizer.collect_comments, daemon=True)
    collection_thread.start()
    
    # Start scheduling in main thread
    summarizer.schedule_summaries()
