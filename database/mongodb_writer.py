import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import sys
import os
import threading
import pymongo

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import (
    MONGODB_CONNECTION_STRING, 
    MONGODB_DATABASE,
    VIDEO_ID
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBWriter:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self.retry_count = 3
        self.retry_delay = 5  
        
    async def connect(self):
        try:
            self.client = AsyncIOMotorClient(MONGODB_CONNECTION_STRING)
            
            await self.client.admin.command('ping')
            self.db = self.client[MONGODB_DATABASE]
            self.connected = True
            logger.info("✅ MongoDB connection established successfully")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("MongoDB connection closed")
    
    async def ensure_connection(self):
        if not self.connected:
            await self.connect()
        return self.connected
    
    async def write_comment_async(self, comment_data: Dict[str, Any]):
        if not await self.ensure_connection():
            logger.error("Cannot write to MongoDB - no connection")
            return False
            
        try:
            video_id = comment_data.get('video_id', VIDEO_ID)
            collection_name = f"{video_id}_comments"
            collection = self.db[collection_name]
            
            document = {
                **comment_data,
                'created_at': datetime.utcnow(),
            }
            
            result = await collection.insert_one(document)
            logger.info(f"✅ Comment written to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing comment to MongoDB: {e}")
            return False
    
    async def write_summary_async(self, summary_data: Dict[str, Any]):
        if not await self.ensure_connection():
            logger.error("Cannot write to MongoDB - no connection")
            return False
            
        try:
            video_id = summary_data.get('video_id', VIDEO_ID)
            collection_name = f"{video_id}_summaries"
            collection = self.db[collection_name]
            
            document = {
                **summary_data,
                'created_at': datetime.utcnow(),
            }
            
            result = await collection.insert_one(document)
            logger.info(f"✅ Summary written to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing summary to MongoDB: {e}")
            return False
    
    async def write_batch_async(self, data_batch: List[Dict[str, Any]], data_type: str):
        if not await self.ensure_connection():
            logger.error("Cannot write batch to MongoDB - no connection")
            return False
            
        try:
            video_id = data_batch[0].get('video_id', VIDEO_ID) if data_batch else VIDEO_ID
            
            if data_type == 'comments':
                collection_name = f"{video_id}_comments"
            elif data_type == 'summaries':
                collection_name = f"{video_id}_summaries"
            else:
                logger.error(f"Invalid data_type: {data_type}")
                return False
                
            collection = self.db[collection_name]
            
            documents = []
            for data in data_batch:
                document = {
                    **data,
                    'created_at': datetime.utcnow(),
                }
                documents.append(document)
            
            
            result = await collection.insert_many(documents)
            logger.info(f"✅ Batch written to MongoDB: {len(result.inserted_ids)} {data_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing batch to MongoDB: {e}")
            return False
    
    async def create_indexes(self):
        if not await self.ensure_connection():
            return False
            
        try:
            video_id = VIDEO_ID
            comments_collection = self.db[f"{video_id}_comments"]
            await comments_collection.create_index("timestamp")
            await comments_collection.create_index("sentiment")
            await comments_collection.create_index("video_id")
            await comments_collection.create_index([("timestamp", -1), ("sentiment", 1)])
            
            summaries_collection = self.db[f"{video_id}_summaries"]
            await summaries_collection.create_index("window_start")
            await summaries_collection.create_index("window_end")
            await summaries_collection.create_index("video_id")
            
            logger.info("✅ MongoDB indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
            return False

mongodb_writer = MongoDBWriter()

async def write_to_mongodb_async(data: Dict[str, Any], data_type: str = 'comment'):
    try:
        if data_type == 'comment':
            await mongodb_writer.write_comment_async(data)
        elif data_type == 'summary':
            await mongodb_writer.write_summary_async(data)
        else:
            logger.error(f"Unknown data_type: {data_type}")
    except Exception as e:
        logger.error(f"Error in write_to_mongodb_async: {e}")

def write_to_mongodb_background(data: Dict[str, Any], data_type: str = 'comment'):
    try:
        def run_sync_write():
            try:
                if data_type == 'comment':
                    sync_mongodb_writer.write_comment_sync(data)
                elif data_type == 'summary':
                    sync_mongodb_writer.write_summary_sync(data)
                else:
                    logger.error(f"Unknown data_type: {data_type}")
                    
            except Exception as e:
                logger.error(f"Error in background MongoDB write thread: {e}")
        
        thread = threading.Thread(target=run_sync_write, daemon=True)
        thread.start()
        
        logger.info(f"📝 MongoDB write scheduled for {data_type}")
        
    except Exception as e:
        logger.error(f"Error scheduling MongoDB write: {e}")


class SyncMongoDBWriter:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        
    def connect(self):
        try:
            self.client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
            
            self.client.admin.command('ping')
            self.db = self.client[MONGODB_DATABASE]
            self.connected = True
            logger.info("✅ Sync MongoDB connection established successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Sync MongoDB connection failed: {e}")
            self.connected = False
            return False
    
    def ensure_connection(self):
        if not self.connected:
            return self.connect()
        return True
    
    def write_comment_sync(self, comment_data: Dict[str, Any]):
        if not self.ensure_connection():
            logger.error("Cannot write to MongoDB - no connection")
            return False
            
        try:
            video_id = comment_data.get('video_id', VIDEO_ID)
            collection_name = f"{video_id}_comments"
            collection = self.db[collection_name]
            document = {
                **comment_data,
                'created_at': datetime.utcnow(),
            }
            
            result = collection.insert_one(document)
            logger.info(f"✅ Comment written to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing comment to MongoDB: {e}")
            return False
    
    def write_summary_sync(self, summary_data: Dict[str, Any]):
        if not self.ensure_connection():
            logger.error("Cannot write to MongoDB - no connection")
            return False
            
        try:
            video_id = summary_data.get('video_id', VIDEO_ID)
            collection_name = f"{video_id}_summaries"
            collection = self.db[collection_name]
            
            document = {
                **summary_data,
                'created_at': datetime.utcnow(),
            }
            
            result = collection.insert_one(document)
            logger.info(f"✅ Summary written to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error writing summary to MongoDB: {e}")
            return False


sync_mongodb_writer = SyncMongoDBWriter()


async def initialize_mongodb():
    await mongodb_writer.connect()
    await mongodb_writer.create_indexes()


try:
    sync_mongodb_writer.connect()
except Exception as e:
    logger.warning(f"⚠️ Could not initialize MongoDB on import: {e}")

if __name__ == "__main__":
    
    async def test_writer():
        await initialize_mongodb()
        
        test_comment = {
            'timestamp': datetime.utcnow().isoformat(),
            'username': 'test_user',
            'comment': 'Test comment for MongoDB',
            'video_id': VIDEO_ID,
            'sentiment': 'positive'
        }
        
        await write_to_mongodb_async(test_comment, 'comment')
        
        test_summary = {
            'window_start': datetime.utcnow().isoformat(),
            'window_end': datetime.utcnow().isoformat(),
            'video_id': VIDEO_ID,
            'summary': 'Test summary for MongoDB',
            'total_comments': 1,
            'sentiment_distribution': {'positive': 1, 'negative': 0, 'neutral': 0}
        }
        
        await write_to_mongodb_async(test_summary, 'summary')
        await mongodb_writer.disconnect()
    
    asyncio.run(test_writer())
