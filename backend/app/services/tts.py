from app.services.llm import LLMService
import numpy as np
import os
import torch
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class TTSGeneratorService:
    """Service for generating podcast audio from a given script using Text-to-Speech."""
    
    def __init__(self):
        self.model_id = os.getenv("TTS_MODEL_ID")
        self.model_path = os.getenv("TTS_MODEL_PATH")
        self.output_path = os.getenv("PODCASTS_OUTPUT_PATH")
        self.llm_service = LLMService()
        self.processor, self.model, self.device = self.llm_service.get_tts_model(self.model_path)
    
    def generate_audio(self, script: str) -> np.ndarray:
        """Generate audio from the podcast script text."""
        inputs = self.processor(
            text=[script],
            voice_samples=[self.output_path + "/reference.wav"],
            return_tensors="pt",
            padding=True,
        )
        
        inputs = {key: val.to(self.device) if isinstance(val, torch.Tensor) else val for key, val in inputs.items()}

        output = self.model.generate(
            **inputs,
            tokenizer=self.processor.tokenizer,
            cfg_scale=1.3,
            max_new_tokens=None,
        )

        generated_speech = output.speech_outputs[0]
        processor_sampling_rate = self.processor.audio_processor.sampling_rate
        self.processor.save_audio(generated_speech, "generated_podcast_1.5B.wav", sampling_rate=processor_sampling_rate)

        logger.info("Audio saved to generated_podcast_1.5B.wav")
        