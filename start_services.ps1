# PowerShell script to start YouTube Live Stream Analytics System

Write-Host "🚀 Starting YouTube Live Stream Analytics System..." -ForegroundColor Green

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Start infrastructure services
Write-Host "📦 Starting infrastructure services (Kafka, Redis, Storm)..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Create Kafka topics
Write-Host "📡 Creating Kafka topics..." -ForegroundColor Yellow
$kafkaContainer = (docker-compose ps -q kafka)

if ($kafkaContainer) {
    docker exec $kafkaContainer kafka-topics --create --topic raw-comments --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
    docker exec $kafkaContainer kafka-topics --create --topic clean-comments --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
    docker exec $kafkaContainer kafka-topics --create --topic sentiment-results --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
}

Write-Host "✅ Infrastructure services started successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services Status:" -ForegroundColor Cyan
Write-Host "- Kafka: http://localhost:9092"
Write-Host "- Redis: localhost:6379"
Write-Host "- Storm UI: http://localhost:8080"
Write-Host ""
Write-Host "🚀 To start the application components, run:" -ForegroundColor Cyan
Write-Host "1. python youtube_api.py          # YouTube comment ingestion"
Write-Host "2. python sentiment_analyzer.py   # Sentiment analysis"
Write-Host "3. python comment_summarizer.py   # Comment summarization"
Write-Host "4. streamlit run dashboard.py     # Dashboard"
