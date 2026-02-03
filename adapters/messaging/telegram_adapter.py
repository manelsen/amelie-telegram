from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import asyncio
from ports.interfaces import MessagingPort
from core.service import VisionService

class TelegramAdapter(MessagingPort):
    def __init__(self, token: str, vision_service: VisionService):
        self.token = token
        self.vision_service = vision_service
        self.app = ApplicationBuilder().token(token).build()
        # Mimetypes suportados
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
        message = update.message
        if not message: return

        # Limite de 20MB em bytes
        MAX_FILE_SIZE = 20 * 1024 * 1024 
        file_to_download = None
        mime_type = None

        # 1. Foto
        if message.photo:
            photo = message.photo[-1]
            if photo.file_size > MAX_FILE_SIZE:
                await message.reply_text("Desculpe, esta imagem é muito grande. O limite é de 20MB.")
                return
            file_to_download = await photo.get_file()
            mime_type = "image/jpeg"
        
        # 2. Vídeo
        elif message.video:
            if message.video.file_size > MAX_FILE_SIZE:
                await message.reply_text("Desculpe, este vídeo é muito grande. O limite é de 20MB.")
                return
            file_to_download = await message.video.get_file()
            mime_type = message.video.mime_type or "video/mp4"

        # 3. Documento (PDF, MD, Vídeos anexados como arquivo, etc)
        elif message.document:
            if message.document.file_size > MAX_FILE_SIZE:
                await message.reply_text(f"O arquivo '{message.document.file_name}' excede o limite de 20MB.")
                return

            raw_mime = message.document.mime_type
            file_name = message.document.file_name.lower()
            
            if raw_mime in self.supported_mimetypes:
                mime_type = self.supported_mimetypes[raw_mime]
            elif file_name.endswith(".md"):
                mime_type = "text/markdown"
            elif file_name.endswith(".pdf"):
                mime_type = "application/pdf"
            elif file_name.endswith(".mp4"):
                mime_type = "video/mp4"
            
            if mime_type:
                file_to_download = await message.document.get_file()
            else:
                await message.reply_text(f"Formato não suportado: {raw_mime or 'desconhecido'}")
                return

        if file_to_download:
            try:
                await update.message.reply_text(f"Processando {mime_type}... 🚀")
                content_bytes = await file_to_download.download_as_bytearray()
                
                result = await self.vision_service.process_file_request(bytes(content_bytes), mime_type)
                
                # Divide a resposta em blocos de no máximo 4000 caracteres
                MAX_LENGTH = 4000
                if len(result) <= MAX_LENGTH:
                    await update.message.reply_text(result)
                else:
                    for i in range(0, len(result), MAX_LENGTH):
                        chunk = result[i:i + MAX_LENGTH]
                        if chunk.strip():
                            await update.message.reply_text(chunk)
            except Exception as e:
                print(f"Erro: {e}")
                await update.message.reply_text(f"Erro ao processar arquivo.")

    def start(self):
        # Escuta fotos, vídeos e documentos
        message_handler = MessageHandler(filters.PHOTO | filters.VIDEO | filters.Document.ALL, self._handle_message)
        self.app.add_handler(message_handler)
        print("Bot iniciado (Imagens + PDF + MD + Vídeo)...")
        self.app.run_polling()

    async def send_message(self, chat_id: str, text: str):
        await self.app.bot.send_message(chat_id=chat_id, text=text)
