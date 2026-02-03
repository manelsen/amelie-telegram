# Arquitetura do Sistema - Amélie 👁️🌸

Este documento detalha as decisões arquiteturais e a estrutura técnica do projeto **Amélie**, um assistente multimodal para acessibilidade construído com foco em privacidade, resiliência e portabilidade.

---

## 1. Visão Geral
A Amélie utiliza o padrão de **Arquitetura Hexagonal (Ports and Adapters)**. O objetivo principal é isolar a inteligência central (lógica de negócio) das tecnologias externas (Telegram, Google Gemini, Banco de Dados), permitindo trocas de componentes com impacto zero no núcleo do sistema.

---

## 2. O Hexágono Central (Core)

O núcleo da aplicação reside em `core/`. Ele contém a lógica que não depende de ferramentas externas.

### 2.1. VisionService
É o orquestrador principal. Ele decide como um arquivo deve ser processado, gerencia a limpeza de texto para acessibilidade e coordena a blindagem de dados.

### 2.2. Fila de Processamento (Worker Queue)
Para garantir estabilidade e evitar bloqueios por excesso de requisições (429 Too Many Requests), a Amélie utiliza uma **Fila Global Assíncrona** (`asyncio.Queue`).
- Todas as mensagens entram em uma fila única.
- Um **Worker** em background processa um item por vez.
- Isso garante que o bot nunca sobrecarregue a API da IA, independente do número de usuários simultâneos.

---

## 3. Portos e Adaptadores (Ports & Adapters)

### 3.1. Messaging (Mensageria)
- **Porto (`MessagingPort`):** Define como o sistema deve enviar mensagens.
- **Adaptador (`TelegramAdapter`):** Implementa a comunicação via Telegram. Lida com o download de fotos, vídeos, áudios e documentos, convertendo-os em fluxos de bytes para o núcleo.

### 3.2. AI Model (Inteligência Artificial)
- **Porto (`AIModelPort`):** Define como fazer upload de arquivos e perguntas.
- **Adaptador (`GeminiAdapter`):** Utiliza o SDK `google-genai` para falar com o modelo **Gemini 2.5 Flash Lite**. Implementa a **File API** do Google para fazer upload único de arquivos pesados (vídeos/PDFs) e consultá-los via URI em cache.

### 3.3. Security (Segurança)
- **Porto (`SecurityPort`):** Define contratos para criptografia e descriptografia.
- **Adaptador (`FernetSecurityAdapter`):** Implementa criptografia simétrica **AES-256 (Fernet)**. É responsável por garantir que nenhum dado sensível saia da memória sem estar protegido.

### 3.4. Persistence (Banco de Dados)
- **Porto (`PersistencePort`):** Define como salvar sessões e preferências.
- **Adaptador (`SQLitePersistenceAdapter`):** Salva dados em um banco **SQLite** assíncrono. 

---

## 4. Privacidade e Blindagem de Dados

A Amélie foi desenhada sob o conceito de **"Cegueira do Gestor"** (Compliance com LGPD/GDPR):
- **Criptografia em Nível de Campo:** Os dados (URIs de arquivos, perguntas e respostas) são criptografados pelo `SecurityAdapter` **antes** de serem enviados para o banco de dados.
- **Resultado:** Se o arquivo `bot_data.db` for acessado por um terceiro ou pelo gestor da VPS, o conteúdo estará ilegível. Apenas o processo em execução com a chave mestra no `.env` pode decifrar os dados.

---

## 5. Resiliência e Robustez
- **Retentativas (Retry):** O adaptador da IA utiliza a biblioteca `tenacity` com estratégia de **Exponencial Backoff**. Se a API falhar momentaneamente, o sistema tenta novamente até 3 vezes antes de reportar erro.
- **Tratamento de Erros Hierárquico:** Distinção clara entre erros transientes (rede/cota) e erros permanentes (configuração), permitindo que o bot informe o usuário de forma amigável sem "morrer".

---

## 6. Fluxo de um Arquivo
1. **Entrada:** Usuário envia um vídeo no Telegram.
2. **Download:** O adaptador baixa os bytes do vídeo.
3. **Upload Único:** O núcleo pede ao adaptador da IA para fazer o upload. O vídeo é armazenado nos servidores do Google.
4. **Criptografia:** A URI retornada pelo Google é criptografada e salva no SQLite.
5. **Análise:** O Gemini processa o vídeo e retorna a audiodescrição.
6. **Limpeza:** O núcleo remove asteriscos e markdown para garantir que leitores de tela leiam o texto de forma limpa.
7. **Saída:** O usuário recebe a resposta em blocos de até 4.000 caracteres.

---

## 7. Estrutura de Arquivos
```text
vision-bot/
├── adapters/           # Implementações (Infraestrutura)
│   ├── messaging/      # Telegram
│   ├── persistence/    # SQLite
│   ├── security/       # AES-256
│   └── vision/         # Gemini 2.5 Flash Lite
├── core/               # Lógica de Negócio (Domínio)
│   ├── exceptions.py   # Exceções customizadas
│   └── service.py      # O Cérebro da Amélie
├── ports/              # Interfaces (Contratos)
│   └── interfaces.py
├── main.py             # Injeção de Dependência e Início
├── .env                # Segredos (Ignorado pelo Git)
├── Dockerfile          # Empacotamento
└── README.md           # Documentação de uso
```
