import logging
from fastapi import APIRouter, Depends
from app.services.summarizer import generate_daily_summary, extract_key_insights
from app.services.timeline import get_today_timeline
from app.services.memory_store import get_memory_stats
from app.services.auth import get_current_user_id
from app.core.logging_config import logger

router = APIRouter()

@router.get("/summary")
async def summary(user_id: str = Depends(get_current_user_id)):
    """Generate daily summary of memories."""
    try:
        logger.info(f"Generating summary for user {user_id}")
        summary_text = await generate_daily_summary(user_id)
        return {"summary": summary_text}
    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        return {"summary": "Unable to generate summary at this time."}

@router.get("/timeline")
async def timeline(user_id: str = Depends(get_current_user_id)):
    """Get today's timeline of memories."""
    try:
        logger.info(f"Getting timeline for user {user_id}")
        timeline_data = await get_today_timeline(user_id)
        return {"timeline": timeline_data}
    except Exception as e:
        logger.error(f"Error getting timeline: {e}", exc_info=True)
        return {"timeline": []}

@router.get("/insights")
async def insights(user_id: str = Depends(get_current_user_id)):
    """Extract key insights from memories."""
    try:
        logger.info(f"Extracting insights for user {user_id}")
        insights_data = await extract_key_insights(user_id)
        return {"insights": insights_data}
    except Exception as e:
        logger.error(f"Error extracting insights: {e}", exc_info=True)
        return {"insights": []}

@router.get("/statistics")
async def statistics(user_id: str = Depends(get_current_user_id)):
    """Get memory statistics."""
    try:
        logger.info(f"Getting statistics for user {user_id}")
        stats = await get_memory_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return {"total": 0, "by_intent": {}, "by_speaker": {}, "avg_importance": 0.0, "recent_count": 0}
