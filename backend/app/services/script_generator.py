from app.services.llm import LLMService
from llama_cpp import Llama
import os
from dotenv import load_dotenv

load_dotenv()


class ScriptGeneratorService:
    """Service for generating podcast scripts using a Large Language Model (LLM)."""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.model_path = os.getenv("TOOL_MODEL_PATH")
        
    def generate_podcast_script(self, duration: int, topic: str, news_content: str) -> str:
        """Genera uno script per podcast basato sul contenuto delle news."""
        model: Llama = self.llm_service.get_model(self.model_path)
        messages = [
            {"role": "system",
            "content": f"""
                You are a professional podcast host creating an engaging {duration}-minute episode about {topic}.

                Based on the following recent news articles, create a natural, conversational podcast script with **one person talking**, as if they are speaking directly to the audience.

                NEWS ARTICLES:
                {news_content}

                REQUIREMENTS:
                - Use a conversational, engaging tone
                - Include natural transitions and personal commentary
                - Include an introduction and conclusion
                - Optimize for text-to-speech:
                - No music cues, stage directions, or special characters
                - Natural pauses with commas and periods
                - Spell out numbers and abbreviations
                - Pronunciation should be clear and natural

                Generate the complete podcast script now:
            """}
        ]
        response = model.create_chat_completion(messages=messages)
        self.llm_service.empty_gpu_cache(model=model)
        return response["choices"][0]["message"]["content"].strip()