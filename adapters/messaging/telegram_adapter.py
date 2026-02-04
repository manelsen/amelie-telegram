from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
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
        
        # Lista exaustiva de mimetypes suportados pela API do Gemini
        self.supported_mimetypes = {
            # Imagens
            "image/jpeg": "image/jpeg", "image/png": "image/png", 
            "image/webp": "image/webp", "image/heic": "image/heic", 
            "image/heif": "image/heif",
            
            # Áudio
            "audio/wav": "audio/wav", "audio/x-wav": "audio/wav",
            "audio/mp3": "audio/mpeg", "audio/mpeg": "audio/mpeg",
            "audio/aac": "audio/aac", "audio/ogg": "audio/ogg",
            "audio/flac": "audio/flac", "audio/x-flac": "audio/flac",
            "audio/aiff": "audio/aiff", "audio/x-aiff": "audio/aiff",
            
            # Vídeo
            "video/mp4": "video/mp4", "video/mpeg": "video/mpeg",
            "video/quicktime": "video/quicktime", "video/x-msvideo": "video/x-msvideo",
            "video/x-flv": "video/x-flv", "video/webm": "video/webm",
            "video/x-ms-wmv": "video/x-ms-wmv", "video/3gpp": "video/3gpp",
            
            # Documentos e Texto
            "application/pdf": "application/pdf",
            "text/plain": "text/plain",
            "text/markdown": "text/markdown",
            "text/html": "text/html",
            "text/csv": "text/csv",
            "text/xml": "text/xml"
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

        # Identificação robusta do tipo de mídia enviada nativamente
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
            
            # Mapeamento para documentos e arquivos genéricos
            if raw_mime in self.supported_mimetypes:
                mime_type = self.supported_mimetypes[raw_mime]
            elif file_name.endswith(".md"): mime_type = "text/markdown"
            elif file_name.endswith(".pdf"): mime_type = "application/pdf"
            elif file_name.endswith(".csv"): mime_type = "text/csv"
            elif file_name.endswith(".txt"): mime_type = "text/plain"
            elif file_name.endswith(".html"): mime_type = "text/html"
            elif file_name.endswith(".xml"): mime_type = "text/xml"
            elif file_name.endswith((".mp3", ".wav", ".ogg", ".flac", ".aac", ".aiff")):
                mime_type = "audio/mpeg" # Fallback para áudio
            elif file_name.endswith((".mp4", ".mov", ".avi", ".webm")):
                mime_type = "video/mp4" # Fallback para vídeo
                
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
                logger.error(f"Erro no processamento de arquivo: {e}", exc_info=True)
            return

        if message.text:
            try:
                result = await self.vision_service.process_question_request(chat_id, message.text)
                if result == "POR_FAVOR_ACEITE_TERMOS":
                    await update.message.reply_text("Por favor, aceite os termos da LGPD digitando /start primeiro.")
                else:
                    await self._send_long_message(update, result)
            except NoContextError:
                await update.message.reply_text("Por favor, envie um arquivo primeiro para começarmos.")
            except Exception as e:
                logger.error(f"Erro na pergunta contextual: {e}", exc_info=True)

    async def _send_long_message(self, update: Update, text: str):
        """Garante o envio completo de textos extensos dividindo em chunks."""
        MAX_LENGTH = 4000
        for i in range(0, len(text), MAX_LENGTH):
            chunk = text[i:i + MAX_LENGTH]
            if chunk.strip(): await update.message.reply_text(chunk)

    async def _setup_commands(self):
        """Configura o menu de comandos (botão Menu) no Telegram."""
        commands = [
            BotCommand("start", "Iniciar Amélie e aceitar termos"),
            BotCommand("ajuda", "Ver manual de uso"),
            BotCommand("curto", "Imagem: Audiodescrição breve"),
            BotCommand("longo", "Imagem: Audiodescrição detalhada"),
            BotCommand("legenda", "Vídeo: Transcrição verbatim"),
            BotCommand("completo", "Vídeo: Descrição narrativa")
        ]
        await self.app.bot.set_my_commands(commands)

    def start(self):
        """Registra handlers e inicia o ciclo de vida do bot."""
        loop = asyncio.get_event_loop()
        loop.create_task(self._setup_commands())

        self.app.add_handler(CommandHandler(["start", "ajuda", "curto", "longo", "legenda", "completo"], self._handle_command))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(
            filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO | filters.Document.ALL | filters.TEXT & (~filters.COMMAND), 
            self._handle_message
        ))
        
        logger.info("Bot Amélie iniciado no Telegram com suporte total a arquivos.")
        self.app.run_polling()

    async def send_message(self, chat_id: str, text: str):
        """Envia mensagem assíncrona para o cliente."""
        await self.app.bot.send_message(chat_id=chat_id, text=text)
