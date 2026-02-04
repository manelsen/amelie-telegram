import io
import asyncio
from google import genai
from google.genai import types
from ports.interfaces import AIModelPort
from core.exceptions import transientAPIError, PermanentAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class GeminiAdapter(AIModelPort):
    """
    Adaptador para os modelos Google Gemini utilizando o SDK google-genai.
    
    Gerencia o ciclo de vida de arquivos na File API e a geração de conteúdo
    multimodal (imagem, vídeo, áudio e documentos). Implementa retentativas
    automáticas para resiliência de rede.
    """

    def __init__(self, api_key: str):
        """
        Inicializa o cliente do Google Gemini.

        Args:
            api_key (str): Chave de API válida do Google AI Studio.
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash-lite"

    async def upload_file(self, content_bytes: bytes, mime_type: str) -> str:
        """
        Faz upload do conteúdo para a File API do Google e aguarda o processamento 'ACTIVE'.

        Args:
            content_bytes (bytes): Conteúdo binário do arquivo.
            mime_type (str): Tipo MIME do arquivo (ex: 'video/mp4').

        Returns:
            str: URI do arquivo nos servidores do Google para uso em consultas.

        Raises:
            PermanentAPIError: Se o upload falhar ou o processamento remoto for negado.
        """
        try:
            file_io = io.BytesIO(content_bytes)
            
            # Realiza o upload assíncrono para a File API
            file_metadata = await self.client.aio.files.upload(file=file_io, config={"mime_type": mime_type})
            
            # Loop de polling para aguardar o estado ACTIVE (Google processando frames/audio)
            while True:
                f = await self.client.aio.files.get(name=file_metadata.name)
                if f.state.name == "ACTIVE":
                    break
                elif f.state.name == "FAILED":
                    raise PermanentAPIError("O processamento do arquivo falhou nos servidores do Google.")
                await asyncio.sleep(2)
            
            return file_metadata.uri
        except Exception as e:
            raise PermanentAPIError(f"Erro crítico no upload para a File API: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(transientAPIError),
        reraise=True
    )
    async def ask_about_file(self, file_uri: str, mime_type: str, prompt: str, history: list = None) -> str:
        """
        Solicita à IA uma análise sobre um arquivo referenciado via URI.

        Garante o envio do histórico de turnos para manter o contexto da conversa.
        Utiliza retentativas exponenciais para erros de rede ou limites de cota.

        Args:
            file_uri (str): URI do arquivo (geralmente gerada pelo método upload_file).
            mime_type (str): Tipo MIME do arquivo para orientação do modelo.
            prompt (str): A pergunta ou instrução atual do usuário.
            history (list, optional): Lista de dicionários {'role', 'parts'} do histórico.

        Returns:
            str: Resposta gerada pela IA em linguagem natural.

        Raises:
            transientAPIError: Erros temporários (HTTP 429, 500, timeouts).
            PermanentAPIError: Erros fatais (401 Unauthorized, 404 Not Found).
        """
        try:
            file_part = types.Part.from_uri(file_uri=file_uri, mime_type=mime_type)
            
            messages = []
            # Reconstrói o histórico para o formato esperado pelo SDK
            if history:
                for entry in history:
                    messages.append(types.Content(
                        role=entry["role"], 
                        parts=[types.Part.from_text(text=p) for p in entry["parts"]]
                    ))

            # Turno atual: Acopla o arquivo à instrução para garantir foco visual
            messages.append(types.Content(
                role="user", 
                parts=[file_part, types.Part.from_text(text=prompt)]
            ))
            
            # Chamada assíncrona para geração de conteúdo multimodal
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Seu nome é Amélie. Você é uma assistente de audiodescrição e análise "
                        "rigorosa para pessoas cegas. Responda sempre em português, texto puro, "
                        "sem markdown ou asteriscos. Foque nos detalhes visuais e contextuais."
                    )
                )
            )
            return response.text
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "rate limit" in err_str:
                raise transientAPIError(f"Limite de cota atingido: {e}")
            raise PermanentAPIError(f"Erro fatal na geração de conteúdo: {e}")

    async def delete_file(self, file_uri: str):
        """
        Remove permanentemente o arquivo do cache do provedor Google.

        Args:
            file_uri (str): URI completa do arquivo a ser deletado.
        """
        try:
            # Extrai o ID do arquivo (slug final da URI)
            file_id = file_uri.split('/')[-1]
            await self.client.aio.files.delete(name=file_id)
        except:
            pass # Silencia erros na deleção para evitar interrupção do fluxo principal
