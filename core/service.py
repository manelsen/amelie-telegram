import re
from ports.interfaces import AIModelPort

class VisionService:
    def __init__(self, ai_model: AIModelPort):
        self.ai_model = ai_model

    def _clean_text_for_accessibility(self, text: str) -> str:
        # Remove asteriscos e outros caracteres de markdown
        text = text.replace("*", "")
        text = text.replace("#", "")
        text = text.replace("_", " ")
        text = text.replace("`", "")
        text = re.sub(r' +', ' ', text)
        return text.strip()

    async def process_file_request(self, content_bytes: bytes, mime_type: str) -> str:
        raw_result = await self.ai_model.process_content(content_bytes, mime_type)
        clean_result = self._clean_text_for_accessibility(raw_result)
        
        if mime_type.startswith("image/"):
            prefix = "Audiodescrição de imagem"
        elif mime_type.startswith("video/"):
            prefix = "Audiodescrição de vídeo"
        elif mime_type == "application/pdf":
            prefix = "Análise de PDF"
        elif "markdown" in mime_type or mime_type == "text/plain":
            prefix = "Análise de Documento"
        else:
            prefix = "Resultado"
            
        return f"{prefix}: {clean_result}"
