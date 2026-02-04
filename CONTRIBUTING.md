# Contribuindo para a Amélie 🌸

Ficamos muito felizes com o seu interesse em ajudar a tornar a Amélie ainda melhor! Este é um projeto focado em acessibilidade e privacidade.

## Diretrizes de Desenvolvimento

### 1. Arquitetura Hexagonal (Ports & Adapters)
O projeto segue rigorosamente a separação entre o **Core** (lógica de negócio) e os **Adapters** (infraestrutura).
- Se quiser adicionar uma nova plataforma (ex: Discord), crie um novo adaptador em `adapters/messaging/`.
- Se quiser trocar o modelo de IA, crie em `adapters/vision/`.
- **Nunca** coloque lógica de rede ou de banco de dados dentro da pasta `core/`.

### 2. Documentação (Docstrings)
Todas as classes e funções públicas **devem** ser documentadas seguindo o padrão Google/Python. Documentação não é opcional, é um ato de carinho com quem mantém o código.

### 3. Acessibilidade em Primeiro Lugar
- As respostas da IA devem ser limpas.
- Caracteres de Markdown (`*`, `#`, `_`) devem ser evitados ou tratados no `VisionService` para não confundir leitores de tela.

### 4. Segurança e Privacidade
- Siga o princípio da "Cegueira do Gestor".
- Dados sensíveis devem ser criptografados via `SecurityPort` antes de tocar a camada de persistência.

## Como começar
1. Faça um Fork do projeto.
2. Crie uma branch para sua funcionalidade (`git checkout -b feat/nova-funcao`).
3. Certifique-se de que o `.env` está configurado corretamente (use o `.env.example`).
4. Abra um Pull Request detalhando suas mudanças.

Obrigado por ajudar a ampliar a visão do mundo! 👁️✨
