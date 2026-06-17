# Developer Handoff — UX Redesign Competitivo (Sprints UX-1 a UX-7)

> **Commit:** `5140997a` · **Branch:** `develop` · **Data:** 2026-04-19
> **Contexto:** Análise competitiva da Tezi (concorrente adquirido por PE para healthcare)
> revelou 7 pilares de UX que o WeDo tinha infraestrutura para entregar mas não ativou.
> Este handoff documenta todos os arquivos, interfaces, eventos e integrações implementados.

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

