> ## ⚠️ CANONICAL DE PRODUÇÃO
>
> **Replit `plataforma-lia/` é canonical de produção** (decisão Paulo 2026-05-23). NÃO é legacy.
>
> - Edits aqui = produção viva
> - Fonte de verdade para todo o frontend Next.js — Estúdio de Agentes, triagem candidato chat público, AgentCard (4 canais: WhatsApp + Voice + VoIP), Wizard goal-first, marketplace, dashboards
> - Consome `lia-agent-system` (FastAPI) + `ats_api` (Rails) via proxy Next em `src/app/api/backend-proxy/*`
>
> Ver `/workspace/CLAUDE.md` para racional completo.

---

# CLAUDE.md — Plataforma LIA · Design System Decisions

> Última atualização: 2026-03-29
> Sprints de padronização executados: 1–10

## Stack
- React 19 + Next.js 15 (App Router)
- Tailwind CSS v3 + shadcn/ui
- next/font (Inter, Open Sans, Crimson Text)

## Tokens WeDo DS

### Tipografia
- Font principal: Inter (via `--font-inter`) — body, UI
- Font secundária: Open Sans (via `--font-open-sans`) — headings, navegação
- Font editorial: Crimson Text (via `--font-crimson`) — destaques editoriais
- NUNCA usar `@import` Google Fonts — apenas `next/font`

### Cores
- Primária: `wedo-coral` (#E87575) — CTAs, destaques
- LIA/IA: `wedo-cyan` (#60BED1) — exclusivo para elementos de IA
- Status semânticos: `status-success` (#16A34A), `status-error` (#DC2626), `status-warning` (#D97706)
- `wedo-apoio-*` tokens: deprecated, zero uso, remoção pendente Sprint final
- Dark mode: `dark:bg-gray-800/900`, `dark:text-gray-100/300/400`, `dark:border-gray-700`

### Bordas
- Cards e modais: `rounded-xl` (12px)
- Inputs e badges: `rounded-lg` (8px)
- Elementos circulares: `rounded-full`
- Tokens semânticos: `border-lia-border-subtle` (gray-200/700), `border-lia-border-default` (gray-300/600)

### Sombras
- `shadow-lia-sm`, `shadow-lia-default`, `shadow-lia-md`, `shadow-lia-lg` — definidos em tailwind.config.ts
- `shadow-lia-focus` — focus ring 2px (0 0 0 2px rgba(0,0,0,0.1))
- `shadow-lia-focus-primary` — focus ring coral

### Espaçamento
- Escala Tailwind padrão (múltiplos de 4px)
- Valores arbitrários [Npx] sem canônico: documentados com `// [OPT-022] px arbitrário`
- Layout tokens: `w-panel-sm/md/lg/xl`, `h-chart-sm`, `h-content-md/lg`, `h-card-lg`

### Z-Index Semântico
- `z-base` (0), `z-raised` (10), `z-dropdown` (40), `z-sticky` (50)
- `z-overlay` (60), `z-toast` (100), `z-select` (200)
- `z-backdrop` (9998), `z-modal` (9999), `z-max` (10000)

### Animações / Motion
- `transition-all` proibido — usar `transition-colors`, `transition-opacity`, `transition-transform`
- framer-motion removido — usar `tailwindcss-animate` (animate-in, fade-in, slide-in-from-*)
- Animações Radix (Dialog, Popover, Dropdown): ativas via data-state

### Ícones
- Biblioteca canônica: `lucide-react`
- Tamanho default inline: `w-4 h-4` (16px)
- Tamanho em navegação/standalone: `w-5 h-5` (20px)
- Ícones decorativos: `aria-hidden="true"` obrigatório
- Top 5 ícones por uso: X (87), Loader2 (81), Brain (68), Search (49), AlertCircle (44)

### Componentes UI
- Base: shadcn/ui — importar de `@/components/ui/*`
- Proibido: `.lia-card` CSS class (usar `<Card>` shadcn), `.lia-input` CSS class (usar `<Input>` shadcn)
- Button variants: `primary`, `secondary`, `ghost`, `destructive`, `outline`, `link`
- Button size default: `h-10` (40px)

### globals.css
- Dividido em: `globals.css` (vars + @layer base) + `src/app/styles/{typography,components,animations,dark-mode}.css`
- Alvo: globals.css < 250 linhas

## Dívidas técnicas conhecidas

| Item | OPT | Descrição |
|------|-----|-----------|
| style={{}} dinâmicos | OPT-043 | ~979 ocorrências — LiaSuperPrompt, EAPTabContent, etc. com TODO |
| wedo-apoio-* | OPT-006 | Tokens deprecated — remover em próxima sprint |
| spacing px arbitrário | OPT-022 | pl-[21px] etc. sem canônico Tailwind |

## Comandos úteis

```bash
# Buscar inline styles dinâmicos pendentes
grep -rn "OPT-043.*TODO" src/

# Buscar border-gray residuais
grep -rn "border-gray-" src/ --include="*.tsx" | grep -v "border-gray-[5-9]"

# Verificar tokens deprecated
grep -rn "wedo-apoio" src/

# Build
cd plataforma-lia && npx next build
```

## Wizard panels canonical pattern (registrado 2026-05-29)

**Contexto:** auditoria 2026-05-29 do wizard de criacao de vaga ("Criando vaga · Descricao") descobriu defeito de canal entre produtor (backend) e consumidor (frontend panel). O `jd_enrichment_node` emitia o sinal canonical `awaiting_jd_input: True` em `build_ws_stage_payload.data` quando o recrutador ainda nao tinha colado a JD (input magro, e.g., "vamos abrir uma vaga"). `JdEnrichmentPanel` ignorava esse sinal e renderizava "Critico - Score: 0/100 - O enriquecimento esta demorando..." com timer de 30s. Saga A-G (`dd2586dc..c288be976`) tratou loop bugs no `jd_gate` mas nunca tocou o consumidor — defeito atravessou.

**Defeito de harness (Hashimoto):** produtor emite sinal correto, consumidor nao le. Classificacao: **computacional × sensor (feedback)** + **computacional × guide (feedforward)**.

### REGRA — Wizard panels DEVEM ler sinais canonical de sub-estado do produtor

Cada panel em `src/components/unified-chat/wizard/panels/*Panel.tsx` recebe `data: Record<string, unknown>` que vem de `build_ws_stage_payload.data` (canonical helper em `lia-agent-system/app/domains/job_creation/helpers/ws_payload_builder.py`). O backend pode emitir, alem dos campos especificos do stage:

- `awaiting_<stage>_input: True` — stage esta idle, aguardando input substancial do recrutador (input thin guard fired). **Panel MUST** renderizar idle state (sem badge, sem timer, sem palavra "demorando")
- `message: string` — Task #1099 invariant, sempre presente, carrega a copy do agente pra esse turno

**Anti-pattern proibido:**

```tsx
// ❌ ANTI-PATTERN — score default 0 vira badge "Critico" em idle/loading
const score = d.quality_score || 0
const badge = getQualityBadge(score)  // 0 -> "Critico"
return (
  <div>
    <div>{badge.label} Score: {score}/100</div>  {/* renderiza sempre, mesmo idle */}
    {enriched ? <Content /> : <LoadingStateWith30sTimer />}
  </div>
)
```

**Pattern canonical:**

```tsx
// ✅ canonical — early-return idle, badge so quando enriched real
export function JdEnrichmentPanel({ data, ... }: Props) {
  const d = data as unknown as JdEnrichmentData
  const enriched = d.jd_enriched
  // ...

  // 1. Idle state — backend signals "awaiting JD content".
  if (d.awaiting_jd_input) {
    return <JdAwaitingInputState message={d.message} />
  }

  return (
    <div>
      {/* 2. Badge — only when enriched (score real, not default-0). */}
      {enriched && <BadgeWithScore score={score} />}
      {/* 3. Loading or content. */}
      {enriched ? <Content enriched={enriched} /> : <JdLoadingState />}
    </div>
  )
}
```

### Sensores canonical

- **Computacional (estatico):** `plataforma-lia/scripts/check_wizard_panel_idle_signals.py` — walks `lia-agent-system/app/domains/job_creation/nodes/*.py` extraindo todos `awaiting_*_input: True` emit sites; para cada sinal cruza com `SIGNAL_TO_PANEL` map e verifica que o panel correspondente le e usa o sinal em conditional. Baseline 2026-05-29: **0 violations, 1 OK** (`awaiting_jd_input -> JdEnrichmentPanel.tsx`). Wired em `.github/workflows/frontend-ci.yml` warn-only enquanto baseline = 0.

- **Runtime (vitest):** `plataforma-lia/src/components/unified-chat/wizard/panels/__tests__/JdEnrichmentPanel.test.tsx` describe "canonical idle state (awaiting_jd_input)" — 3 testes:
  1. `awaiting_jd_input=true` -> renderiza `data-testid="jd-awaiting-input"`, NAO renderiza "Critico"/"0/100"/"demorando"/"Aguardar mais"
  2. `enriched` ausente sem flag idle -> renderiza loading mas NAO badge "Critico"
  3. `enriched` presente -> renderiza badge + score + content

### Como adicionar novo wizard stage que precisa idle state

1. **Backend** (`lia-agent-system/app/domains/job_creation/nodes/<stage>.py`): em branches que detectam "user input is thin", emit:
   ```python
   "ws_stage_payload": build_ws_stage_payload(
       stage="<stage>",
       requires_approval=False,
       data={
           "awaiting_<stage>_input": True,
           "message": msg("<stage>.ask_for_content"),
       },
   ),
   ```
2. **Tipo TS** (`plataforma-lia/src/components/unified-chat/wizard/wizard-types.ts`): adicione `awaiting_<stage>_input?: boolean` + `message?: string` na interface `<Stage>Data`.
3. **Panel** (`plataforma-lia/src/components/unified-chat/wizard/panels/<Stage>Panel.tsx`): early-return idle:
   ```tsx
   if (d.awaiting_<stage>_input) {
     return <<Stage>AwaitingInputState message={d.message} />
   }
   ```
4. **Sensor** (`plataforma-lia/scripts/check_wizard_panel_idle_signals.py`): adicione entry em `SIGNAL_TO_PANEL` mapping `"awaiting_<stage>_input": "<Stage>Panel.tsx"`.
5. **Teste** (`plataforma-lia/src/components/unified-chat/wizard/panels/__tests__/<Stage>Panel.test.tsx`): describe "canonical idle state" copiando template de `JdEnrichmentPanel.test.tsx`.

### Defesa em profundidade

- **Producer-side**: `build_ws_stage_payload` raise ValueError se `data.message` faltar (Task #1099 invariant) — garante que toda copy contextual existe.
- **Consumer-side**: idle state pula badge + loading timer — recrutador ve copy direta do agente, nao mensagem ambigua "demorando".
- **CI**: sensor estatico bloqueia regressao se backend adicionar novo `awaiting_*_input` sem mapping no script + panel handler.


## P0.2 — Acoes do chat (ui_action) nao podem ser ghost (registrado 2026-06-04)

Toda ui_action que o BE pode emitir (contrato em src/lib/api/kanban-assistant.ts) DEVE ter handler no FE: registrada em GLOBAL_UI_ACTION_TYPES (src/types/ui-action.ts, tratada por useUIAction) OU com case/=== num handler page-specific. Acao declarada sem handler = ghost (descartada em silencio quando emitida fora da tela dona) = mentira pro usuario (mesma classe do lia_field_toggles ghost-setting).

Acoes acopladas a uma superficie (ex: modais de candidatos) que precisam ser acionaveis de qualquer tela viram GLOBAIS via padrao navega+re-emite (mirror de settings_open_tab em useUIAction): router.push pra superficie dona + re-emite lia:unhandled_ui_action pro handler page-specific. Nao duplicar modais.

Sensor (computacional, warn-only): scripts/check_ui_action_handlers.py. Baseline 2026-06-04: 2 ghosts conhecidos (compare_jobs, start_candidate_wizard) — follow-up no dominio jobs/wizard. Promover a --blocking quando baseline=0.
