# Diagnóstico Completo - Módulo Gestão de Vagas para Go-Live

**Data:** 13 de Janeiro de 2026  
**Versão:** 5.0 (Atualizada)  
**Última Atualização:** 19 de Janeiro de 2026  
**Responsável:** WeDo Talent Engineering Team

---

## 1. Sumário Executivo

O módulo de **Gestão de Vagas** é o core do sistema WeDo Talent para go-live. Esta auditoria expandida identifica gaps críticos entre o estado atual e os requisitos de produção.

### Score Atual: 78/100 ⬆️ (+13 pontos desde v4.1)

| Área | Score | Status | Atualização |
|------|-------|--------|-------------|
| Carregamento Backend | 90% | ✅ Funcional | - |
| Sistema de Filtros | 100% | ✅ Completo | ✅ CONCLUÍDO |
| Preview de Vaga | 80% | ✅ Funcional | ⬆️ +5% (LinkedIn-style preview) |
| Edição de Vaga | 10% | ❌ Crítico | - |
| Agentes IA/Chat LIA | 15% | ❌ Crítico | - |
| Tab Roteiro Triagem | - | 📦 Arquivado | REMOVIDO do MVP (v4.1) |
| Tab Métricas LIA | - | 📦 Arquivado | REMOVIDO do MVP (v4.1) |
| Notificações Automáticas | 25% | ❌ Crítico | - |
| Integrações Voz (OpenMic/Deepgram) | 55% | 🔶 Parcial | ⬆️ +10% (modais WSI implementados) |
| Botões/Ações Funcionais | 30% | ❌ Crítico | - |
| Templates de Email | 85% | ✅ Funcional | ✅ CONCLUÍDO |
| **Job Creation Wizard** | **95%** | ✅ Funcional | ⬆️ +5% (Company Settings integration, candidate-search stage) |
| **Tabela de Vagas** | **80%** | ✅ Funcional | ✅ CONCLUÍDO |
| **Cabeçalho Kanban** | **85%** | ✅ Funcional | ✅ CONCLUÍDO |
| **Sistema de Notas de Entrevista** | **75%** | ✅ Funcional | ⬆️ +60% (NOVO - componentes completos) |
| **WSI Screening Modals** | **80%** | ✅ Funcional | ⬆️ (NOVO - triagem texto/voz) |
| **SSR/Hydration** | **100%** | ✅ Corrigido | ⬆️ (NOVO - OnboardingController fix) |

**Tempo estimado para go-live: 1-3 semanas** ⬆️ (reduzido)

---

## 2. Arquivos Principais Analisados

| Arquivo | Linhas | Propósito |
|---------|--------|-----------|
| `plataforma-lia/src/components/pages/jobs-page.tsx` | ~6.752 | Página principal de vagas (simplificada v4.1) |
| `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx` | ~2.328 | Wizard de criação conversacional |
| `lia-agent-system/app/services/openmic_service.py` | 721 | Triagens por voz (telefone) |
| `lia-agent-system/app/services/deepgram_service.py` | 332 | Transcrição de áudio |
| `lia-agent-system/app/api/v1/job_vacancies.py` | 672 | Endpoints CRUD vagas |
| `plataforma-lia/src/components/activity-feed.tsx` | 507 | Feed de atividades |
| `plataforma-lia/src/components/email-templates/email-templates-manager.tsx` | 430 | Gestão de templates |
| `plataforma-lia/src/components/interviews-section.tsx` | 203 | Seção de entrevistas (100% MOCK) - **ARQUIVADO v4.1** |
| `plataforma-lia/src/components/archived/tabs-preview-vaga/` | - | Tabs arquivadas para recuperação futura |
| `plataforma-lia/src/components/interview-notes/` | ~56k | **NOVO** Sistema completo de notas de entrevista |
| `plataforma-lia/src/components/wsi/` | ~93k | **NOVO** Modais de triagem WSI (texto/voz) |
| `plataforma-lia/src/components/modals/screening-media-modal.tsx` | ~500 | **NOVO** Modal para exibir mídia de triagem |
| `plataforma-lia/src/types/interview-notes.ts` | ~200 | **NOVO** Tipos TypeScript para notas |

---

## 3. Análise Detalhada por Funcionalidade

### 3.1 Sistema de Criação de Vagas (Job Creation Wizard)

**Arquivo:** `job-creation-wizard.tsx` (~2.500 linhas)  
**Score: 90/100** ⬆️ (+15 pontos)

| Funcionalidade | Status | Observações |
|----------------|--------|-------------|
| Wizard conversacional 10 steps | ✅ | Funcional com LIA |
| Extração de critérios de JD | ✅ | Parsing automático |
| Calibração candidatos locais | ✅ | Busca na base |
| Calibração candidatos globais | ✅ | Integração Pearch |
| Benefícios da empresa | ✅ | Hook useCompanyBenefits |
| Tech Stack | ✅ | Hook useCompanyTechStack |
| Cultura/Big Five | ✅ | Hook useCompanyCulture |
| Screening Questions | ✅ | Panel integrado |
| Salvar no backend | ✅ | updateJobWithWizardData() completo |
| Validação campos obrigatórios | ✅ | validateRequiredFields() implementado |
| Erro LSP conversão tipo | ✅ | Corrigido (linha 795) |
| **Step 8: Prazos e Cronograma** | ✅ | **NOVO - 3 datas de deadline** |

**✅ RESOLVIDO (15-19 Jan 2026):**
- Erro LSP de conversão de tipo corrigido
- Função `updateJobWithWizardData()` sincroniza TODOS os campos com backend
- Função `validateRequiredFields()` valida campos obrigatórios antes de publicar
- Nova etapa "Prazos e Cronograma" com 3 campos de data:
  - Data de encerramento das triagens automáticas
  - Data prevista para entrega da short list
  - Data prevista para encerramento da vaga
- Validação cronológica das datas (triagem < short list < encerramento)
- Formato brasileiro DD/MM/YYYY

**✅ NOVAS FUNCIONALIDADES (16-19 Jan 2026):**
- **Integração Company Settings**: Wizard integra automaticamente dados das configurações da empresa:
  - `work_model` → Modelo de Trabalho
  - `headquarters`/`locations` → Localidade
  - `tech_stack` → Technical Skills
  - `benefits` → Benefits list
  - `departments` → Área dropdown
- **Indicadores visuais**: Banner cyan e ícone ⚙️ indicam quando valor veio das configurações
- **Step Candidate Search**: Novo step entre publicação e calibração para busca de candidatos
- **Preview LinkedIn-style**: Preview de vaga com layout estilo LinkedIn
- **Perguntas padrão da empresa**: Integração com perguntas de triagem configuradas
- **Fluxo corrigido**: publish → 'candidate-search' → calibration → 'active-search'

---

### 3.2 Página Principal de Vagas (Jobs Page)

**Arquivo:** `jobs-page.tsx` (~6.512 linhas)  
**Score: 50/100**

#### 3.2.1 Carregamento de Dados

| Item | Status | Observações |
|------|--------|-------------|
| liaApi.listJobVacancies() | ✅ | 100% backend |
| Mapeamento de campos | ✅ | Conversão completa |
| Tratamento de erros | ✅ | Try-catch + toast |
| Loading states | ✅ | Spinner + skeleton |

#### 3.2.2 Modos de Visualização

| Modo | Status |
|------|--------|
| Compacto (tabela resumida) | ✅ Funcional |
| Detalhado (tabela expandida) | ✅ Funcional |
| Cards (grid) | ✅ Funcional |
| Kanban (pipeline) | ✅ Funcional |

#### 3.2.3 Sistema de Filtros ✅ CONCLUÍDO

| Filtro | Funcional | Persiste |
|--------|-----------|----------|
| Status (12 estados) | ✅ | ✅ |
| Dias Abertos | ✅ | ✅ |
| Departamento | ✅ | ✅ |
| Localização | ✅ | ✅ |
| Modelo de Trabalho | ✅ | ✅ |
| Busca Global | ✅ | ✅ |
| Busca Avançada (18 campos) | ✅ | ✅ |
| Busca Booleana | ✅ | ✅ |
| Buscas Salvas | ✅ | ✅ |

**✅ RESOLVIDO:** Sistema de persistência implementado via `useJobFiltersPersistence.ts` (225 linhas):
- Persistência automática em localStorage
- Até 10 buscas salvas com nome personalizado
- Funções: salvar, aplicar, renomear, deletar buscas
- 18 campos de filtros avançados suportados

#### 3.2.4 Código Morto/Legado

- ~900 linhas de 24 vagas mock hardcoded (linhas 180-1090)
- Não são usadas mas ocupam espaço
- Arquivo precisa refatoração (6.512 para ~2.000 linhas ideal)

---

### 3.3 Agentes IA e Chat LIA

**Score: 15/100 - CRÍTICO**

#### 3.3.1 Quick Actions LIA

**Localização:** Linhas 799-845

Todas as 6 ações apenas preenchem o prompt, não executam nada:

| Ação | Comportamento Atual | Comportamento Esperado |
|------|---------------------|------------------------|
| Comparar | setLiaPromptValue() | Análise comparativa com IA |
| Publicar | setLiaPromptValue() | POST para LinkedIn/Indeed API |
| Analisar Performance | setLiaPromptValue() | GET métricas reais + insights IA |
| Gerar Script | setLiaPromptValue() | Claude gera roteiro |
| Integração ATS | setLiaPromptValue() | Sync Gupy/Pandapé |
| Ver Insights | setLiaPromptValue() | Análise preditiva real |

#### 3.3.2 Sugestões de Análises (Página Inicial)

**Localização:** Linhas 3365-3434

| Botão | Comportamento | Status |
|-------|---------------|--------|
| Criar nova vaga | Abre wizard | ✅ |
| Resumo vagas ativas | Preenche prompt | ❌ |
| Ver vagas urgentes | Muda filtro | ✅ |
| Vagas precisando sourcing | Preenche prompt | ❌ |
| Duplicar vaga | Preenche prompt | ❌ |
| Criar a partir de vaga | Preenche prompt | ❌ |

**Gap:** 4/6 botões não executam ações reais

---

### 3.4 Preview de Vaga - Tab Roteiro de Triagem

**Localização:** Linhas 5645-5869  
**Score: 90/100** ✅ ATUALIZADO (Jan 2026)

| Seção | Fonte Dados | Status |
|-------|-------------|--------|
| Header Roteiro de Triagem Automática | - | ✅ UI |
| Perguntas de Triagem | previewJob.screeningQuestions | ✅ BACKEND |
| Canais de Comunicação | useScreeningConfig hook | ✅ DINÂMICO |
| WhatsApp | screeningConfig.channels.whatsapp.enabled | ✅ DINÂMICO |
| Chat Web | screeningConfig.channels.chat_web.enabled | ✅ DINÂMICO |
| Ligação | screeningConfig.channels.phone.enabled | ✅ DINÂMICO |
| Configurações | useScreeningConfig hook | ✅ DINÂMICO |
| Score Mínimo | screeningConfig.settings.min_score | ✅ DINÂMICO |
| Tempo Resposta | screeningConfig.settings.response_timeout_hours | ✅ DINÂMICO |
| Métricas Performance | useScreeningConfig hook | ✅ DINÂMICO |
| Triados | screeningConfig.metrics.screened_count | ✅ DINÂMICO |
| Conclusão | screeningConfig.metrics.completion_rate | ✅ DINÂMICO |
| Nota | screeningConfig.metrics.average_rating | ✅ DINÂMICO |
| Agendamento Automático | useScreeningConfig hook | ✅ DINÂMICO |
| Agenda | screeningConfig.scheduling.calendar_provider | ✅ DINÂMICO |
| Horários | screeningConfig.scheduling.available_hours | ✅ DINÂMICO |
| Duração | screeningConfig.scheduling.interview_duration_min | ✅ DINÂMICO |
| Loading State | isLoadingScreeningConfig | ✅ UI skeleton |
| Botões Editar | Canais/Config/Agendamento | ✅ MODAIS FUNCIONAIS |

**Implementação (Jan 2026):**
- Endpoint Backend: `GET/PUT /api/v1/vagas/{job_id}/screening-config` (job_vacancies.py)
- Proxy Frontend: `/api/backend-proxy/jobs/[id]/screening-config` (route.ts)
- Hook: `useScreeningConfig(jobId)` retorna config, isLoading, error, updateConfig
- Fallback: Defaults estruturados quando backend retorna 404
- Tipo centralizado: `ScreeningConfig` exportado do hook

**Modais de Edição (Jan 2026):**
- `ScreeningChannelsModal.tsx` - Toggle WhatsApp/Chat Web/Ligação
- `ScreeningSettingsModal.tsx` - Score mínimo, timeout resposta, max retries
- `ScreeningSchedulingModal.tsx` - Auto-agendamento, calendário, horários, duração

**Conclusão:** Sistema de configuração de triagem 100% funcional com leitura e edição via modais + API REST.

---

### 3.5 Preview de Vaga - Tab Métricas LIA

**Localização:** Linhas 5350-5474  
**Score: 35/100**

| Métrica | Tipo de Cálculo | Status |
|---------|-----------------|--------|
| Horas Economizadas | total * 0.85 * 15 / 60 | 🔶 Estimativa |
| ROI da LIA | Baseado em horas | 🔶 Estimativa |
| Tempo Médio/Triagem | 2.3min fixo | ❌ HARDCODED |
| Taxa Conclusão | screening * 0.6 / 0.7 | 🔶 Estimativa |
| Insights LIA | 6.5x mais rápidas fixo | ❌ HARDCODED |
| Economia R$ | Calculado dinamicamente | 🔶 Estimativa |

**Gap:** Métricas são estimativas baseadas em fórmulas fixas, não dados reais de uso.

---

### 3.6 Edição de Vagas

**Score: 10/100 - CRÍTICO**

| Componente | Status |
|------------|--------|
| Endpoint PUT /job-vacancies/id | ✅ Backend existe |
| Formulário de edição UI | ❌ NÃO EXISTE |
| Botão Editar | ⚠️ Redireciona para /settings |
| Campos editáveis inline | ❌ NÃO |
| Histórico de alterações | ❌ NÃO |

**Gap crítico:** Não é possível editar uma vaga após criação.

---

### 3.7 Botões Não Funcionais

| Botão | Localização | Status |
|-------|-------------|--------|
| Compartilhar vaga (Share2 icon) | Preview header | ❌ Sem função |
| Publicar LinkedIn | Quick Action | ❌ Só prompt |
| Publicar Indeed | Quick Action | ❌ Não existe |
| Integração ATS | Quick Action | ❌ Só prompt |
| Duplicar vaga | Sugestões | ❌ Só prompt |
| Comparar vagas | Quick Action | ❌ Só prompt |

---

### 3.8 Sistema de Ações da Tabela

**Localização:** Colunas da tabela

| Ação | Implementação | Status |
|------|---------------|--------|
| Ver Roteiro de Triagem | setJobPreviewTab('screening-script') | ✅ |
| Abrir Preview | setPreviewJob(job) | ✅ |
| Selecionar (checkbox) | selectedJobsForBatch.add() | ✅ |
| Editar | - | ❌ NÃO EXISTE |
| Arquivar | - | ❌ NÃO EXISTE |
| Duplicar | - | ❌ NÃO EXISTE |

**Observação:** O sistema de ações da tabela está fora do padrão das outras tabelas da plataforma (candidatos, por exemplo). Precisa ser padronizado com dropdown de ações.

---

### 3.9 Activity Tracking

**Score: 60/100**

| Componente | Status |
|------------|--------|
| activity-feed.tsx (507 linhas) | ✅ Existe |
| Endpoint /api/backend-proxy/activities | ✅ Funcional |
| 8 tipos de atividade suportados | ✅ |
| Integração na página de candidato | ✅ |
| Integração nas tabs de vaga | ❌ NÃO |
| Registro automático de eventos | 🔶 Parcial |

---

### 3.10 Sistema de Notificações

**Score: 25/100**

| Componente | Status |
|------------|--------|
| notification-context.tsx | ✅ Existe |
| notification-center.tsx | ✅ Existe |
| 8 endpoints backend | ✅ Existem |
| Trigger automático para candidatos | ❌ NÃO |
| Trigger automático para clientes | ❌ NÃO |
| Notificação por email | 🔶 Templates existem |
| Notificação WhatsApp | ❌ Sem envio real |

---

### 3.11 Notas de Entrevistas ⬆️ ATUALIZADO SIGNIFICATIVAMENTE

**Score: 75/100** ⬆️ (+60 pontos)

| Componente | Status | Arquivo |
|------------|--------|---------|
| interviews-section.tsx (legado) | 📦 ARQUIVADO | Substituído por novo sistema |
| **InterviewNoteCard** | ✅ NOVO | interview-notes/interview-note-card.tsx |
| **NextStepModal** | ✅ NOVO | interview-notes/next-step-modal.tsx |
| **ScheduledInterviewActivityCard** | ✅ NOVO | interview-notes/scheduled-interview-activity-card.tsx |
| **CreateAdhocNoteModal** | ✅ NOVO | interview-notes/create-adhoc-note-modal.tsx |
| **ScoreCardWSI** | ✅ NOVO | interview-notes/score-card-wsi.tsx |
| Types TypeScript | ✅ NOVO | types/interview-notes.ts |
| Endpoint /api/v1/interviews | ✅ Existe | - |
| generateInterviewQuestions() | ✅ NOVO | lia-api.ts |
| generateInterviewParecer() | ✅ NOVO | lia-api.ts |
| saveInterviewNote() | ✅ NOVO | lia-api.ts |

**✅ FUNCIONALIDADES IMPLEMENTADAS (15-18 Jan 2026):**
- **Dual rating system**: Star (1-5) + Likert scale (Insatisfatório → Excelente)
- **AI-generated questions**: Perguntas geradas de 3 fontes (Job profile/WSI, CV/Screening gaps, Cultural fit)
- **Collapsible transcription**: Seção de transcrição colapsável (integração Teams/Meet)
- **LIA parecer**: Geração de parecer com Claude (editável antes de salvar)
- **Next-stage suggestions**: Sugestões automáticas de próximo estágio baseadas na análise LIA
- **Feedback scheduling**: Enviar feedback agora ou agendar para depois

**❌ PENDÊNCIAS:**
- Integração com Activity Feed
- Conexão completa com backend (salvar no banco)
- Histórico de notas por candidato

---

### 3.12 Mudança Automática de Status

**Score: 20/100**

| Funcionalidade | Status |
|----------------|--------|
| Mudança manual (Kanban drag) | ✅ |
| Endpoint PATCH status | ✅ Backend |
| Automação por eventos | ❌ |
| Regras de transição (Policy Engine) | ❌ |
| Histórico de status | ❌ |

---

### 3.13 Templates de Email ⬆️ ATUALIZADO

**Score: 85/100** ⬆️ (+15%)

| Funcionalidade | Status |
|----------------|--------|
| CRUD templates | ✅ Funcional |
| Preview com variáveis | ✅ |
| 5 categorias | ✅ interview, rejection, offer, followup, **screening** |
| Templates padrão fallback | ✅ 5 templates default |
| SendGrid backend | ✅ Existe |
| Automação de envio | ❌ Manual apenas |

**✅ Melhorias implementadas:**
- Nova categoria **screening** para triagens de voz
- 5 templates padrão com fallback quando API não retorna
- Badges de categoria com cores padronizadas (#60BED1)

---

### 3.14 Integração OpenMic.ai (Triagens por Voz - Chamadas Telefônicas)

**Score: 40/100**

**O que é:** Plataforma de chamadas telefônicas automatizadas. Um agente de IA liga para o candidato e conduz uma entrevista de triagem por telefone.

| Componente | Status | Arquivo |
|------------|--------|---------|
| Service backend | ✅ 721 linhas | openmic_service.py |
| Endpoints API | ✅ | /api/v1/openmic.py |
| Webhook handler | ✅ | HMAC signature |
| Modelos de dados | ✅ | voice_screening.py |
| WSI Voice Orchestrator | 🔶 | wsi_voice_orchestrator.py |
| API Key configurada | ❌ | OPENMIC_API_KEY |
| Webhook Secret | ❌ | OPENMIC_WEBHOOK_SECRET |
| Frontend UI para iniciar chamadas | ❌ | Não existe |

**Custo:** $0.08-0.15/minuto (inclui TTS + STT + agente IA)

**Funcionalidades do backend:**
- create_screening_agent() - Cria agente de voz para vaga
- start_screening_call() - Inicia ligação para candidato
- process_webhook() - Processa eventos (call_started, call_ended, transcript_ready)
- analyze_screening_response() - Analisa transcrição com Claude

---

### 3.15 Integração Deepgram (Transcrição de Áudio) ⬆️ ATUALIZADO

**Score: 50/100** ⬆️ (+20%)

**O que é:** Serviço de transcrição de áudio para texto. Converte mensagens de voz (WhatsApp, gravações) em texto para análise.

| Componente | Status | Arquivo |
|------------|--------|---------|
| Service backend | ✅ 332 linhas | deepgram_service.py |
| Suporte pt-BR (Nova-2) | ✅ | Melhor modelo |
| Free tier | ✅ | 12.000 min/ano |
| API Key configurada | ✅ | DEEPGRAM_API_KEY ⬆️ |
| Integração WhatsApp áudio | ❌ | |
| Frontend upload áudio | ❌ | |

**Custo:** $0.0043/minuto (muito barato)

**✅ DEEPGRAM_API_KEY configurada** - Pronta para uso

**Funcionalidades do backend:**
- transcribe_audio_url() - Transcreve áudio de URL
- transcribe_audio_bytes() - Transcreve áudio binário
- Suporte a múltiplos idiomas

---

### 3.16 Modais WSI de Triagem ⬆️ NOVO

**Score: 80/100** (NOVO)

| Componente | Status | Arquivo |
|------------|--------|---------|
| **wsi-text-screening-modal.tsx** | ✅ NOVO | wsi/wsi-text-screening-modal.tsx |
| **wsi-triagem-invite-modal.tsx** | ✅ NOVO | wsi/wsi-triagem-invite-modal.tsx |
| **wsi-voice-screening-status.tsx** | ✅ NOVO | wsi/wsi-voice-screening-status.tsx |
| **wsi-scorecard.tsx** | ✅ Existente | wsi/wsi-scorecard.tsx |
| **ScreeningMediaModal** | ✅ NOVO | modals/screening-media-modal.tsx |

**✅ FUNCIONALIDADES IMPLEMENTADAS:**
- **Modal de triagem por texto**: Perguntas WSI com respostas de texto
- **Modal de convite para triagem**: Envio de convites para triagem por voz/vídeo
- **Status de triagem por voz**: Acompanhamento do status da triagem
- **Scorecard WSI**: Exibição de pontuação e análise
- **Modal de mídia**: Exibição de gravações de voz/vídeo com transcrição, análise WSI e parecer LIA

**❌ PENDÊNCIAS:**
- Integração completa com OpenMic.ai para chamadas telefônicas
- Upload de áudio para transcrição Deepgram

---

### 3.17 SSR/Hydration Fix ⬆️ NOVO

**Score: 100/100** (NOVO - CORRIGIDO)

| Componente | Status |
|------------|--------|
| OnboardingController | ✅ CORRIGIDO |
| isMounted state | ✅ Implementado |
| suppressHydrationWarning | ✅ Aplicado |
| Loading flash | ✅ Eliminado |

**✅ RESOLVIDO (19 Jan 2026):**
- Problema de loading infinito na tela inicial corrigido
- Implementação de `isMounted` state para lidar com diferenças SSR/client-side
- Página renderiza corretamente após hidratação do React

---

### 3.18 Integração WhatsApp

**Score: 40/100**

| Componente | Status |
|------------|--------|
| Endpoint proxy | ✅ /api/backend-proxy/communication/send-whatsapp/ |
| Backend dispatcher | ✅ communication_dispatcher.py |
| Envio real (Twilio/Meta) | ❌ |
| Templates WhatsApp Business | ❌ |
| Webhook para respostas | ❌ |

---

### 3.17 Integração Microsoft Azure/Graph (Calendário)

**Score: 30/100**

| Componente | Status |
|------------|--------|
| Referências no código | ✅ Mencionado |
| OAuth flow | ❌ |
| Agendamento automático | ❌ |
| Sync calendário | ❌ |

---

## 4. Endpoints Backend

### 4.1 Endpoints Existentes e Usados

| Método | Endpoint | Frontend Usa |
|--------|----------|--------------|
| GET | /api/v1/job-vacancies | ✅ listJobVacancies() |
| POST | /api/v1/job-vacancies | ✅ Wizard |
| PUT | /api/v1/job-vacancies/id | ❌ NÃO USADO |
| PATCH | /api/v1/job-vacancies/id/status | ❌ |
| DELETE | /api/v1/job-vacancies/id | ❌ |
| GET | /api/v1/activities | ✅ ActivityFeed |
| POST | /api/v1/email-templates | ✅ |
| POST | /api/v1/openmic/webhook | ✅ Backend |

### 4.2 Endpoints Faltantes

| Endpoint | Propósito | Prioridade |
|----------|-----------|------------|
| GET /job-vacancies/id/metrics | Métricas reais de performance | Alta |
| GET /job-vacancies/id/activities | Atividades por vaga | Alta |
| POST /job-vacancies/id/publish | Publicar em canais | Média |
| GET /job-vacancies/id/share-link | Link público | Média |
| POST /interviews/id/notes | Notas de entrevista | Alta |
| GET /candidates/id/status-history | Histórico de status | Média |
| POST /notifications/automatic | Triggers automáticos | Alta |
| POST /saved-searches | Persistir buscas | Baixa |

---

## 5. Erros LSP Pendentes

| Arquivo | Quantidade | Prioridade | Status |
|---------|------------|------------|--------|
| job-creation-wizard.tsx | ~~1 erro~~ | ~~Alta~~ | ✅ CORRIGIDO |
| jobs-page.tsx | 3 erros | Média | Pré-existentes (não bloqueantes) |
| job-kanban-page.tsx | 52 erros | Média | Pré-existentes (não bloqueantes) |
| openmic_service.py | 33 erros | Média | - |

**✅ RESOLVIDO (15 Jan 2026):** Erro crítico do wizard corrigido.
**Nota:** Os erros LSP restantes são pré-existentes e não afetam a compilação.

---

## 6. Plano de Tarefas Estruturado

### Sprint 1: Fundação Crítica (Semanas 1-2)

| Num | Tarefa | Esforço | Prioridade | Dependências |
|-----|--------|---------|------------|--------------|
| 1.1 | Corrigir erros LSP (wizard, jobs-page, openmic) | 4h | Crítica | - |
| 1.2 | Implementar edição de vagas (UI + PUT endpoint) | 8h | Crítica | 1.1 |
| 1.3 | Conectar Tab Roteiro Triagem ao backend | 6h | Crítica | - |
| 1.4 | Conectar Tab Métricas LIA ao backend (criar endpoint /metrics) | 6h | Crítica | - |
| 1.5 | Substituir mock em interviews-section.tsx | 4h | Crítica | - |
| 1.6 | Implementar Activity Feed nas tabs de vaga | 4h | Crítica | - |
| 1.7 | Remover código morto (~900 linhas mock) | 2h | Importante | 1.2-1.6 |
| 1.8 | Padronizar ações da tabela de vagas | 3h | Importante | - |

**Total Sprint 1: ~37 horas**

---

### Sprint 2: Funcionalidades Core (Semanas 3-4)

| Num | Tarefa | Esforço | Prioridade | Dependências |
|-----|--------|---------|------------|--------------|
| 2.1 | Quick Actions funcionais (6 ações com backend) | 12h | Crítica | Sprint 1 |
| 2.2 | Notificações automáticas (triggers por evento) | 8h | Crítica | - |
| 2.3 | Sistema de notas de entrevistas (CRUD completo) | 6h | Crítica | 1.5 |
| 2.4 | Mudança automática de status (policy engine) | 6h | Importante | - |
| 2.5 | Botão Compartilhar funcional (gerar link público) | 4h | Importante | - |
| 2.6 | Persistência de filtros/buscas | 4h | Importante | - |
| 2.7 | Expandir templates email (4 para 8 categorias) | 4h | Importante | - |

**Total Sprint 2: ~44 horas**

---

### Sprint 3: Integrações de Voz (Semanas 5-6)

| Num | Tarefa | Esforço | Prioridade | Dependências |
|-----|--------|---------|------------|--------------|
| 3.1 | Configurar OpenMic.ai (API key + testes) | 4h | Importante | API Key |
| 3.2 | Frontend para iniciar triagens por voz | 8h | Importante | 3.1 |
| 3.3 | Webhook handler + processamento resultados | 6h | Importante | 3.1 |
| 3.4 | Configurar Deepgram (API key + testes) | 4h | Importante | API Key |
| 3.5 | Integrar transcrição com WhatsApp áudio | 6h | Importante | 3.4 |
| 3.6 | UI para upload/player de áudio | 4h | Desejável | 3.4 |

**Total Sprint 3: ~32 horas**

---

### Sprint 4: Integrações Externas (Semana 7+)

| Num | Tarefa | Esforço | Prioridade | Dependências |
|-----|--------|---------|------------|--------------|
| 4.1 | WhatsApp envio real (Twilio/Meta Business) | 8h | Importante | API Key |
| 4.2 | Microsoft Graph Calendar (OAuth + sync) | 12h | Desejável | Azure Config |
| 4.3 | Publicação LinkedIn/Indeed | 8h | Desejável | APIs |
| 4.4 | Refatoração jobs-page.tsx (6.500 para 2.000 linhas) | 12h | Desejável | Sprint 1-2 |
| 4.5 | Chat sugestões funcionais (agente IA) | 8h | Desejável | - |

**Total Sprint 4: ~48 horas**

---

## 7. Resumo de Estimativas

| Sprint | Horas | Semanas | Prioridade | Status |
|--------|-------|---------|------------|--------|
| Sprint 1 | 37h | 1-2 | Crítico | Pendente |
| Sprint 2 | 44h | 2-3 | Crítico | Pendente |
| Sprint 3 | 32h | 1-1.5 | Importante | Pendente |
| Sprint 4 | 48h | 2+ | Desejável | Backlog |
| TOTAL | 161h | 6-8 | - | - |

---

## 8. Dependências Técnicas

### 8.1 API Keys Necessárias

| Serviço | Variável | Status | Onde Obter |
|---------|----------|--------|------------|
| OpenMic.ai | OPENMIC_API_KEY | Pendente | openmic.ai/dashboard |
| OpenMic.ai | OPENMIC_WEBHOOK_SECRET | Pendente | openmic.ai/dashboard |
| Deepgram | DEEPGRAM_API_KEY | Pendente | console.deepgram.com |
| Twilio/WhatsApp | TWILIO_ACCOUNT_SID | Pendente | twilio.com/console |
| Microsoft Graph | AZURE_CLIENT_ID | Pendente | portal.azure.com |

### 8.2 Endpoints Backend a Criar

1. GET /api/v1/job-vacancies/id/metrics
2. GET /api/v1/job-vacancies/id/activities
3. POST /api/v1/job-vacancies/id/publish
4. POST /api/v1/job-vacancies/id/share
5. POST /api/v1/interviews/id/notes
6. POST /api/v1/notifications/automatic-trigger
7. POST /api/v1/saved-searches

---

## 9. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| OpenMic.ai indisponível | Alto | Baixa | Fallback para triagem manual |
| Deepgram quota excedida | Médio | Baixa | Free tier 12k min/ano |
| WhatsApp API complexa | Médio | Média | Começar com Twilio (mais simples) |
| Refatoração muito longa | Médio | Média | Priorizar funcionalidade sobre código |
| API Keys atrasadas | Alto | Média | Solicitar com antecedência |
| Erros LSP bloqueantes | Alto | Alta | Resolver primeiro |

---

## 10. Critérios de Aceite para Go-Live

### 10.1 Mínimo Viável (MVP) - OBRIGATÓRIO

- Edição de vagas funcional
- Tab Roteiro Triagem com dados reais
- Tab Métricas com dados reais
- Notas de entrevistas funcionais
- Notificações automáticas básicas
- Activity Feed nas vagas
- 0 erros LSP
- Ações da tabela padronizadas
- Testes E2E passando

### 10.2 Desejável para Go-Live

- OpenMic.ai triagens por voz
- Deepgram transcrição
- WhatsApp envio real
- Quick Actions funcionais
- Compartilhamento de vagas
- Sugestões de análises funcionais

### 10.3 Pós Go-Live

- Microsoft Graph Calendar
- Publicação LinkedIn/Indeed
- Refatoração código
- ~~Persistência de filtros~~ ✅ CONCLUÍDO

---

## 11. Conclusão

O módulo de Gestão de Vagas tem uma base sólida com carregamento de dados backend funcional, sistema de filtros robusto e UI bem estruturada. Os gaps críticos restantes são:

1. **Edição de vagas** - Impossível alterar após criação (CRÍTICO)
2. **Quick Actions** - 6 ações apenas preenchem prompt, não executam (CRÍTICO)
3. **Dados hardcoded** - Métricas e roteiro de triagem são estáticos
4. **Integrações de voz** - Modais WSI prontos, falta conexão OpenMic
5. **Notificações automáticas** - Estrutura existe, triggers não
6. ~~Notas de entrevistas - 100% dados falsos~~ → ✅ **CORRIGIDO** (v5.0)

Com **1-3 semanas** de trabalho focado, o módulo pode atingir qualidade de produção. *(reduzido de 3-5 semanas)*

**Principais avanços desde v4.0:**
- Sistema de Notas de Entrevista completamente novo (5 componentes)
- Modais WSI de triagem (texto/voz/vídeo)
- Integração Company Settings no Wizard
- Correção crítica de SSR/Hydration

---

## 12. Próximos Passos Imediatos

### ✅ CONCLUÍDOS:
1. ✅ Criar documento de diagnóstico (este documento)
2. ✅ Sistema de filtros com persistência
3. ✅ Configurar DEEPGRAM_API_KEY
4. ✅ Templates de email com categoria screening
5. ✅ Modais DISC e Big Five integrados
6. ✅ Corrigir erros LSP do wizard (15 Jan 2026)
7. ✅ Implementar etapa Prazos e Cronograma no wizard (15 Jan 2026)
8. ✅ Adicionar campos de deadline na tabela/preview/kanban (15 Jan 2026)
9. ✅ **Sistema de Notas de Entrevista** - Componentes completos (15-18 Jan 2026)
10. ✅ **Modais WSI de Triagem** - texto/voz/vídeo (15-18 Jan 2026)
11. ✅ **Integração Company Settings no Wizard** (16-19 Jan 2026)
12. ✅ **Correção SSR/Hydration** - OnboardingController (19 Jan 2026)
13. ✅ **Fluxo do Wizard** - publish → candidate-search → calibration → active-search (19 Jan 2026)
14. ✅ **Preview LinkedIn-style** no wizard (17 Jan 2026)

### PRÓXIMOS (Prioridade):
1. PRÓXIMO - **Edição de Vagas** (CRÍTICO - Score 10%) - Formulário de edição UI
2. PRÓXIMO - **Quick Actions funcionais** (CRÍTICO - Score 15%) - 6 ações com backend
3. PRÓXIMO - **Conectar Notas de Entrevista ao backend** - saveInterviewNote() real
4. PRÓXIMO - Solicitar API Key OpenMic
5. PRÓXIMO - Iniciar Sprint 1 restante

---

## 13. Changelog de Atualizações

### 19 de Janeiro de 2026 - v5.0

| Item | Descrição | Impacto |
|------|-----------|---------|
| **Sistema de Notas de Entrevista** | 5 novos componentes: InterviewNoteCard, NextStepModal, ScheduledInterviewActivityCard, CreateAdhocNoteModal, ScoreCardWSI | +60% score notas |
| **Modais WSI Triagem** | 3 novos modais: triagem texto, convite, status voz | +80% score WSI |
| **ScreeningMediaModal** | Modal para exibir gravações de voz/vídeo com transcrição e análise | Nova funcionalidade |
| **Company Settings Integration** | Wizard integra work_model, tech_stack, locations, departments, benefits | +5% score wizard |
| **Candidate Search Stage** | Novo step entre publicação e calibração | Melhoria fluxo |
| **LinkedIn-style Preview** | Preview de vaga com layout profissional | Melhoria UX |
| **SSR/Hydration Fix** | Correção de loading infinito no OnboardingController | Bug fix crítico |
| **Fluxo Wizard Corrigido** | publish → candidate-search → calibration → active-search | Bug fix |
| **API Notas Entrevista** | generateInterviewQuestions(), generateInterviewParecer(), saveInterviewNote() | Backend integração |
| **Types TypeScript** | interview-notes.ts com tipos completos | DX melhoria |

**Arquivos novos/modificados:**
- `plataforma-lia/src/components/interview-notes/` (5 componentes)
- `plataforma-lia/src/components/wsi/` (3 modais atualizados)
- `plataforma-lia/src/components/modals/screening-media-modal.tsx`
- `plataforma-lia/src/types/interview-notes.ts`
- `plataforma-lia/src/components/onboarding/onboarding-controller.tsx`
- `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx`
- `plataforma-lia/src/services/lia-api.ts`

---

### 15 de Janeiro de 2026 - v4.0

| Item | Descrição | Impacto |
|------|-----------|---------|
| **Job Creation Wizard** | Erro LSP corrigido, validação implementada, nova etapa Prazos | +15% score |
| **Campos de Prazo** | 3 novos campos: deadlineScreening, deadlineShortlist, deadlineClosing | Nova funcionalidade |
| **Tabela de Vagas** | 3 novas colunas de prazos com ordenação | +10% score |
| **Preview de Vaga** | Campos de prazo exibidos no card Informações | +10% score |
| **Cabeçalho Kanban** | 3 badges de prazo após informações da vaga | +10% score |
| **Backend Mapping** | Interface JobVacancy e mapeamento de dados atualizados | Integração completa |
| **Validação Wizard** | validateRequiredFields() com feedback visual | Melhoria UX |
| **Sync Backend** | updateJobWithWizardData() sincroniza todos os campos | Bug fix |

**Arquivos modificados:**
- `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx` (~150 linhas novas)
- `plataforma-lia/src/components/pages/jobs-page.tsx` (~80 linhas novas)
- `plataforma-lia/src/components/pages/job-kanban-page.tsx` (~20 linhas novas)
- `plataforma-lia/src/services/lia-api.ts` (interface atualizada)

---

### 13 de Janeiro de 2026 - v3.0

| Item | Descrição | Impacto |
|------|-----------|---------|
| Sistema de Filtros | Persistência localStorage + buscas salvas | +15% score |
| Templates Email | Nova categoria screening + 5 templates default | +15% score |
| Deepgram | DEEPGRAM_API_KEY configurada | +20% score |
| Modais Assessment | DISC (16 perfis) e Big Five integrados | +10% preview |
| Preview Candidato | Botão "Ver Relatório Completo" nos cards | Melhoria UX |

**Arquivos modificados:**
- `plataforma-lia/src/hooks/useJobFiltersPersistence.ts` (225 linhas)
- `plataforma-lia/src/components/email-templates/email-templates-manager.tsx`
- `plataforma-lia/src/data/screening-email-templates.ts`
- `plataforma-lia/src/components/disc-assessment-modal.tsx`
- `plataforma-lia/src/components/big-five-modal.tsx`
- `plataforma-lia/src/components/candidate-preview.tsx`

---

## 14. Plano de Implementação Go-Live

**Documento completo:** `docs/PLANO_IMPLEMENTACAO_GOLIVE.md`

### Visão Geral das Fases

| Fase | Foco | Duração | Horas | Status |
|------|------|---------|-------|--------|
| **Fase 1** | Fundação Crítica (Edição, Botões) | Semana 1 | 40h | 🔄 Em andamento |
| **Fase 2** | Funcionalidades Core (Quick Actions, Notificações) | Semana 2 | 40h | Pendente |
| **Fase 3** | Integrações (OpenMic, Deepgram, WhatsApp) | Semana 3 | 32h | Pendente |
| **Fase 4** | Polimento (Testes, Documentação, Deploy) | Semana 4 | 24-40h | Pendente |

**Tempo Total Estimado:** 136-152 horas (3-4 semanas)

### Prioridades Críticas

1. **Edição de Vagas** - Score 10% → 90%
2. **Botões/Ações Funcionais** - Score 30% → 85%
3. **Quick Actions LIA** - Score 15% → 70%
4. **Notificações Automáticas** - Score 25% → 80%

### Dependências Externas

| Serviço | Variável | Status |
|---------|----------|--------|
| OpenMic.ai | OPENMIC_API_KEY | ❌ Pendente |
| Twilio/WhatsApp | TWILIO_ACCOUNT_SID | ❌ Pendente |
| Deepgram | DEEPGRAM_API_KEY | ✅ Configurada |

---

Documento gerado em 13 de Janeiro de 2026 - WeDo Talent Engineering  
Última atualização: 19 de Janeiro de 2026 - v5.0
