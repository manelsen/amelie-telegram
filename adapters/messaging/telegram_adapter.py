from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler
import logging
import asyncio
from ports.interfaces import MessagingPort
from core.service import VisionService
from core.exceptions import NoContextError

logger = logging.getLogger("TelegramAdapter")

class TelegramAdapter(MessagingPort):
    """
    Adaptador para a plataforma Telegram (python-telegram-bot).
    
    Implementa a interface MessagingPort para gerenciar mensagens, mídias
    e botões interativos de consentimento da LGPD.
    """

    def __init__(self, token: str, vision_service: VisionService):
        """Inicializa a aplicação Telegram e configura os tipos suportados."""
        self.token = token
        self.vision_service = vision_service
        self.app = ApplicationBuilder().token(token).read_timeout(30).write_timeout(30).build()
        
        self.supported_mimetypes = {
            "image/jpeg": "image/jpeg", "image/png": "image/png", "image/webp": "image/webp",
            "application/pdf": "application/pdf", "text/markdown": "text/markdown",
            "video/mp4": "video/mp4", "audio/mpeg": "audio/mpeg", "audio/ogg": "audio/ogg"
        }

    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direciona comandos do Telegram para o VisionService."""
        chat_id = str(update.effective_chat.id)
        command = update.message.text.split()[0].lower()
        result = await self.vision_service.process_command(chat_id, command)
        
        if result == "LGPD_NOTICE":
            keyboard = [[InlineKeyboardButton("Concordo e Aceito", callback_data='accept_lgpd')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(self.vision_service.get_lgpd_text(), reply_markup=reply_markup)
        else:
            await update.message.reply_text(result)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gerencia cliques em botões (Inline Buttons)."""
        query = update.callback_query
        await query.answer()
        if query.data == 'accept_lgpd':
            chat_id = str(update.effective_chat.id)
            await self.vision_service.accept_terms(chat_id)
            await query.edit_message_text(text="Obrigada por confiar na Amélie! 🌸 Agora você já pode me enviar imagens, vídeos ou documentos para análise.")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler mestre para mensagens recebidas.
        
        Realiza o roteamento de mídias para o núcleo de processamento.
        """
        self.vision_service.start_worker()
        if not update.message: return
        message = update.message
        chat_id = str(update.effective_chat.id)

        file_to_download = None
        mime_type = None

        # Identificação robusta do tipo de mídia
        if message.photo:
            file_to_download = await message.photo[-1].get_file()
            mime_type = "image/jpeg"
        elif message.video:
            file_to_download = await message.video.get_file()
            mime_type = message.video.mime_type or "video/mp4"
        elif message.voice:
            file_to_download = await message.voice.get_file()
            mime_type = message.voice.mime_type or "audio/ogg"
        elif message.audio:
            file_to_download = await message.audio.get_file()
            mime_type = message.audio.mime_type or "audio/mpeg"
        elif message.document:
            raw_mime = message.document.mime_type
            file_name = message.document.file_name.lower()
            if raw_mime in self.supported_mimetypes: mime_type = self.supported_mimetypes[raw_mime]
            elif file_name.endswith(".md"): mime_type = "text/markdown"
            elif file_name.endswith(".pdf"): mime_type = "application/pdf"
            if mime_type: file_to_download = await message.document.get_file()

        if file_to_download:
            try:
                content_bytes = await file_to_download.download_as_bytearray()
                result = await self.vision_service.process_file_request(chat_id, bytes(content_bytes), mime_type)
                if result == "POR_FAVOR_ACEITE_TERMOS":
                    await update.message.reply_text("Para sua segurança, aceite os termos da LGPD digitando /start antes de começarmos.")
                else:
                    await self._send_long_message(update, result)
            except Exception as e:
                logger.error(f"Erro: {e}", exc_info=True)
            return

        if message.text:
            try:
                result = await self.vision_service.process_question_request(chat_id, message.text)
                if result == "POR_FAVOR_ACEITE_TERMOS":
                    await update.message.reply_text("Por favor, aceite os termos da LGPD digitando /start primeiro.")
                else:
                    await self._send_long_message(update, result)
            except NoContextError:
                await update.message.reply_text("Por favor, envie um arquivo primeiro.")
            except Exception as e:
                logger.error(f"Erro: {e}", exc_info=True)

    async def _send_long_message(self, update: Update, text: str):
        """Garante o envio completo de textos extensos dividindo em chunks."""
        MAX_LENGTH = 4000
        for i in range(0, len(text), MAX_LENGTH):
            chunk = text[i:i + MAX_LENGTH]
            if chunk.strip(): await update.message.reply_text(chunk)

    def start(self):
        """Registra handlers e inicia o ciclo de vida do bot."""
        self.app.add_handler(CommandHandler(["start", "ajuda", "curto", "longo", "legenda", "completo"], self._handle_command))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO | filters.Document.ALL | filters.TEXT & (~filters.COMMAND), self._handle_message))
        
        logger.info("Bot Amélie iniciado no Telegram.")
        self.app.run_polling()

    async def send_message(self, chat_id: str, text: str):
        """Envia mensagem assíncrona para o cliente."""
        await self.app.bot.send_message(chat_id=chat_id, text=text)
