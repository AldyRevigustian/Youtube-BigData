# YouTube Live Stream Analytics

Real-time sentiment analysis dan comment summarization untuk YouTube live streaming menggunakan Apache Kafka, Storm, Redis, dan Streamlit.

## 🏗️ Arsitektur

```
YouTube API → Kafka → raw-comments-topic
├─ Sentiment Analyzer → Redis Cache → Dashboard
└─ Comment Summarizer (5 min window) → Redis Cache → Dashboard
```

## 🔧 Komponen

- **YouTube API Ingestion**: Mengambil komentar live stream real-time
- **Sentiment Analysis**: Analisis sentimen menggunakan model `tabularisai/multilingual-sentiment-analysis`
- **Comment Summarization**: Ringkasan komentar setiap 5 menit menggunakan Gemini API
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

Update file `config.py` dengan API keys Anda:

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

### 5. Start Application Components

Buka 4 terminal terpisah dan jalankan:

```bash
# Terminal 1 - YouTube Comment Ingestion
python youtube_api.py

# Terminal 2 - Sentiment Analysis
python sentiment_analyzer.py

# Terminal 3 - Comment Summarization
python comment_summarizer.py

# Terminal 4 - Dashboard
streamlit run dashboard.py
```

## 📊 Dashboard

Akses dashboard di: http://localhost:8501

Features:
- Real-time sentiment metrics
- Sentiment distribution chart
- Live comment feed
- Comment summaries (setiap 5 menit)
- Summary history

## 🔍 Monitoring

- **Storm UI**: http://localhost:8080
- **Kafka**: localhost:9092
- **Redis**: localhost:6379

## 📁 File Structure

```
BigData/
├── config.py                 # Configuration file
├── youtube_api.py            # YouTube API ingestion
├── sentiment_analyzer.py     # Real-time sentiment analysis
├── comment_summarizer.py     # Batch comment summarization
├── gemini.py                # Gemini API wrapper
├── dashboard.py             # Streamlit dashboard
├── docker-compose.yml       # Infrastructure services
├── requirements.txt         # Python dependencies
├── start_services.ps1       # Windows startup script
├── start_services.sh        # Linux/Mac startup script
└── storm/
    └── conf/
        └── storm.yaml       # Storm configuration
```

## 🛠️ Configuration Details

### Kafka Topics
- `raw-comments`: Raw comments from YouTube API
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
Edit `config.py`:
```python
SUMMARY_WINDOW_MINUTES = 10  # Ubah ke 10 menit
```

### Mengubah Model Sentiment
Edit `config.py`:
```python
SENTIMENT_MODEL = "your_preferred_model"
```

### Mengubah Video Target
Edit `config.py`:
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

## 📧 Support

Untuk pertanyaan atau issues, silakan buat issue di repository ini.

## 📜 License

MIT License
