import redis
import json
import time
from kafka import KafkaProducer, KafkaConsumer
import config

def test_redis_connection():
    """Test Redis connection"""
    try:
        r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_kafka_connection():
    """Test Kafka connection"""
    try:
        # Test producer
        producer = KafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Send test message
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Test message from system check'
        }
        
        producer.send('test-topic', value=test_message)
        producer.flush()
        producer.close()
        
        print("✅ Kafka producer test successful")
        return True
        
    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False

def test_sentiment_model():
    """Test sentiment analysis model loading"""
    try:
        from transformers import pipeline
        
        print("📥 Loading sentiment analysis model...")
        sentiment_pipeline = pipeline(
            "sentiment-analysis", 
            model=config.SENTIMENT_MODEL,
            return_all_scores=True
        )
        
        # Test with sample text
        test_text = "Ini adalah komentar yang bagus sekali!"
        result = sentiment_pipeline(test_text)
        
        print(f"✅ Sentiment model test successful: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Sentiment model test failed: {e}")
        return False

def test_gemini_api():
    """Test Gemini API connection"""
    try:
        from google import genai
        
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents="Test connection"
        )
        
        print(f"✅ Gemini API test successful: {response.text[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running system tests...\n")
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Kafka Connection", test_kafka_connection), 
        ("Sentiment Model", test_sentiment_model),
        ("Gemini API", test_gemini_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    # Summary
    print("📊 Test Results Summary:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(tests)} tests")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! System is ready to run.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and services.")

if __name__ == "__main__":
    main()
