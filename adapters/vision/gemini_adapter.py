import io
import asyncio
from google import genai
from google.genai import types
from ports.interfaces import AIModelPort
from core.exceptions import transientAPIError, PermanentAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class GeminiAdapter(AIModelPort):
    def __init__(self, api_key: str):
        # Usamos o cliente para chamadas síncronas e client.aio para assíncronas
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite"

    async def upload_file(self, content_bytes: bytes, mime_type: str) -> str:
        try:
            file_io = io.BytesIO(content_bytes)
            
            # Faz o upload usando o cliente assíncrono
            # O argumento correto para o conteúdo é 'file'
            file_metadata = await self.client.aio.files.upload(file=file_io, config={"mime_type": mime_type})
            
            # Aguarda o arquivo ficar 'ACTIVE' nos servidores do Google
            while True:
                f = await self.client.aio.files.get(name=file_metadata.name)
                if f.state.name == "ACTIVE":
                    break
                elif f.state.name == "FAILED":
                    raise PermanentAPIError("O processamento do arquivo falhou no Google.")
                await asyncio.sleep(2)
            
            # Retornamos a URI para referência futura
            return file_metadata.uri
        except Exception as e:
            raise PermanentAPIError(f"Erro no upload para a File API: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(transientAPIError),
        reraise=True
    )
    async def ask_about_file(self, file_uri: str, mime_type: str, prompt: str, history: list = None) -> str:
        try:
            # Segundo a documentação oficial do SDK google-genai:
            # O argumento correto é 'file_uri' e não 'uri'
            file_part = types.Part.from_uri(file_uri=file_uri, mime_type=mime_type)
            
            messages = []
            if history:
                for entry in history:
                    messages.append(types.Content(
                        role=entry["role"], 
                        parts=[types.Part.from_text(text=p) for p in entry["parts"]]
                    ))

            # Turno atual: Referência ao arquivo em cache + Pergunta
            messages.append(types.Content(
                role="user", 
                parts=[file_part, types.Part.from_text(text=prompt)]
            ))
            
            # Chamada assíncrona para geração de conteúdo
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction="Seu nome é Amélie. Você é uma assistente de audiodescrição e análise rigorosa para pessoas cegas. Responda sempre em português, texto puro, sem markdown ou asteriscos. Foque nos detalhes visuais do arquivo enviado."
                )
            )
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "rate limit" in err_str:
                raise transientAPIError(f"Erro de cota na API: {e}")
            raise PermanentAPIError(f"Erro na geração de conteúdo: {e}")

    async def delete_file(self, file_uri: str):
        try:
            # Extrai o ID do arquivo da URI (última parte da URL)
            file_id = file_uri.split('/')[-1]
            await self.client.aio.files.delete(name=file_id)
        except:
            pass # Silencia erros na deleção para não quebrar o fluxo principal
