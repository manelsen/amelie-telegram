# Vision Bot para Deficientes Visuais 👁️🤖

Um bot multimodal para Telegram construído com **Arquitetura Hexagonal**, focado em acessibilidade e privacidade.

## Funcionalidades
- **Audiodescrição:** Imagens e vídeos processados pelo Gemini 2.5 Flash Lite.
- **Análise de Documentos:** Suporte para PDF e Markdown.
- **Sessões Contextuais:** Pergunte detalhes sobre o último arquivo enviado.
- **Acessibilidade Total:** Respostas em português, texto puro, sem Markdown ou asteriscos.
- **Privacidade (Blindagem):** Banco de dados SQLite criptografado com AES-256 (Ponta-a-ponta na infraestrutura).
- **Resiliência:** Sistema de fila global e retentativas automáticas.

## Como Instalar

### 1. Requisitos
- Docker e Docker Compose (Recomendado) **OU** Python 3.12+

### 2. Configuração
1. Clone o repositório.
2. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```
3. Edite o `.env` e insira seu `TELEGRAM_TOKEN` e sua `GEMINI_API_KEY`.
   - *Nota: A `SECURITY_KEY` será gerada automaticamente no primeiro boot.*

### 3. Rodando com Docker (Recomendado)
```bash
docker-compose up -d --build
```

### 4. Rodando manualmente (venv)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Arquitetura
O projeto segue os princípios de **Clean Architecture / Hexagonal**:
- **Core:** Lógica de negócio e orquestração de sessões.
- **Ports:** Interfaces que definem os contratos do sistema.
- **Adapters:** Implementações tecnológicas (Telegram, Gemini, SQLite, Fernet).

## Licença
Este projeto é Open Source e distribuído sob a licença MIT.
