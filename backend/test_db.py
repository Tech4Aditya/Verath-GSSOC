import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def test_auth():
    print(f"Connecting to: {settings.mongo_uri}")
    client = AsyncIOMotorClient(settings.mongo_uri)
    db = client[settings.database_name]
    users_col = db["users"]
    
    # Check indexes
    indexes = await users_col.list_indexes().to_list(None)
    for idx in indexes:
        print(f"Index: {idx}")

if __name__ == "__main__":
    asyncio.run(test_auth())
