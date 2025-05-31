import os

# YouTube API Configuration
YOUTUBE_API_KEY = "AIzaSyBrFCli-COaOMMoKFkBIt1TuNNOdvqzlcU"
# YOUTUBE_API_KEY = "AIzaSyA-nKO01fRryKtTyhpuLjrAFD1TRTjCVzg"
VIDEO_ID = "QISzH1Pvttw"
CHANNEL_NAME = "IShowSpeed"

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
RAW_COMMENTS_TOPIC = "raw-comments"
CLEAN_COMMENTS_TOPIC = "clean-comments"
SENTIMENT_RESULTS_TOPIC = "sentiment-results"

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyAhb8kIfY6VGPbDq80oI-OoD688TGN0wOI"

# Model Configuration
SENTIMENT_MODEL = "tabularisai/multilingual-sentiment-analysis"

# Timing Configuration
SUMMARY_WINDOW_MINUTES = 3
CACHE_EXPIRY_SECONDS = 300

# Database Keys
SENTIMENT_CACHE_KEY = "sentiment_results"
SUMMARY_CACHE_KEY = "comment_summaries"
