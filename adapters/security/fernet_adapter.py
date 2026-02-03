from cryptography.fernet import Fernet
from ports.interfaces import SecurityPort

class FernetSecurityAdapter(SecurityPort):
    def __init__(self, key: str):
        # A chave deve ser gerada via Fernet.generate_key() e guardada no .env
        self.fernet = Fernet(key.encode())

    def encrypt(self, plain_text: str) -> str:
        if not plain_text: return ""
        return self.fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        if not cipher_text: return ""
        return self.fernet.decrypt(cipher_text.encode()).decode()
