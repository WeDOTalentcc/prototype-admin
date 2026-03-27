# Sistema do Painel de Controle — Plataforma LIA

> **Versão**: 1.0 — 25 de Fevereiro de 2026  
> **Propósito**: Guia de implementação, referência técnica e base para treinamento  
> **Status**: Documento de referência para o Painel de Controle (Dashboard)

---

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Componente](#2-arquitetura-do-componente)
3. [Modelo de Dados](#3-modelo-de-dados)
4. [Seção: Header e Saudação](#4-seção-header-e-saudação)
5. [Seção: Tabs — Entrevistas e Histórico](#5-seção-tabs--entrevistas-e-histórico)
6. [Cards de Entrevista (Agendadas)](#6-cards-de-entrevista-agendadas)
7. [Cards de Histórico](#7-cards-de-histórico)
8. [Layout dos Cards — Grid de 2 Colunas](#8-layout-dos-cards--grid-de-2-colunas)
9. [Sistema de Ações nos Cards](#9-sistema-de-ações-nos-cards)
10. [Integração com Outras Páginas](#10-integração-com-outras-páginas)
11. [Integração Backend — API de Entrevistas](#11-integração-backend--api-de-entrevistas)
12. [Proxy Frontend → Backend](#12-proxy-frontend--backend)
13. [Funções Utilitárias](#13-funções-utilitárias)
14. [Design System Aplicado](#14-design-system-aplicado)
15. [Estados da Interface](#15-estados-da-interface)
16. [Fluxos Completos End-to-End](#16-fluxos-completos-end-to-end)
17. [Endpoints da API](#17-endpoints-da-api)
18. [Glossário](#18-glossário)
19. [Status de Implementação e Roadmap](#19-status-de-implementação-e-roadmap)

---

## 1. Visão Geral

### O que é o Painel de Controle

O Painel de Controle é a **página inicial** do recrutador na Plataforma LIA. Centraliza a agenda de entrevistas, oferecendo uma visão rápida do dia e próximas atividades. É o ponto de partida para ações como abrir reuniões, reagendar entrevistas e navegar para vagas.

### Filosofia Central

```
┌─────────────────────────────────────────────────────────────┐
│                    PRINCÍPIOS FUNDAMENTAIS                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. AGENDA COMO CENTRO                                     │
│     O recrutador vê primeiro suas entrevistas do dia,      │
│     organizadas por período (manhã/tarde/próximos dias).   │
│                                                             │
│  2. AÇÃO IMEDIATA                                          │
│     Cada card de entrevista tem botões de ação diretos:    │
│     abrir reunião, alterar horário, cancelar.              │
│                                                             │
│  3. CONTEXTO COMPLETO NO CARD                              │
│     Candidato (nome, cargo, empresa) + Vaga (ID, título,   │
│     gestor) visíveis no card sem precisar navegar.         │
│                                                             │
│  4. NAVEGAÇÃO FLUIDA                                       │
│     Clicar na vaga leva direto ao Kanban com o candidato   │
│     focado. Alterar horário navega para o fluxo correto.   │
│                                                             │
│  5. DADOS REAIS DO BACKEND                                 │
│     Entrevistas vêm da API real com JOIN em job_vacancies, │
│     enriquecidas com dados do candidato (cargo, empresa).  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Diagrama Geral do Fluxo

```
                  RECRUTADOR ABRE PLATAFORMA
                          │
                          ▼
                ┌───────────────────┐
                │  Painel de        │
                │  Controle         │
                │  (tasks-page-mvp) │
                └────────┬──────────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Saudação   │ │ Tab:       │ │ Tab:       │
    │ + Resumo   │ │ Entrevistas│ │ Histórico  │
    │ do Dia     │ │ (agendadas)│ │ (passadas) │
    └────────────┘ └─────┬──────┘ └─────┬──────┘
                         │              │
                    ┌────┴────┐    ┌────┴────┐
                    │ Cards   │    │ Cards   │
                    │ com     │    │ com     │
                    │ ações   │    │ badge   │
                    │ diretas │    │ status  │
                    └────┬────┘    └─────────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Abrir      │ │ Alterar    │ │ Cancelar   │
    │ Reunião    │ │ Horário    │ │ Entrevista │
    │ (link ext.)│ │ (→ Vagas)  │ │ (→ Vagas)  │
    └────────────┘ └────────────┘ └────────────┘
```

---

## 2. Arquitetura do Componente

### 2.1 Arquivo Principal

| Atributo | Valor |
|----------|-------|
| **Arquivo** | `plataforma-lia/src/components/pages/tasks-page-mvp.tsx` |
| **Tipo** | Client Component (`"use client"`) |
| **Linhas** | ~885 |
| **Exportação** | `TasksPageMVP` (named export) |
| **Props** | `{ onNavigate?: (page: string) => void }` |

### 2.2 Dependências

| Categoria | Dependências |
|-----------|-------------|
| **UI Components** | `Button`, `Avatar`, `AvatarImage`, `AvatarFallback`, `Badge`, `Tabs`, `TabsContent`, `TabsList`, `TabsTrigger` (shadcn/ui) |
| **Ícones** | `Calendar`, `ExternalLink`, `CalendarClock`, `XCircle`, `Clock`, `Briefcase`, `Building2`, `Sun`, `Sunset`, `Moon`, `User`, `Video`, `Loader2`, `RefreshCw`, `Share2`, `Check`, `LayoutDashboard` (lucide-react) |
| **React** | `useState`, `useEffect`, `useCallback` |

### 2.3 Estrutura do Componente

```
TasksPageMVP
├── State
│   ├── todayInterviews: ScheduledInterview[]
│   ├── pastInterviews: ScheduledInterview[]
│   ├── isLoading: boolean
│   ├── error: string | null
│   └── copiedId: string | null
│
├── Effects
│   └── useEffect → fetchInterviews() on mount
│
├── Computed Values
│   ├── todayOnlyInterviews (dateLabel === 'Hoje')
│   ├── morningInterviews (time < '12:00')
│   ├── afternoonInterviews (time >= '12:00')
│   ├── futureInterviews (dateLabel !== 'Hoje')
│   ├── scheduledCount
│   └── timeUntilNext
│
├── Handlers
│   ├── fetchInterviews()
│   ├── handleOpenMeeting()
│   ├── handleCopyLink()
│   ├── handleReschedule()
│   ├── handleReject()
│   └── handleOpenJob()
│
├── Render Helpers
│   ├── renderJobLink()
│   └── renderCandidateInfo()
│
└── Layout
    ├── Header (título + saudação + resumo)
    ├── Tab: Entrevistas
    │   ├── Manhã (Sun icon)
    │   ├── Tarde (Sunset icon)
    │   └── Próximos Dias (Calendar icon, agrupado por data)
    └── Tab: Histórico
        └── Cards com badge de status
```

---

## 3. Modelo de Dados

### 3.1 Interface Backend (`BackendInterview`)

Dados que chegam da API `/api/v1/interviews`:

| Campo | Tipo | Origem | Descrição |
|-------|------|--------|-----------|
| `id` | `string` | `interviews.id` | UUID da entrevista |
| `title` | `string` | `interviews.title` | Título (ex: "Entrevista: João - Dev Frontend") |
| `description` | `string?` | `interviews.description` | Notas adicionais |
| `candidate_id` | `string?` | `interviews.candidate_id` | UUID do candidato (FK) |
| `candidate_name` | `string` | `interviews.candidate_name` | Nome do candidato |
| `candidate_email` | `string` | `interviews.candidate_email` | Email do candidato |
| `interviewer_name` | `string` | `interviews.interviewer_name` | Nome do entrevistador |
| `interviewer_email` | `string` | `interviews.interviewer_email` | Email do entrevistador |
| `interview_type` | `string` | `interviews.interview_type` | Tipo: technical, behavioral, cultural, final |
| `interview_mode` | `string` | `interviews.interview_mode` | Modo: video, in_person, phone |
| `start_time` | `string` | `interviews.start_time` | ISO 8601 datetime de início |
| `end_time` | `string` | `interviews.end_time` | ISO 8601 datetime de fim |
| `duration_minutes` | `number` | `interviews.duration_minutes` | Duração em minutos |
| `status` | `string` | `interviews.status` | scheduled, completed, cancelled, rescheduled, confirmed |
| `confirmation_status` | `string` | `interviews.confirmation_status` | Status de confirmação do candidato |
| `meeting_url` | `string?` | `interviews.meeting_url` | Link da reunião (Meet/Teams/Zoom) |
| `meeting_platform` | `string?` | `interviews.meeting_platform` | Plataforma: google_meet, teams, zoom |
| `location` | `string?` | `interviews.location` | Local (presencial) |
| `job_vacancy_id` | `string?` | `interviews.job_vacancy_id` | UUID da vaga (FK) |
| `job_title` | `string?` | `interviews.job_title` | Título da vaga |
| `job_code` | `string?` | `job_vacancies.job_id` (JOIN) | Código da vaga (ex: "FE-2026-001") |
| `job_manager` | `string?` | `job_vacancies.manager` (JOIN) | Gestor responsável pela vaga |
| `application_stage` | `string?` | `interviews.application_stage` | Etapa atual no pipeline |
| `is_synced_to_calendar` | `boolean` | `interviews.is_synced_to_calendar` | Se está sincronizado com calendário |
| `created_at` | `string?` | `interviews.created_at` | Data de criação |
| `cancelled_at` | `string?` | `interviews.cancelled_at` | Data de cancelamento |
| `cancellation_reason` | `string?` | `interviews.cancellation_reason` | Motivo do cancelamento |

### 3.2 Interface Frontend (`ScheduledInterview`)

Dados mapeados para uso no componente:

| Campo | Tipo | Origem | Descrição |
|-------|------|--------|-----------|
| `id` | `string` | `BackendInterview.id` | ID da entrevista |
| `candidateId` | `string` | `candidate_id` ou `id` | ID do candidato (fallback: id da entrevista) |
| `time` | `string` | Extraído de `start_time` | Horário formatado "HH:MM" |
| `date` | `string` | Extraído de `start_time` | Data "YYYY-MM-DD" |
| `dateLabel` | `string` | Calculado | "Hoje", "Amanhã", "Ontem", ou data formatada |
| `type` | `string` | `INTERVIEW_TYPE_LABELS[interview_type]` | Label traduzido do tipo |
| `interviewType` | `string` | `interview_type` | Tipo original (technical, behavioral, etc.) |
| `candidateName` | `string` | `candidate_name` sem "[DEMO] " | Nome limpo do candidato |
| `candidateAvatar` | `string?` | API `/candidates/{id}` → `avatar_url` | URL do avatar real |
| `candidateRole` | `string?` | API `/candidates/{id}` → `current_title` | Cargo atual |
| `jobId` | `string` | `job_vacancy_id` | ID da vaga |
| `jobCode` | `string` | JOIN `job_vacancies.job_id` | Código da vaga |
| `jobTitle` | `string` | `job_title` sem "[DEMO] " | Título da vaga |
| `company` | `string?` | API `/candidates/{id}` → `current_company` | Empresa atual |
| `jobManager` | `string?` | JOIN `job_vacancies.manager` | Gestor da vaga |
| `manager` | `string` | `interviewer_name` | Entrevistador designado |
| `currentStage` | `string` | `application_stage` ou tipo traduzido | Etapa no pipeline |
| `platform` | enum | Mapeado de `meeting_platform` | google_meet, microsoft_teams, zoom |
| `meetingLink` | `string` | `meeting_url` | Link da reunião |
| `duration` | `number` | `duration_minutes` | Duração em minutos |
| `status` | enum | `status` | scheduled, completed, cancelled, rescheduled, confirmed |
| `completedAt` | `string?` | Formatado de `cancelled_at` ou `created_at` | Data de conclusão |
| `cancelledAt` | `string?` | Formatado de `cancelled_at` | Data de cancelamento |
| `cancelReason` | `string?` | `cancellation_reason` | Motivo do cancelamento |

### 3.3 Mapeamento de Tipo de Entrevista

| Valor Backend | Label Frontend |
|--------------|----------------|
| `technical` | Entrevista Técnica |
| `behavioral` | Entrevista Comportamental |
| `cultural` | Fit Cultural |
| `final` | Entrevista Final |

### 3.4 Mapeamento de Plataforma

| Input Backend | Valor Frontend | Label |
|---------------|----------------|-------|
| `null` / desconhecido | `google_meet` | Google Meet |
| contém "teams" ou "microsoft" | `microsoft_teams` | Teams |
| contém "zoom" | `zoom` | Zoom |

### 3.5 Diagrama do Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND (lia-agent-system)                                      │
│                                                                  │
│  GET /api/v1/interviews?limit=100                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ SELECT interviews.*, job_vacancies.job_id,               │    │
│  │        job_vacancies.manager                             │    │
│  │ FROM interviews                                          │    │
│  │ LEFT JOIN job_vacancies                                   │    │
│  │   ON interviews.job_vacancy_id = job_vacancies.id        │    │
│  │ ORDER BY start_time DESC                                  │    │
│  │ LIMIT 100                                                 │    │
│  └─────────────────────────────┬───────────────────────────┘    │
│                                │                                 │
│                     BackendInterview[]                            │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ PROXY (Next.js API Route)                                       │
│                                                                  │
│  /api/backend-proxy/interviews/route.ts                         │
│  Passa headers de autenticação + query params                    │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (tasks-page-mvp.tsx)                                   │
│                                                                  │
│  1. Recebe BackendInterview[]                                    │
│  2. Busca dados de candidatos em paralelo:                      │
│     GET /api/backend-proxy/candidates/{id}                       │
│     → candidateRole, company, avatar_url                        │
│  3. mapBackendToScheduled() → ScheduledInterview[]              │
│  4. Filtra:                                                      │
│     ├── Agendadas: status in [scheduled,confirmed] AND >= hoje  │
│     └── Passadas: completed/cancelled/rescheduled OU < hoje     │
│  5. Ordena:                                                      │
│     ├── Agendadas: ASC por start_time                           │
│     └── Passadas: DESC por start_time                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Seção: Header e Saudação

### 4.1 Estrutura Visual

```
┌──────────────────────────────────────────────────────────┐
│ 📊 Painel de Controle                                     │
│                                                           │
│ ☀️ Bom dia, Ana                                           │
│    Sua agenda — Terça-feira, 25 de fevereiro de 2026     │
│    3 entrevistas hoje · 2 próximas | Próxima em 1h30min  │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Saudação Dinâmica

| Horário | Saudação | Ícone |
|---------|----------|-------|
| 00:00–11:59 | "Bom dia" | `Sun` (amarelo) |
| 12:00–17:59 | "Boa tarde" | `Sunset` (laranja) |
| 18:00–23:59 | "Boa noite" | `Moon` (índigo) |

### 4.3 Resumo do Dia

Exibido apenas quando existem entrevistas:

```
{scheduledCount} entrevista(s) hoje · {futureCount} próxima(s)
| Próxima em {timeUntilNext}
```

- **scheduledCount**: total de entrevistas com `dateLabel === 'Hoje'`
- **futureCount**: entrevistas futuras (não-hoje), exibido apenas se > 0
- **timeUntilNext**: calculado como diferença entre agora e a primeira entrevista scheduled do dia. Formatos: "Agora", "30min", "1h", "2h15min"

### 4.4 Nome Fixo

O nome "Ana" é hardcoded no componente. Em futuras versões, será substituído pelo nome do usuário autenticado.

---

## 5. Seção: Tabs — Entrevistas e Histórico

### 5.1 Estrutura das Tabs

```
┌──────────────────────────────────────────┐
│ [ Entrevistas (5) ] [ Histórico (12)  ]  │
└──────────────────────────────────────────┘
```

| Tab | Valor | Conteúdo | Contagem |
|-----|-------|----------|----------|
| **Entrevistas** | `entrevistas` (default) | Cards de entrevistas agendadas/futuras | `todayInterviews.length` |
| **Histórico** | `historico` | Cards de entrevistas concluídas/canceladas/reagendadas | `pastInterviews.length` |

### 5.2 Filtro de Dados

```
DADOS DA API (BackendInterview[])
        │
        ▼
   mapBackendToScheduled()
        │
        ▼
   ScheduledInterview[]
        │
        ├──────────────────────────────────────────┐
        │                                          │
        ▼                                          ▼
  todayInterviews                           pastInterviews
  (status in [scheduled,confirmed]          (status in [completed,
   AND start_time >= hoje)                   cancelled, rescheduled]
  Ordenação: ASC                            OR start_time < hoje)
        │                                  Ordenação: DESC
        ├── todayOnlyInterviews
        │   (dateLabel === 'Hoje')
        │   ├── morningInterviews (time < '12:00')
        │   └── afternoonInterviews (time >= '12:00')
        │
        └── futureInterviews
            (dateLabel !== 'Hoje')
            Agrupadas por dateLabel
```

### 5.3 Separadores de Período

Entrevistas do dia são separadas por ícones de período:

| Período | Condição | Ícone | Cor |
|---------|----------|-------|-----|
| Manhã | `time < '12:00'` | `Sun` | `text-amber-400` |
| Tarde | `time >= '12:00'` | `Sunset` | `text-orange-400` |
| Próximos dias | `dateLabel !== 'Hoje'` | `Calendar` | `text-gray-400` |

Cada separador tem uma linha horizontal (`border-t`) à direita do label.

---

## 6. Cards de Entrevista (Agendadas)

### 6.1 Anatomia do Card

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ┌──┐                                                                    │
│ │AV│  10:00 · Entrevista Técnica · 📹 Google Meet 🔗 · 60min          │
│ │AT│                                    [Abrir Reunião] [Alt.Horário]  │
│ │AR│                                                    [Cancelar]     │
│ └──┘                                                                    │
│       ┌─── GRID 2 COLUNAS ──────────────────────────────────┐          │
│       │ Col 1 (Candidato)      │ Col 2 (Vaga)               │          │
│       │ João Silva             │ FE-2026-001 Dev Frontend    │          │
│       │ 💼 Product Designer    │ 👤 Maria Santos             │          │
│       │ 🏢 Acme Corp           │                             │          │
│       └────────────────────────┴─────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Linha 1 — Header do Card

Layout: `flex items-center justify-between`

**Lado esquerdo** (informações):
```
{hora} · {tipo} · {ícone plataforma} {plataforma} {botão copiar link} · {duração}min
```

| Elemento | Font | Tamanho | Cor |
|----------|------|---------|-----|
| Hora | Inter, tabular-nums | 13px, semibold | gray-900 |
| Tipo | Open Sans | 12px, semibold | gray-900 |
| Plataforma | Open Sans | 11px | gray-500 |
| Duração | Inter, tabular-nums | 11px | gray-500 |
| Separadores (·) | — | — | gray-300 (light) / gray-600 (dark) |

**Botão Copiar Link** (inline, ao lado do nome da plataforma):
- Ícone: `Share2` (3.5×3.5) → `Check` verde quando copiado
- Feedback: troca para check por 2 segundos via `copiedId` state

**Lado direito** (ações):
- 3 botões: Abrir Reunião, Alterar Horário, Cancelar (detalhados na Seção 9)

### 6.3 Linha 2 — Informações do Candidato e Vaga

Renderizado por `renderCandidateInfo()`. Layout: `grid grid-cols-2 gap-4`.

Detalhado na Seção 8.

### 6.4 Avatar

Posicionado à esquerda do card, fora do grid de conteúdo.

| Propriedade | Valor |
|-------------|-------|
| Tamanho | 40×40px (`w-10 h-10`) |
| Fallback | Iniciais (2 caracteres) sobre fundo `rgba(96,190,209,0.15)` |
| Fonte | API `/candidates/{id}` → `avatar_url`, fallback: randomuser.me |
| Algoritmo de fallback | Hash determinístico de `id + name` → gênero alternado + número 0-98 |

### 6.5 Repetição de Cards

O mesmo layout de card é usado em 3 seções (manhã, tarde, próximos dias). Cada seção renderiza os cards individualmente (não componente extraído).

---

## 7. Cards de Histórico

### 7.1 Diferenças em Relação aos Cards de Entrevista

| Aspecto | Card Entrevista | Card Histórico |
|---------|----------------|----------------|
| **Status badge** | Não tem | Badge com status (Concluída/Cancelada/Reagendada) |
| **Botões de ação** | Abrir Reunião + Alterar Horário + Cancelar | Abrir Reunião + data de conclusão |
| **Hover** | `hover:border-gray-300` | Sem hover |
| **Motivo cancelamento** | Não exibido | Exibido em itálico abaixo do card |
| **Avatar** | Com fallback randomuser.me | Apenas randomuser.me (sem API candidato) |

### 7.2 Badge de Status

```
┌──────────────────────────────────┐
│ ● Concluída  │  ● Cancelada     │
│ ● Reagendada │                   │
└──────────────────────────────────┘
```

| Status | Label | Classe CSS |
|--------|-------|-----------|
| `completed` | "Concluída" | `bg-gray-100 text-gray-600 border-gray-200` |
| `cancelled` | "Cancelada" | `bg-gray-100 text-gray-500 border-gray-200` |
| `rescheduled` | "Reagendada" | `bg-gray-100 text-gray-500 border-gray-200` |

Badge usa `Badge` do shadcn com ícone de bolinha colorida (`w-1.5 h-1.5 rounded-full bg-gray-400`).

### 7.3 Data de Conclusão/Cancelamento

Exibida ao lado direito do header:
```
{completedAt || cancelledAt}
```

Formato: `"25 fev"` (dia + mês abreviado, sem ponto).

### 7.4 Motivo de Cancelamento

Se `interview.cancelReason` existe, exibido abaixo do `renderCandidateInfo`:
```html
<p class="text-[11px] text-gray-400 italic mt-1.5">
  {cancelReason}
</p>
```

---

## 8. Layout dos Cards — Grid de 2 Colunas

### 8.1 Estrutura do `renderCandidateInfo`

```
┌─────────────────────────────────────────────────────────────┐
│              grid grid-cols-2 gap-4                          │
│                                                              │
│  ┌─── Coluna 1 ──────────┐  ┌─── Coluna 2 ──────────────┐  │
│  │ Nome do Candidato      │  │ FE-2026-001 Dev Frontend   │  │
│  │ 💼 Cargo Atual         │  │ 👤 Gestor da Vaga          │  │
│  │ 🏢 Empresa Atual       │  │                            │  │
│  └────────────────────────┘  └────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Coluna 1 — Candidato

| Elemento | Ícone | Font | Tamanho | Cor |
|----------|-------|------|---------|-----|
| Nome | — | Open Sans, medium | 13px | gray-800 |
| Cargo | `Briefcase` (3×3) | — | 11px | gray-500 |
| Empresa | `Building2` (3×3) | — | 11px | gray-500 |

- Container: `space-y-0.5 min-w-0`
- Nome usa `truncate block` para overflow
- Cargo e empresa são opcionais (condicionais no render)

### 8.3 Coluna 2 — Vaga

| Elemento | Ícone | Font | Tamanho | Cor | Interação |
|----------|-------|------|---------|-----|-----------|
| ID + Título da Vaga | — | Open Sans (label) + Inter (código) | 11px | blue-600 | Clicável → `handleOpenJob` |
| Gestor | `User` (3×3) | — | 11px | gray-500 | — |

- Link da vaga: `button` com hover underline, cor azul, cursor pointer
- Código da vaga (`jobCode`) renderizado com `font-[Inter]` + `mr-0.5` antes do título
- Gestor da vaga é opcional (condicional no render)

### 8.4 Regras de Layout

| Regra | Implementação |
|-------|--------------|
| Grid divide o card ao meio | `grid grid-cols-2 gap-4` |
| Candidato à esquerda | Coluna 1, alinhamento natural (left) |
| Vaga no centro/direita | Coluna 2, alinhamento natural (left) — posição visual no centro do card |
| Sem `text-right` ou `justify-end` | Coluna 2 **não** tem alinhamento forçado à direita |
| Overflow protegido | `min-w-0` em ambas colunas + `truncate` nos textos |

---

## 9. Sistema de Ações nos Cards

### 9.1 Cards de Entrevista (Agendadas)

```
┌────────────────────────────────────────────────────────────┐
│ [Abrir Reunião]  [Alterar Horário]  [Cancelar]            │
│  bg-gray-900      outline/gray       outline/red          │
│  text-white        text-gray-700      text-red-600        │
└────────────────────────────────────────────────────────────┘
```

| Botão | Ícone | Estilo | Handler | Comportamento |
|-------|-------|--------|---------|---------------|
| **Abrir Reunião** | `ExternalLink` | Primary (`bg-gray-900 text-white`) | `handleOpenMeeting` | `window.open(meetingLink, '_blank')` |
| **Alterar Horário** | `CalendarClock` | Outline (gray border) | `handleReschedule` | localStorage + `onNavigate('Vagas')` |
| **Cancelar** | `XCircle` | Outline (red text/border) | `handleReject` | localStorage + `onNavigate('Vagas')` |

Todos os botões: `h-7 text-[11px] font-[Open_Sans] font-medium rounded-md`

### 9.2 Cards de Histórico

```
┌───────────────────────────────────────────────┐
│ [Abrir Reunião]                    25 fev     │
│  bg-gray-900                       gray-500   │
└───────────────────────────────────────────────┘
```

| Elemento | Descrição |
|----------|-----------|
| **Abrir Reunião** | Mesmo botão primary dos cards de entrevista |
| **Data** | `completedAt` ou `cancelledAt`, formato "25 fev" |

### 9.3 Botão Copiar Link (Inline)

Presente em todos os cards, ao lado do nome da plataforma:

| Estado | Ícone | Cor |
|--------|-------|-----|
| Normal | `Share2` (3.5×3.5) | gray-400 → hover: gray-600 |
| Copiado | `Check` (3.5×3.5, stroke 2.5) | emerald-500 |

Feedback dura 2 segundos (`setTimeout` → reset `copiedId`).

---

## 10. Integração com Outras Páginas

### 10.1 Navegação via `handleOpenJob`

Abre a vaga no Kanban com preview do candidato:

```
1. localStorage.setItem('navigateToCandidate', {
     candidateId, candidateName, jobId, jobTitle,
     currentStage,
     action: 'view',
     openTransitionModal: false
   })

2. onNavigate('Vagas')

3. jobs-page detecta → abre kanban-page
   → kanban-page lê localStorage
   → abre preview do candidato (sem modal de transição)
```

### 10.2 Navegação via `handleReschedule`

Reagenda a entrevista via fluxo de transição no Kanban:

```
1. localStorage.setItem('navigateToCandidate', {
     candidateId, candidateName, jobId, jobTitle,
     currentStage, interviewType,
     action: 'reschedule',
     openTransitionModal: true
   })

2. localStorage.setItem('liaPrompt', 
     "Reagendar entrevista '{tipo}' com {nome} para a vaga {vaga}, 
      originalmente às {hora}. Por favor, pergunte ao recrutador 
      qual o dia e horário de preferência para o novo agendamento."
   )

3. onNavigate('Vagas')

4. jobs-page → kanban-page
   → abre UniversalTransitionModal com prompt da LIA pré-preenchido
```

### 10.3 Navegação via `handleReject`

Cancela a entrevista via fluxo de transição:

```
1. localStorage.setItem('navigateToCandidate', {
     candidateId, candidateName, jobId, jobTitle,
     currentStage,
     action: 'cancel',
     openTransitionModal: true
   })

2. localStorage.setItem('liaPrompt',
     "Cancelar entrevista '{tipo}' com {nome} para a vaga {vaga} 
      às {hora}."
   )

3. onNavigate('Vagas')
```

### 10.4 Mapa de Navegação

```
┌──────────────────┐
│ Painel de        │
│ Controle         │
│ (tasks-page-mvp) │
└────────┬─────────┘
         │
         ├── handleOpenJob ──────→ Vagas → Kanban → Preview Candidato
         │                         (action: 'view', sem modal)
         │
         ├── handleReschedule ──→ Vagas → Kanban → UniversalTransitionModal
         │                         (action: 'reschedule', com liaPrompt)
         │
         └── handleReject ──────→ Vagas → Kanban → UniversalTransitionModal
                                   (action: 'cancel', com liaPrompt)
```

### 10.5 Mapeamento interviewType → Pipeline Stage

Para o fluxo "Alterar Horário", o `interviewType` da entrevista precisa ser mapeado para o `slug` da etapa do pipeline (feito no Kanban via `interviewSlugMap`):

| `interviewType` | Pipeline Slug |
|-----------------|---------------|
| `technical` | `interview_hr` |
| `behavioral` | `interview_hr` |
| `cultural` | `interview_hr` |
| `final` | `interview_final` |

---

## 11. Integração Backend — API de Entrevistas

### 11.1 Endpoint Principal: `GET /api/v1/interviews`

**Arquivo**: `lia-agent-system/app/api/v1/interviews.py`

**Query com JOIN**:
```sql
SELECT interviews.*, 
       job_vacancies.job_id AS job_code,
       job_vacancies.manager AS job_manager
FROM interviews
LEFT JOIN job_vacancies 
  ON interviews.job_vacancy_id = job_vacancies.id
WHERE [filters]
ORDER BY start_time DESC
LIMIT {limit}
```

**Parâmetros**:

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `status` | `string?` | — | Filtro por status |
| `candidate_email` | `string?` | — | Filtro por email do candidato |
| `interviewer_email` | `string?` | — | Filtro por email do entrevistador |
| `limit` | `int` | 50 (max 100) | Número de resultados |

### 11.2 Outros Endpoints de Entrevista

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/v1/interviews/schedule` | Cria entrevista com integração Microsoft Calendar |
| `POST` | `/api/v1/interviews/{id}/cancel` | Cancela entrevista + calendar |
| `POST` | `/api/v1/interviews/{id}/complete` | Marca como concluída + dispatch evento |
| `POST` | `/api/v1/interviews/{id}/reschedule` | Reagenda + atualiza calendar |
| `POST` | `/api/v1/interviews/check-availability` | Verifica disponibilidade do entrevistador |
| `POST` | `/api/v1/interviews/{id}/feedback` | Submete feedback da entrevista |
| `POST` | `/api/v1/interviews/generate-email-template` | Gera template de email via IA (Claude) |
| `POST` | `/api/v1/interviews/schedule-from-prompt` | Agenda via linguagem natural (LIA) |

### 11.3 Integração com Microsoft Calendar

O `schedule` e `reschedule` integram com o Microsoft Graph API via `calendar_service`:

```
schedule_interview()
    │
    ├── calendar_service.schedule_interview()
    │   → Microsoft Graph: POST /calendar/events
    │   → Cria evento com Teams meeting
    │   → Retorna meeting_url
    │
    └── Salva interview no banco
        → meeting_url = joinUrl do Teams
        → is_synced_to_calendar = true
```

### 11.4 Enriquecimento de Dados no Frontend

Após receber as entrevistas da API, o frontend faz requests paralelos para enriquecer dados dos candidatos:

```
1. Extrai candidateIds únicos das entrevistas
2. Para cada candidateId:
   GET /api/backend-proxy/candidates/{id}
   → avatar_url → candidateAvatar
   → current_title → candidateRole
   → current_company → company
3. Mapeia dados enriquecidos em cada ScheduledInterview
```

---

## 12. Proxy Frontend → Backend

### 12.1 Arquivo do Proxy

**Arquivo**: `plataforma-lia/src/app/api/backend-proxy/interviews/route.ts`

| Aspecto | Valor |
|---------|-------|
| URL Backend | `process.env.NEXT_PUBLIC_BACKEND_URL` ou `http://127.0.0.1:8000` |
| Método | GET |
| Headers | Auth headers via `getAuthHeaders(request)` |
| Query params | Repassados transparentemente |

### 12.2 Tratamento de Erros

| Cenário | Resposta |
|---------|----------|
| Backend retorna erro | `{ error, details }` com status do backend |
| Conexão falha | `{ error: 'Erro ao conectar com o backend' }`, status 500 |

---

## 13. Funções Utilitárias

### 13.1 Tabela de Funções

| Função | Input | Output | Descrição |
|--------|-------|--------|-----------|
| `getGreeting()` | — | `string` | Saudação baseada na hora |
| `getGreetingIcon()` | — | `JSX` | Ícone Sol/Pôr-do-sol/Lua |
| `getFormattedDate()` | — | `string` | Data formatada em PT-BR (Capitalizada) |
| `getPlatformIcon(platform)` | enum | `JSX` | Ícone `Video` |
| `getPlatformLabel(platform)` | enum | `string` | "Google Meet" / "Teams" / "Zoom" |
| `getStatusLabel(status)` | `string` | `string` | "Concluída" / "Cancelada" / "Reagendada" |
| `getStatusClasses(status)` | `string` | `string` | Classes CSS do badge |
| `getStatusIcon(status)` | `string` | `JSX` | Bolinha colorida |
| `getTimeUntilNext(interviews)` | `ScheduledInterview[]` | `string?` | "Agora" / "30min" / "2h15min" |
| `getAvatarUrl(id, name)` | `string, string` | `string` | URL randomuser.me determinística |
| `getInitials(name)` | `string` | `string` | 2 caracteres iniciais |
| `mapPlatform(platform)` | `string?` | enum | Mapeia string para enum de plataforma |
| `formatDateShort(dateStr)` | `string` | `string` | "25 fev" (sem ponto) |
| `getDateLabel(date)` | `Date` | `string` | "Hoje" / "Amanhã" / "Ontem" / data formatada |
| `mapBackendToScheduled(bi, candidateInfo)` | `BackendInterview, Record?` | `ScheduledInterview` | Transforma dados do backend para o frontend |

---

## 14. Design System Aplicado

### 14.1 Tipografia

| Elemento | Font Family | Peso | Tamanho |
|----------|------------|------|---------|
| Título "Painel de Controle" | Open Sans | semibold | 20px (xl) |
| Saudação "Boa tarde, Ana" | Open Sans | semibold | 18px |
| Subtítulo "Sua agenda" | Open Sans | regular | 13px |
| Hora no card | Inter | semibold, tabular-nums | 13px |
| Tipo de entrevista | Open Sans | semibold | 12px |
| Plataforma/duração | Open Sans / Inter | regular | 11px |
| Nome candidato | Open Sans | medium | 13px |
| Cargo/Empresa/Gestor | — | regular | 11px |
| Label tabs | Open Sans | semibold (ativa) | 12px |
| Botões | Open Sans | medium | 11px |

### 14.2 Cores

| Elemento | Light Mode | Dark Mode |
|----------|-----------|-----------|
| Fundo página | `bg-gray-50` | `bg-gray-950` |
| Card | `bg-white border-gray-200` | `bg-gray-900 border-gray-700` |
| Card hover | `border-gray-300` | `border-gray-600` |
| Texto primário | `text-gray-900` | `text-gray-50` |
| Texto secundário | `text-gray-500` | `text-gray-400` |
| Link da vaga | `text-blue-600` | `text-blue-400` |
| Botão primary | `bg-gray-900 text-white` | `bg-gray-50 text-gray-900` |
| Botão cancelar | `text-red-600 border-red-200` | `text-red-400 border-red-800` |
| Separadores (·) | `text-gray-300` | `text-gray-600` |
| Avatar fallback bg | `rgba(96,190,209,0.15)` | `rgba(96,190,209,0.15)` |

### 14.3 Espaçamento

| Elemento | Valor |
|----------|-------|
| Padding do card | `p-3.5` (14px) |
| Gap entre avatar e conteúdo | `gap-3` (12px) |
| Gap entre colunas do grid | `gap-4` (16px) |
| Espaço vertical entre cards | `space-y-2` (8px) |
| Altura dos botões | `h-7` (28px) |

### 14.4 Componentes Shadcn Utilizados

| Componente | Uso |
|-----------|------|
| `Button` | Ações nos cards |
| `Avatar` + `AvatarImage` + `AvatarFallback` | Foto do candidato |
| `Badge` | Status no histórico |
| `Tabs` + `TabsList` + `TabsTrigger` + `TabsContent` | Navegação Entrevistas/Histórico |

---

## 15. Estados da Interface

### 15.1 Loading

```
┌──────────────────────────────────────┐
│                                      │
│           ⏳ (spinning)              │
│     Carregando entrevistas...        │
│                                      │
└──────────────────────────────────────┘
```

- Ícone: `Loader2` com `animate-spin`
- Texto: "Carregando entrevistas..."

### 15.2 Erro

```
┌──────────────────────────────────────┐
│                                      │
│          📅 (calendar icon)          │
│       Erro ao carregar               │
│       {mensagem de erro}             │
│       [🔄 Tentar novamente]          │
│                                      │
└──────────────────────────────────────┘
```

- Botão "Tentar novamente" chama `fetchInterviews()`

### 15.3 Vazio — Entrevistas

```
┌──────────────────────────────────────┐
│                                      │
│          📅 (calendar icon)          │
│   Nenhuma entrevista agendada        │
│     Sua agenda está livre.           │
│                                      │
└──────────────────────────────────────┘
```

### 15.4 Vazio — Histórico

```
┌──────────────────────────────────────┐
│                                      │
│          🕐 (clock icon)             │
│        Nenhum histórico              │
│  Suas entrevistas passadas           │
│      aparecerão aqui.                │
│                                      │
└──────────────────────────────────────┘
```

---

## 16. Fluxos Completos End-to-End

### 16.1 Fluxo: Recrutador Abre Reunião

```
1. Recrutador abre Painel de Controle
   → fetchInterviews() dispara
   → API retorna entrevistas com JOIN job_vacancies
   → Dados de candidatos enriquecidos em paralelo

2. Tab "Entrevistas" (default) mostra cards
   → Cards organizados: Manhã / Tarde / Próximos Dias

3. Recrutador clica [Abrir Reunião] no card das 10:00
   → window.open(meetingLink, '_blank')
   → Nova aba abre com Google Meet/Teams/Zoom
```

### 16.2 Fluxo: Recrutador Reagenda Entrevista

```
1. Recrutador vê card de entrevista às 15:00
   → Clica [Alterar Horário]

2. Sistema prepara navegação:
   → localStorage.navigateToCandidate = {
       candidateId, jobId, action: 'reschedule',
       openTransitionModal: true, interviewType
     }
   → localStorage.liaPrompt = "Reagendar entrevista..."

3. onNavigate('Vagas') → jobs-page detecta localStorage
   → Navega para kanban-page da vaga
   → Kanban abre candidato no pipeline
   → UniversalTransitionModal abre com prompt da LIA

4. Recrutador interage com LIA:
   → LIA: "Para quando deseja reagendar?"
   → Recrutador: "Quinta às 14h"
   → LIA agenda nova entrevista
```

### 16.3 Fluxo: Recrutador Cancela Entrevista

```
1. Recrutador vê card e clica [Cancelar]

2. Sistema prepara navegação:
   → localStorage.navigateToCandidate = {
       action: 'cancel', openTransitionModal: true
     }
   → localStorage.liaPrompt = "Cancelar entrevista..."

3. Navega para Kanban → Modal de transição
   → Recrutador confirma cancelamento
   → API cancela: POST /interviews/{id}/cancel
   → Calendar event cancelado via Microsoft Graph
```

### 16.4 Fluxo: Recrutador Abre Vaga do Candidato

```
1. Recrutador vê link azul "FE-2026-001 Dev Frontend" no card
   → Clica no link

2. handleOpenJob:
   → localStorage.navigateToCandidate = {
       action: 'view', openTransitionModal: false
     }
   → onNavigate('Vagas')

3. jobs-page → kanban-page da vaga
   → Preview do candidato abre (lateral)
   → Sem modal de transição
   → Recrutador vê perfil completo
```

### 16.5 Fluxo: Copiar Link da Reunião

```
1. Recrutador clica ícone 🔗 (Share2) ao lado de "Google Meet"

2. navigator.clipboard.writeText(meetingLink)
   → Ícone muda para ✓ (Check, verde)
   → Após 2s, volta para 🔗

3. Recrutador cola link onde precisar
```

---

## 17. Endpoints da API

### Entrevistas

| Método | Endpoint | Descrição | Usado pelo Painel? |
|--------|----------|-----------|-------------------|
| `GET` | `/api/v1/interviews` | Lista entrevistas com filtros + JOIN job_vacancies | ✅ Principal |
| `POST` | `/api/v1/interviews/schedule` | Cria entrevista + Calendar | ❌ (via chat/kanban) |
| `POST` | `/api/v1/interviews/{id}/cancel` | Cancela entrevista | ❌ (via kanban após nav) |
| `POST` | `/api/v1/interviews/{id}/complete` | Marca como concluída | ❌ (via kanban) |
| `POST` | `/api/v1/interviews/{id}/reschedule` | Reagenda | ❌ (via kanban após nav) |
| `POST` | `/api/v1/interviews/check-availability` | Disponibilidade | ❌ |
| `POST` | `/api/v1/interviews/{id}/feedback` | Feedback pós-entrevista | ❌ |
| `POST` | `/api/v1/interviews/generate-email-template` | Gera email via IA | ❌ |
| `POST` | `/api/v1/interviews/schedule-from-prompt` | Agenda via linguagem natural | ❌ |

### Candidatos (Enriquecimento)

| Método | Endpoint | Descrição | Usado pelo Painel? |
|--------|----------|-----------|-------------------|
| `GET` | `/api/v1/candidates/{id}` | Dados do candidato | ✅ (avatar, cargo, empresa) |

### Proxy (Next.js)

| Rota Frontend | Rota Backend |
|--------------|-------------|
| `/api/backend-proxy/interviews/` | `/api/v1/interviews` |
| `/api/backend-proxy/candidates/{id}` | `/api/v1/candidates/{id}` |

---

## 18. Glossário

| Termo | Definição | Seção |
|-------|-----------|-------|
| **Painel de Controle** | Página inicial do recrutador (Dashboard). Mostra agenda de entrevistas, histórico e ações rápidas | §1 |
| **Card de Entrevista** | Componente visual que representa uma entrevista agendada ou futura. Contém header (hora/tipo/plataforma/duração), botões de ação e info do candidato/vaga | §6 |
| **Card de Histórico** | Variação do card para entrevistas passadas. Inclui badge de status e data de conclusão | §7 |
| **renderCandidateInfo** | Função que renderiza o grid de 2 colunas (candidato + vaga) na segunda linha do card | §8 |
| **renderJobLink** | Função que renderiza o link clicável da vaga (código + título, em azul) | §8.3 |
| **handleOpenMeeting** | Abre link da reunião em nova aba do navegador | §9.1 |
| **handleReschedule** | Navega para Kanban com prompt da LIA para reagendamento | §10.2 |
| **handleReject** | Navega para Kanban com prompt da LIA para cancelamento | §10.3 |
| **handleOpenJob** | Navega para Kanban com preview do candidato (sem modal) | §10.1 |
| **navigateToCandidate** | Chave do localStorage usada para comunicar dados de navegação entre páginas | §10 |
| **liaPrompt** | Chave do localStorage com prompt em linguagem natural para a LIA processar no Kanban | §10.2 |
| **BackendInterview** | Interface TypeScript dos dados que chegam da API `/api/v1/interviews` | §3.1 |
| **ScheduledInterview** | Interface TypeScript dos dados mapeados para uso no frontend | §3.2 |
| **job_code** | Código da vaga (ex: "FE-2026-001"), obtido via JOIN com `job_vacancies.job_id` | §3.1 |
| **job_manager** | Gestor da vaga, obtido via JOIN com `job_vacancies.manager` | §3.1 |
| **interviewSlugMap** | Mapeamento de `interviewType` para slug do pipeline no Kanban | §10.5 |
| **timeUntilNext** | Tempo até a próxima entrevista do dia. Formatos: "Agora", "30min", "2h15min" | §4.3 |
| **Proxy** | API Route do Next.js que repassa requests para o backend Python, adicionando headers de autenticação | §12 |
| **enriquecimento** | Processo de buscar dados adicionais do candidato (cargo, empresa, avatar) via API de candidatos após receber as entrevistas | §11.4 |

---

## 19. Status de Implementação e Roadmap

### 19.1 Funcionalidades Implementadas

| Feature | Status | Notas |
|---------|--------|-------|
| Header com saudação dinâmica | ✅ Implementado | Ícone + saudação por período do dia |
| Resumo do dia (contagem + próxima) | ✅ Implementado | Conta entrevistas + timer |
| Tab Entrevistas | ✅ Implementado | Separadores manhã/tarde/próximos dias |
| Tab Histórico | ✅ Implementado | Badge de status + data conclusão |
| Cards com grid 2 colunas | ✅ Implementado | Candidato esq. + vaga centro |
| Job link clicável | ✅ Implementado | Navega para Kanban com preview |
| Gestor da vaga | ✅ Implementado | Ícone User + nome do gestor |
| Botão Abrir Reunião | ✅ Implementado | Nos cards de entrevista e histórico |
| Botão Alterar Horário | ✅ Implementado | Navega + liaPrompt |
| Botão Cancelar | ✅ Implementado | Navega + liaPrompt |
| Copiar link reunião | ✅ Implementado | Share2 → Check com feedback 2s |
| JOIN com job_vacancies | ✅ Implementado | job_code + job_manager via SQL |
| Enriquecimento candidatos | ✅ Implementado | cargo, empresa, avatar via API paralela |
| Dark mode | ✅ Implementado | Todas as cores têm variante dark |
| Estados loading/erro/vazio | ✅ Implementado | 4 estados com UI dedicada |

### 19.2 Roadmap — Funcionalidades Futuras

| Feature | Prioridade | Descrição |
|---------|-----------|-----------|
| **Nome dinâmico do usuário** | Alta | Substituir "Ana" hardcoded pelo nome do usuário autenticado |
| **Ações Urgentes** | Alta | Seção com alertas de feedbacks pendentes, vagas sem movimento, candidatos sem resposta |
| **Agenda do Dia (compact)** | Média | Mini-cards horizontais mostrando próximas entrevistas em formato compacto |
| **Insights LIA** | Média | Cards com sugestões da IA (feedbacks acumulados, ofertas pendentes) |
| **Pipeline summary** | Média | Barra inferior com resumo do pipeline global (Em Triagem: X, Entrevista: Y, etc.) |
| **KPIs cards** | Média | Cards de métricas: Urgentes, Tarefas Hoje, Entrevistas, Alertas |
| **Filtro por status** | Baixa | Filtro nas tabs por tipo de entrevista ou plataforma |
| **Notificações em tempo real** | Baixa | Polling ou WebSocket para atualizar cards quando status muda |
| **Botão Nova Tarefa** | Baixa | Ação rápida para criar tarefa/entrevista diretamente do painel |
| **Sync com calendário externo** | Baixa | Exibir eventos do Google Calendar/Outlook além das entrevistas da plataforma |

### 19.3 Seed de Dados para Desenvolvimento

Para popular entrevistas de demonstração:

```bash
cd lia-agent-system && PYTHONPATH=. python3 scripts/seed_interviews_demo.py
```

O seed cria entrevistas com diferentes tipos, plataformas, status e datas para testar todos os cenários do Painel de Controle.

---

## Apêndice A: Arquivos Relacionados

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `plataforma-lia/src/components/pages/tasks-page-mvp.tsx` | Frontend | Componente principal do Painel de Controle |
| `plataforma-lia/src/app/api/backend-proxy/interviews/route.ts` | Proxy | Rota API que repassa requests para o backend |
| `lia-agent-system/app/api/v1/interviews.py` | Backend | Endpoints REST de entrevistas |
| `lia-agent-system/app/models/interview.py` | Backend | Modelo SQLAlchemy da entrevista |
| `lia-agent-system/app/models/job_vacancy.py` | Backend | Modelo SQLAlchemy da vaga (JOIN) |
| `lia-agent-system/app/services/calendar_service.py` | Backend | Integração com Microsoft Calendar |
| `lia-agent-system/app/services/scheduling_service.py` | Backend | Serviço de agendamento |
| `lia-agent-system/scripts/seed_interviews_demo.py` | Script | Seed de entrevistas demo |
| `plataforma-lia/src/components/pages/jobs-page.tsx` | Frontend | Página de vagas (destino da navegação) |
| `plataforma-lia/src/components/pages/job-kanban-page.tsx` | Frontend | Kanban da vaga (destino final da navegação) |
