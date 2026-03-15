# CARDS JIRA — Criação Manual de Vagas e Ciclo de Vida
**Épico:** Gestão de Vagas (VGM)
**Data:** Março 2026
**Stack de produção:** Vue 3 + Vuetify 3 + Nuxt 3 + Pinia (FE) · FastAPI/Python (BE) · PostgreSQL
**Referência prototype:** `plataforma-lia/` (Next.js) + `lia-agent-system/` (FastAPI)
**Skills obrigatórias em cada card FE:** `/vue-migration-prep` · `/design-standardize` · `/feature-impact`

> **Convenção de IDs:** `VGM-001` a `VGM-010`
> **Status do fluxo no protótipo:** parcialmente implementado — seções marcadas com ⚠️ indicam gaps a completar.

---

## FONTES DE VERDADE — Referências do Repositório

> Para agentes de IA (Cursor, Claude Code): **não reimplemente os padrões abaixo**. Leia os arquivos indicados e replique os padrões exatos já estabelecidos no protótipo. O protótipo é a fonte de verdade para todos os contratos de API, interfaces TypeScript, mapeamentos de campos e fluxos de negócio.

### Frontend (TypeScript / Next.js → migrar para Vue 3 + Nuxt 3)

#### Interfaces e Types Centrais

| Contrato | Arquivo | Linha |
|---------|---------|-------|
| `JobVacancy` interface (modelo completo) | `plataforma-lia/src/services/lia-api.ts` | 2691 |
| `JobVacancyCreateRequest` interface (campos para POST) | `plataforma-lia/src/services/lia-api.ts` | 2814 |
| `JobVacancyUpdateRequest` interface (campos para PATCH) | `plataforma-lia/src/services/lia-api.ts` | ~2830 |
| `ManualFormData` interface (dados do formulário manual) | `plataforma-lia/src/components/modals/create-job-modal.tsx` | ~35 |
| `JobEditForm` interface (estado do formulário de edição) | `plataforma-lia/src/components/pages/job-kanban-page.tsx` | ~95 |

#### Serviços de API

| Método | Arquivo | Linha | Retorno |
|--------|---------|-------|---------|
| `createJobVacancy(payload)` | `plataforma-lia/src/services/lia-api.ts` | ~2820 | `{ id, title, status, ... }` |
| `updateJobVacancy(id, payload)` | `plataforma-lia/src/services/lia-api.ts` | ~2840 | `JobVacancy` |
| `generatePublicLink(jobId)` | `plataforma-lia/src/services/lia-api.ts` | 974 | `{ success, public_url, slug, message }` |
| `getJobVacancies(companyId, page, limit)` | `plataforma-lia/src/services/lia-api.ts` | ~2690 | `{ items: JobVacancy[], total }` |
| `closeJobVacancy(jobId, payload)` | `plataforma-lia/src/services/lia-api.ts` | ~2900 | `JobVacancy` |

#### Transformações e Mapeamentos

| Lógica | Arquivo | Linha | Descrição |
|--------|---------|-------|-----------|
| `mapJob()` — converte `JobVacancy` → estado local UI | `plataforma-lia/src/components/pages/jobs-page.tsx` | ~174–240 | Transforma campos API em propriedades do componente |
| `fieldMapping` — camelCase FE → snake_case API | `plataforma-lia/src/components/pages/job-kanban-page.tsx` | ~3106–3130 | `title→title`, `department→department`, `workModel→work_model`, `type→employment_type`, `level→seniority_level`, `manager→hiring_manager`, `managerEmail→hiring_manager_email` |
| `salary_range` builder | `plataforma-lia/src/components/pages/job-kanban-page.tsx` | ~3120 | `{ min, max, currency: 'BRL' }` montado a partir de `salaryMin`/`salaryMax` |
| `handleSaveJobSection` — salva seção do formulário | `plataforma-lia/src/components/pages/job-kanban-page.tsx` | ~3080 | Referência para lógica de salvamento incremental por seção |
| `handlePublishJob` — auto-save + gerar link + status | `plataforma-lia/src/components/pages/job-kanban-page.tsx` | ~442 | Constrói payload completo com todos campos não-vazios antes de publicar |

#### Componentes Principais e State Management

| Componente / Hook | Arquivo | Linhas |
|------------------|---------|--------|
| Modal escolha + formulário manual | `plataforma-lia/src/components/modals/create-job-modal.tsx` | 1–226 |
| Página de listagem de vagas (state pai) | `plataforma-lia/src/components/pages/jobs-page.tsx` | ver `showCreateJobModal`, `pendingNavigateJobId`, `jobsRefreshKey` |
| Navegação pós-criação via callback | `plataforma-lia/src/components/pages/jobs-page.tsx` | prop `onJobCreated` → `setPendingNavigateJobId` + `setJobsRefreshKey` |
| Watcher navegação (`pendingNavigateJobId`) | `plataforma-lia/src/components/pages/jobs-page.tsx` | `useEffect([allJobs, pendingNavigateJobId])` |
| Kanban / detalhe da vaga | `plataforma-lia/src/components/pages/job-kanban-page.tsx` | componente completo |
| Tab de configurações da vaga | `plataforma-lia/src/components/jobs/JobEditTab.tsx` | `SECTIONS` array: linha 65; banner `isCreationMode`: linhas 316–342 |
| Modal fechar vaga | `plataforma-lia/src/components/modals/close-vacancy-modal.tsx` | arquivo completo |
| Modal pausar/reativar | `plataforma-lia/src/components/modals/job-status-modal.tsx` | arquivo completo |

#### Sinalização de Modo de Criação

| Sinal | Mecanismo | Onde Lido |
|-------|-----------|-----------|
| `localStorage("jobCreationMode")` | Setado em `jobs-page.tsx` no callback `onJobCreated` com valor = `jobId` | Lido em `job-kanban-page.tsx` no `useEffect` de mount para abrir `activeTab="edit"` e `isCreationMode=true` |

### Backend (FastAPI / Python)

#### Endpoints Críticos

| Endpoint | Arquivo | Linha | Método |
|---------|---------|-------|--------|
| `POST /api/v1/job-vacancies` — criar vaga | `lia-agent-system/app/api/v1/job_vacancies.py` | 2021 | Recebe `JobVacancyCreate` schema |
| `PATCH /api/v1/job-vacancies/{id}` — atualizar campos | `lia-agent-system/app/api/v1/job_vacancies.py` | ~2100 | Partial update |
| `POST /api/v1/job-vacancies/{id}/generate-link` — publicar | `lia-agent-system/app/api/v1/job_vacancies.py` | ~2200 | Retorna `{ public_url, slug }` |
| `PATCH /api/v1/job-vacancies/{id}/status` — alterar status | `lia-agent-system/app/api/v1/job_vacancies.py` | ~3119 | Aceita `{ status }` |
| `POST /api/v1/job-vacancies/{id}/close` — fechar vaga | `lia-agent-system/app/api/v1/job_vacancies.py` | ~2400 | Aceita `{ reason, placement_candidate_id }` |

#### Schemas e Modelos

| Schema / Model | Arquivo | Linha |
|---------------|---------|-------|
| `JobVacancyCreate` (campos aceitos no POST) | `lia-agent-system/app/api/v1/job_vacancies.py` | 99–138 |
| `JobVacancyUpdate` (campos aceitos no PATCH) | `lia-agent-system/app/api/v1/job_vacancies.py` | ~140 |
| `JobVacancy` SQLAlchemy model | `lia-agent-system/app/models/job_vacancy.py` | ver campos: `work_model`, `employment_type`, `seniority_level`, `hiring_manager`, `salary_range` |

#### Lógica de Negócio

| Função | Arquivo | Linha | Descrição |
|--------|---------|-------|-----------|
| `derive_screening_status()` | `lia-agent-system/app/api/v1/job_vacancies.py` | 2872 | Calcula badge de triagem a partir de `screening_config` |
| `screening_status` computed field | `lia-agent-system/app/api/v1/job_vacancies.py` | 2909 | Retornado no response de `GET /job-vacancies/{id}` |
| Valores `work_model` aceitos | schema | — | `"remoto"`, `"hibrido"`, `"presencial"` (sem acento) |
| Valores `employment_type` aceitos | schema | — | `"CLT"`, `"PJ"`, `"Estágio"`, `"Temporário"`, `"Freelancer"` |
| Valores `status` aceitos | schema | — | `"draft"`, `"active"`, `"paused"`, `"closed"` |
| `company_id` injetado | endpoint | — | Via `get_user_company_id(current_user)` — **nunca enviado pelo FE** |

### Design System e Portabilidade Vue

| Recurso | Caminho |
|---------|---------|
| Design System v4.2.1 canônico | `plataforma-lia/docs/design-system/00-design-system-v4.md` |
| Skill Vue migration prep (padrões Vue 3 + Vuetify 3) | `.agents/skills/vue-migration-prep/SKILL.md` |
| Skill design-standardize (tokens, cores, tipografia) | `.agents/skills/design-standardize/SKILL.md` |
| Skill feature-impact (impacto em 12 dimensões) | `.agents/skills/feature-impact/SKILL.md` |
| Regras condensadas para Cursor | `.cursor/rules/vue-migration-prep.mdc` |
| Tokens tailwind (wedo-* colors) | `plataforma-lia/tailwind.config.ts` |

### Comunicação e Notificações

| Serviço | Arquivo | Descrição |
|---------|---------|-----------|
| Serviço central de notificações | `lia-agent-system/app/services/notification_service.py` | 5 canais: Bell, Email, Teams, WhatsApp, Chat inline |
| Mapa de alertas e comunicações | `docs/integracao/communication-alerts-map.md` | Referência completa de quando/o que notificar |
| SendGrid (email transacional) | `lia-agent-system/app/services/email_service.py` | Templates de fechamento, placement |
| WhatsApp Meta API | `lia-agent-system/app/services/whatsapp_service.py` | Notificações para candidatos |

### Rotas Proxy (Next.js → FastAPI)

| Rota Proxy FE | Arquivo |
|--------------|---------|
| `POST /api/backend-proxy/job-vacancies` | `plataforma-lia/src/app/api/backend-proxy/job-vacancies/route.ts` |
| `PATCH /api/backend-proxy/job-vacancies/[id]` | `plataforma-lia/src/app/api/backend-proxy/job-vacancies/[id]/route.ts` |
| `POST /api/backend-proxy/job-vacancies/[id]/generate-link` | `plataforma-lia/src/app/api/backend-proxy/job-vacancies/[id]/generate-link/route.ts` |

---

## ÍNDICE DE CARDS

| ID | Título | Prioridade | Status Protótipo |
|----|--------|-----------|-----------------|
| VGM-001 | Modal de Escolha: LIA vs Criação Manual | Alta | ✅ Implementado |
| VGM-002 | Formulário de Criação Manual de Vaga | Alta | ✅ Implementado |
| VGM-003 | Navegação Automática pós-criação → Tab Configurações | Alta | ✅ Implementado |
| VGM-004 | Tab Configurações da Vaga (JobEditTab completo) | Alta | ✅ Implementado |
| VGM-005 | Publicação da Vaga: Auto-save + Link + Status Ativa | Alta | ✅ Implementado |
| VGM-006 | Header da Vaga: Badge Status + Popover de Ações | Alta | ✅ Implementado |
| VGM-007 | Badge de Triagem no Header + Controle de Status | Média | ✅ Implementado |
| VGM-008 | Modal Pausar / Reativar Vaga | Alta | ✅ Implementado |
| VGM-009 | Modal Fechar Vaga com Placement de Candidato | Alta | ⚠️ **ATENÇÃO: NÃO IMPLEMENTAR AGORA** — fluxo de fechamento e placement está INCOMPLETO no protótipo. UI existe mas chamadas de API reais e notificações ainda não foram implementadas. Aguardar VGM-010 ser especificado e aprovado antes de construir. |
| VGM-010 | Envio Final: Notificações de Fechamento e Placement | Alta | ❌ **NÃO IMPLEMENTADO** — especificação completa neste documento, mas depende de VGM-009 estar finalizado |

---

## RESUMO DE DEPENDÊNCIAS

```
VGM-001 (Modal Escolha)
  └── VGM-002 (Formulário Manual)
        └── VGM-003 (Navegação Automática)
              └── VGM-004 (Tab Configurações)
                    └── VGM-005 (Publicação)
                          └── VGM-006 (Header + Status)
                                ├── VGM-007 (Triagem Badge)
                                ├── VGM-008 (Pausar/Reativar)
                                └── VGM-009 (Fechar Vaga) ⚠️ INCOMPLETO — NÃO IMPLEMENTAR AGORA
                                      └── VGM-010 (Envio Notificações) ← NÃO IMPLEMENTADO
```

---

## STATUS DE IMPLEMENTAÇÃO NO PROTÓTIPO

| Card | Protótipo | Falta para Produção |
|------|-----------|---------------------|
| VGM-001 | ✅ Completo | Converter para Vue |
| VGM-002 | ✅ Completo | Converter para Vue |
| VGM-003 | ✅ Completo | Usar Pinia + Vue Router |
| VGM-004 | ✅ Completo | Converter para Vue |
| VGM-005 | ✅ Completo | Converter para Vue |
| VGM-006 | ✅ Completo | Converter para Vue |
| VGM-007 | ✅ Completo | Converter para Vue |
| VGM-008 | ✅ Completo | Converter para Vue |
| VGM-009 | ⚠️ UI OK, lógica incompleta | **NÃO IMPLEMENTAR AGORA** — Implementar chamadas API reais + notificações apenas após aprovação |
| VGM-010 | ❌ Não implementado | **NÃO IMPLEMENTAR AGORA** — Implementar do zero após VGM-009 aprovado |

---

## VARIÁVEIS DE AMBIENTE NECESSÁRIAS (VGM-009 / VGM-010)

```env
# Email
SENDGRID_API_KEY=
RESEND_API_KEY=
MAILGUN_API_KEY=
FROM_EMAIL=no-reply@wedotalent.com

# WhatsApp
WHATSAPP_PHONE_ID=
WHATSAPP_TOKEN=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=

# Celery/Redis
REDIS_URL=redis://localhost:6379
RABBITMQ_URL=amqp://localhost

# Feature flags
SCREENING_ENABLED=true
PLACEMENT_TRACKING_ENABLED=true
```

---

## ÉPICO VGM — Gestão de Vagas

---

### CARD VGM-001: Modal de Escolha — LIA vs Criação Manual
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Modal de Escolha: LIA vs Criação Manual"
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: Nenhuma

Descricao: |
  Ponto de entrada do fluxo de criação de vagas. O botão "+ Nova Vaga"
  na página de gestão de vagas abre um modal com duas opções visuais
  lado a lado. A escolha determina o fluxo subsequente: wizard
  conversacional da LIA ou formulário manual direto.

Historia de Usuario: |
  Como recrutador, quero escolher entre criar a vaga com a ajuda da LIA
  (Wizard conversacional) ou preenchendo manualmente um formulário
  direto, para ter flexibilidade no processo de abertura de vagas.

Regras de Negocio:
  1. O modal aparece ao clicar em qualquer botão "+ Nova Vaga" na página de vagas
  2. Opção "Criar com a LIA" → fecha o modal e abre o chat de criação de vaga (Wizard conversacional)
  3. Opção "Criar manualmente" → avança para o step manual-form dentro do mesmo modal (não abre nova janela)
  4. Fechar o modal (X ou click fora) descarta qualquer estado intermediário e não cria nenhum registro
  5. Multi-tenant: a opção LIA respeita os limites de plano (verificado no backend ao tentar criar)

Requisitos Tecnicos:
  Frontend:
    - Componente CreateJobModal.vue com v-model para isOpen
    - Estado interno step: 'choose' | 'manual-form'
    - Emit choose-wizard para ativar wizard LIA
    - Emit choose-manual para avançar para formulário
    - Composable useJobModal.ts com open/close
  Backend:
    - Nenhum endpoint novo — verificação de limites de plano ao criar vaga (VGM-002)
  Dados:
    - Nenhuma tabela nova neste card
  Validacoes:
    - Fechar modal não deve criar registro no banco

Design & Componentes:
  Componentes Existentes:
    - v-dialog (Vuetify) — container do modal
    - v-card — estrutura interna
    - v-row / v-col — layout dos cards de escolha
  Novos Componentes:
    - CreateJobModal.vue — modal principal com step machine
    - CreateJobForm.vue — formulário manual (step manual-form)
  Design Tokens:
    Modal max-width: 448px
    Border-radius: rounded-md (8px)
    Ícone LIA: color wedo-cyan (#60BED1)
    Ícone Manual: color text-gray-600
    Background hover card: translateY(-2px) com borda
  Layout:
    Modal centralizado, max-width 448px
    Cards de escolha em grid 2 colunas (50/50)
    Botão X no canto superior direito
  Estados:
    - step choose: exibe dois cards de escolha
    - step manual-form: exibe CreateJobForm com botão Voltar
  Acessibilidade:
    - aria-label no botão fechar
    - Role dialog no v-dialog
    - Tab order: LIA → Manual → Fechar

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "+ Nova Vaga"
    2. Modal abre no step choose
    3. Dois cards: "Criar com a LIA" e "Criar manualmente"
    4. Clicar "LIA" → emit choose-wizard, modal fecha, chat abre
    5. Clicar "Manual" → step muda para manual-form
    6. No manual-form: botão Voltar retorna para choose
  Estados de Botoes:
    Fechar (X):
      - Default: icon-only, text-gray-500
      - Hover: text-gray-900
  Validacoes Inline:
    Nenhuma neste step
  Mensagens de Feedback:
    Nenhuma — a escolha é silenciosa

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Clicar "Criar com a LIA" emite choose-wizard e fecha modal
  - [ ] Clicar "Criar manualmente" avança para step manual-form
  - [ ] Clicar fora do modal fecha sem criar vaga
  - [ ] Clicar X fecha sem criar vaga
  - [ ] Step manual-form tem botão Voltar que retorna para choose
  - [ ] Dark mode implementado
  - [ ] Responsivo mobile

Criterios de Aceitacao:
  - [ ] Modal abre ao clicar "+ Nova Vaga"
  - [ ] Dois cards de escolha visíveis side by side
  - [ ] Ícone LIA em cyan (#60BED1), ícone Manual em gray-600
  - [ ] Escolher LIA → fecha modal imediatamente
  - [ ] Escolher Manual → exibe formulário sem fechar modal
  - [ ] Fechar modal → nenhum registro criado no banco

Arquivos de Referencia (Prototipo):
  - create-job-modal.tsx: plataforma-lia/src/components/modals/create-job-modal.tsx (linhas 1-226)
  - jobs-page.tsx showCreateJobModal: plataforma-lia/src/components/pages/jobs-page.tsx (linha 142)
  - jobs-page.tsx botão gatilho: plataforma-lia/src/components/pages/jobs-page.tsx (linha 3530)
```

### Implementação Vue/Nuxt

#### Componente: `components/modals/CreateJobModal.vue`

**Props e Emits:**
```typescript
interface Props {
  modelValue: boolean // v-model para isOpen
}
interface Emits {
  (e: 'update:modelValue', val: boolean): void
  (e: 'choose-wizard'): void
  (e: 'choose-manual'): void
}
```

**Estado interno:**
```typescript
const step = ref<'choose' | 'manual-form'>('choose')
```

**Template (Vuetify):**
```vue
<v-dialog v-model="modelValue" max-width="448" persistent>
  <v-card rounded="lg">
    <v-card-title>Nova Vaga</v-card-title>
    <v-card-text>
      <v-row v-if="step === 'choose'">
        <v-col cols="6">
          <v-card variant="outlined" class="cursor-pointer" @click="emit('choose-wizard')">
            <!-- Brain icon cyan + texto "Criar com a LIA" -->
          </v-card>
        </v-col>
        <v-col cols="6">
          <v-card variant="outlined" class="cursor-pointer" @click="step = 'manual-form'">
            <!-- ClipboardList icon + texto "Criar manualmente" -->
          </v-card>
        </v-col>
      </v-row>
      <CreateJobForm v-else @back="step = 'choose'" @created="onJobCreated" />
    </v-card-text>
  </v-card>
</v-dialog>
```

**Composable:** `composables/useJobModal.ts`
```typescript
export function useJobModal() {
  const isOpen = ref(false)
  const open = () => { isOpen.value = true }
  const close = () => { isOpen.value = false }
  return { isOpen, open, close }
}
```

---

### CARD VGM-002: Formulário de Criação Manual de Vaga
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Formulário de Criação Manual de Vaga"
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-001

Descricao: |
  Step manual-form dentro do CreateJobModal. Coleta dados mínimos
  necessários para criação do registro no banco. Após envio, a vaga
  é criada com status "Rascunho" e o usuário é direcionado
  automaticamente para a tab de configurações (VGM-003).

Historia de Usuario: |
  Como recrutador, quero preencher um formulário enxuto com os dados
  essenciais da vaga para criá-la rapidamente como rascunho, sem
  precisar passar pelo wizard conversacional da LIA.

Regras de Negocio:
  1. Campos obrigatórios: title, manager, manager_email
  2. Campos opcionais não enviados se vazios (undefined no payload — sem string vazia)
  3. Ao submeter, o status inicial é sempre "Rascunho" — nunca "Ativa"
  4. work_model usa valores internos do backend: "remoto", "hibrido", "presencial" (sem acento em "híbrido")
  5. employment_type usa os valores: "CLT", "PJ", "Estágio", "Temporário", "Freelancer"
  6. Após criação bem-sucedida: modal fecha, toast de sucesso exibe, e o fluxo de navegação automática inicia (VGM-003)
  7. Em caso de erro da API: toast de erro com mensagem do backend, modal permanece aberto
  8. O botão "Criar e Configurar" fica desabilitado durante o loading (isSubmitting: true)
  9. Multi-tenant: company_id é injetado automaticamente no backend via get_user_company_id(current_user) — não enviado pelo frontend

Requisitos Tecnicos:
  Frontend:
    - Componente CreateJobForm.vue com validação reativa
    - Composable useJobCreate.ts encapsulando chamada de API
    - Validação client-side antes de enviar
    - Estado isSubmitting para desabilitar botão
    - Emit created(jobId, jobTitle) ao sucesso
  Backend:
    - POST /api/v1/job-vacancies (já implementado no protótipo)
    - Auth via get_current_user_or_demo
    - Plano check via check_active_jobs_limit_or_demo
    - company_id injetado via get_user_company_id
    - Status default "Rascunho"
  Dados:
    - Tabela job_vacancies (já existente)
    - Campos mínimos: title, department, work_model, employment_type, manager, manager_email, status, company_id
  Validacoes:
    - title: obrigatório, min 1 char, max 255
    - manager: obrigatório, min 1 char
    - manager_email: obrigatório, formato email válido
    - work_model: enum remoto|hibrido|presencial
    - employment_type: enum CLT|PJ|Estágio|Temporário|Freelancer

Design & Componentes:
  Componentes Existentes:
    - v-text-field (Vuetify) — título, gestor, email
    - v-select (Vuetify) — departamento, modelo trabalho, contratação
    - v-btn — Criar e Configurar, Voltar
    - v-form — container com validação
  Novos Componentes:
    - CreateJobForm.vue — formulário inline dentro do modal
  Design Tokens:
    Botão primário: bg-gray-900, text-white, rounded-md
    Erro de campo: borda vermelha + mensagem abaixo
    Asterisco obrigatório: text-red-500
  Layout:
    Stack vertical de campos, gap 16px
    Modelo de Trabalho + Forma de Contratação: grid 2 colunas (50/50)
    Ações: Voltar (text) à esquerda + Criar e Configurar (filled) à direita
  Estados:
    - Default, Loading (isSubmitting), Error por campo
  Acessibilidade:
    - Labels em todos os campos
    - error-messages associadas aos campos
    - Botão submit desabilitado com aria-disabled durante loading

Comportamento de UI:
  Fluxo Principal:
    1. Usuário está no step manual-form do modal
    2. Preenche Título da Vaga (obrigatório)
    3. Preenche opcionalmente Departamento, Modelo de Trabalho, Contratação
    4. Preenche Gestor Responsável e Email do Gestor (obrigatórios)
    5. Clica "Criar e Configurar"
    6. Validação client-side — se inválido, exibe erros inline
    7. POST para API com payload mapeado
    8. Sucesso: emit created(jobId), modal fecha, toast sucesso, navegação inicia
    9. Erro: toast de erro, modal permanece aberto com dados preservados
  Estados de Botoes:
    Criar e Configurar:
      - Default: bg-gray-900, text-white
      - Loading: spinner + "Criando..."
      - Disabled: durante isSubmitting
    Voltar:
      - Default: variant text, text-gray-600
  Validacoes Inline:
    Título:
      - Erro: "Título é obrigatório"
    Gestor:
      - Erro: "Nome do gestor é obrigatório"
    Email do Gestor:
      - Erro vazio: "Email é obrigatório"
      - Erro formato: "Email inválido"
  Mensagens de Feedback:
    - Sucesso: toast verde "Vaga criada com sucesso!"
    - Erro API: toast vermelho com mensagem do backend

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Submit sem título mostra erro de validação no campo
  - [ ] Submit sem gestor mostra erro de validação
  - [ ] Submit com email inválido mostra erro de validação
  - [ ] Submit válido faz POST para API, toast de sucesso, modal fecha
  - [ ] Erro da API mostra toast de erro, modal permanece aberto
  - [ ] Campos opcionais vazios não enviados no payload (undefined, não string vazia)
  - [ ] work_model "hibrido" sem acento no payload
  - [ ] Botão desabilitado durante isSubmitting
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] Campos obrigatórios com asterisco e validação
  - [ ] Payload POST contém apenas campos preenchidos
  - [ ] Status criado sempre "Rascunho"
  - [ ] company_id não enviado pelo frontend
  - [ ] Resposta 201 retorna id da vaga criada
  - [ ] Após sucesso: emit created(jobId, jobTitle)

Arquivos de Referencia (Prototipo):
  - create-job-modal.tsx ManualFormData: plataforma-lia/src/components/modals/create-job-modal.tsx (linha 16-23)
  - create-job-modal.tsx handleSubmit: plataforma-lia/src/components/modals/create-job-modal.tsx (linhas 118-149)
  - create-job-modal.tsx JSX form: plataforma-lia/src/components/modals/create-job-modal.tsx (linhas 228-375)
  - lia-api.ts createJobVacancy: plataforma-lia/src/services/lia-api.ts (linha 839)
  - job_vacancies.py POST endpoint: lia-agent-system/app/api/v1/job_vacancies.py (linha 2021)
  - job_vacancies.py JobVacancyCreate schema: lia-agent-system/app/api/v1/job_vacancies.py (linhas 99-138)
```

### Implementação Vue/Nuxt

#### Componente: `components/modals/CreateJobForm.vue`

**Emits:**
```typescript
interface Emits {
  (e: 'back'): void
  (e: 'created', jobId: string, jobTitle: string): void
}
```

**Estado reativo:**
```typescript
const form = reactive({
  title: '',
  department: '',
  workModel: '',
  employmentType: '',
  manager: '',
  managerEmail: ''
})
const errors = reactive<Record<string, string>>({})
const isSubmitting = ref(false)
```

**Composable:** `composables/useJobCreate.ts`
```typescript
export function useJobCreate() {
  const jobsApi = useJobsApi()
  async function createJob(data: JobCreatePayload): Promise<{ id: string }> {
    return jobsApi.post('/job-vacancies', data)
  }
  return { createJob }
}
```

**Validação:**
```typescript
function validate(): boolean {
  errors.title = !form.title.trim() ? 'Título é obrigatório' : ''
  errors.manager = !form.manager.trim() ? 'Nome do gestor é obrigatório' : ''
  errors.managerEmail = !form.managerEmail.trim()
    ? 'Email é obrigatório'
    : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.managerEmail)
    ? 'Email inválido'
    : ''
  return !Object.values(errors).some(Boolean)
}
```

**Template (Vuetify):**
```vue
<v-form @submit.prevent="handleSubmit">
  <v-text-field v-model="form.title" label="Título da Vaga *"
    :error-messages="errors.title" />

  <v-select v-model="form.department" label="Departamento"
    :items="DEPARTMENT_OPTIONS" />

  <v-row>
    <v-col cols="6">
      <v-select v-model="form.workModel" label="Modelo de Trabalho"
        :items="WORK_MODEL_OPTIONS" item-title="label" item-value="value" />
    </v-col>
    <v-col cols="6">
      <v-select v-model="form.employmentType" label="Forma de Contratação"
        :items="EMPLOYMENT_TYPE_OPTIONS" />
    </v-col>
  </v-row>

  <v-text-field v-model="form.manager" label="Gestor Responsável *"
    :error-messages="errors.manager" />

  <v-text-field v-model="form.managerEmail" label="Email do Gestor *"
    type="email" :error-messages="errors.managerEmail" />

  <v-card-actions>
    <v-btn variant="text" @click="emit('back')">Voltar</v-btn>
    <v-btn type="submit" color="surface-variant" variant="flat"
      :loading="isSubmitting" class="bg-gray-900 text-white">
      Criar e Configurar
    </v-btn>
  </v-card-actions>
</v-form>
```

### Payload da API (POST)

```json
POST /api/v1/job-vacancies

{
  "title": "Engenheiro de Software Sênior",
  "department": "Tecnologia",
  "work_model": "hibrido",
  "employment_type": "CLT",
  "manager": "João Silva",
  "manager_email": "joao@empresa.com",
  "status": "Rascunho"
}
```

**Resposta (201):**
```json
{
  "id": "uuid-da-vaga",
  "title": "Engenheiro de Software Sênior",
  "status": "Rascunho",
  "created_at": "2026-03-10T..."
}
```

### Banco de Dados

Tabela `job_vacancies` (já existente):
```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
company_id      UUID NOT NULL REFERENCES companies(id)
title           VARCHAR(255) NOT NULL
department      VARCHAR(100)
work_model      VARCHAR(50)       -- 'remoto' | 'hibrido' | 'presencial'
employment_type VARCHAR(50)       -- 'CLT' | 'PJ' | 'Estágio' | 'Temporário' | 'Freelancer'
manager         VARCHAR(255)
manager_email   VARCHAR(255)
status          VARCHAR(50) DEFAULT 'Rascunho'
created_at      TIMESTAMP DEFAULT now()
updated_at      TIMESTAMP DEFAULT now()
```

---

### CARD VGM-003: Navegação Automática pós-criação → Tab Configurações
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FRONTEND] Navegação Automática pós-criação para Tab Configurações"
Tipo: Feature
Area: Frontend
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-002

Descricao: |
  Após criação bem-sucedida via VGM-002, o sistema deve:
  (1) atualizar a lista de vagas incluindo a nova vaga,
  (2) navegar automaticamente para o kanban/view da vaga recém-criada,
  (3) abrir a tab "Configurações" em modo de edição.
  Tudo sem reload da página usando estado reativo e Pinia.

Historia de Usuario: |
  Como recrutador, após criar a vaga manualmente, quero ser redirecionado
  automaticamente para a view de configurações dessa vaga, sem precisar
  procurá-la na lista.

Regras de Negocio:
  1. A navegação ocorre sem window.location.reload() — usando estado reativo (Pinia + Vue Router)
  2. A lista de vagas é re-fetchada imediatamente após criação (refreshKey trigger)
  3. pendingNavigateJobId é setado com o UUID da vaga criada
  4. Um watcher monitora pendingNavigateJobId + jobs e, ao encontrar a vaga na lista, navega
  5. localStorage.setItem("jobCreationMode", jobId) sinaliza para o componente de kanban abrir a tab Configurações
  6. O item jobCreationMode é lido e removido do localStorage pelo componente de kanban no mount
  7. Se a vaga não aparecer na lista em até 10s (timeout), exibir toast de aviso e limpar pendingNavigateJobId
  8. Toast de loading opcional: "Abrindo configurações da vaga..." durante a navegação

Requisitos Tecnicos:
  Frontend:
    - Store Pinia useJobsStore com pendingNavigateJobId e refreshKey
    - Composable useJobNavigation.ts com watcher reativo
    - Vue Router push para /vagas/[id]?tab=configuracoes
    - localStorage flag jobCreationMode para sinalizar modo criação
    - Timeout de 10s com fallback toast
  Backend:
    - Nenhum endpoint novo
  Dados:
    - localStorage: chave jobCreationMode com valor = jobId
  Validacoes:
    - Navegação só ocorre quando a vaga existe na lista local (não navega com dados parciais)

Design & Componentes:
  Componentes Existentes:
    - Skeleton loader da tela de kanban (durante carregamento)
    - Toast de feedback
  Novos Componentes:
    - Nenhum componente visual novo
  Design Tokens:
    Loading skeleton: bg-gray-200 animado
  Layout:
    Sem nova tela — transição transparente para o usuário
  Estados:
    - Aguardando lista atualizar: skeleton ou spinner
    - Vaga encontrada: navegação imediata
    - Timeout 10s: toast amarelo de aviso
  Acessibilidade:
    - Toast de aviso com role="alert"

Comportamento de UI:
  Fluxo Principal:
    1. Modal cria vaga via API → response.id
    2. Callback onJobCreated(jobId) no pai
    3. Modal fecha, toast de sucesso exibe
    4. localStorage.setItem("jobCreationMode", jobId)
    5. store.pendingNavigateJobId = jobId
    6. store.triggerRefresh() — dispara re-fetch da lista
    7. Watcher detecta vaga na lista
    8. router.push('/vagas/[id]?tab=configuracoes')
    9. Componente kanban lê jobCreationMode, seta isCreationMode=true, activeTab='configuracoes'
    10. localStorage.removeItem("jobCreationMode")
  Estados de Botoes:
    Nenhum botão novo
  Validacoes Inline:
    Nenhuma
  Mensagens de Feedback:
    - Loading: "Abrindo configurações da vaga..."
    - Timeout: "A vaga foi criada. Clique aqui para acessá-la."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Criar vaga → lista re-fetcha e inclui nova vaga
  - [ ] Após criação → navegação para kanban da vaga acontece automaticamente
  - [ ] Tab Configurações abre em modo criação (isCreationMode: true)
  - [ ] localStorage.jobCreationMode é removido após leitura
  - [ ] Se API de lista demorar > 10s → toast de feedback ao usuário
  - [ ] Sem window.reload() em nenhum ponto do fluxo

Criterios de Aceitacao:
  - [ ] Após criação bem-sucedida, usuário chega na tab Configurações sem ação manual
  - [ ] isCreationMode=true ativo apenas na primeira abertura pós-criação
  - [ ] localStorage limpo após leitura
  - [ ] Pinia store atualizado com nova vaga

Arquivos de Referencia (Prototipo):
  - jobs-page.tsx onJobCreated callback: plataforma-lia/src/components/pages/jobs-page.tsx (linhas 7514-7519)
  - jobs-page.tsx pendingNavigateJobId: plataforma-lia/src/components/pages/jobs-page.tsx (linhas 143-144)
  - jobs-page.tsx watcher navegação: plataforma-lia/src/components/pages/jobs-page.tsx (linhas 448-457)
  - job-kanban-page.tsx jobCreationMode: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 434-440)
```

### Implementação Vue/Nuxt

#### Store (Pinia): `stores/jobsStore.ts`
```typescript
export const useJobsStore = defineStore('jobs', () => {
  const jobs = ref<Job[]>([])
  const pendingNavigateJobId = ref<string | null>(null)
  const refreshKey = ref(0)

  async function loadJobs() {
    const response = await jobsApi.list()
    jobs.value = response.items.map(mapJob)
  }

  function triggerRefresh() { refreshKey.value++ }

  return { jobs, pendingNavigateJobId, refreshKey, loadJobs, triggerRefresh }
})
```

#### Composable: `composables/useJobNavigation.ts`
```typescript
export function useJobNavigation() {
  const store = useJobsStore()
  const router = useRouter()

  function navigateToJobAfterCreate(jobId: string) {
    localStorage.setItem('jobCreationMode', jobId)
    store.pendingNavigateJobId = jobId
    store.triggerRefresh()
  }

  watch(
    [() => store.jobs, () => store.pendingNavigateJobId],
    ([jobs, pendingId]) => {
      if (!pendingId || !jobs.length) return
      const job = jobs.find(j => j.backendId === pendingId)
      if (!job) return
      store.pendingNavigateJobId = null
      router.push(`/vagas/${job.backendId}?tab=configuracoes`)
    }
  )

  return { navigateToJobAfterCreate }
}
```

#### Rota Vue/Nuxt: `pages/vagas/[id].vue`
```
pages/vagas/[id].vue
  → recebe query param ?tab=configuracoes
  → lê localStorage.getItem('jobCreationMode')
  → se match: activeTab = 'configuracoes', isCreationMode = true
  → localStorage.removeItem('jobCreationMode')
```

---

### CARD VGM-004: Tab Configurações da Vaga (Edição Completa)
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Tab Configurações da Vaga — Edição Completa por Seções"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 8
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-003

Descricao: |
  Tab "Configurações" dentro da view da vaga. Interface com navegação
  lateral por seções e formulário à direita. Em modo criação
  (isCreationMode: true), exibe banner de rascunho e botão "Publicar Vaga".
  Cada seção pode ser salva individualmente via PATCH na API.

Historia de Usuario: |
  Como recrutador, quero configurar todos os detalhes da vaga em uma
  interface organizada por seções, com salvamento individual por seção,
  para ter controle granular sobre o que foi preenchido.

Regras de Negocio:
  1. Cada seção tem botão "Salvar" individual — salva apenas os campos daquela seção via PUT /api/v1/job-vacancies/{id}
  2. Em modo criação (isCreationMode: true): banner âmbar "Vaga em rascunho" + botão "Publicar Vaga" fixo no topo
  3. Indicador visual de completude por seção (ícone check quando seção tem dados preenchidos)
  4. Mapeamento FE→BE obrigatório para todos os campos (camelCase → snake_case)
  5. interviewStages tem atualização especial: após salvar, recalcula o kanban dinâmico
  6. Campos de vaga afirmativa: isAffirmative toggle → exibe sub-campos condicionais
  7. Visibilidade is_confidential: true → exibe campo masked_company_name
  8. saving_section state: enquanto salva uma seção, botão mostra spinner "Salvando..."
  9. Após salvar com sucesso: toast "Seção salva com sucesso"

Requisitos Tecnicos:
  Frontend:
    - Componente JobConfigTab.vue com navegação lateral
    - Composable useJobConfig.ts com saveSection e buildPayload
    - Mapeamento completo camelCase→snake_case
    - salary_range e bonus_range construídos como objetos { min, max, currency }
    - isCreationMode prop controla visibilidade do banner e botão publicar
  Backend:
    - PUT /api/v1/job-vacancies/{vacancy_id} (já implementado)
    - Aceita qualquer subset dos campos JobVacancyCreate
    - Retorna JobVacancyResponse completo
  Dados:
    - Tabela job_vacancies com todos os campos das seções (ver schema abaixo)
  Validacoes:
    - Campos de data: formato ISO 8601
    - salary_range e bonus_range: min <= max
    - isAffirmative: true requer affirmativeCriteriaPrimary preenchido

Design & Componentes:
  Componentes Existentes:
    - v-navigation-drawer (Vuetify) — nav lateral
    - v-list / v-list-item — itens de seção
    - v-text-field, v-select, v-textarea, v-switch — campos
    - v-btn — salvar por seção
  Novos Componentes:
    - JobConfigTab.vue — componente principal da tab
    - SectionInfoGeral.vue — seção Informações Gerais
    - SectionPessoas.vue — seção Pessoas
    - SectionCompetencias.vue — seção Competências e Requisitos
    - SectionRemuneracao.vue — seção Remuneração
    - SectionPipeline.vue — seção Pipeline de Entrevistas
    - SectionTriagem.vue — seção Triagem WSI
    - SectionAvancadas.vue — seção Configurações Avançadas
  Design Tokens:
    Nav lateral: bg-white, border-r border-gray-200, width 220px
    Seção ativa: border border-gray-900 (borda preta)
    Check completude: mdi-check-circle, color success, size 14
    Banner criação: bg-amber-50, border-amber-200, ícone Info âmbar
    Botão Publicar: bg-gray-900, text-white, rounded-md
    Botão Salvar seção: bg-gray-900, text-white, rounded-md
  Layout:
    Duas colunas: nav lateral 220px fixo + área de conteúdo flex
    Nav lateral flat, sem sombra
    Conteúdo: padding 24px, max-width 720px
  Estados:
    - Default: formulário editável
    - saving_section: botão com spinner "Salvando..."
    - isCreationMode=true: banner âmbar visível, botão Publicar visível
    - isCreationMode=false: sem banner, sem botão Publicar
  Acessibilidade:
    - aria-current="true" no item de seção ativa
    - Labels descritivos em todos os campos
    - Mensagens de erro anunciadas para screen readers

Comportamento de UI:
  Fluxo Principal:
    1. Usuário chega na tab Configurações (via VGM-003 ou navegação manual)
    2. Nav lateral exibe 7 seções com ícone de check nas completas
    3. Seção ativa exibe formulário à direita
    4. Usuário preenche campos e clica "Salvar" da seção
    5. Spinner no botão durante requisição
    6. Toast de sucesso ou erro
    7. Se isCreationMode: botão "Publicar Vaga" no banner do topo
  Estados de Botoes:
    Salvar (por seção):
      - Default: bg-gray-900, text-white
      - Loading: spinner + "Salvando..."
      - Disabled: durante saving_section de qualquer seção
    Publicar Vaga (banner):
      - Default: bg-gray-900, text-white, ícone send
      - Loading: spinner + "Publicando..."
  Validacoes Inline:
    salary_range: min > max → "Salário mínimo deve ser menor que o máximo"
    email campos: formato email válido
    campos de data: formato válido
  Mensagens de Feedback:
    - Sucesso: "Seção salva com sucesso"
    - Erro: "Erro ao salvar. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Cada seção tem botão Salvar funcional
  - [ ] Mapeamento camelCase→snake_case correto em todos os campos
  - [ ] salary_range construído corretamente ao salvar Remuneração
  - [ ] isCreationMode: banner âmbar + botão Publicar visíveis
  - [ ] !isCreationMode: banner e botão ocultos
  - [ ] Salvar → toast de sucesso
  - [ ] Erro ao salvar → toast de erro, dados mantidos no form
  - [ ] Check de completude: aparece quando seção tem dados
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] 7 seções navegáveis na lateral
  - [ ] Seção ativa destacada com borda preta
  - [ ] Check verde em seções com dados preenchidos
  - [ ] PUT API chamado apenas com campos da seção em questão
  - [ ] Banner de criação visível apenas em modo criação
  - [ ] isAffirmative toggle exibe campos condicionais

Arquivos de Referencia (Prototipo):
  - JobEditTab.tsx SECTIONS: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 65-100)
  - JobEditTab.tsx isCreationMode banner: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 316-342)
  - job-kanban-page.tsx handleSaveJobSection: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 3102-3170)
  - job-kanban-page.tsx fieldMapping: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 3106-3130)
  - job-kanban-page.tsx init form: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 1676-1730)
  - job_vacancies.py PUT endpoint: lia-agent-system/app/api/v1/job_vacancies.py (~linha 2100)
```

### Implementação Vue/Nuxt

#### Composable principal: `composables/useJobConfig.ts`
```typescript
export function useJobConfig(jobId: string) {
  const form = reactive<JobEditForm>({})
  const savingSection = ref<string | null>(null)

  async function saveSection(sectionId: string, fields: string[]) {
    savingSection.value = sectionId
    try {
      const payload = buildPayload(fields, form)
      await jobsApi.update(jobId, payload)
    } finally {
      savingSection.value = null
    }
  }

  function buildPayload(fields: string[], form: JobEditForm) {
    const mapping: Record<string, string> = {
      workModel: 'work_model',
      type: 'employment_type',
      level: 'seniority_level',
      manager: 'hiring_manager',
      managerEmail: 'hiring_manager_email',
      urgencyLevel: 'urgency_level',
      recruiterEmail: 'recruiter_email',
    }
    const payload: Record<string, any> = {}
    fields.forEach(f => {
      if (f === 'salaryMin' || f === 'salaryMax') {
        payload['salary_range'] = { min: form.salaryMin, max: form.salaryMax, currency: 'BRL' }
        return
      }
      if (f === 'bonusMin' || f === 'bonusMax') {
        payload['bonus_range'] = { min: form.bonusMin, max: form.bonusMax, currency: 'BRL' }
        return
      }
      payload[mapping[f] || f] = (form as any)[f]
    })
    return payload
  }

  return { form, savingSection, saveSection }
}
```

#### Navegação lateral (Vuetify):
```vue
<v-navigation-drawer permanent width="220">
  <v-list nav>
    <v-list-item v-for="section in SECTIONS" :key="section.id"
      :value="section.id" @click="activeSection = section.id"
      :active="activeSection === section.id">
      <template #prepend>
        <v-icon :icon="section.icon" size="16" />
      </template>
      <v-list-item-title>{{ section.title }}</v-list-item-title>
      <template #append>
        <v-icon v-if="isSectionComplete(section)" icon="mdi-check-circle"
          color="success" size="14" />
      </template>
    </v-list-item>
  </v-list>
</v-navigation-drawer>
```

### Banco de Dados

Campos adicionais na tabela `job_vacancies`:
```sql
seniority_level               VARCHAR(50)
description                   TEXT
requirements                  JSONB DEFAULT '[]'
technical_requirements        JSONB DEFAULT '[]'
behavioral_competencies       JSONB DEFAULT '[]'
languages                     JSONB DEFAULT '[]'
salary_range                  JSONB            -- { min, max, currency }
bonus_range                   JSONB            -- { min, max, currency }
benefits                      JSONB DEFAULT '[]'
interview_stages              JSONB DEFAULT '[]'
screening_questions           JSONB DEFAULT '[]'
eligibility_questions         JSONB DEFAULT '[]'
visibility                    VARCHAR(30) DEFAULT 'public'
is_confidential               BOOLEAN DEFAULT false
masked_company_name           VARCHAR(255)
is_affirmative                BOOLEAN DEFAULT false
affirmative_criteria_primary  VARCHAR(100)
affirmative_criteria_secondary VARCHAR(100)
affirmative_description       TEXT
affirmative_document_required BOOLEAN DEFAULT false
affirmative_document_types    JSONB DEFAULT '[]'
urgency_level                 INTEGER DEFAULT 3
priority                      VARCHAR(20) DEFAULT 'média'
open_date                     DATE
deadline                      DATE
deadline_screening            DATE
deadline_shortlist            DATE
deadline_closing              DATE
published_linkedin            BOOLEAN DEFAULT false
published_website             BOOLEAN DEFAULT false
published_indeed              BOOLEAN DEFAULT false
target_audience               TEXT
target_sector                 VARCHAR(100)
target_segment                VARCHAR(100)
exclude_from_sync             BOOLEAN DEFAULT false
```

---

### CARD VGM-005: Publicação da Vaga — Auto-save + Link + Status Ativa
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Publicação da Vaga: Auto-save + Geração de Link + Status Ativa"
Tipo: Feature
Area: Full-Stack
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 5
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-004

Descricao: |
  Ação de publicação da vaga. Executa 3 operações sequenciais:
  (1) auto-save de todos os campos preenchidos no formulário,
  (2) geração do link público de candidatura,
  (3) atualização do status para "Ativa".
  Exibe modal de sucesso com o link copiável. Ao fechar o modal,
  permanece na view da vaga sem redirecionamento.

Historia de Usuario: |
  Como recrutador, quero publicar a vaga clicando em "Publicar Vaga",
  tendo certeza de que todos os dados do formulário serão salvos antes
  da publicação, e receber um link público de candidatura para compartilhar.

Regras de Negocio:
  1. Auto-save obrigatório antes de publicar — todos os campos preenchidos no jobEditForm são enviados antes da publicação
  2. O auto-save usa o mesmo mapeamento de campos de VGM-004 (camelCase→snake_case)
  3. Campos vazios ('', null, undefined) NÃO são incluídos no payload do auto-save
  4. salary_range e bonus_range construídos apenas se salaryMin ou salaryMax estão preenchidos
  5. Após auto-save → generatePublicLink(vacancyId) → retorna { public_url: string }
  6. Após gerar link → updateJobVacancy(vacancyId, { status: "Ativa" })
  7. Modal de sucesso exibe o link copiável, botão de copiar para clipboard
  8. Fechar modal de sucesso → apenas fecha o modal. NÃO redireciona. NÃO recarrega.
  9. Após publicação: banner de rascunho desaparece (isCreationMode: false)
  10. Status no header atualiza para "Ativa" imediatamente (estado local, sem re-fetch)
  11. Botão "Publicar Vaga" fica desabilitado durante loading com spinner "Publicando..."
  12. Em caso de erro em qualquer etapa → toast de erro, vaga permanece em rascunho

Requisitos Tecnicos:
  Frontend:
    - Composable useJobPublish.ts com função publish() sequencial
    - buildAutoSavePayload() filtra campos vazios e mapeia nomes
    - Dialog de sucesso com link copiável (clipboard API)
    - Estado isPublishing para desabilitar botão
    - Emit success para atualizar isCreationMode e status local
  Backend:
    - PUT /api/v1/job-vacancies/{id} (já implementado)
    - POST /api/v1/job-vacancies/{id}/generate-public-link
    - Retorna { public_url: "https://..." }
  Dados:
    - Colunas public_url, slug, published_at na tabela job_vacancies
  Validacoes:
    - Título obrigatório para publicar (validação no backend)
    - Status só muda para "Ativa" após geração bem-sucedida do link

Design & Componentes:
  Componentes Existentes:
    - v-dialog — dialog de sucesso
    - v-text-field readonly — exibe link
    - v-btn — copiar, fechar
  Novos Componentes:
    - PublishSuccessDialog.vue — dialog com link copiável
  Design Tokens:
    Botão Publicar: bg-gray-900, text-white, rounded-md, ícone mdi-send
    Loading: spinner mdi-loading + "Publicando..."
    Dialog: max-width 400px
    Link field: readonly, append-inner-icon mdi-content-copy
  Layout:
    Dialog centralizado, max-width 400px
    Input do link: largura total, readonly
    Ações: botão Fechar à direita
  Estados:
    - Default: botão Publicar ativo
    - isPublishing: spinner + "Publicando...", botão disabled
    - Sucesso: dialog abre com link
    - Erro: toast vermelho, dialog não abre
  Acessibilidade:
    - aria-label no botão copiar link
    - Dialog com foco gerenciado

Comportamento de UI:
  Fluxo Principal:
    1. Usuário clica "Publicar Vaga" no banner de rascunho
    2. Botão muda para "Publicando..." + spinner
    3. Auto-save de todos os campos preenchidos
    4. POST para gerar link público
    5. PUT para mudar status para "Ativa"
    6. Dialog de sucesso abre com link copiável
    7. Usuário copia link e fecha dialog
    8. Banner de rascunho desaparece
    9. Badge de status muda para "Ativa" (verde)
  Estados de Botoes:
    Publicar Vaga:
      - Default: bg-gray-900, text-white, ícone mdi-send
      - Loading: spinner mdi-loading + "Publicando..."
      - Disabled: durante isPublishing
    Copiar link:
      - Default: ícone mdi-content-copy
      - Sucesso: ícone mdi-check por 2s
  Validacoes Inline:
    Nenhuma — validação ocorre no backend
  Mensagens de Feedback:
    - Copiar link: toast "Link copiado!"
    - Erro de publicação: toast "Erro ao publicar a vaga. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Clicar "Publicar" → auto-save roda antes de gerar link
  - [ ] Auto-save não inclui campos vazios no payload
  - [ ] salary_range construído corretamente se salaryMin/Max preenchidos
  - [ ] Link gerado aparece no dialog copiável
  - [ ] Botão copiar → clipboard.writeText + toast "Link copiado!"
  - [ ] Fechar dialog → permanece na view da vaga
  - [ ] isCreationMode → false após publicação
  - [ ] Status do header → "Ativa"
  - [ ] Falha na API → toast de erro, vaga não muda de status

Criterios de Aceitacao:
  - [ ] 3 chamadas API na ordem correta: PUT save → POST link → PUT status
  - [ ] Campos vazios excluídos do payload de auto-save
  - [ ] public_url retornado e exibido no dialog
  - [ ] Clipboard API chamada ao clicar copiar
  - [ ] Banner âmbar desaparece após publicação bem-sucedida

Arquivos de Referencia (Prototipo):
  - job-kanban-page.tsx handlePublishJob: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 442-514)
  - JobEditTab.tsx botão publicar: plataforma-lia/src/components/jobs/JobEditTab.tsx (linhas 324-341)
  - job-kanban-page.tsx dialog sucesso: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 9972-10010)
  - lia-api.ts generatePublicLink: plataforma-lia/src/services/lia-api.ts (linha 974)
```

### Implementação Vue/Nuxt

#### Composable: `composables/useJobPublish.ts`
```typescript
export function useJobPublish(jobId: string, form: JobEditForm) {
  const isPublishing = ref(false)
  const publicLink = ref<string | null>(null)
  const showSuccessDialog = ref(false)

  async function publish() {
    isPublishing.value = true
    try {
      const payload = buildAutoSavePayload(form)
      if (Object.keys(payload).length > 0) {
        await jobsApi.update(jobId, payload)
      }
      const { public_url } = await jobsApi.generatePublicLink(jobId)
      await jobsApi.update(jobId, { status: 'Ativa' })
      publicLink.value = public_url
      showSuccessDialog.value = true
    } catch (e) {
      useToast().error('Erro ao publicar a vaga')
    } finally {
      isPublishing.value = false
    }
  }

  return { publish, isPublishing, publicLink, showSuccessDialog }
}
```

#### Payload de Auto-save (campos mapeados):
```typescript
const fieldMapping = {
  title: 'title', department: 'department', location: 'location',
  workModel: 'work_model', type: 'employment_type', level: 'seniority_level',
  urgencyLevel: 'urgency_level', priority: 'priority',
  recruiter: 'recruiter', recruiterEmail: 'recruiter_email',
  manager: 'hiring_manager', managerEmail: 'hiring_manager_email',
  openDate: 'open_date', deadline: 'deadline',
  deadlineScreening: 'deadline_screening',
  deadlineShortlist: 'deadline_shortlist',
  deadlineClosing: 'deadline_closing',
  benefits: 'benefits', description: 'description',
  targetAudience: 'target_audience', targetSector: 'target_sector',
  visibility: 'visibility', isConfidential: 'is_confidential',
  isAffirmative: 'is_affirmative', languages: 'languages',
}
// salary_range: { min, max, currency: 'BRL' } se salaryMin ou salaryMax preenchidos
// bonus_range: { min, max, currency: 'BRL' } se bonusMin ou bonusMax preenchidos
```

#### Dialog de sucesso (Vuetify):
```vue
<v-dialog v-model="showSuccessDialog" max-width="400" persistent>
  <v-card rounded="lg">
    <v-card-title>Vaga Publicada!</v-card-title>
    <v-card-text>
      <p>A vaga está ativa. Compartilhe o link:</p>
      <v-text-field :model-value="publicLink" readonly
        append-inner-icon="mdi-content-copy"
        @click:append-inner="copyLink" />
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn color="surface-variant" variant="flat"
        @click="showSuccessDialog = false">Fechar</v-btn>
    </v-card-actions>
  </v-card>
</v-dialog>
```

---

### CARD VGM-006: Header da Vaga — Badge Status + Popover de Ações
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FRONTEND] Header da Vaga: Badge de Status Clicável + Popover de Ações"
Tipo: Feature
Area: Frontend
Sprint: 1
Início: 10/Mar
Término: 20/Mar
Data Inicio Jira: 2026-03-10
Data Termino Jira: 2026-03-20
Pontos: 3
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-005

Descricao: |
  Header fixo da view de vaga exibe título, ID interno (WDT-XXXXXXXX),
  badge de status clicável com popover de ações contextuais. As ações
  disponíveis variam conforme o status atual da vaga.

Historia de Usuario: |
  Como recrutador, quero ver o status atual da vaga no cabeçalho e ter
  acesso rápido às ações de mudança de status (pausar, reativar, fechar),
  para gerenciar o ciclo de vida da vaga sem navegar por menus.

Regras de Negocio:
  1. Badge de status é um <button> que abre Popover ao clicar
  2. Status "Ativa" ou "active": mostra Pausar + Fechar
  3. Status "Pausada", "Paused": mostra Reativar + Fechar
  4. Status "Encerrada": badge NÃO abre popover
  5. "Pausar vaga" → abre JobStatusModal com mode 'pause' (VGM-008)
  6. "Reativar vaga" → abre JobStatusModal com mode 'activate' (VGM-008)
  7. "Fechar vaga" → abre CloseVacancyModal (VGM-009)
  8. O badge exibe o valor de jobEditForm.status || currentJob.status (estado local tem prioridade)
  9. Badge ID: WDT-{primeiros 8 chars do UUID em maiúsculas} — ex: WDT-A1B2C3D4

Requisitos Tecnicos:
  Frontend:
    - Componente JobHeader.vue com props job, currentStatus, screeningStatus
    - Emits: pause, reactivate, close-vacancy, screening-action
    - Computed isActive e canChangeStatus
    - v-menu do Vuetify para o popover
    - ID interno formatado: WDT-{uuid.slice(0,8).toUpperCase()}
  Backend:
    - Nenhum endpoint novo neste card
  Dados:
    - Nenhuma tabela nova
  Validacoes:
    - Status "Encerrada" → sem ação de popover

Design & Componentes:
  Componentes Existentes:
    - v-menu (Vuetify) — popover de ações
    - v-chip — badge de status
    - v-list / v-list-item — itens do popover
  Novos Componentes:
    - JobHeader.vue — header completo da view de vaga
  Design Tokens:
    Header: height 56px, border-bottom 1px solid, bg-white
    Badge status: bg-[#DCE4DB], text-gray-800, border-gray-200, text-xs
    Hover badge: bg-[#c9d6c8], cursor-pointer
    Popover: min-width 176px, border-radius 8px, sem sombra (borda)
    Item Fechar: color red-600, ícone mdi-archive
    Item Pausar: ícone mdi-pause-circle, color warning (âmbar)
    Item Reativar: ícone mdi-play-circle, color success (verde)
  Layout:
    Header horizontal: título + código + badge status + badge triagem
    Altura fixa 56px
    Sticky top-0
  Estados:
    - Status Ativa: badge verde-acinzentado, popover com Pausar + Fechar
    - Status Pausada: badge âmbar, popover com Reativar + Fechar
    - Status Encerrada: badge cinza, sem popover
    - Status Rascunho: badge cinza, sem popover de ações
  Acessibilidade:
    - aria-haspopup="true" no badge clicável
    - aria-expanded no estado de menu aberto
    - Role menuitem nos itens do popover

Comportamento de UI:
  Fluxo Principal:
    1. Header exibe título da vaga + ID interno (WDT-XXXXXXXX)
    2. Badge de status à direita do ID
    3. Clicar no badge (se permitido) abre popover
    4. Ações contextuais baseadas no status atual
    5. Clicar em ação → emite evento correto para o pai
    6. Pai abre modal correspondente (VGM-008 ou VGM-009)
  Estados de Botoes:
    Badge status:
      - Clicável: cursor-pointer, hover escurece
      - Não clicável (Encerrada): cursor-default, sem hover
  Validacoes Inline:
    Nenhuma
  Mensagens de Feedback:
    Nenhuma diretamente no header

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Status "Ativa" → popover mostra Pausar + Fechar
  - [ ] Status "Pausada" → popover mostra Reativar + Fechar
  - [ ] Status "Encerrada" → badge sem popover
  - [ ] Clicar "Pausar" → emite evento pause
  - [ ] Clicar "Reativar" → emite evento reactivate
  - [ ] Clicar "Fechar vaga" → emite evento close-vacancy
  - [ ] ID interno renderizado no formato WDT-XXXXXXXX
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] Badge reflete status local (sem re-fetch para mudanças otimistas)
  - [ ] Popover fecha ao clicar em ação
  - [ ] ID formatado como WDT- + 8 chars UUID maiúsculos
  - [ ] Eventos emitidos corretamente para os modais

Arquivos de Referencia (Prototipo):
  - job-kanban-page.tsx header completo: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 4940-5090)
  - job-kanban-page.tsx badge status: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 4951-4993)
  - job-kanban-page.tsx estados modal: plataforma-lia/src/components/pages/job-kanban-page.tsx (showJobStatusModal, jobStatusModalMode, showCloseVacancyModal)
```

### Implementação Vue/Nuxt

#### Componente: `components/jobs/JobHeader.vue`

**Props e Emits:**
```typescript
interface Props {
  job: Job
  currentStatus: string
  screeningStatus: string
}
interface Emits {
  (e: 'pause'): void
  (e: 'reactivate'): void
  (e: 'close-vacancy'): void
  (e: 'screening-action', action: string): void
}
```

**Computeds:**
```typescript
const isActive = computed(() =>
  ['Ativa', 'active'].includes(props.currentStatus)
)
const canChangeStatus = computed(() =>
  !['Encerrada', 'closed'].includes(props.currentStatus)
)
const jobInternalId = computed(() =>
  `WDT-${props.job.id.slice(0, 8).toUpperCase()}`
)
```

---

### CARD VGM-007: Badge de Triagem no Header + Controle de Status
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Badge de Triagem WSI no Header + Controle de Status"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 3
Prioridade: Média
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-006

Descricao: |
  Badge de triagem ao lado do badge de status da vaga no header.
  Indica o estado atual do processo de triagem WSI/LIA. Clicável com
  popover de ações contextuais para iniciar, pausar ou retomar triagem.

Historia de Usuario: |
  Como recrutador, quero ver o status da triagem WSI no cabeçalho da
  vaga e poder iniciar, pausar ou retomar a triagem rapidamente sem
  sair da view.

Regras de Negocio:
  1. Status completed → badge fixo sem ação (Popover não abre)
  2. Ação "Configurar Triagem" → navega para a sub-seção de triagem na tab Configurações
  3. Ações de status → chamam PUT /api/v1/job-vacancies/{id} com { screening_status: newStatus }
  4. Update otimista: estado local atualiza imediatamente, reverter em caso de erro
  5. Toast de confirmação após mudança de status
  6. A triagem só pode ser iniciada se a vaga estiver com status "Ativa" (validação FE + BE)
  7. O campo screening_status é separado do status da vaga

Requisitos Tecnicos:
  Frontend:
    - Componente ScreeningBadge.vue com prop status e vacancyStatus
    - Emits configure e change-status
    - Update otimista com rollback em caso de erro
    - v-menu para popover de ações
  Backend:
    - PATCH /api/v1/job-vacancies/{id} com { screening_status: newStatus }
    - Validação: triagem só pode iniciar se vaga Ativa
  Dados:
    - Coluna screening_status VARCHAR(20) na tabela job_vacancies
  Validacoes:
    - Iniciar triagem requer status da vaga = "Ativa"
    - screening_status enum: not_configured | not_started | active | paused | completed

Design & Componentes:
  Componentes Existentes:
    - v-chip — badge visual
    - v-menu / v-list — popover de ações
  Novos Componentes:
    - ScreeningBadge.vue — badge de triagem com popover
  Design Tokens:
    not_configured: bg-gray-100, text-gray-700, border-gray-300
    not_started: bg-amber-50, text-amber-800, border-amber-300
    active: bg-emerald-50, text-emerald-800, border-emerald-300
    paused: bg-orange-50, text-orange-800, border-orange-300
    completed: bg-sky-50, text-sky-800, border-sky-300
  Layout:
    Posicionado à direita do badge de status no header
    Mesmo tamanho e estilo geral dos badges
  Estados:
    - not_configured: popover com ação "Configurar"
    - not_started: popover com "Iniciar Triagem" e "Configurar"
    - active: popover com "Pausar Triagem"
    - paused: popover com "Retomar" e "Configurar"
    - completed: badge sem popover
  Acessibilidade:
    - aria-label descritivo no badge
    - Itens do popover com role menuitem

Comportamento de UI:
  Fluxo Principal:
    1. Badge exibe status da triagem com cor contextual
    2. Clicar no badge (se não completed) abre popover
    3. Ações contextuais conforme status atual
    4. Clicar em ação → update otimista + chamada API
    5. Sucesso: toast de confirmação
    6. Erro: rollback do estado otimista + toast de erro
  Estados de Botoes:
    Badge triagem:
      - Clicável (non-completed): cursor-pointer
      - Completed: cursor-default
  Validacoes Inline:
    Tentativa de iniciar triagem com vaga pausada → toast de aviso
  Mensagens de Feedback:
    - Sucesso: "Status da triagem atualizado"
    - Erro: "Erro ao atualizar triagem. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Status completed → badge sem popover
  - [ ] Status not_configured → ação "Configurar" disponível
  - [ ] Status active → ação "Pausar" disponível
  - [ ] Status paused → ações "Retomar" e "Configurar" disponíveis
  - [ ] Mudança de status → PATCH API + toast de confirmação
  - [ ] Erro → rollback do estado otimista + toast de erro
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] 5 estados visuais distintos com cores corretas
  - [ ] Update otimista: badge muda antes da resposta da API
  - [ ] Rollback: badge retorna ao estado anterior em caso de erro
  - [ ] Triagem não pode iniciar com vaga pausada ou encerrada

Arquivos de Referencia (Prototipo):
  - job-kanban-page.tsx badge triagem: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 4995-5088)
  - job-kanban-page.tsx handleScreeningStatusChange: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 5011-5019)
```

---

### CARD VGM-008: Modal Pausar / Reativar Vaga
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Modal Pausar / Reativar Vaga com Notificação de Candidatos"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 5
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-006

Descricao: |
  Modal multi-step acionado pelo popover de status (VGM-006). Suporta
  dois modos: pause (pausar) e activate (reativar). No modo pause permite
  informar motivo, notificar candidatos ativos via email/WhatsApp e
  cancelar entrevistas agendadas.

Historia de Usuario: |
  Como recrutador, quero pausar uma vaga ativa informando o motivo e
  opcionalmente notificando candidatos em processo, ou reativar uma
  vaga pausada, para gerenciar o fluxo sem perder histórico.

Regras de Negocio:
  1. Motivo da pausa: texto livre opcional
  2. Toggle "Notificar candidatos em processo" (default: false)
  3. Se notificar: selecionar canal (email / WhatsApp / ambos), selecionar template, selecionar candidatos
  4. Entrevistas agendadas: opção "Cancelar entrevistas agendadas" (toggle)
  5. Ao confirmar pausar: PUT /api/v1/job-vacancies/{id} com { status: "Pausada", pause_reason: "..." }
  6. Se notificar candidatos: disparar notificações separadamente (VGM-010)
  7. Status local atualiza imediatamente para "Pausada"
  8. Ao reativar: PUT /api/v1/job-vacancies/{id} com { status: "Ativa" }
  9. Opcional no reativar: notificar candidatos que vaga voltou
  10. Status local atualiza para "Ativa"

Requisitos Tecnicos:
  Frontend:
    - Componente JobStatusModal.vue com prop mode: 'pause' | 'activate'
    - Composable useJobStatus.ts com pause() e reactivate()
    - Lista de candidatos ativos passada como prop
    - Template selector com preview da mensagem
  Backend:
    - PUT /api/v1/job-vacancies/{id} (já implementado)
    - POST /api/v1/job-vacancies/{id}/notify-candidates (novo)
  Dados:
    - Colunas pause_reason TEXT, paused_at TIMESTAMP, reactivated_at TIMESTAMP na tabela job_vacancies
  Validacoes:
    - Canal de notificação obrigatório se toggle notificar ativo
    - Pelo menos 1 candidato selecionado se toggle notificar ativo

Design & Componentes:
  Componentes Existentes:
    - v-dialog — container do modal
    - v-switch — toggles
    - v-select — canal de notificação, template
    - v-checkbox — seleção de candidatos
    - v-textarea — motivo da pausa
  Novos Componentes:
    - JobStatusModal.vue — modal de pausa/reativação
  Design Tokens:
    Modal: max-width 560px
    Seção notificação: bg-gray-50 border border-gray-200 rounded-md, padding 16px
    Candidato item: flex row com checkbox, avatar inicial, nome, stage
    Botão confirmar Pausar: bg-amber-600, text-white
    Botão confirmar Reativar: bg-green-700, text-white
  Layout:
    Formulário vertical no modo pause
    Seção de notificação aparece condicionalmente quando toggle ativo
    Lista de candidatos scrollável (max-height 200px)
  Estados:
    - mode=pause: formulário com motivo + toggle notificar + toggle cancelar entrevistas
    - mode=activate: confirmação simples + toggle notificar opcionalmente
    - notifyApplicants=true: campos adicionais visíveis
  Acessibilidade:
    - aria-expanded no toggle de notificação
    - Lista de candidatos com role listbox

Comportamento de UI:
  Fluxo Principal (pause):
    1. Modal abre no modo pause
    2. Campo de motivo (opcional)
    3. Toggle "Notificar candidatos"
    4. Se ON: canal + template + lista de candidatos com checkboxes
    5. Toggle "Cancelar entrevistas agendadas" (opcional)
    6. Confirmar → PUT API + notificações + status local
  Fluxo Principal (activate):
    1. Modal abre no modo activate
    2. Confirmação simples da reativação
    3. Toggle opcional para notificar candidatos
    4. Confirmar → PUT API + status local
  Estados de Botoes:
    Confirmar Pausar:
      - bg-amber-600, text-white
      - Loading: "Pausando..."
    Confirmar Reativar:
      - bg-green-700, text-white
      - Loading: "Reativando..."
    Cancelar:
      - variant text
  Validacoes Inline:
    Toggle notificar ON sem candidatos selecionados → aviso
  Mensagens de Feedback:
    - Pausar: toast "Vaga pausada com sucesso"
    - Reativar: toast "Vaga reativada com sucesso"
    - Erro: toast de erro com mensagem

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Modo pause: form com motivo + opção notificação + opção cancelar entrevistas
  - [ ] Toggle notificar OFF: sem campos de notificação
  - [ ] Toggle notificar ON: campos de canal + template + candidatos visíveis
  - [ ] Confirmar pause → PUT API + status local = "Pausada"
  - [ ] Modo activate → PUT API + status local = "Ativa"
  - [ ] Fechar modal sem confirmar → nenhuma mudança
  - [ ] Dark mode implementado

Criterios de Aceitacao:
  - [ ] Status da vaga atualizado localmente sem re-fetch
  - [ ] pause_reason salvo no banco quando informado
  - [ ] Candidatos notificados apenas quando toggle ativo e candidatos selecionados
  - [ ] Entrevistas canceladas quando toggle ativo (integração futura)

Arquivos de Referencia (Prototipo):
  - job-status-modal.tsx: plataforma-lia/src/components/modals/job-status-modal.tsx (arquivo completo)
  - job-status-modal.tsx PauseData interface: plataforma-lia/src/components/modals/job-status-modal.tsx (linhas 52-65)
  - job-kanban-page.tsx uso modal: plataforma-lia/src/components/pages/job-kanban-page.tsx (showJobStatusModal, jobStatusModalMode)
```

### Implementação Vue/Nuxt

#### Composable: `composables/useJobStatus.ts`
```typescript
export function useJobStatus(jobId: string) {
  async function pause(data: PauseData) {
    await jobsApi.update(jobId, { status: 'Pausada', pause_reason: data.reason })
    if (data.notifyApplicants && data.candidateIds?.length) {
      await jobsApi.notifyCandidates(jobId, data)
    }
  }
  async function reactivate() {
    await jobsApi.update(jobId, { status: 'Ativa' })
  }
  return { pause, reactivate }
}
```

### Payload API

```json
PUT /api/v1/job-vacancies/{id}
{
  "status": "Pausada",
  "pause_reason": "Aguardando aprovação de headcount"
}

POST /api/v1/job-vacancies/{id}/notify-candidates
{
  "candidate_ids": ["uuid1", "uuid2"],
  "channel": "email",
  "template_id": "vaga_pausada",
  "message": "..."
}
```

### Banco de Dados

```sql
-- Adicionar à tabela job_vacancies:
pause_reason    TEXT
paused_at       TIMESTAMP
reactivated_at  TIMESTAMP
```

---

### CARD VGM-009: Modal Fechar Vaga com Placement de Candidato
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[FULLSTACK] Modal Fechar Vaga com Registro de Placement"
Tipo: Feature
Area: Full-Stack
Sprint: 2
Início: 21/Mar
Término: 31/Mar
Data Inicio Jira: 2026-03-21
Data Termino Jira: 2026-03-31
Pontos: 8
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-006

Descricao: |
  Modal multi-step para encerramento definitivo da vaga. Inclui:
  seleção do candidato contratado (placement), configuração da
  notificação para o contratado, e configuração de notificação em
  massa para os demais candidatos.
  ⚠️ GAP ATUAL: o protótipo implementa apenas a UI — o envio real
  das notificações e as chamadas à API precisam ser implementados
  (cobertos por VGM-010).

Historia de Usuario: |
  Como recrutador, quero fechar a vaga registrando o candidato
  contratado (placement), enviar mensagem de parabéns a ele e
  notificar os demais candidatos que a vaga foi encerrada, para
  finalizar o ciclo de forma completa e comunicada.

Regras de Negocio:
  1. O candidato da coluna "hired/Contratado" é pré-selecionado automaticamente no Step 1
  2. O placement é obrigatório para registrar fechamento completo. Se não há contratado, o recrutador pode pular (fechar sem placement)
  3. Ao confirmar: atualiza status da vaga para "Encerrada" + registra hired_candidate_id + closed_at
  4. Notificação do contratado: disparada imediatamente
  5. Notificação dos demais: disparada para os selecionados
  6. O campo hired_candidate_id na vaga registra o placement para relatórios
  7. Após confirmar: status local da vaga = "Encerrada", badge do header atualiza
  8. Badge de status "Encerrada" não abre popover de ações
  9. "⚠️ GAP ATUAL (PROTÓTIPO): o onConfirm no protótipo só atualiza estado local, não chama a API real e não envia notificações. Isso precisa ser implementado no produto."

Requisitos Tecnicos:
  Frontend:
    - Componente CloseVacancyModal.vue com 3 steps
    - Composable useVacancyClosure.ts com closeVacancy()
    - Step indicator com progresso 1-2-3
    - Lista scrollável de candidatos com checkboxes
    - Toggle "Selecionar todos"
    - Preview de mensagem com merge fields
  Backend:
    - PUT /api/v1/job-vacancies/{id} com status Encerrada + hired_candidate_id
    - POST /api/v1/placements — cria registro de placement
    - POST /api/v1/communications/send — notificação contratado
    - POST /api/v1/communications/batch-send — notificações em massa
  Dados:
    - Colunas hired_candidate_id, closed_at, closure_reason, closed_by na tabela job_vacancies
    - Nova tabela placements (ver schema abaixo)
  Validacoes:
    - Canal de notificação obrigatório se notificação ativa
    - Pelo menos 1 candidato selecionado para notificação em massa

Design & Componentes:
  Componentes Existentes:
    - v-dialog — container do modal
    - v-stepper (Vuetify) — step indicator
    - v-list com v-checkbox — lista de candidatos
    - v-select — canal, template
    - v-textarea — preview de mensagem
  Novos Componentes:
    - CloseVacancyModal.vue — modal multi-step de fechamento
  Design Tokens:
    Modal: max-width 640px
    Step indicator: pills numeradas 1-2-3
    Card candidato contratado: avatar inicial, nome, email
    Lista candidatos: scrollável, max-height 240px
    Botão confirmar: bg-gray-900, text-white, ícone mdi-archive
  Layout:
    Modal 640px com step indicator no topo
    Step 1: card do contratado + canal + template
    Step 2: lista com "Selecionar todos" + candidatos + preview
    Step 3: resumo + botão confirmar
  Estados:
    - Step 1: candidato pré-selecionado ou campo de seleção manual
    - Step 2: todos os candidatos ativos (exceto hired/rejected)
    - Step 3: resumo das ações a executar
  Acessibilidade:
    - Step indicator com aria-current
    - Checkbox lista com role listbox
    - Preview de mensagem em aria-live

Comportamento de UI:
  Fluxo Principal:
    1. Modal abre com candidato contratado pré-selecionado (se existir)
    2. Step 1: confirmar contratado + canal de notificação
    3. "Próximo" → Step 2: candidatos para notificar
    4. Selecionar candidatos + template
    5. "Próximo" → Step 3: resumo
    6. "Confirmar Encerramento" → 4 chamadas API em sequência
    7. Modal fecha, status local = "Encerrada"
  Estados de Botoes:
    Próximo:
      - bg-gray-900, text-white
    Confirmar Encerramento:
      - bg-gray-900, text-white, ícone mdi-archive
      - Loading: spinner + "Encerrando..."
    Voltar:
      - variant text
  Validacoes Inline:
    Step 3: sem candidato identificado → aviso, mas permite pular
  Mensagens de Feedback:
    - Sucesso: "Vaga encerrada com sucesso"
    - Erro: "Erro ao encerrar vaga. Tente novamente."

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Candidato na coluna "hired" pré-selecionado no Step 1
  - [ ] Sem candidato contratado → campo de seleção manual disponível
  - [ ] Step 2: todos os candidatos ativos listados (exceto hired/rejected)
  - [ ] "Selecionar todos" → marca/desmarca todos
  - [ ] Confirmar → PUT API status "Encerrada" + hired_candidate_id
  - [ ] Confirmar → POST placement criado
  - [ ] Confirmar → notificações disparadas (email/WhatsApp)
  - [ ] Fechar sem confirmar → nenhuma mudança
  - [ ] Badge de status → "Encerrada" após confirmação
  - [ ] Badge "Encerrada" → sem popover de ações

Criterios de Aceitacao:
  - [ ] 3 steps com indicador de progresso
  - [ ] PUT API com status=Encerrada + hired_candidate_id + closed_at
  - [ ] Placement registrado na tabela placements
  - [ ] Notificações disparadas (VGM-010) após confirmação
  - [ ] Status local atualizado sem re-fetch

Arquivos de Referencia (Prototipo):
  - close-vacancy-modal.tsx: plataforma-lia/src/components/modals/close-vacancy-modal.tsx (arquivo completo)
  - close-vacancy-modal.tsx CloseVacancyPayload: plataforma-lia/src/components/modals/close-vacancy-modal.tsx (linhas 44-61)
  - job-kanban-page.tsx uso modal: plataforma-lia/src/components/pages/job-kanban-page.tsx (linhas 9935-9970)
  - job-kanban-page.tsx GAP onConfirm: plataforma-lia/src/components/pages/job-kanban-page.tsx (linha 9963)
```

### Implementação Vue/Nuxt

#### Composable: `composables/useVacancyClosure.ts`
```typescript
export function useVacancyClosure(vacancyId: string) {
  async function closeVacancy(payload: ClosurePayload) {
    await jobsApi.update(vacancyId, {
      status: 'Encerrada',
      hired_candidate_id: payload.hiredCandidateId,
      closed_at: new Date().toISOString(),
      closure_reason: 'filled'
    })
    if (payload.hiredCandidateId) {
      await placementsApi.create({
        job_vacancy_id: vacancyId,
        candidate_id: payload.hiredCandidateId
      })
    }
    if (payload.hiredNotification?.channel) {
      await communicationsApi.send({
        recipient_id: payload.hiredCandidateId,
        ...payload.hiredNotification
      })
    }
    if (payload.otherNotifications?.candidateIds?.length) {
      await communicationsApi.batchSend(payload.otherNotifications)
    }
  }
  return { closeVacancy }
}
```

### Payload API

```json
PUT /api/v1/job-vacancies/{id}
{
  "status": "Encerrada",
  "hired_candidate_id": "uuid-candidato",
  "closed_at": "2026-03-10T...",
  "closure_reason": "filled"
}

POST /api/v1/communications/send
{
  "recipient_type": "candidate",
  "recipient_id": "uuid-candidato",
  "channel": "email",
  "template_id": "proposta_aceita",
  "context": {
    "candidate_name": "João Silva",
    "job_title": "Engenheiro de Software Sênior",
    "company_name": "WeDOTalent"
  }
}

POST /api/v1/communications/batch-send
{
  "recipient_ids": ["uuid1", "uuid2"],
  "channel": "email",
  "template_id": "vaga_encerrada",
  "context": { "job_title": "..." }
}
```

### Banco de Dados

```sql
-- Adicionar à tabela job_vacancies:
hired_candidate_id  UUID REFERENCES candidates(id)
closed_at           TIMESTAMP
closure_reason      VARCHAR(50)  -- 'filled' | 'cancelled' | 'on_hold'
closed_by           UUID REFERENCES users(id)

-- Nova tabela placements:
CREATE TABLE placements (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id       UUID NOT NULL REFERENCES companies(id),
  job_vacancy_id   UUID NOT NULL REFERENCES job_vacancies(id),
  candidate_id     UUID NOT NULL REFERENCES candidates(id),
  placed_at        TIMESTAMP DEFAULT now(),
  placed_by        UUID REFERENCES users(id),
  start_date       DATE,
  salary_agreed    DECIMAL(10,2),
  notes            TEXT,
  created_at       TIMESTAMP DEFAULT now(),
  UNIQUE(job_vacancy_id)
);
```

---

### CARD VGM-010: Envio de Notificações de Fechamento e Placement
**Épico:** VGM — Gestão de Vagas

```yaml
Titulo: "[BACKEND] Endpoints de Notificação de Fechamento e Placement de Candidatos"
Tipo: Feature
Area: Backend
Sprint: 3
Início: 01/Abr
Término: 14/Abr
Data Inicio Jira: 2026-04-01
Data Termino Jira: 2026-04-14
Pontos: 8
Prioridade: Alta
Epic: EPIC-VGM
Status: 📋 Pendente Jira

Dependencias: VGM-009

Descricao: |
  ⚠️ Este card implementa o que está faltando no protótipo. O modal de
  fechamento (VGM-009) captura os dados de notificação, mas o envio real
  ainda não foi implementado. Este card cobre os endpoints de envio de
  comunicação, os templates, e a integração com os canais (email via
  SendGrid/Resend, WhatsApp via Meta/Twilio).

Historia de Usuario: |
  Como candidato contratado, quero receber uma mensagem de parabéns
  pela contratação. Como candidato não selecionado, quero receber uma
  comunicação respeitosa informando que a vaga foi encerrada, para ter
  um encerramento digno do processo.

Regras de Negocio:
  1. Envio é assíncrono (não bloqueia a UI) — disparado via fila (RabbitMQ/Celery)
  2. Email via SendGrid (primário) com fallback para Resend/Mailgun
  3. WhatsApp via Meta Business API ou Twilio WhatsApp
  4. Canal "ambos": dispara email E WhatsApp independentemente
  5. Rastreamento: cada envio gera registro em communication_logs
  6. Falha no envio: retry automático 3x com backoff exponencial
  7. LGPD: candidato deve ter dado consentimento para receber mensagens (verificar consent_status)
  8. Rate limiting: máximo 100 emails/minuto por company para envios em massa
  9. Template da mensagem é editável pelo recrutador no modal antes do envio

Requisitos Tecnicos:
  Frontend:
    - Service communicationsApi.ts com send(), batchSend(), getHistory()
    - Composable useCommunicationTemplates.ts com templates por situação
    - Integrado ao modal VGM-009 — sem nova tela
  Backend:
    - POST /api/v1/communications/send
    - POST /api/v1/communications/batch-send
    - GET /api/v1/job-vacancies/{id}/communication-history
    - Celery task send_closure_notifications com retry 3x backoff exponencial
    - Verificação de consent_status antes de enviar
    - Rate limiter 100 emails/min por company
  Dados:
    - Nova tabela communication_logs (ver schema abaixo)
    - Índices em job_vacancy_id, candidate_id, status
  Validacoes:
    - candidate_id obrigatório no send
    - channel enum email|whatsapp|both
    - template_id obrigatório ou custom_message obrigatório
    - Candidato sem email/telefone: ignorar com log
    - Candidato sem consentimento LGPD: ignorar com log

Design & Componentes:
  Componentes Existentes:
    - Integrado ao CloseVacancyModal.vue (VGM-009)
    - Toast para feedback pós-envio
  Novos Componentes:
    - Nenhum componente novo — backend + service layer
  Design Tokens:
    N/A — sem nova UI
  Layout:
    N/A
  Estados:
    - loading durante envio: spinner no botão Confirmar do modal VGM-009
    - Pós-envio: toast com contagem de notificações
  Acessibilidade:
    N/A — sem nova UI

Comportamento de UI:
  Fluxo Principal:
    1. Recrutador confirma fechamento no modal VGM-009
    2. Frontend chama communicationsApi.send() para contratado
    3. Frontend chama communicationsApi.batchSend() para demais
    4. Backend enfileira tasks Celery
    5. Tasks processam e registram em communication_logs
    6. Toast "Notificações enviadas para X candidatos"
  Estados de Botoes:
    Confirmar Encerramento (do modal VGM-009):
      - Loading durante envio: spinner
  Validacoes Inline:
    N/A no frontend
  Mensagens de Feedback:
    - Sucesso: "Notificações enviadas para X candidatos"
    - Erro parcial: "Vaga encerrada, mas algumas notificações falharam"

Referencias de Design:
  Design System: "Design System LIA v4.2.1 — plataforma-lia/docs/design-system/00-design-system-v4.md"
  Figma: "[A ser preenchido pelo time de Design]"
  Vue Migration: ".agents/skills/vue-migration-prep/SKILL.md"

DoD:
  - [ ] Candidato contratado → email/WhatsApp de parabéns disparado
  - [ ] Demais candidatos selecionados → email "vaga encerrada" disparado
  - [ ] Canal "ambos" → email E WhatsApp enviados separadamente
  - [ ] Falha no envio → retry automático 3x com backoff
  - [ ] Candidato sem email/telefone → notificação ignorada com log
  - [ ] LGPD: candidato sem consentimento → não notificado, log registrado
  - [ ] communication_logs registrado para cada tentativa
  - [ ] Rate limiting: >100/min → fila respeita limite

Criterios de Aceitacao:
  - [ ] Envio assíncrono: resposta da API imediata, processamento em background
  - [ ] Celery task com max_retries=3 e backoff exponencial
  - [ ] communication_logs com status pending → sent/failed
  - [ ] GET /communication-history retorna histórico paginado
  - [ ] Merge fields substituídos corretamente nos templates

Arquivos de Referencia (Prototipo):
  - screening-email-templates.ts: plataforma-lia/src/data/screening-email-templates.ts
  - use-communication-templates.ts: plataforma-lia/src/hooks/use-communication-templates.ts
  - email_service.py: lia-agent-system/app/services/email_service.py
  - whatsapp_service.py: lia-agent-system/app/services/whatsapp_service.py
  - notification_service.py: lia-agent-system/app/services/notification_service.py
  - celery_app.py: lia-agent-system/app/core/celery_app.py
```

### Implementação Vue/Nuxt

#### Service: `services/communicationsApi.ts`
```typescript
export const communicationsApi = {
  async send(payload: SendPayload) {
    return api.post('/communications/send', payload)
  },
  async batchSend(payload: BatchSendPayload) {
    return api.post('/communications/batch-send', payload)
  },
  async getHistory(jobId: string) {
    return api.get(`/job-vacancies/${jobId}/communication-history`)
  }
}
```

#### Composable: `composables/useCommunicationTemplates.ts`
```typescript
export function useCommunicationTemplates(situation: string) {
  const templates = ref<Template[]>([])
  onMounted(async () => {
    templates.value = await communicationsApi.getTemplates({ situation })
  })
  return { templates }
}
```

### Backend

#### Templates necessários

| Situação | Template ID | Canal | Destinatário |
|----------|-------------|-------|--------------|
| Proposta aceita / Contratação | `proposta_aceita` | email + WhatsApp | Candidato contratado |
| Vaga encerrada | `vaga_fechada` | email + WhatsApp | Demais candidatos |
| Feedback construtivo | `feedback_construtivo` | email | Demais candidatos |

**Merge fields disponíveis:**
```
{{ candidate_name }}, {{ job_title }}, {{ company_name }},
{{ recruiter_name }}, {{ start_date }}, {{ department }}
```

#### Endpoints Backend

```
POST /api/v1/communications/send
Body: {
  recipient_type: 'candidate',
  recipient_id: UUID,
  channel: 'email' | 'whatsapp' | 'both',
  template_id: string,
  custom_message?: string,
  subject?: string,
  context: { candidate_name, job_title, company_name, ... }
}

POST /api/v1/communications/batch-send
Body: {
  recipient_ids: UUID[],
  channel: 'email' | 'whatsapp' | 'both',
  template_id: string,
  custom_message?: string,
  context: { job_title, company_name, ... }
}

GET /api/v1/job-vacancies/{id}/communication-history
Response: [{ id, recipient, channel, template, status, sent_at, opened_at }]
```

#### Integrações

**Email (SendGrid):**
```python
# lia-agent-system/app/services/email_service.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

async def send_email(to: str, subject: str, body: str, template_id: str = None):
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    message = Mail(
        from_email=settings.FROM_EMAIL,
        to_emails=to,
        subject=subject,
        html_content=body
    )
    sg.send(message)
```

**WhatsApp (Meta API):**
```python
# lia-agent-system/app/services/whatsapp_service.py
async def send_whatsapp(phone: str, message: str, template: str = None):
    url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": { "body": message }
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload,
                         headers={"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"})
```

**Celery Task:**
```python
# lia-agent-system/app/jobs/celery_tasks.py
@celery_app.task(bind=True, max_retries=3)
def send_closure_notifications(self, job_id: str, payload: dict):
    try:
        # processa envios
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Banco de Dados

```sql
CREATE TABLE communication_logs (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id           UUID NOT NULL REFERENCES companies(id),
  job_vacancy_id       UUID REFERENCES job_vacancies(id),
  candidate_id         UUID REFERENCES candidates(id),
  channel              VARCHAR(20) NOT NULL,
  template_id          VARCHAR(100),
  message              TEXT,
  subject              VARCHAR(255),
  status               VARCHAR(20) DEFAULT 'pending',
  provider             VARCHAR(50),
  provider_message_id  VARCHAR(255),
  sent_at              TIMESTAMP,
  opened_at            TIMESTAMP,
  failed_at            TIMESTAMP,
  error_message        TEXT,
  created_at           TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_comm_logs_vacancy   ON communication_logs(job_vacancy_id);
CREATE INDEX idx_comm_logs_candidate ON communication_logs(candidate_id);
CREATE INDEX idx_comm_logs_status    ON communication_logs(status);
```

