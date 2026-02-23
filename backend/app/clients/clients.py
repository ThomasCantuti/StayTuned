from strands.models.llamacpp import LlamaCppModel
import logging

logger = logging.getLogger(__name__)

def get_model() -> LlamaCppModel:
    return LlamaCppModel(base_url="http://localhost:8080")

# def get_tts_model(model_path: str) -> tuple:
#     """Load the VibeVoice TTS model and processor via remote code."""
#     if torch.cuda.is_available():
#         device = "cuda"
#     elif torch.mps.is_available():
#         device = "mps"
#     else:
#         device = "cpu"
                
#     processor = AutoProcessor.from_pretrained(model_path, use_flash_attention_2=True)
#     model = AutoModel.from_pretrained(model_path)
    
#     return processor, model, device

# def empty_tts_model_cache(model) -> None:
#     """Clears the GPU cache to free up memory."""
#     device = model.device.type
#     model.to("cpu")
#     if device == "mps":
#         torch.mps.empty_cache()
#     elif device == "cuda":
#         torch.cuda.empty_cache()
#     gc.collect()

# def get_client(self, model_name: str, base_url: str) -> OpenAILikeClient:
#     """Creates and returns an OpenAI-like client for the LLM."""
#     return OpenAILikeClient(
#         api_key="",
#         model=model_name,
#         system_prompt="You are a helpful assistant.",
#         base_url=base_url,
#     )

# @staticmethod
# def empty_gpu_cache(model: Llama) -> None:
#     """Clears the GPU cache to free up memory."""
#     model.close()
#     llama_backend_free()
#     gc.collect()
    
#     if platform.system() == "Darwin":
#         torch.mps.empty_cache()
#     elif torch.cuda.is_available():
#         torch.cuda.empty_cache()
