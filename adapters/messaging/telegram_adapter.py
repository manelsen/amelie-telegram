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

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Pega a foto de maior resolução
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            
            await update.message.reply_text("Processando com Gemini Flash 3... 👁️")
            
            # Processa a imagem no Core
            description = await self.vision_service.process_image_request(bytes(image_bytes))
            await update.message.reply_text(description)
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 1000:
                error_msg = error_msg[:1000] + "... (erro truncado)"
            print(f"Erro no processamento: {e}")
            await update.message.reply_text(f"Desculpe, houve um erro: {error_msg}")

    def start(self):
        # Adiciona o handler e inicia o polling de forma síncrona (gerencia o próprio loop)
        photo_handler = MessageHandler(filters.PHOTO, self._handle_photo)
        self.app.add_handler(photo_handler)
        print("Bot do Telegram iniciado e aguardando imagens...")
        self.app.run_polling()

    async def send_message(self, chat_id: str, text: str):
        await self.app.bot.send_message(chat_id=chat_id, text=text)
