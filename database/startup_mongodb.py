import asyncio
import logging
from database.mongodb_writer import mongodb_writer, initialize_mongodb
from config.config import VIDEO_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup_mongodb():
    try:
        logger.info("🚀 Starting MongoDB initialization...")
        await initialize_mongodb()
        if mongodb_writer.connected:
            logger.info("✅ MongoDB connection established")

            logger.info(f"📋 Collections will be created for video: {VIDEO_ID}")
            logger.info(f"   - {VIDEO_ID}_comments")
            logger.info(f"   - {VIDEO_ID}_summaries")
            logger.info("✅ MongoDB startup completed successfully")
            return True
        else:
            logger.error("❌ Failed to establish MongoDB connection")
            return False

    except Exception as e:
        logger.error(f"❌ MongoDB startup failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(startup_mongodb())
