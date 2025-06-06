# YouTube API Configuration

YOUTUBE_API_KEY = "AIzaSyA-nKO01fRryKtTyhpuLjrAFD1TRTjCVzg"
# YOUTUBE_API_KEY = "AIzaSyBrFCli-COaOMMoKFkBIt1TuNNOdvqzlcU"
# YOUTUBE_API_KEY = "AIzaSyBUSqmcjVkT9xFprzMao8U_Q5215JnQR8o"
# YOUTUBE_API_KEY = "AIzaSyB0FjKXHdc53vjA4LFR_921ngDhUF-Q9b0"
# YOUTUBE_API_KEY = "AIzaSyDG3CDIL2jQQcquqTG-QSe5Dm6xrS0hVks"
# YOUTUBE_API_KEY = "AIzaSyDoMVREIBSPmZwKgFxDAQfvHBurQ6AUb1Y"
# YOUTUBE_API_KEY = "AIzaSyBT48ooU4fAYwgUREVe0IyXA4VL6n9QsNY"
# YOUTUBE_API_KEY = "AIzaSyDb4mmFfCigrnP1L5bcEMtfW1Qdh6UlOjw"

IS_INDONESIAN = True  # Set to True for Indonesian comments
VIDEO_ID = "0r_VwfKv6Cg"

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
RAW_COMMENTS_TOPIC = "raw-comments"
CLEAN_COMMENTS_TOPIC = "clean-comments"
SENTIMENT_RESULTS_TOPIC = "sentiment-results"

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# MongoDB Configuration
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017
MONGODB_USERNAME = "admin"
MONGODB_PASSWORD = "admin123"
MONGODB_DATABASE = "youtube_analytics"
MONGODB_CONNECTION_STRING = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin"

# Gemini API Configuration
GEMINI_API_KEY = "AIzaSyAhb8kIfY6VGPbDq80oI-OoD688TGN0wOI"

# Model Configuration
SENTIMENT_MODEL = "tabularisai/multilingual-sentiment-analysis"
# INDONESIAN_SENTIMENT_MODEL = "cahya/distilbert-base-indonesian"
INDONESIAN_SENTIMENT_MODEL = "indo-bert2"

# Timing Configuration
SUMMARY_WINDOW_MINUTES = 3

# Database Keys
SENTIMENT_CACHE_KEY = "sentiment_results"
SUMMARY_CACHE_KEY = "comment_summaries"
