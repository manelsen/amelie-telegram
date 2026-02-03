from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class MessagingPort(ABC):
    @abstractmethod
    def start(self): pass
    @abstractmethod
    async def send_message(self, chat_id: str, text: str): pass

class AIModelPort(ABC):
    @abstractmethod
    async def upload_file(self, content_bytes: bytes, mime_type: str) -> str: pass
    @abstractmethod
    async def ask_about_file(self, file_uri: str, mime_type: str, prompt: str, history: list = None) -> str: pass
    @abstractmethod
    async def delete_file(self, file_uri: str): pass

class SecurityPort(ABC):
    @abstractmethod
    def encrypt(self, plain_text: str) -> str: pass
    @abstractmethod
    def decrypt(self, cipher_text: str) -> str: pass

class PersistencePort(ABC):
    @abstractmethod
    async def save_session(self, chat_id: str, data: Dict[str, Any]): pass
    @abstractmethod
    async def get_session(self, chat_id: str) -> Optional[Dict[str, Any]]: pass
    @abstractmethod
    async def clear_session(self, chat_id: str): pass
    @abstractmethod
    async def save_preference(self, chat_id: str, key: str, value: str): pass
    @abstractmethod
    async def get_preference(self, chat_id: str, key: str) -> Optional[str]: pass
