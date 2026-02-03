import os
from dotenv import load_dotenv
from core.service import VisionService
from adapters.vision.gemini_adapter import GeminiAdapter
from adapters.messaging.telegram_adapter import TelegramAdapter

# Carrega variáveis do arquivo .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("Erro: Verifique se TELEGRAM_TOKEN e GEMINI_API_KEY estão no .env")
        return

    # 1. Configura o modelo (Gemini 2.0 Flash)
    ai_model = GeminiAdapter(api_key=GEMINI_API_KEY)
    
    # 2. Configura o serviço core (Refatorado para ai_model)
    service = VisionService(ai_model=ai_model)
    
    # 3. Configura o bot do Telegram
    bot = TelegramAdapter(token=TELEGRAM_TOKEN, vision_service=service)
    
    # 4. Inicia o bot (bloqueante)
    bot.start()

if __name__ == "__main__":
    main()
