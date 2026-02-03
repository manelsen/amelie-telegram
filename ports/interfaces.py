from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class MessagingPort(ABC):
    """
    Interface para adaptadores de mensagens (ex: Telegram, Discord).
    
    Define os contratos básicos para envio de mensagens, inicialização do serviço
    e gestão de fluxos interativos (como botões).
    """
    @abstractmethod
    def start(self):
        """Inicia o serviço de escuta de mensagens."""
        pass

    @abstractmethod
    async def send_message(self, chat_id: str, text: str):
        """
        Envia uma mensagem de texto para um chat específico.
        
        Args:
            chat_id: Identificador único do chat.
            text: Conteúdo da mensagem.
        """
        pass

class AIModelPort(ABC):
    """
    Interface para adaptadores de modelos de Inteligência Artificial (ex: Gemini, GLM).
    
    Gerencia o ciclo de vida de arquivos e a geração de conteúdo multimodal.
    """
    @abstractmethod
    async def upload_file(self, content_bytes: bytes, mime_type: str) -> str:
        """
        Realiza o upload de um arquivo para o provedor de IA.
        """
        pass

    @abstractmethod
    async def ask_about_file(self, file_uri: str, mime_type: str, prompt: str, history: list = None) -> str:
        """
        Faz uma pergunta contextual sobre um arquivo previamente enviado.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_uri: str):
        """
        Remove um arquivo do cache do provedor.
        """
        pass

class SecurityPort(ABC):
    """
    Interface para serviços de criptografia e segurança (AES-256).
    """
    @abstractmethod
    def encrypt(self, plain_text: str) -> str:
        """Criptografa um texto puro."""
        pass

    @abstractmethod
    def decrypt(self, cipher_text: str) -> str:
        """Descriptografa um texto cifrado."""
        pass

class PersistencePort(ABC):
    """
    Interface para adaptadores de banco de dados e armazenamento.
    """
    @abstractmethod
    async def save_session(self, chat_id: str, data: Dict[str, Any]):
        """Salva os dados de sessão de um usuário."""
        pass

    @abstractmethod
    async def get_session(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Recupera os dados de sessão de um usuário."""
        pass

    @abstractmethod
    async def clear_session(self, chat_id: str):
        """Remove a sessão de um usuário."""
        pass

    @abstractmethod
    async def save_preference(self, chat_id: str, key: str, value: str):
        """Salva uma preferência de usuário."""
        pass

    @abstractmethod
    async def get_preference(self, chat_id: str, key: str) -> Optional[str]:
        """Recupera uma preferência de usuário."""
        pass
    
    @abstractmethod
    async def has_accepted_terms(self, chat_id: str) -> bool:
        """
        Verifica se o usuário já aceitou os termos da LGPD.
        
        Args:
            chat_id: ID do chat.
            
        Returns:
            bool: True se aceitou, False caso contrário.
        """
        pass

    @abstractmethod
    async def accept_terms(self, chat_id: str):
        """
        Registra o consentimento do usuário com os termos de privacidade.
        
        Args:
            chat_id: ID do chat.
        """
        pass
