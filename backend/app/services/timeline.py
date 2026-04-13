import logging
from datetime import datetime, timedelta
from typing import List, Dict
from app.services.memory_store import all_memories
from app.core.logging_config import logger

async def get_today_timeline(user_id: str) -> List[Dict]:
    """Get timeline of memories from today."""
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        all_mems = await all_memories(user_id, limit=1000)
        today_memories = []
        
        for mem in all_mems:
            timestamp = mem.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except:
                        continue
                
                if timestamp >= today:
                    today_memories.append(mem)
        
        # Sort by timestamp
        today_memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return [
            {
                "time": _format_timestamp(mem.get('timestamp')),
                "timestamp": mem.get('timestamp').timestamp() if isinstance(mem.get('timestamp'), datetime) else 0,
                "text": mem.get('cleaned_text', mem.get('text', '')),
                "speaker": mem.get('speaker', 'unknown'),
                "importance": mem.get('importance', 0.5),
                "tags": mem.get('tags', []),
                "intent": mem.get('intent'),
                "id": str(mem.get('_id', idx))
            }
            for idx, mem in enumerate(today_memories)
        ]
    except Exception as e:
        logger.error(f"Error getting today's timeline: {e}", exc_info=True)
        return []

async def get_date_timeline(user_id: str, date_str: str) -> List[Dict]:
    """Get timeline for specific date (YYYY-MM-DD format)."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        start_time = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        all_mems = await all_memories(user_id, limit=1000)
        date_memories = []
        
        for mem in all_mems:
            timestamp = mem.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except:
                        continue
                
                if start_time <= timestamp < end_time:
                    date_memories.append(mem)
        
        # Sort by timestamp
        date_memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return [
            {
                "time": _format_timestamp(mem.get('timestamp')),
                "timestamp": mem.get('timestamp').timestamp() if isinstance(mem.get('timestamp'), datetime) else 0,
                "text": mem.get('cleaned_text', mem.get('text', '')),
                "speaker": mem.get('speaker', 'unknown'),
                "importance": mem.get('importance', 0.5),
                "tags": mem.get('tags', []),
                "intent": mem.get('intent'),
                "id": str(mem.get('_id', idx))
            }
            for idx, mem in enumerate(date_memories)
        ]
    except ValueError:
        logger.warning(f"Invalid date format: {date_str}")
        return []
    except Exception as e:
        logger.error(f"Error getting date timeline: {e}", exc_info=True)
        return []

async def get_recent_timeline(user_id: str, hours: int = 24) -> List[Dict]:
    """Get timeline from last N hours."""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        all_mems = await all_memories(user_id, limit=1000)
        recent_memories = []
        
        for mem in all_mems:
            timestamp = mem.get('timestamp')
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except:
                        continue
                
                if timestamp >= cutoff_time:
                    recent_memories.append(mem)
        
        # Sort by timestamp
        recent_memories.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return [
            {
                "time": _format_timestamp(mem.get('timestamp')),
                "timestamp": mem.get('timestamp').timestamp() if isinstance(mem.get('timestamp'), datetime) else 0,
                "text": mem.get('cleaned_text', mem.get('text', '')),
                "speaker": mem.get('speaker', 'unknown'),
                "importance": mem.get('importance', 0.5),
                "tags": mem.get('tags', []),
                "intent": mem.get('intent'),
                "id": str(mem.get('_id', idx))
            }
            for idx, mem in enumerate(recent_memories)
        ]
    except Exception as e:
        logger.error(f"Error getting recent timeline: {e}", exc_info=True)
        return []

def _format_timestamp(timestamp) -> str:
    """Format timestamp to readable time string."""
    if not timestamp:
        return "Unknown"
    
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return "Unknown"
    
    if isinstance(timestamp, datetime):
        return timestamp.strftime("%H:%M")
    
    return "Unknown"
