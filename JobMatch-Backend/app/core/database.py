from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
        db = client[settings.database_name]
        from app.core.indexes import create_indexes
        await create_indexes(db)
        print(f"[OK] Connected to MongoDB: {settings.database_name}")
    except Exception as e:
        print(f"[NOTICE] MongoDB connection notice: {e}")


async def close_db():
    global client
    if client:
        client.close()
        print("[INFO] MongoDB connection closed")



def get_db():
    return db