# Handoff — Preview de Candidato: Painel Lateral de Detalhes

> **Objetivo deste documento:** permitir que um time de devs **replique do zero**, em outro ambiente, o **painel lateral de preview de candidato** — incluindo seus 3 contextos de uso (Funil de Talentos, Kanban de Vaga e CandidatePreviewPanel legado), todos os sub-componentes (Header, ActionBar, PipelineDecisionBar, abas Perfil / Atividades / Arquivos / Pareceres / Consentimento) e a lógica de backend (endpoint `GET /candidates/{id}`, PII redaction por papel, opiniões da IA).
>
> **Fora de escopo:** a página full de candidato (rota `/pt/candidatos/{id}`), o modal de triagem WSI, o modal DISC e o modal BigFive — esses são disparados *a partir* do preview mas têm handoff próprio.
>
> **Como ler:** a **Parte A** descreve arquitetura e fluxos end-to-end. A **Parte B** cobre a anatomia de cada sub-componente. A **Parte C** é material de referência (contratos de API, PII, scores, checklist). Cada funcionalidade traz blocos `⚠️` com os erros mais comuns. O §13 consolida todas as regras num quadro-resumo.
>
> **Stack:** Next.js 15 (App Router) · FastAPI + PostgreSQL (`lia-agent-system`) · Zustand · React Query v5 · Tanstack Query

---

## Índice

**Parte A — Arquitetura & Fluxos**
1. [Visão geral & arquitetura](#1-visão-geral--arquitetura)
2. [Onde o preview aparece — 3 contextos](#2-onde-o-preview-aparece--3-contextos)
3. [Fluxo de hidratação de dados](#3-fluxo-de-hidratação-de-dados)

**Parte B — Anatomia do Preview**
4. [Header — dados sempre visíveis](#4-header--dados-sempre-visíveis)
5. [ActionBar — ações inline](#5-actionbar--ações-inline)
6. [PipelineDecisionBar — movimentação de pipeline](#6-pipelinedecisionbar--movimentação-de-pipeline)
7. [Aba Perfil](#7-aba-perfil)
8. [Aba Atividades](#8-aba-atividades)
9. [Aba Arquivos](#9-aba-arquivos)
10. [Aba Pareceres e Análises](#10-aba-pareceres-e-análises)
11. [Aba Consentimento](#11-aba-consentimento)
12. [Modais disparados a partir do preview](#12-modais-disparados-a-partir-do-preview)

**Parte C — Referência**
13. [📋 Quadro-resumo de regras de negócio](#13--quadro-resumo-de-regras-de-negócio)
14. [PII Visibility — campos por papel de usuário](#14-pii-visibility--campos-por-papel-de-usuário)
15. [Score LIA vs Score WSI no preview](#15-score-lia-vs-score-wsi-no-preview)
16. [Contratos de API](#16-contratos-de-api)
17. [Componentes & estado (frontend)](#17-componentes--estado-frontend)
18. [Checklist de replicação](#18-checklist-de-replicação-em-outro-ambiente)
19. [Glossário](#19-glossário)
20. [Gaps & pontos de atenção](#20-gaps--pontos-de-atenção)

---

# PARTE A — ARQUITETURA & FLUXOS

## 1. Visão geral & arquitetura

O preview de candidato é um **painel lateral deslizante** que mostra os detalhes de um candidato sem sair da tela atual. Ele é renderizado ao lado da lista/tabela principal e recebe o objeto `candidate` diretamente da store/estado da tela pai — **não faz fetch próprio do candidato no mount**; os dados já foram carregados pela busca ou pelo kanban.

```
┌─ Tela pai (Funil / Kanban) ─────────────────────────────────────────────┐
│                                                                          │
│  ┌─── Lista de candidatos ────────┐  ┌──── Preview (painel lateral) ────┐ │
│  │  card candidato A              │  │  CandidatePreview                │ │
│  │  card candidato B  ← click     │  │  ├─ Header                      │ │
│  │  card candidato C              │  │  ├─ ActionBar                   │ │
│  └────────────────────────────────┘  │  ├─ PipelineDecisionBar(*)      │ │
│                                      │  ├─ Tab bar (5 abas)            │ │
│                                      │  └─ Tab content                 │ │
│                                      └──────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
(*) só aparece quando jobId / vacancy_candidate_id está presente
```

### Componentes por camada

| Camada | Arquivo principal | Papel |
|---|---|---|
| Container Funil | `CandidatePreviewSidePanel.tsx` | Wrapper com resize drag, `h-[calc(100vh-6rem)]` |
| Container Kanban | `KanbanCandidatePreviewPanel.tsx` | Wrapper com resize próprio (360–700px), `React.Suspense` |
| Container Legado | `CandidatePreviewPanel.tsx` | Preview simplificado, usado em telas mais antigas (sem `useCandidatePreviewCore`) |
| Preview raiz | `candidate-preview.tsx` (barrel: `index.ts`) | Orquestra todos os sub-componentes; chama `useCandidatePreviewCore` |
| Hook de estado | `useCandidatePreviewCore.tsx` | Único dono de estado: tabs, modais, opiniões, LIA chat |

### Fluxo de dados simplificado

```
click no card
    → setPreviewCandidate(candidate)  [estado da tela pai]
    → CandidatePreview recebe candidate como prop
    → useCandidatePreviewCore(candidate, jobId) monta
        → useEffect: fetchOpinionsSummary()   [mount]
        → useEffect: fetchOpinionsHistory()   [ao mudar para aba "opinions"]
    → cada sub-componente recebe dados via props do core
```

⚠️ **O erro mais comum é achar que o preview faz fetch do candidato.** Ele **não faz**. O objeto `candidate` chega pronto da tela pai (resultado de busca, dado do kanban). O preview apenas busca *informações adicionais* (opiniões, histórico de atividades, arquivos, consentimentos) a partir do `candidateId` já presente no objeto.

---

## 2. Onde o preview aparece — 3 contextos

### 2.1 Funil de Talentos (`/pt/funil`)

**Wrapper:** `CandidatePreviewSidePanel.tsx`
(`plataforma-lia/src/components/pages/candidates/CandidatePreviewSidePanel.tsx`)

- Ativado por `showCandidatePreview` (estado local em `useCandidatesPageCore`)
- Largura controlada por `previewWidth` (state do pai) com handle de drag
- Recebe `searchCriteria` → passado para `CandidatePreview` → repassado para `QualificationMatrixCard`
- **Não passa `jobId`** (contexto de busca livre, sem vaga específica)

```tsx
// CandidatePreviewSidePanel.tsx:68
<div data-testid="candidate-preview-side-panel"
     className="flex-shrink-0 relative"
     style={{ width: `${previewWidth}px` }}>
```

### 2.2 Kanban de Vaga (`/pt/recrutar/[jobId]`)

**Wrapper:** `KanbanCandidatePreviewPanel.tsx`
(`plataforma-lia/src/components/pages/job-kanban/KanbanCandidatePreviewPanel.tsx`)

- Largura: `PANEL_MIN_WIDTH=360`, `PANEL_DEFAULT_WIDTH=480`, `PANEL_MAX_WIDTH=700`
- Resize é gerenciado *internamente* no componente (não herda do pai)
- **Passa `jobId={jobVacancyId}`** → ativa a `PipelineDecisionBar` e o parecer por vaga
- Usa `React.Suspense` (não `dynamic()`) para lazy load do `CandidatePreview`
- Deriva `candidates` e `currentIndex` filtrando `candidatesData` pela coluna do candidato atual

```tsx
// KanbanCandidatePreviewPanel.tsx:20-22
const PANEL_MIN_WIDTH = 360
const PANEL_MAX_WIDTH = 700
const PANEL_DEFAULT_WIDTH = 480
```

### 2.3 CandidatePreviewPanel — contexto legado

**Arquivo:** `CandidatePreviewPanel.tsx`
(`plataforma-lia/src/components/pages/candidates/CandidatePreviewPanel.tsx`)

- Versão simplificada que **não usa** `useCandidatePreviewCore`
- 4 abas fixas com dados fictícios/hardcoded na aba `experience` e `skills`
- Score mostrado como `formatScorePercent(candidate.score)` (campo único, sem distinção WSI/geral)
- Inclui `LIAFeedbackWidget` e `CandidateChatPopover`
- Usado em contextos mais antigos da plataforma

⚠️ **O erro mais comum é usar `CandidatePreviewPanel` em lugar de `CandidatePreview`.** O `CandidatePreviewPanel` tem dados hardcoded e não reflete informações reais do candidato nas abas de experiência e skills.

---

## 3. Fluxo de hidratação de dados

### 3.1 Dados que chegam via prop (sem fetch adicional)

O objeto `candidate` passado como prop já contém todos estes campos (vindos do endpoint de busca ou do kanban):

- Dados de identidade: `name`, `id`, `email`, `phone`, `avatar_url`, `position`, `location`
- Dados profissionais: `work_history[]`, `education[]`, `skills[]`, `certifications[]`
- Metadados: `seniority_level`, `years_of_experience`, `enrichment_source`, `is_enriching`
- Links sociais: `linkedin`, `github`, `stackoverflow`, `twitter`/`x_url`, `behance`, `portfolio`
- Datas: `created_at`, `updated_at`, `last_contacted_at`
- Flags de consentimento: `communication_consent`
- Dados de pipeline (quando vem do kanban): `vacancy_id`, `vacancy_candidate_id`, `stage`, `status`

### 3.2 Dados buscados pelo useCandidatePreviewCore (lazy)

| Dado | Endpoint | Quando busca |
|---|---|---|
| Sumário de opiniões | `GET /api/backend-proxy/opinions/candidate/{id}/summary?company_id=X` | No mount (useEffect) |
| Histórico de opiniões | `GET /api/backend-proxy/opinions/candidate/{id}/history?company_id=X` | Ao entrar na aba "opinions" |

### 3.3 Dados buscados por sub-componentes (independentemente)

| Componente | Endpoint | Quando busca |
|---|---|---|
| `PipelineDecisionBar` | `GET /api/backend-proxy/jobs/{jobId}/pipeline` | No mount (quando `effectiveJobId` existe) |
| `PipelineDecisionBar` | `GET /api/backend-proxy/interviews?candidate_id=X&status=scheduled` | No mount |
| `PipelineDecisionBar` | `GET /api/backend-proxy/opinions/candidate/{id}/summary` | No mount (para highlight) |
| `CandidateConsentTab` | `GET /api/backend-proxy/observability/consents/{candidateId}` | No mount da aba |
| `QualificationMatrixCard` | `GET /api/backend-proxy/candidates/{id}/criteria-match` (on-the-fly) | Quando sem matrix e com searchCriteria ou jobId |

### 3.4 Normalização de arrays no mount

Logo após receber o `candidate` prop, o componente raiz normaliza campos que podem vir como objeto único ou array:

```tsx
// candidate-preview.tsx:112-120
candidate = {
  ...candidate,
  education:      Array.isArray(candidate.education)      ? candidate.education      : (candidate.education      ? [candidate.education]      : []),
  workHistory:    Array.isArray(candidate.work_history)   ? candidate.work_history   : (candidate.work_history   ? [candidate.work_history]   : []),
  skills:         Array.isArray(candidate.skills)         ? candidate.skills         : (candidate.skills         ? [candidate.skills]         : []),
  certifications: Array.isArray(candidate.certifications) ? candidate.certifications : (candidate.certifications ? [candidate.certifications] : []),
  projects:       Array.isArray(candidate.projects)       ? candidate.projects       : (candidate.projects       ? [candidate.projects]       : []),
  awards:         Array.isArray(candidate.awards)         ? candidate.awards         : (candidate.awards         ? [candidate.awards]         : []),
}
```

---

# PARTE B — ANATOMIA DO PREVIEW

## 4. Header — dados sempre visíveis

**Arquivo:** `CandidatePreviewHeader.tsx`
(`plataforma-lia/src/components/candidate-preview/CandidatePreviewHeader.tsx`)

### 4.1 Estrutura visual

```
┌─────────────────────────────────────────────────────────────┐
│  [Avatar]  Nome                 [ID] [Sênior] [X anos]      │
│            Cargo • Empresa • Segmento                        │
│            ✉ email (lápis)  📞 telefone (lápis)            │
│            📅 cadastro  🕐 atualizado  💬 último contato    │
│                                               [↗] [✕]       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Chips de status no header

| Chip | Campo fonte | Cor | Condição de exibição |
|---|---|---|---|
| ID curto (`AB1234`) | `generateShortId(name, id)` | Neutro | Sempre |
| Nível de senioridade | `seniority_level` / `seniorityLevel` | Warning (âmbar) | Quando presente |
| Anos de experiência | `years_of_experience` / `yearsOfExperience` | Neutro | Quando presente e não null |
| Consent. com. | `communication_consent` | Depende do valor | Quando campo presente |
| Consent. audio OK | prop `hasAudioConsent=true` | Verde | Quando `hasAudioConsent === true` |
| Sem consent. audio | prop `hasAudioConsent=false` | Neutro | Quando `hasAudioConsent === false` |
| Enriquecendo... | `is_enriching` | Warning + animate-pulse | Quando `is_enriching === true` |
| Fonte (Apify/Pearch/Local) | `enrichment_source` | Cores específicas por fonte | Quando presente e não enriquecendo |

### 4.3 Cores por fonte de enriquecimento

```tsx
// CandidatePreviewHeader.tsx:204-211
src === 'apify'  → 'bg-wedo-orange/15 text-wedo-orange-text border-wedo-orange/30'
src === 'pearch' → 'bg-wedo-cyan/15 text-wedo-cyan-text border-wedo-cyan/30'
src === 'local'  → 'bg-stone-400/15 text-stone-500 border-stone-400/30'
```

### 4.4 Edição inline de contato (ContactField)

O header contém dois `ContactField` (email e telefone) com lápis on-hover. Ao clicar no lápis, abre um `Popover` ancorado com input e botões Salvar/Cancelar.

**Endpoint de salvamento:** `POST /api/backend-proxy/chat/actions/candidate-field-update`
(`lia-agent-system/app/api/v1/chat.py:1146`)

```json
{
  "candidate_id": "<uuid>",
  "fields": { "email": "novo@email.com" }
}
```

⚠️ **O erro mais comum é apontar para o proxy Rails `/api/backend-proxy/candidates/{id}`.** O endpoint correto para editar email/telefone é o FastAPI `chat/actions/candidate-field-update`. O comentário no arquivo marca a correção do bug F11 (2026-05-24): o Rails estava offline no Replit dev.

**Validação de email:** regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` feita no FE antes do POST.

**Optimistic update:** o estado local `emailLocal` / `phoneLocal` é atualizado *após* confirmação do servidor (não optimistic). Em caso de erro, a toast mostra a mensagem do body da resposta.

### 4.5 Botão de expandir

O botão `[↗]` chama `onOpenFullPage?.(candidate)` — callback do pai que navega para a página full do candidato. A lógica de navegação fica no pai, não no preview.

---

## 5. ActionBar — ações inline

**Arquivo:** `CandidatePreviewActionBar.tsx`
(`plataforma-lia/src/components/candidate-preview/CandidatePreviewActionBar.tsx`)

### 5.1 Botões de ação

| Ícone | Tooltip | Comportamento quando sem handler | Condição de disable |
|---|---|---|---|
| `Mail` | Email | `window.open('mailto:...')` | `!c.email && !onSendEmail` |
| `Phone` | WhatsApp | `window.open('https://wa.me/...')` | `!c.phone && !onSendWhatsApp` |
| `Calendar` (laranja) | Agendar Entrevista | Chama `onScheduleInterview` | Nunca disabled |
| `ClipboardCheck` | Triagem WSI | Chama `onSendTriagem` | Nunca disabled |
| `Briefcase` | Atribuir à Vaga | Chama `onAddToVacancy` | Nunca disabled |
| `Star` (âmbar) | Favoritar/Desfavoritar | toast de feedback | Nunca disabled |
| `MessageSquareText` (roxo) | Enviar Feedback | Chama `onSendFeedback` | Nunca disabled |

### 5.2 Links sociais

Após separador `|`, exibidos como `<a>` links com `target="_blank"`:

| Rede | Campo fonte | Hover color |
|---|---|---|
| LinkedIn | `c.linkedin` \| `c.linkedin_url` | `wedo-cyan/10` |
| GitHub | `c.github` \| `c.github_url` | `lia-bg-tertiary` |
| Stack Overflow | `c.stackoverflow` \| `c.stackoverflow_url` | `wedo-orange/10` |
| X (Twitter) | `c.twitter` \| `c.twitter_url` \| `c.x_url` | `lia-bg-tertiary` |
| Behance | `c.behance` \| `c.behance_url` | `wedo-cyan/10` |
| Portfolio | `c.portfolio` \| `c.portfolio_url` | `lia-bg-tertiary` |

Links sem URL ficam com `opacity-30 cursor-default` e `e.preventDefault()` no click.

### 5.3 Lógica de fallback nos handlers

Os botões de comunicação têm dupla lógica: se o handler do pai (`onSendEmail`) existe, usa-o (abre o modal de envio da plataforma); se não, faz fallback direto (mailto / wa.me). Isso permite reusar o componente em contextos sem os modais da plataforma.

⚠️ **O erro mais comum é passar `onSendWhatsApp` sem o `c.phone` preenchido.** O botão ficará enabled (pois `onSendWhatsApp` existe) mas ao executar o handler o modal não terá número válido. Sempre verificar se `c.phone` está populado antes de confiar na ação.

---

## 6. PipelineDecisionBar — movimentação de pipeline

**Arquivo:** `PipelineDecisionBar.tsx`
(`plataforma-lia/src/components/candidate-preview/PipelineDecisionBar.tsx`)

### 6.1 Quando aparece

```tsx
// candidate-preview.tsx:168
{!!(jobId || c.vacancy_id || c.vacancy_candidate_id) && (
  <PipelineDecisionBar candidate={c} jobId={jobId} onCandidateUpdated={onCandidateUpdated} />
)}
```

A barra só é renderizada quando o candidato está associado a uma vaga. Os três caminhos de ativação:
1. `jobId` passado diretamente como prop do `CandidatePreview` (contexto kanban)
2. `c.vacancy_id` no objeto candidato (candidato no kanban passado via resultados da busca de vaga)
3. `c.vacancy_candidate_id` (candidato que já está no pipeline de uma vaga)

### 6.2 Endpoints usados pela PipelineDecisionBar

```
GET /api/backend-proxy/jobs/{effectiveJobId}/pipeline
  → popula `pipeline: StageInfo[]`

GET /api/backend-proxy/interviews?candidate_id=X&status=scheduled[&job_vacancy_id=Y]
  → detecta entrevista ativa

GET /api/backend-proxy/opinions/candidate/{id}/summary?company_id=X
  → busca sumário para "highlight" (preview rápido do parecer)

POST /api/backend-proxy/candidates/{candidateId}/screening-decision/
  → decisão de aprovação/rejeição

POST /api/backend-proxy/transition/execute
  → mover candidato para outra etapa
```

### 6.3 Lógica de movimentação

- A barra exibe a lista de stages do pipeline via dropdown
- `canTransition = !!vacancyCandidateId && !!effectiveJobId` — sem ambos, botões ficam disabled
- Stages marcados com `is_hired=true` são filtrados do dropdown (`pipeline.filter(s => !s.is_hired)`)
- Stages com `is_rejection=true` exibem fluxo de confirmação antes de executar

### 6.4 Highlight do candidato

Ao abrir o flyout de stages, a barra carrega um "highlight" do candidato (sumário + pontos fortes do último parecer). Se não há parecer, usa `position` e `current_company` como fallback.

---

## 7. Aba Perfil

**Arquivo:** `CandidatePreviewProfileTab.tsx`
(`plataforma-lia/src/components/candidate-preview/CandidatePreviewProfileTab.tsx`)

### 7.1 Seções da aba Perfil (em ordem de renderização)

```
1. ExperienceHighlightCard          → destaque automático de experiência relevante
2. QualificationMatrixCard          → matriz de qualificação (vaga OU busca)
3. EligibilityResultsSection        → resultados das perguntas eliminatórias (quando presentes)
4. ProfileLiaOpinionCard            → parecer IA (só quando jobId presente)
5. ProfileSkillsMapCard             → mapa de skills
6. ProfileExperienceCards           → experiência profissional + educação
7. ProfileInfoCards                 → info pessoal (salário, endereço, idiomas, preferências)
```

### 7.2 QualificationMatrixCard — dois modos

**Arquivo:** `QualificationMatrixCard.tsx`
(`plataforma-lia/src/components/candidate-preview/QualificationMatrixCard.tsx`)

O card opera em dois modos mutuamente exclusivos:

**Modo Vaga (grouped):**
- Fonte: `currentOpinion.score_breakdown.qualification_matrix` (dados do parecer salvo)
- Ativado quando: `jobId` presente E `currentOpinion` existe
- Agrupa critérios em `must_have` / `preferred`
- Não faz fetch (dados já no parecer)

**Modo Busca (flat):**
- Fonte: `GET /api/backend-proxy/candidates/{id}/criteria-match` (on-the-fly)
- Ativado quando: `!jobId` E `searchCriteria` presente
- Lista única de critérios sem agrupamento
- Usa `useQuery` (React Query v5) com cache automático

```tsx
// CandidatePreviewProfileTab.tsx:44-49
const groupedMatrix =
  jobId && currentOpinion
    ? (((currentOpinion as { score_breakdown?: Record<string, unknown> })
        .score_breakdown?.qualification_matrix as QualificationMatrixData | undefined) ?? null)
    : null
```

⚠️ **O erro mais comum é esperar a matriz no modo busca sem passar `searchCriteria`.** Se `searchCriteria` for `null` e não houver `jobId`, o `QualificationMatrixCard` não renderiza nada — comportamento correto mas confuso.

### 7.3 EligibilityResultsSection

Extrai `eligibility_results` do objeto candidato:

```tsx
// CandidatePreviewProfileTab.tsx:15-27
function extractEligibilityResults(candidate: Record<string, unknown>): EligibilityResultItem[] | undefined {
  const raw = candidate?.eligibility_results
  if (!Array.isArray(raw) || raw.length === 0) return undefined
  return (raw as Record<string, unknown>[]).map((r, i) => ({
    id: String(r.id ?? r.question_id ?? i),
    question: String(r.question ?? r.question_text ?? ""),
    answer: r.answer != null ? String(r.answer) : undefined,
    passed: Boolean(r.passed ?? r.met ?? true),
    is_eliminatory: r.is_eliminatory !== false,
    reconsideration: r.reconsideration != null ? String(r.reconsideration) : undefined,
  }))
}
```

Só aparece quando `eligibility_results` é array não-vazio. O campo vem do backend no `_serialize_candidate(candidate, full=True)`.

### 7.4 ProfileLiaOpinionCard — condições de exibição

```tsx
// ProfileLiaOpinionCard.tsx:30
if (!jobId) return null   // só exibe com vaga em contexto
```

Além disso, não exibe se não há `current_general_opinion` nem `vacancy_opinions[0]` no `opinionsData`.

O score exibido depende do tipo de opinião:
- WSI opinion (`opinion_type === 'wsi'` OR `wsi_score !== null`): exibe `wsi_score` (escala 0–10)
- Opinião geral: exibe `score` (escala 0–100)

---

## 8. Aba Atividades

**Arquivo:** `CandidateActivitiesTab.tsx` (412 linhas)
(`plataforma-lia/src/components/candidate-preview/CandidateActivitiesTab.tsx`)

### 8.1 Estrutura

A aba usa o hook `useCandidateActivities` e renderiza:
- `ActivityFilters` — filtros de tipo, view e período
- `ActivityTimeline` — linha do tempo de atividades

### 8.2 Mapa de ícones por tipo de atividade

O mapa `getActivityIconMeta(type)` converte o string do tipo em ícone + cor:

| Pattern no type | Ícone | Cor |
|---|---|---|
| `email` | `Mail` | `var(--wedo-cyan)` |
| `voice`, `wsi`, `screening` | `Mic` | `var(--wedo-purple)` |
| `video`, `interview` | `Video` | `var(--wedo-orange)` |
| `lia`, `brain`, `ai`, `analysis` | `Brain` | `var(--wedo-coral)` |
| `calendar`, `schedule`, `agendamento` | `Calendar` | `var(--wedo-orange)` |
| `offer`, `onboarding` | `Gift` | `var(--status-success)` |
| `approved`, `hired` | `ThumbsUp` | `var(--status-success)` |
| `rejected`, `declined` | `ThumbsDown` | `var(--status-error)` |
| default | `Activity` | `var(--lia-text-secondary)` |

---

## 9. Aba Arquivos

**Arquivo:** `CandidateFilesTab.tsx` (253 linhas)
(`plataforma-lia/src/components/candidate-preview/CandidateFilesTab.tsx`)

### 9.1 Endpoints

```
GET  /api/backend-proxy/candidates/{id}/files
POST /api/backend-proxy/candidates/{id}/files
GET  /api/backend-proxy/candidates/{id}/files/{attachmentId}  (download)
```

O hook `useCandidateFiles` gerencia upload, listagem e download. Suporta tipos: PDF, imagem, vídeo, áudio — com preview modal (`FilePreviewModal.tsx`).

---

## 10. Aba Pareceres e Análises

**Arquivo:** `CandidateOpinionsTab.tsx`
(`plataforma-lia/src/components/candidate-preview/CandidateOpinionsTab.tsx`)

### 10.1 Estados da aba

| Estado | Quando | UI |
|---|---|---|
| Loading | `isLoadingHistory=true` | Skeleton de 2 cards pulsantes |
| Error | `isErrorHistory=true` | Alert com ícone + botão "Tentar novamente" |
| Empty | `opinionsHistory.length === 0` | Estado vazio com FileText icon |
| Filled | `opinionsHistory.length > 0` | Lista de `OpinionCard` |

⚠️ **O erro mais comum é usar `catch {}` silencioso.** O componente exibe estado de erro explícito (`isErrorHistory`) com botão de retry — **não silenciar erros de fetch nesta aba**.

### 10.2 Cache de histórico (dedup de fetch)

```tsx
// useCandidatePreviewCore.tsx:91-105
const lastFetchedHistoryCandidateRef = useRef<string | null>(null)

// Se já buscou para este candidateId e tem dados, não rebusca
if (lastFetchedHistoryCandidateRef.current === candidateId && opinionsHistory.length > 0) {
  return
}
```

### 10.3 Geração de parecer

O fluxo de `generateNewOpinion()` tem dois caminhos:

**Com `jobId` (parecer por vaga):**
```
POST /api/backend-proxy/opinions/candidate/{id}/parecer?company_id=X
body: { job_vacancy_id: jobId }
```

**Sem `jobId` (parecer geral):**
```
POST /api/backend-proxy/analysis/candidates?company_id=X
body: { candidates: [candidateInput], analysis_type: 'general' }
→ extrai result.lia_score, archetype, score_breakdown
→ POST /api/backend-proxy/opinions?company_id=X&user_id=system
body: { candidate_id, opinion_type: 'general', source: 'cv_analysis', score, ... }
```

**Threshold de recomendação** (parecer geral):
- `lia_score >= 70` → `recommendation = 'approved'`
- `lia_score < 50` → `recommendation = 'not_approved'`
- entre 50 e 70 → `recommendation = 'pending_review'`

### 10.4 Guard de geração: dados insuficientes

Antes de gerar, `handleAnalyzeWithLia()` chama `validateCandidateDataForOpinion(candidate)`. Se o candidato não tem dados suficientes:
- `isValid=false` → abre `InsufficientDataModal` bloqueando
- `canProceedWithWarning=true` → abre `InsufficientDataModal` mas permite prosseguir

### 10.5 Guard de atualização (30 dias)

Se o candidato já tem parecer com menos de 30 dias, exibe `AlertDialog` pedindo confirmação antes de regerar.

### 10.6 Cópia de pareceres para clipboard

`handleCopyOpinion(opinion, type)` formata o parecer como texto plain:
```
PARECER IA - <Nome>
Tipo: Parecer WSI | Parecer de Vaga | Parecer Geral
Vaga: <título> (se houver)
Nota: X.X/10 (WSI) | XX/100 (geral)

<sumário>

PONTOS FORTES:
• ...

PONTOS DE ATENÇÃO:
• ...

GAPS IDENTIFICADOS:
• ...

PRÓXIMOS PASSOS:
...
```

Nota: comentário `// @canonical-allow-100 fallback for non-WSI legacy opinion in copy-to-clipboard text` marca o único local onde a escala 0–100 é usada para opiniões não-WSI no texto copiado.

---

## 11. Aba Consentimento

**Arquivo:** `CandidateConsentTab.tsx` (447 linhas)
(`plataforma-lia/src/components/candidate-preview/CandidateConsentTab.tsx`)

### 11.1 Endpoint

```
GET /api/backend-proxy/observability/consents/{candidateId}
→ retorna ConsentRecord[]
```

### 11.2 Tipos de consentimento mapeados

```tsx
// CandidateConsentTab.tsx (label maps)
const CONSENT_TYPE_LABELS = {
  consentimento_audio:             "Áudio da triagem",
  consentimento_audio_revoked:     "Áudio revogado",
  dados_sensiveis_acao_afirmativa: "Dados de ação afirmativa",
  comunicacao:                     "Comunicação",
}
```

### 11.3 Status do consentimento

| Condição | Display |
|---|---|
| `revoked_at` presente | Revogado |
| `expires_at < now` E `is_active` | Expirado |
| `is_active = true` | Ativo |
| default | Inativo |

### 11.4 Canais mapeados

```tsx
const CANAL_LABELS = {
  chat_web:            "Chat web",
  whatsapp:            "WhatsApp",
  chamada_online:      "Chamada online",
  chamada_telefonica:  "Chamada telefônica",
}
```

Usa `useQuery` do React Query v5 — diferentemente das outras abas que usam `useState + fetch`.

---

## 12. Modais disparados a partir do preview

O componente `CandidatePreviewModals.tsx` centraliza todos os modais do preview. Todos são carregados com `dynamic()` para lazy loading:

| Modal | Campo de controle | Disparo |
|---|---|---|
| `LiaChatModal` | `showLiaModal` | Botão LIA (ações legadas) |
| `InsufficientDataModal` | `showInsufficientDataModal` | `handleAnalyzeWithLia` → `validateCandidateDataForOpinion` |
| `AlertDialog` (parecer existente) | `showUpdateOpinionAlert` | `handleAnalyzeWithLia` → parecer < 30 dias |
| `ScreeningMediaModal` | `screeningModalOpen` | click em resultado de triagem WSI |
| `DISCAssessmentModal` | `discModalOpen` | click no resultado DISC do candidato |
| `BigFiveModal` | `bigFiveModalOpen` | click no resultado BigFive do candidato |

---

# PARTE C — REFERÊNCIA

## 13. 📋 Quadro-resumo de regras de negócio

| # | Regra | Onde é enforçada | Evidência |
|---|---|---|---|
| R1 | Preview **não faz fetch** do candidato: recebe objeto pronto via prop | `candidate-preview.tsx:53` (recebe como prop) | — |
| R2 | Normalização de arrays no mount: campos podem vir como objeto único | `candidate-preview.tsx:112-120` | Evita crash em `.map()` |
| R3 | `PipelineDecisionBar` só aparece com `jobId \|\| vacancy_id \|\| vacancy_candidate_id` | `candidate-preview.tsx:168` | — |
| R4 | `canTransition` exige `vacancyCandidateId && effectiveJobId` | `PipelineDecisionBar.tsx:57` | Sem ambos, botões disabled |
| R5 | Stages `is_hired=true` são filtrados do dropdown de movimentação | `PipelineDecisionBar.tsx:80` | `.filter(s => !s.is_hired)` |
| R6 | Score WSI: escala 0–10. Score geral: escala 0–100 | `OpinionCard.tsx:54-55` | `isWsiOpinion ? wsi_score : score` |
| R7 | `ProfileLiaOpinionCard` só renderiza quando `jobId` presente | `ProfileLiaOpinionCard.tsx:30` | `if (!jobId) return null` |
| R8 | Threshold de recomendação geral: ≥70 = approved, <50 = not_approved | `useCandidatePreviewCore.tsx:247-251` | — |
| R9 | Guard de regeneração: não regenera parecer com menos de 30 dias sem confirmação | `useCandidatePreviewCore.tsx:314-325` | `daysSince < 30` |
| R10 | Guard de dados insuficientes: `validateCandidateDataForOpinion` antes de gerar | `useCandidatePreviewCore.tsx:291` | — |
| R11 | Edição inline de email/phone usa FastAPI (não Rails) | `CandidatePreviewHeader.tsx:74-98` | `POST /chat/actions/candidate-field-update` |
| R12 | Cache de histórico de opiniões por `candidateId` (evita refetch) | `useCandidatePreviewCore.tsx:91-100` | `lastFetchedHistoryCandidateRef` |
| R13 | PII redaction por papel: campos sensíveis mascarados pelo backend | `candidates_crud.py:253` | `apply_pii_field_visibility` |
| R14 | Links sociais disabled (não hidden) quando ausentes | `CandidatePreviewActionBar.tsx` | `opacity-30 cursor-default + e.preventDefault()` |
| R15 | Resize drag: Funil herda do pai; Kanban gerencia internamente | `KanbanCandidatePreviewPanel.tsx:20-22` | 360–700px |
| R16 | `QualificationMatrixCard` modo vaga usa dados do parecer salvo (sem fetch) | `CandidatePreviewProfileTab.tsx:44-49` | `groupedMatrix` do `score_breakdown` |
| R17 | Histórico de opiniões é lazy: só busca ao entrar na aba "opinions" | `useCandidatePreviewCore.tsx:116-120` | `if (activeTab === 'opinions')` |

---

## 14. PII Visibility — campos por papel de usuário

**Arquivo BE:** `lia-agent-system/app/api/v1/candidates/candidates_crud.py:253`
**Arquivo BE:** `lia-agent-system/app/shared/rbac/pii_field_resolver.py`
**Arquivo BE:** `lia-agent-system/app/shared/rbac/pii_field_catalog.py`

### 14.1 Como funciona

O endpoint `GET /api/v1/candidates/{id}` aplica `apply_pii_field_visibility(serialized, current_user, role_defaults)` antes de retornar. Esse método:

1. Chama `resolve_pii_field_visibility(current_user, role_defaults)` → retorna `dict[field, can_view]`
2. Para cada campo onde `can_view = False`, mascara o valor
3. Adiciona flags `salary_masked: bool` e `sensitive_pii_masked: bool` na resposta

```python
# candidates_crud.py:253-275
def apply_pii_field_visibility(candidate_dict: dict, current_user, role_defaults: dict | None = None) -> dict:
    effective = resolve_pii_field_visibility(current_user, role_defaults or {})
    any_salary_masked = False
    any_sensitive_masked = False
    for field, can_view in effective.items():
        if can_view:
            continue  # campo visível
        # mascara o campo
        any_salary_masked = True   # se é campo de salário
        any_sensitive_masked = True  # se é campo sensível
    candidate_dict["salary_masked"] = any_salary_masked
    candidate_dict["sensitive_pii_masked"] = any_sensitive_masked
```

### 14.2 Flags de resultado no objeto candidato

| Flag | Significado para o FE |
|---|---|
| `salary_masked: true` | Campos de salário foram removidos/mascarados |
| `sensitive_pii_masked: true` | Campos sensíveis (CPF, RG, endereço completo) foram mascarados |

### 14.3 Consentimento de comunicação vs. consentimento de áudio

São dois campos independentes:
- `communication_consent` (bool) — consentimento para contato por email/WhatsApp
- `hasAudioConsent` (bool | undefined) — prop passada para o Header, calculada a partir dos consentimentos retornados pela aba Consentimento

⚠️ **O `communication_consent` vem no objeto candidato da busca. O consentimento de áudio é calculado lendo os registros de `/observability/consents/{id}` e verificando se existe registro `consentimento_audio` ativo.**

### 14.4 RAILS_ENABLED = False

`RAILS_API_URL` não está definido no Replit dev. `RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL")) = False`. O endpoint de candidato (`GET /api/v1/candidates/{id}`) usa exclusivamente PostgreSQL local (`candidate_repo.get_by_id_str()`). Não há fallback para Rails.

```python
# candidates_crud.py:535-565
# "Only call Rails when explicitly enabled — avoids adapter's own DB fallback"
try:
    candidate = await candidate_repo.get_by_id_str(candidate_id)
```

---

## 15. Score LIA vs Score WSI no preview

### 15.1 Dois sistemas de score distintos

| Sistema | Campo | Escala | Quando aparece |
|---|---|---|---|
| Score Geral LIA | `opinion.score` | 0–100 | Pareceres `opinion_type='general'` ou `opinion_type=null` |
| Score WSI | `opinion.wsi_score` | 0–10 | Pareceres `opinion_type='wsi'` OU `wsi_score != null` |

### 15.2 Lógica de detecção

```tsx
// OpinionCard.tsx:54-55 / ProfileLiaOpinionCard.tsx:54-55
const isWsiOpinion = opinion.opinion_type === 'wsi' || opinion.wsi_score !== null
const displayScore = isWsiOpinion ? opinion.wsi_score : opinion.score
```

### 15.3 Cores por faixa de score

**Score geral (0–100):**
```tsx
score >= 80 → 'text-status-success'
score >= 60 → 'text-status-warning'
score  < 60 → 'text-status-error'
```

**Score WSI (0–10):** usa `getWsiScoreColor(score)` de `@/lib/wsi/visual`.

### 15.4 Score no CandidatePreviewPanel (legado)

O `CandidatePreviewPanel.tsx` usa um campo único `candidate.score` formatado como `formatScorePercent(candidate.score)` — não distingue WSI de geral. Esse componente está em contexto legado.

⚠️ **Nunca usar `candidate.score` como campo único em novos componentes.** A distinção `isWsiOpinion ? wsi_score : score` é obrigatória.

---

## 16. Contratos de API

### 16.1 GET /api/v1/candidates/{id}

```
GET /api/v1/candidates/{id}
→ Proxy: /api/backend-proxy/candidates/[id]/route.ts
→ Backend: FastAPI candidates_crud.py:535
→ Auth: JWT obrigatório (Depends(get_current_user_or_demo))
→ multi-tenancy: company_id do JWT (Depends(require_company_id))
→ Resposta: ResponseEnvelope { ok, data: CandidateData, meta: { source: "local" } }
```

Campos que podem vir mascarados dependendo do papel:
- Campos de salário: `current_salary`, `desired_salary_min`, `desired_salary_max`, `salary_expectation_clt`, `salary_expectation_pj`
- Campos sensíveis: CPF, RG, endereço completo, dados de ação afirmativa

### 16.2 GET /api/v1/opinions/candidate/{id}/summary

```
GET /api/v1/opinions/candidate/{id}/summary?company_id={cid}
→ Resposta:
{
  "current_general_opinion": OpinionEntry | null,
  "vacancy_opinions": OpinionEntry[],
  "total_opinions": number
}
```

`OpinionEntry`:
```typescript
interface OpinionEntry {
  opinion_type?: string       // 'general' | 'wsi' | 'vacancy'
  wsi_score?: number | null   // 0-10 (WSI)
  score?: number | null       // 0-100 (geral)
  archetype?: string
  summary?: string
  created_at?: string         // ISO 8601
  score_breakdown?: {
    qualification_matrix?: QualificationMatrixData  // só em pareceres por vaga
  }
}
```

### 16.3 GET /api/v1/opinions/candidate/{id}/history

```
GET /api/v1/opinions/candidate/{id}/history?company_id={cid}
→ Resposta: LiaOpinionFull[]   (lista completa com strengths, concerns, gaps, next_steps)
```

### 16.4 POST /api/v1/opinions/candidate/{id}/parecer

```
POST /api/v1/opinions/candidate/{id}/parecer?company_id={cid}
Body: { "job_vacancy_id": string }
→ Gera parecer específico para a vaga
→ Persiste a qualification_matrix no score_breakdown
```

### 16.5 POST /api/v1/chat/actions/candidate-field-update

```
POST /api/v1/chat/actions/candidate-field-update
Body:
{
  "candidate_id": string,   // UUID do candidato
  "fields": {
    "email": string | null,
    "phone": string | null
  }
}
→ Resposta: { data: { results: [{ status: "executed" | "failed", ... }] } }
→ company_id do JWT (multi-tenancy)
→ Verifica ownership via vacancy_candidates join
```

### 16.6 GET /api/v1/jobs/{jobId}/pipeline

```
GET /api/v1/jobs/{jobId}/pipeline
→ Resposta: { pipeline: StageInfo[] }
```

`StageInfo`:
```typescript
interface StageInfo {
  name: string
  display_name: string
  stage_order: number
  color: string
  action_behavior: string
  is_rejection?: boolean
  is_hired?: boolean
  sub_statuses?: Array<{ name: string; display_name: string }>
}
```

---

## 17. Componentes & estado (frontend)

### 17.1 Mapa de componentes

```
src/components/candidate-preview/
├── index.ts                          ← barrel export: export { CandidatePreview }
├── candidate-preview.tsx             ← raiz, orquestra tudo
├── useCandidatePreviewCore.tsx       ← único dono de estado
├── ProfileTabTypes.ts                ← tipos: CandidateData, OpinionsData, OpinionEntry
│
├── CandidatePreviewHeader.tsx        ← header com avatar, chips, contact fields
├── CandidatePreviewActionBar.tsx     ← botões de ação + links sociais
├── PipelineDecisionBar.tsx           ← barra de movimentação de pipeline
├── CandidatePreviewModals.tsx        ← container de todos os modais
│
├── CandidatePreviewProfileTab.tsx    ← aba Perfil (orquestra sub-cards)
├── CandidateActivitiesTab.tsx        ← aba Atividades
├── CandidateFilesTab.tsx             ← aba Arquivos
├── CandidateOpinionsTab.tsx          ← aba Pareceres e Análises
├── CandidateConsentTab.tsx           ← aba Consentimento
│
├── ExperienceHighlightCard (externo) ← ExperienceHighlightCard.tsx (fora da pasta)
├── QualificationMatrixCard.tsx       ← matriz de qualificação
├── ProfileLiaOpinionCard.tsx         ← card de parecer IA no perfil
├── ProfileSkillsMapCard.tsx          ← mapa de skills
├── ProfileExperienceCards.tsx        ← cards de experiência + educação
├── ProfileInfoCards.tsx              ← info pessoal
├── OpinionCard.tsx                   ← card individual de parecer
├── LiaChatModal.tsx                  ← modal de chat LIA (legado)
├── FilePreviewModal.tsx              ← preview de arquivos
│
├── activities/
│   ├── ActivityFilters.tsx
│   └── ActivityTimeline.tsx
└── __tests__/
    └── (testes unitários)
```

### 17.2 Estado mantido em useCandidatePreviewCore

```typescript
// Estado de navegação
activeTab: 'profile' | 'activities' | 'files' | 'opinions' | 'consent'

// Estado de modais
showLiaModal: boolean
screeningModalOpen: boolean
discModalOpen: boolean
bigFiveModalOpen: boolean
showUpdateOpinionAlert: boolean
showInsufficientDataModal: boolean

// Estado de opiniões
opinionsData: OpinionsData | null
opinionsHistory: Record<string, unknown>[]
isLoadingOpinions: boolean
isLoadingHistory: boolean
isErrorHistory: boolean
expandedOpinionId: string | null
lastOpinionDate: Date | null
isAnalyzingWithLia: boolean
lastAnalysisDate: Date | null

// Estado de LIA chat (legado)
liaChatMessages: LiaChatMessage[]
isLiaChatLoading: boolean
liaConversationId: string | null
```

### 17.3 Props do componente raiz CandidatePreview

```typescript
interface CandidatePreviewProps {
  candidate: Record<string, unknown>  // obrigatório
  isOpen: boolean                     // obrigatório
  onClose: () => void                 // obrigatório
  isMaximized?: boolean
  onToggleMaximize?: () => void
  candidates?: Record<string, unknown>[]  // para navegação prev/next
  currentIndex?: number
  onNavigateCandidate?: (index: number) => void
  onOpenFullPage?: (candidate) => void
  onScheduleInterview?: (candidate) => void
  onAddToVacancy?: (candidate) => void
  onToggleFavorite?: (candidateId: string) => void
  onWSIScreening?: (candidate) => void
  onOpenTriagemDetails?: (candidate) => void
  isFavorite?: boolean
  onSendEmail?: (candidate) => void
  onSendWhatsApp?: (candidate) => void
  onSendTriagem?: (candidate) => void
  onSendAgendamento?: (candidate) => void
  onSendFeedback?: (candidate) => void
  onContact?: (candidate, channel?: 'email' | 'whatsapp') => void
  onSchedule?: (candidate) => void
  onAddToList?: (candidate) => void
  jobId?: string                      // ativa PipelineDecisionBar e parecer por vaga
  searchCriteria?: Record<string, unknown> | null  // ativa QualificationMatrix modo busca
  onCandidateUpdated?: () => void     // callback após update de pipeline
}
```

### 17.4 Geração de ID curto

```typescript
// useCandidatePreviewCore.tsx:359-367
function generateShortId(name: string, id: string | number | null | undefined): string {
  const letters = (name || 'XX').replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase() || 'XX'
  const idStr = String(id || '')
  const digits = idStr.replace(/[^0-9]/g, '')
  const lastFourDigits = digits.length >= 4
    ? digits.slice(-4)
    : digits.padStart(4, '0').slice(-4) || String(Math.floor(1000 + Math.random() * 9000))
  return `${letters}${lastFourDigits}`
}
// Exemplo: "Paulo Moraes", id="abc-1234" → "PM1234"
```

---

## 18. Checklist de replicação em outro ambiente

### Infraestrutura mínima

- [ ] FastAPI rodando em porta 8001 com `RAILS_ENABLED=False`
- [ ] PostgreSQL com tabelas: `candidates`, `vacancy_candidates`, `lia_opinions`, `company_hiring_policies`
- [ ] Redis disponível (usado por token budget no chat, não no preview em si)
- [ ] Variável `BACKEND_URL` apontando para FastAPI no proxy Next.js

### Endpoints obrigatórios

- [ ] `GET /api/v1/candidates/{id}` — com `apply_pii_field_visibility` e multi-tenancy
- [ ] `GET /api/v1/opinions/candidate/{id}/summary` — sumário de opiniões
- [ ] `GET /api/v1/opinions/candidate/{id}/history` — histórico completo
- [ ] `POST /api/v1/opinions/candidate/{id}/parecer` — gerar parecer por vaga
- [ ] `POST /api/v1/analysis/candidates` — análise geral (sem jobId)
- [ ] `POST /api/v1/opinions` — salvar parecer gerado
- [ ] `POST /api/v1/chat/actions/candidate-field-update` — editar email/telefone
- [ ] `GET /api/v1/jobs/{id}/pipeline` — stages do pipeline (para PipelineDecisionBar)
- [ ] `GET /api/v1/interviews` — entrevistas ativas (para PipelineDecisionBar)
- [ ] `POST /api/v1/transition/execute` — mover candidato no pipeline
- [ ] `GET /api/v1/observability/consents/{candidateId}` — consentimentos
- [ ] `GET /api/v1/candidates/{id}/files` — arquivos
- [ ] `GET /api/v1/candidates/{id}/criteria-match` — matriz de qualificação on-the-fly

### Proxy Next.js (routes obrigatórias)

- [ ] `src/app/api/backend-proxy/candidates/[id]/route.ts` → `/api/v1/candidates/:id`
- [ ] `src/app/api/backend-proxy/opinions/candidate/[id]/summary/route.ts`
- [ ] `src/app/api/backend-proxy/opinions/candidate/[id]/history/route.ts`
- [ ] `src/app/api/backend-proxy/opinions/candidate/[id]/parecer/route.ts`
- [ ] `src/app/api/backend-proxy/chat/actions/candidate-field-update/route.ts`

### Componentes externos que o preview importa

- [ ] `CandidateAvatar` — `src/components/candidate-profile/CandidateAvatar.tsx`
- [ ] `ExperienceHighlightCard` — `src/components/experience-highlight-card.tsx`
- [ ] `EligibilityResultsSection` — `src/components/wsi/eligibility-results-section.tsx`
- [ ] `LIAFeedbackWidget` — `src/components/calibration/`
- [ ] Design tokens: `src/lib/design-tokens.ts` (textStyles, previewChipVariants, formatScore, formatScorePercent)
- [ ] `src/lib/wsi/visual.ts` — `getWsiScoreColor()`
- [ ] Hooks: `useCurrentCompany`, `useAuthenticatedUserId`, `useCandidateActivities`
- [ ] Modais externos (dynamic import): `ScreeningMediaModal`, `DISCAssessmentModal`, `BigFiveModal`

### Verificações de Rules of Hooks

O componente raiz tem >10 hooks via `useCandidatePreviewCore`. O early return `if (!isOpen || !candidate) return null` está **APÓS** o call do hook:

```tsx
// candidate-preview.tsx:73 — correto
const core = useCandidatePreviewCore(candidate, jobId)
const { activeTab, ... } = core

// ...desestruturação de todos os valores...

if (!isOpen || !candidate) return null  // early return DEPOIS dos hooks
```

---

## 19. Glossário

| Termo | Definição |
|---|---|
| **Preview** | Painel lateral que mostra detalhes de um candidato sem sair da tela atual |
| **Score Geral LIA** | Pontuação 0–100 da análise geral do candidato pelo LLM |
| **Score WSI** | Pontuação 0–10 da triagem estruturada (WSI = Workplace Skills Interview) |
| **Parecer** | Registro persistido da análise IA de um candidato (`LiaOpinion` no banco) |
| **Parecer Geral** | Parecer sem vaga específica, `opinion_type='general'` |
| **Parecer de Vaga** | Parecer vinculado a uma `job_vacancy_id`, contém `qualification_matrix` |
| **Qualification Matrix** | Grade de critérios (must_have / preferred) avaliados contra o perfil do candidato |
| **PipelineDecisionBar** | Barra de movimentação de candidato entre stages do pipeline de uma vaga |
| **vacancy_candidate_id** | FK da tabela `vacancy_candidates` — representa a relação candidato↔vaga |
| **enrichment_source** | Origem do enriquecimento do perfil: `apify`, `pearch`, `local` |
| **ContactField** | Componente inline com Popover para editar email/telefone diretamente no header |
| **generateShortId** | Função que gera ID de exibição como "PM1234" (iniciais + últimos 4 dígitos) |
| **CandidatePreviewPanel** | Versão legada simplificada do preview, sem `useCandidatePreviewCore` |
| **salary_masked** | Flag na resposta do backend indicando que campos de salário foram ocultados |
| **sensitive_pii_masked** | Flag na resposta do backend indicando que PII sensível foi ocultada |
| **RAILS_ENABLED** | `bool(os.environ.get("RAILS_API_URL")) = False` no Replit dev — Rails fora do fluxo |

---

## 20. Gaps & pontos de atenção

### 🔴 P0 — Issues que podem causar comportamento incorreto

**G1 — `useCandidatePreviewCore` usa `useState + fetch` (anti-pattern)**
`fetchOpinionsSummary` e `fetchOpinionsHistory` usam `useState + useEffect + fetch` em vez de React Query. Isso viola a REGRA 1 de Settings (`useState` proibido para server data). Para telas de settings isso é blocking — para o preview está pendente de migração.
- Arquivo: `useCandidatePreviewCore.tsx:70-107`
- Impacto: sem cache, sem dedup de requests, sem retry automático

**G2 — `CandidatePreviewPanel.tsx` tem dados hardcoded nas abas experience e skills**
As abas de experiência e skills do painel legado mostram "Senior Developer / Tech Corp" e "React, TypeScript" hardcoded. Se esse componente for usado em produção real, exibe dados fictícios.
- Arquivo: `CandidatePreviewPanel.tsx:64-108`
- Impacto: dados de experience/skills não correspondem ao candidato real

**G3 — `company_id` passado como query string nas opiniões**
Diferentemente do padrão canônico (que usa JWT exclusivamente), as chamadas de opiniões no frontend passam `?company_id={companyId}` como query parameter:
```tsx
// useCandidatePreviewCore.tsx:73
`/api/backend-proxy/opinions/candidate/${candidateId}/summary?company_id=${encodeURIComponent(companyId)}`
```
O `companyId` vem de `useCurrentCompany()` (JWT-derived hook), então não é vulnerável — mas o padrão diverge do canônico.

### 🟡 P1 — Issues importantes sem impacto imediato de segurança

**G4 — Sem navegação prev/next funcional no Funil**
`onNavigateCandidate` é passado como prop mas a lógica de navegação (prev/next entre candidatos do resultado de busca) não está implementada no `CandidatePreviewSidePanel`. No Kanban está implementada.
- Arquivo: `CandidatePreviewSidePanel.tsx:84-88` (callback presente mas sem lógica de prev/next)

**G5 — `lastAnalysisDate` inicializa com "2 dias atrás" como fallback**
```tsx
// useCandidatePreviewCore.tsx:26-28
const [lastAnalysisDate, setLastAnalysisDate] = useState<Date | null>(
  (candidate as Record<string, unknown>)?.lastLiaAnalysis
    ? new Date(String(...))
    : new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)  // fallback: 2 dias atrás
)
```
Se o candidato não tem `lastLiaAnalysis`, o preview mostra "Há 2 dias" como data de última análise mesmo sem ter análise prévia. O dado real vem do `opinionsData.current_general_opinion.created_at`.

**G6 — `opinionsHistory.length` como dependência causa re-fetch indesejado**
```tsx
// useCandidatePreviewCore.tsx:107
}, [candidateId, companyId, opinionsHistory.length])
```
`opinionsHistory.length` como dep do `useCallback` é problemático: ao receber a primeira página, o length muda, potencialmente triggerando um segundo fetch. A lógica de cache via `lastFetchedHistoryCandidateRef` mitiga mas não elimina completamente.

### 🟢 P2 — Melhorias e polish

**G7 — Falta i18n nas strings do useCandidatePreviewCore**
O hook usa strings PT-BR hardcoded como "Parecer gerado", "Erro ao gerar parecer" (toast messages). Elas não passam pelo sistema de i18n `next-intl`.

**G8 — `CandidatePreviewPanel` usa `Avatar` diretamente em vez de `CandidateAvatar`**
O componente legado usa `<Avatar>` + `<AvatarImage>` com src de ui-avatars.com como fallback. O `CandidatePreview` real usa `CandidateAvatar` que encapsula essa lógica.

**G9 — Aba Consentimento usa `useQuery` mas as outras abas não**
A aba Consentimento foi migrada para React Query v5 (`useQuery`). As demais abas (atividades via `useCandidateActivities`) usam padrões variados. Oportunidade de uniformizar.

**G10 — Sem teste de regressão para early return position**
O early return `if (!isOpen || !candidate) return null` está correto (após hooks), mas não há teste de smoke que verifique render com `isOpen=false → true → false` sem crash (conforme REGRA 4 de React Hooks — componentes com 5+ hooks).
