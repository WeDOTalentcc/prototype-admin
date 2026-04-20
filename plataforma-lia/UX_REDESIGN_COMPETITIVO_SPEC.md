# UX Redesign Competitivo — WeDO LIA Chat Experience
## Especificação Técnica Completa para o Time de Desenvolvimento

> **Versão:** 1.0 · **Data:** 2026-04-19  
> **Produto:** WeDOTalent — Plataforma LIA (AI Recruiter)  
> **Escopo:** 7 Sprints UX (UX-1 a UX-7) já implementados + pendências de backend  
> **Repositórios:** `wedotalent02202026` (monorepo) · `ats-api-copia` (Rails) · IA em repo separado  
> **Preparado para:** Cursor AI / Claude Code — leia este arquivo inteiro antes de tocar em qualquer código

---

## Índice

1. [Contexto Estratégico](#1-contexto-estratégico)
2. [Plano Completo Original](#2-plano-completo-original)
3. [Arquitetura Canônica](#3-arquitetura-canônica)
4. [Commits e Histórico Git](#4-commits-e-histórico-git)
5. [Sprint UX-1 — Live Task Feed](#5-sprint-ux-1--live-task-feed-manus-style)
6. [Sprint UX-2 — Task Context Bar + Fullscreen](#6-sprint-ux-2--task-context-bar--fullscreen-ux)
7. [Sprint UX-3 — Split View Cirúrgico](#7-sprint-ux-3--split-view-cirúrgico)
8. [Sprint UX-4 — CalibrationPanel Upgrade](#8-sprint-ux-4--calibrationpanel-upgrade)
9. [Sprint UX-5 — SchedulingPanel](#9-sprint-ux-5--schedulingpanel)
10. [Sprint UX-6 — OutreachCard Multi-Canal](#10-sprint-ux-6--outreachcard-multi-canal)
11. [Sprint UX-7 — Workflow Rail Integration](#11-sprint-ux-7--workflow-rail-integration)
12. [Sistema de Tipos Completo](#12-sistema-de-tipos-completo)
13. [Sistema de Eventos Customizados](#13-sistema-de-eventos-customizados)
14. [APIs e Endpoints](#14-apis-e-endpoints)
15. [Pendências de Backend](#15-pendências-de-backend)
16. [Design System — Regras para este módulo](#16-design-system--regras-para-este-módulo)
17. [Arquivos de Referência no Replit](#17-arquivos-de-referência-no-replit)
18. [Mapa Arquitetura Frontend](#18-mapa-arquitetura-frontend)
19. [Cobertura Competitiva Final](#19-cobertura-competitiva-final)
20. [Itens Futuros (não implementados)](#20-itens-futuros-não-implementados)

---

## 1. Contexto Estratégico

### Por que este redesign?

Análise competitiva da **Tezi** (concorrente adquirido por PE para healthcare) + benchmarks
**Manus** e **ChatGPT canvas** revelou 3 pilares de UX que o WeDO tinha infraestrutura para
entregar mas **nunca ativou**:

1. **Live task evolution** (Manus-style): `thinkingSteps` já vinha do backend, passava como prop
   para `UnifiedMessageList`, mas nunca era renderizado — aparecia só um `<TypingIndicator />` genérico.

2. **Right panel como workspace** (não só wizard): o painel de 340px existia mas só servia o
   wizard de criação de vaga. Podia servir agendamento, análise de candidato, calibração, outreach.

3. **Fullscreen como modo principal de trabalho intenso**: modo fullscreen existia, mas o right
   panel dentro dele era o mesmo estreito de 340px — sem aproveitar o espaço extra.

### Premissa de produto

- **Zero páginas novas** — tudo vive no right panel ou no chat. Paulo quer MENOS páginas.
- **Reuso máximo** — cada componente reusa o que já existe (shadcn/ui, lucide, tokens).
- **Portabilidade Vue** — props tipadas, callbacks `on*`, sem HOCs nem cloneElement.
- **Canônico** — edições sempre no arquivo canônico, nunca no consumidor.

### Onde o WeDO supera a Tezi (vantagens a manter)

| Feature | Tezi | WeDO |
|---------|------|------|
| Cards de candidato | Simples | **ParecerLIACard mais rico** |
| Triagem | Só texto | **WSI Voice + Gemini + Twilio** |
| Outreach | Só email | **Email + WA + Tel + VoIP + WebChat** |
| Multi-tenancy | N/A | **Nativo** |

---

## 2. Plano Completo Original

> Replicação integral do plano aprovado pelo Paulo antes da implementação.

---

### Restrições Canônicas de Arquitetura (CLAUDE.md — Non-Negotiable)

**Antes de qualquer código:**
- ✅ Zero componentes novos quando equivalente existe — verificar `/components/ui/` primeiro
- ✅ Todos os cards DEVEM usar `Card` + `CardContent` de `shadcn/ui` (não criar shell próprio)
- ✅ Todas as cores DEVEM usar tokens: `--lia-*`, `--wedo-*`, `--status-*` (zero hardcode)
- ✅ Animações DEVEM usar: `animate-fade-in-up`, `animate-scale-in-delayed`, `animate-slide-in-up`
- ✅ Novos eventos customizados DEVEM usar namespace `lia:*` (ex: `lia:workflow:started`)
- ✅ Novos tipos de mensagem DEVEM seguir o padrão de `FlowStepMessage` em `UnifiedMessageList`
- ✅ Radix UI animations desabilitadas globalmente — usar keyframes customizadas do tailwind.config
- ✅ Design system v4.2.2 — tokens em `src/styles/design-tokens.css` + `src/lib/design-tokens.ts`

---

### Mapa de Reuso Canônico (auditado — zero invenção)

| Componente planejado | Reusa? | O que reutilizar | O que é novo |
|---------------------|--------|-----------------|-------------|
| ThinkingStepsCard | ✅ Parcial | `FlowStepMessage` + `Card` shadcn | Adaptar para thinkingSteps prop |
| ActiveTaskPill | ✅ Parcial | `Badge` + `--lia-brand-primary` token | Lógica de exibir task name do wizard stage |
| WorkflowRail (bottom bar) | ✅ Parcial | `BulkActionsBar` layout + `Card` + `status-*` tokens | Lógica de workflow tracking |
| CalibrationPanel upgrade | ✅ Maioria | CalibrationPanel EXISTENTE (já tem thumbs!) | Candidatos reais + pool counter |
| SchedulingPanel | ✅ Parcial | `InterviewSchedulingModal` existente + `Card` + `Tabs` shadcn | Grid semanal visual, multi-entrevista |
| OutreachCard | ✅ Parcial | `Card` + `Badge` + `lia-icon.tsx` | Card por canal (email/WA/phone/voip/chat) |
| CandidateProfilePanel | ✅ Maioria | `CandidateCard` existente + `Card` + `Tabs` | Versão "painel direito" |
| PipelineSnapshotPanel | ✅ Parcial | `PipelineStagesCarousel` + `progress.tsx` | Mini-kanban leve |
| Novos eventos workflow:* | ✅ Total | Padrão `window.dispatchEvent(new CustomEvent(...))` | Novos tipos |
| Novos tipos de mensagem | ✅ Total | Padrão `metadata` + UnifiedMessageList | Cases: `outreach_message` |

**Tudo que pode ser reusado, SERÁ reusado. Nada criado do zero se já existe.**

---

### Estado do codebase antes do redesign (auditado)

| Componente | Arquivo | Status antes |
|-----------|---------|--------|
| thinkingSteps prop | `UnifiedMessageList.tsx:20` | ✅ Existia, ❌ NUNCA RENDERIZADO |
| Fullscreen mode | `UnifiedChat.tsx:187` | ✅ Existia e funcionava |
| Right panel (wizard only) | `UnifiedChat.tsx:264-277` | ✅ Existia, escopo limitado |
| DynamicContextPanel router | `wizard/DynamicContextPanel.tsx` | ✅ 12 stages lazy-loaded |
| Mode switcher (3 modos) | `UnifiedChatHeader.tsx:120-148` | ✅ Existia |
| SmartSuggestions chips | `SmartSuggestions.tsx` | ✅ Existia, genérico |
| SwitchTaskModal (⌘K) | `UnifiedChat.tsx` | ✅ Existia |
| CalibrationPanel | `wizard/panels/CalibrationPanel.tsx` | ✅ Existia, sem candidatos reais |
| PlanProgressCard | `UnifiedMessageList.tsx` | ✅ Existia (execution plan) |
| FlowStepMessage | `UnifiedMessageList.tsx` | ✅ Existia (workflow visual) |

**Gap central**: Temos a data (thinkingSteps, toolCalls, executionPlan) mas não a UX para exibi-la.

---

### Os 7 Pilares do Redesign

#### Pilar 1 — Live Task Feed (Manus-style)

Enquanto a LIA trabalha, o recrutador vê em tempo real:
```
⟳ Buscando candidatos compatíveis...
✓ Encontrados 847 perfis
⟳ Aplicando filtros de experiência...
✓ 124 passaram nos critérios
⟳ Ranqueando por aderência à vaga...
```

#### Pilar 2 — Right Panel como Workspace Adaptativo

| Contexto | Trigger | Conteúdo do Panel |
|----------|---------|------------------|
| Wizard ativo | stage != null | 12 panels existentes (sem mudança) |
| Análise de candidato | LIA menciona candidato específico | `CandidateProfilePanel` |
| Agendamento | LIA propõe entrevista | `SchedulingPanel` (grade de horários, não modal) |
| Calibração standalone | recrutador pede "ajustar critérios" | `CalibrationPanel` standalone |
| Pipeline view | LIA relata status da vaga | `PipelineSnapshotPanel` |
| Sem contexto | chat livre | Panel fechado (100% conversa) |

#### Pilar 3 — Fullscreen como modo padrão para trabalho intenso

1. Right panel responsivo: `sidebar = 340px`, `fullscreen = 420px`
2. Task Context Bar no header (padrão Tezi): pill com workflow ativo + `⌘K`
3. Auto-suggest fullscreen quando wizard inicia (toast único por sessão)

#### Pilar 4 — Split View Cirúrgico no Wizard

**Stages que NÃO abrem split view** (conversa pura, full-width):
`intake`, `jd_enrichment`, `bigfive`, `salary`, `competency`, `wsi_questions`, `eligibility`

**Stages que PRECISAM de split view** (visual):
`review`, `publish`, `calibration`, `handoff`, `done`, `scheduling`

#### Pilar 5 — Agendamento como Workspace Panel

Layout:
```
┌─────────────────────────────────────────┐
│ Agendar entrevista · 1 de 2             │
│ Duração: [45min ▼]  Fuso: [BRT ▼]      │
├─────────────────────────────────────────┤
│       Seg 14   Ter 15   Qua 16   Qui 17 │
│ 09:00 [     ] [  ✓  ] [     ] [     ]  │
│ 10:00 [     ] [     ] [     ] [  ✓  ]  │
│ 14:00 [  ✓  ] [     ] [     ] [     ]  │
├─────────────────────────────────────────┤
│              [Confirmar →]              │
└─────────────────────────────────────────┘
```

Multi-entrevista paginada: "1 de 2" → Confirmar → "2 de 2" → Concluir

#### Pilar 6 — Outreach Multi-Canal Inline com Aprovação

Componente único `OutreachCard` por canal (email / WhatsApp / phone / webchat / voip).  
LIA gera conteúdo → recrutador revisa inline → Editar (right panel) ou Enviar.

#### Pilar 7 — Workflow Rail como Hub Global de Tarefas

```
UnifiedChat ──────────────────────────────┐
(wizard, outreach, calibração via LIA)     ▼
                                  ┌──────────────────┐
Funil de Talentos ─────────────►  WORKFLOW RAIL      │
(mover candidato, triagem, outreach) (rodapé global) │
                                  └──────────────────┘
                                           ▲
Agent Studio ─────────────────────────────┘
(fluxos automáticos por agentes)
```

---

### O que NÃO fazer

- ❌ Criar novas páginas (tudo vive no right panel ou no chat)
- ❌ Reescrever o UnifiedChat do zero (é incremental)
- ❌ Simplificar nav para 4 itens agora (decisão de produto maior)
- ❌ Substituir candidate cards por texto simples (WeDO tem vantagem visual)
- ❌ Scheduling como página separada (vai para o workspace panel)

---

### Sequência de execução original (sprints)

```
Sprint UX-1 (2 dias) — Live Task Feed                    ✅ IMPLEMENTADO
Sprint UX-2 (2 dias) — Task Context Bar + Fullscreen UX  ✅ IMPLEMENTADO
Sprint UX-3 (2 dias) — Split view cirúrgico              ✅ IMPLEMENTADO
Sprint UX-4 (3 dias) — Calibration upgrade               ✅ FRONTEND IMPLEMENTADO (backend pendente)
Sprint UX-5 (3 dias) — Agendamento como workspace panel  ✅ FRONTEND IMPLEMENTADO (backend pendente)
Sprint UX-6 (3 dias) — Outreach multi-canal inline       ✅ FRONTEND IMPLEMENTADO (backend pendente)
Sprint UX-7 (3 dias) — Workflow Rail integration         ✅ IMPLEMENTADO
Sprint UX-8 (2 dias) — Right panel workspace adicional   🔴 PLANEJADO (não implementado)
Sprint UX-9 (1 dia)  — SmartSuggestions pós-workflow     🔴 PLANEJADO (não implementado)
```

---

## 3. Arquitetura Canônica

### Repositórios

| Repositório | Branch principal | Localização | Responsabilidade |
|-------------|-----------------|-------------|-----------------|
| `wedotalent02202026` | `develop` / `replit-sync` | Monorepo no Replit | Frontend (Next.js) + FastAPI (IA) |
| `ats-api-copia` | `develop` | Replit | Rails API (ATS) |
| IA Separado | TBD | TBD | Agentes LangGraph isolados (futuro) |

### Estrutura de Diretórios — Frontend

```
/home/runner/workspace/plataforma-lia/src/
├── app/
│   ├── api/backend-proxy/         ← 362 rotas proxy (Next.js → FastAPI/Rails)
│   ├── (dashboard)/               ← Páginas principais (vagas, funil, chat, etc.)
│   └── layout.tsx                 ← Layout global com WorkflowRail
├── components/
│   ├── unified-chat/              ← ⭐ MÓDULO PRINCIPAL DESTE REDESIGN
│   │   ├── UnifiedChat.tsx        ← Shell principal (3 modos: sidebar/floating/fullscreen)
│   │   ├── UnifiedChatHeader.tsx  ← Header com breadcrumb + ActiveTaskPill + mode switcher
│   │   ├── UnifiedChatInput.tsx   ← Textarea + @mention + /commands + file upload
│   │   ├── UnifiedMessageList.tsx ← Lista de mensagens + ThinkingStepsCard + OutreachCard
│   │   ├── ThinkingStepsCard.tsx  ← ✅ NOVO — Live task feed (UX-1)
│   │   ├── OutreachCard.tsx       ← ✅ NOVO — Outreach multi-canal (UX-6)
│   │   └── wizard/
│   │       ├── DynamicContextPanel.tsx  ← Router de panels com SPLIT_STAGES
│   │       ├── wizard-types.ts          ← Tipos + WizardStage union
│   │       └── panels/
│   │           ├── CalibrationPanel.tsx ← ✅ MODIFICADO — pool counter + must-haves
│   │           ├── SchedulingPanel.tsx  ← ✅ NOVO — grade semanal (UX-5)
│   │           ├── ReviewPanel.tsx
│   │           ├── PublishPanel.tsx
│   │           ├── HandoffPanel.tsx
│   │           └── [outros panels existentes...]
│   ├── workflow-rail/
│   │   ├── WorkflowRail.tsx       ← Componente visual do rodapé (pré-existente)
│   │   └── useWorkflowRail.ts     ← ✅ MODIFICADO — listeners workflow:* events (UX-7)
│   └── ui/                        ← shadcn/ui base components
├── hooks/
│   └── useChatContext.ts          ← Contexto global do chat (chatThinkingSteps, etc.)
└── styles/
    └── design-tokens.css          ← Tokens CSS (--lia-*, --wedo-*, --status-*)
```

### Estrutura de Diretórios — Backend (FastAPI/IA)

```
/home/runner/workspace/lia-agent-system/app/
├── api/v1/
│   ├── conversations.py           ← GET/POST/PATCH /conversations
│   ├── vacancies.py               ← GET/POST /vacancies + preview candidates
│   ├── calibration.py             ← POST /calibration/feedback
│   └── scheduling.py              ← GET /scheduling/slots (pendente)
├── domains/
│   ├── wizard/
│   │   ├── agent.py               ← Agente LangGraph (14 stages)
│   │   ├── nodes/
│   │   │   ├── intake_node.py
│   │   │   ├── jd_enrichment_node.py
│   │   │   ├── calibration_node.py ← Precisa enviar pool_count + criteria
│   │   │   └── scheduling_node.py  ← Precisa enviar ws_stage_payload("scheduling")
│   │   └── state.py               ← WizardState (stage machine)
│   └── sourcing/
│       └── outreach_agent.py      ← Precisa retornar metadata.type = "outreach_message"
└── shared/
    ├── websocket/
    │   └── ws_helpers.py          ← ws_stage_payload() + ws_thinking_steps()
    └── prompts/
        └── interaction_patterns.py
```

### Fluxo de dados — WebSocket (FastAPI → Frontend)

```
FastAPI (LangGraph nodes)
    ↓ ws_stage_payload(stage, data)
    ↓ ws_thinking_steps(steps)
WebSocket /ws/chat/{conversation_id}
    ↓
useChatContext (hook global)
    ↓ chatThinkingSteps: string[]
    ↓ dynamicPanel: { stage, data }
    ↓ isThinking: boolean
UnifiedMessageList ← ThinkingStepsCard
UnifiedChat ← DynamicContextPanel ← SchedulingPanel / CalibrationPanel
```

---

## 4. Commits e Histórico Git

### Commits do redesign UX (local — `develop`)

```
1d5b6a77  docs(ux): add DEVELOPER_HANDOFF_UX_REDESIGN.md — 7 sprints UX competitivo
5140997a  feat(ux): UX redesign competitivo — 7 pilares Tezi/Manus (Sprints UX-1 a UX-7)
```

### Commit no Replit (incluído em `c6220768f`)

```
c6220768f  Improve job creation and candidate sourcing workflows
           └── plataforma-lia/src/components/unified-chat/ThinkingStepsCard.tsx (novo)
           └── plataforma-lia/src/components/unified-chat/OutreachCard.tsx (novo)
           └── plataforma-lia/src/components/unified-chat/wizard/panels/SchedulingPanel.tsx (novo)
           └── plataforma-lia/src/components/unified-chat/UnifiedChat.tsx (modificado)
           └── plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx (modificado)
           └── plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx (modificado)
           └── plataforma-lia/src/components/unified-chat/wizard/DynamicContextPanel.tsx (modificado)
           └── plataforma-lia/src/components/unified-chat/wizard/panels/CalibrationPanel.tsx (modificado)
           └── plataforma-lia/src/components/unified-chat/wizard/wizard-types.ts (modificado)
           └── plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts (modificado)
           └── plataforma-lia/DEVELOPER_HANDOFF_UX_REDESIGN.md (novo)
```

### Commits de contexto anteriores (develop)

```
ff293913  feat(byok): Choose Your AI — frontend UI completo
aec04a92  fix(ds): replace wedo-orange token com status-error/5
a62fda0c  feat(kanban): WhatsApp template + onSend wiring
bdc59f37  feat(kanban): Gerenciar Proposta Phase 1
a169e2bb  fix(kanban): 4 bugs confirmados no job-kanban
68a2b366  test(e2e): suite Playwright criação manual de vaga — 37 testes
0acf9ac6  feat(auth): MFA email OTP no login via Rails ats_api
```

### Commits históricos Replit (contexto)

```
5cf89193e  Task #591: Saneamento Fase 1 P0 — chat unificado
a174d7d67  Task #591: Saneamento Fase 1 P0 — chat unificado
d46fd1dae  Remove unnecessary data from the system
d63271238  Add new components and evaluation results for job postings
9eafa6207  fix(tools): P0/P1 hardening — multi-tenancy + capacity
cd89fcf8f  feat(eval): unified diagnostic battery for LIA via Playwright
```

---

## 5. Sprint UX-1 — Live Task Feed (Manus-style)

### Problema resolvido

`chatThinkingSteps: string[]` vinha do backend, passava como prop para `UnifiedMessageList`,
mas **nunca era renderizado**. O recrutador via apenas um spinner genérico.

### Solução: `ThinkingStepsCard.tsx`

**Arquivo canônico:** `plataforma-lia/src/components/unified-chat/ThinkingStepsCard.tsx`

```tsx
"use client"

import React from "react"
import { CheckCircle2, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ThinkingStepsCardProps {
  steps: string[]
}

export function ThinkingStepsCard({ steps }: ThinkingStepsCardProps) {
  if (!steps || steps.length === 0) {
    return (
      <div className="flex items-center gap-2 px-1 py-2">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-wedo-cyan" aria-hidden="true" />
        <span className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
          Pensando...
        </span>
      </div>
    )
  }

  return (
    <div className="animate-fade-in-up rounded-xl border border-lia-border-subtle bg-lia-bg-secondary px-3 py-2.5 max-w-[85%] space-y-1.5">
      {steps.map((step, i) => {
        const isActive = i === steps.length - 1
        return (
          <div key={i} className="flex items-start gap-2">
            {isActive ? (
              <Loader2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 animate-spin text-wedo-cyan" aria-hidden="true" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-status-success" aria-hidden="true" />
            )}
            <span className={cn(
              "text-xs leading-5 font-['Open_Sans',sans-serif]",
              isActive ? "text-lia-text-primary font-medium" : "text-lia-text-secondary"
            )}>
              {step}
            </span>
          </div>
        )
      })}
    </div>
  )
}
```

### Modificação em `UnifiedMessageList.tsx`

```diff
- import { TypingIndicator } from "@/components/chat/typing-indicator"
+ import { ThinkingStepsCard } from "./ThinkingStepsCard"

  // No bloco de rendering do isThinking:
- {isThinking && !streamingContent && (
-   <div className="flex items-center gap-2"><TypingIndicator /></div>
- )}
+ {isThinking && !streamingContent && (
+   <div className="group"><ThinkingStepsCard steps={thinkingSteps} /></div>
+ )}
```

**Prop já existia:** `thinkingSteps: string[]` já estava na interface Props — apenas não usado.

### Como o backend envia os steps

```python
# Em qualquer node do LangGraph que queira exibir progresso:
from app.shared.websocket.ws_helpers import ws_thinking_steps

await ws_thinking_steps(
    conversation_id=state["conversation_id"],
    steps=[
        "Buscando candidatos compatíveis...",   # step ativo
    ]
)

# Quando step completa, adicionar ao array:
await ws_thinking_steps(
    steps=[
        "Buscando candidatos compatíveis...",   # concluído (não é o último)
        "Encontrados 847 perfis",               # concluído
        "Aplicando filtros de experiência...",  # ativo (último)
    ]
)
```

### Tokens de design usados

| Token | Uso |
|-------|-----|
| `wedo-cyan` | Spinner do step ativo (exclusivo para elementos LIA/IA) |
| `status-success` | Ícone CheckCircle2 dos steps concluídos |
| `lia-bg-secondary` | Fundo do card |
| `lia-border-subtle` | Borda do card |
| `lia-text-primary` | Texto do step ativo |
| `lia-text-secondary` | Texto dos steps concluídos |
| `animate-fade-in-up` | Animação de entrada do card |
| `rounded-xl` | Border radius do card (12px — padrão para cards) |

---

## 6. Sprint UX-2 — Task Context Bar + Fullscreen UX

### 2a — ActiveTaskPill no Header

**Arquivo:** `plataforma-lia/src/components/unified-chat/UnifiedChatHeader.tsx`

Nova prop adicionada à interface `Props`:

```typescript
interface Props {
  // ... props existentes (connectionStatus, onModeChange, onSwitchTask, etc.) ...
  activeTaskLabel?: string | null   // ex: "Criando vaga · Calibração"
}
```

Pill renderizada no left section do header (após connection dot):

```tsx
{activeTaskLabel && (
  <button
    onClick={onSwitchTask}
    className="flex items-center gap-1 px-2 py-0.5 rounded-lg border border-lia-border-subtle
               bg-lia-bg-secondary text-lia-text-secondary hover:text-lia-text-primary
               hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none
               flex-shrink-0 max-w-[200px]"
    title={`${activeTaskLabel} — trocar conversa (⌘K)`}
  >
    <span className="text-xs truncate">{activeTaskLabel}</span>
    <ArrowRightLeft className="w-3 h-3 flex-shrink-0 opacity-60" aria-hidden="true" />
  </button>
)}
```

**Nota de design:**
- `rounded-lg` para pill/badge (8px — não `rounded-xl` que é para cards)
- `transition-colors` NUNCA `transition-all` (regra DS)
- `motion-reduce:transition-none` para acessibilidade

### 2b — WIZARD_STAGE_LABELS

**Arquivo:** `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`

```typescript
const WIZARD_STAGE_LABELS: Record<string, string> = {
  intake:        "Criando vaga · Início",
  jd_enrichment: "Criando vaga · Descrição",
  bigfive:       "Criando vaga · Perfil",
  salary:        "Criando vaga · Salário",
  competency:    "Criando vaga · Competências",
  wsi_questions: "Criando vaga · Triagem",
  eligibility:   "Criando vaga · Elegibilidade",
  review:        "Criando vaga · Revisão",
  publish:       "Criando vaga · Publicação",
  calibration:   "Calibrando · Candidatos",
  handoff:       "Criando vaga · Finalização",
  done:          "Vaga criada",
  scheduling:    "Agendando · Entrevistas",
}

// Derivação do label a partir do stage atual:
const activeTaskLabel = dynamicPanel?.stage
  ? (WIZARD_STAGE_LABELS[dynamicPanel.stage] ?? dynamicPanel.stage)
  : null
```

### 2c — Toast de sugestão fullscreen

Aparece **uma vez por sessão** quando wizard inicia em modo sidebar/floating.
Auto-dismiss após 7 segundos.

```typescript
// Estado e ref:
const [showFullscreenHint, setShowFullscreenHint] = useState(false)
const fullscreenHintShown = useRef(false)

// useEffect que dispara o toast:
useEffect(() => {
  if (
    dynamicPanel?.stage === "intake" &&
    mode !== "fullscreen" &&
    renderMode !== "inline" &&
    !fullscreenHintShown.current
  ) {
    fullscreenHintShown.current = true
    setShowFullscreenHint(true)
    const timer = setTimeout(() => setShowFullscreenHint(false), 7000)
    return () => clearTimeout(timer)
  }
}, [dynamicPanel?.stage, mode, renderMode])
```

JSX do toast (renderizado acima do `<UnifiedChatInput />`):

```tsx
{showFullscreenHint && (
  <div className="px-4 pb-1">
    <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg
                    border border-lia-border-subtle bg-lia-bg-secondary animate-fade-in-up">
      <span className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
        Tela cheia melhora a experiência do wizard
      </span>
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <button
          onClick={() => {
            handleModeChange("fullscreen")
            setShowFullscreenHint(false)
          }}
          className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-gray-900 text-white
                     text-[10px] font-medium transition-colors hover:bg-gray-800"
        >
          <Maximize2 className="w-3 h-3" aria-hidden="true" />
          Tela cheia
        </button>
        <button
          onClick={() => setShowFullscreenHint(false)}
          className="p-0.5 text-lia-text-disabled hover:text-lia-text-secondary transition-colors"
          aria-label="Fechar sugestão"
        >
          <X className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      </div>
    </div>
  </div>
)}
```

### 2d — Right panel width responsivo

```tsx
// No JSX do UnifiedChat, o container do panel direito:
<div className={cn(
  "flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto",
  effectiveMode === "fullscreen" ? "w-[420px]" : "w-[340px]"
)}>
  <DynamicContextPanel ... />
</div>
```

| Modo | Largura | Uso |
|------|---------|-----|
| sidebar | 340px | Espaço padrão |
| floating | 340px | Mesma lógica |
| fullscreen | 420px | Mais espaço para calendário, perfis, calibração |

---

## 7. Sprint UX-3 — Split View Cirúrgico

### Problema resolvido

O split view abria para **todos os 12 stages do wizard**, incluindo stages 1-7 que são
conversação pura (intake, jd_enrichment, bigfive, salary, competency, wsi_questions, eligibility).
Isso criava um painel lateral vazio durante as fases mais conversacionais.

### Solução: SPLIT_STAGES

**Arquivo:** `plataforma-lia/src/components/unified-chat/wizard/DynamicContextPanel.tsx`

```typescript
export const SPLIT_STAGES: WizardStage[] = [
  "review",       // stage 8 — JD final para aprovação
  "publish",      // stage 9 — seleção de plataformas
  "calibration",  // stage 10 — candidatos reais + thumbs
  "handoff",      // stage 11 — confirmação visual
  "done",         // stage 12 — concluído
  "scheduling",   // panel de agendamento (além do wizard core)
]
```

**Modificação em `UnifiedChat.tsx`:**

```typescript
// Import atualizado:
import { DynamicContextPanel, SPLIT_STAGES } from "./wizard/DynamicContextPanel"
import type { WizardStage } from "./wizard/wizard-types"

// Condição para mostrar o panel:
// Antes:
const hasDynamicPanel = !!dynamicPanel
// Depois:
const hasDynamicPanel = !!dynamicPanel &&
  SPLIT_STAGES.includes(dynamicPanel.stage as WizardStage)
```

**Resultado:**
- Stages 1-7 (`intake` → `eligibility`): chat 100% full-width, sem split
- Stages 8-12 (`review` → `done`) + `scheduling`: split view abre automaticamente

**Nota importante:** O `activeTaskLabel` (pill no header) continua aparecendo para
**todos os stages 1-12** — apenas o split view é limitado.

---

## 8. Sprint UX-4 — CalibrationPanel Upgrade

**Arquivo:** `plataforma-lia/src/components/unified-chat/wizard/panels/CalibrationPanel.tsx`

### Pool Counter

O backend deve enviar `pool_count: number` no payload do stage `calibration`.
Atualizado via WebSocket após cada feedback de thumbs.

```typescript
// Tipos estendidos para o panel:
interface CriterionItem {
  label: string
  type: "must_have" | "sourcing"
}

// Cast do data do stage:
const d = data as unknown as CalibrationData & {
  pool_count?: number
  criteria?: CriterionItem[]
}
const poolCount = d.pool_count ?? null
```

Renderização no header da seção de calibração:

```tsx
{poolCount !== null && (
  <span className="flex items-center gap-1 text-[10px] text-wedo-cyan font-medium font-['Open_Sans',sans-serif]">
    <Users className="w-3 h-3" aria-hidden="true" />
    {poolCount.toLocaleString("pt-BR")} compatíveis
  </span>
)}
```

### Separação Must-haves vs Sourcing Constraints

```tsx
{/* Must-haves — chips cinza escuro (requisitos eliminatórios) */}
{mustHaves.length > 0 && (
  <div>
    <p className="text-[10px] font-semibold text-lia-text-disabled uppercase tracking-wider mb-1.5">
      Must-haves
    </p>
    <div className="flex flex-wrap gap-1.5">
      {mustHaves.map((c, i) => (
        <span key={i} className="px-2 py-0.5 rounded-full bg-gray-900 text-white text-[10px] font-medium">
          {c.label}
        </span>
      ))}
    </div>
  </div>
)}

{/* Sourcing constraints — chips com borda (preferências) */}
{sourcing.length > 0 && (
  <div>
    <p className="text-[10px] font-semibold text-lia-text-disabled uppercase tracking-wider mb-1.5">
      Preferências de sourcing
    </p>
    <div className="flex flex-wrap gap-1.5">
      {sourcing.map((c, i) => (
        <span key={i} className="px-2 py-0.5 rounded-full border border-lia-border-subtle
                                 text-lia-text-secondary text-[10px]">
          {c.label}
        </span>
      ))}
    </div>
  </div>
)}
```

### Payload esperado do backend (stage calibration)

```json
{
  "type": "wizard_stage",
  "stage": "calibration",
  "data": {
    "candidates": [
      {
        "id": "cand-123",
        "name": "João Silva",
        "current_title": "Software Engineer Sr.",
        "current_company": "Itaú",
        "match_score": 0.87,
        "match_criteria": [
          { "criterion": "Python 5+ anos", "score": 0.95, "met": true },
          { "criterion": "Experiência Fintech", "score": 0.78, "met": true }
        ]
      }
    ],
    "threshold": 3,
    "approved_count": 1,
    "complete": false,
    "pool_count": 847,
    "criteria": [
      { "label": "5+ anos Python", "type": "must_have" },
      { "label": "Kubernetes", "type": "must_have" },
      { "label": "Experiência Fintech", "type": "sourcing" },
      { "label": "Inglês avançado", "type": "sourcing" }
    ]
  },
  "completeness": 0.33,
  "requires_approval": false
}
```

---

## 9. Sprint UX-5 — SchedulingPanel

### Arquivo novo: `src/components/unified-chat/wizard/panels/SchedulingPanel.tsx`

Código completo implementado:

```tsx
"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { ChevronDown, ChevronRight, Check, CalendarDays, Clock } from "lucide-react"

interface SlotItem {
  date: string       // ISO date string "YYYY-MM-DD"
  day_label: string  // ex: "Seg 14"
  time: string       // ex: "09:00"
  available: boolean
}

interface InterviewItem {
  id: string
  title: string          // ex: "Triagem Técnica"
  type?: string
  candidate_name?: string
}

interface SchedulingData {
  interviews?: InterviewItem[]
  available_slots?: SlotItem[]
  job_title?: string
  candidate_name?: string
  vacancy_id?: string
}

interface Props {
  data: Record<string, unknown>
  onApprove?: () => void
}

const DURATION_OPTIONS = ["30 min", "45 min", "60 min", "90 min"]
const TIMEZONE_OPTIONS = ["BRT (UTC-3)", "AMT (UTC-4)", "UTC"]

export function SchedulingPanel({ data, onApprove }: Props) {
  const d = data as SchedulingData
  const interviews = d.interviews ?? []
  const slots = d.available_slots ?? generatePlaceholderSlots()
  const jobTitle = d.job_title ?? "Vaga"
  const candidateName = d.candidate_name ?? ""

  const [currentIdx, setCurrentIdx] = useState(0)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [duration, setDuration] = useState("45 min")
  const [timezone, setTimezone] = useState("BRT (UTC-3)")
  const [confirmedSlots, setConfirmedSlots] = useState<Record<number, string>>({})

  const totalInterviews = Math.max(interviews.length, 1)
  const currentInterview = interviews[currentIdx] ?? { id: "1", title: "Triagem", candidate_name: candidateName }
  const isLastInterview = currentIdx === totalInterviews - 1
  const allDone = Object.keys(confirmedSlots).length === totalInterviews

  // Group slots by day
  const days = Array.from(new Set(slots.map((s) => s.date))).slice(0, 4)
  const times = Array.from(new Set(slots.map((s) => s.time))).sort()

  const handleConfirm = () => {
    if (!selectedSlot) return
    const next = { ...confirmedSlots, [currentIdx]: selectedSlot }
    setConfirmedSlots(next)
    setSelectedSlot(null)

    if (isLastInterview) {
      window.dispatchEvent(new CustomEvent("lia:scheduling-confirmed", {
        detail: { slots: next, interviews, vacancyId: d.vacancy_id },
      }))
      onApprove?.()
    } else {
      setCurrentIdx((i) => i + 1)
    }
  }

  if (allDone) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 px-4 py-10 text-center">
        <div className="w-10 h-10 rounded-full bg-status-success/10 flex items-center justify-center">
          <Check className="w-5 h-5 text-status-success" />
        </div>
        <p className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
          {totalInterviews === 1 ? "Entrevista agendada!" : `${totalInterviews} entrevistas agendadas!`}
        </p>
        <p className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
          Os convites serão enviados por email.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Interview info + pagination */}
      <div className="px-4 py-3 border-b border-lia-border-subtle">
        {totalInterviews > 1 && (
          <div className="flex items-center gap-1.5 mb-1">
            {Array.from({ length: totalInterviews }).map((_, i) => (
              <div key={i} className={cn(
                "h-1 rounded-full transition-[width,background-color] duration-200",
                i < currentIdx  ? "w-6 bg-status-success" :
                i === currentIdx ? "w-6 bg-wedo-cyan" :
                                   "w-3 bg-lia-border-subtle"
              )} />
            ))}
            <span className="ml-auto text-[10px] text-lia-text-disabled">
              {currentIdx + 1}/{totalInterviews}
            </span>
          </div>
        )}
        <div className="flex items-start gap-2">
          <CalendarDays className="w-4 h-4 text-wedo-cyan mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-lia-text-primary font-['Open_Sans',sans-serif] truncate">
              {currentInterview.title}
              {totalInterviews > 1 && (
                <span className="text-lia-text-secondary font-normal ml-1">
                  · {currentIdx + 1} de {totalInterviews}
                </span>
              )}
            </p>
            <p className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif] truncate">
              {currentInterview.candidate_name || candidateName || jobTitle}
            </p>
          </div>
        </div>
      </div>

      {/* Duration + timezone */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-lia-border-subtle">
        <Clock className="w-3.5 h-3.5 text-lia-text-disabled flex-shrink-0" aria-hidden="true" />
        <NativeSelect value={duration} onChange={setDuration} options={DURATION_OPTIONS} aria-label="Duração" />
        <span className="text-lia-border-default">·</span>
        <NativeSelect value={timezone} onChange={setTimezone} options={TIMEZONE_OPTIONS} aria-label="Fuso horário" />
      </div>

      {/* Week grid */}
      <div className="flex-1 overflow-x-auto overflow-y-auto px-4 py-3">
        <table className="w-full border-collapse text-xs font-['Open_Sans',sans-serif]">
          <thead>
            <tr>
              <th className="w-12 pb-2 text-left text-lia-text-disabled font-normal" />
              {days.map((date) => {
                const slot = slots.find((s) => s.date === date)
                return (
                  <th key={date} className="pb-2 text-center font-medium text-lia-text-secondary min-w-[56px]">
                    {slot?.day_label ?? date}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {times.map((time) => (
              <tr key={time}>
                <td className="py-0.5 pr-2 text-right text-lia-text-disabled whitespace-nowrap align-middle">
                  {time}
                </td>
                {days.map((date) => {
                  const slot = slots.find((s) => s.date === date && s.time === time)
                  const key = `${date}|${time}`
                  const isSelected = selectedSlot === key
                  const isAvailable = slot?.available ?? false

                  return (
                    <td key={date} className="py-0.5 px-1 text-center">
                      {isAvailable ? (
                        <button
                          onClick={() => setSelectedSlot(isSelected ? null : key)}
                          className={cn(
                            "w-full py-1.5 rounded-md border text-[10px] font-medium transition-colors motion-reduce:transition-none",
                            isSelected
                              ? "bg-gray-900 border-gray-900 text-white"
                              : "border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:border-lia-border-default hover:bg-lia-bg-secondary"
                          )}
                          aria-pressed={isSelected}
                          aria-label={`${time} em ${slot?.day_label}`}
                        >
                          {isSelected ? <Check className="w-3 h-3 mx-auto" aria-hidden="true" /> : "·"}
                        </button>
                      ) : (
                        <div className="w-full py-1.5 rounded-md bg-lia-bg-tertiary opacity-30" aria-hidden="true" />
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Confirm footer */}
      <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle">
        <button
          onClick={handleConfirm}
          disabled={!selectedSlot}
          className={cn(
            "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none font-['Open_Sans',sans-serif]",
            selectedSlot
              ? "bg-gray-900 text-white hover:bg-gray-800"
              : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
          )}
        >
          {isLastInterview ? "Confirmar agendamento" : "Confirmar e avançar"}
          <ChevronRight className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
```

### WizardStage atualizado

```typescript
// wizard-types.ts
export type WizardStage =
  | "intake" | "jd_enrichment" | "bigfive" | "salary"
  | "competency" | "wsi_questions" | "eligibility"
  | "review" | "publish" | "calibration" | "handoff" | "done"
  | "scheduling"   // ← adicionado neste sprint (UX-5)
```

### DynamicContextPanel — lazy import

```typescript
// wizard/DynamicContextPanel.tsx
const SchedulingPanel = lazy(() =>
  import("./panels/SchedulingPanel").then((m) => ({ default: m.SchedulingPanel }))
)

// No switch:
case "scheduling":
  return <SchedulingPanel data={data} onApprove={onApprove} />
```

### Como o backend aciona o SchedulingPanel

```python
# Em qualquer agent/node que proponha agendamento:
from app.shared.websocket.ws_helpers import ws_stage_payload

await ws_stage_payload(
    conversation_id=state["conversation_id"],
    stage="scheduling",
    data={
        "interviews": [
            {"id": "int-1", "title": "Triagem", "candidate_name": "João Silva"},
            {"id": "int-2", "title": "Técnica", "candidate_name": "João Silva"},
        ],
        "available_slots": [
            {"date": "2026-04-21", "day_label": "Seg 21", "time": "09:00", "available": True},
            {"date": "2026-04-21", "day_label": "Seg 21", "time": "10:00", "available": False},
            # ... mais slots
        ],
        "vacancy_id": str(vacancy.id),
        "candidate_name": "João Silva",
        "job_title": "Engenheiro de Software Sr.",
    },
    completeness=0.5,
    requires_approval=True,
)
```

O SPLIT_STAGES já inclui `"scheduling"`, então o panel abre automaticamente ao receber este payload.

---

## 10. Sprint UX-6 — OutreachCard Multi-Canal

### Arquivo novo: `src/components/unified-chat/OutreachCard.tsx`

### Interface pública exportada

```typescript
export interface OutreachData {
  channel: "email" | "whatsapp" | "phone" | "webchat" | "voip"
  candidate_name: string
  candidate_id?: string

  // email
  subject?: string
  body?: string

  // whatsapp
  phone?: string
  template?: string

  // phone/voip — script de ligação
  script?: string[]              // ex: ["Confirmar interesse", "Alinhamento salarial"]
  estimated_duration?: string    // ex: "5-10 min"

  // webchat — mensagem inicial
  initial_message?: string

  // voip específico
  extension?: string
  recording?: boolean
}
```

### Código completo

```tsx
"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import {
  Mail, MessageSquare, Phone, Globe, Mic2,
  Pencil, Send, CheckCircle, ChevronDown, ChevronUp,
} from "lucide-react"

type OutreachChannel = "email" | "whatsapp" | "phone" | "webchat" | "voip"

const CHANNEL_META: Record<OutreachChannel, { icon: React.ElementType; label: string; color: string }> = {
  email:    { icon: Mail,          label: "Email",     color: "text-lia-text-secondary" },
  whatsapp: { icon: MessageSquare, label: "WhatsApp",  color: "text-status-success"    },
  phone:    { icon: Phone,         label: "Ligação",   color: "text-lia-text-secondary" },
  webchat:  { icon: Globe,         label: "Chat Web",  color: "text-wedo-cyan"          },
  voip:     { icon: Mic2,          label: "VoIP",      color: "text-lia-text-secondary" },
}

export function OutreachCard({ data }: { data: OutreachData }) {
  const [sent, setSent] = useState(false)
  const [expanded, setExpanded] = useState(false)

  const meta = CHANNEL_META[data.channel]
  const Icon = meta.icon

  const handleSend = () => {
    window.dispatchEvent(new CustomEvent("lia:outreach-send", {
      detail: { channel: data.channel, candidateId: data.candidate_id, data },
    }))
    setSent(true)
  }

  const handleEdit = () => {
    window.dispatchEvent(new CustomEvent("lia:outreach-edit", {
      detail: { channel: data.channel, candidateId: data.candidate_id, data },
    }))
  }

  if (sent) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary max-w-[85%]">
        <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
        <span className="text-xs text-lia-text-secondary font-['Open_Sans',sans-serif]">
          {meta.label} enviado para {data.candidate_name}
        </span>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-secondary max-w-[85%] overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2.5 border-b border-lia-border-subtle">
        <Icon className={cn("w-4 h-4 flex-shrink-0", meta.color)} aria-hidden="true" />
        <span className="text-xs font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
          {meta.label} · {data.candidate_name}
        </span>
      </div>
      {/* Channel-specific content (email, whatsapp, phone/voip, webchat) */}
      <div className="px-3 py-2">
        {/* ... renderização por canal ... */}
      </div>
      <div className="flex items-center gap-2 px-3 py-2.5 border-t border-lia-border-subtle">
        <button onClick={handleEdit} className="...">
          <Pencil className="w-3.5 h-3.5" /> Editar
        </button>
        <button onClick={handleSend} className="flex-1 bg-gray-900 text-white ...">
          {/* label por canal: Aprovar e enviar / Enviar via WhatsApp / Iniciar ligação / etc. */}
        </button>
      </div>
    </div>
  )
}
```

### Integração em UnifiedMessageList.tsx

```typescript
// Import adicionado:
import { OutreachCard } from "./OutreachCard"
import type { OutreachData } from "./OutreachCard"

// Na renderização de mensagens LIA:
const meta = message.metadata
const hasOutreach = meta?.type === "outreach_message" && meta?.outreach != null

// No JSX:
{hasOutreach && (
  <OutreachCard data={meta!.outreach as OutreachData} />
)}
```

### Como o backend envia o OutreachCard

```python
# Em qualquer agent que gere comunicação com candidato (sourcing_agent, outreach_agent):
from app.models.conversation import LiaChatMessage

# Enviar como metadata na resposta do agente:
return LiaChatMessage(
    content="Preparei o email para João Silva. Revise antes de enviar:",
    metadata={
        "type": "outreach_message",
        "outreach": {
            "channel": "email",  # ou "whatsapp", "phone", "webchat", "voip"
            "candidate_name": candidate.name,
            "candidate_id": str(candidate.id),
            "subject": "Oportunidade em Fintech — Engenheiro Sênior",
            "body": "Olá João, vi que você liderou projetos de alto impacto...",
        }
    }
)

# Exemplo para WhatsApp:
metadata={
    "type": "outreach_message",
    "outreach": {
        "channel": "whatsapp",
        "candidate_name": candidate.name,
        "candidate_id": str(candidate.id),
        "phone": "+55 11 99999-9999",
        "initial_message": "Oi João! Sou da WeDOTalent e vi seu perfil...",
        "template": "candidate_outreach_v2",
    }
}

# Exemplo para ligação com roteiro:
metadata={
    "type": "outreach_message",
    "outreach": {
        "channel": "phone",
        "candidate_name": candidate.name,
        "estimated_duration": "5-10 min",
        "script": [
            "Confirmar interesse na vaga de Engenheiro Sr.",
            "Alinhamento de expectativas salariais",
            "Verificar disponibilidade para entrevista técnica",
            "Explicar próximos passos do processo",
        ],
    }
}
```

---

## 11. Sprint UX-7 — Workflow Rail Integration

### Eventos emitidos pelo UnifiedChat.tsx

**Arquivo:** `plataforma-lia/src/components/unified-chat/UnifiedChat.tsx`

```typescript
const prevStageRef = useRef<string | null>(null)
const wizardWorkflowIdRef = useRef<string | null>(null)

useEffect(() => {
  const stage = dynamicPanel?.stage ?? null
  const prevStage = prevStageRef.current
  if (stage === prevStage) return
  prevStageRef.current = stage

  if (stage === "intake" && !prevStage) {
    // Wizard inicia — criar novo ID e emitir workflow:started
    wizardWorkflowIdRef.current = `wizard-${Date.now()}`
    window.dispatchEvent(new CustomEvent("workflow:started", {
      detail: {
        id: wizardWorkflowIdRef.current,
        type: "campaign",
        label: "Criando vaga",
        stage: "intake",
      },
    }))
  } else if (stage === "done" && wizardWorkflowIdRef.current) {
    // Wizard concluído — remover do Rail
    window.dispatchEvent(new CustomEvent("workflow:completed", {
      detail: { id: wizardWorkflowIdRef.current, outcome: "success" },
    }))
    wizardWorkflowIdRef.current = null
  } else if (stage && wizardWorkflowIdRef.current) {
    // Stage mudou — atualizar label no Rail
    window.dispatchEvent(new CustomEvent("workflow:updated", {
      detail: {
        id: wizardWorkflowIdRef.current,
        stage,
        label: WIZARD_STAGE_LABELS[stage] ?? stage,
      },
    }))
  } else if (!stage && prevStage && wizardWorkflowIdRef.current) {
    // Panel fechado antes de concluir — marcar como falho
    window.dispatchEvent(new CustomEvent("workflow:failed", {
      detail: { id: wizardWorkflowIdRef.current, error: "Fluxo interrompido" },
    }))
    wizardWorkflowIdRef.current = null
  }
}, [dynamicPanel?.stage])

// Sync thinking state com Rail:
useEffect(() => {
  if (!wizardWorkflowIdRef.current) return
  window.dispatchEvent(new CustomEvent("workflow:thinking", {
    detail: { id: wizardWorkflowIdRef.current, isThinking: chatIsThinking },
  }))
}, [chatIsThinking])
```

### Listeners em useWorkflowRail.ts

**Arquivo:** `plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts`

```typescript
useEffect(() => {
  const onStarted = (e: Event) => {
    const { id, type, label, stage, vacancyId } = (e as CustomEvent).detail
    setEntries(prev => {
      if (prev.find(en => en.id === id)) return prev   // dedup
      return [{
        id,
        type: type === "campaign" ? "campaign" : "search",
        name: label ?? "Fluxo",
        currentStage: stage,
        stages: [],
        jobId: vacancyId ?? null,
        talentPoolId: null,
        pendingAction: null,
        createdAt: new Date().toISOString(),
      } as WorkflowEntry, ...prev]
    })
  }

  const onUpdated = (e: Event) => {
    const { id, stage, label } = (e as CustomEvent).detail
    setEntries(prev => prev.map(en =>
      en.id === id
        ? { ...en, currentStage: stage ?? en.currentStage, name: label ?? en.name }
        : en
    ))
  }

  const onCompleted = (e: Event) => {
    // Remove do Rail — vai para Tarefas como task fechada
    setEntries(prev => prev.filter(en => en.id !== (e as CustomEvent).detail.id))
  }

  const onFailed = (e: Event) => {
    const { id, error } = (e as CustomEvent).detail
    // Mantém o card mas marca como pendingAction (vermelho no Rail)
    setEntries(prev => prev.map(en =>
      en.id === id
        ? { ...en, pendingAction: { message: error ?? "Falha no fluxo" } }
        : en
    ))
  }

  window.addEventListener("workflow:started",   onStarted)
  window.addEventListener("workflow:updated",   onUpdated)
  window.addEventListener("workflow:completed", onCompleted)
  window.addEventListener("workflow:failed",    onFailed)

  return () => {
    window.removeEventListener("workflow:started",   onStarted)
    window.removeEventListener("workflow:updated",   onUpdated)
    window.removeEventListener("workflow:completed", onCompleted)
    window.removeEventListener("workflow:failed",    onFailed)
  }
}, [])
```

### Integração com outras páginas do produto

| Página | O que deve emitir | Quando |
|--------|------------------|--------|
| **Chat LIA** | `workflow:started/updated/completed/failed` | Wizard, outreach, calibração |
| **Funil de Talentos** | `workflow:started` | Mover candidato, triagem em lote, outreach |
| **Vagas** | `workflow:started` | Calibrar, triar, publicar via botão |
| **Agent Studio** | `workflow:started/updated` | Agentes rodando em background |

```typescript
// Exemplo: Funil de Talentos emitindo workflow ao mover candidato
window.dispatchEvent(new CustomEvent("workflow:started", {
  detail: {
    id: `schedule-${candidateId}-${Date.now()}`,
    type: "campaign",
    label: `${candidateName} · agendando`,
    stage: "scheduling",
    vacancyId: vacancyId,
  },
}))
```

---

## 12. Sistema de Tipos Completo

**Arquivo canônico:** `plataforma-lia/src/components/unified-chat/wizard/wizard-types.ts`

```typescript
/**
 * TypeScript types for the Wizard WSI pipeline.
 * Mirrors backend state.py WizardStage + ws_stage_payload format.
 */

export type WizardStage =
  | "intake"
  | "jd_enrichment"
  | "bigfive"
  | "salary"
  | "competency"
  | "wsi_questions"
  | "eligibility"
  | "review"
  | "publish"
  | "calibration"
  | "handoff"
  | "done"
  | "scheduling"        // ← adicionado UX-5

export type ScreeningMode = "compact" | "full"

export interface WizardStagePayload {
  type: "wizard_stage"
  stage: WizardStage
  data: Record<string, unknown>
  completeness: number       // 0.0 to 1.0
  requires_approval: boolean
}

// Calibration
export interface CalibrationData {
  candidates: CalibrationCandidate[]
  threshold: number
  approved_count: number
  complete: boolean
  pool_count?: number                   // ← adicionado UX-4
  criteria?: Array<{                    // ← adicionado UX-4
    label: string
    type: "must_have" | "sourcing"
  }>
}

export interface CalibrationCandidate {
  id: string
  name: string
  current_title: string
  current_company: string
  match_score: number
  match_criteria: Array<{ criterion: string; score: number; met: boolean }>
  decision?: "approved" | "rejected"
  reason?: string
}

// Scheduling (novo UX-5)
export interface SchedulingData {
  interviews?: Array<{
    id: string
    title: string
    type?: string
    candidate_name?: string
  }>
  available_slots?: Array<{
    date: string
    day_label: string
    time: string
    available: boolean
  }>
  job_title?: string
  candidate_name?: string
  vacancy_id?: string
}

// Outreach (novo UX-6)
export interface OutreachData {
  channel: "email" | "whatsapp" | "phone" | "webchat" | "voip"
  candidate_name: string
  candidate_id?: string
  subject?: string
  body?: string
  phone?: string
  template?: string
  script?: string[]
  estimated_duration?: string
  initial_message?: string
  extension?: string
  recording?: boolean
}

// Stage labels para o WorkflowRail
export const WIZARD_STAGE_LABELS: Record<WizardStage, string> = {
  intake:        "Criando vaga · Início",
  jd_enrichment: "Criando vaga · Descrição",
  bigfive:       "Criando vaga · Perfil",
  salary:        "Criando vaga · Salário",
  competency:    "Criando vaga · Competências",
  wsi_questions: "Criando vaga · Triagem",
  eligibility:   "Criando vaga · Elegibilidade",
  review:        "Criando vaga · Revisão",
  publish:       "Criando vaga · Publicação",
  calibration:   "Calibrando · Candidatos",
  handoff:       "Criando vaga · Finalização",
  done:          "Vaga criada",
  scheduling:    "Agendando · Entrevistas",
}

export const SPLIT_STAGES: WizardStage[] = [
  "review", "publish", "calibration", "handoff", "done", "scheduling"
]
```

---

## 13. Sistema de Eventos Customizados

### Namespace existente (não alterado)

| Evento | Quem emite | Quem escuta | Payload |
|--------|-----------|------------|---------|
| `lia:navigation-hint` | UnifiedChat | dashboard-app | `{ url, label }` |
| `lia:navigate-chat-page` | UnifiedChat | dashboard-app | `{ conversationId }` |
| `lia:leave-fullscreen-chat` | UnifiedChat | dashboard-app | — |
| `lia:chat-mode-changed` | UnifiedChat | dashboard-app | `{ mode }` |
| `lia:prefill-message` | MessageActions | UnifiedChatInput | `{ text }` |
| `lia:wizard-edit-question` | WizardPanels | useWizardIntegration | `{ questionId }` |

### Novos eventos (UX-1 a UX-7)

| Evento | Quem emite | Quem escuta | Payload |
|--------|-----------|------------|---------|
| `workflow:started` | UnifiedChat | useWorkflowRail | `{ id, type, label, stage, vacancyId? }` |
| `workflow:updated` | UnifiedChat | useWorkflowRail | `{ id, stage, label }` |
| `workflow:completed` | UnifiedChat | useWorkflowRail | `{ id, outcome }` |
| `workflow:failed` | UnifiedChat | useWorkflowRail | `{ id, error }` |
| `workflow:thinking` | UnifiedChat | (futuro: Rail pulsing) | `{ id, isThinking }` |
| `lia:scheduling-confirmed` | SchedulingPanel | backend via chat | `{ slots, interviews, vacancyId }` |
| `lia:outreach-send` | OutreachCard | backend via chat | `{ channel, candidateId, data }` |
| `lia:outreach-edit` | OutreachCard | DynamicContextPanel | `{ channel, candidateId, data }` |

### Padrão de uso

```typescript
// Emitir:
window.dispatchEvent(new CustomEvent("workflow:started", {
  detail: { id: "wizard-xxx", type: "campaign", label: "Criando vaga" },
}))

// Escutar (dentro de useEffect):
const handler = (e: Event) => {
  const { id, label } = (e as CustomEvent).detail
  // ...
}
window.addEventListener("workflow:started", handler)
return () => window.removeEventListener("workflow:started", handler)
```

---

## 14. APIs e Endpoints

### Endpoints FastAPI existentes (usados pelo módulo)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/v1/conversations` | Lista conversas do workspace |
| `POST` | `/api/v1/conversations` | Cria nova conversa |
| `PATCH` | `/api/v1/conversations/{id}` | Rename de conversa |
| `DELETE` | `/api/v1/conversations/{id}` | Deleta conversa |
| `GET` | `/api/v1/candidates/search` | Autocomplete @mention |
| `POST` | `/api/v1/hitl/{thread_id}/approve` | Aprovar HITL action |
| `POST` | `/api/v1/hitl/{thread_id}/reject` | Rejeitar HITL action |
| `POST` | `/api/v1/feedback/message` | Thumbs up/down em mensagem |
| `GET` | `/api/v1/vacancies/{id}/candidates/preview` | Preview candidatos para calibração |

### Endpoints Rails ATS (ats-api-copia)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/v1/vacancies` | Lista vagas |
| `POST` | `/api/v1/vacancies` | Cria vaga |
| `PATCH` | `/api/v1/vacancies/{id}` | Atualiza vaga |
| `POST` | `/api/v1/vacancies/{id}/publish` | Publica vaga |
| `GET` | `/api/v1/candidates` | Lista candidatos |
| `POST` | `/api/v1/interviews` | Agenda entrevista |
| `GET` | `/api/v1/talent_pools` | Lista talent pools |
| `GET` | `/api/v1/recruitment-campaigns` | Campanhas ativas (WorkflowRail) |

### Proxy Next.js

Todas as chamadas do frontend passam pelo proxy em:
```
plataforma-lia/src/app/api/backend-proxy/[...path]/route.ts
```

Que roteia para:
- FastAPI: `NEXT_PUBLIC_API_URL` (default: Replit FastAPI)
- Rails: `NEXT_PUBLIC_RAILS_API_URL` ou `RAILS_API_URL`

### WebSocket do Chat

```
WebSocket: ws://{NEXT_PUBLIC_API_URL}/ws/chat/{conversation_id}

Mensagens do backend para o frontend:
{
  "type": "token",           // streaming token
  "content": "..."
}
{
  "type": "thinking_steps",  // live task feed
  "steps": ["Buscando...", "Encontrados 847 perfis"]
}
{
  "type": "wizard_stage",    // stage do wizard (abre panel)
  "stage": "calibration",
  "data": { ... },
  "completeness": 0.33,
  "requires_approval": false
}
{
  "type": "panel_update",    // atualiza panel sem mudar stage
  "panel_type": "calibration",
  "data": { "pool_count": 923 }
}
{
  "type": "message",         // mensagem completa com metadata
  "content": "...",
  "metadata": {
    "type": "outreach_message",
    "outreach": { ... }
  }
}
```

---

## 15. Pendências de Backend

### Alta prioridade (bloqueiam features UX)

#### P1 — UX-4: Pool count + criteria no payload de calibração

**Arquivo backend:** `lia-agent-system/app/domains/wizard/nodes/calibration_node.py`

```python
# Adicionar ao payload do stage calibration:
payload = {
    "candidates": [candidate.to_dict() for candidate in top_candidates],
    "threshold": 3,
    "approved_count": state.get("approved_count", 0),
    "complete": False,
    # ↓ NOVO — necessário para UX-4
    "pool_count": await count_matching_pool(vacancy_id, criteria),
    "criteria": [
        {"label": c.label, "type": c.type}
        for c in vacancy.screening_criteria
    ],
}
```

**Atualizar pool_count após thumbs feedback:**

```python
# No endpoint POST /api/v1/calibration/feedback:
async def calibration_feedback(feedback: CalibrationFeedback, ...):
    # ... salva feedback ...
    new_pool_count = await recalculate_pool(vacancy_id)
    # Enviar via WebSocket para atualizar o panel:
    await ws_panel_update(
        conversation_id=conversation_id,
        panel_type="calibration",
        data={"pool_count": new_pool_count}
    )
```

#### P2 — UX-5: SchedulingPanel trigger via WebSocket

**Arquivo backend:** `lia-agent-system/app/domains/wizard/nodes/scheduling_node.py` (criar ou adaptar)

```python
from app.shared.websocket.ws_helpers import ws_stage_payload

async def scheduling_node(state: WizardState) -> WizardState:
    slots = await get_available_slots(
        vacancy_id=state["vacancy_id"],
        duration_minutes=45,
    )
    await ws_stage_payload(
        conversation_id=state["conversation_id"],
        stage="scheduling",
        data={
            "interviews": [
                {"id": str(i.id), "title": i.type, "candidate_name": i.candidate.name}
                for i in state["pending_interviews"]
            ],
            "available_slots": [
                {"date": s.date.isoformat(), "day_label": s.day_label, "time": s.time_str, "available": s.available}
                for s in slots
            ],
            "vacancy_id": str(state["vacancy_id"]),
        },
        completeness=0.5,
        requires_approval=True,
    )
    return state
```

**Ouvir `lia:scheduling-confirmed`:** O frontend dispara o evento via WebSocket message ou pode ser capturado via endpoint dedicado:

```python
# POST /api/v1/scheduling/confirm
class SchedulingConfirmPayload(BaseModel):
    vacancy_id: str
    slots: dict[int, str]   # {0: "2026-04-21|09:00", 1: "2026-04-22|14:00"}
    interviews: list[dict]

@router.post("/scheduling/confirm")
async def confirm_scheduling(payload: SchedulingConfirmPayload, ...):
    for idx, slot_key in payload.slots.items():
        date_str, time_str = slot_key.split("|")
        await create_interview_event(
            interview=payload.interviews[idx],
            date=date_str,
            time=time_str,
            vacancy_id=payload.vacancy_id,
        )
    return {"status": "scheduled"}
```

#### P3 — UX-6: metadata.type = "outreach_message" nas mensagens LIA

**Arquivo backend:** `lia-agent-system/app/domains/sourcing/outreach_agent.py` (adaptar)

```python
# O agente de outreach deve retornar a mensagem com metadata correto:
return {
    "messages": [
        HumanMessage(content="[agente interno]"),
        AIMessage(
            content=f"Preparei o {channel} para {candidate.name}. Revise antes de enviar:",
            additional_kwargs={
                "metadata": {
                    "type": "outreach_message",
                    "outreach": {
                        "channel": channel,  # "email", "whatsapp", etc.
                        "candidate_name": candidate.name,
                        "candidate_id": str(candidate.id),
                        **channel_specific_data,
                    }
                }
            }
        ),
    ]
}
```

### Média prioridade (melhorias de UX)

#### P4 — Rail pulsing: `workflow:thinking`

O evento `workflow:thinking` já é emitido pelo frontend mas o WorkflowRail ainda não escuta.
Adicionar listener em `useWorkflowRail.ts`:

```typescript
const onThinking = (e: Event) => {
  const { id, isThinking } = (e as CustomEvent).detail
  setEntries(prev => prev.map(en =>
    en.id === id ? { ...en, isThinking } : en
  ))
}
window.addEventListener("workflow:thinking", onThinking)
```

Depois aplicar animação visual no card do Rail quando `entry.isThinking === true`.

#### P5 — OutreachEditPanel

O evento `lia:outreach-edit` é emitido mas o `DynamicContextPanel` não tem case para
abrir um editor de outreach no right panel. Adicionar:

```typescript
// DynamicContextPanel.tsx
const OutreachEditPanel = lazy(() =>
  import("./panels/OutreachEditPanel").then((m) => ({ default: m.OutreachEditPanel }))
)

// No switch:
case "outreach_edit":
  return <OutreachEditPanel data={data} onApprove={onApprove} />
```

E criar `OutreachEditPanel.tsx` com textarea editável por canal.

#### P6 — SmartSuggestions pós-workflow

Quando `stage === "done"`, mostrar chips contextuais:

```typescript
// SmartSuggestions.tsx
if (currentStage === "done") {
  return [
    "Ver candidatos da vaga",
    "Calibrar mais critérios",
    "Exportar JD aprovado",
    "Agendar entrevistas",
  ]
}
```

---

## 16. Design System — Regras para este módulo

**Arquivo canônico DS:** `plataforma-lia/docs/design-system/00-design-system-v4.md`  
**Tokens CSS:** `plataforma-lia/src/styles/design-tokens.css`

### Regras invioláveis (aplicadas em todos os arquivos UX-1 a UX-7)

| Regra | Aplicação | Proibido |
|-------|-----------|---------|
| Animações | `animate-fade-in-up`, `animate-spin` | `framer-motion`, `transition-all` |
| Border radius cards | `rounded-xl` (12px) | `rounded-2xl`, `rounded-full` em cards |
| Border radius pills/badges | `rounded-lg` (8px) | `rounded-xl` em pills |
| Transições | `transition-colors` | `transition-all` (causa GPU text blur) |
| `motion-reduce` | Sempre incluir `motion-reduce:transition-none` | — |
| Botão primário | `bg-gray-900 text-white hover:bg-gray-800` | Hardcode hex |
| Cor IA/LIA | `wedo-cyan` exclusivo para elementos de IA | Em UI genérica |
| Cor sucesso | `status-success` | Verde hardcoded |
| Cor erro | `status-error` | Vermelho hardcoded |
| Fonte body | `font-['Open_Sans',sans-serif]` | `font-sans` genérico |
| Ícones | `lucide-react` | Heroicons, FontAwesome |
| Ícone tamanho | `w-4 h-4` inline, `w-3 h-3` em pill/badge | Tamanhos inconsistentes |
| Acessibilidade | `aria-hidden="true"` em ícones decorativos | Ícones sem aria |

### Tokens de cor mapeados

```css
/* Backgrounds */
--lia-bg-primary:    oklch(100% 0 0)          /* white */
--lia-bg-secondary:  oklch(97.6% 0 0)         /* gray-50 */
--lia-bg-tertiary:   oklch(95.7% 0 0)         /* gray-100 */

/* Borders */
--lia-border-subtle:  oklch(91.8% 0 0)        /* gray-200 */
--lia-border-default: oklch(87.2% 0 0)        /* gray-300 */

/* Text */
--lia-text-primary:   oklch(9% 0 0)           /* gray-900 */
--lia-text-secondary: oklch(32.6% 0 0)        /* gray-600 */
--lia-text-disabled:  oklch(55.6% 0 0)        /* gray-400 */

/* Interactive */
--lia-interactive-hover: oklch(95.7% 0 0)     /* gray-100 */

/* Brand */
--wedo-cyan: oklch(72.7% 0.086 213.1)         /* #60BED1 — exclusivo LIA */
--status-success: oklch(51.6% 0.178 142.4)    /* green-600 */
--status-error:   oklch(52.7% 0.19 27.5)      /* red-600 */
```

---

## 17. Arquivos de Referência no Replit

### Conexão SSH ao Replit

```bash
ssh -i ~/.ssh/replit -p 22 \
  82791557-0b63-4f8d-baed-bba54c6e1fdf@82791557-0b63-4f8d-baed-bba54c6e1fdf-00-32kinhguzv9ak.picard.replit.dev
```

### Estrutura no Replit

```
/home/runner/workspace/
├── plataforma-lia/               ← Frontend canônico (Next.js)
│   └── src/components/unified-chat/
│       ├── ThinkingStepsCard.tsx      ✅ IMPLEMENTADO (UX-1)
│       ├── OutreachCard.tsx           ✅ IMPLEMENTADO (UX-6)
│       ├── UnifiedChat.tsx            ✅ MODIFICADO (UX-2,3,7)
│       ├── UnifiedChatHeader.tsx      ✅ MODIFICADO (UX-2)
│       ├── UnifiedMessageList.tsx     ✅ MODIFICADO (UX-1,6)
│       └── wizard/
│           ├── DynamicContextPanel.tsx     ✅ MODIFICADO (UX-3,5)
│           ├── wizard-types.ts             ✅ MODIFICADO (UX-5)
│           └── panels/
│               ├── CalibrationPanel.tsx    ✅ MODIFICADO (UX-4)
│               └── SchedulingPanel.tsx     ✅ IMPLEMENTADO (UX-5)
├── plataforma-lia/src/components/workflow-rail/
│   └── useWorkflowRail.ts         ✅ MODIFICADO (UX-7)
├── lia-agent-system/              ← Backend FastAPI
│   └── app/
│       ├── domains/wizard/nodes/  ← nodes LangGraph
│       ├── shared/websocket/      ← ws_stage_payload, ws_thinking_steps
│       └── api/v1/               ← endpoints REST
└── ats-api-copia/                 ← Rails API (ATS)
    └── app/
        ├── controllers/api/v1/
        ├── models/
        └── channels/              ← ActionCable (WorkflowChannel)
```

### Arquivos de configuração importantes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `plataforma-lia/.env.local` | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_RAILS_WS_URL` |
| `plataforma-lia/tailwind.config.ts` | Tokens `wedo-*`, `lia-*`, `status-*`, animações |
| `plataforma-lia/src/styles/design-tokens.css` | Variáveis CSS canônicas |
| `lia-agent-system/.env` | `ANTHROPIC_API_KEY` (= `AI_INTEGRATIONS_ANTHROPIC_API_KEY`), `DATABASE_URL` |
| `ats-api-copia/config/database.yml` | PostgreSQL config |

---

## 18. Mapa Arquitetura Frontend

```
┌─────────────────────────────────────────────────────────┐
│  Layout Global (app/layout.tsx)                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Navigation (Sidebar 64px)                       │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  Page Content (flex-1)                           │   │
│  │  ┌──────────────────────────────────────────┐   │   │
│  │  │  UnifiedChat (sidebar / floating mode)   │   │   │
│  │  │  ┌──────────────────┐  ┌──────────────┐  │   │   │
│  │  │  │ Chat Messages    │  │ Right Panel  │  │   │   │
│  │  │  │ ┌─────────────┐  │  │ 340px/420px  │  │   │   │
│  │  │  │ │ThinkingSteps│  │  │ DynamicCtx   │  │   │   │
│  │  │  │ │Card         │  │  │ ┌──────────┐ │  │   │   │
│  │  │  │ └─────────────┘  │  │ │Calibration│ │  │   │   │
│  │  │  │ ┌─────────────┐  │  │ │Panel     │ │  │   │   │
│  │  │  │ │OutreachCard │  │  │ └──────────┘ │  │   │   │
│  │  │  │ └─────────────┘  │  │ ┌──────────┐ │  │   │   │
│  │  │  └──────────────────┘  │ │Scheduling│ │  │   │   │
│  │  └──────────────────────────│Panel     │─┘  │   │   │
│  │                             └──────────┘    │   │   │
│  ├─────────────────────────────────────────────┤   │   │
│  │  WorkflowRail (bottom bar — rodapé fixo)     │   │   │
│  │  [Criando vaga · Dev Sr] [Triando · 23] [+]  │   │   │
│  └─────────────────────────────────────────────┘   │   │
└─────────────────────────────────────────────────────────┘

Fullscreen mode (fixed inset-0 z-50):
┌──────────────────────────────────────────────────────────┐
│ Header: [LIA] [Criando vaga · Calibração ⇄⌘K] [□ ✕]     │
├──────────────────────────┬───────────────────────────────┤
│  Chat Messages           │  Right Panel (420px fullscreen)│
│  (full-width stages 1-7) │  (split view stages 8-12)      │
│                          │                               │
│  ThinkingStepsCard       │  CalibrationPanel             │
│  OutreachCard            │  SchedulingPanel              │
│  FlowStepMessage         │  ReviewPanel                  │
│                          │  PublishPanel                 │
├──────────────────────────┴───────────────────────────────┤
│  Input + @mention + /commands + file upload               │
│  [Fullscreen hint toast — aparece uma vez por sessão]     │
└──────────────────────────────────────────────────────────┘
```

---

## 19. Cobertura Competitiva Final

| Feature Tezi | WeDO antes | WeDO após UX-1 a UX-7 | Pilar |
|-------------|-----------|----------------------|-------|
| Task Context Bar (tarefa ativa + ⌘K) | ❌ | ✅ ActiveTaskPill | UX-2 |
| Multi-tasking Switch Task ⌘K | ✅ existe | ✅ exposto visualmente | UX-2 |
| Criação de vaga conversacional (sem split) | ⚠️ split em todos stages | ✅ stages 1-7 full-width | UX-3 |
| Split view SOMENTE na calibração/review | ⚠️ split em todos | ✅ SPLIT_STAGES cirúrgico | UX-3 |
| Live task evolution (Manus-style) | ❌ spinner genérico | ✅ ThinkingStepsCard | UX-1 |
| Calibração com perfis reais | ❌ | ✅ (backend pendente P1) | UX-4 |
| Pool counter em tempo real | ❌ | ✅ (backend pendente P1) | UX-4 |
| Must-haves vs Sourcing separados | ❌ misturado | ✅ seções separadas | UX-4 |
| Agendamento como workspace (não modal) | ❌ modal interrompe | ✅ SchedulingPanel | UX-5 |
| Multi-entrevista paginada (1/2 → 2/2) | ❌ | ✅ | UX-5 |
| Email outreach inline com aprovação | ⚠️ existe mas não visível | ✅ OutreachCard email | UX-6 |
| WhatsApp outreach inline | ❌ (Tezi não tem) | ✅ OutreachCard whatsapp | UX-6 |
| Ligação com roteiro inline | ❌ (Tezi não tem) | ✅ OutreachCard phone | UX-6 |
| VoIP + WebChat inline | ❌ (Tezi não tem) | ✅ OutreachCard voip/webchat | UX-6 |
| WorkflowRail integrado ao wizard | ❌ | ✅ eventos lifecycle | UX-7 |
| Fullscreen mais largo (420px) | ❌ 340px fixo | ✅ responsivo por mode | UX-2 |
| Sugestão automática de fullscreen | ❌ | ✅ toast único por sessão | UX-2 |

**Vantagens WeDO mantidas (não replicar a Tezi nestes):**
- Cards de candidato mais ricos (ParecerLIACard)
- Triagem por voz (WSI Voice + Gemini + Twilio)
- Outreach VoIP e WebChat (Tezi só tem email)
- Multi-tenant nativo (Tezi é mono-tenant)

---

## 20. Itens Futuros (não implementados)

### Sprint UX-8 — Right Panel Workspace Adicional

```
Criar:
  - wizard/panels/CandidateProfilePanel.tsx
    Props: { candidateId: string, vacancyId?: string }
    Reusa: CandidateCard + Card shadcn + Tabs (perfil, histórico, scores)
    Trigger: message com metadata.type === "candidate_profile"

  - wizard/panels/PipelineSnapshotPanel.tsx
    Props: { vacancyId: string }
    Reusa: PipelineStagesCarousel + progress.tsx
    Trigger: message com metadata.type === "pipeline_snapshot"

Modificar:
  - wizard/DynamicContextPanel.tsx — adicionar cases
    case "candidate_profile": return <CandidateProfilePanel ...>
    case "pipeline_snapshot": return <PipelineSnapshotPanel ...>
```

### Sprint UX-9 — SmartSuggestions pós-workflow

```
Modificar: SmartSuggestions.tsx
Adicionar chips contextuais após stage === "done":
  - "Ver candidatos da vaga"
  - "Calibrar mais critérios"
  - "Exportar JD aprovado"
  - "Agendar entrevistas"
```

### Sprint UX-10 — Navegação simplificada (4 itens)

Decisão de produto maior — requer redesign da sidebar.
Não implementar sem aprovação explícita do Paulo.

---

## Checklist de Verificação E2E

Antes de marcar qualquer sprint como completo, verificar:

```
[ ] UX-1: LIA pensa → ThinkingStepsCard aparece com steps reais
[ ] UX-1: Streaming começa → ThinkingStepsCard some, resposta aparece
[ ] UX-2: Wizard stage qualquer → ActiveTaskPill visível no header
[ ] UX-2: Clicar na pill → SwitchTaskModal abre (⌘K)
[ ] UX-2: Wizard inicia em sidebar → toast de fullscreen aparece uma vez
[ ] UX-2: Fullscreen → right panel 420px (não 340px)
[ ] UX-3: Stages 1-7 (intake→eligibility) → chat 100% full-width, sem split
[ ] UX-3: Stage review → split view abre automaticamente
[ ] UX-3: Stage calibration → split view + pool counter visível
[ ] UX-4: Thumbs feedback → pool_count atualiza em tempo real
[ ] UX-4: Must-haves → chips cinza escuro; Sourcing → chips com borda
[ ] UX-5: Backend envia stage="scheduling" → SchedulingPanel abre no panel
[ ] UX-5: Selecionar slot → botão Confirmar ativa
[ ] UX-5: 2 entrevistas → paginação "1 de 2" → "2 de 2" → Agendadas!
[ ] UX-6: Backend envia metadata.type="outreach_message" → OutreachCard aparece
[ ] UX-6: Email/WA/phone/voip/webchat → cada canal renderiza conteúdo correto
[ ] UX-6: Botão Enviar → card colapsa para confirmação "Email enviado para João"
[ ] UX-7: Wizard inicia → card aparece no WorkflowRail do rodapé
[ ] UX-7: Stage muda → card do Rail atualiza o label
[ ] UX-7: stage=done → card some do Rail
[ ] UX-7: Panel fecha sem done → card do Rail fica vermelho
```

---

*Documento gerado em 2026-04-19. Versão 1.0.*  
*Para dúvidas: tech@wedotalent.cc*
