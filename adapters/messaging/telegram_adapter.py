from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import asyncio
import logging
from ports.interfaces import MessagingPort
from core.service import VisionService

logger = logging.getLogger("TelegramAdapter")

class TelegramAdapter(MessagingPort):
    def __init__(self, token: str, vision_service: VisionService):
        self.token = token
        self.vision_service = vision_service
        # Configuração de persistência e retentativa básica do próprio SDK do Telegram
        self.app = ApplicationBuilder().token(token).read_timeout(30).write_timeout(30).build()
        
        self.supported_mimetypes = {
            "image/jpeg": "image/jpeg",
            "image/png": "image/png",
            "image/webp": "image/webp",
            "application/pdf": "application/pdf",
            "text/markdown": "text/markdown",
            "text/x-markdown": "text/markdown",
            "text/plain": "text/plain",
            "video/mp4": "video/mp4",
            "video/mpeg": "video/mpeg",
            "video/quicktime": "video/quicktime",
            "video/x-msvideo": "video/x-msvideo",
            "video/x-flv": "video/x-flv",
            "video/webm": "video/webm",
            "video/x-ms-wmv": "video/x-ms-wmv",
            "video/3gpp": "video/3gpp"
        }

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message: return
        message = update.message

        MAX_FILE_SIZE = 20 * 1024 * 1024 
        file_to_download = None
        mime_type = None

        try:
            # Identificação do tipo
            if message.photo:
                photo = message.photo[-1]
                if photo.file_size > MAX_FILE_SIZE:
                    await message.reply_text("Imagem muito grande (máximo 20MB).")
                    return
                file_to_download = await photo.get_file()
                mime_type = "image/jpeg"
            
            elif message.video:
                if message.video.file_size > MAX_FILE_SIZE:
                    await message.reply_text("Vídeo muito grande (máximo 20MB).")
                    return
                file_to_download = await message.video.get_file()
                mime_type = message.video.mime_type or "video/mp4"

            elif message.document:
                if message.document.file_size > MAX_FILE_SIZE:
                    await message.reply_text(f"Arquivo '{message.document.file_name}' excede 20MB.")
                    return
                raw_mime = message.document.mime_type
                file_name = message.document.file_name.lower()
                
                if raw_mime in self.supported_mimetypes:
                    mime_type = self.supported_mimetypes[raw_mime]
                elif file_name.endswith(".md"): mime_type = "text/markdown"
                elif file_name.endswith(".pdf"): mime_type = "application/pdf"
                elif file_name.endswith(".mp4"): mime_type = "video/mp4"
                
                if mime_type:
                    file_to_download = await message.document.get_file()
                else:
                    await message.reply_text(f"Formato não suportado: {raw_mime or 'desconhecido'}")
                    return

            if file_to_download:
                await update.message.reply_text(f"Processando {mime_type.split('/')[-1]}... 🔄")
                content_bytes = await file_to_download.download_as_bytearray()
                
                # Chamada ao Core Service (que já tem retry e tratamento de erro)
                result = await self.vision_service.process_file_request(bytes(content_bytes), mime_type)
                
                # Envio resiliente (várias mensagens se for longo)
                MAX_LENGTH = 4000
                for i in range(0, len(result), MAX_LENGTH):
                    chunk = result[i:i + MAX_LENGTH]
                    if chunk.strip():
                        await update.message.reply_text(chunk)
            else:
                await update.message.reply_text("Por favor, envie uma foto, vídeo ou documento (.pdf, .md).")

        except Exception as e:
            logger.error(f"Erro no adaptador Telegram: {e}", exc_info=True)
            await update.message.reply_text("Houve um erro técnico ao baixar o arquivo. Tente novamente.")

    def start(self):
        message_handler = MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, self._handle_message)
        self.app.add_handler(message_handler)
        
        # Log de inicialização
        logger.info("Bot iniciado com sistema de resiliência e logs.")
        
        # O run_polling do Telegram já tem um sistema interno de reconexão 
        # se a internet cair (retries=infinitos por padrão)
        self.app.run_polling()

    async def send_message(self, chat_id: str, text: str):
        await self.app.bot.send_message(chat_id=chat_id, text=text)
