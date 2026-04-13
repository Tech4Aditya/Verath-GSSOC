import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.services.embedding import get_embedding

logger = logging.getLogger(__name__)


# ── ChromaDB client (persistent, file-backed, concurrent-safe) ──────────────
_chroma_client = chromadb.PersistentClient(
    path=settings.vector_db_path,
    settings=ChromaSettings(anonymized_telemetry=False)
)


def _get_collection(user_id: str):
    """Return (or create) a per-user ChromaDB collection."""
    collection_name = f"user_{user_id.replace('-', '_')}"
    return _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


# ── MongoDB client ────────────────────────────────────────────────────────────
_mongo_client = AsyncIOMotorClient(settings.mongo_uri)
_db = _mongo_client[settings.database_name]


def _memories_collection():
    return _db["memories"]


# ── Write ─────────────────────────────────────────────────────────────────────
async def store_memory(
    user_id: str,
    text: str,
    metadata: Dict[str, Any]
) -> str:
    """
    Store a memory in both MongoDB (full document) and ChromaDB (vector + metadata).
    Returns the new memory's ID.
    """
    memory_id = str(uuid.uuid4())
    now = datetime.utcnow()

    # Sanitise metadata for ChromaDB — values must be str/int/float/bool
    chroma_meta = {
        "user_id": user_id,
        "intent": str(metadata.get("intent", "general")),
        "speaker": str(metadata.get("speaker", "unknown")),
        "importance": float(metadata.get("importance", 0.5)),
        "lifecycle": str(metadata.get("lifecycle", "short_term")),
        "timestamp": now.isoformat(),
    }

    # 1. Generate embedding
    embedding = get_embedding(text)

    # 2. Upsert into ChromaDB
    collection = _get_collection(user_id)
    collection.upsert(
        ids=[memory_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[chroma_meta],
    )

    # 3. Store full document in MongoDB
    mongo_doc = {
        "_id": memory_id,
        "user_id": user_id,
        "text": text,
        "metadata": metadata,
        "lifecycle": metadata.get("lifecycle", "short_term"),
        "created_at": now,
        "updated_at": now,
    }
    await _memories_collection().insert_one(mongo_doc)

    logger.info(f"Stored memory {memory_id} for user {user_id}")
    return memory_id


# ── Read / Search ─────────────────────────────────────────────────────────────
async def search_memories(
    user_id: str,
    query: str,
    limit: int = 5,
    intent_filter: Optional[str] = None,
    min_importance: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Vector similarity search with optional metadata filters.
    Returns a list of memory dicts sorted by relevance.
    """
    collection = _get_collection(user_id)
    query_embedding = get_embedding(query)

    # Build ChromaDB where clause
    where: Dict[str, Any] = {"user_id": user_id}
    if intent_filter:
        where["intent"] = intent_filter
    if min_importance > 0.0:
        where["importance"] = {"$gte": min_importance}

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(limit, collection.count()),
            where=where if len(where) > 1 else {"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return []

    memories = []
    if results and results["ids"]:
        for i, mem_id in enumerate(results["ids"][0]):
            memories.append({
                "id": mem_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # cosine → similarity
            })

    return memories


# ── Update lifecycle ──────────────────────────────────────────────────────────
async def update_memory_lifecycle(memory_id: str, user_id: str, new_lifecycle: str):
    """Promote or archive a memory by updating its lifecycle stage."""
    col = _memories_collection()
    await col.update_one(
        {"_id": memory_id},
        {"$set": {"lifecycle": new_lifecycle, "updated_at": datetime.utcnow()}}
    )

    collection = _get_collection(user_id)
    try:
        existing = collection.get(ids=[memory_id], include=["metadatas", "documents", "embeddings"])
        if existing["ids"]:
            meta = existing["metadatas"][0]
            meta["lifecycle"] = new_lifecycle
            collection.update(ids=[memory_id], metadatas=[meta])
    except Exception as e:
        logger.warning(f"ChromaDB lifecycle update failed for {memory_id}: {e}")


# ── Delete ────────────────────────────────────────────────────────────────────
async def delete_memory(memory_id: str, user_id: str):
    """Remove a memory from both stores."""
    await _memories_collection().delete_one({"_id": memory_id})
    collection = _get_collection(user_id)
    try:
        collection.delete(ids=[memory_id])
    except Exception as e:
        logger.warning(f"ChromaDB delete failed for {memory_id}: {e}")


# ── Stats ─────────────────────────────────────────────────────────────────────
async def get_memory_stats(user_id: str) -> Dict[str, Any]:
    col = _memories_collection()
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$lifecycle",
            "count": {"$sum": 1},
            "avg_importance": {"$avg": "$metadata.importance"},
        }}
    ]
    stats: Dict[str, Any] = {"short_term": 0, "long_term": 0, "archived": 0}
    async for doc in col.aggregate(pipeline):
        stats[doc["_id"]] = doc["count"]
    return stats


# ── Get all memories ───────────────────────────────────────────────────────────
async def all_memories(user_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
    """Get all memories for a user from MongoDB."""
    col = _memories_collection()
    cursor = col.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    memories = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["timestamp"] = doc.get("created_at", datetime.utcnow()).isoformat()
        memories.append(doc)
    return memories
