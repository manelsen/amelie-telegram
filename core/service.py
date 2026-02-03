import re
import logging
from ports.interfaces import AIModelPort
from core.exceptions import VisionBotError, transientAPIError, PermanentAPIError, NoContextError

# Configuração de logging profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True # Garante que as configurações sejam aplicadas
)

# Silenciar apenas as bibliotecas de rede externas
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("VisionService")

class VisionService:
    def __init__(self, ai_model: AIModelPort):
        self.ai_model = ai_model
        self.sessions = {}

    def _clean_text_for_accessibility(self, text: str) -> str:
        text = text.replace("*", "")
        text = text.replace("#", "")
        text = text.replace("_", " ")
        text = text.replace("`", "")
        text = re.sub(r' +', ' ', text)
        return text.strip()

    async def process_file_request(self, chat_id: str, content_bytes: bytes, mime_type: str) -> str:
        logger.info(f"Recebido. Tipo: {mime_type} | Chat: {chat_id}")
        
        self.sessions[chat_id] = {
            "bytes": content_bytes,
            "mime": mime_type,
            "history": []
        }
        
        if mime_type.startswith("image/"): prompt = "Descreva esta imagem para um cego."
        elif mime_type.startswith("video/"): prompt = "Descreva este vídeo cronologicamente para um cego."
        elif mime_type == "application/pdf": prompt = "Resuma este PDF de forma simples para um cego."
        else: prompt = "Analise este documento."

        result = await self._ask_ai(chat_id, prompt)
        logger.info(f"Processado. Tipo: {mime_type}")
        return result

    async def process_question_request(self, chat_id: str, question: str) -> str:
        if chat_id not in self.sessions:
            raise NoContextError("Nenhum arquivo enviado anteriormente.")
        
        logger.info(f"Processando pergunta contextual: '{question[:30]}...' | Chat: {chat_id}")
        result = await self._ask_ai(chat_id, question)
        logger.info(f"Resposta contextual enviada com sucesso para o chat {chat_id}")
        return result

    async def _ask_ai(self, chat_id: str, prompt: str) -> str:
        session = self.sessions[chat_id]
        try:
            full_prompt = f"{prompt}. Responda em português, texto puro, sem qualquer markdown ou asteriscos."
            raw_result = await self.ai_model.process_content(
                session["bytes"], 
                session["mime"], 
                full_prompt,
                session["history"]
            )
            clean_result = self._clean_text_for_accessibility(raw_result)
            session["history"].append({"role": "user", "parts": [prompt]})
            session["history"].append({"role": "model", "parts": [clean_result]})
            return clean_result
        except Exception as e:
            logger.error(f"Erro fatal na IA durante o processamento (Chat {chat_id}): {e}")
            raise e
