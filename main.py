import os
from dotenv import load_dotenv
from core.service import VisionService
from adapters.vision.gemini_adapter import GeminiAdapter
from adapters.messaging.telegram_adapter import TelegramAdapter
from adapters.security.fernet_adapter import FernetSecurityAdapter
from adapters.persistence.sqlite_adapter import SQLitePersistenceAdapter

load_dotenv()

def main():
    # 1. Configurações
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SECURITY_KEY = os.getenv("SECURITY_KEY")

    if not all([TELEGRAM_TOKEN, GEMINI_API_KEY, SECURITY_KEY]):
        print("Erro: Verifique se TELEGRAM_TOKEN, GEMINI_API_KEY e SECURITY_KEY estão no .env")
        return

    # 2. Montagem do Hexágono (Injeção de Dependência)
    ai_model = GeminiAdapter(api_key=GEMINI_API_KEY)
    security = FernetSecurityAdapter(key=SECURITY_KEY)
    persistence = SQLitePersistenceAdapter(db_path="bot_data.db")
    
    service = VisionService(ai_model=ai_model, security=security, persistence=persistence)
    
    # 3. Inicia o Bot
    bot = TelegramAdapter(token=TELEGRAM_TOKEN, vision_service=service)
    bot.start()

if __name__ == "__main__":
    main()
