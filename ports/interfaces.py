from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

class MessagingPort(ABC):
    """
    Interface para adaptadores de mensagens (ex: Telegram, Discord).
    
    Define os contratos básicos para envio de mensagens, inicialização do serviço
    e gestão de fluxos interativos e comandos de menu.
    """
    @abstractmethod
    def start(self):
        """
        Inicia o serviço de escuta de mensagens e configura o ambiente operacional.
        """
        pass

    @abstractmethod
    async def send_message(self, chat_id: str, text: str):
        """
        Envia uma mensagem de texto para um chat específico.
        
        Args:
            chat_id (str): Identificador único do chat ou usuário.
            text (str): Conteúdo textual da mensagem a ser enviada.
        """
        pass

class AIModelPort(ABC):
    """
    Interface para adaptadores de modelos de Inteligência Artificial (ex: Gemini, GLM).
    
    Gerencia o ciclo de vida de arquivos na nuvem do provedor e a geração de conteúdo multimodal.
    """
    @abstractmethod
    async def upload_file(self, content_bytes: bytes, mime_type: str) -> str:
        """
        Realiza o upload de um arquivo para o provedor de IA.
        
        Args:
            content_bytes (bytes): Conteúdo bruto do arquivo em bytes.
            mime_type (str): Tipo MIME do arquivo (ex: 'image/jpeg').
            
        Returns:
            str: URI ou identificador único do arquivo no cache do provedor.
        """
        pass

    @abstractmethod
    async def ask_about_file(self, file_uri: str, mime_type: str, prompt: str, history: list = None) -> str:
        """
        Faz uma pergunta contextual sobre um arquivo previamente enviado.
        
        Args:
            file_uri (str): URI do arquivo no cache da infraestrutura de IA.
            mime_type (str): Tipo do arquivo para prover contexto ao modelo.
            prompt (str): Pergunta, instrução ou comando do usuário.
            history (list, optional): Lista de turnos anteriores da conversa para manter contexto.
            
        Returns:
            str: Resposta textual gerada pela Inteligência Artificial.
        """
        pass

    @abstractmethod
    async def delete_file(self, file_uri: str):
        """
        Remove permanentemente um arquivo do cache do provedor para otimização de recursos.
        
        Args:
            file_uri (str): URI completa do arquivo a ser deletado.
        """
        pass

class SecurityPort(ABC):
    """
    Interface para serviços de criptografia e segurança (Blindagem de Dados).
    """
    @abstractmethod
    def encrypt(self, plain_text: str) -> str:
        """
        Criptografa um texto puro utilizando algoritmos simétricos.
        
        Args:
            plain_text (str): Texto original sensível a ser protegido.
            
        Returns:
            str: Texto cifrado resultante (geralmente codificado em Base64).
        """
        pass

    @abstractmethod
    def decrypt(self, cipher_text: str) -> str:
        """
        Descriptografa um texto cifrado para sua forma original.
        
        Args:
            cipher_text (str): Texto criptografado (token Fernet/AES).
            
        Returns:
            str: Texto puro original descriptografado.
        """
        pass

class PersistencePort(ABC):
    """
    Interface para adaptadores de banco de dados e persistência de longo prazo.
    """
    @abstractmethod
    async def save_session(self, chat_id: str, data: Dict[str, Any]):
        """
        Salva ou atualiza os dados de sessão criptografados de um usuário.
        
        Args:
            chat_id (str): ID único do chat.
            data (Dict[str, Any]): Dicionário contendo os dados da sessão (URI, histórico, etc).
        """
        pass

    @abstractmethod
    async def get_session(self, chat_id: str) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        Recupera os dados de sessão e o timestamp da última atualização.
        
        Args:
            chat_id (str): ID único do chat.
            
        Returns:
            Optional[Tuple[Dict[str, Any], str]]: Tupla com os dados da sessão e a data (ISO string), 
                                                 ou None se não encontrado.
        """
        pass

    @abstractmethod
    async def clear_session(self, chat_id: str):
        """
        Remove a sessão ativa de um usuário do armazenamento.
        
        Args:
            chat_id (str): ID único do chat.
        """
        pass

    @abstractmethod
    async def save_preference(self, chat_id: str, key: str, value: str):
        """
        Armazena preferências persistentes de interface (ex: modo de audiodescrição).
        
        Args:
            chat_id (str): ID único do chat.
            key (str): Nome da chave de preferência (ex: 'style').
            value (str): Valor da preferência (ex: 'curto').
        """
        pass

    @abstractmethod
    async def get_preference(self, chat_id: str, key: str) -> Optional[str]:
        """
        Recupera uma preferência específica de um usuário.
        
        Args:
            chat_id (str): ID único do chat.
            key (str): Nome da chave de preferência.
            
        Returns:
            Optional[str]: O valor da preferência ou None se não definida.
        """
        pass

    @abstractmethod
    async def has_accepted_terms(self, chat_id: str) -> bool:
        """
        Verifica se o usuário já consentiu com os termos da LGPD.
        
        Args:
            chat_id (str): ID único do chat.
            
        Returns:
            bool: True se o usuário aceitou os termos, False caso contrário.
        """
        pass

    @abstractmethod
    async def accept_terms(self, chat_id: str):
        """
        Registra o consentimento oficial do usuário no banco de dados.
        
        Args:
            chat_id (str): ID único do chat.
        """
        pass
