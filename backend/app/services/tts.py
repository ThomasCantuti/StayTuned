from app.services.llm import LLMService
import logging
import time
import torch
import numpy as np
import scipy.io.wavfile
import os
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
    
    def generate_audio(self, script: str) -> str:
        """Generate audio from the provided script and save it to a file."""
        logger.info(f"Moving model to {self.device}...")
        self.model.to(self.device)
        
        sampling_rate = self.model.generation_config.sample_rate

        lines = [line.strip() for line in script.strip().splitlines() if line.strip()]
        full_audio_pieces = []

        logger.info(f"Starting generation for {len(lines)} segments...")
        total_start_time = time.time()

        for i, line in enumerate(lines):
            logger.info(f"[{i+1}/{len(lines)}] Generating: {line[:50]}...")
            start_time = time.time()
            
            inputs = self.processor(
                text=[line],
                return_tensors="pt",
            )

            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            speech_values = self.model.generate(**inputs, do_sample=True)
            audio_segment = speech_values.cpu().float().numpy().squeeze()

            full_audio_pieces.append(audio_segment)
            
            logger.info("Time of generation: %.2f seconds" % (time.time() - start_time))

        final_audio = np.concatenate(full_audio_pieces)
        logger.info("Total time of generation: %.2f seconds" % (time.time() - total_start_time))

        max_val = np.abs(final_audio).max()
        if max_val > 0:
            final_audio = final_audio / max_val

        final_path = os.path.join(self.output_path, "bark_out_final.wav")
        scipy.io.wavfile.write(final_path, rate=sampling_rate, data=final_audio)
        logger.info(f"Audio saved to {final_path}.")
        self.llm_service.empty_tts_model_cache(self.model)
        return final_path