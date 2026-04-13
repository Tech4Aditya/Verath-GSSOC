import logging
from fastapi import APIRouter, Depends, HTTPException
from app.models.schema import RecordRequest
from app.services.audio import record_audio
from app.services.pipeline import process_audio
from app.services.auth import get_current_user_id
from app.core.exceptions import TranscriptionError, MemoryStorageError
from app.core.logging_config import logger

router = APIRouter()

@router.post("/record")
async def record(payload: RecordRequest, user_id: str = Depends(get_current_user_id)):
    """Record audio and process it through the intelligent extraction pipeline."""
    try:
        logger.info(f"Recording audio for user {user_id}")
        file_path = record_audio(filename=payload.filename, duration=payload.duration)
        memory = await process_audio(file_path, user_id)
        
        return {
            "success": memory is not None,
            "memory": memory,
            "message": "Audio processed successfully" if memory else "Processing failed"
        }
    except TranscriptionError as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except MemoryStorageError as e:
        logger.error(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in record: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal processing error")
