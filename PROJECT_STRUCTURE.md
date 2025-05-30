# YouTube Live Stream Sentiment Analysis System

## 📁 Project Structure

```
BigData/
├── 📊 dashboard/              # Real-time visualization
│   ├── __init__.py
│   └── dashboard.py           # Streamlit dashboard
├── 🔧 config/                 # Configuration files
│   ├── __init__.py
│   └── config.py             # System configuration
├── 📥 ingestion/              # Data ingestion modules
│   ├── __init__.py
│   └── youtube_api.py        # YouTube API data fetching
├── ⚙️ processing/             # Data processing modules
│   ├── __init__.py
│   ├── sentiment_analyzer.py # Real-time sentiment analysis
│   └── comment_summarizer.py # Batch comment summarization
├── 🛠️ scripts/               # Utility scripts
│   ├── __init__.py
│   ├── restart_services.py   # Service management
│   └── system_status.py      # System monitoring
├── 🧪 tests/                  # Testing modules
│   ├── __init__.py
│   ├── test_system.py        # System component tests
│   └── test_data_flow.py     # End-to-end data flow tests
├── ⚡ storm/                  # Apache Storm configuration
│   └── conf/
│       └── storm.yaml
├── 🐳 docker-compose.yml      # Infrastructure services
├── 📋 requirements.txt        # Python dependencies
├── 🚀 start_system.py         # Main system launcher
├── 🧪 run_tests.py           # Test runner
└── 📖 README.md              # This file
```

## 🚀 Quick Start

### 1. Start Infrastructure Services
```bash
docker-compose up -d
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start All Services
```bash
python start_system.py
```

### 4. Access Dashboard
- **Main Dashboard**: http://localhost:8501
- **Storm UI**: http://localhost:8080

## 🧪 Testing

Run all tests:
```bash
python run_tests.py
```

Run specific test modules:
```bash
# System component tests
python tests/test_system.py

# Data flow tests
python tests/test_data_flow.py
```

## 📊 System Architecture

```
YouTube API → Kafka → raw-comments-topic
                ├─ Storm → Realtime Sentiment → Redis/DB
                └─ Kafka Streams → Tumbling Window (3 min) → Summary → Redis/DB
```

### Data Flow:
1. **YouTube API** fetches live comments → Kafka
2. **Sentiment Analyzer** processes comments in real-time
3. **Comment Summarizer** generates summaries every 3 minutes
4. **Dashboard** visualizes real-time metrics and summaries

## 🔧 Configuration

Edit `config/config.py` to:
- Set YouTube API key and video ID
- Configure Gemini API key for summarization
- Adjust processing parameters

## 📦 Services

| Service | Location | Description |
|---------|----------|-------------|
| YouTube API | `ingestion/youtube_api.py` | Fetches live stream comments |
| Sentiment Analyzer | `processing/sentiment_analyzer.py` | Real-time sentiment analysis |
| Comment Summarizer | `processing/comment_summarizer.py` | Batch summarization with Gemini |
| Dashboard | `dashboard/dashboard.py` | Streamlit visualization |

## 🛠️ Management Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| Start System | `start_system.py` | Launch all services |
| Restart Services | `scripts/restart_services.py` | Restart Python services |
| System Status | `scripts/system_status.py` | Check system health |
| Run Tests | `run_tests.py` | Execute test suite |

## 🐳 Infrastructure

- **Kafka**: Message streaming (port 9092)
- **Redis**: Caching and storage (port 6379)
- **Storm**: Real-time processing (UI on port 8080)
- **Zookeeper**: Kafka coordination (port 2181)

## 📈 Features

✅ Real-time sentiment analysis with multilingual support  
✅ Live comment ingestion from YouTube  
✅ Automated comment summarization every 3 minutes  
✅ Real-time dashboard with charts and metrics  
✅ Docker containerized infrastructure  
✅ Comprehensive testing suite  
✅ Modular, scalable architecture  

## 🔍 Monitoring

Use `python scripts/system_status.py` to check:
- Service health status
- Recent sentiment analysis results
- Comment summaries
- System performance metrics
