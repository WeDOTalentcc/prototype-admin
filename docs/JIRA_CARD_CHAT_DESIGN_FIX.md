# Card Jira: Correção de Design do Chat/Prompt LIA (ats_front)

**Projeto:** WeDOTalent ATS Frontend
**Tipo:** Bug / Design Debt
**Prioridade:** Alta
**Componente:** Chat LIA / Prompt Panel
**Repositório:** `WeDOTalent/ats_front` (branch `develop`)

---

## Resumo

O chat da LIA no prompt expandido (lado de vagas) apresenta problemas visuais significativos de design, formatação, tipografia e disposição das informações. Os balões de mensagem, fontes, cores e formatação de conteúdo estão desalinhados com o Design System LIA v4.2.1.

---

## Screenshot de Referência

![Chat com problemas](../attached_assets/Screen_Shot_2026-03-25_at_11.31.00_PM_1774492277682.png)

---

## Arquivos Afetados no Repositório

### Arquivos de componentes (Vue/Vuetify)

| Arquivo | Função | Problemas Identificados |
|---------|--------|------------------------|
| `features/prompt/BotMessage.vue` | Balão da mensagem da LIA | Cores, font-size, border-radius, espaçamento, renderização de conteúdo |
| `features/prompt/UserMessage.vue` | Balão da mensagem do usuário | Cor do balão (#00B8B8 vs #111827), border-radius, font-size |
| `features/prompt/prompt_input.vue` | Campo de entrada do chat | Cor de foco (#00B8B8 vs gray-900), botão send |
| `features/prompt/PromptHeader.vue` | Header do prompt expandido | Layout, badges, botões |
| `features/prompt/ExecutionTracker.vue` | Indicador de execução/pensamento | Animações, cores |
| `components/ui/chat/MessageContent.vue` | Parser e renderização do conteúdo (markdown, tabelas, listas) | Formatação de texto, bullet points, tabelas, código |
| `components/ui/chat/DomainChat.vue` | Container principal do chat por domínio | Layout geral, scroll, espaçamento |
| `components/ui/chat/StreamingMessage.vue` | Mensagens em streaming | Animação, formatação incremental |
| `components/ui/chat/MarkdownTable.vue` | Tabelas dentro de mensagens | Estilo das células, borders, fontes |
| `components/ui/chat/ChatCodeBlock.vue` | Blocos de código | Font mono, background, cores |

### Composables relacionados

| Arquivo | Função |
|---------|--------|
| `composables/useDomainMessages.ts` | Gestão de mensagens por domínio |
| `composables/useMessageStreaming.ts` | Streaming de mensagens |
| `composables/useLiaDomainConfig.ts` | Configuração visual por domínio |
| `stores/lia.ts` | Store Pinia da LIA |

---

## Problemas Identificados vs Design System LIA v4.2.1

### 1. Cores dos Balões

| Elemento | Atual (GitHub) | Esperado (DS v4.2.1) | Arquivo |
|----------|---------------|---------------------|---------|
| Balão Bot background | `#F8FAFB` (quase branco) | `#F3F4F6` (gray-100) ou `#F9FAFB` (gray-50) com borda `border-gray-200` | `BotMessage.vue` `.lia-msg-bubble--bot` |
| Balão User background | `#00B8B8` (teal) | `#111827` (gray-900) — cor primária do DS monocromático | `UserMessage.vue` `.lia-msg-bubble--user` |
| Avatar Bot background | `#E6F9F9` (teal claro) | `rgba(96,190,209,0.15)` — wedo-cyan 15% opacity | `BotMessage.vue` `.lia-msg-avatar--bot` |
| Avatar Bot icon color | `#00B8B8` (teal) | `#60BED1` (wedo-cyan) | `BotMessage.vue` `.lia-msg-avatar--bot svg` |
| Suggestion chip hover | `#00B8B8` border + `#E6F9F9` bg | `border-gray-900` + `bg-gray-50` | `BotMessage.vue` `.lia-suggestion-chip:hover` |
| Input focus ring | `#00B8B8` border + teal shadow | `border-gray-900` + `ring-1 ring-gray-900/10` | `prompt_input.vue` `.lia-input-wrapper:focus-within` |
| Send button background | `#00B8B8` | `#111827` (gray-900) | `prompt_input.vue` `.lia-btn-send` |
| Input icon color | `#00B8B8` | `#60BED1` (wedo-cyan) — apenas o ícone Brain da LIA | `prompt_input.vue` `.lia-input-icon` |

**Problema central:** O código usa `#00B8B8` (teal genérico) em vez das cores do DS: gray-900 para elementos primários e `#60BED1` (wedo-cyan) exclusivamente para elementos de IA/LIA.

### 2. Tipografia

| Elemento | Atual (GitHub) | Esperado (DS v4.2.1) | Arquivo |
|----------|---------------|---------------------|---------|
| Font-size mensagens | `13.5px` | `11px` (`text-[11px]`) — padrão universal LIA | `BotMessage.vue`, `UserMessage.vue` |
| Font-family | `inherit` (browser default) | `'Open Sans', sans-serif` explícito | Todos |
| Timestamp font-size | Não visível | `10px` `text-gray-400` | `BotMessage.vue` |
| Suggestion chips | `12px` | `11px` | `BotMessage.vue` `.lia-suggestion-chip` |
| Input placeholder | `13.5px` | `11px` | `prompt_input.vue` `.lia-input-field` |

**Nota:** A plataforma Replit usa `text-[11px]` como tamanho base para toda a UI. O produto GitHub usa `13.5px`, criando inconsistência visual.

### 3. Renderização de Conteúdo (MessageContent.vue)

| Problema | Descrição | Impacto Visual |
|----------|-----------|---------------|
| `asPlainText()` em BotMessage | Usa `div.innerHTML → textContent` que REMOVE toda formatação HTML | Bullet points viram texto corrido, tabelas perdem estrutura, negrito/itálico desaparecem |
| Markdown não renderizado | O `BotMessage.vue` chama `asPlainText()` em vez de usar `MessageContent.vue` | Conteúdo rico (tabelas, listas, código) exibido como texto puro |
| Caracteres Unicode mal renderizados | Emojis e caracteres especiais (📋, 🏢, 📍, 👤) misturados com texto | Layout quebrado com emojis desalinhados |
| Listas com bullet points | CSS de lista não aplicado — `v-list` sem estilização consistente | Items empilhados sem indentação |
| Tabelas dentro de mensagens | `MarkdownTable.vue` existe mas não é invocado pelo `BotMessage.vue` | Dados tabulares exibidos como texto corrido |

**Problema crítico:** O `BotMessage.vue` (line ~74) usa `asPlainText(message.content)` que converte TODO o HTML/markdown em texto puro. O componente `MessageContent.vue` que faz o parsing correto (tabelas, listas, código, imagens) existe em `components/ui/chat/` mas **não é usado** pelo `BotMessage.vue`.

### 4. Layout e Espaçamento

| Elemento | Atual (GitHub) | Esperado (DS v4.2.1) |
|----------|---------------|---------------------|
| Balão border-radius | `14px` (arredondado) | `8px` (`rounded-md`) — padrão do DS |
| Balão bot corner | `border-bottom-left-radius: 4px` | `border-bottom-left-radius: 2px` |
| Balão user corner | `border-bottom-right-radius: 4px` | `border-bottom-right-radius: 2px` |
| Avatar tamanho | `30px` | `28px` ou `32px` (múltiplo de 4) |
| Gap avatar-balão | `10px` | `8px` |
| Padding balão | `10px 14px` | `8px 12px` (mais compacto, alinhado com `text-[11px]`) |
| Max-width mensagem | `92%` | `85%` (melhor para telas largas) |
| Message bottom margin | `16px` | `12px` |

### 5. Funcionalidades Visuais Ausentes

| Feature | Presente no Replit | Presente no GitHub | Correção |
|---------|-------------------|-------------------|----------|
| Markdown rendering (bold, italic, code) | Sim (`.lia-markdown-content`) | Não (asPlainText remove) | Usar `MessageContent.vue` ou adicionar v-html com sanitização |
| Dark mode | Sim (`.dark` classes) | Parcial (apenas backgrounds) | Adicionar variáveis dark para todos os elementos |
| Tabelas formatadas | Sim (via HTML tables) | Componente existe mas não usado | Integrar `MessageContent.vue` no `BotMessage.vue` |
| Code blocks com syntax highlight | Sim (`JetBrains Mono`) | `ChatCodeBlock.vue` existe mas não usado | Integrar via `MessageContent.vue` |
| Scroll area custom | Sim (`custom-scrollbar` CSS) | Vuetify default | Adicionar scrollbar customizado |
| Score badges nas mensagens | Sim (5-band colors) | Não | Adicionar `v-chip` com cores por faixa |

---

## Correções Sugeridas

### Prioridade 1 — Crítico (Funcionalidade quebrada)

**1.1 Substituir `asPlainText()` por `MessageContent.vue` no BotMessage**

```vue
<!-- BotMessage.vue — ANTES -->
<span class="lia-msg-text">{{ asPlainText(message.content) }}</span>

<!-- BotMessage.vue — DEPOIS -->
<MessageContent :content="message.content" :metadata="message.metadata" />
```

Isso corrige: formatação de markdown, tabelas, listas, blocos de código, imagens e links.

**1.2 Corrigir cor do balão do usuário**

```css
/* UserMessage.vue — ANTES */
.lia-msg-bubble--user {
  background: #00B8B8;
  color: #fff;
}

/* UserMessage.vue — DEPOIS */
.lia-msg-bubble--user {
  background: #111827; /* gray-900 — cor primária DS */
  color: #fff;
  border-bottom-right-radius: 2px;
}
```

### Prioridade 2 — Alta (Inconsistência visual)

**2.1 Padronizar cores do avatar e ícone LIA**

```css
/* BotMessage.vue */
.lia-msg-avatar--bot {
  background: rgba(96, 190, 209, 0.15); /* wedo-cyan 15% */
}
.lia-msg-avatar--bot svg {
  color: #60BED1; /* wedo-cyan */
}
```

**2.2 Padronizar font-size para 11px**

```css
.lia-msg-bubble {
  font-size: 11px; /* DS v4.2.1 padrão */
  line-height: 1.6;
  font-family: 'Open Sans', sans-serif;
}
```

**2.3 Padronizar input field**

```css
.lia-input-wrapper:focus-within {
  border-color: #111827; /* gray-900 */
  box-shadow: 0 0 0 1px rgba(17, 24, 39, 0.1);
}
.lia-btn-send {
  background: #111827; /* gray-900 */
}
.lia-btn-send:hover {
  background: #1F2937; /* gray-800 */
}
```

### Prioridade 3 — Média (Refinamento visual)

**3.1 Ajustar border-radius e espaçamentos**

```css
.lia-msg-bubble {
  border-radius: 8px; /* rounded-md */
  padding: 8px 12px;
}
.lia-msg-bubble--bot {
  border-bottom-left-radius: 2px;
}
.lia-msg-bubble--user {
  border-bottom-right-radius: 2px;
}
.lia-msg {
  gap: 8px;
  margin-bottom: 12px;
  max-width: 85%;
}
```

**3.2 Suggestion chips alinhados com DS**

```css
.lia-suggestion-chip {
  font-size: 11px;
  font-family: 'Open Sans', sans-serif;
  border: 1px solid #E5E7EB; /* gray-200 */
  color: #374151; /* gray-700 */
}
.lia-suggestion-chip:hover {
  border-color: #111827; /* gray-900 */
  background: #F9FAFB; /* gray-50 */
  color: #111827;
}
```

---

## Referências

| Documento | Path |
|-----------|------|
| Design System v4.2.1 | `plataforma-lia/docs/design-system/00-design-system-v4.md` |
| Chat CSS (Replit — referência correta) | `plataforma-lia/src/components/pages/chat-page.css` |
| Chat Page (Replit — referência correta) | `plataforma-lia/src/components/pages/chat-page.tsx` |
| Inventário de Design | `docs/PRODUCT_DESIGN_INVENTORY.md` (seção 13.1 Chat LIA) |
| Vuetify Migration Plan | `plataforma-lia/docs/design-system/VUETIFY-MIGRATION-PLAN.md` |
| Vue Migration Skill | `.agents/skills/vue-migration-prep/SKILL.md` |

---

## Critérios de Aceite

- [ ] Balão do usuário com background `#111827` (gray-900)
- [ ] Balão da LIA renderizando markdown completo (tabelas, listas, negrito, código)
- [ ] Avatar da LIA com background `rgba(96,190,209,0.15)` e ícone `#60BED1`
- [ ] Font-size `11px` com `font-family: 'Open Sans', sans-serif` em todos os elementos
- [ ] Input com focus ring `gray-900` e botão send `gray-900`
- [ ] Suggestion chips com hover `border-gray-900` + `bg-gray-50`
- [ ] Border-radius `8px` (rounded-md) nos balões
- [ ] Dark mode funcional em todos os elementos do chat
- [ ] Caracteres especiais e emojis renderizados corretamente
- [ ] Tabelas dentro de mensagens formatadas com borders e alinhamento
