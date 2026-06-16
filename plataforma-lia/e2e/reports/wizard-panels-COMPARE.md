# Wizard Panels — COMPARE (Audit comparativo)

**Data:** 2026-04-29
**Escopo:** comparação feature-by-feature dos 3 pares de painéis (atual vs novo "Wizard\*"), recomendação canônica e esforço de wiring. Audit complementar ao `wizard-e2e-AUDIT.md`. Nenhum arquivo de produção tocado.

---

## TL;DR

> **Os 3 painéis "novos" NÃO são substitutos drop-in dos atuais. Cada par resolve problemas diferentes.**

- **JD Review:** os dois painéis têm o mesmo prefixo `Review` no nome mas fazem coisas DIFERENTES — `ReviewPanel` é checklist de prontidão pra publicação (no stage `review`); `WizardJDReviewPanel` é HITL gate de comparação raw-vs-enriched (sem stage backend). **Manter os dois, criar stage novo.**
- **WSI:** `WsiQuestionsPanel` é mais rico (frameworks Bloom/Dreyfus/peso, edit/regen/remove por pergunta via event bus); `WizardWSIListPanel` adiciona drag-to-reorder e selectability (mas perde os metadados ricos). **Manter atual + porting do drag.**
- **Calibration:** `CalibrationPanel` está alinhado com backend real (usa tipos do `wizard-types.ts`, dispatchEvents corretos, threshold gate, design tokens LIA); `WizardCalibrationPanel` usa tipos sintéticos (`yearsExp`/`experiences[]`) que não batem com o payload, e usa tokens shadcn genéricos. **Manter atual; cherry-pick criteria toggle/Tezi-table se UX desejar.**
- **Chips contextuais:** `PromptSuggestionsPanel` inteiro é dead code (zero callers), não só `workflowContext`. Esforço maior do que parecia.
- **`missingFields` banner:** não criar componente novo — reusar `AIDisclaimer.inline` ou padrão `bg-status-warning` já presente no `ReviewPanel`.

---

## 1. Feature matrix por par

### JD Review

| Feature | `ReviewPanel` (atual, 90 LoC) | `WizardJDReviewPanel` (novo, 221 LoC) |
|---|---|---|
| **Propósito real** | Checklist de prontidão p/ publicar (`readiness.checks`) | HITL gate de comparação raw-vs-enriched JD |
| Side-by-side raw vs enriched | ❌ não tem JD nenhum | ✅ grid 2 colunas com divisor |
| Diff visual highlighting | ❌ | ✅ heurística line-by-line, novas linhas em `bg-green-50` |
| Quality score badge | ❌ | ✅ `QualityBadge` (3 faixas: ≥80 verde, ≥60 âmbar, <60 vermelho) |
| Fairness warnings list | ❌ | ✅ box âmbar com `AlertTriangle` + lista bullets |
| Botão "Refazer com ajustes" | ❌ (mas tem "Aplicar defaults da empresa") | ✅ input livre + Send + Enter handler |
| Checklist de readiness (jd/questions/seniority/quality/eligibility/salary) | ✅ 7 checks com `CheckCircle`/`XCircle` | ❌ |
| Lista de pendências | ✅ `readiness.missing.join(", ")` em box `bg-status-warning/5` | ❌ |
| Lista de defaults aplicados | ✅ texto pequeno cinza | ❌ |
| Apply defaults button (`window.dispatchEvent("lia:prefill-message")`) | ✅ | ❌ |
| Design tokens vs hardcoded | ✅ tokens LIA: `text-lia-text-*`, `bg-status-success/warning`, `text-wedo-cyan` | ❌ tokens shadcn genéricos: `bg-green-100`, `text-amber-700`, `bg-primary` (hardcoded Tailwind palette) |
| Acessibilidade | parcial — sem aria-labels nos checks | parcial — `aria-label="Enviar ajustes"` no Send; sem `role` no input |
| Linhas de código | 90 | 221 |
| Última modificação (git) | 2026-04-26 (`17031f1dc` Task #840 DS v4.2.1) | 2026-04-28 (`05ccd6fcc` Onda 26-27 Tezi panels) |
| Wirado em `DynamicContextPanel` | ✅ stage `review` | ❌ zero callers |
| Backend payload type | ✅ `ReviewData` de `wizard-types.ts` (`readiness.checks/missing`, `defaults_applied`) | ❌ usa tipo próprio (`rawJD`/`enrichedJD`/`qualityScore`/`fairnessWarnings`) — sem stage do backend que entregue isso |

**Achado:** os dois NÃO são alternativas — são telas conceitualmente diferentes que por azar compartilham "Review" no nome. `WizardJDReviewPanel` representa um gate HITL **adicional** que o backend ainda não emite.

### WSI List

| Feature | `WsiQuestionsPanel` (atual, 229 LoC) | `WizardWSIListPanel` (novo, 268 LoC) |
|---|---|---|
| **Propósito real** | HITL F6: aprovar/editar/regenerar perguntas geradas | Selecionar e reordenar perguntas |
| Lista de perguntas | ✅ cards expansíveis (Chevron) | ✅ rows fixos |
| Drag-to-reorder | ❌ | ✅ `draggable` + handle `⠿` |
| Checkbox de seleção por pergunta | ❌ (todas aprovadas em massa) | ✅ `role="checkbox"` + `aria-checked` |
| Edit inline da pergunta | ✅ via `lia:wizard-edit-question` event | ✅ inline input on-click |
| Regenerar pergunta individual | ✅ via `lia:wizard-regenerate-question` event | ❌ |
| Remover pergunta individual | ✅ com guard de mínimo (compact:7, completo:12) | ❌ |
| Generate more (lote) | ❌ | ✅ botão "Gerar mais" |
| Badge framework (CBI/Bloom/Dreyfus/BigFive) | ✅ 4 cores | ❌ só technical/behavioral |
| Badge tipo (técnica/comportamental) | ✅ | ✅ |
| Badge trait OCEAN | ✅ | ❌ |
| Resposta ideal (expandida) | ✅ | ❌ |
| Skill / Bloom level / Dreyfus level / weight | ✅ tudo no expand | ❌ só competency |
| Header summary (n perguntas, n técnicas, n comportamentais) | ✅ + badge Compacto/Completo | ✅ + badge `${modeLabel}` (compacto N / completo N) |
| Modo mínimo enforce | ✅ desabilita "Remover" no mínimo | ❌ |
| HITL Approval footer | ✅ Regenerar (lote) + Aprovar todas | ✅ Gerar mais + Aceitar selecionadas (N) |
| Design tokens | ✅ tokens LIA | ❌ tokens shadcn (`bg-blue-100`, `text-purple-700`, `bg-primary`) |
| Backend payload type | ✅ `WsiQuestionsData`/`ScreeningQuestion` de `wizard-types.ts` | ❌ tipo próprio `WsiQuestion` (`id`, `text`, `competency`, `type`, `selected`) — não bate com `ScreeningQuestion` |
| Linhas de código | 229 | 268 |
| Última modificação (git) | 2026-04-26 (`17031f1dc` Task #840 DS v4.2.1) | 2026-04-28 (`05ccd6fcc` Onda 26-27) |
| Wirado em `DynamicContextPanel` | ✅ stage `wsi_questions` | ❌ |

**Achado:** `WsiQuestions` é semanticamente alinhado ao backend; `WizardWSI` traz drag-to-reorder e seleção granular, mas perde Bloom/Dreyfus/weight/ideal_answer. Drag-to-reorder é genuinamente novo.

### Calibration

| Feature | `CalibrationPanel` (atual, 256 LoC) | `WizardCalibrationPanel` (novo, 252 LoC) |
|---|---|---|
| **Propósito real** | Aprovar mín. 3 perfis para calibrar busca | Tezi-style toggle entre critérios e candidatos |
| Threshold gate (mín 3 aprovações) | ✅ `canAdvance = approvedCount >= threshold` | ❌ "Finalizar" sempre habilitado |
| Progress bar X/threshold | ✅ animada, troca cor quando completa | ❌ |
| Pool counter ("X compatíveis") | ✅ no header, com `Users` icon | ✅ no header + footer ("Pool: X+") |
| Must-haves section | ✅ flex-wrap chips pretos | ✅ tabela full-width com ícones, valores, qualidade (●) |
| Sourcing constraints section | ✅ flex-wrap chips outline | ✅ tabela com mesmo estilo |
| Toggle critérios on/off | ❌ (sempre visível) | ✅ ChevronUp/Down + 2 modos |
| Quality dot por criterion (good/warning/poor) | ❌ | ✅ `qualityColor()` |
| "+ Add" inline por criterion | ❌ | ✅ |
| CandidateCard rico (avatar/título/empresa/match%/match_criteria pills) | ✅ | ❌ apenas anos-exp + location + experiences[] + criteriaMatched/total |
| Match score por candidato (%) | ✅ `Math.round(c.match_score * 100)%` | ❌ |
| Match criteria pills (met/not met com cores) | ✅ por candidato | ❌ |
| Avatar real (foto) vs placeholder | ❌ só placeholder | ✅ `<img src={candidate.avatar}>` com fallback |
| Approve/Reject por candidato | ✅ ThumbsUp/Down embedded no card | ✅ 👎/👍 emoji buttons no footer do card |
| Visual decided state (opacity-70) | ✅ + ícone CheckCircle/XCircle | ❌ |
| Botão "Calibracao completa" / "Faltam X perfis" | ✅ texto dinâmico, disabled até atingir threshold | ❌ "Finalizar Calibração" sempre clicável |
| Design tokens | ✅ tokens LIA (`text-lia-*`, `bg-status-*`, `bg-wedo-cyan`) | ❌ tokens shadcn (`text-foreground`, `bg-primary`, `text-green-600` hardcoded) |
| Acessibilidade | parcial | parcial — `aria-label="Aprovar/Rejeitar ${name}"` ✅ |
| Backend payload type | ✅ `CalibrationData & {pool_count, criteria}` extends `wizard-types.ts` | ❌ tipo próprio `CandidateProfile` (`yearsExp`/`experiences[]`/`criteriaMatched`) — backend retorna `CalibrationCandidate` (`current_title`/`current_company`/`match_score`/`match_criteria`) |
| dispatchEvent (event bus) | ✅ `lia:wizard-edit-question` com `type: "calibration_approve/reject"` | ❌ callback prop `onFeedback(id, approved)` — sem wiring |
| Linhas de código | 256 | 252 |
| Última modificação (git) | 2026-04-26 (`2528738cf` A11y Focus Trap + WCAG Contrast) | 2026-04-28 (`05ccd6fcc` Onda 26-27 Tezi) |
| Wirado em `DynamicContextPanel` | ✅ stage `calibration` | ❌ |

**Achado:** `CalibrationPanel` está pronto pra produção e alinhado com payload real do backend. `WizardCalibration` parece ter sido construído contra um mock UX (Tezi-style) sem olhar o que o backend manda.

---

## 2. Recomendação canônica por par

### JD Review → **manter ambos, criar stage novo**

Não é "manter atual + descartar novo" nem "substituir". O conflito é nominal — os dois resolvem problemas diferentes:

- `ReviewPanel` continua sendo o painel do stage `review` (checklist de publicação). Não tocar.
- `WizardJDReviewPanel` precisa de um **stage novo** no orchestrator (sugestão: `jd_review` ou `enrichment_review`) que emita `wizard_step_response` com `{ rawJD, enrichedJD, qualityScore, fairnessWarnings }`. Daí registrar o painel em `DynamicContextPanel.tsx:11` ao lado dos outros lazy imports.
- Antes de wirar, decidir se esse gate HITL é desejável no flow atual. Se não, **deletar** o `WizardJDReviewPanel` (canonical-fix) — ele não é refactor do `ReviewPanel`, é uma feature distinta que ficou pela metade.

### WSI List → **manter atual + porting de drag-to-reorder**

`WsiQuestionsPanel` é claramente o canônico:
- Tem suporte a Bloom/Dreyfus/weight/ideal_answer (dados reais que o backend gera no F6).
- Frameworks coloridos (CBI/Bloom/Dreyfus/BigFive) mapeam o que o agent retorna.
- Edit/regen/remove individuais já estão wirados via event bus.
- Tokens DS LIA, alinhado com Task #840.

`WizardWSIListPanel` traz uma feature genuinamente nova: **drag-to-reorder + checkbox de seleção**. Recomendação: **port** essas duas features pro `WsiQuestionsPanel` (adicionar prop opcional `reorderable` + checkbox no header de cada card). Daí deletar `WizardWSIListPanel`. Esforço estimado: 60-90min.

Se a feature "selecionar subconjunto" não estiver no roadmap, descartar `WizardWSIListPanel` direto.

### Calibration → **manter atual; cherry-pick criteria toggle (opcional)**

`CalibrationPanel` está pronto:
- Threshold gate de 3 aprovações (regra de negócio explícita).
- Progress bar visual.
- Tipos batem com `CalibrationData`/`CalibrationCandidate` do backend.
- Match score + match_criteria pills (dados reais).
- Tokens DS LIA.
- A11y Focus Trap recém-aplicado (commit `2528738cf`).

`WizardCalibrationPanel` é interessante visualmente (Tezi-style com tabela de critérios + toggle), mas:
- Tipos não batem (backend não manda `yearsExp`/`experiences[]`/`criteriaMatched`).
- Sem threshold gate (regra de negócio quebrada).
- `onFeedback` é callback prop, não dispatchEvent — não wira no chat.
- Tokens shadcn (regressão DS).

Se UX quiser o toggle "Ver critérios / Ocultar critérios" e a tabela full-width de must-haves: **port** só essa parte pro `CalibrationPanel`. Esforço estimado: 30-45min. Daí deletar `WizardCalibrationPanel`.

---

## 3. Esforço de wiring (cenário "substituir atual pelo novo")

> **Nenhum dos 3 pares justifica substituição completa.** Esta seção é "se mesmo assim alguém quiser substituir".

### Arquivos a editar (substituição completa hipotética)

`src/components/unified-chat/wizard/DynamicContextPanel.tsx` linhas 11-47:

```tsx
// Trocar:
const ReviewPanel = lazy(() =>
  import("./panels/ReviewPanel").then((m) => ({ default: m.ReviewPanel }))
)
// Por:
const ReviewPanel = lazy(() =>
  import("./panels/WizardJDReviewPanel").then((m) => ({ default: m.WizardJDReviewPanel }))
)
// (idem para WsiQuestionsPanel → WizardWSIListPanel, CalibrationPanel → WizardCalibrationPanel)
```

E adaptar a forma como `data` é passada (linhas mais abaixo no `<Suspense>`), porque os contratos de props são totalmente diferentes:
- Atual: `<ReviewPanel data={...} onUpdate={...} />` (genérico).
- Novo: `<WizardJDReviewPanel rawJD={...} enrichedJD={...} qualityScore={...} fairnessWarnings={...} onAccept={...} onRequestChanges={...} />` (props específicas).

### Riscos de regressão

1. **Tipos do backend não batem** (descrito acima por par). Substituição quebra renderização porque os payloads não conseguem ser narrowed pros novos shapes.
2. **Specs em `e2e/tests/job-creation/`** NÃO testam diretamente esses 3 painéis (testam o fluxo modal-driven, ver Seção 3 do `wizard-e2e-AUDIT.md`). Risco de regressão E2E é **baixo nessa pasta** — mas as specs de chat-driven do wizard (que ainda nem existem) viriam contra esses painéis.
3. **Testes unitários:** `__tests__/useWizardFlow.test.ts` referencia `CalibrationPanel`/`ReviewPanel`/`WsiQuestionsPanel` por nome. Substituir os nomes quebraria os imports.
4. **dispatchEvent listeners:** quem escuta `lia:wizard-edit-question`, `lia:wizard-regenerate-question`, `lia:wizard-remove-question`, `lia:prefill-message` perderia os emissores. Os Wizard\*Panel novos NÃO emitem nenhum desses — usam callback props. Backend não recebe mais ações.
5. **Design tokens regressão:** os 3 novos usam `bg-primary`/`bg-green-100`/`text-foreground` (shadcn defaults), regredindo Task #840 que migrou tudo para tokens LIA (`text-lia-text-primary` etc.).

### Estimativa

- **Substituição completa dos 3 painéis:** **6-10 horas** (rebind de props, alinhar tipos com payloads reais, retokenizar pra DS v4.2.1, atualizar `useWizardFlow.test.ts`, validar A11y Focus Trap, adaptar dispatchEvent → callbacks no orchestrator) + risco real de regressão. **Não recomendado.**
- **Port das features novas (drag-reorder pro WsiQuestions + criteria toggle pro Calibration):** **1.5-2 horas** total. **Recomendado se UX quiser as features.**
- **Wirar `WizardJDReviewPanel` em stage novo (caminho B):** **3-5 horas** (criar stage no orchestrator backend, payload, teste agent, integrar `DynamicContextPanel`, fluxo HITL). Decisão de produto se vale.
- **Deletar os 3 Wizard\* (canonical-fix, caminho A):** **15min** + 1 commit. **Recomendado se as features não vão ser portadas E o stage novo não vai ser criado.**

---

## 4. Chips contextuais (`workflowContext`) e missing_fields banner

### Chips contextuais — `PromptSuggestionsPanel`

**Achado novo (mais grave que o do AUDIT inicial):** `PromptSuggestionsPanel` **inteiro** é dead code, não só a parte do `workflowContext`. `rg -n 'PromptSuggestionsPanel' src/` retorna apenas o próprio arquivo — zero `<PromptSuggestionsPanel ... />` em qualquer outro componente.

Onde renderizado hoje: **lugar nenhum.** O empty state do chat (`UnifiedChatEmptyState`) provavelmente tem suas próprias suggestions hardcoded, não usa este componente.

**Esforço pra wirar:**
1. Decidir onde montar (sugestão: dentro de `UnifiedChat.tsx` acima do `UnifiedChatInput`, condicional ao número de mensagens ou ao stage do wizard).
2. Passar `workflowContext` derivado de `wizardStage` ou de evento backend (ex.: após `wizard_stage="done"` setar `workflowContext="vacancy_published"`).
3. Wirar `onContextPromptClick={(prompt) => sendChatMessage(prompt)}` (já existe `sendChatMessage` em `UnifiedChat.tsx`).

Esforço: **45-60min** + decisão de UX (em quais momentos os chips aparecem). É barato porque o componente já existe completo, só falta o caller.

**Alternativa "barata":** se a única intenção é cenário G ("Iniciar triagem após publicar vaga"), bastaria adicionar uma única ação visível na confirmação de publicação (ex.: card final do `wizard_published_job` metadata, que já existe em `UnifiedMessageList.tsx:303` como `wizard-plan-card`). Esforço: 15min, sem precisar wirar `PromptSuggestionsPanel`.

### `missingFields` banner

**Não existe componente reusável dedicado**, mas existem 2 padrões já no DS LIA que cobrem o caso:

1. **`AIDisclaimer.inline`** (`src/components/ui/ai-disclaimer.tsx`) — variant que renderiza:
   ```tsx
   <div className="flex items-start gap-2 p-2 bg-status-warning/10 border border-status-warning/30 rounded-md text-xs text-status-warning">
     <Brain className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-wedo-cyan" />
     <span>{disclaimerText}</span>
   </div>
   ```
   Já tokenizado, basta passar texto custom. Reusável diretamente.

2. **Padrão inline do próprio `ReviewPanel.tsx:64-68`** — `<div className="p-2.5 rounded-md bg-status-warning/5 border border-status-warning/20"><p className="text-xs text-status-warning font-medium">Pendencias: {readiness.missing.join(", ")}</p></div>`. Já existe pra exibir pendencias (mesma natureza do `missing_fields`).

**Recomendação:** **NÃO criar componente novo.** Wirar diretamente em `UnifiedChat.tsx`:
```tsx
{missingFields && missingFields.length > 0 && (
  <div className="p-2.5 mx-4 rounded-md bg-status-warning/5 border border-status-warning/20">
    <p className="text-xs text-status-warning font-medium">
      ⚠️ Campos obrigatórios: {missingFields.join(", ")}
    </p>
  </div>
)}
```
Onde `missingFields` vem de `useWizardIntegration()` que já está disponível no escopo do `UnifiedChat`.

Esforço: **10-15min** (1 PR pequeno + 1 testid `missing-fields-warning` pra capturar no E2E).

**Alternativa shadcn `Alert`:** projeto **NÃO tem** `Alert` do shadcn instalado — só `AlertDialog` (modal). Adicionar `alert.tsx` do shadcn seria overhead desnecessário pra um caso simples.

---

## Conclusão executiva

**Caminho recomendado (mínima fricção, máxima clareza):**

1. **Calibration:** manter `CalibrationPanel`. Cherry-pick o toggle "Ver critérios / Ocultar" se UX quiser (~30min). Deletar `WizardCalibrationPanel`.
2. **WSI:** manter `WsiQuestionsPanel`. Port drag-to-reorder + checkbox de seleção se roadmap pede (~90min). Deletar `WizardWSIListPanel`.
3. **JD Review:** decidir produto. Se gate HITL pós-enriquecimento for desejável → criar stage novo no orchestrator + wirar `WizardJDReviewPanel` (~5h). Se não → deletar `WizardJDReviewPanel`.
4. **Chips:** wirar `PromptSuggestionsPanel` em `UnifiedChat` (~60min) OU adicionar ação direta no card de publicação (~15min, cobre só cenário G).
5. **missingFields banner:** wirar inline padrão `bg-status-warning` em `UnifiedChat` lendo do `useWizardIntegration` (~15min).

**Total esforço caminho recomendado:** ~3-7h dependendo da decisão sobre o JD Review e os chips. Daí abrir Fase 2 do audit E2E pra escrever specs A-G.

**Caminho rápido (descarte sem feature parity):** deletar os 3 Wizard\*, deletar branch `if (workflowContext)` do PromptSuggestionsPanel + 70 LoC mortas, deletar state `missingFields` órfão do `useWizardIntegration`. ~30min, fecha 4 BLOCKERS por remoção. Cenários A-D, F continuam testáveis contra os painéis atuais; E e G ficam descobertos.

---

**Tamanho:** ~245 linhas (target ~250 ✓). Working tree dirty: apenas `plataforma-lia/e2e/reports/wizard-panels-COMPARE.md`. Nenhum arquivo de produção tocado.
