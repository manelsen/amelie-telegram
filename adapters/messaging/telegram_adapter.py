from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import logging
import asyncio
from ports.interfaces import MessagingPort
from core.service import VisionService
from core.exceptions import NoContextError

logger = logging.getLogger("TelegramAdapter")

class TelegramAdapter(MessagingPort):
    def __init__(self, token: str, vision_service: VisionService):
        self.token = token
        self.vision_service = vision_service
        self.app = ApplicationBuilder().token(token).read_timeout(30).write_timeout(30).build()
        
        self.supported_mimetypes = {
            "image/jpeg": "image/jpeg", "image/png": "image/png", "image/webp": "image/webp",
            "application/pdf": "application/pdf", "text/markdown": "text/markdown",
            "video/mp4": "video/mp4"
        }

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Garante que o worker está rodando
        self.vision_service.start_worker()
        
        if not update.message: return
        message = update.message
        chat_id = str(update.effective_chat.id)

        file_to_download = None
        mime_type = None

        # Identificação de anexo
        if message.photo:
            file_to_download = await message.photo[-1].get_file()
            mime_type = "image/jpeg"
        elif message.video:
            file_to_download = await message.video.get_file()
            mime_type = message.video.mime_type or "video/mp4"
        elif message.document:
            raw_mime = message.document.mime_type
            file_name = message.document.file_name.lower()
            if raw_mime in self.supported_mimetypes: mime_type = self.supported_mimetypes[raw_mime]
            elif file_name.endswith(".md"): mime_type = "text/markdown"
            elif file_name.endswith(".pdf"): mime_type = "application/pdf"
            elif file_name.endswith(".mp4"): mime_type = "video/mp4"
            if mime_type: file_to_download = await message.document.get_file()

        if file_to_download:
            try:
                # Agora o bot faz o download em silêncio (sem mensagens pro usuário)
                content_bytes = await file_to_download.download_as_bytearray()
                result = await self.vision_service.process_file_request(chat_id, bytes(content_bytes), mime_type)
                await self._send_long_message(update, result)
            except Exception as e:
                # Erro logado internamente, não enviado pro cliente
                logger.error(f"Erro no processamento de arquivo: {e}", exc_info=True)
            return

        if message.text:
            try:
                # Pergunta processada em silêncio
                result = await self.vision_service.process_question_request(chat_id, message.text)
                await self._send_long_message(update, result)
            except NoContextError:
                # Apenas erros de fluxo básico são informados ao usuário
                await update.message.reply_text("Por favor, envie um arquivo primeiro para começarmos.")
            except Exception as e:
                logger.error(f"Erro na pergunta contextual: {e}", exc_info=True)

    async def _send_long_message(self, update, text):
        MAX_LENGTH = 4000
        for i in range(0, len(text), MAX_LENGTH):
            chunk = text[i:i + MAX_LENGTH]
            if chunk.strip(): await update.message.reply_text(chunk)

    def start(self):
        handler = MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.TEXT, self._handle_message)
        self.app.add_handler(handler)
        logger.info("Bot iniciado em modo silencioso (logs apenas no terminal).")
        self.app.run_polling()

    async def send_message(self, chat_id: str, text: str):
        await self.app.bot.send_message(chat_id=chat_id, text=text)
