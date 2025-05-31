# YouTube Live Stream Analytics

Real-time sentiment analysis dan comment summarization untuk YouTube live streaming menggunakan Apache Kafka, Redis, dan Streamlit.

## 🏗️ Arsitektur Sistem

```
YouTube API → Kafka Producer → raw-comments-topic
                     ↓
            Comment Cleaner → clean-comments-topic
                     ↓
         ┌─ Sentiment Analyzer → Redis Cache ─┐
         │                                    │→ Dashboard (Streamlit)
         └─ Comment Summarizer (3 min) ───────┘
```

## 📁 Struktur Project

```
BigData/
├── 📊 dashboard/              # Real-time visualization
│   ├── __init__.py
│   └── dashboard.py           # Streamlit dashboard utama
├── 🔧 config/                 # Configuration files
│   ├── __init__.py
│   └── config.py             # System configuration & API keys
├── 📥 ingestion/              # Data ingestion modules
│   ├── __init__.py
│   └── youtube_api.py        # YouTube API data fetching
├── ⚙️ processing/             # Data processing modules
│   ├── __init__.py
│   ├── comment_cleaner.py    # Comment cleaning dan filtering
│   ├── sentiment_analyzer.py # Real-time sentiment analysis
│   └── comment_summarizer.py # Batch comment summarization
├── 🛠️ scripts/               # Utility scripts
│   ├── __init__.py
│   ├── restart_services.py   # Service management
│   └── system_status.py      # System monitoring
├── 🧪 tests/                  # Testing modules
│   ├── __init__.py
│   ├── test_system.py        # System component tests
│   ├── test_data_flow.py     # End-to-end data flow tests
│   └── test_comment_cleaner.py # Comment cleaner unit tests
├── 🐳 docker-compose.yml      # Infrastructure services
├── 📋 requirements.txt        # Python dependencies
├── 🚀 start_services.py       # Infrastructure services launcher
├── 🚀 start_system.py         # Application services launcher
├── 🧪 start_tests.py          # Test suite runner
└── 📖 README.md              # This documentation
```

## 🔧 Komponen Utama

### 📥 **Data Ingestion**
- **YouTube API Integration**: Real-time comment fetching dari live streams
- **Kafka Producer**: Streaming data ke topics untuk processing

### ⚙️ **Data Processing**
- **Comment Cleaner**: Pembersihan emoji, normalisasi text, filtering spam
- **Sentiment Analyzer**: Analisis sentimen menggunakan model `tabularisai/multilingual-sentiment-analysis`
- **Comment Summarizer**: Ringkasan batch setiap 3 menit menggunakan Google Gemini 2.0 Flash

### 📊 **Data Storage & Caching**
- **Redis Cache**: Real-time storage untuk hasil sentiment dan summaries
- **Kafka Topics**: Stream processing untuk data flow

### 🖥️ **Visualization**
- **Streamlit Dashboard**: Real-time visualization dan monitoring
- **Interactive Charts**: Sentiment distribution, timeline, live feed

## 🚀 Quick Start Guide

### 1. Prerequisites

```bash
# Required Software
- Docker & Docker Compose
- Python 3.8+
- Git

# API Keys Required
- YouTube Data API v3 Key
- Google Gemini API Key
```

### 2. Clone & Setup

```bash
# Clone repository
git clone <your-repo-url>
cd BigData

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `config/config.py` dengan API keys Anda:

```python
# YouTube API Configuration
YOUTUBE_API_KEY = "your_youtube_api_key_here"
VIDEO_ID = "target_video_id"

# Gemini API Configuration  
GEMINI_API_KEY = "your_gemini_api_key_here"
```

### 4. Start Infrastructure Services

```bash
# Start Docker services (Kafka, Redis, Zookeeper)
python start_services.py
```

### 5. Start Application Services


```bash
# Start semua application services sekaligus
python start_system.py
```

**Services yang akan dijalankan:**
- ✅ YouTube Comment Ingestion
- ✅ Comment Cleaning & Filtering  
- ✅ Real-time Sentiment Analysis
- ✅ Comment Summarization (3-min batches)
- ✅ Streamlit Dashboard


## 🧪 Testing & Quality Assurance

### Complete Test Suite

```bash
# Run all tests
python start_tests.py
```

### Individual Test Categories

```bash
# System component tests
python tests/test_system.py

# End-to-end data flow tests  
python tests/test_data_flow.py

# Comment cleaner unit tests
python tests/test_comment_cleaner.py
```

### Test Coverage
- ✅ Kafka connectivity tests
- ✅ Redis connectivity tests  
- ✅ YouTube API integration tests
- ✅ Sentiment analysis pipeline tests
- ✅ Comment cleaning functionality tests
- ✅ End-to-end data flow validation

## 📊 Dashboard Features

**Access:** http://localhost:8501

### Real-time Metrics
- 📈 **Live Comment Feed**: Stream komentar real-time
- 📊 **Sentiment Distribution**: Pie chart positive/negative/neutral
- 📉 **Sentiment Timeline**: Trend sentimen over time
- 📝 **Comment Summaries**: Ringkasan AI setiap 3 menit
- 🔄 **Auto-refresh**: Data update otomatis setiap detik

### Interactive Features
- 🎯 **Filter by Sentiment**: Filter komentar berdasarkan sentimen
- 📅 **Time Range Selection**: Pilih periode waktu analisis
- 💾 **Export Data**: Download data untuk analisis lebih lanjut
- 🔍 **Search Comments**: Cari komentar spesifik

## 🔍 System Monitoring & Management

### Access Points
- 🎯 **Main Dashboard**: http://localhost:8501
- 📡 **Kafka**: localhost:9092
- 🗄️ **Redis**: localhost:6379

### Management Commands

```bash
# System status check
python scripts/system_status.py

# Restart semua application services
python scripts/restart_services.py

# Docker services management
docker-compose ps                    # Status check
docker-compose logs kafka            # Kafka logs
docker-compose logs redis            # Redis logs
docker-compose restart kafka         # Restart Kafka
```

### Health Monitoring

```bash
# Check Kafka topics
docker exec -it bigdata_kafka_1 kafka-topics.sh --list --bootstrap-server localhost:9092

# Check Redis data
docker exec -it bigdata_redis_1 redis-cli keys "*"

# Monitor system resources
docker stats
```

## 🛠️ Configuration Details

### Kafka Topics Configuration
```python
# Default Topics (auto-created)
RAW_COMMENTS_TOPIC = "raw-comments"        # Raw YouTube comments
CLEAN_COMMENTS_TOPIC = "clean-comments"    # Cleaned comments  
SENTIMENT_RESULTS_TOPIC = "sentiment-results" # Processed results
```

### Redis Key Structure
```python
# Sentiment Data
"sentiment_results:timeline"              # Timeline data
"sentiment_results:counts:positive"       # Positive count
"sentiment_results:counts:negative"       # Negative count  
"sentiment_results:counts:neutral"        # Neutral count

# Summary Data
"comment_summaries:timeline"              # Summary timeline
"comment_summaries:{timestamp}"           # Individual summaries
```

### Model Configuration
```python
# Sentiment Analysis Model
SENTIMENT_MODEL = "tabularisai/multilingual-sentiment-analysis"

# Summary Model  
GEMINI_MODEL = "gemini-2.0-flash-exp"

# Processing Windows
SUMMARY_WINDOW_MINUTES = 3               # Summary interval
SENTIMENT_BATCH_SIZE = 10                # Processing batch size
```

## 🔧 Customization Guide

### Mengubah Target Video

```python
# Edit config/config.py
VIDEO_ID = "new_video_id_here"
```

### Mengubah Summary Interval

```python
# Edit config/config.py  
SUMMARY_WINDOW_MINUTES = 5  # Change to 5 minutes
```

### Mengubah Sentiment Model

```python
# Edit config/config.py
SENTIMENT_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"
```