from google import genai
from google.genai import types
from ports.interfaces import AIModelPort
from core.exceptions import transientAPIError, PermanentAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
    async def process_content(self, content_bytes: bytes, mime_type: str, prompt: str, history: list = None) -> str:
        try:
            content_part = types.Part.from_bytes(data=content_bytes, mime_type=mime_type)
            
            # Construindo o contexto: [ARQUIVO] + [HISTÓRICO] + [PERGUNTA ATUAL]
            # Isso é mais eficiente em tokens do que repetir o arquivo em cada turno
            messages = []
            
            # Adiciona o histórico
            if history:
                for entry in history:
                    role = entry["role"]
                    parts = [types.Part.from_text(text=p) for p in entry["parts"]]
                    messages.append(types.Content(role=role, parts=parts))

            # Adiciona o turno atual com o arquivo acoplado à pergunta do usuário
            current_parts = [content_part, types.Part.from_text(text=prompt)]
            messages.append(types.Content(role="user", parts=current_parts))
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction="Você é um assistente de audiodescrição e análise rigorosa para pessoas cegas. Responda em português, texto puro, sem markdown. Use o arquivo enviado como referência principal."
                )
            )
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "rate limit" in err_str:
                raise transientAPIError(f"Erro de cota: {e}")
            raise PermanentAPIError(f"Erro na API Gemini: {e}")
