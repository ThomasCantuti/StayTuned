from datapizza.clients.openai_like import OpenAILikeClient
from llama_cpp import Llama
from llama_cpp.llama_cpp import llama_backend_free
import torch
import gc
import platform


class LLMService:
    """Service for interacting and managing Large Language Models (LLMs)."""

    def get_model(self, model_path: str) -> Llama:
        return Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=0,
            verbose=True,
        )
    
    def get_client(self, model_name: str) -> OpenAILikeClient:
        """Creates and returns an OpenAI-like client for the LLM."""
        return OpenAILikeClient(
            api_key="",
            model=model_name,
            system_prompt="You are a helpful assistant.",
            base_url="http://localhost:8000/v1",
        )
    
    @staticmethod
    def empty_gpu_cache(model: Llama) -> None:
        """Clears the GPU cache to free up memory."""
        model.close()
        llama_backend_free()
        gc.collect()
        
        try:
            if platform.system() == "Darwin":
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as e:
            print(f"Error while emptying GPU cache: {e}")