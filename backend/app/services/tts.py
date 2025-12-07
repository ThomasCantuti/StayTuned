from app.services.llm import LLMService
from scipy.io import wavfile
import numpy as np
import os
import torch
from dotenv import load_dotenv

load_dotenv()


class TTSGeneratorService:
    """Service for generating podcast audio from a given script using Text-to-Speech."""
    
    def __init__(self):
        self.model_path = os.getenv("TTS_MODEL_PATH")
        self.output_path = os.getenv("PODCASTS_OUTPUT_PATH")
        self.llm_service = LLMService()
        self.feature_extractor, self.model = self.llm_service.get_tts_model(self.model_path)
    
    def generate_audio(self, script: str) -> np.ndarray:
        """Generate audio from the podcast script text."""
        
        # Tokenize the text
        inputs = self.feature_extractor(text=script, return_tensors="pt")
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        if torch.mps.is_available():
            inputs = {k: v.to("mps") for k, v in inputs.items()}
        else:
            inputs = {k: v.cpu() for k, v in inputs.items()}
        
        # Generate the audio
        with torch.no_grad():
            output = self.model.generate(**inputs)
        
        # Extract the audio and save as WAV
        audio_array = output.cpu().numpy().squeeze()
        sample_rate = getattr(self.model.config, 'sample_rate', 22050)
        
        wavfile.write(self.output_path, sample_rate, audio_array)
        
        return audio_array
    
    def generate_audio_chunks(self, script: str, output_path: str, chunk_size: int = 500) -> str:
        """Generate audio by splitting the script into chunks for long texts."""
        import numpy as np
        
        # Split into sentences for more natural chunks
        sentences = script.replace('\n', ' ').split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Generate audio for each chunk
        audio_segments = []
        sample_rate = getattr(self.model.config, 'sample_rate', 22050)
        
        for chunk in chunks:
            inputs = self.feature_extractor(text=chunk, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                output = self.model.generate(**inputs)
            
            audio_segments.append(output.cpu().numpy().squeeze())
        
        # Concatenate all segments
        full_audio = np.concatenate(audio_segments)
        wavfile.write(output_path, sample_rate, full_audio)
        
        return output_path
