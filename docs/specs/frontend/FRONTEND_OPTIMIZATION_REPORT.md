# FRONTEND OPTIMIZATION REPORT — Plataforma LIA
> **Gerado em:** 2026-04-03 (Task #111 — Auditoria e Otimização Frontend Profunda)
> **Baseado em:** Scan direto do código-fonte em `/plataforma-lia/src/`
> **Não baseado em documentação** — todos os números foram apurados por grep/find em tempo real
> **Referências:** `FRONTEND_INVENTORY_v1.md`, `INVENTARIO_COMPONENTES.md`, `OPORTUNIDADES_PADRONIZACAO.md`
> **Stack:** React 19 + Next.js 15 + Tailwind CSS v3 + shadcn/ui (Radix UI)

---

## METODOLOGIA

Todos os dados foram coletados via grep no diretório `/plataforma-lia/src/` em 2026-04-03.
Comandos utilizados documentados ao final de cada seção para reprodutibilidade.

**Definições:**
- **Ocorrência**: uma linha de código com o padrão encontrado
- **Classe-ocorrência**: uma instância de uma classe CSS específica (uma linha pode ter múltiplas classes)
- **Arquivo**: qualquer `.tsx` ou `.ts` contendo pelo menos uma ocorrência

---

## SUMÁRIO EXECUTIVO

| Categoria | Ocorrências | Arquivos | P0 | P1 | P2 | P3 |
|-----------|-------------|----------|----|----|----|----|
| Componentes Duplicados | 1 par ativo real | 2 | 0 | 1 | 0 | 0 |
| Inline Styles | 886 `style={{}}` | 259 | 0 | 1 | 1 | 1 |
| Hex Hardcoded | 163 occ | 17 | 0 | 0 | 1 | 1 |
| wedo-cyan (auditoria) | 865 linhas / 928 class-occ | — | 0 | 1 | 1 | 0 |
| Font Families Explícitas | 449 occ removíveis | ~80 arquivos | 0 | 1 | 1 | 0 |
| Framer-Motion | 0 imports (resolvido) | — | — | — | — | — |
| Modais/Dialogs | 72 Dialog + 24 AlertDialog | — | 0 | 0 | 1 | 1 |
| Unsafe Any Types | 270 occ | 58 | 0 | 1 | 1 | 1 |

---

## 1. COMPONENTES DUPLICADOS

### 1.1 Contexto

O `OPORTUNIDADES_PADRONIZACAO.md` (OPT-035, OPT-036, OPT-038) listava três situações de duplicação. Após scan direto do filesystem:

| Duplicata Documentada | Status Real |
|-----------------------|-------------|
| `settings-page.tsx` vs `settings-page-enhanced.tsx` | `settings-page.tsx` **não existe** — OPT-035 resolvido |
| `jobs2-page.tsx` (variante alternativa) | Arquivo **não existe** — OPT-036 resolvido |
| `useTableFeatures.ts` duplicado | Apenas **um arquivo** existe — OPT-038 resolvido |
| `tasks-page.tsx` vs `tasks-page-mvp.tsx` | **AMBOS ATIVOS** em `dashboard-app.tsx` — ação necessária |

**Apenas 1 par de duplicata real permanece ativo.**

---

### 1.2 `tasks-page.tsx` vs `tasks-page-mvp.tsx` — ATIVO

**Prioridade:** P1 | **Impacto:** Clareza arquitetural, manutenção | **Esforço:** Baixo (renomear + atualizar imports)

**Diagnóstico confirmado por scan:**

`dashboard-app.tsx`:
```
linha 13: import { TasksPageMVP } from "@/components/pages/tasks-page-mvp"
linha 135: return <TasksPageMVP onNavigate={handleNavigate} />
```

`settings-page-enhanced.tsx`:
```
linha 27: import { TasksPage } from "@/components/pages/tasks-page"
```

**Diferença funcional real (não duplicata de código):**

| Componente | Linhas | Domínio | Dados |
|------------|--------|---------|-------|
| `tasks-page-mvp.tsx` | 881L | Agenda de entrevistas (view diária) — Tabs: Entrevistas, Histórico | Reais via `/api/backend-proxy/interviews/` |
| `tasks-page.tsx` | 827L | Painel de controle geral — Tarefas pendentes, Alertas, Vagas ativas | Mockados |

**Conclusão:** Não são duplicatas de código — resolvem domínios diferentes. O nome `tasks-page-mvp` é enganoso porque sugere uma versão provisória, quando na verdade é o componente ativo de agenda.

**Ação recomendada:**
1. Renomear `tasks-page-mvp.tsx` → `interview-schedule-page.tsx` (exportar `InterviewSchedulePage`)
2. Renomear `tasks-page.tsx` → `control-panel-page.tsx` (exportar `ControlPanelPage`)
3. Atualizar imports em `dashboard-app.tsx` (linhas 13, 135) e `settings-page-enhanced.tsx` (linhas 27, 408)
4. Deletar `app/_archived-routes/tasks-mvp/page.tsx` (rota arquivada, sem uso ativo)

**Cmd:** `grep -rln "TasksPageMVP\|tasks-page-mvp\|TasksPage\|tasks-page'" src --include="*.tsx"`

---

## 2. INLINE STYLES — Mapa Completo e Priorização

**Dados reais (scan 2026-04-03):**
- **886 ocorrências** de `style={{}}` em **259 arquivos** `.tsx`
- Contabilização: 1 ocorrência = 1 bloco `style={{ ... }}` em uma linha ou abertura de bloco

**Nota metodológica:** Um mesmo bloco `style={{}}` pode conter ao mesmo tempo um `var(--token)` e um valor raw (ex: `style={{ color: 'var(--lia-text)', height: '40px' }}`). As categorias abaixo são mutuamente exclusivas por tipo de valor dentro do bloco, não por bloco completo.

### 2.1 Top 20 Arquivos por Quantidade de `style={{}}`

| Rank | Arquivo | Count | Tipo Dominante |
|------|---------|-------|----------------|
| 1 | `components/rubric-evaluation-modal.tsx` | 21 | Score percentages + dynamic colors |
| 2 | `components/pages/jobs/JobsCompactTableView.tsx` | 21 | Column widths + status colors |
| 3 | `components/expanded-chat/components/ChatMessageList.tsx` | 21 | Message bubble colors |
| 4 | `components/lia-float/LiaSuperPrompt.tsx` | 20 | Positioning + heights |
| 5 | `components/daily-briefing-card.tsx` | 18 | Progress bar widths + colors |
| 6 | `components/clouds-background.tsx` | 16 | SVG animation values |
| 7 | `components/ui/prompt-suggestions-dock.tsx` | 15 | Positions, transforms |
| 8 | `components/pages/big-five-dashboard-page.tsx` | 13 | Radar chart colors |
| 9 | `components/expandable-ai-prompt/tabs/EAPTabNatural.tsx` | 13 | Dynamic sizes |
| 10 | `components/agent-control-center/index.tsx` | 13 | Floating positions |
| 11 | `components/ui/lia-search-queries-guide.tsx` | 12 | Scroll heights |
| 12 | `components/ui/candidate-queries-guide.tsx` | 12 | Scroll heights |
| 13 | `components/expandable-ai-prompt/EAPModals.tsx` | 12 | Transforms, positions |
| 14 | `components/ui/lia-vacancy-queries-guide.tsx` | 11 | Scroll heights |
| 15 | `components/ui/lia-queries-guide.tsx` | 11 | Scroll heights |
| 16 | `components/search/search-preview-card.tsx` | 11 | Score bars |
| 17 | `components/settings/HiringPoliciesHub.tsx` | 10 | Progress bars |
| 18 | `components/pages/jobs/InlineChatPanel.tsx` | 10 | Layout positions |
| 19 | `app/portal/data-request/[token]/page.tsx` | 10 | Print layout |
| 20 | `components/ui/lia-expanded-panel.tsx` | 9 | Dynamic heights |

**Cmd:** `grep -rc "style={{" src --include="*.tsx" | sort -t: -k2 -rn | head -20`

### 2.2 Classificação por Tipo de Valor

**TIPO A — CSS vars (token-aware, aceitáveis para valores dinâmicos):**
Uso de `var(--token)` dentro de `style={{}}` — responde ao tema, suporta dark mode.
Exemplo correto: `style={{ color: 'var(--lia-text-primary)' }}`
Prevalência: ~511 linhas contendo pelo menos 1 `var(--` em bloco `style`.

**TIPO B — Valores raw sem dark mode (risco médio-alto):**
Raw hex, px hardcoded como cores, strings de cor sem variável. Não respondem ao dark mode.
Exemplos críticos:
- `daily-briefing-card.tsx`: progress bars com `background-color` raw
- `JobsCompactTableView.tsx`: status colors hardcoded
- `ChatMessageList.tsx`: bubble background colors raw
Prevalência: estimada em ~300–400 blocos com pelo menos 1 valor raw de cor

**TIPO C — Valores dinâmicos legítimos (não migráveis, aceitar):**
- Percentages calculadas: `style={{ width: `${score}%` }}`
- Posições JavaScript: `style={{ left: x, top: y }}`
- Colors de chart/viz vindas de dados: `style={{ color: dimension.color }}`

**TIPO D — Valores estáticos migráveis para classe Tailwind (P1):**
Valores raw que não são dinâmicos — podem virar classes:
- `style={{ fontWeight: 600 }}` → `className="font-semibold"`
- `style={{ textAlign: 'center' }}` → `className="text-center"`
- `style={{ display: 'flex' }}` → `className="flex"`
Prevalência: estimada ~100–150 blocos

### 2.3 Risco por Dark Mode

Os ~300–400 blocos TIPO B são o principal risco de dark mode. No modo claro produzem visual correto mas no dark mode podem aparecer como cores claras em fundo escuro ou cores escuras em fundo escuro.

**Arquivos de maior risco (dark mode):**

| Arquivo | Risco | Motivo |
|---------|-------|--------|
| `daily-briefing-card.tsx` | Alto | Progress bars com cores de status raw |
| `rubric-evaluation-modal.tsx` | Alto | Score bars e scale colors raw |
| `ChatMessageList.tsx` | Alto | Message bubble backgrounds raw |
| `JobsCompactTableView.tsx` | Médio | Status badge colors |
| `big-five-dashboard-page.tsx` | Baixo | Chart viz — intencional |

### 2.4 Plano de Migração

**P1 (próximo sprint, 3–5 dias):**
- Migrar TIPO D (estáticos) → classes Tailwind (100–150 blocos em ~20 arquivos)
- Migrar TIPO B em `daily-briefing-card.tsx`, `rubric-evaluation-modal.tsx`, `ChatMessageList.tsx` → `var(--token)` ou classe

**P2 (sprint seguinte, 3–5 dias):**
- Migrar TIPO B restante — progresso incremental por arquivo

**P3 (aceitar):**
- TIPO C (dinâmicos) — não migrar
- Chart viz colors (`big-five-dashboard-page.tsx`, `clouds-background.tsx`) — aceitar com comentário

---

## 3. HEX HARDCODED — Inventário Completo

**Dados reais (scan 2026-04-03):**
- **163 ocorrências** de hex 6 dígitos em **17 arquivos** `.tsx`

**Cmd:** `grep -rn '#[0-9A-Fa-f]\{6\}\b' src --include="*.tsx"`

### 3.1 Inventário por Arquivo (Total por Arquivo)

| Arquivo | Hex Count | Categoria |
|---------|-----------|-----------|
| `components/email-templates/report-email-templates.tsx` | 59 | ISENTO — email template |
| `components/email-templates/email-templates-manager.tsx` | 38 | ISENTO — email template |
| `app/ajuda/AjudaClient.tsx` | 16 | ISENTO — viz colors (ver 3.2) |
| `components/pages/login-page.tsx` | 12 | ISENTO — OAuth SVG brand |
| `components/clouds-background.tsx` | 7 | ISENTO — SVG animation palette |
| `app/admin/clientes/[clientId]/big-five/page.tsx` | 5 | ISENTO — radar viz colors |
| `components/triagem-details-modal.tsx` | 5 | MISTO — ver 3.3 |
| `app/login/LoginClient.tsx` | 4 | ISENTO — OAuth SVG brand |
| `app/opengraph-image.tsx` | 3 | ISENTO — imagem estática OG |
| `components/pages/tasks/TaskCard.tsx` | 3 | CRIAR TOKEN — ver 3.3 |
| `components/pages/tasks/ActiveAlertsCard.tsx` | 2 | CRIAR TOKEN — ver 3.3 |
| `components/search/search-preview-card.tsx` | 2 | CRIAR TOKEN — ver 3.3 |
| `components/chat/ChatContextPanelPart2.tsx` | 2 | CRIAR TOKEN — ver 3.3 |
| `stories/Header.tsx` | 2 | Storybook — não produção |
| `app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` | 1 | CRIAR TOKEN — GitHub icon |
| `components/tables/unified-candidate-table.tsx` | 1 | MIGRÁVEL — token existe |
| `components/chat/ChatContextPanelPart3.tsx` | 1 | CRIAR TOKEN — ver 3.3 |
| **TOTAL** | **163** | |

### 3.2 Categorias de Isenção (149 occ — 91% do total)

| Categoria | Count | Arquivos | Justificativa |
|-----------|-------|----------|---------------|
| Email templates (body_html) | 97 | `report-email-templates.tsx`, `email-templates-manager.tsx` | Clientes de email (Gmail, Outlook) não processam CSS vars. Inline hex é padrão da indústria. |
| OAuth/brand SVG | 16 | `login-page.tsx`, `LoginClient.tsx` | Cores de marca Google (#4285F4, #34A853, #FBBC05, #EA4335) e Microsoft (#F25022, #7FBA00, #00A4EF, #FFB900) — imutáveis por contrato |
| Viz/chart colors dinâmicos | 21 | `AjudaClient.tsx` (16), `big-five/page.tsx` (5) | Cores de legenda para arquétipos Big Five e senioridades — parte de configuração de dados, sem token equivalente |
| SVG animation palette | 7 | `clouds-background.tsx` | Gradiente de nuvens decorativas com 7 tons progressivos — aceitar como palette interna |
| Imagem OG estática | 3 | `opengraph-image.tsx` | CSS vars não funcionam em rendering de imagem OG no servidor |
| Print-window HTML inline | 3 | `triagem-details-modal.tsx:322` | Template de impressão de relatório WSI: `#166534`, `#854D0E`, `#991B1B` como scores semânticos — mesmo caso dos email templates |
| Storybook | 2 | `stories/Header.tsx` | Fora de produção |
| **TOTAL ISENTO** | **149** | | |

### 3.3 Inventário Completo — Acionável (14 occ em 6 arquivos)

#### MIGRÁVEL — Token já existe (P2, esforço baixo)

| Arquivo | Linha | Hex | Token Equivalente | Contexto |
|---------|-------|-----|-------------------|----------|
| `components/tables/unified-candidate-table.tsx` | 339 | `#E5E7EB` | `--gray-200` / `--lia-border-subtle` | Border em linha de tabela |
| `components/triagem-details-modal.tsx` | 319 | `#F3F4F6` | `--gray-100` / `--lia-bg-secondary` | Border em print window |
| `components/triagem-details-modal.tsx` | 333 | `#F3F4F6` | `--gray-100` / `--lia-bg-secondary` | Border em print window |

**Nota sobre triagem-details-modal:** As linhas 322 (`#166534`, `#854D0E`, `#991B1B`) são cores de score semântico em um template de impressão (print window HTML inline) — funcionam como email template, portanto **ISENTAS** de migração. As linhas 319 e 333 têm token equivalente e devem ser migradas.

#### CRIAR TOKEN — Padrão recorrente justifica novo token (P2, esforço baixo)

| Hex | Ocorrências | Arquivos | Token Proposto | Contexto |
|-----|-------------|----------|----------------|----------|
| `#F0FDF4` | 7 | `TaskCard.tsx` (3), `search-preview-card.tsx` (2), `ChatContextPanelPart2.tsx` (1), `ChatContextPanelPart3.tsx` (1) | `--wedo-green-light` ou `--status-success-subtle` | Background de estado positivo/sucesso |
| `#FEFCE8` | 2 | `ActiveAlertsCard.tsx` (1), `ChatContextPanelPart2.tsx` (1) | `--status-warning-subtle` | Background de alerta |
| `#EFF6FF` | 1 | `ActiveAlertsCard.tsx` (1) | `--status-info-subtle` | Background de informação |
| `#181717` | 1 | `CandidatoDetailClient.tsx` (210) | Usar `currentColor` + `fill="black"` | GitHub icon SVG inline |

**Nota sobre `#F0FDF4` em TaskCard.tsx:** Já usa `var(--wedo-green-light, #f0fdf4)` como fallback — o token `--wedo-green-light` está referenciado mas não definido em `design-tokens.css`. A ação é **definir o token**, não remover o uso.

**Resumo acionável (163 occ totais):**
```
149 occ isentas (91%)  → documentar com comentário /* category-exempt */
               Detalhes: 97 email + 16 OAuth SVG + 21 viz/chart + 7 SVG animation
                       + 3 OG + 3 print-window + 2 Storybook
  3 occ migráveis      → substituir por var(--token) existente
 11 occ novo token     → definir tokens em design-tokens.css (--wedo-green-light, etc.)
----
Verificação: 149 + 3 + 11 = 163 ✓
```

---

## 4. AUDITORIA wedo-cyan — Semântico vs Decorativo

**Dados reais (scan 2026-04-03):**

| Métrica | Valor | Método |
|---------|-------|--------|
| Linhas contendo `wedo-cyan` em .tsx | **865** | `grep -rn "wedo-cyan" *.tsx | wc -l` |
| Classe-ocorrências `text-wedo-cyan*` | **560** | `grep -rc "text-wedo-cyan" | sum` |
| Classe-ocorrências `bg-wedo-cyan*` | **271** | `grep -rc "bg-wedo-cyan" | sum` |
| Classe-ocorrências `border-wedo-cyan*` | **81** | `grep -rc "border-wedo-cyan" | sum` |
| Classe-ocorrências `ring-wedo-cyan*` | **3** | `grep -rc "ring-wedo-cyan" | sum` |
| Outras (`fill-`, `from-`, `to-`, `via-`) | **13** | grep combinado |
| **Total classe-ocorrências** | **928** | Soma acima |

**Discrepância 865 vs 928:** Uma linha pode conter múltiplas classes `wedo-cyan` (ex: `className="text-wedo-cyan border-wedo-cyan/30"`). 865 = linhas; 928 = class-ocorrências.

### 4.1 Top 10 Arquivos por Ocorrências

| Arquivo | Count linhas | Classificação |
|---------|-------------|---------------|
| `components/triagem-details-modal.tsx` | 17 | Semântico (triagem IA) |
| `app/admin/AdminTemplateHub.tsx` | 17 | Misto — auditoria manual necessária |
| `components/search/EditArchetypeModal.tsx` | 15 | Semântico (busca IA) |
| `components/job-creation/compensation-analysis-panel.tsx` | 13 | Semântico (análise IA) |
| `components/kanban/components/UniversalTransitionModal.tsx` | 12 | Misto |
| `components/daily-briefing-card.tsx` | 12 | Semântico (briefing LIA) |
| `components/rubric-evaluation-modal.tsx` | 11 | Semântico (avaliação IA) |
| `components/chat/parecer-lia-card.tsx` | 11 | Semântico (parecer LIA) |
| `components/search/SSISimilarMode.tsx` | 9 | Semântico (busca IA) |
| `components/expanded-chat/stages/CompetenciesStage.tsx` | 9 | Semântico |

### 4.2 Regra de Decisão Semântico vs Decorativo

```
wedo-cyan = SEMÂNTICO (manter) quando:
  ✅ Representa output, processamento ou ação da LIA/IA
  ✅ Indicador de "inteligência" ou "análise automatizada"
  ✅ Contexto: chat, scoring, análise, triagem, competências, wizard de vaga com IA
  ✅ Badge/ícone associado a feature de IA nomeada (LIA, WSI, Big Five, etc.)

wedo-cyan = DECORATIVO (migrar para gray-* ou lia-bg-*) quando:
  ❌ Ícone de funcionalidade genérica sem IA (ajuda, config, integrações)
  ❌ Loading spinner em contexto não-IA
  ❌ Badge de status genérico (ex: "Entrevista" no color picker de templates)
  ❌ O elemento existiria com mesma cor em sistema sem nenhuma IA
```

### 4.3 Candidatos Decorativos para Migração (P2, ~50 class-ocorrências)

| Arquivo | Linha(s) | Uso Atual | Migração Proposta |
|---------|----------|-----------|-------------------|
| `app/ajuda/AjudaClient.tsx` | 60, 245 | `bg-wedo-cyan/15` em ícone de help | `bg-lia-bg-tertiary` |
| `app/ajuda/AjudaClient.tsx` | 201 | `text-wedo-cyan border-wedo-cyan/30` em badge | `text-lia-text-secondary border-lia-border-default` |
| `app/admin/clientes/[clientId]/workforce/page.tsx` | 550 | `bg-wedo-cyan/[0.08]` em card de métrica genérica | `bg-lia-bg-secondary` |
| `app/jobs/[id]/JobDetailClient.tsx` | 108 | `border-wedo-cyan/30` em `animate-spin` genérico | `border-lia-border-medium` |
| `app/configuracoes/integracoes/IntegracoesClient.tsx` | 68 | `bg-wedo-cyan/10` em ícone de integração | `bg-lia-bg-tertiary` |
| `components/modals/create-job-modal.tsx` | 195 | `bg-wedo-cyan/10` em ícone de "nova vaga" | `bg-lia-bg-tertiary` |
| `components/module-access/module-upsell.tsx` | 98 | `bg-wedo-cyan/10 dark:bg-wedo-cyan/15` em upsell card | `bg-lia-bg-secondary` |
| `components/email-templates/email-templates-manager.tsx` | 33 | `bg-wedo-cyan/10 text-wedo-cyan` no badge "Entrevista" | `bg-lia-bg-secondary text-lia-text-secondary` |

### 4.4 Plano

**P1 (esforço baixo, 1–2h):** Adicionar regra formal de uso de `wedo-cyan` em `FRONTEND_STANDARDS.md` com exemplos CORRETO/INCORRETO.

**P2 (esforço médio, 1–2 dias):** Migrar ~50 class-ocorrências decorativas listadas acima.

---

## 5. FONT FAMILIES — Análise das Referências Explícitas

**Dados reais (scan 2026-04-03):**

| Classe | Ocorrências em .tsx | Status |
|--------|---------------------|--------|
| `font-open-sans` | 281 | **Redundante** — body já herda |
| `font-inter` | 168 | **Parcialmente incorreto** — 151 em não-numérico |
| `font-[...]` arbitrário | 48 | **Desnecessário** — forma proibida |
| `font-brand` | 0 | Token definido mas sem uso |
| `font-data` | 0 | Token definido mas **sem uso algum** |

**Cmd:** `grep -rc "font-open-sans\|font-inter\|font-\[" src --include="*.tsx" | awk -F: '{sum+=$2} END {print sum}'`

### 5.1 font-open-sans — 281 Ocorrências Redundantes (P1)

**Por que é redundante:** `app/layout.tsx` (linha 183 via `globals.css`) define `body { font-family: var(--font-open-sans), "Open Sans", sans-serif }`. Todo elemento herda automaticamente. Adicionar `font-open-sans` nos componentes não muda absolutamente nada visualmente.

**Exemplos (representativos de 10+ arquivos):**
```tsx
// app/register/RegisterClient.tsx:64
<div className="min-h-screen flex items-center justify-center bg-lia-bg-secondary font-open-sans p-4">

// app/forgot-password/ForgotPasswordClient.tsx:41
<div className="min-h-screen flex items-center justify-center bg-lia-bg-secondary font-open-sans p-4">

// components/pages/candidates/lia-sidebar/TabBoolean.tsx:40
<Button className="w-full h-11 !text-sm font-semibold bg-wedo-cyan-dark text-white font-open-sans">

// components/pages/dashboards-page/KanbanLoadingState.tsx:10
<span className="text-sm text-lia-text-tertiary font-open-sans">Carregando...</span>
```

**Arquivos com mais ocorrências:**

| Arquivo | Count |
|---------|-------|
| `app/reset-password/ResetPasswordClient.tsx` | 4 |
| `app/accept-invitation/AcceptInvitationClient.tsx` | 5 |
| `app/register/RegisterClient.tsx` | 2 |
| `components/pages/dashboards-page/*.tsx` (vários) | ~20 |
| Restante distribuído em ~40 arquivos | ~250 |

**Solução:** Remoção simples — `sed -i 's/ font-open-sans//g'` em ~50 arquivos (ou grep+replace em editor). Exceção: `app/layout.tsx` linha 24 (definição da CSS var — manter).

**Estimativa:** 0.5 dia

### 5.2 font-inter — 168 Ocorrências, 151 Indevidas (P2)

**Contexto correto:** `font-inter` deve ser usado apenas em contextos numéricos/tabulares (o Inter tem `font-feature-settings: "tnum"` ativo via Tailwind config).

**Análise:** 17 ocorrências em contexto numérico legítimo (mantidas) vs 151 em contexto não-numérico (indevidas).

**Uso CORRETO (17 occ — manter como `font-data`):**
```tsx
// IndicadoresEstrategicosPlaceholder.tsx:132
<div className="text-xl font-inter font-bold text-lia-text-primary">+28%</div>
// IndicadoresEstrategicosPlaceholder.tsx:240
<span className="text-sm font-inter font-bold text-lia-text-primary">12 dias</span>
// AnaliseCompetenciasPlaceholder.tsx:154
<Badge className="... font-inter font-bold">Gap 55%</Badge>
```

**Uso INCORRETO (151 occ — remover):** Aplicado em labels de texto, títulos, elementos não-numéricos — herdam Open Sans do body que é igualmente correto.

**token `font-data` tem 0 usos:** O alias semântico `font-data` está definido em `tailwind.config.ts` mas nenhum componente o usa. Os 17 usos corretos de `font-inter` deveriam usar `font-data`.

**Solução:**
1. Substituir `font-inter` por `font-data` nos 17 contextos numéricos
2. Remover `font-inter` nos 151 contextos não-numéricos

### 5.3 Formas Arbitrárias — 48 Ocorrências (P3)

```tsx
font-[Inter,sans-serif]   // ~20 occ — usar font-data
font-[Open_Sans,sans-serif] // ~28 occ — remover (body herda)
```

**Regra formal proposta:**
```
✅ CORRETO:
  font-data  → números, métricas, percentuais, datas em tabela (substitui font-inter)
  (nenhuma)  → texto, labels, títulos, body — herda Open Sans via body

❌ PROIBIDO em componentes:
  font-inter          → usar font-data quando numérico, nada quando texto
  font-open-sans      → redundante, sempre remover
  font-[Inter,...]    → usar font-data
  font-[Open_Sans,...]→ remover
  font-brand          → reservado, sem uso atual
```

---

## 6. FRAMER-MOTION — Status: RESOLVIDO

**Dados reais (scan 2026-04-03):**

```bash
grep -rn "from 'framer-motion'" src --include="*.tsx" --include="*.ts"
# Resultado: 0 resultados

grep "framer-motion" plataforma-lia/package.json
# Resultado: (vazio — não está em nenhuma secção do package.json)
```

**Conclusão:** O item OPT-027 do `OPORTUNIDADES_PADRONIZACAO.md` estava registrando "framer-motion instalado e usado em 1 arquivo". Hoje:
- **0 imports** em qualquer arquivo
- **Não está no `package.json`** (nem em `dependencies` nem em `devDependencies`)

A biblioteca foi removida em sprint anterior. Nenhuma ação de código necessária.

**Cobertura de animações atual:**
- `tailwind.config.ts`: define keyframes `fade-in-up`, `scale-in-delayed`, `slide-in-up`
- `src/styles/animations.css`: ~20 keyframes adicionais
- Tailwind built-in: `animate-spin`, `animate-pulse`, `animate-bounce`, `animate-ping`
- 12 usos de `animate-fade`, `animate-slide`, `animate-scale` (aliases customizados)

**Ação:** Atualizar `OPORTUNIDADES_PADRONIZACAO.md` marcando OPT-027 como RESOLVIDO.

---

## 7. MODAIS E DIALOGS — Padrão Composable

**Dados reais (scan 2026-04-03):**

| Componente | Arquivos | Count linhas |
|------------|----------|-------------|
| `Dialog` (from shadcn/ui) | 72 | — |
| `AlertDialog` | 24 | — |
| `Sheet` (drawer lateral) | 4 | — |
| Arquivos com `open={is*}` ou `open={show*}` | 91 | — |
| Arquivos com `onCancel\|onClose\|onConfirm\|onSubmit` | 224 | — |

**Cmd:** `grep -rln "from \"@/components/ui/dialog\"" src --include="*.tsx" | wc -l`

### 7.1 Top 10 Arquivos por Repetição de Estrutura Dialog

| Arquivo | Dialog Refs | Padrão |
|---------|-------------|--------|
| `components/bulk-actions-bar.tsx` | 44 | Multi-modal no mesmo arquivo |
| `app/admin/clientes/[clientId]/usuarios/page.tsx` | 32 | CRUD de usuários com 5+ dialogs |
| `components/talent-funnel-tabs/saved-searches-tab.tsx` | 31 | CRUD de buscas salvas |
| `components/kanban/components/ColumnContextMenu.tsx` | 28 | Menu contextual com dialogs |
| `app/admin/compliance/riscos/seguro/page.tsx` | 25 | CRUD compliance |
| `components/talent-funnel-tabs/lists-tab.tsx` | 24 | CRUD de listas |
| `components/talent-funnel-tabs/history-tab.tsx` | 23 | Histórico com modals |
| `components/settings/DepartmentsTab.tsx` | 21 | CRUD de departamentos |
| `components/candidate-preview.tsx` | 20 | Preview com sub-modals |
| `components/big-five-modal.tsx` | 20 | Modal complexo |

### 7.2 Padrão Repetido — Form Dialog

O padrão abaixo aparece com variações mínimas em **todos os 72 arquivos com Dialog**:

```tsx
// Padrão atual — repetido ~72x
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>{title}</DialogTitle>
      <DialogDescription>{description}</DialogDescription>
    </DialogHeader>
    {/* conteúdo específico */}
    <DialogFooter>
      <Button variant="outline" onClick={() => setIsOpen(false)}>Cancelar</Button>
      <Button onClick={handleSubmit} disabled={isLoading}>
        {isLoading ? 'Salvando...' : 'Salvar'}
      </Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 7.3 Proposta — `FormDialog` Composable (P2)

```tsx
// components/ui/form-dialog.tsx (a criar)
interface FormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  onSubmit?: () => void | Promise<void>
  onCancel?: () => void
  submitLabel?: string
  cancelLabel?: string
  isLoading?: boolean
  isDangerous?: boolean    // botão vermelho
  size?: 'sm' | 'md' | 'lg' | 'xl'
  children: React.ReactNode
}

// Uso simplificado:
<FormDialog
  open={isOpen}
  onOpenChange={setIsOpen}
  title="Novo Departamento"
  onSubmit={handleCreate}
  submitLabel="Criar"
>
  <DepartmentForm ref={formRef} />
</FormDialog>
```

**Benefícios:**
- Elimina ~30% do boilerplate em 72 arquivos
- Dark mode, focus trap, aria-labels, Escape key — automáticos
- Padrão Vue-ready: mapeia diretamente para `v-dialog` do Vuetify na migração

### 7.4 Proposta — `ConfirmationDialog` (P3)

```tsx
// components/ui/confirmation-dialog.tsx (a criar)
interface ConfirmationDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description: string
  onConfirm: () => void
  variant?: 'default' | 'destructive'
  confirmLabel?: string
  cancelLabel?: string
}
```

**Estimativa de esforço:**
- Criar `FormDialog`: 2–3 horas
- Migrar top-5 arquivos: 1–2 dias
- Migrar restante incrementalmente

---

## 8. UNSAFE ANY TYPES — Lista Priorizada Completa

**Dados reais (scan 2026-04-03):**
- **270 ocorrências** de `: any` e `as any` em **58 arquivos**

**Cmd:** `grep -rn ": any\b\|as any\b" src --include="*.tsx" --include="*.ts" | grep -v "// "`

### 8.1 Inventário Completo por Arquivo (todos os 58 arquivos)

| Prioridade | Count | Arquivo |
|------------|-------|---------|
| **P1** | **26** | `app/admin/clientes/[clientId]/conformidade/lgpd/page.tsx` |
| **P1** | **16** | `components/search/SearchModeArchetypes.tsx` |
| **P1** | **16** | `components/kanban/components/CandidateTableRow.tsx` |
| **P1** | **15** | `components/pages/chat-page/useChatPageCore.tsx` |
| **P2** | 13 | `components/triagem-details-modal.tsx` |
| **P2** | 12 | `components/pages/candidates/CandidatePreviewSidePanel.tsx` |
| **P2** | 12 | `components/pages/candidates-page.tsx` |
| **P2** | 11 | `components/modals/technical-test-modal.tsx` |
| **P2** | 11 | `components/expanded-chat/hooks/useCompanyConfigLoader.ts` |
| **P2** | 8 | `app/admin/configuracoes/comunicacoes/components/TemplatesSection.tsx` |
| **P2** | 8 | `app/admin/clientes/[clientId]/conformidade/page.tsx` |
| **P2** | 8 | `components/jobs/JobPreviewTab.tsx` |
| **P2** | 8 | `components/autonomous/proactive-actions-bell.tsx` |
| **P2** | 8 | `components/candidate-preview/OpinionCard.tsx` |
| **P3** | 7 | `components/quick-actions/schedule-modal.tsx` |
| **P3** | 6 | `components/jobs/job-edit-tab/useJobEditTab.ts` |
| **P3** | 6 | `components/big-five-modal.tsx` |
| **P3** | 5 | `components/chat/resume-analysis-result.tsx` |
| **P3** | 5 | `components/candidate-page/CandidatePageOpinionsTab.tsx` |
| **P3** | 4 | `components/modals/english-test-modal.tsx` |
| **P3** | 3 | `app/admin/clientes/[clientId]/conformidade/controles/page.tsx` |
| **P3** | 3 | `components/pages/tasks/TaskCard.tsx` |
| **P3** | 3 | `components/screening-config/ScreeningConfigManager.tsx` |
| **P3** | 3 | `components/test-status-indicators.tsx` |
| **P3** | 3 | `components/lia-performance-indicators.tsx` |
| **P3** | 3 | `components/lia-screening-dialogue.tsx` |
| **P3** | 3 | `components/job-report-modal.tsx` |
| **P3** | 3 | `components/candidate-preview.tsx` |
| P3 | 2 | `app/privacidade/PrivacidadeClient.tsx` |
| P3 | 2 | `components/modals/job-compare-modal.tsx` |
| P3 | 2 | `components/modals/general-score-modal.tsx` |
| P3 | 2 | `components/settings/CompanyProfileTab.tsx` |
| P3 | 2 | `components/modals/create-job-modal.tsx` |
| P3 | 2 | `components/ui/lia-expanded-panel.tsx` |
| P3 | 2 | `components/jobs/JobDescriptionEditor.tsx` |
| P3 | 2 | `components/expanded-chat/hooks/useCoachingModule.ts` |
| P3 | 2 | `components/expanded-chat/components/ChatMessageList.tsx` |
| P3 | 1 | `app/admin/clientes/[clientId]/conformidade/auditoria/page.tsx` |
| P3 | 1 | `components/talent-funnel-tabs/saved-searches-tab.tsx` |
| P3 | 1 | `components/talent-funnel-tabs/lists-tab.tsx` |
| P3 | 1 | `components/settings/DepartmentsTab.tsx` |
| P3 | 1 | `components/search/SearchModeAdvanced.tsx` |
| P3 | 1 | `components/pages/tasks/useTasksCore.ts` |
| P3 | 1 | `components/pages/dashboards-page/PeopleAnalyticsPlaceholder.tsx` |
| P3 | 1 | `components/page-titles.tsx` |
| P3 | 1 | `components/kanban/components/SmartProgressBar.tsx` |
| P3 | 1 | `components/jobs/CandidateKanbanView.tsx` |
| P3 | 1 | `components/expanded-chat/stages/ScreeningStage.tsx` |
| P3 | 1 | `components/email-templates/email-templates-manager.tsx` |
| P3 | 1 | `components/candidate-timeline.tsx` |
| P3 | 1 | `components/bulk-actions-bar.tsx` |
| P3 | 1 | `components/big-five-context.tsx` |
| P3 | 1 | `components/ai-recruiter/AIRecruiterPanel.tsx` |
| P3 | 1 | `app/funil-de-talentos/candidato/[id]/CandidatoDetailClient.tsx` |
| P3 | 1 | `app/admin/clientes/[clientId]/workforce/page.tsx` |
| P3 | 1 | `app/admin/clientes/[clientId]/screening/page.tsx` |
| P3 | 1 | `app/admin/clientes/[clientId]/relatorios/page.tsx` |
| P3 | 1 | `app/admin/clientes/[clientId]/big-five/page.tsx` |
| **TOTAL** | **270** | **58 arquivos** |

### 8.2 Análise de Risco por Área

| Área | Ocorrências | Risco |
|------|-------------|-------|
| API routes (`app/api/`) | **0** | Nenhum — limpo |
| Hooks (`hooks/`) | **0** | Nenhum — limpo |
| Admin LGPD (dados de titular) | **26** | **ALTO** — falha de tipo pode afetar fluxo de conformidade |
| Core do chat (`useChatPageCore`) | **15** | **ALTO** — hook central do fluxo principal |
| Busca de candidatos | **32** | **Alto** — feature core (SearchModeArchetypes + CandidateTableRow) |
| Modais de avaliação | **29** | Médio |
| Admin compliance (não-LGPD) | **16** | Médio |
| Admin configurações | **8** | Baixo |
| Componentes de preview/opinião | **16** | Baixo |
| Restante (1–3 occ) | **80** | Baixo |

### 8.3 Padrões Dominantes de `any`

**Padrão 1 — State não tipado (mais comum):**
```tsx
const [data, setData] = useState<any>(null)
// Fix: useState<CandidateData | null>(null) usando interface da API
```

**Padrão 2 — Callback handler não tipado:**
```tsx
const handleUpdate = (item: any) => { ... }
// Fix: usar type narrowing ou interface específica
```

**Padrão 3 — `as any` para bypass de TypeScript:**
```tsx
const result = apiResponse as any
// Fix: usar `unknown` + type guard, ou interface explícita
```

### 8.4 Plano de Resolução

**P1 (próximo sprint, 2–3 dias):**
1. `lgpd/page.tsx` (26 any): criar interfaces `ConsentimentoData`, `TitularData`, `RelatorioLGPD`
2. `useChatPageCore.tsx` (15 any): tipar `ChatMessage`, `ChatContext`, `ChatAction`
3. `SearchModeArchetypes.tsx` + `CandidateTableRow.tsx` (32 any): usar interfaces de `CandidateSearchResult` e `CandidateRow` existentes (verificar se já estão em `types/`)

**P2 (sprint seguinte, 3–5 dias):**
4. Modais e componentes de candidatos (~80 occ em 8 arquivos)
5. Usar `unknown` + type guards em lugar de `any` para dados de API não validados

**P3 (backlog — gradual):**
6. Componentes de 1–3 occ (qualquer sprint disponível)
7. Adicionar `@typescript-eslint/no-explicit-any: "warn"` no eslint para prevenir novos any

---

## 9. ÍNDICE DE PRIORIDADES CONSOLIDADO

### P1 — Alta Prioridade (executar no próximo sprint)

| ID | Item | Esforço | Arquivos Chave |
|----|------|---------|----------------|
| OPT-R01 | Renomear tasks-page*.tsx para nomes semânticos | 0.5 dia | `dashboard-app.tsx`, `settings-page-enhanced.tsx` |
| OPT-R02 | Remover 281 `font-open-sans` redundantes | 1 dia | ~50 arquivos |
| OPT-R03 | Tipar any em fluxos críticos (LGPD + chat + kanban) | 2–3 dias | `lgpd/page.tsx`, `useChatPageCore.tsx`, `CandidateTableRow.tsx` |
| OPT-R04 | Definir regra formal wedo-cyan em FRONTEND_STANDARDS | 0.5 dia | `FRONTEND_STANDARDS.md` |
| OPT-R05 | Migrar inline styles TIPO D (estáticos) → classes Tailwind | 2–3 dias | `daily-briefing-card.tsx`, `rubric-evaluation-modal.tsx`, `ChatMessageList.tsx` |
| OPT-R06 | Tipar any em SearchModeArchetypes + CandidateTableRow | 1–2 dias | 2 arquivos |

### P2 — Prioridade Média (próximos 2 sprints)

| ID | Item | Esforço | Arquivos Chave |
|----|------|---------|----------------|
| OPT-R07 | Remover 151 `font-inter` não-numéricos + adotar `font-data` | 1 dia | ~40 arquivos |
| OPT-R08 | Migrar 3 hex com token existente | 0.5 dia | `unified-candidate-table.tsx`, `triagem-details-modal.tsx` |
| OPT-R09 | Definir tokens `--wedo-green-light`, `--status-warning-subtle`, `--status-info-subtle` | 0.5 dia | `design-tokens.css` |
| OPT-R10 | Migrar ~50 class-ocorrências wedo-cyan decorativas | 1–2 dias | `AjudaClient.tsx`, `IntegracoesClient.tsx`, 6+ arquivos |
| OPT-R11 | Criar `FormDialog` composable + migrar top-5 arquivos | 2–3 dias | `DepartmentsTab.tsx`, `ApprovalsHub.tsx`, `email-templates-manager.tsx` |
| OPT-R12 | Tipar any em modais e candidates-page (~80 occ) | 3–5 dias | 8 arquivos |

### P3 — Prioridade Baixa (backlog)

| ID | Item | Esforço | Arquivos Chave |
|----|------|---------|----------------|
| OPT-R13 | Remover `font-[...]` formas arbitrárias (48 occ) | 0.5 dia | ~20 arquivos |
| OPT-R14 | Criar `ConfirmationDialog` composable | 1–2 dias | 24 arquivos AlertDialog |
| OPT-R15 | Tipar any em componentes de 1–3 occ (restante) | Gradual | 43 arquivos |
| OPT-R16 | Adicionar `@typescript-eslint/no-explicit-any: warn` | 0.5 dia | `.eslintrc.json` |
| OPT-R17 | Migrar inline styles TIPO B restante | 3–5 dias | ~80 arquivos |
| OPT-R18 | Documentar isenções hex com comentário `/* category-exempt */` | 1 dia | 7 arquivos isentos |
| OPT-R19 | Atualizar OPORTUNIDADES_PADRONIZACAO.md (OPT-027, 035, 036, 038 resolvidos) | 0.5 dia | `OPORTUNIDADES_PADRONIZACAO.md` |

---

## 10. RESUMO DE ITENS JÁ RESOLVIDOS (Verificados por Código)

| Item | Status | Verificação |
|------|--------|-------------|
| OPT-027 framer-motion | **RESOLVIDO** | 0 imports, não no package.json |
| OPT-035 settings-page.tsx duplicata | **RESOLVIDO** | `settings-page.tsx` não existe |
| OPT-036 jobs2-page.tsx | **RESOLVIDO** | Arquivo não existe |
| OPT-038 useTableFeatures duplicado | **RESOLVIDO** | Apenas 1 arquivo existe |

---

## 11. MÉTRICAS DE IMPACTO ESTIMADAS PÓS-IMPLEMENTAÇÃO P1+P2

| Métrica | Estado Atual | Estimativa Pós-P1+P2 |
|---------|-------------|----------------------|
| `font-open-sans` redundantes | 281 | 0 |
| `font-inter` não-numéricos | 151 | ~10 (legítimos restantes) |
| `font-data` adoções | 0 | ~27 (17 numéricos + 10 novos) |
| Any types em áreas críticas | 73 (P1) | ~10 |
| Any types total | 270 | ~170 (após P1+P2) |
| wedo-cyan decorativos | ~50 class-occ | ~0–10 |
| Hex acionáveis não-isentos | 14 | 0 |
| Tokens faltando definição | 3 (`--wedo-green-light`, etc.) | 0 |
| Boilerplate modal LOC | ~3.000 | ~1.500 (com FormDialog) |

---

*Relatório gerado por Task #111 — Frontend Optimization Report*
*Scan realizado em: 2026-04-03 | Código fonte: `/plataforma-lia/src/`*
