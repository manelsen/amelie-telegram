import aiosqlite
import json
from typing import Optional, Dict, Any, Tuple
from ports.interfaces import PersistencePort

class SQLitePersistenceAdapter(PersistencePort):
    """
    Adaptador de persistência que utiliza o banco de dados SQLite assíncrono.
    
    Responsável por armazenar dados de sessão criptografados, preferências 
    de interface e o registro de consentimento legal (LGPD).
    """

    def __init__(self, db_path: str):
        """
        Inicializa o caminho para o arquivo do banco de dados.

        Args:
            db_path (str): Caminho local do arquivo .db.
        """
        self.db_path = db_path

    async def _init_db(self):
        """
        Garante a criação das tabelas 'sessions', 'preferences' e 'users' se não existirem.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    chat_id TEXT PRIMARY KEY,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    chat_id TEXT,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY (chat_id, key)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id TEXT PRIMARY KEY,
                    accepted_terms INTEGER DEFAULT 0,
                    accepted_at TIMESTAMP
                )
            ''')
            await db.commit()

    async def save_session(self, chat_id: str, data: Dict[str, Any]):
        """
        Salva ou substitui os dados da sessão de um usuário.

        Args:
            chat_id (str): ID do chat do usuário.
            data (Dict[str, Any]): Dicionário com os dados (ex: URI, histórico).
        """
        await self._init_db()
        json_data = json.dumps(data)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO sessions (chat_id, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)',
                (chat_id, json_data)
            )
            await db.commit()

    async def get_session(self, chat_id: str) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        Recupera a sessão de um chat e a data da última atualização.

        Args:
            chat_id (str): ID do chat do usuário.

        Returns:
            Optional[Tuple[Dict[str, Any], str]]: Tupla contendo os dados e o timestamp (UTC).
        """
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT data, updated_at FROM sessions WHERE chat_id = ?', (chat_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return json.loads(row[0]), row[1]
        return None

    async def clear_session(self, chat_id: str):
        """
        Deleta os dados de sessão de um chat específico.

        Args:
            chat_id (str): ID do chat a ser limpo.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM sessions WHERE chat_id = ?', (chat_id,))
            await db.commit()

    async def save_preference(self, chat_id: str, key: str, value: str):
        """
        Armazena uma preferência personalizada de interface.

        Args:
            chat_id (str): ID do chat do usuário.
            key (str): Chave da preferência (ex: 'style').
            value (str): Valor da preferência (ex: 'curto').
        """
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO preferences (chat_id, key, value) VALUES (?, ?, ?)',
                (chat_id, key, value)
            )
            await db.commit()

    async def get_preference(self, chat_id: str, key: str) -> Optional[str]:
        """
        Recupera uma preferência salva anteriormente.

        Args:
            chat_id (str): ID do chat do usuário.
            key (str): Chave da preferência.

        Returns:
            Optional[str]: O valor salvo ou None se não existir.
        """
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT value FROM preferences WHERE chat_id = ? AND key = ?', (chat_id, key)) as cursor:
                row = await cursor.fetchone()
                if row: return row[0]
        return None

    async def has_accepted_terms(self, chat_id: str) -> bool:
        """
        Verifica se o usuário deu consentimento à política de privacidade.

        Args:
            chat_id (str): ID do chat do usuário.

        Returns:
            bool: True se aceito, False se pendente.
        """
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT accepted_terms FROM users WHERE chat_id = ?', (chat_id,)) as cursor:
                row = await cursor.fetchone()
                return bool(row and row[0])

    async def accept_terms(self, chat_id: str):
        """
        Registra a aceitação dos termos no banco com timestamp.

        Args:
            chat_id (str): ID do chat do usuário.
        """
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                'INSERT OR REPLACE INTO users (chat_id, accepted_terms, accepted_at) VALUES (?, 1, CURRENT_TIMESTAMP)',
                (chat_id,)
            )
            await db.commit()
