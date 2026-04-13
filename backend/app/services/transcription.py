import logging
from functools import lru_cache
from faster_whisper import WhisperModel
from app.config import settings

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    try:
        logger.info(f"Loading Whisper model '{settings.whisper_model}' on {settings.whisper_device} ({settings.whisper_compute_type})")
        return WhisperModel(
            settings.whisper_model, 
            device=settings.whisper_device, 
            compute_type=settings.whisper_compute_type
        )
    except Exception as e:
        logger.error(f"Failed to load Whisper model on {settings.whisper_device}: {e}")
        if settings.whisper_device != "cpu":
            logger.info("Retrying on CPU...")
            return WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
        raise


def transcribe(audio_path: str) -> str:
    try:
        model = get_model()
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        logger.info(f"Transcription complete. Language: {info.language} ({info.language_probability:.2f})")
        return text
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise
