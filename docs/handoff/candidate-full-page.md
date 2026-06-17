# Handoff — Página Completa do Candidato: Perfil, Histórico e Gestão

> **Objetivo deste documento:** permitir que um time de devs **replique do zero**, em outro ambiente, toda a funcionalidade da **página full do candidato** — incluindo header de ações, abas de Perfil / Atividades / Arquivos / Pareceres, edição inline, LGPD/consentimentos, scores e o painel lateral de resumo.
>
> **Fora de escopo:** a aba Banco de Talentos (listagem de listas, buscas salvas) e o kanban de candidatos por vaga — documentados em `funil-talentos-busca.md`.
>
> **Como ler:** a **Parte A** descreve arquitetura e fluxos de carregamento. A **Parte B** cobre cada aba/seção individualmente. A **Parte C** é referência consolidada (API, schema, PII, estado, checklist). Cada funcionalidade traz um bloco **📋 Regras de negócio** com o *como* funciona, não só o *que* existe.
>
> **Stack:** Next.js 15 (App Router) · FastAPI · PostgreSQL + EncryptedFieldMixin (PII at rest) · SWR · React Context · Zustand (stores globais do kanban/funil)

---

## Índice

**Parte A — Arquitetura e Fluxos**
1. [Visão geral & arquitetura](#1-visão-geral--arquitetura)
2. [Rota da página e contextos de acesso](#2-rota-da-página-e-contextos-de-acesso)
3. [Fluxo de carregamento de dados](#3-fluxo-de-carregamento-de-dados)

**Parte B — Abas e Seções**
4. [Header e dados principais](#4-header-e-dados-principais)
5. [Aba Perfil Completo](#5-aba-perfil-completo)
6. [Aba Atividades](#6-aba-atividades--linha-do-tempo)
7. [Aba Arquivos](#7-aba-arquivos)
8. [Aba Pareceres](#8-aba-pareceres)
9. [Seção LGPD (consentimento)](#9-seção-lgpd-consentimentos)
10. [Tags e notas](#10-tags-e-notas)
11. [Scores — LIA, WSI, BigFive, DISC](#11-scores--lia-wsi-bigfive-disc)
12. [Edição inline de campos](#12-edição-inline-de-campos)

**Parte C — Referência**
13. [Contratos de API (CRUD completo)](#13-contratos-de-api-crud-completo)
14. [Schema do modelo de candidato](#14-schema-do-modelo-de-candidato)
15. [PII por campo: visibilidade por papel de usuário](#15-pii-por-campo-visibilidade-por-papel-de-usuário)
16. [Componentes & estado (frontend)](#16-componentes--estado-frontend)
17. [📋 Quadro-resumo de regras de negócio](#17--quadro-resumo-de-regras-de-negócio)
18. [Checklist de replicação](#18-checklist-de-replicação)
19. [Glossário](#19-glossário)
20. [Gaps & pontos de atenção](#20-gaps--pontos-de-atenção)

---

# PARTE A — ARQUITETURA E FLUXOS

## 1. Visão geral & arquitetura

A página full do candidato é um componente polimórfico — funciona em dois modos: como **overlay de tela cheia** (kanban/modal) e como **rota standalone** (URL direta). O mesmo componente `<CandidatePage>` renderiza os dois casos via prop `mode`.

```
┌─ Next.js App Router ────────────────────────────────────────────────────────┐
│                                                                              │
│  Rota standalone: /[locale]/(dashboard)/funil-de-talentos/candidato/[id]   │
│    └── page.tsx (ErrorBoundary)                                             │
│         └── CandidateRoutePage.tsx ("use client")                          │
│              └── useCandidateForPage(id) — SWR fetcher via liaApi           │
│                   └── <CandidatePage candidate={...} mode="page" />         │
│                                                                              │
│  Overlay de kanban: chamado por CandidatePreview no contexto do kanban      │
│    └── <CandidatePage candidate={...} mode="modal" isOpen={true} />        │
│                                                                              │
│  Compartilhado em ambos os casos:                                           │
│    candidate-page.tsx  ← raiz do componente                                │
│    ├── CandidateEditProvider   ← Context edição inline (D7)                │
│    ├── CandidatePageHeader     ← identidade + botões de ação                │
│    ├── Tabs (profile|activities|files|opinions)                             │
│    └── [mode=page] CandidatePageSummary  ← aside sticky (col-span-2/5)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Backend (FastAPI 8001) ────────────────────────────────────────────────────┐
│                                                                              │
│  GET  /api/v1/candidates/{id}         ← dados completos do perfil           │
│  PUT  /api/v1/candidates/{id}         ← update completo                    │
│  PATCH /api/v1/candidates/{id}/stage  ← mover no pipeline                  │
│  PUT  /api/v1/candidates/{id}/experiences                                   │
│  PUT  /api/v1/candidates/{id}/education                                     │
│  PUT  /api/v1/candidates/{id}/skills                                        │
│  PUT  /api/v1/candidates/{id}/certifications                                │
│  PUT  /api/v1/candidates/{id}/identity ← name (criptografado)              │
│  GET/POST /api/v1/candidates/{id}/consents ← LGPD                          │
│  DELETE /api/v1/candidates/{id}/consents/{type}                             │
│  GET  /api/v1/activities?candidate_id={id} ← timeline de atividades        │
│  GET  /api/v1/opinions/candidate/{id}/history                               │
│  POST /api/v1/opinions/candidate/{id}/parecer ← gera parecer LIA           │
│  GET  /api/v1/candidates/{id}/files    ← arquivos e CV                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Princípios de replicação:**
- Todo fetch passa pelo proxy Next.js `/api/backend-proxy/*` (cookie httpOnly / CORS).
- `company_id` SEMPRE vem do JWT via `Depends(require_company_id)` — nunca do payload.
- Rails eliminado: `RAILS_ENABLED=False` (sem `RAILS_API_URL` no `.env`). O router de candidates (`candidates_crud.py`) carrega `enforce_candidates_deprecation` mas não faz HTTP 410 a menos que `STRICT_RAILS_ONLY=true`.
- PII sensível (name, email, CPF, phone) está criptografado em repouso via `EncryptedFieldMixin` (Fernet + SHA-256 hash). O ORM transparece a decriptação; o JSON de resposta já traz o texto plano (após auth).

---

## 2. Rota da página e contextos de acesso

### 2.1 Rota standalone

```
/[locale]/(dashboard)/funil-de-talentos/candidato/[id]
```

Arquivo: `plataforma-lia/src/app/[locale]/(dashboard)/funil-de-talentos/candidato/[id]/page.tsx`

```tsx
// page.tsx — Server Component (apenas metadata)
export default function CandidatoDetailRoute() {
  return (
    <ErrorBoundarySection>
      <CandidateRoutePage />
    </ErrorBoundarySection>
  )
}
```

```tsx
// CandidateRoutePage.tsx — "use client"
// Lê id da URL via useParams(), carrega via useCandidateForPage(id)
// Renderiza <CandidatePage mode="page" />
```

### 2.2 Contexto de overlay (kanban)

Quando o recrutador abre um candidato a partir do kanban de vaga, o chamador passa o objeto diretamente — **sem fetch de rede** porque o kanban já tem os dados em memória:

```tsx
<CandidatePage
  candidate={candidateObject}   // já carregado pelo kanban
  mode="modal"
  isOpen={isOpen}
  onClose={handleClose}
  jobId={currentJobId}
  onSendEmail={...}
  onSendWhatsApp={...}
  // ... outros callbacks de ação
/>
```

⚠️ **O erro mais comum é** tentar usar `useCandidateForPage` em ambos os contextos. O hook usa SWR com key `["candidate-by-id", id]` e é específico para a rota standalone. Em contexto kanban, o candidate já está no estado do componente pai — não usar este hook.

### 2.3 Rota alternativa (Teams)

```
/[locale]/teams-tab/candidatos
```

Renderiza `<CandidatesPage />` (não a página full do candidato — é o listing do Microsoft Teams).

---

## 3. Fluxo de carregamento de dados

```
1. URL /funil-de-talentos/candidato/[id]
   → CandidateRoutePage monta
   → useCandidateForPage(id) dispara

2. useCandidateForPage:
   → SWR key: ["candidate-by-id", id]
   → fetcher: liaApi.getCandidate(id)
   → GET /api/backend-proxy/candidates/[id]
   → proxy → FastAPI GET /api/v1/candidates/{id}

3. FastAPI get_candidate():
   a. UUID parse (HTTPException 404 se inválido)
   b. candidate_repo.get_by_id_str(id) — scoped por company_id RLS
   c. _filter_candidates_by_dept_scope() — Sprint 2 RBAC (soft 404 se fora do dept)
   d. _load_role_pii_defaults(company_id) — HiringPolicy.pii_visibility_defaults
   e. apply_pii_field_visibility(serialized, current_user, role_defaults)
      → resolve_pii_field_visibility() → precedência user > role > legacy > show
      → redact campos indisponíveis (None para strings, [] para listas)
      → seta salary_masked / sensitive_pii_masked flags
   f. _audit_pii_access() — log SOX quando user privilegiado acessa PII (Art. 37 V)
   g. Retorna ResponseEnvelope{ok: true, data: {...}}

4. SWR recebe data → CandidateRoutePage renderiza CandidatePage com candidate={data}

5. CandidatePage monta:
   → useCandidatePreviewCore(candidate) — state central (tabs, modais, opinions)
   → useCandidateFieldUpdate(candidateId) — hook de edição inline (D7)
   → CandidateEditProvider(editable=mode==="page" && FF_CANDIDATE_EDIT)
   → renders: Header + Tabs + [mode=page] Aside Summary

6. Opiniões carregam LAZY:
   → useCandidatePreviewCore:fetchOpinionsSummary() — ao montar
   → GET /api/backend-proxy/opinions/candidate/{id}/summary
   → fetchOpinionsHistory() — só quando activeTab === "opinions"
   → GET /api/backend-proxy/opinions/candidate/{id}/history
```

**SWR config:**

```ts
// use-candidate-for-page.ts:22
{
  revalidateOnFocus: false,
  dedupingInterval: 30000,    // 30s — evita refetch em navegação rápida
  revalidateOnReconnect: true,
}
```

📋 **Regras de negócio — carregamento:**

| Regra | Mecanismo |
|---|---|
| Multi-tenancy: candidato pertence à empresa do JWT | `_assert_tenant_scope()` em crud.py:49 + Postgres RLS |
| Dept scope: candidatos de outros departamentos = 404 | `_filter_candidates_by_dept_scope()` crud.py:342 — soft 404, não 403 (evita leakage de existência) |
| PII mascarado por papel | `apply_pii_field_visibility()` crud.py:253 — field-level, precedência: user > role > legacy bucket |
| Enriquecimento LinkedIn é background task | `_background_enrich_candidate()` crud.py:572 — dispara quando `linkedin_url` presente no create |

---

# PARTE B — ABAS E SEÇÕES

## 4. Header e dados principais

**Componente:** `CandidatePageHeader.tsx`

**O que exibe:**
- Avatar (`CandidateAvatar`) + Nome + ID chip + Score badge
- Headline e cargo atual (editáveis se `editable=true`)
- Links sociais: LinkedIn, GitHub, Portfolio (ícones)
- Barra de ações rápidas (ícones): Email, WhatsApp, Agendar Entrevista, Triagem WSI, Adicionar à Vaga, Adicionar à Lista, Enviar Feedback
- Botão X (fechar/voltar)

**Dependências de edição inline:**

```tsx
// CandidatePageHeader.tsx:63
const { editable, updateField, isSaving } = useCandidateEdit()
// "editable" vem do CandidateEditProvider — true só em mode="page" + FF_CANDIDATE_EDIT=true
```

**Campos editáveis no header (quando editable=true):**
- `name` → rota dedicada `/api/backend-proxy/candidates/{id}/identity` (criptografia-aware)
- `headline`
- `current_title`
- `location_city`
- `years_of_experience` (tipo number)
- `github_url` (tipo url)
- `portfolio_url` (tipo url)

**Score badge:**

```tsx
// candidate-page.tsx:101
const liaScore = c.liaAnalysis?.score ?? 0
// CandidateScoreBadge format="percent": score >= 80 → verde, >= 60 → amarelo, < 60 → vermelho
```

⚠️ **O erro mais comum é** confundir `liaAnalysis.score` (0-100, vem normalizado do backend) com o `lia_score` raw do modelo (também 0-100, mesmo dado, nomes diferentes dependendo do contexto de serialização).

**Ações rápidas — regras:**

| Ação | Handler | Condição |
|---|---|---|
| Email | `onSendEmail(candidate)` ou `mailto:` direto | Desabilitado se sem email e sem handler |
| WhatsApp | `onSendWhatsApp(candidate)` ou `wa.me/{phone}` | Desabilitado se sem phone e sem handler |
| Agendar | `onSendAgendamento(candidate)` | Sempre disponível |
| Triagem WSI | `onWSIScreening(candidate)` | Sempre disponível |
| Adicionar à Vaga | `onAddToVacancy(candidate)` | Sempre disponível |
| Adicionar à Lista | `onAddToList(candidate)` | Sempre disponível |
| Feedback | `onSendFeedback(candidate)` | Sempre disponível |

Todos os callbacks de ação são **opcionais** — passados pelo contexto chamador (kanban) ou undefined (rota standalone, onde o header habilita ações padrão via `window.open`/`mailto:`).

---

## 5. Aba Perfil Completo

**Componente principal:** `CandidatePreviewProfileTab.tsx`

**Estrutura interna (blocos sequenciais):**

```
<CandidatePreviewProfileTab>
  ├── ExperienceHighlightCard      ← highlights gerados por LIA (lazy por companyId)
  ├── QualificationMatrixCard      ← matriz de qualificação da vaga (se jobId + parecer)
  │                                   OU flat search criteria (se busca ativa sem jobId)
  ├── EligibilityResultsSection    ← resultados de perguntas eliminatórias (se presentes)
  ├── ProfileLiaOpinionCard        ← parecer LIA atual + botão "Analisar com LIA"
  ├── ProfileSkillsMapCard         ← mapa de skills técnicas + soft skills
  ├── ProfileExperienceCards       ← histórico profissional (work_history)
  └── ProfileInfoCards             ← educação, certificações, idiomas, salário, endereço, LGPD link
```

### 5.1 Matriz de qualificação

A `QualificationMatrixCard` exibe a qualificação do candidato contra os requisitos. O mecanismo muda dependendo do contexto:

- **Com `jobId` + parecer salvo:** usa `score_breakdown.qualification_matrix` do parecer mais recente (grouped por categoria). Vem do backend via `/api/backend-proxy/opinions/candidate/{id}/summary`.
- **Sem `jobId` (busca ativa):** aceita `searchCriteria` prop com os critérios flat da busca. Busca on-the-fly via `QualificationMatrixCard` com `candidateId + companyId + searchCriteria`.

### 5.2 Resultados de elegibilidade

```tsx
// CandidatePreviewProfileTab.tsx:13
function extractEligibilityResults(candidate): EligibilityResultItem[] | undefined {
  const raw = candidate?.eligibility_results
  if (!Array.isArray(raw) || raw.length === 0) return undefined
  // normaliza 4 shapes legados para EligibilityResultItem canônico
}
```

Os resultados vêm serializados em `candidate.eligibility_results` (campo JSONB no perfil). Só aparecem quando o candidato passou pela triagem de elegibilidade. Se `eligibility_results` for array vazio ou ausente, a seção não renderiza.

### 5.3 ProfileInfoCards — dados pessoais, salário, localização, LGPD

**Subcards dentro de ProfileInfoCards:**

| Card | Campos do candidato | Editável |
|---|---|---|
| Resumo Profissional | `self_introduction` | Sim (textarea) |
| Formação Acadêmica | `education[]` (snapshot) | Via `EditArrayItemModal` |
| Certificações | `certifications[]` | Via `EditArrayItemModal` |
| Idiomas | `languages` (objeto) | Não (read-only) |
| Dados Financeiros | `current_salary`, `desired_salary_*` | Mascarado se `salary_masked=true` |
| Localização | `location_city`, `location_state`, etc. | Sim (string) |
| Consentimento LGPD | link para `onShowConsentHistory()` | N/A — leva à aba Consentimento |

📋 **Regras de negócio — Perfil:**

| Regra | Evidência |
|---|---|
| Salary masking: campos financeiros nullados quando `salary_masked=true` | `candidates_crud.py:205` `_redact_salary_for_user()` — mutates dict in-place, sets `salary_masked=True` |
| Endereço mascarado quando `sensitive_pii_masked=true` | `candidates_crud.py:228` `_redact_sensitive_pii_for_user()` — CPF, DoB, endereço, secondary contacts |
| Elegibilidade usa shape canônico único | `EligibilityVerificationService.get_eligibility_questions_from_job()` — único parser; 4 shapes legados normalizados via `EligibilityQuestionItem` |
| Parecer LIA gera/salva versionado | POST `/opinions/candidate/{id}/parecer` — auto-salva versão; aba Pareceres exibe histórico com chip "v{N} - Histórico" |

---

## 6. Aba Atividades / Linha do tempo

**Componente:** `CandidateActivitiesTab.tsx`
**Hook de dados:** `use-candidate-activities.ts`

### 6.1 Fetch de atividades

```ts
// use-candidate-activities.ts:56
// GET /api/backend-proxy/activities?candidate_id={id}&limit={n}
// Multi-tenancy: company_id enforced no backend via Depends(require_company_id) do JWT
// Frontend NÃO passa company_id na query — só JWT auth header
```

O backend `/api/v1/activities` filtra por `candidate_id`. O limite padrão é 50 atividades.

### 6.2 Normalização de atividades

```tsx
// CandidateActivitiesTab.tsx:normalizeActivity()
// Cada CandidateActivity recebe:
//   - icon / iconColor derivados do type string (email, wsi, screening, lia, offer, etc.)
//   - status mapeado: "approved"|"completed"|"in-progress"|"rejected"|"pending"
//   - date formatada em pt-BR
//   - statusLabel em português
```

**Tipos de atividade e seus ícones:**

| Tipo (substring) | Ícone | Cor |
|---|---|---|
| email | Mail | wedo-cyan |
| voice/wsi/screening | Mic | wedo-purple |
| video/interview | Video | wedo-orange |
| lia/brain/ai/analysis | Brain | wedo-coral |
| calendar/schedule/agendamento | Calendar | wedo-orange |
| offer/onboarding | Gift | status-success |
| test/code/technical | Code | wedo-purple |
| eval/rubric/feedback | ClipboardCheck | wedo-orange |
| approved/hired | ThumbsUp | status-success |
| rejected/declined | ThumbsDown | status-error |
| stage/pipeline | Target | wedo-cyan |

### 6.3 Filtros e visualização

`ActivityFilters` oferece:
- Filtro por tipo de atividade (`ActivityFilterType`)
- Modo de visualização (`ActivityViewType`)
- Filtro por período (`PeriodFilterType`)

`ActivityTimeline` renderiza a lista normalizada com expansão de detalhes por item.

**Detalhe expandido:** cada atividade expandida renderiza sub-componentes:
- `ActivityEvaluationDetails` — avaliações (score, BigFive, DISC via modal)
- `ActivityExpandedDetails` — detalhes genéricos
- `ActivityOtherDetails` / `ActivityAssessmentDetails` — assessments (abre BigFiveModal ou DISCModal)

📋 **Regras de negócio — Atividades:**

| Regra | Mecanismo |
|---|---|
| Multi-tenancy: só atividades da empresa do JWT | Backend enforça via `require_company_id` + scoping no `activities.py` |
| Triagem WSI/screening: abre modal com transcrição | `onOpenTriagemDetails(candidate)` passado como callback — abre `ScreeningMediaModal` |
| BigFive e DISC em atividade: abre modal específico | `ActivityEvaluationDetails.tsx:261` — chama `onSetBigFiveModalCandidate/Open` ou `onSetDiscModalData/Open` |

---

## 7. Aba Arquivos

**Componente:** `CandidateFilesTab.tsx`
**Hook:** `useCandidateFiles` (em `useCandidateFiles.tsx`)

### 7.1 Operações disponíveis

- **Listar:** GET `/api/backend-proxy/candidates/{id}/files`
- **Upload:** drag-and-drop ou seletor de arquivo (`.pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov`)
- **Download:** via `handleDownloadFile`
- **Deletar:** via `handleDeleteFile`
- **Preview:** `FilePreviewModal` — pdf, image, video, audio

### 7.2 Categorias automáticas

A LIA categoriza os arquivos automaticamente. As categorias são exibidas como chips filtrantes. Cada categoria tem um ícone e label.

### 7.3 Proxy routes de arquivo

```
GET  /api/backend-proxy/candidates/[id]/files          → lista arquivos
POST /api/backend-proxy/candidates/[id]/files          → upload
GET  /api/backend-proxy/candidates/[id]/files/[attachmentId] → download
DELETE /api/backend-proxy/candidates/[id]/files/[attachmentId] → delete
```

Todos os proxies usam `createProxyHandlers` com `auth: true` e `backendTarget: "fastapi"`.

📋 **Regras de negócio — Arquivos:**

| Regra | Mecanismo |
|---|---|
| Upload com progresso visual | `isUploading` + `uploadProgress` no hook — não bloqueia UI |
| Tipos aceitos explícitos | `input.accept = ".pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mov"` — validação client-side |
| Preview sem download forçado | `FilePreviewModal` — renderiza inline para PDF/image/video/audio |

---

## 8. Aba Pareceres

**Componente:** `CandidateOpinionsTab.tsx`
**Fetch via:** `useCandidatePreviewCore.fetchOpinionsHistory()` — lazy, só ao ativar a aba

### 8.1 Carregamento

```ts
// useCandidatePreviewCore.tsx:87
// GET /api/backend-proxy/opinions/candidate/{candidateId}/history?company_id={cid}
// Dedup: lastFetchedHistoryCandidateRef evita re-fetch ao trocar de aba
```

### 8.2 OpinionCard — versionamento

```tsx
// CandidateOpinionsTab.tsx
{!opinion.is_current && (
  <Chip>v{opinion.version} - Histórico</Chip>
)}
<OpinionCard
  opinion={opinion}
  type={opinion.opinion_type === 'wsi' ? 'wsi' : 'general'}
  isExpanded={expandedOpinionId === opinion.id}
  onToggle={...}
/>
```

Cada parecer tem:
- `is_current: boolean` — o mais recente é marcado como atual
- `version: number` — incrementado a cada nova análise
- `opinion_type: "wsi" | "general"` — WSI = resultado de triagem; general = parecer LIA sobre vaga

### 8.3 Gerar novo parecer

```ts
// useCandidatePreviewCore.tsx:handleAnalyzeWithLia()
// POST /api/backend-proxy/opinions/candidate/{id}/parecer
// Body: { job_id?: string, company_id: string }
// Backend gera, salva versão e retorna o novo parecer
```

O botão "Analisar com LIA" na `ProfileLiaOpinionCard` dispara esse fluxo. Há um modal de confirmação (`showUpdateOpinionAlert`) quando já existe um parecer — evita sobrescrever acidentalmente.

**Guard de dados insuficientes:**

```ts
// validateCandidateDataForOpinion(candidate) → DataRequirement[]
// Se requirements.length > 0 → abre InsufficientDataModal ao invés de gerar parecer
```

📋 **Regras de negócio — Pareceres:**

| Regra | Mecanismo |
|---|---|
| Histórico versionado imutável | Cada `POST /parecer` cria nova versão — o backend nunca sobrescreve, apenas cria nova |
| Parecer WSI vs LIA: tipos distintos | `opinion_type` define a renderização do `OpinionCard` |
| Erro de carregamento: fail-loud | `isErrorHistory=true` → `AlertCircle` + botão "Tentar novamente" (não silencia com try/catch) |
| Lazy load: só quando aba ativa | `useEffect` em `useCandidatePreviewCore` — só chama `fetchOpinionsHistory` quando `activeTab === "opinions"` |

---

## 9. Seção LGPD — Consentimentos

**Componente:** `CandidateConsentTab.tsx`
**Acesso:** via `ProfileInfoCards` → `onShowConsentHistory()` (link no card de perfil)

⚠️ **O erro mais comum é** procurar a aba de Consentimento no array `TABS` de `candidate-page.tsx`. Ela **não existe como aba separada** na página full — é acessada via link dentro da aba Perfil, que exibe o `CandidateConsentTab` embutido em `candidate-preview.tsx` (contexto kanban/drawer).

### 9.1 Fetch de consentimentos

```tsx
// CandidateConsentTab.tsx — useQuery do React Query v5
useQuery({
  queryKey: ["candidate-consents", candidateId],
  queryFn: () => fetch(`/api/backend-proxy/observability/consents/${candidateId}`)
             .then(r => r.json()),
})
```

Proxy route: `GET /api/backend-proxy/observability/consents/[candidateId]`
Backend: `GET /api/v1/candidates/{id}/consents` (em `candidates_consent.py:32`)

### 9.2 Estrutura de um consentimento

```ts
interface ConsentRecord {
  id: string
  consent_type: string           // ex: "consentimento_audio", "comunicacao"
  purpose?: string | null
  legal_basis?: string | null
  channel?: string | null        // "chat_web" | "whatsapp" | "chamada_online" | ...
  granted_at?: string | null
  version?: string | null
  is_active: boolean
  revoked_at?: string | null     // se revogado
  expires_at?: string | null
  source?: string | null
}
```

### 9.3 Revogar consentimento

```
DELETE /api/v1/candidates/{id}/consents/{consent_type}
→ Backend: ConsentCheckerService.register_consent(..., consent_given=False, consent_source="candidate_request")
→ Não exclui o registro — cria novo com consent_given=False e revoked_at=now
```

### 9.4 Tipos de consentimento com labels

| consent_type | Label UI |
|---|---|
| consentimento_audio | Áudio da triagem |
| consentimento_audio_revoked | Áudio revogado |
| dados_sensiveis_acao_afirmativa | Dados de ação afirmativa |
| comunicacao | Comunicação |

📋 **Regras de negócio — LGPD:**

| Regra | Mecanismo | Base legal |
|---|---|---|
| Revogação = novo registro (não delete) | `candidates_consent.py:DELETE` → chama `register_consent` com `consent_given=False` | LGPD Art. 18 — direito de revogação com rastreabilidade |
| `consent_type` é a chave de upsert | `ConsentCheckerService.register_consent()` — upsert por `(candidate_id, company_id, consent_type)` | — |
| Consentimento de triagem verificado antes de iniciar sessão | `start_session` verifica `ConsentCheckerService.check_candidate_consent(purpose="ai_screening")` | LGPD Art. 7 — base legal |

---

## 10. Tags e notas

Tags e notas são campos simples do modelo `Candidate`:

```python
# candidate.py (ORM)
tags = Column(ARRAY(String), default=list)   # ex: ["python", "sênior", "indicação"]
notes = Column(Text, nullable=True)           # texto livre
```

Ambos são serializados em `_serialize_candidate()` (crud.py:160):

```python
"tags": c.tags or [],
"notes": c.notes,
```

**No frontend:** tags são exibidas como chips na aba Perfil. Notas aparecem como texto. Edição via `PUT /api/v1/candidates/{id}` com `CandidateUpdate` schema.

⚠️ **O erro mais comum é** tentar usar o `PUT /candidates/{id}` passando `company_id` no body. `CandidateUpdate` herda de `WeDoBaseModel` (extra='forbid') — qualquer campo inesperado gera HTTP 422.

---

## 11. Scores — LIA, WSI, BigFive, DISC

### 11.1 Score LIA

**O que é:** score global de adequação do candidato à vaga ou ao perfil ideal da empresa.

**Localização no modelo:** `candidate.lia_score` (Float) e `candidate.liaAnalysis.score` (na serialização FE).

**Exibição:** `CandidateScoreBadge` (format="percent"):

```ts
// CandidateScoreBadge.tsx
function getScoreColor(score: number, format: "percent"): string {
  if (score >= 80) return "text-status-success"   // verde
  if (score >= 60) return "text-wedo-orange-text" // amarelo
  return "text-status-error"                       // vermelho
}
// formatScore: Math.round(score) + "%"
```

Score null → exibe "—" (em-dash) com classe `text-lia-text-secondary`. Nunca renderiza zero como "0%" — verifica `score == null`.

### 11.2 Score WSI

**O que é:** score da triagem estruturada de entrevista por blocos.

**Escala:** 0-10 (diferente do LIA que é 0-100 em %).

```ts
// CandidateScoreBadge format="wsi"
function getScoreColor(score, "wsi"): string {
  return getWsiScoreColor(score) // WSI_VISUAL_3TIER: verde >=7.5, amarelo >=6.0, vermelho <6.0
}
// formatScore: score.toFixed(1) + "/10"
```

`wsi_score` aparece em `candidate.liaAnalysis` ou via atividade WSI na timeline.

### 11.3 BigFive

Dados em `candidate.bigFiveScores` ou via atividade de assessment. Abertura via `BigFiveModal` (dynamic import):

```tsx
// CandidatePreviewModals.tsx
const BigFiveModal = dynamic(() => import("@/components/big-five-modal")...)
// Aberto por: ActivityEvaluationDetails ou ActivityOtherDetails
// Trigger: onSetBigFiveModalCandidate(candidate) + onSetBigFiveModalOpen(true)
```

### 11.4 DISC

Mesmo padrão do BigFive. `DISCAssessmentModal` (dynamic import). Aberto pela aba Atividades quando o item tem `activity.details.discScores`.

📋 **Regras de negócio — Scores:**

| Regra | Mecanismo |
|---|---|
| LIA score null → "—" não "0%" | `CandidateScoreBadge.tsx:45` — `if (score == null) return <span>—</span>` |
| WSI e decimal usam escala 0-10 | `getWsiScoreColor(score)` de `@/lib/wsi/visual` — thresholds 7.5 / 6.0 |
| BigFive e DISC são modais lazy | `dynamic()` import — não carregam JS até primeira abertura |
| Score LIA no header: de `liaAnalysis.score` | `candidate-page.tsx:101` — `c.liaAnalysis?.score ?? 0` |

---

## 12. Edição inline de campos

**Feature flag:** `NEXT_PUBLIC_FF_CANDIDATE_EDIT=true` (env ou runtime)

**Condição de ativação:** `mode === "page" && isFeatureEnabled(FF_CANDIDATE_EDIT)`

### 12.1 Arquitetura

```
CandidateEditProvider (Context)
├── editable: boolean
├── candidateId: string | undefined
├── updateField(fieldName, value) → Promise<UpdateFieldResult>
└── isSaving(fieldName) → boolean

useCandidateFieldUpdate(candidateId)
├── Rota especial para "name": PUT /candidates/{id}/identity (ORM criptografia-aware)
└── Demais campos: POST /chat/actions/candidate-field-update
    { candidate_id, fields: { [fieldName]: value } }
```

### 12.2 LGPD_BLOCKED_FIELDS

Campos que o hook **recusa editar** (runtime defense-in-depth):

```ts
// use-candidate-field-update.ts:13
export const LGPD_BLOCKED_FIELDS = new Set([
  "race", "raca", "racial_origin",
  "gender", "genero",
  "marital_status", "estado_civil",
  "religion", "religiao",
  "health_data", "dados_saude",
  "ethnic_origin", "origem_etnica",
  "political_opinion", "opiniao_politica",
  "sexual_orientation", "orientacao_sexual",
  "union_membership", "filiacao_sindical",
  "date_of_birth", "data_nascimento",
  "cpf", "rg", "passport",
  "id", "candidate_id", "company_id", "account_id",
  "created_at", "updated_at", "created_by",
])
```

### 12.3 Otimistic update

Após save bem-sucedido: `mutate(["candidate-by-id", candidateId])` (SWR) — revalida o cache e atualiza a UI automaticamente.

📋 **Regras de negócio — Edição:**

| Regra | Mecanismo |
|---|---|
| Edição só em `mode="page"` + FF ativo | `candidate-page.tsx:93` `editableInline = mode === "page" && isFeatureEnabled(FF_CANDIDATE_EDIT)` |
| `name` usa endpoint dedicado | `use-candidate-field-update.ts:53` — rota `/identity` para respeitar EncryptedFieldMixin |
| Campos LGPD bloqueados em runtime | `use-candidate-field-update.ts:31` — `LGPD_BLOCKED_FIELDS.has(fieldName)` retorna `{success:false,error}` |
| Sensor build-time adicional | `check_editable_fields_not_lgpd_sensitive.py` — bloqueia no build antes de runtime |
| Toast de feedback | `sonner` toast.success/error em cada save/fail |

---

# PARTE C — REFERÊNCIA

## 13. Contratos de API (CRUD completo)

Todos os endpoints passam pelo proxy Next.js. O proxy usa `createProxyHandlers` (maioria) ou handler manual (casos especiais).

### 13.1 Endpoints de candidato (CRUD principal)

| Método | Proxy FE | Backend FastAPI | Descrição |
|---|---|---|---|
| GET | `/api/backend-proxy/candidates/[id]` | `GET /api/v1/candidates/{id}` | Perfil completo + PII redaction |
| PUT | `/api/backend-proxy/candidates/[id]` | `PUT /api/v1/candidates/{id}` | Update completo (CandidateUpdate schema) |
| DELETE | `/api/backend-proxy/candidates/[id]` | `DELETE /api/v1/candidates/{id}` | Soft delete (is_active=False) |
| PATCH | `/api/backend-proxy/candidates/[id]/stage` | `PATCH /api/v1/candidates/{id}/stage` | Mover no pipeline (CandidateStageUpdate) |
| PUT | `/api/backend-proxy/candidates/[id]/experiences` | `PUT /api/v1/candidates/{id}/experiences` | Atualizar experiências |
| PUT | `/api/backend-proxy/candidates/[id]/education` | `PUT /api/v1/candidates/{id}/education` | Atualizar formação |
| PUT | `/api/backend-proxy/candidates/[id]/skills` | `PUT /api/v1/candidates/{id}/skills` | Atualizar skills |
| PUT | `/api/backend-proxy/candidates/[id]/certifications` | `PUT /api/v1/candidates/{id}/certifications` | Atualizar certificações |
| PUT | `/api/backend-proxy/candidates/[id]/identity` | `PUT /api/v1/candidates/{id}/identity` | Atualizar nome (criptografado) |

### 13.2 Endpoints de metadados e interação

| Método | Proxy FE | Backend FastAPI | Descrição |
|---|---|---|---|
| POST | `/api/backend-proxy/candidates/[id]/viewed` | `POST /api/v1/candidates/{id}/viewed` | Marcar como visto |
| GET | `/api/backend-proxy/candidates/[id]/favorite` | — | Ver status favorito |
| POST | `/api/backend-proxy/candidates/[id]/favorite` | — | Marcar favorito |
| POST | `/api/backend-proxy/candidates/[id]/hide` | — | Ocultar candidato |
| POST | `/api/backend-proxy/candidates/[id]/quick-ask` | — | Chat rápido sobre candidato |

### 13.3 Endpoints de consentimento LGPD

| Método | Proxy FE | Backend FastAPI | Descrição |
|---|---|---|---|
| GET | `/api/backend-proxy/observability/consents/[candidateId]` | `GET /api/v1/candidates/{id}/consents` | Listar consentimentos |
| POST | `/api/backend-proxy/observability/consents/[candidateId]` | `POST /api/v1/candidates/{id}/consents` | Criar/atualizar consentimento |
| DELETE | `/api/backend-proxy/observability/consents/[candidateId]/revoke` | `DELETE /api/v1/candidates/{id}/consents/{type}` | Revogar consentimento |

### 13.4 Endpoints de opinião/parecer

| Método | Proxy FE | Backend FastAPI | Descrição |
|---|---|---|---|
| GET | `/api/backend-proxy/opinions/candidate/[id]/summary` | `GET /api/v1/opinions/candidate/{id}/summary` | Resumo do parecer atual |
| GET | `/api/backend-proxy/opinions/candidate/[id]/history` | `GET /api/v1/opinions/candidate/{id}/history` | Histórico versionado |
| POST | `/api/backend-proxy/opinions/candidate/[id]/parecer` | `POST /api/v1/opinions/candidate/{id}/parecer` | Gerar novo parecer LIA |

### 13.5 Endpoints de atividades e arquivos

| Método | Proxy FE | Backend FastAPI | Descrição |
|---|---|---|---|
| GET | `/api/backend-proxy/activities?candidate_id={id}` | `GET /api/v1/activities?candidate_id={id}` | Timeline de atividades |
| GET | `/api/backend-proxy/candidates/[id]/files` | `GET /api/v1/candidates/{id}/files` | Listar arquivos |
| POST | `/api/backend-proxy/candidates/[id]/files` | `POST /api/v1/candidates/{id}/files` | Upload de arquivo |
| DELETE | `/api/backend-proxy/candidates/[id]/files/[attachmentId]` | `DELETE /api/v1/candidates/{id}/files/{attachmentId}` | Deletar arquivo |

### 13.6 Envelope de resposta

O endpoint `GET /candidates/{id}` retorna `ResponseEnvelope`:

```json
{
  "ok": true,
  "data": { ...candidate_dict... },
  "meta": { "source": "local" }
}
```

`liaApi.getCandidate()` desembrulha o envelope automaticamente.

### 13.7 Validação de stage update — LGPD art. 20

```python
# candidates_crud.py:PATCH stage
# Rejeição de candidato EXIGE user_id (revisão humana obrigatória):
if is_rejection and not stage_data.user_id:
    raise HTTPException(422, {
      "error": "human_review_required",
      "compliance": ["LGPD art. 20", "EU AI Act art. 14"]
    })

# Rejeição com motivo discriminatório (FairnessGuard):
if is_rejection and stage_data.sub_status:
    fg_rejection = check_rejection_reason(...)
    if fg_rejection.is_blocked:
        raise HTTPException(422, {
          "error": "fairness_blocked",
          "compliance": ["Lei 9.029/95", "CLT Art. 373-A"]
        })
```

---

## 14. Schema do modelo de candidato

### 14.1 Campos principais do ORM (`libs/models/lia_models/candidate.py`)

```python
class Candidate(EncryptedFieldMixin, Base):
    __tablename__ = "candidates"

    # PII criptografados (Fernet at rest, SHA-256 hash para busca)
    # Acesso via hybrid_property que decripta automaticamente:
    name    # _name_raw + _name_encrypted
    email   # _email_raw + _email_encrypted + email_hash
    cpf     # _cpf_raw + _cpf_encrypted + cpf_hash
    phone   # _phone_raw + _phone_encrypted + phone_hash

    # Identificação
    id: UUID (PK)
    headline: String(255)
    current_title: String(255)
    current_company: String(255)
    seniority_level: String(50)
    years_of_experience: Integer

    # Contato
    secondary_email: String(255)    # LGPD sensitive
    mobile_phone: String(50)
    secondary_phone: String(50)     # LGPD sensitive
    linkedin_url: String(500)
    github_url: String(255)
    portfolio_url: String(255)

    # Localização
    location_city: String(100)
    location_state: String(50)
    location_country: String(50)
    address_street: String(255)     # LGPD sensitive
    address_number: String(20)      # LGPD sensitive
    address_district: String(100)
    address_zip: String(20)         # LGPD sensitive
    address_complement: String(100) # LGPD sensitive

    # Preferências de trabalho
    is_remote: Boolean
    willing_to_relocate: Boolean
    mobility: String(50)
    work_model_preference: String(50)
    contract_type_preference: String(50)

    # Dados financeiros (LGPD sensitive — gated por can_view_salary)
    current_salary: Float
    desired_salary_min: Float
    desired_salary_max: Float
    salary_currency: String(10)
    salary_expectation_clt: Float
    salary_expectation_pj: Float
    salary_expectation_freelance: Float

    # Skills e qualificação
    technical_skills: ARRAY(String)
    soft_skills: ARRAY(String)
    languages: JSON           # {lingua: nivel}
    certifications: JSON[]
    interests: ARRAY(String)
    expertise: JSON

    # Histórico (snapshots)
    work_history: JSON[]      # experiências profissionais
    education_snapshot: JSON[]  # educação

    # Score e análise LIA
    lia_score: Float           # 0-100
    lia_insights: JSON
    skills_match_percentage: Float

    # Status no pipeline
    status: String(50)
    is_active: Boolean
    is_blacklisted: Boolean
    blacklist_reason: String(255)

    # Gestão
    tags: ARRAY(String)
    notes: Text
    additional_data: JSON

    # Origem
    source: String(100)       # "ats", "manual", "pearch", "cv_upload"
    ats_source_name: String(100)
    ats_candidate_id: String(255)
    pearch_profile_id: String(255)

    # Auditoria
    created_at: DateTime
    updated_at: DateTime
    last_contacted_at: DateTime
    last_activity_at: DateTime
```

### 14.2 PII encryption status

```python
# EncryptedFieldMixin.py (_pii_encrypt_fields em Candidate)
# (raw_attr, enc_attr, hash_attr) — hash=None quando não há busca por hash
("_email_raw", "_email_encrypted", "email_hash"),
("_cpf_raw",   "_cpf_encrypted",   "cpf_hash"),
("_name_raw",  "_name_encrypted",  None),      # name search degradada pós-migração
("_phone_raw", "_phone_encrypted", "phone_hash"),
```

Pre-migração: rows com plaintext nos campos raw. Pós-migração (quando `pii.backfill_encrypt_existing` completa): raw columns ficam NULL, criptografado em `*_encrypted`.

### 14.3 CandidateUpdate schema

```python
class CandidateUpdate(WeDoBaseModel):  # extra='forbid'
    name: Optional[str] = None
    headline: Optional[str] = None
    current_title: Optional[str] = None
    # ... todos os campos editáveis
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    # NÃO inclui: company_id, id, created_at, updated_at
```

---

## 15. PII por campo: visibilidade por papel de usuário

### 15.1 Arquitetura (A4 — 2026-06-06)

A visibilidade de PII é resolvida em três camadas:

```
Precedência (por campo): user override > role default > legacy bucket > show

resolve_pii_field_visibility(current_user, role_defaults)
→ Retorna: { fieldName: bool (can_view) }
→ Source: app/shared/rbac/pii_field_resolver.py
→ Catalog: app/shared/rbac/pii_field_catalog.py
```

### 15.2 Grupos de campos PII

| Grupo | Campos | Gate legado |
|---|---|---|
| salary | current_salary, desired_salary_*, salary_expectation_* | `can_view_salary` (Sprint 5) |
| sensitive_pii | cpf, date_of_birth, address_*, secondary_email, secondary_phone, personal_emails, business_emails, best_personal_email, best_business_email | `can_view_sensitive_pii` (Sprint 8) |

### 15.3 Flags de masking no JSON de resposta

```json
{
  "salary_masked": true,        // quando campos de salary estão nullados
  "sensitive_pii_masked": true  // quando CPF/endereço/etc estão nullados
}
```

UI usa esses flags para exibir "Restrito" em vez de valor vazio.

### 15.4 Audit trail

```python
# candidates_crud.py:290
async def _audit_pii_access(current_user, candidate_id, company_id, role_defaults):
    # Log SOXAuditLog quando privilegiado acessa PII não-mascarado
    # LGPD Art. 37 V — rastreabilidade de acesso
```

### 15.5 Chat masking de PII (ADR-002)

No chat SSE/WS, CPF/RG/CNPJ são mascarados antes de enviar ao LLM vendor (`strip_pii_for_llm_prompt`), mas o recrutador autenticado **vê** o dado completo (ADR-LGPD-002: PII operacional ≠ classe protegida).

---

## 16. Componentes & estado (frontend)

### 16.1 Mapa de componentes

```
candidate-page.tsx                    ← raiz do componente polimórfico
├── CandidateEditProvider             ← Context: edição inline
├── useCandidatePreviewCore           ← state central (tabs, modais, opinions, files)
├── useCandidateFieldUpdate           ← mutations de campo
│
├── CandidatePageHeader.tsx           ← identidade + ações (usa CandidateEditContext)
│   ├── CandidateAvatar               ← avatar com fallback inicial
│   ├── CandidateScoreBadge           ← score LIA em %
│   └── EditableField[]               ← inputs inline (quando editable)
│
├── Tabs [profile|activities|files|opinions]
│   ├── CandidatePreviewProfileTab    ← aba Perfil Completo
│   │   ├── ExperienceHighlightCard
│   │   ├── QualificationMatrixCard
│   │   ├── EligibilityResultsSection
│   │   ├── ProfileLiaOpinionCard
│   │   ├── ProfileSkillsMapCard
│   │   ├── ProfileExperienceCards
│   │   └── ProfileInfoCards          ← educação, salário, LGPD link
│   │
│   ├── CandidateActivitiesTab        ← aba Atividades
│   │   ├── ActivityFilters
│   │   └── ActivityTimeline
│   │       ├── ActivityEvaluationDetails
│   │       ├── ActivityExpandedDetails
│   │       └── ActivityOtherDetails / ActivityAssessmentDetails
│   │
│   ├── CandidateFilesTab             ← aba Arquivos
│   │   └── FilePreviewModal
│   │
│   └── CandidateOpinionsTab          ← aba Pareceres
│       └── OpinionCard[]
│
├── [mode=page] CandidatePageSummary  ← aside sticky col-span-2/5 (lg+)
│
└── CandidatePreviewModals            ← modais lazy (BigFive, DISC, LIA chat, Screening)
    ├── LiaChatModal
    ├── BigFiveModal        (dynamic)
    ├── DISCAssessmentModal (dynamic)
    └── ScreeningMediaModal (dynamic)
```

### 16.2 Estado em useCandidatePreviewCore

```ts
// useCandidatePreviewCore.tsx
activeTab: 'profile' | 'activities' | 'files' | 'opinions'
showLiaModal: boolean
isAnalyzingWithLia: boolean
lastAnalysisDate: Date | null
opinionsData: Record<string, unknown> | null      // summary do parecer atual
isLoadingOpinions: boolean
opinionsHistory: Record<string, unknown>[]        // histórico versionado
isLoadingHistory: boolean
isErrorHistory: boolean
expandedOpinionId: string | null
screeningModalOpen: boolean
discModalOpen: boolean / discModalData
bigFiveModalOpen: boolean / bigFiveModalCandidate
showUpdateOpinionAlert: boolean
showInsufficientDataModal: boolean / dataRequirements
```

### 16.3 Layout grid (mode=page, lg+)

```tsx
// candidate-page.tsx:163
// F9 Item 3: grid 5 colunas no lg+
<div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
  <div className="lg:col-span-3 min-w-0">   ← tabs (Perfil/Atividades/Arquivos/Pareceres)
    {/* conteúdo da aba ativa */}
  </div>
  <aside className="lg:col-span-2 lg:sticky lg:top-4 lg:self-start min-w-0">
    <CandidatePageSummary ... />              ← painel lateral sticky
  </aside>
</div>
```

Em `mode="modal"` ou viewport < lg: layout single-column sem grid.

### 16.4 SWR cache keys

| Key | Dado | Invalidação |
|---|---|---|
| `["candidate-by-id", id]` | Perfil completo | `mutate(["candidate-by-id", id])` após field update |
| `["candidate-consents", id]` | Consentimentos LGPD | React Query — invalidate após revogação |

### 16.5 CandidatePageSummary — painel lateral sticky

```tsx
// CandidatePageSummary.tsx
// Exibe: avatar, nome, ID, cargo, score badge, stage chip, contatos, links sociais
// Read-only: não tem edição inline (header é a superfície de ação)

// Lógica de stage chip:
stage = candidate.pipeline_stage ?? candidate.kanban_stage ?? candidate.current_stage ?? candidate.stage
// Quando sem stage (rota standalone / talent pool):
// is_blacklisted → chip "Bloqueado" (danger)
// is_hired → chip "Contratado · {hired_job_title}" (success)
// else → sem chip (active = noise)
```

---

## 17. 📋 Quadro-resumo de regras de negócio

| # | Regra | Mecanismo / Evidência | LGPD/Compliance |
|---|---|---|---|
| R1 | `company_id` SEMPRE do JWT | `Depends(require_company_id)` em todos os endpoints | Multi-tenancy |
| R2 | Candidato de outro dept = 404, não 403 | `_filter_candidates_by_dept_scope()` crud.py:342 — soft 404 evita leakage | Privacy by design |
| R3 | PII financeiro mascarado por role | `apply_pii_field_visibility()` crud.py:253 — field-level, precedência user > role | LGPD Art. 6 III minimização |
| R4 | PII sensível (CPF, endereço) mascarado por role | `_redact_sensitive_pii_for_user()` crud.py:228 | LGPD Art. 5 II |
| R5 | Audit trail de acesso privilegiado a PII | `_audit_pii_access()` crud.py:290 — log SOXAuditLog | LGPD Art. 37 V |
| R6 | Rejeição exige `user_id` (revisão humana) | `update_candidate_stage()` crud.py:737 — HTTP 422 sem user_id | LGPD art. 20, EU AI Act art. 14 |
| R7 | FairnessGuard bloqueia motivo de rejeição discriminatório | `check_rejection_reason()` crud.py:756 — HTTP 422 fairness_blocked | Lei 9.029/95, CLT Art. 373-A |
| R8 | Revogação de consentimento = novo registro (não delete) | `candidates_consent.py:DELETE` → upsert consent_given=False | LGPD Art. 18 |
| R9 | Parecer LIA cria versão nova (imutável) | `POST /parecer` — nunca sobrescreve versão anterior | Auditabilidade |
| R10 | Edição inline bloqueada para campos LGPD-sensíveis | `LGPD_BLOCKED_FIELDS` em `use-candidate-field-update.ts:13` | LGPD Art. 5 II |
| R11 | Nome usa endpoint criptografia-aware | `use-candidate-field-update.ts:53` → `/identity` (EncryptedFieldMixin) | — |
| R12 | LIA score null exibe "—" nunca "0%" | `CandidateScoreBadge.tsx:45` — `if (score == null) return <span>—</span>` | — |
| R13 | WSI escala 0-10, LIA escala 0-100 (%) | `CandidateScoreBadge` format="wsi"\|"percent" — thresholds distintos | — |
| R14 | Chat masking: CPF/RG/CNPJ strippados para LLM vendor | `strip_pii_for_llm_prompt()` — recrutador VÊ, LLM NÃO VÊ | ADR-LGPD-002 |
| R15 | Rails eliminado: `RAILS_ENABLED=False` | sem `RAILS_API_URL` no env; `enforce_candidates_deprecation` serve como shim | — |
| R16 | `CandidateUpdate` rejeita campos extras | `WeDoBaseModel` (extra='forbid') — HTTP 422 em campo inesperado | — |
| R17 | Opinião Summary carrega ao montar; History apenas na aba | `useCandidatePreviewCore` useEffect lazy — evita fetch desnecessário | Performance |
| R18 | Atividades sem company_id no request FE | `use-candidate-activities.ts:56` — só `candidate_id` na query; `company_id` via JWT | Multi-tenancy |

---

## 18. Checklist de replicação

### Frontend

- [ ] Criar rota `[locale]/(dashboard)/funil-de-talentos/candidato/[id]/page.tsx` com `ErrorBoundarySection`
- [ ] Criar `CandidateRoutePage.tsx` com `useParams` + `useCandidateForPage`
- [ ] Implementar `useCandidateForPage` (SWR, key `["candidate-by-id", id]`, `liaApi.getCandidate`)
- [ ] Implementar `CandidatePage` com props `mode`, `isOpen`, `onClose`, callbacks de ação
- [ ] Implementar `CandidateEditProvider` + `useCandidateEdit` Context
- [ ] Implementar `useCandidateFieldUpdate` com `LGPD_BLOCKED_FIELDS` e rota especial para `name`
- [ ] Implementar `CandidatePageHeader` (avatar, score, edição inline, ações rápidas)
- [ ] Implementar `CandidatePageSummary` (aside sticky, stage chip, contatos)
- [ ] Implementar tabs: `CandidatePreviewProfileTab`, `CandidateActivitiesTab`, `CandidateFilesTab`, `CandidateOpinionsTab`
- [ ] Implementar `CandidateScoreBadge` com null-safety e formatos percent/wsi/decimal
- [ ] Implementar `CandidateConsentTab` com React Query + revogação
- [ ] Implementar `useCandidateActivities` (GET `/activities?candidate_id=`)
- [ ] Implementar `useCandidateFiles` com upload/download/delete
- [ ] Configurar dynamic imports para BigFiveModal, DISCAssessmentModal, ScreeningMediaModal
- [ ] Configurar proxy routes em `/api/backend-proxy/candidates/[id]/` e subrotas
- [ ] Configurar feature flag `FF_CANDIDATE_EDIT` (default: false em production)
- [ ] Implementar layout 2-col `lg:grid-cols-5` (col-span-3/2) só em `mode="page"`

### Backend

- [ ] Endpoint `GET /api/v1/candidates/{id}` com `apply_pii_field_visibility` e `_audit_pii_access`
- [ ] Endpoint `PUT /api/v1/candidates/{id}` com `WeDoBaseModel` (extra='forbid')
- [ ] Endpoint `PATCH /api/v1/candidates/{id}/stage` com FairnessGuard + human_review_required gate
- [ ] Endpoints `/experiences`, `/education`, `/skills`, `/certifications`, `/identity`
- [ ] Endpoints LGPD: `GET/POST /consents`, `DELETE /consents/{type}` (upsert, nunca delete)
- [ ] Endpoint `/files` com upload/download/delete
- [ ] Endpoint `GET /activities?candidate_id=` filtrado por company_id
- [ ] Endpoint `GET/POST /opinions/candidate/{id}/history|summary|parecer`
- [ ] `EncryptedFieldMixin` para name/email/cpf/phone (Fernet + SHA-256 hash)
- [ ] `CandidateRepository._require_company_id` em todos os métodos públicos
- [ ] `LGPD_BLOCKED_FIELDS` check também no backend (defense-in-depth)
- [ ] `ConsentCheckerService.check_candidate_consent` antes de iniciar triagem
- [ ] FairnessGuard wired em `check_rejection_reason` (rejeição de candidato)

### LGPD e Compliance

- [ ] `pii_field_catalog.py` com grupos salary e sensitive_pii
- [ ] `pii_field_resolver.py` com precedência user > role > legacy > show
- [ ] `HiringPolicy.pii_visibility_defaults` configurável por empresa
- [ ] Audit log em acesso privilegiado a PII (Art. 37 V)
- [ ] FairnessGuard no endpoint de rejeição (Art. 373-A CLT)
- [ ] `user_id` obrigatório em rejeições (LGPD Art. 20)
- [ ] Consentimento LGPD verificado antes de iniciar triagem de IA

---

## 19. Glossário

| Termo | Definição |
|---|---|
| **mode="page"** | Layout standalone com URL dedicada, aside sticky, edição inline habilitável |
| **mode="modal"** | Overlay de tela cheia sobre o kanban — mesmo componente, sem aside, sem edição inline |
| **Parecer LIA** | Análise gerada pela LIA sobre o fit do candidato para uma vaga. Versionado e imutável. |
| **Opinion Summary** | Resumo do parecer mais recente — inclui score_breakdown.qualification_matrix |
| **Opinion History** | Lista versionada de pareceres — general (LIA vs vaga) + wsi (triagem estruturada) |
| **PII at rest** | name, email, CPF, phone criptografados via Fernet (EncryptedFieldMixin) no banco |
| **salary_masked** | Flag no JSON de resposta — true quando campos financeiros foram nullados por RBAC |
| **sensitive_pii_masked** | Flag no JSON — true quando CPF, endereço, secondary contacts foram nullados |
| **LGPD_BLOCKED_FIELDS** | Set de nomes de campos que o hook de edição inline recusa atualizar |
| **FairnessGuard** | Módulo que detecta termos discriminatórios em motivos de rejeição (CLT 373-A) |
| **human_review_required** | Erro 422 retornado quando rejeição automática sem `user_id` (LGPD art. 20) |
| **enforce_candidates_deprecation** | Middleware de deprecation — adiciona headers mas não bloqueia (sem `STRICT_RAILS_ONLY=true`) |
| **ExperienceHighlightCard** | Card gerado por LIA com highlights da experiência do candidato (lazy, por companyId) |
| **QualificationMatrixCard** | Matriz de qualificação: grouped (do parecer salvo) ou flat (da busca ativa) |
| **EligibilityResultsSection** | Resultados de perguntas eliminatórias da vaga — shape canônico EligibilityQuestionItem |
| **dept scope** | Visibilidade de candidatos limitada ao departamento do recrutador (Sprint 2 RBAC, soft-launch) |

---

## 20. Gaps & pontos de atenção

### G1 — Aba Consentimento não está no array TABS da candidate-page

A `CandidateConsentTab` existe mas **não é uma aba da candidate-page.tsx**. Está integrada em `candidate-preview.tsx` (contexto kanban/drawer). Na rota standalone, o acesso é via link em `ProfileInfoCards` que chama `onShowConsentHistory()`. Se precisar expor como aba própria na rota standalone, adicionar ao array `TABS` e passar `candidateId` como prop.

### G2 — Edição inline desabilitada por padrão (FF)

`FF_CANDIDATE_EDIT` default é `false`. A edição inline só aparece em `mode="page"` E com flag ativa. Em produção sem a flag, os campos são read-only mesmo em rota standalone.

### G3 — PII encryption: busca por nome degradada pós-migração

`_name_raw` fica NULL após migração 111. Queries ILIKE em `name` só funcionam em rows pré-migração. Post-backfill, busca por nome precisa de índice full-text ou trigram.

### G4 — enforce_candidates_deprecation: shim Rails sem kill-switch

O router de CRUD de candidatos carrega `enforce_candidates_deprecation`. Sem `STRICT_RAILS_ONLY=true`, apenas adiciona headers Deprecation/Sunset mas não bloqueia. O Python CRUD é a fonte ativa (Rails eliminado).

### G5 — useCandidateActivities: fallback silencioso em erro

O hook `use-candidate-activities.ts` captura erros via `try/catch` mas renderiza array vazio sem toast visível. Se a timeline aparecer vazia e o candidato tem atividades, verificar os logs do proxy.

### G6 — BigFive e DISC: dados não persistem no perfil

BigFive e DISC scores aparecem somente via atividades na timeline. Não há campo canônico dedicado no modelo `Candidate` para os scores de assessments — vivem em `activity.details.bigFiveScores` ou `activity.details.discScores`.

### G7 — CandidatePageSummary: stage chip prioriza kanban sobre global state

Se o candidato vem do kanban, `pipeline_stage` tem valor. Se vem da rota standalone (talent pool), `pipeline_stage` é undefined e o chip usa `is_hired`/`is_blacklisted`. Candidato ativo sem stage específico não exibe chip (design intencional).

### G8 — Consentimento: `CandidateConsentTab` usa React Query, não SWR

Diferença de paradigma: a aba de consentimento usa `@tanstack/react-query` com `SETTINGS_QUERY_KEYS`. O restante da página usa SWR. Invalidação de cache após revogação precisa de `queryClient.invalidateQueries(["candidate-consents", id])`.

### G9 — Opinião Summary: `company_id` passado como query param

```ts
// useCandidatePreviewCore.tsx:fetchOpinionsSummary
GET /api/backend-proxy/opinions/candidate/{id}/summary?company_id={cid}
```

O proxy de opiniões aceita `company_id` como query param (resolve via `resolveCompanyId`). Diferente dos endpoints de candidato que usam JWT puro. Histórico: endpoint de opiniões não usa `require_company_id` no mesmo padrão.

### G10 — Layout 2-col: apenas lg+ e mode="page"

Em mobile ou mode="modal", `CandidatePageSummary` não renderiza. O conteúdo é single-column. Qualquer feature que dependa do painel lateral só funciona em desktop + rota standalone.
