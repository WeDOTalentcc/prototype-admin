# Análise Comparativa: Chats LIA vs. Padrões de Mercado

**Data:** Abril 2026  
**Autor:** Auditoria automatizada Playwright  
**Versão da plataforma:** LIA v4.x  

---

## 1. Contexto

A plataforma LIA possui 4 interfaces de chat distintas:

| Interface | Rota | Componente Principal | Modo |
|---|---|---|---|
| Chat Principal | `/chat` | `LiaChatShell` (FullPageShell) | full-page |
| Chat Flutuante/Sidebar | Qualquer página | `LiaChatPanel` | dialog fixed |
| Chat Expandido/SuperPrompt | Ícone LIA expandido | `LiaSuperPrompt` | modal overlay |
| Chat Wizard/Vagas | `/vagas/nova` | `LiaChatShell` (InlineLeft) | inline-left |

---

## 2. Critérios de Comparação com Padrões de Mercado

### Referências de mercado analisadas:
- **ChatGPT** (chat.openai.com) — padrão de UX para LLMs
- **Claude** (claude.ai) — interface minimalista
- **Gemini** (gemini.google.com) — interface Google Material
- **Manus** — ferramenta de agentes AI

---

## 3. Análise por Critério

### 3.1 Posição do Input (Bottom Fixed)

| Plataforma | Posição do Input | Fixo no Scroll? |
|---|---|---|
| ChatGPT | Bottom center, fixo | ✅ Sim |
| Claude | Bottom center, fixo | ✅ Sim |
| Gemini | Bottom center, fixo | ✅ Sim |
| **LIA /chat** | Bottom, `flex-shrink-0` | ✅ Sim (OK) |
| **LIA Flutuante** | Bottom do painel flutuante | ✅ Sim (OK) |
| **LIA SuperPrompt** | Bottom do modal | ✅ Sim (OK) |

**Status:** ✅ CONFORME — Todos os chats LIA fixam o input no rodapé.

---

### 3.2 Alinhamento dos Balões de Mensagem

| Plataforma | Usuário | Assistente |
|---|---|---|
| ChatGPT | Direita (gray bg) | Esquerda (sem bg, full width) |
| Claude | Direita (light bg) | Esquerda (full width, sem bg) |
| Gemini | Direita | Esquerda |
| **LIA Chat Principal** | `justify-start` (⚠️ INVERTIDO!) | `justify-end` (⚠️ INVERTIDO!) |
| **LIA Chat Flutuante** | `justify-end` ✅ | `justify-start` ✅ |
| **LIA SuperPrompt** | `justify-end` ✅ | `justify-start` ✅ |

**BUG CRÍTICO DETECTADO no Chat Principal:**

No componente `ChatMessageList.tsx` (linha 71):
```tsx
className={`flex ${message.sender === "lia" ? "justify-end" : "justify-start"}`}
```

O alinhamento está **INVERTIDO** em relação ao padrão de mercado:
- `message.sender === "lia"` → `justify-end` → LIA aparece À DIREITA ❌
- `message.sender === "user"` → `justify-start` → Usuário aparece À ESQUERDA ❌

**Padrão correto:**
- Usuário → `justify-end` (direita)
- LIA → `justify-start` (esquerda)

**Nota:** O `message-bubble.tsx` está correto (LIA `justify-end` = direita com Brain icon, mas o código usa `isLia ? "justify-end" : "justify-start"` também de forma invertida em relação à UX esperada).

---

### 3.3 Presença de Avatar

| Plataforma | Avatar Usuário | Avatar Assistente |
|---|---|---|
| ChatGPT | Ícone circular (letra) | Logo ChatGPT |
| Claude | Inicial do nome | Ícone Claude |
| Gemini | Foto Google Account | Ícone Gemini |
| **LIA /chat (ChatMessageList)** | Avatar com `AvatarFallback` "AS" | `LIAIcon` (ícone circular) |
| **LIA Flutuante** | `User` icon (lucide) circular | `Brain` icon cyan |
| **LIA SuperPrompt** | `User` icon circular | `Brain` icon cyan |

**BUG:** O avatar do usuário no Chat Principal sempre exibe "AS" (hardcoded: `<AvatarFallback>AS</AvatarFallback>`), não usa o nome/foto real do usuário logado.

---

### 3.4 Botões de Controle do Chat

| Funcionalidade | ChatGPT | Claude | Gemini | LIA /chat | LIA Flutuante | LIA SuperPrompt |
|---|---|---|---|---|---|---|
| Novo Chat | ✅ | ✅ | ✅ | ✅ (via LiaChatHeader) | ✅ | ✅ |
| Limpar Mensagens | ❌ | ❌ | ❌ | ✅ (Eraser) | ✅ (Eraser) | ✅ (Eraser) |
| Fechar/Minimizar | N/A (SPA) | N/A | N/A | ✅ (X) | ✅ (X) | ✅ (Minimize2 + X) |
| Busca na conversa | ✅ (Ctrl+F) | ✅ | ❌ | ✅ (Search icon) | ❌ | ❌ |
| Histórico | ✅ (sidebar) | ✅ (sidebar) | ✅ | ✅ (History btn) | ✅ (History btn) | ✅ (History btn) |
| Expandir | N/A | N/A | N/A | N/A (já é full-page) | ✅ (Maximize2) | ✅ (já expandido) |

**BUG DETECTADO:** O Chat Principal em `/chat` usa `LiaChatShell` com `FullPageShell` e usa `LiaChatHeader`, que TEM os botões de limpar/fechar. Porém, o componente `LegacyChatPage` (que é exportado como `ChatPage`) tem sua própria UI e **não usa LiaChatHeader** — ele tem apenas Search e Centro de Controle no header.

---

### 3.5 Formatação de Markdown

| Plataforma | Bold | Italic | Listas | Código | Headers | Links |
|---|---|---|---|---|---|---|
| ChatGPT | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Claude | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Gemini | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **LIA (parseChatMarkdown)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Status:** ✅ CONFORME — `parseChatMarkdown` implementa todos os elementos markdown básicos.

**NOTA:** O `ChatMessageList.tsx` em `/chat` usa `sanitizeHtml(onHighlightSearchTerm(...))` sem passar pelo `parseChatMarkdown`, então o markdown pode não ser renderizado corretamente no Chat Principal legado.

---

### 3.6 Comportamento de Scroll (Auto-scroll)

| Plataforma | Auto-scroll em nova mensagem | "Nova mensagem" indicator |
|---|---|---|
| ChatGPT | ✅ | ✅ (scroll to bottom btn) |
| Claude | ✅ | ✅ |
| Gemini | ✅ | ✅ |
| **LIA /chat** | ✅ (`messagesEndRef.scrollIntoView`) | ✅ (`newMessageIndicator` button) |
| **LIA Flutuante** | ✅ | ❌ |
| **LIA SuperPrompt** | ✅ | ❌ |

**Status:** Parcialmente conforme. Chat Principal tem indicador de nova mensagem, Flutuante e SuperPrompt não têm.

---

### 3.7 Empty State Design

| Plataforma | Empty State |
|---|---|
| ChatGPT | Grid de sugestões (4 cards) + barra de busca |
| Claude | Tela branca limpa com input proeminente |
| Gemini | Saudação + grid de sugestões |
| **LIA /chat (LegacyChatPage)** | "Oi, eu sou a LIA" + PromptSuggestionsDock |
| **LIA Chat Flutuante** | EmptyState com sugestões dinâmicas da API |
| **LIA SuperPrompt** | Grid 2x2 de sugestões categorizadas por cor |

**Status:** ✅ CONFORME com padrões de mercado. Os 3 chats têm empty state funcional.

---

### 3.8 Responsividade Mobile

| Plataforma | Mobile Support |
|---|---|
| ChatGPT | ✅ Responsivo, app nativo |
| Claude | ✅ Responsivo |
| Gemini | ✅ Responsivo, app nativo |
| **LIA /chat** | ⚠️ Não testado em produção |
| **LIA Flutuante** | ⚠️ Panel 420px pode não caber em mobile (390px) |

**BUG POTENCIAL:** O painel flutuante `LiaChatPanel` tem `w-[420px] min-w-[420px]` fixos — em mobile (390px de largura), o painel transbordaria a tela.

---

## 4. Bugs e Inconsistências Consolidados

### 🔴 CRÍTICOS

| ID | Local | Descrição | Impacto |
|---|---|---|---|
| BUG-001 | `ChatMessageList.tsx:71` | Alinhamento dos balões INVERTIDO no Chat Principal legado — LIA aparece à direita, usuário à esquerda | Experiência confusa, contrária ao padrão de mercado |
| BUG-002 | `LiaChatPanel.tsx:84` | Painel flutuante com `w-[420px] min-w-[420px]` fixos não funciona em mobile (390px) | Chat inutilizável em dispositivos mobile |

### 🟠 ALTOS

| ID | Local | Descrição | Impacto |
|---|---|---|---|
| BUG-003 | `ChatMessageList.tsx:92-98` | Avatar do usuário hardcoded como "AS" — não usa dados reais do usuário logado | UX não personalizada |
| BUG-004 | `/chat` (LegacyChatPage) | Chat Principal não usa `LiaChatHeader` — faltam botões de limpar/fechar/histórico que os outros chats possuem | Inconsistência de UX entre chats |
| BUG-005 | `ChatMessageList.tsx` em `/chat` | `sanitizeHtml()` usado sem `parseChatMarkdown()` — markdown pode não ser renderizado no chat legado | Texto com `**bold**`, `# header` visíveis |

### 🟡 MÉDIOS

| ID | Local | Descrição | Impacto |
|---|---|---|---|
| BUG-006 | `LiaChatInput.tsx` | Input do chat flutuante usa `<input type="text">` simples sem auto-resize, enquanto `ChatInputBar.tsx` usa `<textarea>` com auto-resize | Inconsistência de UX — difícil digitar textos longos no flutuante |
| BUG-007 | `LiaSuperPrompt.tsx`, `LiaChatMessageList.tsx` | Sem indicador "Nova mensagem" quando usuário está scrollado para cima | Usuário pode perder mensagens da LIA |
| BUG-008 | Chat Principal input | Relatos de que o chat trava ao digitar — possível re-render excessivo em `useChatPageCore` | Perda de foco/congelamento do input |

### 🔵 BAIXOS

| ID | Local | Descrição | Impacto |
|---|---|---|---|
| BUG-009 | `LiaChatMessageList.tsx:77` | Container `role="status" aria-live="polite" aria-label="Carregando..."` sempre presente, mesmo quando não está carregando | Acessibilidade incorreta |
| BUG-010 | `LiaSuperPrompt.tsx:202` | Uso excessivo de `inline styles` (23 ocorrências documentadas com TODO) | Manutenção difícil, inconsistência com design tokens |
| BUG-011 | `ChatMessageList.tsx:113` | Nome do usuário hardcoded como "Ana Silva" | Dados estáticos em produção |

---

## 5. Resumo Executivo

### Pontos Fortes ✅
1. `parseChatMarkdown` robusto — suporta todos os elementos markdown básicos
2. `cleanAgentResponse` eficaz — remove `<thought>`, JSON blocks, etc.
3. Auto-scroll implementado nos principais chats
4. Empty state com sugestões dinâmicas em todos os chats
5. Botões de controle bem implementados na `LiaChatHeader`
6. Input fixo no rodapé em todos os modos

### Principais Problemas ❌
1. **Alinhamento de balões invertido** no Chat Principal legado (BUG-001) — CRÍTICO
2. **Chat Principal não tem botões de controle** que os outros chats têm (BUG-004)
3. **Painel flutuante não é responsivo** para mobile (BUG-002)
4. **Input inconsistente** — textarea vs. input simples entre os chats (BUG-006)
5. **Avatar hardcoded** "AS" e nome "Ana Silva" (BUG-003, BUG-011)

### Recomendações Prioritárias

1. **[URGENTE]** Corrigir alinhamento dos balões no `ChatMessageList.tsx` — inverter `justify-end/justify-start`
2. **[ALTO]** Migrar `/chat` para usar `LiaChatShell` (FullPageShell) em vez de `LegacyChatPage` — assim herda todos os botões de controle
3. **[ALTO]** Investigar e corrigir trava ao digitar no Chat Principal — possível profiling de renders
4. **[MÉDIO]** Trocar `<input>` por `<textarea>` no `LiaChatInput.tsx` para suportar auto-resize
5. **[MÉDIO]** Adicionar responsividade mobile ao `LiaChatPanel.tsx` — remover `min-w-[420px]` fixo
6. **[BAIXO]** Usar dados reais do usuário logado no avatar e nome

---

## 6. Matriz de Paridade com Mercado

| Feature | ChatGPT | Claude | Gemini | LIA Score |
|---|---|---|---|---|
| Input fixo no rodapé | ✅ | ✅ | ✅ | ✅ 100% |
| Balões alinhados corretamente | ✅ | ✅ | ✅ | ⚠️ 66% (2/3 chats OK) |
| Markdown renderizado | ✅ | ✅ | ✅ | ⚠️ 75% |
| Empty state com sugestões | ✅ | ❌ | ✅ | ✅ 100% |
| Histórico de conversas | ✅ | ✅ | ✅ | ✅ 100% |
| Auto-scroll | ✅ | ✅ | ✅ | ✅ 100% |
| Avatar do usuário real | ✅ | ✅ | ✅ | ❌ 0% |
| Responsividade mobile | ✅ | ✅ | ✅ | ❌ 33% |
| Botões de controle | ✅ | ✅ | ✅ | ⚠️ 66% |
| Typing indicator | ✅ | ✅ | ✅ | ✅ 100% |

**Score Geral LIA: ~74%** — Funcional mas com inconsistências importantes a corrigir.

---

## 7. Cobertura de Testes Automatizados

### Playwright E2E (63 testes totais)

| Suite | Arquivo | Testes | Interface Coberta |
|---|---|---|---|
| Chat Principal | `chat-principal.spec.ts` | 9 testes | `/chat` (FullPageShell) |
| Chat Flutuante | `chat-flutuante.spec.ts` | 13 testes | `LiaChatPanel` (qualquer página) |
| Chat Expandido/SuperPrompt | `chat-superprompt.spec.ts` | 11 testes | `LiaSuperPrompt` (modal overlay) |
| Chat Wizard Inline | `chat-wizard.spec.ts` | 10 testes | `LiaChatShell` InlineLeft (`/vagas/nova`) |
| Formatação/Markdown | `chat-formatacao.spec.ts` | 4 testes | Chat Flutuante + Principal |
| Consistência Cross-Chat | `chat-consistencia-cross.spec.ts` | 6 testes | Todos os chats |
| Comportamento do Input | `chat-comportamento-input.spec.ts` | 10 testes | Chat Flutuante + Principal |

### Cobertura por Interface

| Interface | Testes Dedicados | Testes Compartilhados | Total |
|---|---|---|---|
| Chat Principal `/chat` | 8 | 14 | ~22 |
| Chat Flutuante | 11 | 16 | ~27 |
| Chat Expandido/SuperPrompt | 11 | 6 | ~17 |
| Chat Wizard (`/vagas/nova`) | 10 | 6 | ~16 |

### Vitest Unit Tests (24 testes)

| Módulo | Testes | Status |
|---|---|---|
| `cleanAgentResponse` | 17 | ✅ PASSA |
| `parseChatMarkdown` | 3 | ✅ PASSA |
| `escapeHtml` | 4 | ✅ PASSA |

**Total: 87 testes (63 E2E + 24 unitários)**
