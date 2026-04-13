import logging
from typing import List
import ollama
from app.config import settings

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> List[float]:
    """Generate a vector embedding for a given text string using Ollama."""
    try:
        response = ollama.embeddings(
            model=settings.embed_model,
            prompt=text
        )
        return response["embedding"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise
