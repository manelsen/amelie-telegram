# Changelog - Amélie 👁️🌸

## [1.0.0] - 2026-02-03
### Adicionado
- Identidade visual e rebatismo para **Amélie**.
- Sistema de consentimento LGPD com botões interativos no `/start`.
- Banco de dados SQLite persistente para sessões e preferências.
- **Blindagem AES-256:** Criptografia ponta-a-ponta na infraestrutura.
- Comandos de usuário: `/ajuda`, `/curto`, `/longo`, `/legenda`, `/completo`.
- Suporte multimodal completo: Imagens, Vídeos, PDFs, Markdown e Áudios/Voz.
- Fila de processamento global para estabilidade da API.
- Arquitetura Hexagonal robusta.
- Dockerização e documentação técnica completa.

### Corrigido
- Falha na "memória" do bot: o histórico agora é enviado corretamente para o Gemini.
- Erros de compatibilidade com o novo SDK `google-genai`.

---
*Nota: Este projeto nasceu hoje e evoluiu de um simples script de visão para uma plataforma de acessibilidade completa.*
