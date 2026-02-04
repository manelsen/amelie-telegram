from cryptography.fernet import Fernet
from ports.interfaces import SecurityPort

class FernetSecurityAdapter(SecurityPort):
    """
    Adaptador de segurança que utiliza criptografia simétrica AES-256 (Padrão Fernet).
    
    Garante o isolamento e a privacidade dos dados sensíveis armazenados, 
    permitindo que o sistema opere sob o conceito de 'Cegueira do Gestor'.
    """

    def __init__(self, key: str):
        """
        Inicializa o motor de criptografia com a chave mestra.

        Args:
            key (str): Chave simétrica em Base64 (32 bytes).
        """
        self.fernet = Fernet(key.encode())

    def encrypt(self, plain_text: str) -> str:
        """
        Transforma texto legível em um token criptografado seguro.

        Args:
            plain_text (str): Conteúdo original a ser protegido.

        Returns:
            str: Texto cifrado em formato string (Base64).
        """
        if not plain_text: return ""
        return self.fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        """
        Reverte um token criptografado para sua forma original legível.

        Args:
            cipher_text (str): Token Fernet criptografado.

        Returns:
            str: O texto original descriptografado.
        """
        if not cipher_text: return ""
        return self.fernet.decrypt(cipher_text.encode()).decode()
