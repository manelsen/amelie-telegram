import os
import logging
from dotenv import load_dotenv, set_key
from cryptography.fernet import Fernet
from core.service import VisionService
from adapters.vision.gemini_adapter import GeminiAdapter
from adapters.messaging.telegram_adapter import TelegramAdapter
from adapters.security.fernet_adapter import FernetSecurityAdapter
from adapters.persistence.sqlite_adapter import SQLitePersistenceAdapter

# Configuração de log para o processo de inicialização
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Launcher")

def setup_security_key():
    """Garante que haja uma chave de segurança no .env"""
    key = os.getenv("SECURITY_KEY")
    if not key:
        logger.info("Nenhuma SECURITY_KEY encontrada. Gerando uma nova blindagem...")
        new_key = Fernet.generate_key().decode()
        # Tenta gravar no arquivo .env se ele existir
        if os.path.exists(".env"):
            set_key(".env", "SECURITY_KEY", new_key)
            logger.info("Nova SECURITY_KEY gerada e salva no arquivo .env")
        else:
            logger.warning("Arquivo .env não encontrado. Usando chave temporária para esta sessão.")
        return new_key
    return key

def main():
    load_dotenv()
    
    # 1. Configurações essenciais
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SECURITY_KEY = setup_security_key()

    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logger.error("TELEGRAM_TOKEN ou GEMINI_API_KEY faltando no ambiente/env.")
        return

    # 2. Montagem da Arquitetura Hexagonal
    try:
        ai_model = GeminiAdapter(api_key=GEMINI_API_KEY)
        security = FernetSecurityAdapter(key=SECURITY_KEY)
        persistence = SQLitePersistenceAdapter(db_path="bot_data.db")
        
        service = VisionService(ai_model=ai_model, security=security, persistence=persistence)
        
        # 3. Início do Adaptador de Mensagens
        bot = TelegramAdapter(token=TELEGRAM_TOKEN, vision_service=service)
        bot.start()
    except Exception as e:
        logger.critical(f"Falha catastrófica na inicialização: {e}", exc_info=True)

if __name__ == "__main__":
    main()
