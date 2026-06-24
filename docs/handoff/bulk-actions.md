# Handoff — Bulk Actions: Ações em Lote no Funil de Talentos

> **Objetivo deste documento:** permitir que um time de devs **replique do zero** toda a barra de bulk actions do Funil de Talentos — da seleção de candidatos ao resultado final de cada operação, passando pelos guardrails de segurança (FairnessGuard, saturation guard, HITL gate, LGPD consent).
>
> **Fora de escopo:** ações de lote em vagas (JobsListContent usa o mesmo `BulkActionsBar` UI com `entityLabel="vaga"`, mas com actions diferentes — documentar separadamente); editor de listas (`CandidateLists`); detalhes do pipeline WSI além do ponto de entrada.
>
> **Como ler:** Parte A = arquitetura e fluxos end-to-end. Parte B = cada ação documentada individualmente com seus guardrails. Parte C = referência (API, schemas, estado frontend, checklist, glossário, gaps).
>
> **Stack:** Next.js 15 (App Router) · FastAPI (porta 8001) · PostgreSQL · Redis · Zustand · sonner (toasts)

---

## Índice

**Parte A — Arquitetura e Fluxos**
1. [Visão geral & arquitetura](#1-visão-geral--arquitetura)
2. [Dois componentes, uma confusão frequente](#2-dois-componentes-uma-confusão-frequente)
3. [Anatomia da barra de bulk actions](#3-anatomia-da-barra-de-bulk-actions)
4. [Seleção de candidatos: como funciona](#4-seleção-de-candidatos-como-funciona)
5. [Fluxo padrão de uma operação bulk](#5-fluxo-padrão-de-uma-operação-bulk)

**Parte B — As Ações**
6. [Atualizar Status](#6-atualizar-status)
7. [Enviar E-mail em Massa](#7-enviar-e-mail-em-massa)
8. [Atribuir à Vaga](#8-atribuir-à-vaga)
9. [Iniciar Triagem WSI](#9-iniciar-triagem-wsi)
10. [Exportar (CSV/XLSX)](#10-exportar-csvxlsx)
11. [Compartilhar Seleção](#11-compartilhar-seleção)
12. [Adicionar à Lista](#12-adicionar-à-lista)
13. [Excluir Candidatos](#13-excluir-candidatos)
14. [Ações de conveniência (Favoritar, Ocultar, Revelar Contatos, Salvar na Base)](#14-ações-de-conveniência-favoritar-ocultar-revelar-contatos-salvar-na-base)

**Parte C — Referência**
15. [Contratos de API](#15-contratos-de-api)
16. [Schema drift FE ↔ BE](#16-schema-drift-fe--be)
17. [Componentes & estado (frontend)](#17-componentes--estado-frontend)
18. [HITL gate nas bulk actions](#18-hitl-gate-nas-bulk-actions)
19. [FairnessGuard nas bulk actions](#19-fairnessguard-nas-bulk-actions)
20. [Saturation guard (Iniciar Triagem)](#20-saturation-guard-iniciar-triagem)
21. [Config & variáveis de ambiente](#21-config--variáveis-de-ambiente)
22. [📋 Quadro-resumo de regras de negócio](#22--quadro-resumo-de-regras-de-negócio)
23. [Checklist de replicação](#23-checklist-de-replicação)
24. [Glossário](#24-glossário)
25. [Gaps & pontos de atenção](#25-gaps--pontos-de-atenção)

---

# PARTE A — ARQUITETURA E FLUXOS

## 1. Visão geral & arquitetura

As bulk actions permitem que o recrutador execute uma operação em múltiplos candidatos de uma vez. O fluxo sempre passa pelo proxy Next.js antes de chegar ao FastAPI.

```
Recrutador seleciona N candidatos
        │
        ▼
BulkActionsBar (UI)  ←  o recrutador clica em uma ação
        │
        ▼  (modalconfirmação ou seletor inline)
bulk-api.ts  →  /api/backend-proxy/candidates/bulk/<ação>  [Next.js App Router]
        │
        ▼  (valida body via Zod schema, repassa Authorization header)
FastAPI  /api/v1/candidates/bulk/<ação>  [porta 8001]
        │
        ├── require_company_id (JWT) ← company_id NUNCA do payload
        ├── FairnessGuard.check() (se tiver campo de texto livre)
        ├── Saturation guard (apenas start-screening)
        ├── BulkActionsRepository (session-in-constructor)
        │     └── operação por candidato em loop
        ├── audit_service.log_decision (por candidato, não-bloqueante)
        └── BulkOperationResult {total, successful, failed, errors[], processed_ids[]}
        │
        ▼
Progress modal (FE) → toast final (success/partial)
```

**Princípio de transação:** cada operação itera sobre os candidatos individualmente. Se um candidato falha (não encontrado, inativo, sem consent), ele vai para `errors[]` mas os demais prosseguem. O `repo.commit()` é único, no final — se o loop todo explodir, há `repo.rollback()`.

**Limite físico:** `MAX_BULK_ITEMS = 100` (`bulk_actions.py:47`). Requests com mais de 100 IDs recebem HTTP 422 antes de tocar o banco.

## 2. Dois componentes, uma confusão frequente

⚠️ **"O erro mais comum é confundir os dois `BulkActionsBar` do projeto."**

Existem **dois** componentes com esse nome. Eles fazem coisas diferentes:

| Aspecto | `src/components/ui/bulk-actions-bar.tsx` | `src/components/bulk-actions-bar.tsx` |
|---|---|---|
| **Quem usa** | `CandidateSearchResultsView`, `KanbanPageContent`, `JobsListContent` | **Ninguém usa diretamente** (legacy/standalone) |
| **Natureza** | Componente **genérico/headless** — recebe `actions: BulkActionItem[]` como prop | Componente **self-contained** — inclui handlers, modais e chamadas de API internamente |
| **Exportação** | Named export: `export const BulkActionsBar` + `export type BulkActionType` | Default export: `export default BulkActionsBar` |
| **Path** | `@/components/ui/bulk-actions-bar` | `@/components/bulk-actions-bar` |
| **Estado** | Stateless (exceto loading por action via `action.loading`) | Stateful — gerencia `progressModal`, `confirmDeleteModal`, `assignJobModal`, etc. |

**Qual é o canônico?** O componente em `ui/` é o canônico — é ele que os três consumers ativos importam. O componente em `components/` (raiz) é um componente legacy/standalone que não é montado em nenhuma página ativa.

## 3. Anatomia da barra de bulk actions

O componente `BulkActionsBar` em `src/components/ui/bulk-actions-bar.tsx` aceita estas props:

```typescript
interface BulkActionsBarProps {
  selectedCount: number          // obrigatório — oculta o bar se === 0
  totalCount?: number            // opcional — exibe "X de Y"
  entityLabel?: string           // 'candidato' | 'vaga' | qualquer string
  entityIcon?: React.ReactNode   // ícone do tipo de entidade
  showSelectAll?: boolean        // mostra checkbox "Selecionar todos"
  isAllSelected?: boolean        // estado do checkbox "Selecionar todos"
  onSelectAll?: () => void       // callback do checkbox
  onDeselectAll: () => void      // obrigatório — botão X
  actions: BulkActionItem[]      // lista de ações renderizadas como botões
  layout?: 'inline' | 'fixed'   // 'inline' = flutuante dentro da página; 'fixed' = sticky top-0
  className?: string
}
```

O componente se **auto-oculta** (`if (selectedCount === 0) return null`) — não precisa de renderização condicional externa.

Cada item em `actions` segue:

```typescript
interface BulkActionItem {
  id: string                   // identificador único
  label: string                // texto do botão
  icon: React.ReactNode        // ícone lucide
  onClick: () => void          // callback
  variant?: 'default' | 'destructive'  // 'destructive' = vermelho
  disabled?: boolean           // desabilita o botão
  loading?: boolean            // mostra spinner em lugar do ícone
  loadingLabel?: string        // texto enquanto loading=true
  hidden?: boolean             // remove o botão da lista visível
}
```

**Layout `fixed`** (`KanbanPageContent`): posicionado `fixed top-0 left-0 right-0 z-50`, escorrega da parte superior com `animate-in slide-in-from-top`. Usado quando a barra precisar flutuar sobre o conteúdo.

**Layout `inline`** (`CandidateSearchResultsView`, `JobsListContent`): renderizado no fluxo normal da página, estilo card com borda sutil.

## 4. Seleção de candidatos: como funciona

A seleção é gerenciada localmente em cada consumer com `useState<Set<string>>`. Não há store global de seleção — cada página tem seu próprio `selectedCandidates`.

### No Funil (CandidateSearchResultsView)

- Estado: `selectedCandidatesForBatch: Set<string>` — gerenciado no componente pai do funil
- Seleção individual: checkbox por linha na tabela de resultados
- Seleção total: via `SearchControlsBar` (botão "Selecionar todos")
- `selectedCandidatesForBatch.size` → `BulkActionsBar.selectedCount`
- IDs passados: `Array.from(selectedCandidatesForBatch)` → campos `candidate_ids` nas requests

### No Kanban (KanbanPageContent)

- Estado: `selectedCandidates: Set<string>` (via `useKanbanPageCore`)
- Controle via `showSelectAll` + `isAllSelected` + `onSelectAll` com toggle: se `selectedCandidates.size === allTableCandidates.length` → desseleciona tudo, senão → seleciona tudo
- `allTableCandidates` é a lista flat de todos os candidatos do kanban visível

### Na Lista de Vagas (JobsListContent)

- Usa o mesmo padrão do Funil, mas `entityLabel="vaga"` — as ações são diferentes (publish, toggle_status, duplicate, assign_recruiter, etc.) — **não são bulk actions de candidatos**

## 5. Fluxo padrão de uma operação bulk

A maioria das ações segue este padrão de UX:

```
1. Recrutador seleciona candidatos
2. Clica no botão da ação no BulkActionsBar
3. [AÇÕES COM SELETOR] Modal de seleção abre (vaga, template de email)
   [AÇÕES DESTRUTIVAS] AlertDialog de confirmação abre (excluir)
   [AÇÕES DIRETAS] Nenhum modal — executa direto (status, exportar)
4. Progress modal abre enquanto operação roda:
   - setProgressValue(10)  ← inicia
   - ... operação async ...
   - setProgressValue(100) ← conclui
5. operationResult populado:
   - failed === 0: toast.success + fecha modal em 1.5s + onActionComplete()
   - failed > 0: toast.error "Operação parcial" + modal fica aberto com lista de erros (até 5 exibidos)
6. onClearSelection() chamado em caso de sucesso
```

O `onActionComplete()` é um callback do consumer — tipicamente força reload/refetch dos dados.

---

# PARTE B — AS AÇÕES

## 6. Atualizar Status

**Onde:** Funil (via `useKanbanBulkActions`) e Kanban.
**Rota:** `POST /api/backend-proxy/candidates/bulk/update-status` → `POST /api/v1/candidates/bulk/update-status`
**Auth:** `get_current_user` (qualquer usuário autenticado)

**Statuses válidos** (`bulk_actions.py:49`):
```python
VALID_CANDIDATE_STATUSES = ["new", "screening", "interview", "offer", "hired", "rejected"]
```

**Fluxo backend (bulk_actions.py:204):**
1. Para cada `candidate_id` no request:
   - Busca candidato pelo UUID (`repo.get_candidate_by_id`)
   - Verifica `candidate.is_active` — inativo → erro por candidato
   - Atualiza `candidate.status = new_status` + `updated_at` + `last_activity_at`
   - Chama `audit_service.log_decision` (não-bloqueante — falha é logada, não propaga)
2. `repo.commit()` único ao final

**Mapeamento de `decision_type` para auditoria** (`bulk_actions.py:27`):
```python
_DECISION_TYPE_MAP = {
    'rejected': 'reject_candidate',
    'hired': 'approve_candidate',
    'screening': 'move_stage',
    'interview': 'move_stage',
    'offer': 'move_stage',
    'new': 'move_stage',
}
```

**No Kanban:** após sucesso, `setCandidatesData` reorganiza as colunas localmente (sem refetch) — move candidatos do estágio antigo para o novo no estado Zustand. `bulk_actions.py` retorna `processed_ids[]` para identificar os sucessos.

📋 **Regras de negócio:**
- Candidato inativo não é atualizado (erro silencioso por item, não falha global)
- Status `rejected` e `hired` geram `decision_type` específicos na auditoria (mais rastreáveis que `move_stage`)
- Sem validação de transição de status — qualquer status → qualquer status é permitido

⚠️ **"O erro mais comum é achar que a auditoria bloqueia a operação se falhar."** O try/except em torno do `audit_service.log_decision` é intencional — auditoria é não-bloqueante. Falha de auditoria só aparece em log DEBUG.

## 7. Enviar E-mail em Massa

**Onde:** Funil (`CandidateSearchResultsView`) e Kanban (`useKanbanBulkActions`).
**Rota:** `POST /api/backend-proxy/candidates/bulk/send-email` → `POST /api/v1/candidates/bulk/send-email`
**Auth:** `get_current_user`

**Fluxo FE (bulk-actions-bar.tsx legacy / CandidateSearchResultsView):**
1. Clique em "Enviar Email" → abre `Dialog` com `<Select>` de templates
2. Recrutador escolhe um template (`selectedTemplateId`)
3. Clica "Enviar Emails" → `handleSendEmail()` → `liaApi.bulkSendEmail({ candidate_ids, template_id })`

**No Kanban:** usa `useKanbanBulkActions.handleBulkActionExecute` com `data.actionType === 'send_message'`. O `template_id` passado é `data.message || 'default-template'` — atenção: nenhum seletor de template é apresentado no Kanban, o ID é o payload de mensagem bruto.

**Fluxo backend (bulk_actions.py:431):**
1. Busca e valida template (`repo.get_email_template_by_id`)
   - template não encontrado → HTTP 404
   - `template.is_active === false` → HTTP 400
2. Para cada candidato:
   - Verifica `candidate.is_active` — inativo → erro
   - Verifica **`candidate.communication_consent`** — sem consent → erro (não pula silenciosamente, registra em `errors[]`)
   - Monta `variables = { candidate_name, candidate_email, current_title, current_company }` + `custom_variables` do request
   - Chama `email_svc.send_email(db, template_id, recipient_email, variables, candidate_id, send_immediately=True)`
   - Atualiza `candidate.last_contacted_at` + `last_activity_at`
3. `repo.commit()` único ao final

📋 **Regras de negócio:**
- **LGPD consent obrigatório:** candidato sem `communication_consent=True` recebe erro individual — não é enviado. Isso é uma verificação hard no backend, não pode ser bypassed pelo FE.
- Template inativo bloqueia **toda** a operação antes do loop — não é por candidato.
- `custom_variables` sobrescrevem os defaults (nome, email, título, empresa) se as keys baterem.

⚠️ **"O erro mais comum é enviar um `template_id` inválido ou de template inativo."** O backend responde HTTP 400/404 antes de processar qualquer candidato — o FE receberá erro genérico via `throw new Error(error.detail || ...)`.

## 8. Atribuir à Vaga

**Onde:** Funil e Kanban.
**Rota:** `POST /api/backend-proxy/candidates/bulk/assign-job` → `POST /api/v1/candidates/bulk/assign-job`
**Auth:** `get_current_user`

**Request schema:**
```typescript
// FE (bulk.types.ts)
interface BulkAssignJobRequest {
  candidate_ids: string[]
  job_id: string            // ← FE usa "job_id"
}

// BE (bulk_actions.py:134)
class BulkAssignJobRequest(WeDoBaseModel):
  candidate_ids: list[str]
  job_vacancy_id: str       // ← BE usa "job_vacancy_id"
  notes: str | None = None
```

⚠️ **"O erro mais comum é não perceber o drift de nome do campo: FE envia `job_id`, BE lê `job_vacancy_id`."** O proxy Next.js em `/api/backend-proxy/candidates/bulk/assign-job/route.ts` valida via `bulkAssignJobSchema` (Zod) e repassa o body. O schema Zod (`candidate.schema.ts:36`) usa `job_vacancy_id` — o FE precisaria alinhar com esse campo ou o proxy faz o mapeamento.

**Fluxo backend (bulk_actions.py:301):**
1. **FairnessGuard** em `request.notes` (se presente) — `_fairness_guard.check(notes)` → HTTP 422 se bloqueado (antes de qualquer DB call)
2. Valida job vacancy (`repo.get_job_vacancy_by_id`) → HTTP 404 se não existe
3. Para cada candidato:
   - Verifica `is_active`
   - Lê `candidate.additional_data["job_assignments"]` (lista JSONB)
   - Adiciona entrada se `job_vacancy_id` não está já presente (dedup)
   - **P0-1 (2026-06-05):** cria link canônico em `VacancyCandidate` se não existir — com `source="manual_assign"`, `stage="sourcing"`, `status="sourced"`, `company_id=company_id` do JWT

📋 **Regras de negócio:**
- **Idempotência:** segundo assign do mesmo candidato à mesma vaga não cria duplicata no `job_assignments` JSONB. Mas também **não atualiza** a entrada existente — é skip silencioso.
- **VacancyCandidate canônico:** antes da correção P0-1, o assign só escrevia no JSONB inerte. Agora escreve na tabela `vacancy_candidates` que o kanban e a contagem de candidatos da vaga leem. Esse é o único write que realmente faz o candidato aparecer na vaga.
- **FairnessGuard em notes:** notas discriminatórias (gênero, raça, etc.) bloqueiam **toda** a operação antes do loop — HTTP 422 com `error: "fairness_blocked"`.
- **company_id** do `VacancyCandidate` vem do JWT, não do payload.

## 9. Iniciar Triagem WSI

**Onde:** Funil (`CandidateSearchResultsView`) e Kanban.
**Rota:** `POST /api/backend-proxy/candidates/bulk/start-screening` → `POST /api/v1/candidates/bulk/start-screening`
**Auth:** `get_current_user`

**Request:**
```typescript
interface BulkStartScreeningRequest {
  candidate_ids: string[]
  screening_type?: string      // 'text' | 'voice' — FE não envia (undefined)
}
```
O backend default é `"text"` (`bulk_actions.py:168`). O FE no componente legacy (`bulk-actions-bar.tsx:219`) não envia `screening_type`.

**Fluxo backend (bulk_actions.py:550):**
1. Valida job vacancy (`job_vacancy_id` **obrigatório no BE** — mas o FE não envia!) → ver Gap §25
2. **Saturation guard** (se `override_saturation=False`, que é o default):
   - `_check_vacancy_saturation(repo, job_vacancy)` verifica `vacancy_candidates` por canal (organic vs sourcing)
   - Thresholds: `governance_rules.threshold_web` ou `company.additional_data.saturation_settings.threshold_web` ou default 20
   - Saturado → HTTP 409 com `error: "saturation_limit_reached"` + counts/thresholds para diagnóstico
   - `saturation_disabled_until` (ISO datetime em `governance_rules`) → bypass temporário
3. Para cada candidato:
   - Verifica `is_active`
   - Adiciona entrada em `candidate.additional_data["screening_sessions"]` (JSONB) com `session_id` novo UUID, `status: "pending"`, `screening_type`
   - Se `candidate.status === "new"` → atualiza para `"screening"` automaticamente

📋 **Regras de negócio:**
- **Saturation guard é fail-closed:** pipeline saturado bloqueia o bulk inteiro, não candidato por candidato. `override_saturation=True` deve ser enviado explicitamente pelo recrutador (UX ainda não exposta no FE padrão).
- **Screening session é JSONB:** a sessão criada é um blob em `additional_data` — não é a `TriagemSession` canônica do `TriagemSessionService`. É um marcador de "triagem pendente" que o serviço canônico deve ler para iniciar. A conexão entre esse JSONB e o fluxo real de triagem não está wired neste endpoint.
- Status auto-promovido: `new → screening` se o status atual for `new`. Outros status não são modificados.

Ver §20 para detalhes do saturation guard.

## 10. Exportar (CSV/XLSX)

**Onde:** Funil (via legacy `bulk-actions-bar.tsx`) e tecnicamente disponível em qualquer consumer.
**Rota:** `POST /api/backend-proxy/candidates/bulk/export` → `POST /api/v1/candidates/bulk/export`
**Auth:** `require_admin_or_recruiter` (mais restritivo que os demais — exige role específica)

**Request:**
```typescript
interface BulkExportRequest {
  candidate_ids: string[]
  format: 'csv' | 'xlsx'
  fields?: string[]      // quais campos incluir; null = todos
}
```

**Resposta:** não é JSON — é `StreamingResponse` com `Content-Disposition: attachment; filename=...`.

**Campos exportados (todos, se `fields` null):**
`id, name, email, phone, linkedin_url, current_title, current_company, seniority_level, years_of_experience, technical_skills (join), soft_skills (join), location_city, location_state, location_country, is_remote, desired_salary_min, desired_salary_max, salary_currency, work_model_preference, source, lia_score, status, tags (join), created_at, updated_at`

**Fallback XLSX→CSV:** se `openpyxl` não estiver instalado, o backend faz fallback para CSV com header `X-Format-Fallback`. O FE não trata esse header — o usuário recebe CSV mesmo pedindo XLSX sem aviso visual.

**Fluxo FE para download (bulk-actions-bar.tsx:243):**
```javascript
const result = await liaApi.bulkExport({ candidate_ids, format })
if (result instanceof Blob) {
  const url = window.URL.createObjectURL(result)
  const a = document.createElement('a')
  a.href = url
  a.download = `candidatos_${data}.${format}`
  document.body.appendChild(a); a.click()
  window.URL.revokeObjectURL(url); document.body.removeChild(a)
}
```

O `bulk-api.ts:bulkExport` detecta o content-type para decidir se retorna `Blob` ou JSON.

**Headers de diagnóstico:**
- `X-Export-Total`: total de candidatos exportados com sucesso
- `X-Export-Errors`: candidatos que falharam (não interrompem a exportação)

📋 **Regras de negócio:**
- Apenas `admin` ou `recruiter` podem exportar (roles verificadas por `require_admin_or_recruiter`)
- Candidatos não encontrados ou com UUID inválido geram erro por item (registrado em `errors[]`) mas não bloqueiam a exportação dos demais
- Se **nenhum** candidato for válido → HTTP 404 "No valid candidates found for export"
- Exportação não tem auditoria por candidato (diferente de update-status e delete)

⚠️ **"O erro mais comum é esperar JSON na resposta."** A rota retorna `StreamingResponse`, não `application/json`. O proxy Next.js (`bulk/export/route.ts`) detecta `content-type` e repassa o blob com headers corretos.

## 11. Compartilhar Seleção

**Onde:** Funil (`CandidateSearchResultsView`) e Kanban.
**Componente:** `ShareSearchModal` (`src/components/modals/share-search-modal.tsx`)
**Rota backend:** não usa as rotas `/bulk/*` — usa as rotas de shared searches

**Invocação no Funil:**
```typescript
// CandidateSearchResultsView.tsx
actions={[{
  id: 'share_search',
  onClick: () => {
    const selectedList = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
    setShareSearchCandidates(selectedList.map(c => ({ id, name, email, avatar_url, current_title, linkedin_url })))
    setShareSearchTitle(lastSearchQuery || `Busca de ${new Date().toLocaleDateString('pt-BR')}`)
    setShowShareSearchModal(true)
  }
}]}
```

**Invocação no Kanban:** via `useKanbanBulkActions` → `setShowShareGestorModal(true)`.

**`ShareSearchModal` props:**
```typescript
interface ShareSearchModalProps {
  open: boolean
  onClose: () => void
  shareType: 'search' | 'list'     // 'list' para bulk selection
  title: string                      // título do shortlist
  candidateIds: string[]
  candidateCount: number
  sourceQuery?: string
  sourceListId?: string
  onSuccess?: (sharedSearch) => void
}
```

**Canais disponíveis:** `email | whatsapp | both`

**Expiração configurável:** sem prazo / 7 / 14 / 30 dias / personalizado

**Templates de comunicação:** carregados via `useCommunicationTemplates({ channel, situation: 'share_with_manager', autoLoad: true })`. Template de situação `share_with_manager` é pré-selecionado automaticamente se disponível.

**Permissões de visualização:** `canComment` e `canRate` — gestores podem comentar e avaliar candidatos no shortlist compartilhado.

📋 **Regras de negócio:**
- O compartilhamento cria um shortlist com token de acesso temporário — não é uma exportação
- `shareType: 'list'` (seleção manual) vs `shareType: 'search'` (compartilha a query de busca) — para bulk actions, sempre `'list'`
- LGPD consent dos candidatos para compartilhamento não é verificado neste modal (gap — ver §25)

## 12. Adicionar à Lista

**Onde:** Funil (`CandidateSearchResultsView`) e Kanban.
**Componente:** `AddToListModal` (`src/components/modals/add-to-list-modal.tsx`)
**Rota:** via `liaApi.getCandidateLists` + `liaApi.addCandidatesToList` (não usa rotas `/bulk/*`)

**Fluxo:**
1. Clique em "Lista" → `setShowAddToVacancyModal(true)` (ou handler específico no Kanban)
2. `AddToListModal` carrega listas existentes via `liaApi.getCandidateLists({ limit: 100 })`
3. Se sem listas → vai direto para modo "criar nova lista"
4. Recrutador seleciona lista existente ou cria nova (nome + cor)
5. Submit → `liaApi.addCandidatesToList(listId, candidateIds)` ou cria lista + adiciona

**Cores disponíveis:** 6 opções usando CSS variables do design system (`--lia-text-tertiary`, `--status-success`, `--status-warning`, `--status-error`, `--wedo-purple`, `--lia-text-secondary`).

📋 **Regras de negócio:**
- Sem limite explícito de candidatos por lista (não usa `MAX_BULK_ITEMS`)
- Lista nova recebe cor selecionada e nome livre
- Operação de "adicionar" é idempotente no backend (candidato já na lista → não duplica)

## 13. Excluir Candidatos

**Onde:** Funil (via legacy `bulk-actions-bar.tsx`).
**Rota:** `DELETE /api/backend-proxy/candidates/bulk/delete` → `DELETE /api/v1/candidates/bulk/delete`
**Auth:** `require_admin_or_recruiter`

**Tipos de exclusão:**
```python
class BulkDeleteRequest(WeDoBaseModel):
  candidate_ids: list[str]
  permanent: bool = False   # False = soft delete (is_active=False)
```

O FE sempre envia `permanent=False` (via `hard_delete: false` — ver §16 Schema drift).

**Soft delete:** `candidate.is_active = False` — preserva todos os dados para auditoria. O candidato não aparece mais em buscas ativas mas os dados permanecem no banco.

**Hard delete (`permanent=True`):** `repo.delete_candidate(candidate)` — deleção física. Só acionável via API direta (nenhuma UI expõe `permanent=True`).

**UX de confirmação:** `AlertDialog` com `<AlertTriangle>` em vermelho exibe: "Você está prestes a excluir **N candidato(s)**. Esta ação não pode ser desfeita." — mesmo que seja soft delete (texto tecnicamente impreciso).

📋 **Regras de negócio:**
- Apenas `admin` ou `recruiter` podem excluir (mesmo role gate da exportação)
- Soft delete é o default e o único path exposto pela UI
- Hard delete exige `permanent=True` explícito via API — não é acessível pelo FE atual
- Auditoria por candidato (`audit_service.log_decision` com `action="bulk_delete"`, não-bloqueante)
- Candidato já inativo (`is_active=False`) pode ser "excluído" novamente sem erro — só atualiza `updated_at`

⚠️ **"O erro mais comum é achar que soft delete é reversível pela UI."** Não há endpoint de "reativar candidato" exposto no FE. Reativação exige acesso direto ao banco ou endpoint admin específico.

## 14. Ações de conveniência (Favoritar, Ocultar, Revelar Contatos, Salvar na Base)

Estas ações não chamam as rotas `/bulk/*` — são operações locais de estado ou chamadas individuais:

### Favoritar (`favorites`)
- Handler: `talentFunnel.toggleFavoriteCandidate(id)` em loop para cada `id` em `selectedCandidatesForBatch`
- Persiste via store Zustand do funil (sincroniza com backend individualmente)
- Toast: `toast.success(t('results.favoritesUpdated'))`
- **Não usa batch API**

### Ocultar (`hide`)
- Handler: `talentFunnel.hideCandidate(id)` em loop
- Remove candidato da lista de resultados no estado local
- Toast + `deselectAllCandidates()`
- **Não usa batch API**

### Revelar Contatos (`reveal_contacts`)
- Handler: `onBulkReveal` (prop do consumer)
- Debita créditos de reveal por candidato
- **Usa chamadas individuais** via crédito service

### Salvar na Base (`save_to_base`)
- Handler: `onSaveToLocalBase` (prop do consumer)
- Importa candidatos Pearch/externos para a base local PostgreSQL
- Visível apenas quando `selectedPearchCount > 0` (candidatos de fontes externas selecionados)
- `hidden: !(selectedPearchCount > 0)` — item invisível se não houver candidatos externos

---

# PARTE C — REFERÊNCIA

## 15. Contratos de API

### Endpoints bulk (FastAPI, porta 8001)

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/api/v1/candidates/bulk/update-status` | any auth | Atualiza status de N candidatos |
| POST | `/api/v1/candidates/bulk/assign-job` | any auth | Atribui N candidatos à uma vaga |
| POST | `/api/v1/candidates/bulk/send-email` | any auth | Envia email de template para N candidatos |
| POST | `/api/v1/candidates/bulk/start-screening` | any auth | Cria sessão de triagem WSI para N candidatos |
| POST | `/api/v1/candidates/bulk/export` | admin/recruiter | Exporta N candidatos como CSV/XLSX |
| DELETE | `/api/v1/candidates/bulk/delete` | admin/recruiter | Soft/hard delete de N candidatos |
| POST | `/api/v1/candidates/bulk/add-tags` | any auth | Adiciona tags a N candidatos |
| POST | `/api/v1/candidates/bulk/remove-tags` | any auth | Remove tags de N candidatos |

### Proxy Next.js (App Router)

| Rota proxy | Mapeamento |
|-----------|-----------|
| `/api/backend-proxy/candidates/bulk/update-status` | `POST /api/v1/candidates/bulk/update-status` |
| `/api/backend-proxy/candidates/bulk/assign-job` | `POST /api/v1/candidates/bulk/assign-job` |
| `/api/backend-proxy/candidates/bulk/send-email` | `POST /api/v1/candidates/bulk/send-email` |
| `/api/backend-proxy/candidates/bulk/start-screening` | `POST /api/v1/candidates/bulk/start-screening` |
| `/api/backend-proxy/candidates/bulk/export` | `POST /api/v1/candidates/bulk/export` (streaming) |
| `/api/backend-proxy/candidates/bulk/delete` | `DELETE /api/v1/candidates/bulk/delete` |

Cada proxy route: `export const dynamic = "force-dynamic"` + valida body via Zod + repassa `Authorization` header.

### `BulkOperationResult` (backend, bulk_actions.py:104)

```python
class BulkOperationResult(BaseModel):
    total: int           # total de IDs recebidos
    successful: int      # processados com sucesso
    failed: int          # com erro
    errors: list[BulkOperationError] = []
    processed_ids: list[str] = []
    message: str = ""
```

```python
class BulkOperationError(BaseModel):
    id: str              # candidate_id que falhou
    error_message: str   # razão do erro
```

## 16. Schema drift FE ↔ BE

⚠️ **Discrepância importante: o tipo `BulkOperationResult` no FE difere do BE.**

| Campo | BE (`bulk_actions.py`) | FE (`bulk.types.ts`) |
|-------|----------------------|---------------------|
| sucesso geral | `successful` (int) | `success` (boolean) |
| itens processados | `successful` (int) | `processed` (int) |
| itens com erro | `failed` (int) | `failed` (int) |
| detalhe do erro | `errors[].error_message` | `errors[].error` |

O FE legacy (`bulk-actions-bar.tsx`) usa `result.processed - result.failed` para calcular sucessos — mas o BE retorna `successful` diretamente. O kanban (`useKanbanBulkActions`) usa `apiResult.errors?.map(e => [e.id, e.error])` — mas o BE retorna `e.error_message`.

Esse drift causa silenciamento de erros em alguns paths do kanban.

**Discrepância no assign-job:**

| Campo | FE (`bulk.types.ts`) | BE (`BulkAssignJobRequest`) |
|-------|---------------------|---------------------------|
| ID da vaga | `job_id` | `job_vacancy_id` |

**Discrepância no delete:**

| Campo | FE (`BulkDeleteRequest`) | BE (`BulkDeleteRequest`) |
|-------|------------------------|------------------------|
| hard delete | `hard_delete?: boolean` | `permanent: bool = False` |

## 17. Componentes & estado (frontend)

### Arquivo canônico: `src/components/ui/bulk-actions-bar.tsx`

- Exporta: `BulkActionsBar`, `BulkActionType` (union de 17 strings), `BulkActionItem`, `BulkActionsBarProps`
- Stateless — sem useState interno (exceto nenhum)
- `displayName = 'BulkActionsBar'` para DevTools

### `BulkActionType` (union canônica, bulk-actions-bar.tsx:174)

```typescript
export type BulkActionType =
  | 'move_stage' | 'request_data' | 'send_message' | 'reject'
  | 'export' | 'add_to_list' | 'add_to_vacancy' | 'share_search'
  | 'favorites' | 'wsi_screening' | 'hide' | 'save_to_base'
  | 'publish' | 'insights' | 'duplicate' | 'toggle_status'
  | 'assign_recruiter'
```

### Serviço de API: `src/services/lia-api/bulk-api.ts`

Exporta: `bulkUpdateStatus`, `bulkAssignJob`, `bulkSendEmail`, `bulkStartScreening`, `bulkExport`, `bulkDelete`. Todos fazem fetch direto para o proxy Next.js com `getAuthHeaders()`.

### Schemas Zod: `src/lib/schemas/candidate.schema.ts`

```typescript
const bulkIdsSchema = z.object({ candidate_ids: z.array(z.string().uuid()).min(1).max(100) })
const bulkUpdateStatusSchema = bulkIdsSchema.extend({ new_status: z.enum([...]) })
const bulkAssignJobSchema = bulkIdsSchema.extend({ job_vacancy_id: z.string().uuid(), notes: z.string().optional() })
const bulkSendEmailSchema = bulkIdsSchema.extend({ template_id: z.string().uuid() })
const bulkStartScreeningSchema = bulkIdsSchema.extend({ job_vacancy_id: z.string().uuid(), screening_type: z.enum(['text','voice']).default('text'), override_saturation: z.boolean().default(false) })
const bulkDeleteSchema = bulkIdsSchema.extend({ permanent: z.boolean().default(false) })
const bulkExportSchema = bulkIdsSchema.extend({ format: z.enum(['csv','xlsx']), fields: z.array(z.string()).optional() })
```

### `BulkActionsRepository` (`app/repositories/bulk_actions_repository.py`)

- Session-in-constructor pattern: `def __init__(self, db: AsyncSession)`
- Métodos: `get_candidate_by_id`, `get_job_vacancy_by_id`, `get_email_template_by_id`, `get_company_by_id`, `get_default_company`, `get_vacancy_channel_counts`, `delete_candidate`, `commit`, `rollback`
- `get_job_vacancy_by_id`: usa comment `# TENANT-EXEMPT` — RLS PostgreSQL enforça o filtro de company a nível de DB via role `lia_app`
- Injetado via `Depends(get_bulk_actions_repo)` (`app/repositories/dependencies.py`)

## 18. HITL gate nas bulk actions

O HITL (Human-In-The-Loop) gate (`LIA_HITL_GATE=on`) aplica-se às **tools do agente**, não às APIs bulk diretas.

**Onde HITL está wired para operações relacionadas a bulk:**

| Tool do agente | Arquivo | Linha |
|----------------|---------|-------|
| `bulk_update_candidates_stage` | `candidate_tools.py` | 790 |
| `send_bulk_email` | `communication_tools.py` | 377 |
| `send_email` (individual) | `communication_tools.py` | 44 |
| `reject_candidate` (individual) | `candidate_tools.py` | 526 |
| `update_candidate_stage` (kanban) | `kanban_tool_registry.py` | 763 |
| `reject_candidate` (kanban) | `kanban_tool_registry.py` | 826 |

**HITL NÃO se aplica** quando o recrutador usa a barra de bulk actions diretamente — as chamadas vão direto para `/api/v1/candidates/bulk/*` sem passar pelo agente. O HITL só é acionado quando o **agente LIA** invoca essas tools via chat.

**Modo dormante:** `LIA_HITL_GATE` default é `off` (produção). Ativar para testar o fluxo de aprovação.

## 19. FairnessGuard nas bulk actions

O `FairnessGuard` é instanciado uma vez no módulo (`bulk_actions.py:26`):
```python
_fairness_guard = _FairnessGuard()
```

**Onde está wired:**

| Endpoint | Campo verificado | Linha |
|----------|----------------|-------|
| `bulk_assign_to_job` | `request.notes` | 325 |

O check roda **antes de qualquer operação de banco** e bloqueia a requisição inteira se encontrar termos discriminatórios:

```python
if request.notes:
    _fg_result = _fairness_guard.check(request.notes)
    if _fg_result.is_blocked:
        raise HTTPException(status_code=422, detail={
            "error": "fairness_blocked",
            "field": "notes",
            "needs_review": _fg_result.blocked_terms or [],
            "category": _fg_result.category,
        })
```

**Outros endpoints:** `update-status`, `send-email`, `start-screening`, `export`, `delete` não verificam FairnessGuard (sem campo de texto livre).

**FairnessGuard também wired em:**
- `bulk_actions.py` como instância de módulo (`_fairness_guard`)
- `candidate_search/search.py:134` (busca de candidatos)
- `candidate_search/archetypes.py:1234` (arquétipos de busca)
- `candidates_crud.py:785` (motivo de rejeição individual)

## 20. Saturation guard (Iniciar Triagem)

O saturation guard previne sobrecarga do pipeline de triagem. Configuração por vaga e empresa.

**Função:** `_check_vacancy_saturation(repo, vacancy)` (`bulk_actions.py:51`)

**Fontes de threshold (ordem de precedência):**
1. `vacancy.governance_rules["threshold_web"]` / `["threshold_sourcing"]`
2. `company.additional_data["saturation_settings"]["threshold_web"]` / `["threshold_sourcing"]`
3. Constante default: `DEFAULT_SATURATION_THRESHOLD = 20`

**Contagem por canal** (`BulkActionsRepository.get_vacancy_channel_counts`):
- **Organic:** `VacancyCandidate.origin IN ('web', 'whatsapp') OR origin IS NULL`
- **Sourcing:** `VacancyCandidate.origin IN ('sourcing', 'ats')`
- Status excluídos da contagem: `('rejected', 'declined', 'withdrawn')`

**Bypass temporal:** `vacancy.governance_rules["saturation_disabled_until"]` (ISO datetime string) — se esta data for no futuro, o guard é ignorado completamente para esta vaga.

**Override manual:** `override_saturation=True` no request — loga a decisão mas não verifica saturation.

**Resposta ao cliente quando saturado:**
```json
{
  "error": "saturation_limit_reached",
  "message": "Pipeline saturado (organic 22/20). Triagem bloqueada. Use override_saturation=true para aprovar manualmente.",
  "organic_count": 22,
  "organic_threshold": 20,
  "sourcing_count": 5,
  "sourcing_threshold": 20
}
```

## 21. Config & variáveis de ambiente

| Variável | Onde | Valor típico | Efeito |
|----------|------|-------------|--------|
| `BACKEND_URL` | Next.js proxy routes | `http://127.0.0.1:8001` | URL base do FastAPI |
| `LIA_HITL_GATE` | `lia-agent-system/.env` | `off` | Ativa/desativa gate HITL nas tools do agente |
| `MAX_BULK_ITEMS` | `bulk_actions.py:47` | `100` | Limite de IDs por operação bulk |
| `DEFAULT_SATURATION_THRESHOLD` | `bulk_actions.py:56` | `20` | Threshold padrão de saturation por canal |
| `DEFAULT_UNLOCK_INCREMENT` | `bulk_actions.py:57` | `10` | (não usado no FE atual) |
| `DEFAULT_UNLOCK_HOURS` | `bulk_actions.py:58` | `24` | (não usado no FE atual) |

**RAILS_ENABLED:** sempre `False` no ambiente atual (sem `RAILS_API_URL` definido). Nenhum dos endpoints bulk toca Rails.

## 22. 📋 Quadro-resumo de regras de negócio

| Regra | Ação afetada | Onde está | Consequência se violada |
|-------|-------------|-----------|------------------------|
| `MAX_BULK_ITEMS = 100` | Todas | `bulk_actions.py:47` + Zod schema | HTTP 422 antes do loop |
| `company_id` do JWT | Todas | `Depends(require_company_id)` | HTTP 401/403 |
| Candidato inativo → erro por item | Update status, assign, email, screening, delete | Loop de cada endpoint | Registra em `errors[]`, não interrompe os demais |
| Template inativo → bloqueia TUDO | Send email | `bulk_actions.py:448` | HTTP 400 antes do loop |
| LGPD consent obrigatório | Send email | `candidate.communication_consent` | Erro por candidato (não enviado) |
| FairnessGuard em notes | Assign job | `bulk_actions.py:325` | HTTP 422 antes do loop, todos bloqueados |
| Saturation guard | Start screening | `_check_vacancy_saturation` | HTTP 409 antes do loop, todos bloqueados |
| Soft delete = padrão | Delete | `request.permanent = False` | `is_active=False`, dados preservados |
| Admin/Recruiter apenas | Export, Delete | `require_admin_or_recruiter` | HTTP 403 |
| Auditoria por candidato | Update status, Delete | `audit_service.log_decision` | Não-bloqueante (falha silenciosa) |
| VacancyCandidate canônico | Assign job | P0-1 correction (`_VacancyCandidate`) | Sem link → candidato não aparece no kanban/contagem |
| communication_consent | Send email | `candidate.communication_consent` | Candidato sem consent → erro individual |

## 23. Checklist de replicação

Para replicar o sistema de bulk actions em outro ambiente do zero:

**Backend (FastAPI)**
- [ ] Criar `BulkActionsRepository` com session-in-constructor e métodos necessários
- [ ] Criar `bulk_actions.py` com todos os endpoints e `MAX_BULK_ITEMS`
- [ ] Instalar `openpyxl` para exportação XLSX (sem ele, fallback silencioso para CSV)
- [ ] Registrar `router` em `app/main.py` com prefix `/api/v1`
- [ ] Verificar que `FairnessGuard` está importável de `app.shared.compliance.fairness_guard`
- [ ] Verificar que `audit_service` está importável de `app.shared.compliance.audit_service`
- [ ] Verificar que `require_company_id` está disponível em `app.shared.security`
- [ ] Verificar que `require_admin_or_recruiter` está em `app.auth.dependencies`
- [ ] Configurar RLS PostgreSQL na role `lia_app` para multi-tenancy no `BulkActionsRepository`

**Frontend (Next.js)**
- [ ] Criar `src/components/ui/bulk-actions-bar.tsx` (componente genérico)
- [ ] Criar `src/services/lia-api/bulk-api.ts` com todas as funções
- [ ] Criar `src/services/lia-api/types/bulk.types.ts` (alinhar campos com BE — ver §16)
- [ ] Criar proxy routes em `src/app/api/backend-proxy/candidates/bulk/*/route.ts`
- [ ] Criar schemas Zod em `src/lib/schemas/candidate.schema.ts` (bulkIdsSchema + extensões)
- [ ] Instalar `sonner` para toasts
- [ ] Montar `BulkActionsBar` em cada consumer com `actions` corretos
- [ ] Gerenciar `selectedCandidates: Set<string>` localmente em cada consumer

**Modais auxiliares**
- [ ] `ShareSearchModal` para compartilhamento (usa `useCommunicationTemplates`)
- [ ] `AddToListModal` para adição a listas (usa `liaApi.getCandidateLists`)
- [ ] `BulkActionModal` para move_stage/reject no Kanban (usa `useKanbanBulkActions`)

## 24. Glossário

| Termo | Definição |
|-------|-----------|
| **Bulk operation** | Operação executada em N candidatos de uma vez via um único request |
| **Soft delete** | `is_active=False` — dado preservado, candidato oculto de buscas |
| **Hard delete** | Deleção física do banco — irreversível |
| **Saturation guard** | Limite de candidatos por canal (organic/sourcing) por vaga para evitar sobrecarga |
| **HITL gate** | Human-in-the-Loop: aprovação explícita do recrutador antes de ação sensível do agente |
| **FairnessGuard** | Detector de termos discriminatórios — bloqueia antes de qualquer operação |
| **VacancyCandidate** | Tabela canônica `vacancy_candidates` que liga candidato à vaga — lida pelo kanban |
| **communication_consent** | Campo booleano em `Candidate` — LGPD consent para receber comunicações |
| **progress modal** | Dialog de progresso mostrado durante a operação bulk (bloqueante para o usuário) |
| **BulkActionType** | Union TypeScript de 17 strings identificando cada tipo de ação |
| **override_saturation** | Flag para bypassar saturation guard manualmente (com log de auditoria) |
| **session-in-constructor** | Padrão de repositório onde `AsyncSession` é injetado no `__init__`, não nos métodos |

## 25. Gaps & pontos de atenção

### G1 — Schema drift FE ↔ BE (risco de bugs silenciosos)
**Impacto:** P1. Os campos `successful`/`processed` e `error_message`/`error` não batem entre FE e BE. O Kanban usa `apiResult.errors?.map(e => [e.id, e.error])` mas o BE retorna `e.error_message`. Resultado: o mapa de erros fica vazio, candidatos que falharam parecem bem-sucedidos na UI.
**Evidência:** `bulk.types.ts:1-14` vs `bulk_actions.py:104-112`.

### G2 — job_id vs job_vacancy_id no assign-job
**Impacto:** P1. `bulk.types.ts` declara `job_id`, o schema Zod do proxy usa `job_vacancy_id`, o BE espera `job_vacancy_id`. O FE em `bulk-api.ts:bulkAssignJob` envia `job_id`. O Zod do proxy pode não validar corretamente ou silenciar o campo errado.
**Evidência:** `bulk.types.ts:20` vs `bulk_actions.py:135`.

### G3 — Triagem WSI: job_vacancy_id obrigatório no BE, não enviado pelo FE legacy
**Impacto:** P1. `BulkStartScreeningRequest` (BE) exige `job_vacancy_id` para checar saturation e criar a sessão vinculada. O FE legacy (`bulk-actions-bar.tsx:219`) chama `liaApi.bulkStartScreening({ candidate_ids: selectedIds })` — sem `job_vacancy_id`. O BE recebe `job_vacancy_id` ausente → `uuid.UUID(request.job_vacancy_id)` lança `AttributeError` ou `ValidationError`. A operação falha antes de criar qualquer sessão.
**Evidência:** `bulk-actions-bar.tsx:219-233` vs `bulk_actions.py:162-175`.

### G4 — Screening session JSONB não conecta ao TriagemSession canônico
**Impacto:** P1. `bulk_start_screening` cria entradas em `candidate.additional_data["screening_sessions"]` (JSONB), não em `triagem_sessions` (tabela canônica). O `TriagemSessionService` não lê esse JSONB para iniciar triagens automaticamente. O candidato muda para status `screening` mas nenhum fluxo de triagem é ativado de fato.
**Evidência:** `bulk_actions.py:618-643` — sem chamada a `TriagemSessionService` ou `WSIInterviewGraph`.

### G5 — Fallback XLSX→CSV sem aviso ao usuário
**Impacto:** P2. Se `openpyxl` não estiver instalado, o backend exporta CSV com header `X-Format-Fallback`. O FE não lê esse header — o usuário recebe CSV achando que é XLSX.
**Evidência:** `bulk_actions.py:796-825`.

### G6 — LGPD consent não verificado no ShareSearchModal
**Impacto:** P2. Ao compartilhar uma seleção de candidatos com um gestor externo, o modal não verifica se cada candidato consentiu com o compartilhamento. O consent para `purpose="share_with_manager"` não existe no fluxo atual.
**Evidência:** `share-search-modal.tsx` — sem chamada a `ConsentCheckerService`.

### G7 — Componente legacy `src/components/bulk-actions-bar.tsx` sem consumer ativo
**Impacto:** P2. O componente autônomo em `src/components/bulk-actions-bar.tsx` (696 linhas) não é montado em nenhuma página ativa — nenhum import ativo aponta para ele. É dead code funcional que inclui handlers completos com modais internos. Pode criar confusão se um dev adicionar um novo consumer apontando para o path errado.
**Evidência:** grep confirma que todos os consumers importam de `@/components/ui/bulk-actions-bar`, não de `@/components/bulk-actions-bar`.

### G8 — add-tags/remove-tags sem exposição na UI
**Impacto:** P2. Os endpoints `POST /candidates/bulk/add-tags` e `POST /candidates/bulk/remove-tags` existem no backend mas nenhum `BulkActionType` ou action no FE os chama. São endpoints sem consumer de UI.
**Evidência:** `bulk_actions.py:937-1076` vs ausência em `BulkActionType` union e nos `actions[]` dos consumers.

### G9 — hard_delete vs permanent: naming drift
**Impacto:** P3. FE envia `hard_delete: false` (`BulkDeleteRequest` em `bulk.types.ts`) mas BE lê `permanent: bool`. O Zod schema do proxy usa `permanent`. O FE `bulk-api.ts:bulkDelete` passa `hard_delete` que o proxy Zod ignora, enviando `permanent` com seu default `False`. Funciona acidentalmente, mas o campo semântico está errado.
**Evidência:** `bulk.types.ts:33` vs `bulk_actions.py:191`.
