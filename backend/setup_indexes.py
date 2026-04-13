"""
One-off script to create MongoDB indexes for the reminders system.
Run this once after deploying the reminder service.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def setup_reminder_indexes():
    """Create indexes for the alerts collection."""
    mongo = AsyncIOMotorClient(settings.mongo_uri)
    db = mongo[settings.database_name]
    alerts_col = db["alerts"]

    # Unique index for deduplication: memory_id + parsed_date
    await alerts_col.create_index(
        [("memory_id", 1), ("parsed_date", 1)],
        unique=True,
        name="unique_memory_date"
    )
    print("Created unique index on memory_id + parsed_date")

    # Index for querying upcoming reminders by user
    await alerts_col.create_index(
        [("user_id", 1), ("alerted_at", -1)],
        name="user_alerted_at"
    )
    print("Created index on user_id + alerted_at")

    # Index for due_in_minutes sorting
    await alerts_col.create_index([("due_in_minutes", 1)])
    print("Created index on due_in_minutes")

    print("All indexes created successfully!")


if __name__ == "__main__":
    asyncio.run(setup_reminder_indexes())
