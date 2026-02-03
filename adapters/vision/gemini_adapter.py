from google import genai
from google.genai import types
from ports.interfaces import AIModelPort
from core.exceptions import transientAPIError, PermanentAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import google.api_core.exceptions

class GeminiAdapter(AIModelPort):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(transientAPIError),
        reraise=True
    )
    async def process_content(self, content_bytes: bytes, mime_type: str) -> str:
        # Define o prompt com base no tipo de arquivo
        if mime_type.startswith("image/"):
            prompt = (
                "Descreva esta imagem detalhadamente para uma pessoa com deficiência visual (audiodescrição). "
                "Use apenas texto puro, sem negrito, sem itálico e sem asteriscos. "
                "Responda obrigatoriamente em português brasileiro."
            )
        elif mime_type.startswith("video/"):
            prompt = (
                "Descreva o conteúdo deste vídeo detalhadamente para uma pessoa com deficiência visual (audiodescrição). "
                "Relate as ações, cenários e elementos visuais importantes de forma cronológica. "
                "Use apenas texto puro, sem negrito, sem itálico e sem asteriscos. "
                "Responda obrigatoriamente em português brasileiro."
            )
        elif mime_type == "application/pdf":
            prompt = (
                "Resuma o conteúdo deste PDF de forma clara e organizada. "
                "Use apenas texto simples, sem listas com asteriscos, sem negrito e sem qualquer formatação markdown. "
                "Responda obrigatoriamente em português brasileiro."
            )
        else:
            prompt = (
                "Analise este documento e descreva seu conteúdo. "
                "Use texto puro, sem formatação markdown e sem asteriscos. "
                "Responda obrigatoriamente em português brasileiro."
            )

        try:
            content_part = types.Part.from_bytes(data=content_bytes, mime_type=mime_type)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, content_part]
            )
            return response.text
        except Exception as e:
            # Mapeamento de erros do Google para nossas exceções de domínio
            err_str = str(e).lower()
            if "quota" in err_str or "rate limit" in err_str or "timeout" in err_str:
                raise transientAPIError(f"Erro temporário na API do Google: {e}")
            elif "key" in err_str or "auth" in err_str or "404" in err_str:
                raise PermanentAPIError(f"Erro fatal na configuração da API: {e}")
            else:
                raise PermanentAPIError(f"Erro desconhecido na API: {e}")
