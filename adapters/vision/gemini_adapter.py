from google import genai
from google.genai import types
from ports.interfaces import VisionModelPort

class GeminiAdapter(VisionModelPort):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite"

    async def describe_image(self, image_bytes: bytes) -> str:
        prompt = "Descreva esta imagem detalhadamente para uma pessoa com deficiência visual (audiodescrição)."
        
        # Na biblioteca google-genai, imagens em bytes devem ser enviadas como Part
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        
        # Executa a chamada
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt, image_part]
        )
        return response.text
