from strands.models.llamacpp import LlamaCppModel
import logging

logger = logging.getLogger(__name__)

def get_model() -> LlamaCppModel:
    return LlamaCppModel(base_url="http://localhost:8080")
