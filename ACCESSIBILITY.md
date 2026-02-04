# Manual de Acessibilidade - Amélie 👁️🌸

Este documento descreve as diretrizes, decisões técnicas e a filosofia por trás da **Amélie**, visando garantir a melhor experiência possível para pessoas com deficiência visual e usuários de leitores de tela (como TalkBack, VoiceOver, NVDA e JAWS).

---

## 1. Filosofia: "Visão sem Barreiras"
A Amélie não é apenas um bot que usa IA; ela é uma ponte sensorial. Nossa filosofia baseia-se em:
- **Verbosidade Útil:** Descrições detalhadas o suficiente para criar uma imagem mental, sem ruídos desnecessários.
- **Padrão Cronológico:** Vídeos são descritos segundo a linha do tempo das ações.
- **Privacidade como Respeito:** Garantir que dados sensíveis de usuários (que muitas vezes enviam fotos de documentos ou ambientes privados) estejam 100% blindados.

---

## 2. Decisões Técnicas de Interface

### 2.1. Limpeza de Texto (Markdown Zero)
Leitores de tela costumam ler caracteres de formatação como "asterisco", "cerquilha" ou "sublinhado" em voz alta, o que interrompe o fluxo de compreensão. 
- **Decisão:** O código da Amélie remove automaticamente todos os asteriscos (`*`), hashtags (`#`) e crases (`` ` ``) das respostas da IA.
- **Substituição:** Caracteres como o sublinhado (`_`) são convertidos em espaços para evitar que o leitor tente ler palavras grudadas.

### 2.2. Divisão de Mensagens
O Telegram impõe um limite de 4.096 caracteres por mensagem.
- **Decisão:** Para evitar que informações sejam cortadas, a Amélie divide automaticamente textos longos em múltiplas mensagens sequenciais, garantindo que o usuário ouça a análise completa sem interrupções de "texto truncado".

---

## 3. Guia de Funcionalidades para Acessibilidade

### 3.1. Audiodescrição de Imagens
- **Modo Padrão (/longo):** Foca em cores, texturas, posicionamento de objetos e expressões faciais.
- **Modo Rápido (/curto):** Otimizado para uma identificação imediata do objeto principal (máximo 200 caracteres).

### 3.2. Audiodescrição de Vídeos
- **Modo Legenda (/legenda):** Gera uma lista cronológica (ex: "00:05 - Homem acena com a mão"). Ideal para entender o ritmo das ações.
- **Modo Narrativo (/completo):** Descreve o vídeo como uma cena cinematográfica contínua.

### 3.3. Análise de Documentos (PDF/MD)
A Amélie converte tabelas e listas complexas em prosa ou listas simples de texto puro, facilitando a leitura linear pelos softwares de apoio.

---

## 4. Como Testar a Acessibilidade do Bot

Para desenvolvedores ou auditores, recomendamos testar a Amélie seguindo estes passos:

1. **Ative o Leitor de Tela:** Use o **TalkBack** (Android) ou **VoiceOver** (iOS).
2. **Envio de Mídia:** Verifique se as mensagens intermediárias (como o aviso da LGPD) possuem botões claros e se o foco do leitor cai corretamente no texto do manifesto.
3. **Leitura da Resposta:** Ouça a descrição completa de uma imagem. Se você ouvir a palavra "asterisco", o filtro de limpeza precisa de ajustes.
4. **Perguntas Contextuais:** Teste a função de chat perguntando detalhes ("O que está no canto direito?"). A resposta deve manter o mesmo padrão de limpeza.

---

## 5. Contribuições
Se você encontrar algum padrão de fala da Amélie que seja confuso ou difícil de navegar via áudio, por favor, abra uma *Issue* com a tag `accessibility`. Este é um projeto em constante evolução.

*Amélie: Enxergando a beleza nos pequenos detalhes.*
