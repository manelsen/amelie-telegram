import re
import logging
import asyncio
from typing import Dict, Any, Optional
from ports.interfaces import AIModelPort, SecurityPort, PersistencePort
from core.exceptions import transientAPIError, PermanentAPIError, NoContextError

# Configuração de logging profissional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

logger = logging.getLogger("VisionService")

class VisionService:
    def __init__(self, ai_model: AIModelPort, security: SecurityPort, persistence: PersistencePort):
        self.ai_model = ai_model
        self.security = security
        self.persistence = persistence
        self.queue = asyncio.Queue()
        self.worker_task = None

    def start_worker(self):
        if self.worker_task is None:
            logger.info("Iniciando worker blindado...")
            self.worker_task = asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            request = await self.queue.get()
            chat_id, func, args, future = request
            try:
                result = await func(*args)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self.queue.task_done()
                await asyncio.sleep(0.5)

    def _clean_text_for_accessibility(self, text: str) -> str:
        text = text.replace("*", "").replace("#", "").replace("_", " ").replace("`", "")
        text = re.sub(r' +', ' ', text)
        return text.strip()

    async def _enqueue_request(self, chat_id: str, func, *args):
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.queue.put((chat_id, func, args, future))
        return await future

    async def process_file_request(self, chat_id: str, content_bytes: bytes, mime_type: str) -> str:
        logger.info(f"Recebido. Tipo: {mime_type} | Chat: {chat_id}")
        
        # Busca sessão anterior para limpar cache do Google
        old_session = await self.persistence.get_session(chat_id)
        if old_session:
            # Descriptografa a URI antiga para deletar
            old_uri = self.security.decrypt(old_session["uri"])
            asyncio.create_task(self.ai_model.delete_file(old_uri))

        # 1. Faz upload e recebe URI limpa
        file_uri = await self._enqueue_request(chat_id, self.ai_model.upload_file, content_bytes, mime_type)
        
        # 2. CRIPTOGRAFA os dados sensíveis antes de salvar no banco
        encrypted_uri = self.security.encrypt(file_uri)
        
        new_session = {
            "uri": encrypted_uri,
            "mime": mime_type,
            "history": [] # Histórico será criptografado conforme cresce
        }
        await self.persistence.save_session(chat_id, new_session)
        
        # 3. Processamento inicial
        prompt = "Descreva este arquivo detalhadamente para um cego."
        return await self.process_question_request(chat_id, prompt)

    async def process_question_request(self, chat_id: str, question: str) -> str:
        session = await self.persistence.get_session(chat_id)
        if not session:
            raise NoContextError("Nenhum arquivo no cache.")
        
        # DESCRIPTOGRAFA para usar na IA
        real_uri = self.security.decrypt(session["uri"])
        
        # Descriptografa o histórico
        real_history = []
        for h in session.get("history", []):
            real_history.append({
                "role": h["role"],
                "parts": [self.security.decrypt(p) for p in h["parts"]]
            })

        logger.info(f"Processando pergunta contextual (Chat: {chat_id})")
        
        raw_result = await self._enqueue_request(
            chat_id, 
            self.ai_model.ask_about_file,
            real_uri, 
            session["mime"], 
            question,
            real_history
        )

        clean_result = self._clean_text_for_accessibility(raw_result)
        
        # CRIPTOGRAFA a nova interação antes de salvar
        new_history_entry_user = {"role": "user", "parts": [self.security.encrypt(question)]}
        new_history_entry_model = {"role": "model", "parts": [self.security.encrypt(clean_result)]}
        
        session["history"].append(new_history_entry_user)
        session["history"].append(new_history_entry_model)
        
        await self.persistence.save_session(chat_id, session)
        logger.info(f"Processado. Chat: {chat_id}")
        return clean_result
