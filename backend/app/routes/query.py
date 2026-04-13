import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.query_engine import run_query
from app.models.schema import QueryResponse
from app.services.auth import verify_access_token
from app.core.logging_config import logger

router = APIRouter()

def get_current_user_id(token: str = Query(...)) -> str:
    """Extract and verify user ID from access token."""
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id

@router.get("/query", response_model=QueryResponse)
async def query(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(5, ge=1, le=20),
    intent_filter: str = Query(None),
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    user_id: str = Depends(get_current_user_id)
):
    """Query the memory system with cross-encoder re-ranking."""
    try:
        logger.info(f"Query from user {user_id}: {q[:50]}...")
        result = await run_query(
            user_id=user_id,
            query=q,
            limit=limit,
            intent_filter=intent_filter,
            min_importance=min_importance
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal query error")
