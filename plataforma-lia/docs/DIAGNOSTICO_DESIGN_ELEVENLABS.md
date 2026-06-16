# Diagnóstico de Design: LIA vs ElevenLabs Style

**Data:** 09/04/2026  
**Objetivo:** Comparar o design atual da plataforma LIA com o estilo visual da ElevenLabs e identificar oportunidades de melhoria para tornar a interface mais limpa, organizada e menos densa.

---

## 1. Resumo Executivo

| Dimensão | ElevenLabs | LIA Atual | Gap |
|----------|-----------|-----------|-----|
| **Densidade** | Baixa — muito espaço branco | Alta — informação compactada | ALTO |
| **Tipografia base** | 14-16px | 11-12px | ALTO |
| **Sidebar** | Limpa, 6-8 itens, espaçada | 7 itens + seções densas | MÉDIO |
| **Espaçamento** | Generoso (24-48px entre seções) | Compacto (8-16px entre seções) | ALTO |
| **Cards** | Bordas sutis, padding amplo | Bordas finas, padding menor | MÉDIO |
| **Filtros** | Chips horizontais clean | Mix de pills e underline tabs | MÉDIO |
| **Empty states** | Ilustrações com mensagem clara | Básicos, sem ilustrações | BAIXO |
| **Header da página** | Título grande + breadcrumb + 1 CTA | Título + tabs + múltiplos CTAs | MÉDIO |
| **Paleta de cores** | Quase monocromático (preto/cinza/branco) | 90% mono + cyan/green accents | BAIXO |
| **Ícones** | 20px, stroke fino, espaçados | 16px, compactos | MÉDIO |

**Score geral de alinhamento: ~45%** — A paleta de cores e a filosofia monocromática estão alinhadas, mas a densidade, tipografia e espaçamento são significativamente diferentes.

---

## 2. Análise Detalhada por Dimensão

### 2.1 Sidebar

**ElevenLabs:**
- Fundo branco limpo, sem borda lateral visível
- Logo + seletor de workspace no topo
- Seções agrupadas por categoria (Configure, Monitor, Deploy) com labels em ALL CAPS cinza claro, font ~10px
- Itens de menu: font 14px, font-weight 400/500, padding vertical ~10-12px
- Ícone + texto, espaçamento generoso entre itens (~8px gap)
- Item ativo: fundo cinza sutil (`#F5F5F5`), font-weight 500, sem borda
- Hover: fundo cinza muito sutil
- Ação "+" ao lado de itens criáveis (Agents, Voices)
- Footer: "Invite team members" discreto

**LIA Atual:**
- Fundo branco com borda direita sutil
- Logo WeDO grande no topo
- Seções: RECRUTAMENTO, OPERACIONAL, CONFIGURAÇÃO em caps
- Itens: font 11px (`text-base-ui`), padding `py-2 px-2`, min-height 40px
- Ícones 16px (`w-4 h-4`)
- Item ativo: `bg-lia-bg-tertiary` + font-semibold
- Footer: ícones de busca, settings, tema, ajuda

**Oportunidades:**
1. **Aumentar font para 13-14px** nos itens do menu
2. **Aumentar padding vertical** para 12px entre itens
3. **Aumentar ícones** para 18-20px
4. **Simplificar footer** — mover busca e settings para o header
5. **Reduzir logo** — usar versão compacta do WeDO
6. **Adicionar "+" buttons** ao lado de itens criáveis (Vagas)

---

### 2.2 Header da Página

**ElevenLabs:**
- Breadcrumb no topo (ícone + "Voices > Explore"), font 14px cinza
- Título grande abaixo: "Conversation history" / nenhum — só breadcrumb
- Barra de busca full-width com bordas arredondadas
- CTA primário isolado à direita ("+ Create Voice"), botão preto pill
- Header bar com ícones: Feedback, Docs, Ask, notificações, avatar

**LIA Atual:**
- Título com ícone (ex: "Funil de Talentos" com Users icon)
- Tabs imediatamente abaixo do título
- Múltiplos CTAs (Novo Candidato, Filtros, etc)
- Sem breadcrumb
- Header top bar: notificação + avatar + "Centro de Controle"

**Oportunidades:**
1. **Adicionar breadcrumb** no topo (seção > subseção)
2. **Separar título dos tabs** com mais espaçamento (24px vs 8px atual)
3. **Limitar CTAs** a 1 botão primário por página
4. **Barra de busca** mais proeminente e centralizada
5. **Aumentar font do título** para 20-24px (atual é ~16-18px)

---

### 2.3 Tipografia

**ElevenLabs:**
- Font base: ~14px para texto geral
- Labels de seção: 12px, font-weight 500, gray claro, uppercase
- Títulos de card: 14-16px, font-weight 600
- Descrições: 13-14px, font-weight 400, gray médio
- Line-height generoso: 1.5-1.6

**LIA Atual (Design Tokens v4.0):**
- Font base: 11px (`text-base-ui: 0.6875rem`)
- xs: 12px (usado para quase tudo)
- sm: 14px (raramente usado)
- micro: 10px (labels, captions)
- Line-height: 1.2-1.5

**Oportunidades:**
1. **Aumentar `text-base-ui`** de 11px para 13px
2. **Aumentar `text-xs`** de 12px para 13px (ou usar como `sm`)
3. **Usar 14px como padrão** para corpo de texto
4. **Títulos h2** de 18px para 20-22px
5. **Line-height padrão** de 1.5 para 1.6
6. **Reduzir uso de `text-micro` (10px)** — muito pequeno para legibilidade

---

### 2.4 Espaçamento e Densidade

**ElevenLabs:**
- Padding de página: ~32-48px horizontal
- Espaço entre seções: 32-48px
- Cards com padding interno: 20-24px
- Gap entre cards: 16-24px
- Margem do conteúdo ao sidebar: ~24px
- "Ar" abundante — conteúdo respira

**LIA Atual:**
- Padding de página: 16px (`px-4 pt-3`)
- Espaço entre seções: 8-16px
- Cards com padding: 12px (`p-3`) a 16px (`p-4`)
- Gap entre cards: 8-12px
- Conteúdo colado nas bordas

**Oportunidades:**
1. **Padding de página**: aumentar de `px-4` para `px-6` ou `px-8`
2. **Espaçamento entre seções**: de 8-16px para 24-32px
3. **Padding de cards**: de `p-3/p-4` para `p-5/p-6`
4. **Gap entre cards**: de 8-12px para 16-20px
5. **Adicionar `max-w-[1200px] mx-auto`** para centralizar conteúdo em telas grandes

---

### 2.5 Cards e Componentes

**ElevenLabs:**
- Cards com borda `1px solid #E5E7EB`, radius 12px
- Hover: borda escurece levemente, sem shadow
- Cards de feature (Voices > Handpicked): fundo escuro com arte, radius 16px
- Cards de integração: borda + ícone colorido + nome + descrição
- Sem sombras — tudo flat com bordas

**LIA Atual:**
- Cards: `border border-lia-border-subtle rounded-md` (8px)
- Hover em interactive: `hover:border-lia-border-default`
- Cards no Chat: 6 cards de ação em grid 2x3, com ícone cyan
- Cards no Agent Studio: grid com ícone + título + descrição

**Oportunidades:**
1. **Aumentar border-radius** de 8px (`rounded-md`) para 12px (`rounded-lg`)
2. **Padding interno** de cards: aumentar para 20-24px
3. **Hover mais sutil** — apenas border color, sem shadow
4. **Cards de feature** poderiam ter visual mais rico (background gradient)
5. **Ícones em cards** maiores: de 16px para 24px

---

### 2.6 Filtros e Busca

**ElevenLabs:**
- Barra de busca: full-width, borda cinza, radius 8px, height ~44px
- Chips de filtro: pills horizontais com ícone, font 14px, gap 8px
- Botão "Filters" separado à direita da busca
- Layout limpo: busca → chips → conteúdo

**LIA Atual:**
- Busca integrada em headers ou tables
- Tabs underline/pill para navegação
- Filtros em dropdowns
- Múltiplos controles na mesma linha

**Oportunidades:**
1. **Busca mais proeminente** — full-width, maior (height 40-44px)
2. **Chips de filtro** horizontais abaixo da busca (ao invés de dropdowns)
3. **Separar busca de filtros** visualmente
4. **Input de busca com ícone lupa** à esquerda (padrão ElevenLabs)

---

### 2.7 Empty States

**ElevenLabs:**
- Ícone ilustrado centralizado (ex: chat bubble para "No conversations")
- Título em bold: "No results"
- Descrição em cinza: "No conversations were found."
- Limpo e informativo

**LIA Atual:**
- Básicos com texto e ícones simples
- Sem ilustrações dedicadas
- Funcionais mas sem polish

**Oportunidades:**
1. **Adicionar ilustrações** custom para empty states
2. **Título + descrição + CTA** em empty states
3. **Centralizar** verticalmente no espaço disponível

---

### 2.8 Botões

**ElevenLabs:**
- Primário: fundo preto, texto branco, radius 8px (ou pill/full), padding horizontal 16-20px
- CTA principal sempre à direita, com ícone "+"
- Ghost buttons para ações secundárias
- Tamanho: height ~36-40px, font 14px

**LIA Atual:**
- Primário: preto (`bg-lia-btn-primary-bg`), radius 8px, `px-4 py-2`
- Font: `text-xs` (12px) com `font-semibold`
- Ghost e outline variants disponíveis
- Tamanhos menores que ElevenLabs

**Oportunidades:**
1. **Font de botões**: de 12px para 13-14px
2. **Height de botões**: padronizar em 36-40px
3. **CTAs primários**: considerar `rounded-full` (pill) para o botão principal
4. **Reduzir número de botões** visíveis — usar menus "..." para ações secundárias

---

## 3. Análise por Página

### 3.1 Chat LIA (Home)
**Score: 55%** — Layout mais próximo do ElevenLabs

| Aspecto | Status | Nota |
|---------|--------|------|
| Cards de ação centralizados | OK | Grid 2x3 clean |
| Tipografia do greeting | OK | Grande e legível |
| Ícones dos cards | MELHORAR | Muito pequenos, cor cyan distrai |
| Input de chat | OK | Full-width, boa posição |
| Espaçamento geral | MELHORAR | Cards poderiam ter mais padding |

### 3.2 Vagas (Jobs)
**Score: 35%**

| Aspecto | Status | Nota |
|---------|--------|------|
| Tabela de dados | MELHORAR | Muito densa, fonts 10-12px |
| Header | MELHORAR | Muitos controles, sem hierarquia |
| Filtros | MELHORAR | Poderiam ser chips horizontais |
| Espaçamento | MELHORAR | Tudo compactado |

### 3.3 Funil de Talentos (Candidatos)
**Score: 35%**

| Aspecto | Status | Nota |
|---------|--------|------|
| Tabela densa | MELHORAR | Avatares 36px, text 12px, tudo apertado |
| Tabs | OK | Pill tabs alinhados com DS v4 |
| Header | MELHORAR | Título + tabs + CTAs muito juntos |
| Score badges | OK | Coloridos e informativos |

### 3.4 Agent Studio
**Score: 50%**

| Aspecto | Status | Nota |
|---------|--------|------|
| Layout geral | OK | Grid de cards, limpo |
| Cards de templates | MELHORAR | Poderiam ter mais padding e radius maior |
| Seção "Como funciona" | OK | 4 passos claros |
| Tipografia | MELHORAR | Fonts pequenas nos cards |

### 3.5 Bancos de Talentos
**Score: 40%**

| Aspecto | Status | Nota |
|---------|--------|------|
| Grid de cards | OK | Layout em grid |
| Densidade | MELHORAR | Cards muito próximos |
| Visual | MELHORAR | Poderiam ter ícones maiores |

---

## 4. Plano de Ação (Priorizado por Impacto)

### Fase 1: Quick Wins (Alto impacto, baixo esforço)
1. **Aumentar font base** de 11px para 13px (`text-base-ui`)
2. **Aumentar padding de página** de `px-4` para `px-6`
3. **Aumentar espaçamento entre seções** para 24px mínimo
4. **Aumentar border-radius** de cards de 8px para 12px
5. **Sidebar: font de 11px para 13px**, padding vertical de itens

### Fase 2: Refinamentos Estruturais (Médio esforço)
6. **Redesign do header** de cada página: breadcrumb + título + 1 CTA
7. **Barra de busca** full-width e proeminente em páginas de listagem
8. **Chips de filtro** horizontais (substituir dropdowns)
9. **Tabelas menos densas**: row height +4px, font +1px
10. **Empty states** com ilustrações e CTAs

### Fase 3: Polish (Maior esforço)
11. **Sidebar redesign completo** — mais espaçada, ícones maiores
12. **Cards de feature** com visuais mais ricos
13. **Animações sutis** em transições de página
14. **Responsividade** — max-width para conteúdo em telas grandes
15. **Dark mode** alinhado com contraste ElevenLabs

---

## 5. Tokens Específicos a Alterar

```typescript
// ANTES (atual)
fontSize: {
  'base-ui': '0.6875rem',  // 11px
  xs: '0.75rem',            // 12px
  sm: '0.875rem',           // 14px
}

// DEPOIS (proposta ElevenLabs-style)
fontSize: {
  'base-ui': '0.8125rem',  // 13px (+2px)
  xs: '0.8125rem',          // 13px (+1px)
  sm: '0.875rem',           // 14px (manter)
}

// ANTES
borderRadius: {
  DEFAULT: '6px',
  md: '8px',
  lg: '12px',
}

// DEPOIS
borderRadius: {
  DEFAULT: '8px',    // +2px
  md: '12px',        // +4px
  lg: '16px',        // +4px
}

// Sidebar item padding
// ANTES: py-2 px-2 (8px vertical)
// DEPOIS: py-2.5 px-3 (10px vertical, 12px horizontal)

// Page padding
// ANTES: px-4 pt-3 (16px, 12px)
// DEPOIS: px-6 pt-5 (24px, 20px)
```

---

## 6. Aplicações Realizadas (09/04/2026)

### 6.1 Cores — Padrão ElevenLabs aplicado globalmente

**Textos (3 tons):**
| Token | Antes | Depois | Referência ElevenLabs |
|---|---|---|---|
| `--lia-text-primary` | `#111827` (cinza-azulado) | `#000000` (preto puro) | Títulos, texto principal |
| `--lia-text-secondary` | `#6B7280` | `#6B7280` (mantido) | Descrições, corpo |
| `--lia-text-tertiary` | `#9CA3AF` | `#9CA3AF` (mantido) | Placeholders, hints |

**Bordas (1 tom unificado):**
| Token | Antes | Depois |
|---|---|---|
| `--lia-border-subtle` | `#E5E7EB` | `#E5E7EB` (mantido) |
| `--lia-border-default` | `#D1D5DB` | `#E5E7EB` (unificado) |
| `--lia-border-medium` | `#9CA3AF` | `#E5E7EB` (unificado) |

### 6.2 Tipografia — Escala aumentada globalmente

| Token | Antes | Depois |
|---|---|---|
| `--font-size-base-ui` | 11px (0.6875rem) | 13px (0.8125rem) |
| `--font-size-xs` | 12px (0.75rem) | 13px (0.8125rem) |
| `--font-size-sm-ui` | 12px (0.75rem) | 13px (0.8125rem) |
| `--font-size-micro` | 10px (0.625rem) | 11px (0.6875rem) |

---

## 7. Conclusão

A plataforma LIA agora segue o padrão de cores ElevenLabs (preto puro para texto, 1 tom de borda) e teve a escala tipográfica aumentada em +1-2px globalmente. A base monocromática (90% grayscale, botões pretos, clean) está alinhada.

**Próximos passos potenciais:**
- Avaliar se badges/pills precisam de ajuste fino de padding após aumento de font
- Considerar aumento de padding de página (`px-4` → `px-6`) nas páginas que ainda não foram redesenhadas
- Sidebar: avaliar aumento de padding vertical dos itens de menu
