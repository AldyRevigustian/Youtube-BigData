# Comment Cleaner Documentation

## Overview

Comment Cleaner adalah komponen baru dalam sistem YouTube Live Stream Analytics yang bertanggung jawab untuk membersihkan dan memfilter komentar sebelum diproses lebih lanjut.

## Fungsi Utama

### 1. Penghapusan Emoji
- Menghapus semua emoji dari teks komentar menggunakan library `emoji`
- Menggunakan regex pattern tambahan untuk emoji yang mungkin terlewat
- Mendukung berbagai jenis emoji: emoticons, symbols, pictographs, flags, dll.

### 2. Filtering Berdasarkan Panjang
- Memfilter komentar yang panjangnya kurang dari 10 karakter setelah dibersihkan
- Mencegah komentar yang hanya berisi emoji atau teks sangat pendek

### 3. Preservasi Data
- Mempertahankan semua field lain (timestamp, username, video_id, channel_name)
- Hanya mengubah field `comment` yang berisi teks komentar

## Alur Data

```
Raw Comments (with emojis) → Comment Cleaner → Clean Comments (emoji-free, filtered)
```

### Input (dari topic `raw-comments`):
```json
{
    "timestamp": "2024-01-01T10:00:00Z",
    "username": "User123",
    "comment": "Great stream! 😍💖✨",
    "video_id": "abc123",
    "channel_name": "Channel Name"
}
```

### Output (ke topic `clean-comments`):
```json
{
    "timestamp": "2024-01-01T10:00:00Z", 
    "username": "User123",
    "comment": "Great stream!",
    "video_id": "abc123",
    "channel_name": "Channel Name"
}
```

## Aturan Filtering

### ✅ Komentar yang LOLOS:
- Komentar dengan panjang ≥ 10 karakter setelah emoji dihapus
- Contoh: "Great stream! 😍" → "Great stream!" (12 karakter)

### ❌ Komentar yang DIFILTER:
- Komentar yang hanya berisi emoji: "😂😂😂" → "" (0 karakter)
- Komentar terlalu pendek: "nice 👍" → "nice" (4 karakter)
- Komentar kosong setelah dibersihkan

## Penggunaan

### 1. Standalone
```bash
python processing/comment_cleaner.py
```

### 2. Sebagai bagian dari sistem
```bash
# Start semua services
python start_system.py
# atau
.\start_system.ps1
```

## Testing

### 1. Test Sistem
```bash
python tests/test_system.py
```

### 2. Test Comment Cleaner Khusus
```bash
python tests/test_comment_cleaner.py
```

### 3. Demo Interactive
```bash
python scripts/demo_comment_cleaner.py
```

## Konfigurasi

File: `config/config.py`

```python
# Kafka Topics
RAW_COMMENTS_TOPIC = 'raw-comments'      # Input topic
CLEAN_COMMENTS_TOPIC = 'clean-comments'  # Output topic

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
```

## Dependencies

- `kafka-python`: Untuk Kafka consumer/producer
- `emoji`: Untuk penghapusan emoji yang robust
- `re`: Untuk regex pattern matching

## Monitoring

### Logs
Comment Cleaner menghasilkan log untuk:
- Komentar yang berhasil diproses
- Komentar yang difilter
- Statistik processing (setiap 10 komentar)
- Error handling

### Metrics
- Total komentar diproses
- Total komentar difilter
- Ratio filtering

## Error Handling

- Connection errors ke Kafka: Auto-retry
- Malformed JSON: Skip message dengan log error
- Processing errors: Log error, lanjutkan ke message berikutnya

## Performance

- Memory efficient: Stream processing tanpa buffer besar
- Low latency: Real-time processing
- Scalable: Dapat dijalankan multiple instance dengan consumer group

## Integration

Comment Cleaner terintegrasi dengan:
- **Input**: YouTube API → raw-comments topic
- **Output**: clean-comments topic → Sentiment Analyzer
- **Monitoring**: System status scripts
- **Testing**: Automated test suite

## Troubleshooting

### Common Issues:

1. **Kafka Connection Error**
   ```bash
   # Check Kafka status
   docker-compose ps
   docker-compose logs kafka
   ```

2. **No Messages Processed**
   - Pastikan topic `raw-comments` memiliki messages
   - Check consumer group status
   - Verify Kafka broker connectivity

3. **Emoji Not Removed**
   - Update emoji library: `pip install --upgrade emoji`
   - Check regex patterns

4. **High Memory Usage**
   - Monitor consumer lag
   - Consider increasing consumer instances

### Debug Mode:
```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
```

## Examples

### Input Examples:
```python
# Will be processed and pass filter
"This is an amazing stream! 😍💖✨"

# Will be processed but filtered (too short after cleaning)
"😂😂😂"

# Will pass through (no emojis, sufficient length)
"Great content, keep it up!"

# Will be filtered (too short)
"nice 👍"
```

### Output Examples:
```python
# From: "This is an amazing stream! 😍💖✨"
"This is an amazing stream!"

# From: "Great content, keep it up!"
"Great content, keep it up!"

# Filtered examples don't produce output
```
