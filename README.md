# YouTube Live Stream Analytics

Real-time sentiment analysis dan comment summarization untuk YouTube live streaming menggunakan Apache Kafka, Storm, Redis, dan Streamlit.

## 🏗️ Arsitektur

```
YouTube API → Kafka → raw-comments-topic
├─ Comment Cleaner → clean-comments-topic
├─ Sentiment Analyzer → Redis Cache → Dashboard
└─ Comment Summarizer (3 min window) → Redis Cache → Dashboard
```

## 📁 Struktur Project

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
│   ├── comment_cleaner.py    # Comment cleaning and filtering
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
├── 🚀 start_system.py         # Main system launcher (Python)
├── 🚀 start_system.ps1        # Main system launcher (PowerShell)
├── 🧪 run_tests.py           # Test runner (Python)
├── 🧪 run_tests.ps1          # Test runner (PowerShell)
└── 📖 README.md              # This file
```

## 🔧 Komponen

- **YouTube API Ingestion**: Mengambil komentar live stream real-time
- **Comment Cleaner**: Membersihkan emoji dan memfilter komentar pendek
- **Sentiment Analysis**: Analisis sentimen menggunakan model `tabularisai/multilingual-sentiment-analysis`
- **Comment Summarization**: Ringkasan komentar setiap 3 menit menggunakan Gemini API
- **Real-time Dashboard**: Streamlit dashboard untuk visualisasi data

## 🚀 Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Python 3.8+
- YouTube API Key
- Google Gemini API Key

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuration

Update file `config/config.py` dengan API keys Anda:

```python
YOUTUBE_API_KEY = 'your_youtube_api_key'
GEMINI_API_KEY = 'your_gemini_api_key'
VIDEO_ID = 'your_video_id'
```

### 4. Start Infrastructure Services

#### Windows (PowerShell):
```powershell
.\start_services.ps1
```

#### Linux/Mac:
```bash
chmod +x start_services.sh
./start_services.sh
```

#### Manual:
```bash
docker-compose up -d
```

### 5. Start Application Services

#### 🚀 OPSI 1: Automatic Start (Recommended)

##### Windows PowerShell:
```powershell
.\start_system.ps1
```

##### Python Cross-platform:
```bash
python start_system.py
```

#### 🔧 OPSI 2: Manual Start (Individual Services)

Buka 4 terminal terpisah dan jalankan:

```bash
# Terminal 1 - YouTube Comment Ingestion
python ingestion/youtube_api.py

# Terminal 2 - Comment Cleaning
python processing/comment_cleaner.py

# Terminal 3 - Sentiment Analysis
python processing/sentiment_analyzer.py

# Terminal 4 - Comment Summarization
python processing/comment_summarizer.py

# Terminal 5 - Dashboard
streamlit run dashboard/dashboard.py
```

#### 🛠️ OPSI 3: Using Utility Scripts

```bash
# Restart services
python scripts/restart_services.py

# Check system status
python scripts/system_status.py
```

## 🧪 Testing

### Run Complete Test Suite

#### PowerShell:
```powershell
.\run_tests.ps1
```

#### Python:
```bash
python run_tests.py
```

### Run Individual Tests

```bash
# System component tests
python tests/test_system.py

# End-to-end data flow tests
python tests/test_data_flow.py
```

## 📊 Dashboard

Akses dashboard di: http://localhost:8501

Features:
- Real-time sentiment metrics
- Sentiment distribution chart
- Live comment feed
- Comment summaries (setiap 3 menit)
- Summary history

## 🔍 Monitoring & Management

### Access Points
- **Main Dashboard**: http://localhost:8501
- **Storm UI**: http://localhost:8080
- **Kafka**: localhost:9092
- **Redis**: localhost:6379

### System Management Commands

```bash
# Check system status
python scripts/system_status.py

# Restart all services
python scripts/restart_services.py

# Check Docker services
docker-compose ps

# View service logs
docker-compose logs kafka
docker-compose logs redis
```

## 📁 Detailed File Structure

## 📁 Detailed File Structure

```
BigData/
├── 📊 dashboard/
│   ├── __init__.py              # Module init
│   └── dashboard.py             # Streamlit real-time dashboard
├── 🔧 config/
│   ├── __init__.py              # Module init
│   └── config.py                # System configuration & API keys
├── 📥 ingestion/
│   ├── __init__.py              # Module init
│   └── youtube_api.py           # YouTube API comment fetching
├── ⚙️ processing/
│   ├── __init__.py              # Module init
│   ├── sentiment_analyzer.py   # Real-time sentiment analysis
│   └── comment_summarizer.py   # Batch summarization with Gemini
├── 🛠️ scripts/
│   ├── __init__.py              # Module init
│   ├── restart_services.py     # Service restart automation
│   └── system_status.py        # System health monitoring
├── 🧪 tests/
│   ├── __init__.py              # Module init
│   ├── test_system.py          # Component integration tests
│   └── test_data_flow.py       # End-to-end data flow tests
├── ⚡ storm/
│   └── conf/
│       └── storm.yaml           # Apache Storm configuration
├── 🐳 docker-compose.yml       # Infrastructure services definition
├── 📋 requirements.txt         # Python package dependencies
├── 🚀 start_system.py          # Python system launcher
├── 🚀 start_system.ps1         # PowerShell system launcher
├── 🧪 run_tests.py            # Python test runner
├── 🧪 run_tests.ps1           # PowerShell test runner
├── 🔧 start_services.ps1       # Infrastructure startup (Windows)
├── 🔧 start_services.sh        # Infrastructure startup (Unix)
└── 📖 README.md               # This documentation
```

## 🛠️ Configuration Details

### Kafka Topics
- `raw-comments`: Raw comments from YouTube API
- `clean-comments`: Cleaned comments (emoji removed, filtered by length)
- `sentiment-results`: Processed comments with sentiment analysis

### Redis Keys
- `sentiment_results:*`: Individual sentiment results
- `sentiment_results:timeline`: Timeline of comments
- `sentiment_results:counts:*`: Sentiment counters
- `comment_summaries:*`: Comment summaries
- `comment_summaries:timeline`: Summary timeline

### Model Information
- **Sentiment Model**: `tabularisai/multilingual-sentiment-analysis`
- **Summary Model**: Google Gemini 2.0 Flash

## 🔧 Customization

### Mengubah Window Summary
Edit `config/config.py`:
```python
SUMMARY_WINDOW_MINUTES = 5  # Ubah ke 5 menit
```

### Mengubah Model Sentiment
Edit `config/config.py`:
```python
SENTIMENT_MODEL = "your_preferred_model"
```

### Mengubah Video Target
Edit `config/config.py`:
```python
VIDEO_ID = 'new_video_id'
CHANNEL_NAME = "New Channel"
```

## 🐛 Troubleshooting

### Kafka Connection Issues
```bash
# Check Kafka status
docker-compose ps

# Check Kafka logs
docker-compose logs kafka
```

### Redis Connection Issues
```bash
# Test Redis connection
docker exec -it bigdata_redis_1 redis-cli ping
```

### Model Loading Issues
```bash
# Clear Hugging Face cache
rm -rf ~/.cache/huggingface/transformers/
```

### YouTube API Issues
- Pastikan API key valid dan memiliki quota
- Pastikan video sedang live streaming
- Check video ID format

## 📝 API Limits

- **YouTube API**: 10,000 units/day default
- **Gemini API**: Varies by plan
- **Sentiment Model**: No limits (local)

## 🚀 Deployment

### Production Considerations
1. Use environment variables for API keys
2. Set up proper logging
3. Implement error recovery
4. Scale Kafka partitions
5. Use Redis cluster for high availability

### Environment Variables (Production)
```bash
# Set environment variables
export YOUTUBE_API_KEY="your_youtube_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
export VIDEO_ID="your_video_id"
```

### Docker Production
```yaml
# Add to docker-compose.yml for production
services:
  app:
    build: .
    environment:
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
```

## 📋 System Commands Reference

### Infrastructure Management
```bash
# Start all infrastructure services
docker-compose up -d

# Stop all infrastructure services
docker-compose down

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Application Management
```bash
# Quick start (all services)
python start_system.py          # Python
.\start_system.ps1              # PowerShell

# System monitoring
python scripts/system_status.py

# Restart application services
python scripts/restart_services.py

# Run tests
python run_tests.py             # Python
.\run_tests.ps1                 # PowerShell
```

### Individual Service Management
```bash
# Start individual services
python ingestion/youtube_api.py
python processing/sentiment_analyzer.py
python processing/comment_summarizer.py
streamlit run dashboard/dashboard.py
```

## 🎯 Usage Workflow

1. **Setup**: Install dependencies dan konfigurasi API keys
2. **Infrastructure**: Start Docker services dengan `docker-compose up -d`
3. **Application**: Start application services dengan `.\start_system.ps1`
4. **Monitor**: Check dashboard di http://localhost:8501
5. **Test**: Run test suite dengan `.\run_tests.ps1`
6. **Manage**: Use utility scripts untuk monitoring dan restart

## 📧 Support

Untuk pertanyaan atau issues, silakan buat issue di repository ini.

## 📜 License

MIT License
