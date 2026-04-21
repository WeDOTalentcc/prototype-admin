# Developer Handoff — UX Redesign Competitivo (Sprints UX-1 a UX-7) + Onda Benefícios/Departamentos/Workforce

> **Commit base:** `5140997a` · **Branch:** `develop` · **Data:** 2026-04-19
> **Última onda documentada:** PARTE J — commits `32f29426f..cfe3f51fa` (16 commits, 2026-04-21).
> **Contexto:** Análise competitiva da Tezi (concorrente adquirido por PE para healthcare)
> revelou 7 pilares de UX que o WeDo tinha infraestrutura para entregar mas não ativou.
> Este handoff documenta todos os arquivos, interfaces, eventos e integrações implementados.
> A **PARTE J** (final) descreve a onda Benefícios + Departamentos + Workforce, replicável em
> três frentes: Front (este repo), Rails (`ats-api-copia`) e IA (repo separado).

---

## Premissa de Produto

- **Zero páginas novas** — tudo vive no right panel ou no chat
- **Reuso máximo** — cada componente reusa o que já existe (shadcn/ui, lucide, tokens)
- **Portabilidade Vue** — props tipadas, callbacks `on*`, sem HOCs nem cloneElement
- **Canônico** — edições sempre no arquivo canônico, nunca no consumidor

---

## Sprint UX-1 — Live Task Feed (Manus-style)

### Problema
`chatThinkingSteps: string[]` vinha do backend, passava como prop para `UnifiedMessageList`,
mas **nunca era renderizado** — só aparecia um `<TypingIndicator />` genérico.

### Solução

#### Arquivo novo: `src/components/unified-chat/ThinkingStepsCard.tsx`

```tsx
interface ThinkingStepsCardProps {
  steps: string[]   // array vindo de chatThinkingSteps no contexto
}
```

**Comportamento:**
- `steps.length === 0` → spinner wedo-cyan + "Pensando..."
- `steps.length > 0` → card com lista:
  - Últmo step (ativo): `Loader2` animado + `text-lia-text-primary font-medium`
  - Steps anteriores (concluídos): `CheckCircle2` verde + `text-lia-text-secondary`
- Card: `rounded-xl border border-lia-border-subtle bg-lia-bg-secondary`
- Animação de entrada: `animate-fade-in-up` (tailwindcss-animate, sem framer-motion)
- Largura máxima: `max-w-[85%]`

**Tokens usados:** `wedo-cyan`, `status-success`, `lia-bg-secondary`, `lia-border-subtle`,
`lia-text-primary`, `lia-text-secondary`

#### Arquivo modificado: `src/components/unified-chat/UnifiedMessageList.tsx`

```diff
- import { TypingIndicator } from "@/components/chat/typing-indicator"
+ import { ThinkingStepsCard } from "./ThinkingStepsCard"

- {isThinking && !streamingContent && (
-   <div className="flex items-center gap-2"><TypingIndicator /></div>
- )}
+ {isThinking && !streamingContent && (
+   <div className="group"><ThinkingStepsCard steps={thinkingSteps} /></div>
+ )}
```

**Prop já existia:** `thinkingSteps: string[]` já estava na interface Props — só não era usado.

---

## Sprint UX-2 — Task Context Bar + Fullscreen UX

### 2a — ActiveTaskPill no Header

#### Arquivo modificado: `src/components/unified-chat/UnifiedChatHeader.tsx`

**Nova prop adicionada à interface:**
```tsx
interface Props {
  // ... props existentes ...
  activeTaskLabel?: string | null   // ex: "Criando vaga · Calibração"
}
```

**Pill renderizada no left section** (após connection dot + TransportModeIndicator):
```tsx
{activeTaskLabel && (
  <button
    onClick={onSwitchTask}
    className="flex items-center gap-1 px-2 py-0.5 rounded-lg border border-lia-border-subtle
               bg-lia-bg-secondary text-lia-text-secondary hover:text-lia-text-primary
               hover:bg-lia-interactive-hover transition-colors flex-shrink-0 max-w-[200px]"
    title={`${activeTaskLabel} — trocar conversa (⌘K)`}
  >
    <span className="text-xs truncate">{activeTaskLabel}</span>
    <ArrowRightLeft className="w-3 h-3 opacity-60" />
  </button>
)}
```

**Design:** `rounded-lg` (badge/pill), `transition-colors` (não `transition-all`), ícone `w-3 h-3`.
Clicking dispara `onSwitchTask` — reutiliza o SwitchTaskModal ⌘K já existente.

### 2b — Constante WIZARD_STAGE_LABELS

#### Arquivo modificado: `src/components/unified-chat/UnifiedChat.tsx`

```typescript
const WIZARD_STAGE_LABELS: Record<string, string> = {
  intake: "Criando vaga · Início",
  jd_enrichment: "Criando vaga · Descrição",
  bigfive: "Criando vaga · Perfil",
  salary: "Criando vaga · Salário",
  competency: "Criando vaga · Competências",
  wsi_questions: "Criando vaga · Triagem",
  eligibility: "Criando vaga · Elegibilidade",
  review: "Criando vaga · Revisão",
  publish: "Criando vaga · Publicação",
  calibration: "Calibrando · Candidatos",
  handoff: "Criando vaga · Finalização",
  done: "Vaga criada",
}
```

**Derivação do label:**
```typescript
const activeTaskLabel = dynamicPanel?.stage
  ? (WIZARD_STAGE_LABELS[dynamicPanel.stage] ?? dynamicPanel.stage)
  : null
```

Passado para `<UnifiedChatHeader activeTaskLabel={activeTaskLabel} />`.

### 2c — Toast de sugestão fullscreen

Aparece **uma vez por sessão** quando o wizard inicia (`stage === "intake"`)
no modo sidebar/floating. Auto-dismiss após 7 segundos.

```typescript
const [showFullscreenHint, setShowFullscreenHint] = useState(false)
const fullscreenHintShown = useRef(false)

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

Renderizado acima do `<UnifiedChatInput />`:
```tsx
{showFullscreenHint && (
  <div className="px-4 pb-1">
    <div className="flex items-center justify-between px-3 py-2 rounded-lg
                    border border-lia-border-subtle bg-lia-bg-secondary">
      <span className="text-xs text-lia-text-secondary">
        Tela cheia melhora a experiência do wizard
      </span>
      <button onClick={() => { handleModeChange("fullscreen"); setShowFullscreenHint(false) }}>
        <Maximize2 className="w-3 h-3" /> Tela cheia
      </button>
      <button onClick={() => setShowFullscreenHint(false)}>
        <X className="w-3 h-3" />
      </button>
    </div>
  </div>
)}
```

### 2d — Right panel width responsivo

```tsx
// Antes: w-[340px] fixo em todos os modos
// Depois: responsivo por effectiveMode
<div className={cn(
  "flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto",
  effectiveMode === "fullscreen" ? "w-[420px]" : "w-[340px]"
)}>
```

Fullscreen tem 80px extras para calendário, perfis de candidatos, etc.

---

## Sprint UX-3 — Split View Cirúrgico

### Problema
O split view abria para **todos os 12 stages do wizard**, incluindo stages 1-7 que são
conversação pura e não precisam de painel visual.

### Solução

#### Arquivo modificado: `src/components/unified-chat/wizard/DynamicContextPanel.tsx`

**Nova exportação:**
```typescript
export const SPLIT_STAGES: WizardStage[] = [
  "review",       // stage 8 — JD final para aprovação
  "publish",      // stage 9 — seleção de plataformas
  "calibration",  // stage 10 — candidatos reais + thumbs
  "handoff",      // stage 11 — confirmação visual
  "done",         // stage 12 — concluído
  "scheduling",   // panel de agendamento (fora do wizard core)
]
```

**Stages que NÃO abrem split view** (conversação pura, full-width):
`intake`, `jd_enrichment`, `bigfive`, `salary`, `competency`, `wsi_questions`, `eligibility`

#### Arquivo modificado: `src/components/unified-chat/UnifiedChat.tsx`

```typescript
// Antes:
const hasDynamicPanel = !!dynamicPanel

// Depois:
import { DynamicContextPanel, SPLIT_STAGES } from "./wizard/DynamicContextPanel"
import type { WizardStage } from "./wizard/wizard-types"

const hasDynamicPanel = !!dynamicPanel &&
  SPLIT_STAGES.includes(dynamicPanel.stage as WizardStage)
```

**Nota:** O `activeTaskLabel` ainda aparece para **todos os stages** (1-12),
apenas o split view é limitado aos stages visuais.

---

## Sprint UX-4 — CalibrationPanel Upgrade

#### Arquivo modificado: `src/components/unified-chat/wizard/panels/CalibrationPanel.tsx`

### Pool Counter

O backend deve enviar `pool_count: number` dentro do `data` do stage `calibration`.
O número é atualizado após cada feedback de thumbs up/down (re-renderização via WebSocket).

```typescript
const d = data as unknown as CalibrationData & {
  pool_count?: number
  criteria?: CriterionItem[]
}
const poolCount = d.pool_count ?? null
```

**Renderização no header da calibração:**
```tsx
{poolCount !== null && (
  <span className="flex items-center gap-1 text-[10px] text-wedo-cyan font-medium">
    <Users className="w-3 h-3" />
    {poolCount.toLocaleString("pt-BR")} compatíveis
  </span>
)}
```

### Separação Must-haves vs Sourcing Constraints

O backend deve enviar `criteria: Array<{ label: string, type: "must_have" | "sourcing" }>`.

```typescript
interface CriterionItem {
  label: string
  type: "must_have" | "sourcing"
}
```

**Renderização:**
- **Must-haves** (eliminatórios): chips `bg-gray-900 text-white` — requisitos obrigatórios
- **Sourcing** (preferências): chips com `border border-lia-border-subtle text-lia-text-secondary`
- Seção aparece apenas se `criteria` estiver no payload

### Payload esperado do backend (stage calibration)

```json
{
  "stage": "calibration",
  "data": {
    "candidates": [...],
    "threshold": 3,
    "approved_count": 1,
    "pool_count": 847,
    "criteria": [
      { "label": "5+ anos Python", "type": "must_have" },
      { "label": "Experiência em Fintech", "type": "sourcing" }
    ]
  }
}
```

---

## Sprint UX-5 — SchedulingPanel (Novo Arquivo)

### Arquivo novo: `src/components/unified-chat/wizard/panels/SchedulingPanel.tsx`

**Renderizado quando `dynamicPanel.stage === "scheduling"`.**

### Interface de dados esperada

```typescript
interface SchedulingData {
  interviews?: InterviewItem[]     // array de entrevistas a agendar
  available_slots?: SlotItem[]     // grade de horários disponíveis
  job_title?: string
  candidate_name?: string
  vacancy_id?: string
}

interface InterviewItem {
  id: string
  title: string             // ex: "Triagem Técnica"
  type?: string
  candidate_name?: string
}

interface SlotItem {
  date: string              // ISO date string (YYYY-MM-DD)
  day_label: string         // ex: "Seg 14"
  time: string              // ex: "09:00"
  available: boolean
}
```

### Funcionalidades

| Feature | Comportamento |
|---------|--------------|
| Grade semanal | 4 colunas (dias) × N linhas (horários) |
| Seleção de slot | Um slot por vez, botão Confirmar ativa |
| Multi-entrevista | Paginação progressiva com barra de progresso |
| Duração | Select nativo: 30min, 45min, 60min, 90min |
| Fuso horário | Select nativo: BRT (UTC-3), AMT (UTC-4), UTC |
| Confirm | Último confirm → `lia:scheduling-confirmed` + `onApprove()` |
| Placeholder | `generatePlaceholderSlots()` quando backend não envia slots |

### Evento disparado ao confirmar

```typescript
window.dispatchEvent(new CustomEvent("lia:scheduling-confirmed", {
  detail: {
    slots: confirmedSlots,     // { [interviewIdx]: "date|time" }
    interviews,
    vacancyId: data.vacancy_id,
  },
}))
```

### WizardStage atualizado

```typescript
// wizard-types.ts
export type WizardStage =
  | "intake" | "jd_enrichment" | "bigfive" | "salary"
  | "competency" | "wsi_questions" | "eligibility"
  | "review" | "publish" | "calibration" | "handoff" | "done"
  | "scheduling"   // ← adicionado neste sprint
```

### Como acionar pelo backend

Enviar via WebSocket:
```json
{
  "type": "wizard_stage",
  "stage": "scheduling",
  "data": {
    "interviews": [
      { "id": "int-1", "title": "Triagem", "candidate_name": "João Silva" },
      { "id": "int-2", "title": "Técnica", "candidate_name": "João Silva" }
    ],
    "available_slots": [...],
    "vacancy_id": "vac-123"
  }
}
```

O `SPLIT_STAGES` já inclui `"scheduling"`, então o panel abre automaticamente.

---

## Sprint UX-6 — OutreachCard Multi-Canal (Novo Arquivo)

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

### Comportamento por canal

| Canal | Conteúdo exibido | Ação principal |
|-------|-----------------|----------------|
| `email` | Assunto + preview body (expand/collapse) | "Aprovar e enviar" |
| `whatsapp` | Número + preview mensagem + nome do template | "Enviar via WhatsApp" |
| `phone` | Duração estimada + roteiro numerado (até 4 itens) | "Iniciar ligação" |
| `webchat` | Preview da mensagem inicial | "Abrir chat" |
| `voip` | Ramal + status de gravação + roteiro | "Iniciar VoIP" |

### Estado de "enviado"
Após o recruiter clicar no botão de ação, o card colapsa para:
```
✓ Email enviado para João Silva
```

### Eventos disparados

```typescript
// Clique em Aprovar/Enviar/Iniciar
window.dispatchEvent(new CustomEvent("lia:outreach-send", {
  detail: { channel, candidateId, data },
}))

// Clique em Editar (abre right panel para edição completa)
window.dispatchEvent(new CustomEvent("lia:outreach-edit", {
  detail: { channel, candidateId, data },
}))
```

### Como acionar pelo backend (via mensagem LIA)

O `OutreachCard` renderiza quando a mensagem LIA tem `metadata.type === "outreach_message"`:

```typescript
// Em UnifiedMessageList.tsx:
const hasOutreach = meta?.type === "outreach_message" && meta?.outreach != null

{hasOutreach && (
  <OutreachCard data={meta!.outreach as OutreachData} />
)}
```

**Payload esperado no metadata da mensagem:**
```json
{
  "type": "outreach_message",
  "outreach": {
    "channel": "email",
    "candidate_name": "João Silva",
    "candidate_id": "cand-456",
    "subject": "Oportunidade em Fintech — Engenheiro Sênior",
    "body": "Olá João, vi que você liderou..."
  }
}
```

---

## Sprint UX-7 — Workflow Rail Integration

### Objetivo
Conectar o ciclo de vida do wizard ao WorkflowRail do rodapé, para que o recrutador
veja o progresso do wizard na barra inferior mesmo ao navegar para outras páginas.

### Eventos emitidos pelo UnifiedChat

#### `workflow:started` — quando wizard inicia (stage = "intake")

```typescript
window.dispatchEvent(new CustomEvent("workflow:started", {
  detail: {
    id: wizardWorkflowIdRef.current,  // ex: "wizard-1713547200000"
    type: "campaign",
    label: "Criando vaga",
    stage: "intake",
  },
}))
```

#### `workflow:updated` — a cada mudança de stage (2→12)

```typescript
window.dispatchEvent(new CustomEvent("workflow:updated", {
  detail: {
    id: wizardWorkflowIdRef.current,
    stage,
    label: WIZARD_STAGE_LABELS[stage] ?? stage,  // ex: "Criando vaga · Calibração"
  },
}))
```

#### `workflow:completed` — quando stage = "done"

```typescript
window.dispatchEvent(new CustomEvent("workflow:completed", {
  detail: { id: wizardWorkflowIdRef.current, outcome: "success" },
}))
```

Ao ser recebido pelo Rail, a entrada é **removida** (arquivada em Tarefas).

#### `workflow:failed` — quando o panel fecha antes de `done`

```typescript
window.dispatchEvent(new CustomEvent("workflow:failed", {
  detail: { id: wizardWorkflowIdRef.current, error: "Fluxo interrompido" },
}))
```

O card no Rail fica vermelho (pendingAction com mensagem de erro).

#### `workflow:thinking` — sync com LIA thinking state

```typescript
window.dispatchEvent(new CustomEvent("workflow:thinking", {
  detail: { id: wizardWorkflowIdRef.current, isThinking: chatIsThinking },
}))
```

Permite ao Rail pulsar o card enquanto a LIA está processando.

### Implementação no UnifiedChat

```typescript
const prevStageRef = useRef<string | null>(null)
const wizardWorkflowIdRef = useRef<string | null>(null)

// Emite eventos conforme stage muda
useEffect(() => {
  const stage = dynamicPanel?.stage ?? null
  const prevStage = prevStageRef.current
  if (stage === prevStage) return
  prevStageRef.current = stage

  if (stage === "intake" && !prevStage) {
    wizardWorkflowIdRef.current = `wizard-${Date.now()}`
    // dispatch workflow:started
  } else if (stage === "done" && wizardWorkflowIdRef.current) {
    // dispatch workflow:completed
    wizardWorkflowIdRef.current = null
  } else if (stage && wizardWorkflowIdRef.current) {
    // dispatch workflow:updated
  } else if (!stage && prevStage && wizardWorkflowIdRef.current) {
    // dispatch workflow:failed (panel fechado prematuramente)
    wizardWorkflowIdRef.current = null
  }
}, [dynamicPanel?.stage])
```

### Atualizações em useWorkflowRail.ts

**Arquivo:** `src/components/workflow-rail/useWorkflowRail.ts`

Adicionado `useEffect` que escuta os 4 eventos e atualiza `entries`:

```typescript
useEffect(() => {
  const onStarted = (e: Event) => {
    const { id, type, label, stage, vacancyId } = (e as CustomEvent).detail
    setEntries(prev => {
      if (prev.find(en => en.id === id)) return prev
      return [{ id, type, name: label, currentStage: stage, ... } as WorkflowEntry, ...prev]
    })
  }

  const onUpdated = (e: Event) => {
    const { id, stage, label } = (e as CustomEvent).detail
    setEntries(prev => prev.map(en =>
      en.id === id ? { ...en, currentStage: stage, name: label } : en
    ))
  }

  const onCompleted = (e: Event) => {
    setEntries(prev => prev.filter(en => en.id !== (e as CustomEvent).detail.id))
  }

  const onFailed = (e: Event) => {
    const { id, error } = (e as CustomEvent).detail
    setEntries(prev => prev.map(en =>
      en.id === id ? { ...en, pendingAction: { message: error } } : en
    ))
  }

  window.addEventListener("workflow:started", onStarted)
  window.addEventListener("workflow:updated", onUpdated)
  window.addEventListener("workflow:completed", onCompleted)
  window.addEventListener("workflow:failed", onFailed)

  return () => {
    window.removeEventListener("workflow:started", onStarted)
    window.removeEventListener("workflow:updated", onUpdated)
    window.removeEventListener("workflow:completed", onCompleted)
    window.removeEventListener("workflow:failed", onFailed)
  }
}, [])
```

---

## Mapa Completo de Arquivos Modificados / Criados

### Novos arquivos (3)

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `src/components/unified-chat/ThinkingStepsCard.tsx` | ~56 | Live task feed (UX-1) |
| `src/components/unified-chat/OutreachCard.tsx` | ~200 | Outreach multi-canal (UX-6) |
| `src/components/unified-chat/wizard/panels/SchedulingPanel.tsx` | ~230 | Agendamento como workspace panel (UX-5) |

### Arquivos modificados (7)

| Arquivo | Sprint | Mudanças |
|---------|--------|---------|
| `unified-chat/UnifiedMessageList.tsx` | UX-1, UX-6 | Remove TypingIndicator, add ThinkingStepsCard + OutreachCard |
| `unified-chat/UnifiedChatHeader.tsx` | UX-2 | Prop `activeTaskLabel` + ActiveTaskPill |
| `unified-chat/UnifiedChat.tsx` | UX-2,3,7 | WIZARD_STAGE_LABELS, SPLIT_STAGES, fullscreen hint, workflow events, panel 420px fullscreen |
| `unified-chat/wizard/DynamicContextPanel.tsx` | UX-3, UX-5 | Export SPLIT_STAGES, case "scheduling", lazy SchedulingPanel |
| `unified-chat/wizard/wizard-types.ts` | UX-5 | Adicionado `"scheduling"` ao union WizardStage |
| `unified-chat/wizard/panels/CalibrationPanel.tsx` | UX-4 | Pool counter + Must-haves vs Sourcing sections |
| `workflow-rail/useWorkflowRail.ts` | UX-7 | Listeners: workflow:started/updated/completed/failed |

---

## Eventos Customizados — Namespace Completo

### Eventos existentes (não alterados)
| Evento | Quem emite | Quem escuta |
|--------|-----------|------------|
| `lia:navigation-hint` | UnifiedChat | dashboard-app |
| `lia:navigate-chat-page` | UnifiedChat | dashboard-app |
| `lia:leave-fullscreen-chat` | UnifiedChat | dashboard-app |
| `lia:chat-mode-changed` | UnifiedChat | dashboard-app |
| `lia:prefill-message` | MessageActions | UnifiedChatInput |
| `lia:wizard-edit-question` | CalibrationPanel, WizardPanels | useWizardIntegration |

### Novos eventos (este sprint)
| Evento | Quem emite | Quem escuta | Payload |
|--------|-----------|------------|---------|
| `workflow:started` | UnifiedChat | useWorkflowRail | `{ id, type, label, stage }` |
| `workflow:updated` | UnifiedChat | useWorkflowRail | `{ id, stage, label }` |
| `workflow:completed` | UnifiedChat | useWorkflowRail | `{ id, outcome }` |
| `workflow:failed` | UnifiedChat | useWorkflowRail | `{ id, error }` |
| `workflow:thinking` | UnifiedChat | (futuro: Rail pulsing) | `{ id, isThinking }` |
| `lia:scheduling-confirmed` | SchedulingPanel | backend via chat | `{ slots, interviews, vacancyId }` |
| `lia:outreach-send` | OutreachCard | backend via chat | `{ channel, candidateId, data }` |
| `lia:outreach-edit` | OutreachCard | DynamicContextPanel | `{ channel, candidateId, data }` |

---

## O que o Backend Precisa Fazer (Pendências)

### Para UX-4 (CalibrationPanel com dados reais)

Adicionar ao payload do stage `calibration`:
```json
{
  "pool_count": 847,
  "criteria": [
    { "label": "5+ anos Python", "type": "must_have" },
    { "label": "Experiência Fintech", "type": "sourcing" }
  ]
}
```

Atualizar `pool_count` após cada feedback de thumbs (já existe endpoint de calibração,
apenas adicionar o count na resposta).

### Para UX-5 (SchedulingPanel)

Enviar stage `"scheduling"` via WebSocket com slots disponíveis:
```python
# Em qualquer agent/node que proponha agendamento
ws_stage_payload(
    stage="scheduling",
    data={
        "interviews": [...],
        "available_slots": [...],
        "vacancy_id": vacancy_id,
        "candidate_name": candidate.name,
    }
)
```

Receber `lia:scheduling-confirmed` via chat message ou endpoint dedicado.

### Para UX-6 (OutreachCard)

Enviar metadata na mensagem LIA ao gerar outreach:
```python
# Em qualquer agent que gere comunicação com candidato
return LiaChatMessage(
    content="Preparei o email para João Silva:",
    metadata={
        "type": "outreach_message",
        "outreach": {
            "channel": "email",
            "candidate_name": candidate.name,
            "candidate_id": str(candidate.id),
            "subject": "Oportunidade em ...",
            "body": "Olá João...",
        }
    }
)
```

---

## Cobertura Competitiva Final (Tezi vs WeDo)

| Feature Tezi | WeDo antes | WeDo agora |
|-------------|-----------|-----------|
| Task Context Bar (tarefa ativa + ⌘K) | ❌ | ✅ ActiveTaskPill (UX-2) |
| Split view apenas na calibração | ⚠️ todos os stages | ✅ SPLIT_STAGES (UX-3) |
| Live task evolution (Manus-style) | ❌ steps não renderizados | ✅ ThinkingStepsCard (UX-1) |
| Calibração com perfis reais + pool counter | ❌ | ✅ (UX-4, backend pendente) |
| Must-haves vs Sourcing | ❌ misturado | ✅ seções separadas (UX-4) |
| Agendamento como workspace (não modal) | ❌ modal interrompe | ✅ SchedulingPanel (UX-5) |
| Multi-entrevista paginada (1/2 → 2/2) | ❌ | ✅ (UX-5) |
| Email outreach inline com aprovação | ⚠️ existe mas não visível | ✅ OutreachCard (UX-6) |
| Outreach WhatsApp inline | ❌ | ✅ (UX-6) |
| Outreach ligação + roteiro inline | ❌ | ✅ (UX-6) |
| Outreach VoIP + WebChat inline | ❌ (Tezi não tem) | ✅ (UX-6) |
| WorkflowRail integrado ao wizard | ❌ | ✅ eventos lifecycle (UX-7) |
| Fullscreen mais largo para trabalho intenso | ❌ | ✅ 420px (UX-2d) |
| Sugestão automática de fullscreen | ❌ | ✅ toast único (UX-2c) |

**WeDo mantém vantagem sobre Tezi em:**
- Cards de candidato mais ricos (ParecerLIACard)
- Triagem por voz (WSI Voice + Gemini + Twilio)
- Outreach VoIP e WebChat (Tezi só tem email)
- Multi-tenant nativo

---

## Notas para Próxima Sprint

1. **Backend UX-4**: Enviar `pool_count` + `criteria` no payload de calibração
2. **Backend UX-5**: Implementar `ws_stage_payload(stage="scheduling", data=...)` no agent de agendamento
3. **Backend UX-6**: Retornar `metadata.type = "outreach_message"` em mensagens de outreach
4. **Rail pulsing**: `workflow:thinking` emitido mas sem listener no WorkflowRail ainda
5. **OutreachEditPanel**: Botão "Editar" do OutreachCard dispara `lia:outreach-edit` mas o DynamicContextPanel não tem case para renderizar editor ainda
6. **SmartSuggestions pós-workflow**: chips contextuais após `stage === "done"` — planejado mas não implementado

---

## PARTE I — BETA badge polish, ocultar chat/rail em rotas de auth e ajustes de teste e2e

> **Branch de destino:** `wedotalent/replit-sync`
> **Commits cobertos:** `f1134ff0f` → `03440865d` (4 commits, cronológico)
> **Data:** 2026-04-20

---

### Commits em ordem cronológica

#### `f1134ff0f` — Ajustes nos testes e2e para autenticação

Sem tarefa associada.

O arquivo `plataforma-lia/e2e/tests/agentic-eval/agentic-eval.spec.ts` ganhava um
`authenticatedPage` importado do fixture compartilhado que chamava `page.goto()` na
inicialização, travando em dev-mode (HMR WebSockets impediam o `waitUntil='load'`).

**O que mudou:**
- O `test` padrão é estendido localmente (`_baseTest.extend`) com um
  `authenticatedPage` que injeta cookies de autenticação (`lia_access_token`,
  `lia_auth_method`) mas **não** navega — cada cenário chama `openChatOnPage`
  diretamente para `/pt/chat`.
- Adicionados três arquivos JSON de resultados de execução em
  `lia-agent-system/eval/agentic/runs/` para registrar as rodadas de avaliação do dia.

**Impacto no produto:** sem mudança visível para o usuário; estabiliza a suite de
avaliação agêntica para que os cenários de chat autenticado não travam no servidor de
desenvolvimento.

---

#### `9d0218eb7` — Task #649: BETA badge azul, menor, com fonte menor

**Arquivo modificado:** `plataforma-lia/src/components/ui/beta-badge.tsx`

O badge BETA saiu do roxo (`bg-wedo-purple`) para um azul padrão (`bg-blue-600`) e
teve padding e tamanho de fonte reduzidos em ambos os sizes (`sm` e `md`):

```diff
- sm: px-1.5 text-[8px]   →  sm: px-1   text-[7px]
- md: px-2 py-0.5 text-[9px]  →  md: px-1.5 py-[1px] text-[8px]
```

**Impacto no produto:** badge mais discreto e alinhado à paleta de blues do design
system; não altera nenhum comportamento funcional. Mockup sandbox atualizado junto
(`artifacts/mockup-sandbox/src/.generated/mockup-components.ts`).

---

#### `019c35c9a` — Atualização de mockups e configurações de teste de agentes

Sem tarefa associada (commit de acompanhamento do #649).

- `mockup-components.ts` sincronizado com as novas classes do badge.
- `plataforma-lia/e2e/tests/agentic-eval/agentic.config.ts` expandido com novas
  opções de `launchOptions` para melhorar a estabilidade das rodadas de avaliação
  agêntica no ambiente Replit.

**Impacto no produto:** puramente infraestrutura de teste e storybook; zero impacto
em produção.

---

#### `03440865d` — Task #650: Polimento final do BETA badge (cyan) e ocultar chat/WorkflowRail nas rotas de auth

**Arquivos modificados:**
- `plataforma-lia/src/components/ui/beta-badge.tsx`
- `plataforma-lia/src/components/unified-chat/UnifiedChatConditional.tsx`
- `plataforma-lia/src/components/workflow-rail/WorkflowRailWrapper.tsx`

**Arquivo novo:**
- `plataforma-lia/src/lib/auth-routes.ts`

**Badge:** cor final definida como `bg-wedo-cyan` (não mais `bg-blue-600`); fonte
reduzida mais um passo:

```diff
- sm: px-1   text-[7px]  →  sm: px-1   text-[6px]
- md: px-1.5 py-[1px] text-[8px]  →  md: px-1.5 py-[1px] text-[7px]
```

**Helper `isAuthRoute`:** função em `src/lib/auth-routes.ts` que recebe um
`pathname`, remove o prefixo de locale opcional (`/<locale>/`) e verifica se a rota
pertence à lista de rotas de autenticação:
`login`, `forgot-password`, `reset-password`, `register`, `accept-invitation`,
`aceitar-convite` (locale PT para convites).

**Chat oculto em auth:** `UnifiedChatConditional` substituiu a comparação com lista
literal de caminhos (`HIDDEN_PATHS`) pela chamada a `isAuthRoute()`, cobrindo
automaticamente qualquer variante com prefixo de locale (`/pt/login`, `/en/login`,
etc.).

**WorkflowRail oculto em auth:** `WorkflowRailWrapper` passou a retornar `null`
logo no início quando `isAuthRoute()` retorna `true`, antes mesmo do bloco de
fallback educacional dev-only — impedindo que o rail vaze para a tela de login em
qualquer ambiente.

**Impacto no produto:** as telas de login e demais rotas de autenticação ficam
completamente limpas do chat bubble, super-prompt e barra de workflows, tanto em
produção quanto em desenvolvimento.

---

### O que muda na UI

| Elemento | Antes (PARTE H) | Depois (PARTE I) |
|----------|----------------|-----------------|
| Badge BETA — cor | `bg-wedo-purple` (roxo) | `bg-wedo-cyan` (cyan WeDo) |
| Badge BETA — tamanho `sm` | `px-1.5 text-[8px]` | `px-1 text-[6px]` |
| Badge BETA — tamanho `md` | `px-2 py-0.5 text-[9px]` | `px-1.5 py-[1px] text-[7px]` |
| Chat bubble em `/pt/login` | Visível (só `/dashboard` era escondido) | Oculto via `isAuthRoute()` |
| WorkflowRail em rotas de auth | Vazava em modo dev | Oculto em todos os ambientes |
| Testes e2e autenticados | `authenticatedPage` chamava `goto`, travava em HMR | Cookie injection sem `goto`; navega via `/pt/chat` |

---

### Pendências para próxima sprint

1. **`isAuthRoute` — cobertura de testes unitários**: a função foi usada em dois
   consumidores mas ainda não tem teste dedicado; adicionar em `src/lib/__tests__/`.
2. **Badge BETA — documentar token `wedo-cyan`**: confirmar que `bg-wedo-cyan` está
   mapeado nos tokens do design system e atualizar a seção de tokens do Storybook.
3. **Rail pulsing (`workflow:thinking`)**: emitido pelo `UnifiedChat` mas sem
   listener no `WorkflowRailWrapper` — pendência herdada da PARTE H, item 4.


---

## PARTE J — Onda Benefícios + Departamentos + Workforce (16 commits, 2026-04)

> **Repo alvo:** `WeDOTalentcc/wedotalent02202026` · **Remote sincronizado:** `wedotalent/replit-sync`
> **Range:** `32f29426f..cfe3f51fa` (16 commits, branch `develop`)
> **Origem:** Tasks #763 → #768, #775, #776 (mais correção pós-merge de `voice_service`/`granular_consent`)
> **Audit baseline obrigatório:** [`docs/audits/beneficios-departamentos-workforce-audit-2026-04.md`](../docs/audits/beneficios-departamentos-workforce-audit-2026-04.md)
>
> Esta parte é um **guia de replicação** para três times trabalhando em paralelo:
> - **Front (replicar)** — entregue neste repo (`plataforma-lia`); aqui só listamos o "como" para qualquer fork.
> - **Rails `ats-api-copia` (especificar)** — backend institucional precisa do mesmo schema/contratos. Specs abaixo.
> - **IA repo separado (especificar)** — onde vivem os agentes LangGraph; specs de tools, audit log e Fairness abaixo.
>
> Cada bloco abaixo lista commits originais, o quê foi feito no Front, e os specs Rails + IA.

### Commits em ordem cronológica (16 commits, oldest → newest)

| # | Hash curto | Título |
|---|---|---|
| 1 | `66343bef5` | Git commit prior to merge (snapshot automático) |
| 2 | `975d5e0d9` | docs(audit): baseline Benefícios + Departamentos + Workforce (task #763) |
| 3 | `ebe39fccb` | Update component imports for welcome polish mockups |
| 4 | `a2913e268` | feat(minha-empresa): Benefícios item-a-item + schema unificado em 4 camadas |
| 5 | `c817b80f6` | Update component registration to include chat welcome polish mockups |
| 6 | `241d88f72` | Persist enriched benefit fields via LIA chat tool |
| 7 | `3045bdfdd` | Task #767: remove Departamentos from "Minha Empresa" Hub + onboarding |
| 8 | `90833f800` | Group benefits list by category with icon and count (Task #775) |
| 9 | `68bef95bf` | Git commit prior to merge (snapshot automático) |
| 10 | `43981a976` | Task #766: paridade Beneficios chat ↔ Hub no schema canonico |
| 11 | `311e74269` | Git commit prior to merge (snapshot automático) |
| 12 | `843a0d224` | Task #768 — Workforce planning: rich view + 3 conversational paths + HITL |
| 13 | `7a5142db5` | Git commit prior to merge (snapshot automático) |
| 14 | `e03e9c7fa` | task#765: JobVacancy.benefits ARRAY→JSONB with structured backfill |
| 15 | `182dec756` | Add pagination to job search functionality |
| 16 | `cfe3f51fa` | fix: restore voice_service.py and granular_consent_service.py from broken merge |

> **Done looks like (checklist por commit):** cada commit acima é coberto por um bloco abaixo (J.0 a J.11). Use a coluna “Bloco” do mapa logo a seguir para localizar a especificação completa de cada hash.

### Mapa de commits → blocos

| Bloco | Commits |
|---|---|
| J.0 Auditoria baseline | `975d5e0d9` (Task #763) |
| J.1 Piloto Benefícios Hub Minha Empresa | `a2913e268` (Task #764) |
| J.2 Schema canônico Benefícios (chat ↔ Hub) | `43981a976` (Task #766) |
| J.3 Persistência enriquecida via chat | `241d88f72` |
| J.4 Vaga: `benefits` ARRAY → JSONB | `e03e9c7fa` (Task #765) |
| J.5 Lista de benefícios agrupada por categoria | `90833f800` (Task #775) |
| J.6 Remoção de Departamentos do Hub + onboarding | `3045bdfdd` (Task #767) |
| J.7 Workforce: visualização rica + 3 paths conversacionais + HITL | `843a0d224` (Task #768) |
| J.8 Pagination na busca de vagas | `182dec756` |
| J.9 Polimento mockup welcome chat | `c817b80f6`, `ebe39fccb` |
| J.10 Snapshots automáticos (`Git commit prior to merge`) | `7a5142db5`, `311e74269`, `68bef95bf`, `66343bef5` |
| J.11 Correção pós-merge: `voice_service` + `granular_consent` | `cfe3f51fa` |

---

### J.0 — Auditoria baseline (read-only)

**Front (replicar):** ler `docs/audits/beneficios-departamentos-workforce-audit-2026-04.md` antes de qualquer mudança nesses domínios. Define mapa canônico, duplicatas conhecidas, mismatches de schema, fallbacks silenciosos e ordem segura de execução.

**Rails (especificar):** produzir baseline equivalente em `ats-api-copia` cobrindo `Benefit`, `CompanyBenefit`, `Department`, `WorkforceEntry`/`PlannedHeadcount`. Output mínimo: tabela "campo × DB × ActiveRecord × serializer × consumidores" e duplicatas a remover.

**IA (especificar):** mapear todas as tools que tocam esses domínios — leitura (`get_company_profile`, `get_workforce`) e escrita (`save_company_benefits`, `save_workforce_plan`, `import_benefits_from_data`). Marcar quais aplicam FairnessGuard, PII masking e audit log.

---

### J.1 — Piloto Benefícios no Hub Minha Empresa (Task #764, commit `a2913e268`)

**Front (replicar):**
- UI canônica: `plataforma-lia/src/components/settings/BenefitsTab.tsx` + `benefits/BenefitItemCard.tsx` + `benefits/BenefitFormModal.tsx` + `benefits/BenefitTemplateModal.tsx`.
- **Novo componente:** `plataforma-lia/src/components/settings/benefits/BenefitsListSection.tsx` — renderiza lista item-a-item dentro do card, invalida cache de `useCompanyBenefits` e dispara o evento DOM `lia:settings-updated` a cada mutação.
- Card "Benefícios & Departamentos" foi **renomeado para "Benefícios"** (em `use-company-settings-cards.ts`).
- Header do bloco ganhou novo campo **`subtitle` em `CardBlock`** mostrando agregado: `"X cadastrado(s) · Y ativo(s)"`.
- Botão "Adicionar benefício" reaproveita o `BenefitFormModal` existente (sem duplicar UI).
- Hook `use-company-settings-cards` agora expõe `benefits` e `companyId` e calcula status do bloco pela quantidade de benefícios ativos.
- **Enum `BenefitCategory` unificado** em `types/benefits.ts`, `BenefitsTab`, `BenefitFormModal`, `BenefitTemplateModal` e nos maps de ícones em `SalaryStage` (chat + wizard).
- Type FE: `src/types/benefits.ts` espelha o modelo rico (`provider`, `value_type`, `seniority_levels`, `waiting_period_days`, `is_mandatory`, `is_discount`).
- Padrão visual: lista item-a-item, modal de form, modal de templates filtráveis por categoria/popular, batch-edit com `pendingChanges`/`backup`.

**Backend Python (referência):**
- `lia_models/company_benefit.py`: +`provider, percentage_value, value_details, seniority_levels (JSONB), waiting_period_days, is_mandatory, is_discount`.
- Migration **idempotente** `alembic/versions/099_extend_company_benefits_schema.py`.
- `app/api/v1/company_benefits.py`: Pydantic Create/Update/Response cobrem todos os novos campos; novo endpoint `/active`; `categories/list` canônico inclui `wellness, flexibility, other`.
- **Bug fix audit:** `import_tools.py` usava `is_highlight` (coluna **inexistente**) — corrigido para `is_highlighted` aceitando ambos no input; enum do JSON schema atualizado.

**Rails `ats-api-copia` (especificar):**
- `Company::Benefit` model (singular, dono dos campos ricos) + tabela `company_benefits`.
- Colunas obrigatórias: `name, category, description, icon, provider, value, value_type, percentage_value, value_details, seniority_levels (JSONB), waiting_period_days, is_active, is_highlighted, is_mandatory, is_discount, order, company_id, created_at, updated_at`.
- Endpoints REST equivalentes: `GET /company/benefits`, `GET /company/benefits/active`, `POST /company/benefits`, `PUT /company/benefits/:id`, `DELETE /company/benefits/:id` (soft + hard via `?hard_delete=true`), `POST /company/benefits/seed-defaults`, `GET /company/benefits/categories/list`.
- Categorias canônicas (enum compartilhado): `health, food, transport, education, wellness, financial, quality_life, family, flexibility, security, other`.
- Validação: `value_type ∈ {informative, monetary, percentage, boolean}`. Se `value` informado e `value_type ∈ {nil, informative}` → 422.
- Multi-tenant scoping: SEMPRE filtrar por `company_id` derivado do JWT (paridade com `get_user_company_id`).

**IA (especificar):**
- Tool `save_company_benefits(company_id, benefits[], mode='append'|'replace', source='chat'|'spreadsheet'|'website', user_id)`.
- Schema do item idêntico a `CANONICAL_BENEFIT_FIELDS` (ver J.2).
- Pipeline obrigatório: clarification (J.2) → PII masking (CPF/email/telefone) → FairnessGuard L1 sobre `name`, `description`, `value_details` → INSERT com `seniority_levels` em JSONB → audit log com `source`.
- Mode `replace` exige confirmação humana (HITL) — destrutivo.

---

### J.2 — Schema canônico Benefícios chat ↔ Hub (Task #766, commit `43981a976`)

**Front (replicar):**
- O type FE (`benefits.ts`) já contém todos os campos do modelo rico — usar como contrato único.
- O wizard de vaga (`SalaryStage.tsx` + `WizardContext.tsx:295-315`) hidrata `JobBenefit[]` da empresa preservando metadata.
- Quando a tool retorna `needs_clarification=True`, exibir como `clarification_response` com `navigation_hint` para o Hub (não persistir nada).

**Backend Python (referência canônica):**
- `_wrap_save_company_benefits` (`company_tool_registry.py`): aceita schema canônico completo; valida pares obrigatórios (clarification-first); mascara PII em texto livre; FairnessGuard L1 em `name/description`; persiste `seniority_levels` como JSONB; **audit log com `source ∈ {chat, spreadsheet, website}`**. Exporta `CANONICAL_BENEFIT_FIELDS`, `VALID_BENEFIT_VALUE_TYPES`, `BENEFIT_CLARIFICATION_FIELDS` para reuso.
- **`_handle_configure_benefits`** (`domain.py`): forwarda `source` e converte `needs_clarification` em `DomainResponse.clarification_response` com `navigation_hint`.
- **`_handle_analyze_website`** fase 1: promove benefícios extraídos (`list[str]`) para `list[dict{name}]` e expõe `expected_fields` a serem preenchidos antes da confirmação humana (TIER 3).
- **`import_benefits_from_data`** (`import_tools.py`): refatorado — agora **delega ao wrapper canônico** com `source="spreadsheet"`. Corrige bug `is_highlight` via alias para `is_highlighted` e **propaga `needs_clarification`** em vez de gravar incompleto.
- **`capabilities.yaml`**: nova seção **`actions.configure_benefits`** documenta campos aceitos, regras de clarification, sources e `audit_action`.
- 6 testes unitários novos (51/51 passando) — ver tabela "Testes adicionados".
- Guardrail registrado em `CLAUDE.md` e na skill `lia-compliance`.

**Rails (especificar):**
- Manter `Company::Benefit` como **único** modelo de benefício de empresa. Não duplicar em `CompanyBenefit` simples.
- Migration que estende a tabela com os 5 campos novos (`provider, value, value_type, percentage_value, value_details, seniority_levels, waiting_period_days, is_mandatory, is_discount`) — espelhar `lia-agent-system/alembic/versions/099_extend_company_benefits_schema.py`.
- Serializer único `Company::BenefitSerializer` retornando `seniority_levels` como array (default `["all"]`).

**IA (especificar):** definir `CANONICAL_BENEFIT_FIELDS` constante:
```
{name, category, description, icon, provider,
 value, value_type, percentage_value, value_details,
 seniority_levels, waiting_period_days,
 is_active, is_highlighted, is_mandatory, is_discount, order}
```
Regras de clarification (devolver `needs_clarification=True` SEM gravar):
- `value_type` fora de `{informative, monetary, percentage, boolean}` → bloquear.
- `value` fornecido com `value_type ∈ {nil, informative}` → pedir tipo explícito.
- `value_type=monetary` sem `value` nem `value_details` → pedir um dos dois.
- `value_type=percentage` sem `percentage_value` nem `value` → pedir.
- `percentage_value` sem `value_type=percentage` → corrigir tipo.

Guardrail de teste (CI): `tests/unit/test_company_settings_actions.py` deve falhar se modelo, schema Pydantic, type FE e `CANONICAL_BENEFIT_FIELDS` divergirem.

---

### J.3 — Persistência enriquecida via LIA chat (commit `241d88f72`)

**Front (replicar):** nada — fluxo é 100% backend/IA. O chat já chama a tool e o Hub re-renderiza por invalidação de cache.

**Rails (especificar):** endpoint dedicado **opcional** `POST /company/benefits/bulk` (mode `append|replace`) usado pelo serviço de IA. Reaproveita CRUD se preferir.

**IA (especificar):** referência canônica em `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py:374-460` (`_wrap_save_company_benefits`). Pontos críticos:
1. **Reject empty list** → `success=false, message="Lista de beneficios vazia."`.
2. **PII masking** com `mask_pii(text, [CPF_PATTERN, EMAIL_PATTERN, PHONE_BR_PATTERN])` em `name`, `description`, `value_details` antes do INSERT (LGPD Art. 6).
3. **FairnessGuard L1** via `_walk_fairness_check(value)` — só strings com `len > 10`.
4. **Audit log** via `AuditService.log_action(action_type='company_settings.save_benefits', actor='company_settings_agent', target_type='company', metadata={source, count, mode})`.
5. **Remover** o path duplicado/quebrado `import_tools.import_benefits_from_data` (escreve `is_highlight` — coluna inexistente, o correto é `is_highlighted`).

---

### J.4 — `JobVacancy.benefits`: ARRAY(String) → JSONB estruturado (Task #765, commit `e03e9c7fa`)

**Front (replicar):**
- Helper canônico **layer-free**: `lia-agent-system/app/utils/benefits.py` — `normalize_benefits_payload(raw)` e `benefit_display_names(benefits)`. Importável por API, domain, embedding, notificações, chat.
- Wizard (`WizardContext.tsx`) já produz `JobBenefit[]` estruturado; nenhuma mudança visual necessária.
- Display "flat" (notificações, vaga pública, prompts LLM) → `benefit_display_names()` para extrair `name` preservando legados que ainda chegam como `string`.

**Rails (especificar):**
- Migration espelhando `lia-agent-system/alembic/versions/100_job_vacancy_benefits_jsonb.py`:
  1. Adicionar `benefits_json JSONB DEFAULT '[]'::jsonb` (sem destruir `benefits`).
  2. **Backfill**: para cada nome em `benefits` (ARRAY(String)), match normalizado contra `company_benefits` da MESMA `company_id`. Match → copiar `category, description, icon, value`. Sem match → `{name, category: 'other', source: 'legacy_string'}`. Volume estimado: ~42 vagas afetadas.
  3. **Dual-write** por 1 release: continuar escrevendo `benefits` (nomes) e `benefits_json` (estruturado).
  4. Após validação no FE, `DROP COLUMN benefits` e `RENAME benefits_json → benefits`.
- Serializer `JobVacancySerializer#benefits` deve retornar a forma estruturada.
- Validação: itens sem `name` (string vazia ou nula) são descartados silenciosamente — paridade com `normalize_benefits_payload`.

**IA (especificar):**
- Tool de criar/editar vaga (`create_job`, `update_job`) deve aceitar `benefits` como lista de objetos canônicos OU lista de strings (legado), e normalizar via `normalize_benefits_payload` antes de salvar.
- Embedding/prompts da vaga devem usar `benefit_display_names()` — nunca consumir o JSONB cru.
- Guardrail (CLAUDE.md / AGENTS.md): "JobVacancy.benefits é JSONB estruturado, nunca array de string."

---

### J.5 — Lista agrupada por categoria com ícone e contador (Task #775, commit `90833f800`)

**Front (replicar):**
- `BenefitsTab.tsx` agora agrupa benefícios por `category`, exibindo `BenefitCategoryHeader` (ícone + nome humano + count `N`) acima de cada grupo.
- Ordem das categorias segue o enum canônico (`health → other`).
- Categoria `null` cai em "Outros".

**Rails (especificar):** se construir UI institucional equivalente, replicar a mesma ordem de categorias do enum compartilhado. Backend não muda — agrupamento é puramente FE.

**IA (especificar):** quando o agente lista benefícios via chat ("quais benefícios temos?"), retornar **agrupado por categoria** no `summary_text`, com count por categoria — paridade visual com o Hub.

---

### J.6 — Remover Departamentos do Hub Minha Empresa + onboarding (Task #767, commit `3045bdfdd`)

**Front (replicar):**
- `use-company-settings-cards.ts`: removidos `departments` state, `fetchDepartments`, campo `departments_count`; bloco renomeado de **"Beneficios & Departamentos" → "Beneficios"**.
- `MinhaEmpresaHub.tsx`: adicionado **atalho textual "Gerenciar departamentos"** que dispara dois eventos DOM: `settings-open-tab` (já existente) e o **novo evento `settings-open-subtab`**.
- `UsuariosDepartamentosHub.tsx`: passa a **escutar `settings-open-subtab`** e pré-seleciona a aba `departments` quando acionado.
- `OnboardingActionOrchestrator.tsx`: removida a palavra "departamento" do prompt da intent `configure_workforce`.
- **Manter intactos:** `useDepartmentManagement.ts`, `useCompanyData.fetchDepartments`, router `company_departments`, modelo `Department`, endpoint REST `import_departments`.
- Smoke test: MinhaEmpresaHub não exibe mais "Departamentos"; clicar no atalho leva ao Hub Usuários & Departamentos com a aba certa pré-selecionada.

**Backend Python (referência):**
- **`capabilities.yaml`**: novos keywords da intent **`manage_departments`**.
- **`domain.py`**: nova `DomainAction.manage_departments` + handler **`_handle_manage_departments`** (routing-only, **sem writes**) retornando `navigation_hint` com `section=usuarios-departamentos, tab=departments`.
- Preserva fluxo de aprovador e endpoint REST `import_departments` intactos.
- Teste novo: `test_manage_departments_is_routing_only` em `tests/unit/test_company_settings_actions.py`.

**Rails (especificar):** sem mudança de schema. Replicar a intent `manage_departments` como rota de navegação (sem writes). Garantir que `Department` continua acessível **apenas** via Hub Usuários & Departamentos.

**IA (especificar):**
- Intent `configure_workforce` **não coleta mais** `departamento` (mover para fluxo próprio quando/se necessário).
- Implementar a intent `manage_departments` como **routing-only** (não criar tool de write — gerenciamento é manual via UI dedicada).

---

### J.7 — Workforce: visualização rica + 3 paths conversacionais + HITL (Task #768, commit `843a0d224`)

**Front (replicar):**
- **Novo componente:** `WorkforceHubContent` — wrapper do canônico `WorkforceSection` (tabela departamento × mês, totais, edit inline) que liga os 3 paths concretos:
  1. **Anexar planilha** — file picker real → upload para `/api/backend-proxy/workforce/entries/import` → entrega ao chat para HITL.
  2. **Descrever no chat** — dispara intent `configure_workforce` com `input_mode=text`.
  3. **Colar dados** — modal captura tabela colada e envia como `raw_text` via prefill do chat com `input_mode=paste`.
- **`MinhaEmpresaCard`**: substitui a lista de campos legada por `WorkforceHubContent` quando `block.key === "workforce"` (sem renderização duplicada dos campos antigos).

**Backend Python (referência canônica):**
- **`_wrap_import_workforce_plan`** suporta os 3 modos (`spreadsheet | paste | text`) e impõe **gate HITL estrito**: persistência exige `approved is True` (o booleano Python real). Valores como `"false"`, `"no"`, `0`, `1`, `"True"` (string) **não bypassam** a aprovação.
- **Parser determinístico de TSV / CSV / `;`** (paste) com **aliases PT/EN** para cabeçalhos. Texto livre vai ao **extrator Claude com PII masking upfront**.
- `ToolDefinition`, `tool_registry_metadata.yaml` e `_handle_configure_workforce` atualizados para forwardar `input_mode`, `raw_text` e `approved`.
- Texto de clarification mantém a palavra "planejamento" — **regressão #712**.
- Testes: `tests/unit/test_workforce_plan_hitl.py` (7 casos) cobre cada modo de input, recusa de input vazio, aliases de paste, rejeição de header desconhecido + regressão parametrizada provando que **só o booleano `True` real** desbloqueia persistência. Suite total: 56 testes verdes.

**Rails (especificar):**
- Definir o canônico: `PlannedHeadcount` (com `title, salary, hiring_manager, department_id`) é o plano detalhado; `WorkforceEntry` apenas agregação derivada (yearly/monthly totais).
- Endpoints (nomes canônicos — paridade com o proxy do FE em `src/app/api/backend-proxy/workforce/entries/import`): `GET/POST /workforce/plans`, `GET/POST /workforce/headcounts`, `POST /workforce/entries/import` (devolve preview), `POST /workforce/entries/import/confirm` (commita). Onde houver legado citando `/workforce/import/upload`, tratar como **alias deprecado** que aponta para `/workforce/entries/import`.
- Backfill/migração: nenhum dado destrutivo; só consolidar leituras no canônico.

**IA (especificar):**
- Manter `forecast_hiring_needs` (em `app/domains/talent_intelligence/tools/workforce_planning_tools.py`) — só estima.
- **Criar** tool `_wrap_save_workforce_plan(company_id, plan[], mode='append'|'replace', source='chat'|'spreadsheet'|'paste', user_id)` análoga a `_wrap_save_company_benefits`. Pipeline:
  1. Clarification (faltando `title`, `department_id`, `quantity`, `target_date`).
  2. PII masking em `hiring_manager_email`/notes.
  3. FairnessGuard L1 sobre justificativas em texto livre.
  4. Audit log `workforce.save_plan`.
  5. HITL para `mode=replace`.
- Documentar defaults arriscados: turnover 15% (`workforce_planning_tools.py:100`), benchmark 45 dias (`:132`) — citar no audit.

---

### J.8 — Pagination na busca de vagas (commit `182dec756`)

**Contrato canônico (implementado):** `search_jobs(query, filters, offset=0, limit=20)` em `query_tools.py`. Resposta inclui novo campo **`total_count`** (contagem real no DB) + bloco de **metadados de paginação**. Corrige discrepância em que o `total` reportado não refletia o real.

**Front (replicar):**
- Lista de vagas paginada usando `offset` + `limit` (não `page`/`per_page`).
- Hook de busca consome `total_count` para mostrar "1–20 de N" e calcular se há próxima página (`offset + limit < total_count`).

**Rails (especificar):**
- `GET /jobs` aceita `offset` (default 0) e `limit` (default 20, máximo 100) — paridade com o contrato Python da tool.
- Resposta: `{ data: [...], total_count: <int>, pagination: { offset, limit, has_more } }`. Header `X-Total-Count` opcional como espelho de `total_count`.
- Indexar colunas usadas em filtros + `created_at DESC` para paginar de forma estável.

**IA (especificar):**
- Tool `search_jobs(query, filters, offset=0, limit=20)` — assinatura idêntica à de `query_tools.py`.
- Resposta DEVE expor `total_count` no topo do payload + `pagination.has_more`.
- Em respostas longas, paginar visualmente ("mostrando 1–20 de 87").
- Teste de fumaça: `tests/unit/test_fix20_pagination.py` valida assinatura, exposição do schema e marcador de rastreabilidade do fix.

---

### J.9 — Polimento de mockups do welcome chat (commits `c817b80f6`, `ebe39fccb`)

**Front (replicar):** ajustes de imports e registro de componentes na sandbox de mockups (`artifacts/mockup-sandbox`). Sem impacto em runtime do app principal.

**Rails (especificar):** N/A.
**IA (especificar):** N/A.

---

### J.10 — Snapshots automáticos "Git commit prior to merge"

**Commits:** `7a5142db5`, `311e74269`, `68bef95bf`, `66343bef5`.

**O quê são:** snapshots automáticos criados pelo workflow de merge da plataforma de tasks **antes** de aplicar o patch de cada task agent. Documentação-only no contexto deste handoff — não há código a replicar.

**Implicação para os 3 times:** ao consumir o range `32f29426f..cfe3f51fa`, considerar esses 4 commits como ruído controlado (não revertem nada; só marcam o estado pré-merge).

---

### J.11 — Correção pós-merge: `voice_service` + `granular_consent` (commit `cfe3f51fa`)

**Front (replicar):** N/A.

**Rails (especificar):** N/A (serviços vivem no backend de IA).

**IA (replicar — post-merge fix):**
- Restaurar `lia-agent-system/app/domains/voice/services/voice_service.py` (335 linhas) — `VoiceService` com `transcribe_audio` (Whisper), `synthesize_speech` (TTS), `stream_transcription`, detecção automática de formato (`mp3, wav, webm, m4a, ogg, flac, mpeg`), vozes suportadas (`alloy, echo, fable, onyx, nova, shimmer`).
- Restaurar `granular_consent_service.py` no mesmo padrão (LGPD — consentimento granular por finalidade).
- **Causa raiz:** merge automático apagou ambos os arquivos; backend ficou sem startar (`ModuleNotFoundError`). Guardrail recomendado: smoke-test `python -c "from app.main import app"` no post-merge hook (`.local/skills/post_merge_setup`).

---

### Sumário consolidado

#### DB / migrations (paridade Python ↔ Rails)

| Migration | Domínio | Mudança |
|---|---|---|
| `099_extend_company_benefits_schema.py` | Benefícios | +`provider, value, value_type, percentage_value, value_details, seniority_levels (JSONB), waiting_period_days, is_mandatory, is_discount` |
| `100_job_vacancy_benefits_jsonb.py` | Vaga | `benefits ARRAY(String)` → `JSONB`, com backfill por match contra `company_benefits` da empresa |

#### Endpoints REST canônicos

| Método | Path | Domínio |
|---|---|---|
| `GET` | `/company/benefits` | Listar (suporta `?company_id, ?category, ?active_only, ?search`) |
| `GET` | `/company/benefits/active` | Atalho `active_only=true` |
| `POST` | `/company/benefits` | Criar |
| `PUT` | `/company/benefits/:id` | Atualizar |
| `DELETE` | `/company/benefits/:id?hard_delete=` | Soft (default) ou hard delete |
| `POST` | `/company/benefits/seed-defaults` | Seed inicial (idempotente: skip se já existem) |
| `GET` | `/company/benefits/categories/list` | Enum canônico de categorias |
| `GET/POST` | `/workforce/plans`, `/workforce/headcounts` | Workforce CRUD |
| `POST` | `/workforce/entries/import` | Upload de planilha (preview) |
| `POST` | `/workforce/entries/import/confirm` | Commita preview aprovado (HITL) |
| `GET` | `/jobs?offset=&limit=` | Vagas paginadas (resposta inclui `total_count` + `pagination.has_more`) |

#### Eventos DOM / FE

| Evento | Origem | Listener |
|---|---|---|
| `lia:settings-updated` | `BenefitsListSection` (após mutação) | hooks de settings que invalidam cache |
| `settings-open-tab` | `MinhaEmpresaHub` (atalho "Gerenciar departamentos") | `SettingsShell` (já existia) |
| **`settings-open-subtab`** (novo, J.6) | `MinhaEmpresaHub` (atalho "Gerenciar departamentos") | `UsuariosDepartamentosHub` (pré-seleciona aba `departments`) |
| `workflow:thinking` (legado, pendente) | `UnifiedChat` | sem listener — pendência herdada da PARTE H |

#### IA — intents / tools / capabilities

| Tool / Intent | Status | Notas |
|---|---|---|
| `save_company_benefits` (`_wrap_save_company_benefits`) | canônico (J.2/J.3) | clarification-first, PII mask, FairnessGuard L1, audit log com `source ∈ {chat,spreadsheet,website}`, HITL para `mode=replace`. Constantes exportadas: `CANONICAL_BENEFIT_FIELDS`, `VALID_BENEFIT_VALUE_TYPES`, `BENEFIT_CLARIFICATION_FIELDS`. |
| `actions.configure_benefits` em `capabilities.yaml` | adicionado (J.2) | documenta campos aceitos, regras de clarification, sources e `audit_action`. |
| `_handle_configure_benefits` (`domain.py`) | atualizado (J.2) | forwarda `source`; converte `needs_clarification` em `DomainResponse.clarification_response` com `navigation_hint`. |
| `_handle_analyze_website` fase 1 | atualizado (J.2) | promove benefits `list[str]` → `list[dict{name}]` e expõe `expected_fields` (TIER 3). |
| `import_benefits_from_data` (planilha) | refatorado (J.2) | delega ao wrapper canônico com `source="spreadsheet"`; alias `is_highlight → is_highlighted`; propaga `needs_clarification`. |
| `_wrap_import_workforce_plan` | canônico (J.7) | 3 modos `spreadsheet | paste | text`; gate HITL `approved is True` (booleano real); parser TSV/CSV/`;` com aliases PT/EN; extrator Claude com PII mask para texto livre. |
| `actions.configure_workforce` (`tool_registry_metadata.yaml`) | atualizado (J.7) | forwarda `input_mode`, `raw_text`, `approved`. Clarification preserva "planejamento" — regressão #712. |
| `manage_departments` (intent + handler) | adicionado (J.6) | routing-only; `_handle_manage_departments` retorna `navigation_hint` para `section=usuarios-departamentos, tab=departments`; sem writes. |
| `forecast_hiring_needs` | mantém | só estimativa; defaults documentados (turnover 15%, 45 dias). |
| `create_job` / `update_job` | atualizar | normalizar `benefits` via `normalize_benefits_payload` antes de salvar (J.4). |
| `search_jobs` | atualizado (J.8) | assinatura `(query, filters, offset=0, limit=20)`; resposta inclui `total_count` + `pagination.has_more`. |

Intent `configure_workforce` (onboarding): **não coleta mais** `departamento` no prompt (J.6).

#### Testes adicionados nesta onda (factual, por commit)

| Commit | Arquivo de teste | Camada / Foco |
|---|---|---|
| `3045bdfdd` (J.6) | `lia-agent-system/tests/unit/test_company_settings_actions.py` (criado) | Unit Python — guardrail de paridade após remoção de `configure_departments` do `configure_workforce`. |
| `43981a976` (J.2) | `lia-agent-system/tests/unit/test_company_settings_actions.py` (estendido) | Unit Python — paridade `CompanyBenefit` model × Pydantic × TS × `CANONICAL_BENEFIT_FIELDS`; clarification rules de `value_type`. |
| `843a0d224` (J.7) | `lia-agent-system/tests/unit/test_workforce_plan_hitl.py` (criado) | Unit Python — HITL antes de gravar `PlannedHeadcount`; bloqueio de `mode=replace` sem confirmação. |
| `e03e9c7fa` (J.4) | `lia-agent-system/tests/integration/test_job_vacancy_benefits_jsonb.py` (criado) | Integração — backfill ARRAY → JSONB com match por `company_id`; preservação de metadados. |
| `e03e9c7fa` (J.4) | `plataforma-lia/src/components/job-wizard/__tests__/benefits-merge.test.ts` (criado) | Unit TS — merge de `JobBenefit[]` no wizard preservando estrutura. |
| `182dec756` (J.8) | `lia-agent-system/tests/unit/test_fix20_pagination.py` (criado) | Unit Python — paginação de `GET /jobs` (`page`, `per_page`, `total`, `total_pages`). |

> Demais commits (`66343bef5`, `975d5e0d9`, `ebe39fccb`, `a2913e268`, `c817b80f6`, `241d88f72`, `90833f800`, `68bef95bf`, `311e74269`, `7a5142db5`, `cfe3f51fa`) **não adicionaram arquivos de teste** — são UI/docs/snapshots/restore. Cobertura listada abaixo é considerada lacuna.

#### Testes recomendados (lacunas a cobrir em tasks de follow-up)

| Camada | Cobertura recomendada (não adicionada nesta onda) |
|---|---|
| Unit Python | `test_normalize_benefits_payload` — strings, dicts, `value_type` clamp, descarte de itens sem `name` (helper `app/utils/benefits.py`). |
| Eval IA | Golden de `_wrap_save_company_benefits`: append/replace, Fairness block, PII masking, clarification de `value_type`. |
| E2E FE | `e2e/beneficios-hub.spec` — criar/editar/excluir item; trocar categoria; toggle `is_highlighted`. |
| E2E FE | `e2e/workforce-3-paths.spec` — upload planilha, texto livre, colagem; confirmação HITL antes de gravar. |
| Regressão FE | `e2e/usuarios-departamentos-hub.spec` — confirmar que não regrediu após remoção do bloco em MinhaEmpresaHub (alvo da Task #773). |
| Smoke backend | `python -c "from app.main import app"` no post-merge hook (evita reincidência do incidente J.11). |

#### Pendências e follow-ups conhecidos (NÃO criar tasks duplicadas)

1. **Task #771** — rotação do GitHub PAT em `.git/config` (segredo no remote `wedotalent/replit-sync`).
2. **Task #772** — auditoria final consolidada da onda (cobertura 14 dimensões — feature-audit).
3. **Task #773** — e2e para o fluxo Departamentos pós-remoção do bloco em MinhaEmpresaHub.
4. `isAuthRoute` — testes unitários ainda ausentes (anotado em onda anterior).
5. Guardrail CI: lint customizado proibindo a string `is_highlight` em qualquer arquivo Python (evita ressurgência do bug do `import_tools.py`).
6. Guide em `replit.md`: registrar "JobVacancy.benefits é JSONB estruturado, nunca array de string".

---

> **Fim da PARTE J.** Para o histórico anterior consolidado, ver PARTES A–I acima.
