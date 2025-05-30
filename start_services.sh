#!/bin/bash

# Start all services for YouTube Live Stream Analytics

echo "🚀 Starting YouTube Live Stream Analytics System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start infrastructure services
echo "📦 Starting infrastructure services (Kafka, Redis, Storm)..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Create Kafka topics
echo "📡 Creating Kafka topics..."
docker exec -it $(docker-compose ps -q kafka) kafka-topics --create --topic raw-comments --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
docker exec -it $(docker-compose ps -q kafka) kafka-topics --create --topic sentiment-results --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1

echo "✅ Infrastructure services started successfully!"
echo ""
echo "📊 Services Status:"
echo "- Kafka: http://localhost:9092"
echo "- Redis: localhost:6379"
echo "- Storm UI: http://localhost:8080"
echo ""
echo "🚀 To start the application components, run:"
echo "1. python youtube_api.py          # YouTube comment ingestion"
echo "2. python sentiment_analyzer.py   # Sentiment analysis"
echo "3. python comment_summarizer.py   # Comment summarization"
echo "4. streamlit run dashboard.py     # Dashboard"
