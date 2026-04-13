import os
import logging
from typing import Optional
from datetime import datetime

from app.models.memory import Memory
from app.services.transcription import transcribe
from app.services.embedding import get_embedding
from app.services.memory_store import store_memory
from app.services.importance import score_importance, categorize_importance
from app.services.speaker import identify_speakers, get_primary_speaker
from app.services.privacy import is_private
from app.services.memory_extractor import memory_extractor
from app.core.exceptions import TranscriptionError, EmbeddingError, MemoryStorageError
from app.core.logging_config import logger

async def process_audio(file_path: str, user_id: str) -> Optional[Memory]:
    """Process audio file through the complete pipeline with intelligent extraction."""
    try:
        # Check privacy mode
        if is_private():
            logger.info("Privacy mode enabled - skipping processing")
            return None
        
        # Transcribe audio
        logger.info(f"Transcribing audio: {file_path}")
        text = transcribe(file_path)
        
        # Skip if transcription is too short
        if len(text.strip()) < 5:
            logger.info("Skipping - transcription too short")
            return None
        
        logger.info(f"Transcribed: {text[:100]}...")
        
        # Intelligent memory extraction
        extraction_result = memory_extractor.extract_memory(text)
        cleaned_text = extraction_result['cleaned_text']
        intent = extraction_result['intent']
        entities = extraction_result['entities']
        summary = extraction_result['summary']
        has_correction = extraction_result['has_correction']
        importance_boost = extraction_result['importance_boost']
        
        # Identify speakers
        speakers = identify_speakers(file_path)
        primary_speaker = get_primary_speaker(speakers)
        
        # Score importance with boost
        base_importance = score_importance(cleaned_text)
        final_importance = min(base_importance + importance_boost, 1.0)
        importance_category = categorize_importance(final_importance)
        
        logger.info(f"Speaker: {primary_speaker}, Intent: {intent}, Importance: {final_importance:.2f} ({importance_category})")
        
        # Get embedding for cleaned text
        embedding = get_embedding(cleaned_text)
        if not embedding or all(v == 0 for v in embedding):
            raise EmbeddingError("Failed to generate valid embedding")
        
        # Create enhanced memory object
        memory = Memory(
            text=text,
            cleaned_text=cleaned_text,
            intent=intent,
            entities=entities,
            summary=summary,
            speaker=primary_speaker,
            importance=final_importance,
            tags=[importance_category] + ([intent] if intent else []),
            source="audio",
            audio_file=file_path,
            embedding=embedding,
            user_id=user_id,
            has_correction=has_correction,
            importance_boost=importance_boost,
            metadata={
                "speakers": speakers,
                "importance_category": importance_category,
                "extraction_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Store in memory
        memory_id = await store_memory(
            user_id=user_id,
            text=cleaned_text,
            metadata={
                "intent": intent,
                "speaker": primary_speaker,
                "importance": final_importance,
                "lifecycle": importance_category,
                "entities": entities,
                "summary": summary,
                "has_correction": has_correction,
                "importance_boost": importance_boost,
            }
        )
        memory.id = memory_id
        
        logger.info(f"Stored memory with importance {final_importance:.2f}")
        return memory
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        raise TranscriptionError(f"Failed to process audio: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
