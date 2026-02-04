import re
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from ports.interfaces import AIModelPort, SecurityPort, PersistencePort
from core.exceptions import VisionBotError, transientAPIError, PermanentAPIError, NoContextError

# Configuração de logging profissional global para a Amélie
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
# Silenciamento de logs de infraestrutura para evitar poluição visual
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("VisionService")

class VisionService:
    """
    Cérebro central da aplicação Amélie (Core Domain Service).
    
    Orquestra o processamento multimodal, gerencia filas de mensagens, 
    garante a acessibilidade via limpeza de texto, controla timeouts de sessão 
    e aplica a blindagem criptográfica AES-256.
    """

    def __init__(self, ai_model: AIModelPort, security: SecurityPort, persistence: PersistencePort):
        """
        Inicializa o serviço core com os adaptadores necessários.

        Args:
            ai_model (AIModelPort): Adaptador para comunicação com a IA.
            security (SecurityPort): Adaptador de criptografia e proteção de dados.
            persistence (PersistencePort): Adaptador de armazenamento persistente.
        """
        self.ai_model = ai_model
        self.security = security
        self.persistence = persistence
        self.queue = asyncio.Queue()
        self.worker_task = None
        # Tempo limite de inatividade (180 segundos)
        self.SESSION_TIMEOUT_SECONDS = 180

    def start_worker(self):
        """
        Inicia o Worker de processamento serializado no loop de eventos.
        
        Utiliza o padrão Lazy Initialization para garantir que o loop 
        esteja rodando no momento da criação da task.
        """
        if self.worker_task is None:
            logger.info("Worker blindado da Amélie iniciado com sucesso.")
            self.worker_task = asyncio.create_task(self._worker())

    async def _worker(self):
        """
        Worker em background que processa a fila global.
        
        Garante a serialização dos pedidos para evitar estouro de cota nas APIs
        e coordena o tempo de resposta do sistema.
        """
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
                # Pausa estratégica para respeitar limites de cota
                await asyncio.sleep(0.5)

    def _clean_text_for_accessibility(self, text: str) -> str:
        """
        Sanitiza o texto removendo caracteres especiais de Markdown.

        Args:
            text (str): Texto bruto gerado pela IA.

        Returns:
            str: Texto limpo, amigável para softwares leitores de tela.
        """
        text = text.replace("*", "").replace("#", "").replace("_", " ").replace("`", "")
        text = re.sub(r' +', ' ', text)
        return text.strip()

    async def _enqueue_request(self, chat_id: str, func, *args):
        """
        Adiciona uma requisição à fila global e aguarda a conclusão.

        Args:
            chat_id (str): ID do chat solicitante.
            func: Função do adaptador a ser executada.
            *args: Argumentos da função.

        Returns:
            Any: O resultado da função executada pelo worker.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        await self.queue.put((chat_id, func, args, future))
        return await future

    async def process_file_request(self, chat_id: str, content_bytes: bytes, mime_type: str) -> str:
        """
        Coordena o processamento inicial de um novo arquivo.

        Realiza o upload, criptografia da URI e geração da primeira audiodescrição.

        Args:
            chat_id (str): Identificador do usuário.
            content_bytes (bytes): Conteúdo binário do arquivo.
            mime_type (str): Tipo MIME do arquivo.

        Returns:
            str: Resposta inicial da Amélie sobre o arquivo.
        """
        logger.info(f"Recebido. Tipo: {mime_type} | Chat: {chat_id}")
        
        if not await self.persistence.has_accepted_terms(chat_id):
            return "POR_FAVOR_ACEITE_TERMOS"

        # Limpa cache do Google de sessões anteriores do mesmo usuário
        session_data = await self.persistence.get_session(chat_id)
        if session_data:
            session, _ = session_data
            old_uri = self.security.decrypt(session["uri"])
            asyncio.create_task(self.ai_model.delete_file(old_uri))

        # Upload e blindagem via fila serializada
        file_uri = await self._enqueue_request(chat_id, self.ai_model.upload_file, content_bytes, mime_type)
        encrypted_uri = self.security.encrypt(file_uri)
        
        new_session = {
            "uri": encrypted_uri,
            "mime": mime_type,
            "history": []
        }
        await self.persistence.save_session(chat_id, new_session)
        
        # Seleção de prompt baseado em preferências persistentes
        style = await self.persistence.get_preference(chat_id, "style") or "longo"
        if mime_type.startswith("image/"):
            prompt = "Descreva esta imagem de forma muito breve (200 letras)." if style == "curto" else "Descreva detalhadamente esta imagem para um cego."
        elif mime_type.startswith("video/"):
            video_mode = await self.persistence.get_preference(chat_id, "video_mode") or "completo"
            if video_mode == "legenda":
                prompt = "Transcreva a faixa de áudio deste vídeo palavra por palavra (verbatim), criando uma legenda fiel ao que é dito."
            else:
                prompt = "Descreva este vídeo detalhadamente de forma cronológica para um cego."
        elif mime_type.startswith("audio/"):
            prompt = "Transcreva este áudio palavra por palavra (verbatim). Não inclua descrições ambientais, ruídos de fundo ou interpretações de contexto. Apenas o texto do que é dito."
        elif mime_type == "application/pdf":
            prompt = "Resuma este PDF de forma simples para um cego."
        elif mime_type == "text/csv":
            prompt = "Analise esta tabela CSV e descreva seus dados de forma clara para um cego."
        elif mime_type == "text/html" or mime_type == "text/xml":
            prompt = "Analise o conteúdo deste documento estruturado e extraia as informações principais."
        else:
            prompt = "Analise este documento e descreva seu conteúdo para uma pessoa cega."

        result = await self.process_question_request(chat_id, prompt)
        logger.info(f"Processado. Tipo: {mime_type}")
        return result

    async def process_question_request(self, chat_id: str, question: str) -> str:
        """
        Processa perguntas de acompanhamento sobre o arquivo em cache.

        Args:
            chat_id (str): Identificador do usuário.
            question (str): Texto da pergunta.

        Returns:
            str: Resposta da IA sobre o contexto.

        Raises:
            NoContextError: Se não houver arquivo ativo ou se a sessão expirou.
        """
        if not await self.persistence.has_accepted_terms(chat_id):
            return "POR_FAVOR_ACEITE_TERMOS"

        session_data = await self.persistence.get_session(chat_id)
        if not session_data:
            raise NoContextError("Sem contexto ativo.")
        
        session, updated_at_str = session_data
        
        # Validação de Inatividade (3 minutos)
        updated_at = datetime.strptime(updated_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        diff = (datetime.now(timezone.utc) - updated_at).total_seconds()
        
        if diff > self.SESSION_TIMEOUT_SECONDS:
            logger.info(f"Sessão expirada para {chat_id}. Limpando silenciosamente.")
            real_uri = self.security.decrypt(session["uri"])
            asyncio.create_task(self.ai_model.delete_file(real_uri))
            await self.persistence.clear_session(chat_id)
            raise NoContextError("Sessão expirada.")

        # Desblindagem de dados para uso na IA
        real_uri = self.security.decrypt(session["uri"])
        real_history = []
        for h in session.get("history", []):
            real_history.append({
                "role": h["role"],
                "parts": [self.security.decrypt(p) for p in h["parts"]]
            })

        logger.info(f"Pergunta sobre cache: '{question[:30]}...' | Chat: {chat_id}")
        
        raw_result = await self._enqueue_request(
            chat_id, self.ai_model.ask_about_file, real_uri, session["mime"], question, real_history
        )

        clean_result = self._clean_text_for_accessibility(raw_result)
        
        # Re-blindagem e salvamento de histórico
        session["history"].append({"role": "user", "parts": [self.security.encrypt(question)]})
        session["history"].append({"role": "model", "parts": [self.security.encrypt(clean_result)]})
        
        await self.persistence.save_session(chat_id, session)
        return clean_result

    async def process_command(self, chat_id: str, command: str) -> str:
        """
        Gerencia comandos do usuário e persistência de preferências de interface.

        Args:
            chat_id (str): ID do usuário.
            command (str): Comando recebido (ex: '/curto').

        Returns:
            str: Mensagem explicativa de feedback para o usuário.
        """
        if command == "/start":
            if await self.persistence.has_accepted_terms(chat_id):
                return "Olá! Sou a Amélie. Já nos conhecemos. Como posso ajudar hoje?"
            return "LGPD_NOTICE"

        if command == "/ajuda":
            return (
                "Olá! Sou a Amélie, sua assistente de audiodescrição e acessibilidade. 👁️🌸\n\n"
                "Aqui está como você pode me usar:\n\n"
                "1. Envie uma mídia: Mande uma foto, vídeo, áudio ou documento (PDF/MD).\n"
                "2. Pergunte detalhes: Após enviar, você pode digitar perguntas sobre o arquivo.\n\n"
                "Comandos de Configuração:\n"
                "/curto - Imagem: Audiodescrição breve (até 200 letras).\n"
                "/longo - Imagem: Audiodescrição detalhada (padrão).\n"
                "/legenda - Vídeo: Transcrição literal (verbatim) da fala presente no vídeo.\n"
                "/completo - Vídeo: Descrição visual narrativa detalhada (padrão).\n"
                "/ajuda - Mostra esta mensagem de ajuda."
            )
        
        prefs = {"/curto": ("style", "curto"), "/longo": ("style", "longo"), 
                 "/legenda": ("video_mode", "legenda"), "/completo": ("video_mode", "completo")}
        
        if command in prefs:
            key, val = prefs[command]
            await self.persistence.save_preference(chat_id, key, val)
            
            if command == "/curto":
                return "O modo curto foi ativado com sucesso. Isso significa que as audiodescrições de imagem serão breves, com até 200 letras, ideais para uma identificação rápida."
            elif command == "/longo":
                return "O modo longo foi ativado com sucesso. Agora as audiodescrições de imagem serão completas e detalhadas, fornecendo o máximo de contexto visual."
            elif command == "/legenda":
                return "O modo legenda foi ativado com sucesso. A Amélie agora irá transcrever a faixa de áudio dos vídeos palavra por palavra (verbatim), gerando uma legenda fiel ao que é dito."
            elif command == "/completo":
                return "O modo completo para vídeos foi ativado com sucesso. As descrições de vídeo agora serão narrativas e detalhadas."
            
            return f"Preferência atualizada: o modo {val} foi ativado!"
        
        return "Comando desconhecido. Digite /ajuda para ver as opções."

    async def accept_terms(self, chat_id: str):
        """
        Registra o consentimento definitivo do usuário no banco de dados.

        Args:
            chat_id (str): ID do usuário.
        """
        await self.persistence.accept_terms(chat_id)

    def get_lgpd_text(self) -> str:
        """
        Retorna o manifesto de privacidade e proteção de dados da Amélie.

        Returns:
            str: Texto do manifesto de consentimento.
        """
        return (
            "Olá, eu sou a Amélie! 👁️🌸\n\n"
            "Antes de começarmos, preciso informar como cuido da sua privacidade em conformidade com a LGPD:\n\n"
            "1. Blindagem Total: Suas imagens, vídeos e conversas são protegidos por criptografia de ponta AES-256 antes mesmo de serem salvos. Nem meus gestores conseguem ler o seu histórico.\n"
            "2. Processamento Seguro: Seus arquivos são enviados temporariamente para o Google Gemini apenas para análise e deletados automaticamente após o uso.\n"
            "3. Seus Direitos: Seus dados pertencem a você. Usamos a tecnologia para ampliar sua visão, não para vigiá-lo.\n\n"
            "Ao clicar no botão abaixo, você concorda com estes termos e podemos iniciar nossa jornada juntos."
        )
