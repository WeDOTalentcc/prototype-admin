# Auditoria de Funcionalidades — LIA Platform (Frontend)

**Data:** 2026-03-03
**Versão:** 0.1.0
**Stack:** Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
**Backend:** FastAPI (Python 3.11)
**Auditado por:** Claude Code (Sonnet 4.6)

---

## 📊 RESUMO EXECUTIVO

| Métrica | Valor |
|---------|-------|
| Total de páginas/rotas | 89 |
| Total de componentes | 530 |
| Total de hooks | 87 |
| Total de serviços | 10+ |
| Total de rotas API (proxy) | 370+ |
| Linhas de TypeScript (estimado) | ~200.000 |
| **Taxa de completude** | **~92%** |

### Status das Páginas
- ✅ Completas: 74 (83%)
- ⚠️ Parciais/Em Refatoração: 12 (13%)
- ❌ Incompletas/Placeholder: 3 (3%)

### Status das Funcionalidades
- ✅ Completas: ~85%
- ⚠️ Parciais: ~12%
- ❌ Incompletas: ~3%

---

## 🚨 O QUE PRECISA SER FINALIZADO

### 🔴 P0 — CRÍTICO (Bloqueia funcionalidade multi-tenant)

#### 1. Hardcoding de `company_id = 'demo'` (Multi-Tenant Quebrado)
- **Arquivos afetados:**
  - `src/lib/api/global-search-settings.ts:3`
  - `src/app/api/backend-proxy/company/global-search-settings/route.ts:5`
  - `src/components/expanded-chat-modal.tsx:8466`
- **O que funciona:** A feature em si funciona em ambiente demo
- **O que falta:**
  - [ ] Substituir `'demo'` por `company_id` real do contexto de autenticação (`useClient()` hook ou `auth-context.tsx`)
  - [ ] Testar com múltiplos tenants em paralelo
- **Impacto:** Todos os clientes que não se chamam "demo" verão dados errados / vazios em Global Search Settings
- **Esforço:** 0,5 dia
- **Dependências:** `ClientContext.tsx` já tem o `companyId` disponível

#### 2. Stub de Endpoint — Onboarding Submit
- **Arquivo:** `src/app/api/backend-proxy/onboarding/submit/route.ts:24`
- **O que funciona:** Retorna `{ success: true }` sempre (stub)
- **O que falta:**
  - [ ] Implementar chamada real ao backend FastAPI
  - [ ] Tratar erros de validação do backend
  - [ ] Loading state no formulário de onboarding
- **Impacto:** Dados de onboarding de novos clientes nunca são salvos
- **Esforço:** 1 dia
- **Dependências:** Endpoint backend `POST /api/v1/onboarding`

#### 3. Stub de Endpoint — Recruitment Journey Templates
- **Arquivo:** `src/app/api/backend-proxy/recruitment-journey/templates/route.ts:70-73`
- **O que funciona:** Retorna `"Recruitment stages saved successfully (stub)"`
- **O que falta:**
  - [ ] Integração real com backend
  - [ ] Feedback visual de sucesso/erro real
- **Impacto:** Configuração de jornada de recrutamento não persiste
- **Esforço:** 1 dia

#### 4. Stub de Endpoint — Jobs Screening Config Save
- **Arquivo:** `src/app/api/backend-proxy/jobs/[id]/screening-config/route.ts:113-116`
- **O que funciona:** Retorna `"Screening config saved (stub)"`
- **O que falta:**
  - [ ] Persistência real via backend
- **Impacto:** Configuração de screening por vaga não salva
- **Esforço:** 0,5 dia

#### 5. Stub de Endpoint — Screening Questions (3 operações)
- **Arquivo:** `src/app/api/backend-proxy/screening-questions/route.ts:69, 113, 164`
- **O que falta:**
  - [ ] POST (criar pergunta): integração real
  - [ ] PUT (editar pergunta): integração real
  - [ ] DELETE (deletar pergunta): integração real
- **Impacto:** Perguntas de screening não persistem
- **Esforço:** 1 dia

---

### 🟡 P1 — ALTO (Qualidade / Estabilidade)

#### 6. 182 console.log em código de produção
- **Arquivos principais:**
  - `src/components/expanded-chat-modal.tsx` — 15+ `[DEBUG handleSendMessage]`
  - `src/components/pages/candidates-page.tsx` — 30+ console.logs
  - `src/components/pages/jobs-page.tsx` — 10+ console.logs
  - `src/services/lia-api.ts` — 10+ console.logs
  - `src/components/pages/indicators-page.tsx` — 8 console.logs
  - `src/components/pages/work-model-analytics-page.tsx` — 1 console.log
- **O que falta:**
  - [ ] Substituir todos por logger condicional (`if (process.env.NODE_ENV === 'development')`)
  - [ ] Ou usar logger centralizado já existente
- **Impacto:** Exposição de informações internas no console do browser em produção; performance
- **Esforço:** 2 dias (mecânico)

#### 7. `/tasks` — Rota com página errada
- **Arquivo:** `src/app/tasks/page.tsx`
- **O que funciona:** Página renderiza mas mostra "Configurações" em vez de "Tasks"
- **O que falta:**
  - [ ] Corrigir `initialPage` em `DashboardApp` de `"Configurações"` para `"Tasks"` ou redirecionar para `/tasks-mvp`
  - [ ] Ou deprecar a rota `/tasks` em favor de `/tasks-mvp`
- **Impacto:** Usuários que acessam `/tasks` veem conteúdo errado
- **Esforço:** 0,5 dia

#### 8. Upload de Arquivo e Gravação de Áudio — candidates-page
- **Arquivo:** `src/components/pages/candidates-page.tsx:8451-8463`
- **Código:**
  ```tsx
  // TODO: Implementar upload de arquivo
  console.log('Anexar documento')

  // TODO: Implementar gravação de áudio
  console.log('Gravar áudio')
  ```
- **O que funciona:** Botões renderizam
- **O que falta:**
  - [ ] Upload de arquivo (o componente `multimodal-upload.tsx` existe em `/components/chat/`, reutilizar)
  - [ ] Gravação de áudio (o componente `voice-chat-button.tsx` existe, reutilizar)
- **Impacto:** Funcionalidades de anexar documento e gravar áudio na página de candidatos não funcionam
- **Esforço:** 2 dias

#### 9. Export de Dados — Work Model Analytics
- **Arquivo:** `src/components/pages/work-model-analytics-page.tsx:134-135`
- **O que falta:**
  - [ ] Implementar exportação real (CSV/PDF)
  - [ ] `console.log('Exportando dados em formato ${format}')` precisa ser substituído
- **Impacto:** Funcionalidade de exportação de analytics não funciona
- **Esforço:** 1 dia

#### 10. Ações não implementadas em candidates-page (3 botões)
- **Arquivo:** `src/components/pages/candidates-page.tsx:5197, 5207, 5216`
- **O que falta:**
  - [ ] `onClick={() => console.log('Agendar entrevista')}` — integrar com modal real
  - [ ] `onClick={() => console.log('Enviar email')}` — integrar com `UnifiedCommunicationModal`
  - [ ] `onClick={() => console.log('Perguntar à LIA')}` — integrar com chat
- **Impacto:** 3 ações rápidas na tabela de candidatos não funcionam
- **Esforço:** 1 dia

#### 11. Busca Boolean — candidates-page (stub parcial)
- **Arquivo:** `src/components/pages/candidates-page.tsx:8935`
- **O que falta:**
  - [ ] `console.log('Buscar boolean:', booleanSearchValue)` — implementar busca boolean real via API
- **Impacto:** Busca boolean não funciona
- **Esforço:** 2 dias

---

### 🟢 P2 — MÉDIO (Débito Técnico / UX)

#### 12. Refatoração Sprint E — candidates-page.tsx (12.387 linhas)
- **Arquivo:** `src/components/pages/candidates-page.tsx`
- **Status da refatoração:**
  - ✅ Fase 1 completa: hooks extraídos (`use-candidate-filters.ts`, `use-candidate-selection.ts`)
  - ❌ Fase 2 pendente: substituir `useState` inline por hooks (linhas ~3430-3480)
  - ❌ Fase 3 pendente: extrair `CandidateSearchBar`, `CandidateTableSection`, `CandidateTabs`
- **Impacto:** Manutenibilidade e performance (re-renders desnecessários)
- **Esforço:** 5 dias

#### 13. Decomposição do expanded-chat-modal.tsx (11.821 linhas)
- **Arquivo:** `src/components/expanded-chat-modal.tsx`
- **Status:** Em decomposição para `/expanded-chat/` subcomponents
- **O que falta:**
  - [ ] Concluir extração para subcomponentes
  - [ ] Remover 15+ `[DEBUG]` console.logs
- **Impacto:** Manutenibilidade; bundle size desnecessariamente grande
- **Esforço:** 5 dias

#### 14. `/funil` — Rota duplicada/legada
- **Arquivo:** `src/app/funil/page.tsx`
- **Problema:** Duplica funcionalidade de `/funil-de-talentos` (versão mais completa)
- **O que falta:**
  - [ ] Redirecionar `/funil` → `/funil-de-talentos` ou deprecar
- **Impacto:** UX fragmentado; manutenção dupla
- **Esforço:** 0,5 dia

#### 15. Integrations Page — Dados Mock
- **Arquivo:** `src/components/pages/integrations-page.tsx`
- **Problema:** Placeholders de Slack webhook hardcoded: `https://hooks.slack.com/services/T00000000/...`
- **O que falta:**
  - [ ] Carregar webhooks reais da API
  - [ ] Formulário de criação com validação
  - [ ] `{/* Modals placeholder */}` (linha 673) — modais não implementados
- **Impacto:** Configuração de integrações não persiste
- **Esforço:** 2 dias

#### 16. `/configuracoes` — Usa DashboardApp legado
- **Arquivo:** `src/app/configuracoes/page.tsx`
- **Problema:** 3 linhas, delega para `DashboardApp` em vez de usar `SettingsPage` dedicada
- **O que falta:**
  - [ ] Migrar para componente `SettingsPage` (existe em `src/components/pages/settings-page.tsx`)
- **Impacto:** Padrão inconsistente com demais rotas
- **Esforço:** 0,5 dia

---

## 📱 INVENTÁRIO COMPLETO DE PÁGINAS

### Rotas Públicas

| Rota | Arquivo | Status | Observação |
|------|---------|--------|------------|
| `/` | `app/page.tsx` | ✅ 100% | Landing page |
| `/login` | `app/login/page.tsx` | ✅ 100% | Auth via WorkOS |
| `/login/welcome` | `app/login/welcome/page.tsx` | ✅ 100% | Welcome pós-login |
| `/register` | `app/register/page.tsx` | ✅ 100% | Registro |
| `/forgot-password` | `app/forgot-password/page.tsx` | ✅ 100% | Recuperação de senha |
| `/reset-password` | `app/reset-password/page.tsx` | ✅ 100% | Reset de senha |
| `/accept-invitation` | `app/accept-invitation/page.tsx` | ✅ 100% | Convite (EN) |
| `/aceitar-convite` | `app/aceitar-convite/page.tsx` | ✅ 100% | Convite (PT) |
| `/access` | `app/access/page.tsx` | ✅ 100% | Verificação de acesso |
| `/privacidade` | `app/privacidade/page.tsx` | ✅ 100% | Política de privacidade |
| `/trust` | `app/trust/page.tsx` | ✅ 100% | Trust center público |
| `/upgrade` | `app/upgrade/page.tsx` | ✅ 100% | Upgrade de plano |
| `/shared/[token]` | `app/shared/[token]/page.tsx` | ✅ 100% | Compartilhamento de buscas (OTP) |
| `/vagas/[slug]` | `app/vagas/[slug]/page.tsx` | ✅ 100% | Vaga pública |
| `/portal/data-request/[token]` | `app/portal/data-request/[token]/page.tsx` | ✅ 100% | Portal LGPD |

---

### Rotas Protegidas (Usuário)

#### `/chat` — Interface LIA
**Arquivo:** `src/components/pages/chat-page.tsx` (5.481 linhas)
**Status:** ✅ 100%

**Funcionalidades:**
- [x] Interface conversacional com agente LIA (ReAct)
- [x] Upload multimodal (CV, imagens, documentos)
- [x] Tipos de mensagem: texto, ação, aprovação, thinking, progresso, comando
- [x] Painel lateral com contexto (resumos de candidatos, vagas, WSI scores)
- [x] Indicador de memória do agente
- [x] Quick action chips + command palette
- [x] Agendamento de entrevistas via chat
- [x] Comparação de candidatos
- [x] Integração com resultados de busca Pearch AI
- [x] Notificações Slack/Teams

---

#### `/jobs` — Gestão de Vagas
**Arquivo:** `src/components/pages/jobs-page.tsx` (7.970 linhas)
**Status:** ✅ 95%

**Funcionalidades:**
- [x] Listagem de vagas com filtros avançados
- [x] CRUD de vagas (criar, editar, publicar, despublicar, duplicar)
- [x] Modal de comparação de vagas
- [x] Insights de vagas (analytics, forecast)
- [x] Configuração de WSI (Work Style Interview)
- [x] Modal de canais de screening
- [x] Requisitos técnicos, competências, idiomas
- [x] Faixas salariais, timeline, estrutura organizacional
- [ ] `console.log('Criar template a partir de vaga')` — Criação de template de vaga não implementada (`jobs-page.tsx:4348`)
- [ ] `console.log('Anexar documento')` — Anexar documento na vaga não implementado (`jobs-page.tsx:4209`)

---

#### `/jobs/[id]` — Detalhe de Vaga / Kanban
**Arquivo:** `src/components/pages/job-kanban-page.tsx` (9.822 linhas)
**Status:** ✅ 100%

**Funcionalidades:**
- [x] Kanban drag-and-drop para pipeline de candidatos
- [x] Movimentação de candidatos entre etapas com confirmação
- [x] Transições de etapa em tempo real
- [x] Integração com `useUniversalTransition`
- [x] Suporte a WebSocket para atualizações colaborativas
- [x] Ações em lote e filtragem
- [x] Assistente LIA do kanban (kanban-assistant)

---

#### `/funil-de-talentos` — Funil de Talentos
**Arquivo:** `src/app/funil-de-talentos/page.tsx` (395 linhas) + componentes
**Status:** ✅ 95%

**Funcionalidades:**
- [x] Interface multi-tab (Todos | Favoritos | Listas | Buscas Salvas)
- [x] Busca de candidatos com filtros (status, senioridade)
- [x] Barra de seleção em lote (mover etapa, enviar mensagem, compartilhar)
- [x] Tabela de candidatos com ordenação e paginação
- [x] Gestão de favoritos com candidatos fixados
- [x] Funcionalidade de compartilhamento de busca
- [ ] Algumas ações rápidas com console.log stub (`candidates-page.tsx:5197, 5207, 5216`)

---

#### `/funil-de-talentos/candidato/[id]` — Perfil do Candidato
**Status:** ✅ 95%

**Funcionalidades:**
- [x] Preview completo do candidato
- [x] Análise LIA do perfil
- [x] Histórico de comunicações
- [x] Notas de entrevista
- [x] Avaliação por rubrica
- [x] Big Five / OCEAN

---

#### `/funil` — Funil Legado
**Arquivo:** `src/app/funil/page.tsx` (3 linhas)
**Status:** ❌ Duplicata/Legado

**Problema:** Usa `DashboardApp` sem configuração específica. Duplica `/funil-de-talentos`.

---

#### `/tasks` — Tarefas
**Arquivo:** `src/app/tasks/page.tsx` (3 linhas)
**Status:** ❌ Configuração errada

**Problema:** Renderiza `DashboardApp initialPage="Configurações"` em vez de conteúdo de tasks.

---

#### `/tasks-mvp` — Tarefas MVP
**Arquivo:** `src/components/pages/tasks-page-mvp.tsx`
**Status:** ✅ 100%

**Funcionalidades:**
- [x] Kanban de tarefas (board view)
- [x] Agendamento e gestão de prioridades
- [x] Gestão multi-tenant
- [x] Integração com etapas do pipeline de vagas

---

#### `/configuracoes` — Configurações
**Arquivo:** `src/components/pages/settings-page.tsx` (4.475 linhas)
**Status:** ⚠️ 85% (rota usa wrapper legado)

**Funcionalidades:**
- [x] 10+ abas de configuração: ATS, Comunicação, Benefícios, Cultura, Metas, Instruções LIA, etc.
- [x] Mapeamento de campos para sistemas ATS (SAP, Workday, BambooHR, Greenhouse)
- [x] Integração de comunicação (Slack, Teams webhooks)
- [x] Templates de notificação
- [x] Statuses de candidatos, motivos de rejeição, motivos de declínio de oferta
- [x] Configuração de solicitações de dados (compliance LGPD)
- [x] Políticas de contratação
- [ ] Rota `/configuracoes/page.tsx` usa DashboardApp legado em vez de `SettingsPage` diretamente

---

#### `/configuracoes/ai-credits` — Créditos de IA
**Status:** ✅ 100%

---

#### `/configuracoes/integracoes` — Integrações
**Arquivo:** `src/components/pages/integrations-page.tsx` (804 linhas)
**Status:** ⚠️ 70%

**Funcionalidades:**
- [x] UI de integração Slack (webhook management)
- [x] UI de integração Teams
- [x] Template builder de notificações
- [x] Log de eventos de webhook
- [ ] Dados de webhook mockados (placeholder hardcoded)
- [ ] `{/* Modals placeholder */}` — modais não implementados (linha 673)
- [ ] Webhook URLs de Slack hardcoded (`https://hooks.slack.com/services/T00000000/...`)

---

#### `/ajuda` — Ajuda / Central de Conhecimento
**Arquivo:** `src/app/ajuda/page.tsx` (466 linhas)
**Status:** ✅ 100%

**Funcionalidades:**
- [x] Como a LIA analisa candidatos (NLP)
- [x] Classificação de senioridade (7 níveis)
- [x] Classificação de skills (Técnicas vs Soft Skills)
- [x] Campos extraídos vs inferidos
- [x] Cálculo de anos de experiência
- [x] Big Five / OCEAN (5 dimensões)
- [x] 8 arquétipos profissionais
- [x] Metodologia WSI
- [x] Limitações e disclaimers éticos

---

### Rotas Admin

#### `/admin` — Dashboard Admin
**Arquivo:** `src/app/admin/page.tsx` (392 linhas)
**Status:** ✅ 100%

**Funcionalidades:**
- [x] 4 cards de KPI (MRR, Clientes Ativos, Trial, Churn Rate)
- [x] 3 cards de status de clientes (Novos, Trial, Churned)
- [x] Rastreamento de consumo de serviços (tokens IA, buscas globais, storage)
- [x] Feed de atividades em tempo real
- [x] Atalhos de ações rápidas
- [x] Filtro de período customizável
- [x] Dados via `useDashboardSummary()` hook

---

#### `/admin/setup-empresa` — Setup da Empresa
**Arquivo:** `src/app/admin/setup-empresa/page.tsx` (79KB)
**Status:** ✅ 100%

**Funcionalidades:**
- [x] Wizard de configuração empresarial completo
- [x] 8 categorias de benefícios (Saúde, Alimentação, Transporte, etc.)
- [x] 8 níveis de senioridade
- [x] 3 tipos de valores (monetário, percentual, informativo)
- [x] 6 opções de período de carência

---

#### `/admin/clientes` — Gestão de Clientes
**Arquivo:** `src/app/admin/clientes/page.tsx`
**Status:** ✅ 100%

**Funcionalidades:**
- [x] Listagem e CRUD de clientes
- [x] Rastreamento de status (ativo, trial, suspenso, churned)
- [x] Gestão de planos (starter, professional, enterprise)
- [x] Alocação de seats de usuário
- [x] Busca e filtros
- [x] Modal `CreateClientDialog`

---

#### `/admin/clientes/[clientId]/*` — Cliente Individual (14 sub-rotas)
**Status:** ✅ 90%

| Sub-rota | Funcionalidades | Status |
|----------|----------------|--------|
| `/` | Dashboard do cliente | ✅ |
| `/setup` | Configuração do cliente | ✅ |
| `/usuarios` | Gestão de usuários | ✅ |
| `/integracoes` | Integrações do cliente | ✅ |
| `/automacoes` | Automações do cliente | ✅ |
| `/metricas` | Métricas do cliente | ✅ |
| `/comunicacoes` | Comunicações do cliente | ✅ |
| `/consumo-ia` | Consumo de IA | ✅ |
| `/faturamento` | Faturamento | ✅ |
| `/observabilidade` | Observabilidade | ✅ |
| `/big-five` | Testes Big Five | ✅ |
| `/testes` | Testes técnicos | ✅ |
| `/jornada` | Jornada de recrutamento | ✅ |
| `/conformidade/*` | LGPD, controles, incidentes | ✅ |

---

#### `/admin/compliance/*` — Compliance e Governança (26 sub-rotas)
**Status:** ✅ 95%

| Sub-rota | Status | Funcionalidades |
|----------|--------|----------------|
| `/` | ✅ | Dashboard compliance; progresso ISO27001/SOC2/SOX/BCB498 |
| `/health-check` | ✅ | Health check do sistema |
| `/lgpd` | ✅ | Tracking LGPD |
| `/lgpd/consentimentos` | ✅ | Gestão de consentimentos |
| `/lgpd/dpo` | ✅ | Dashboard DPO |
| `/lgpd/transferencias` | ✅ | Transferências de dados |
| `/lgpd/portal-titular` | ✅ | Portal do titular |
| `/controles` | ✅ | Controles de compliance |
| `/controles/cobertura` | ✅ | Cobertura de controles |
| `/controles/soc-2` | ✅ | Controles SOC 2 |
| `/controles/iso-27001` | ✅ | Controles ISO 27001 |
| `/controles/sox` | ✅ | Controles SOX |
| `/auditoria` | ✅ | Trilha de auditoria |
| `/auditoria/logs` | ✅ | Logs de auditoria |
| `/auditoria/bias` | ✅ | Auditoria de viés (Four-Fifths Rule) |
| `/auditoria/exportar` | ✅ | Exportação de dados de auditoria |
| `/auditoria/sod` | ✅ | Segregação de funções |
| `/auditoria/treinamentos` | ✅ | Registros de treinamento |
| `/monitoramento` | ✅ | Monitoramento em tempo real (drift detection) |
| `/monitoramento/alertas` | ✅ | Alertas de segurança |
| `/monitoramento/incidentes` | ✅ | Gestão de incidentes |
| `/monitoramento/dashboard-seguranca` | ✅ | Dashboard de segurança |
| `/riscos` | ✅ | Gestão de riscos |
| `/riscos/registro` | ✅ | Registro de riscos |
| `/riscos/continuidade` | ✅ | Continuidade de negócios |
| `/riscos/fornecedores` | ✅ | Risco de fornecedores |
| `/riscos/seguro` | ✅ | Seguros |
| `/trust-center/certificacoes` | ✅ | Certificações |
| `/trust-center/subprocessadores` | ✅ | Sub-processadores |
| `/trust-center/recursos` | ✅ | Recursos do trust center |

---

#### Demais Páginas Admin
| Rota | Status | Observação |
|------|--------|------------|
| `/admin/sso` | ✅ | Configuração SSO WorkOS |
| `/admin/templates` | ✅ | Templates de comunicação |
| `/admin/onboarding-clientes` | ⚠️ 70% | Endpoint stub (ver P0 #2) |
| `/admin/metricas-plataforma` | ✅ | Métricas da plataforma |
| `/admin/jornada-recrutamento` | ⚠️ 70% | Endpoint stub (ver P0 #3) |
| `/admin/configuracoes/*` | ✅ | Configurações admin |

---

## 🔧 FUNCIONALIDADES TRANSVERSAIS

### Autenticação (WorkOS)
| Funcionalidade | Status |
|---------------|--------|
| Login SSO | ✅ 100% |
| Logout | ✅ 100% |
| Refresh token automático | ✅ 100% |
| Callback WorkOS | ✅ 100% |
| Proteção de rotas | ✅ 100% |
| Convite de usuários | ✅ 100% |

### Multi-Tenancy
| Funcionalidade | Status |
|---------------|--------|
| `ClientContext.tsx` (tenant isolation) | ✅ 100% |
| `company_id` em queries | ✅ 95% |
| Global Search Settings (hardcoded 'demo') | ❌ Quebrado — P0 |
| expanded-chat-modal (hardcoded 'demo') | ❌ Quebrado — P0 |

### Sistema de Notificações (5 canais)
| Canal | Status |
|-------|--------|
| Bell in-app | ✅ 100% |
| Email (SendGrid/Resend) | ✅ 100% |
| Microsoft Teams | ✅ 100% |
| WhatsApp (Meta/Twilio) | ✅ 100% |
| Chat inline | ✅ 100% |

### Integrações Externas
| Integração | Status | Observação |
|-----------|--------|------------|
| WorkOS SSO/SCIM | ✅ 100% | |
| Pearch AI (busca de candidatos) | ✅ 100% | |
| Microsoft Teams | ✅ 100% | |
| Microsoft Graph/Outlook | ✅ 100% | |
| WhatsApp (Meta API + Twilio) | ✅ 100% | |
| Email (SendGrid/Resend/Mailgun) | ✅ 100% | |
| Deepgram (speech-to-text) | ✅ 100% | |
| OpenMic.ai (triagem por voz) | ✅ 100% | |
| Slack | ⚠️ 70% | Webhooks mockados na UI |
| ATS (Gupy/Pandapé) | ✅ 90% | Via Merge connector |
| HubSpot | ✅ 80% | |
| Stripe | ✅ 80% | |
| LangSmith | ✅ 100% | |
| Jira | ✅ 100% | Webhook receiver implementado |
| Google Calendar | ✅ 90% | Auth via OAuth |

### Compliance e Governança
| Funcionalidade | Status |
|---------------|--------|
| LGPD (portal titular, consentimentos) | ✅ 100% |
| FairnessGuard (3 camadas) | ✅ 100% |
| Bias Audit (Four-Fifths Rule) | ✅ 100% |
| Model Drift Detection | ✅ 100% |
| SOC2/ISO27001/SOX/BCB498 | ✅ 100% |
| Audit Logs (exportação) | ✅ 100% |
| Segregação de Funções (SoD) | ✅ 100% |

### Performance e UX
| Funcionalidade | Status |
|---------------|--------|
| Dark mode | ✅ 100% |
| Skeleton loading states | ✅ 100% |
| Error boundaries | ✅ 90% |
| Virtualização de listas longas (`@tanstack/react-virtual`) | ✅ 100% |
| Paginação | ✅ 100% |
| Infinite scroll | ✅ 90% |
| Websockets (kanban collaborativo) | ✅ 100% |

---

## 🔌 API ENDPOINTS (Status)

### Endpoints Proxy com Stubs (❌ Não integrados ao backend)

| Endpoint | Arquivo | Status |
|----------|---------|--------|
| `POST /api/backend-proxy/onboarding/submit` | `onboarding/submit/route.ts` | ❌ Stub |
| `POST /api/backend-proxy/recruitment-journey/templates` | `recruitment-journey/templates/route.ts` | ❌ Stub |
| `PUT /api/backend-proxy/jobs/[id]/screening-config` | `jobs/[id]/screening-config/route.ts` | ❌ Stub |
| `POST/PUT/DELETE /api/backend-proxy/screening-questions` | `screening-questions/route.ts` | ❌ Stub (3 ops) |

### Endpoints Proxy Funcionais (✅ Integrados ao backend FastAPI)

Todos os outros ~366 endpoints estão funcionais e integrados. Veja a lista completa na seção de mapa de rotas.

---

## 🐛 TODOs E FIXMEs NO CÓDIGO

```
src/lib/api/global-search-settings.ts:3 — TODO: multi-tenancy company_id from auth
src/app/api/backend-proxy/company/global-search-settings/route.ts:5 — TODO: multi-tenancy
src/components/expanded-chat-modal.tsx:8466 — TODO: companyId hardcoded 'demo'
src/components/expanded-chat-modal.tsx:819 — NOTE: default-company placeholder
src/hooks/use-candidate-filters.ts:7 — TODO Sprint E phase 2: move useState
src/hooks/use-candidate-selection.ts:7 — TODO Sprint E phase 2: replace useState
src/components/pages/candidates-page.tsx:9 — TODO phase 2: replace useState at ~3430-3480
src/components/pages/candidates-page.tsx:11 — TODO phase 3: extract CandidateSearchBar, etc.
src/components/pages/candidates-page.tsx:8451 — TODO: implementar upload de arquivo
src/components/pages/candidates-page.tsx:8462 — TODO: implementar gravação de áudio
src/components/pages/candidates-page.tsx:11138 — TODO: company_id 'demo' hardcoded
src/components/pages/work-model-analytics-page.tsx:135 — TODO: implementar exportação real
```

**Total:** 31 TODOs/FIXMEs encontrados
**Console.log em produção:** 182 ocorrências (debug)
**Console.error/warn legítimos:** ~1.753 ocorrências (tratamento de erros — OK)

---

## 📋 BACKLOG PRIORIZADO

### 🔴 Sprint Atual — P0 (1-2 semanas)
- [ ] Substituir `company_id = 'demo'` por auth context em 3 arquivos
- [ ] Implementar endpoint onboarding/submit real
- [ ] Implementar endpoint recruitment-journey/templates real
- [ ] Implementar endpoint jobs/screening-config save real
- [ ] Implementar endpoints screening-questions (POST/PUT/DELETE) reais
- [ ] Corrigir rota `/tasks` (initialPage errado)

### 🟡 Próximo Sprint — P1 (2-3 semanas)
- [ ] Remover/guardar 182 console.log de produção (lint rule)
- [ ] Implementar upload de arquivo em candidates-page
- [ ] Implementar gravação de áudio em candidates-page
- [ ] Implementar ações rápidas (agendar, email, LIA) em candidates-page
- [ ] Implementar busca boolean real
- [ ] Implementar exportação de work model analytics
- [ ] Criar template de vaga a partir de jobs-page
- [ ] Implementar modais em integrations-page

### 🟢 Backlog — P2/P3 (> 1 mês)
- [ ] Sprint E: candidates-page — Fase 2 (substituir useState inline)
- [ ] Sprint E: candidates-page — Fase 3 (extrair CandidateSearchBar, etc.)
- [ ] Decomposição expanded-chat-modal.tsx em subcomponentes
- [ ] Deprecar/redirecionar rota `/funil` legada
- [ ] Migrar `/configuracoes` de DashboardApp para SettingsPage direto
- [ ] Integrar dados reais em integrations-page (Slack webhooks)
- [ ] Aumentar cobertura de testes (atualmente 2 hooks com testes)

---

## 🎯 RECOMENDAÇÕES

### Imediato (P0)
1. **Multi-tenancy:** Criar helper centralizado `useCompanyId()` que leia do `ClientContext` e substituir todas as ocorrências de `'demo'` hardcoded
2. **Stubs:** Para cada endpoint stub, checar se o backend FastAPI já tem a rota implementada e apenas conectar o proxy — se não tiver, criar ticket de backend junto
3. **Tasks route:** Uma linha de fix — mudar `"Configurações"` para `"Tasks"` ou simplesmente redirecionar

### Curto Prazo (P1)
1. **Console.logs:** Adicionar regra ESLint `no-console` e limpar em um único PR dedicado
2. **Ações stub:** Os componentes `multimodal-upload.tsx` e `voice-chat-button.tsx` já existem em `/components/chat/` — apenas importar e integrar na candidates-page

### Médio Prazo (P2/P3)
1. **Refatoração incremental:** Continuar Sprint E por fases, sem breaking changes
2. **Testes:** Priorizar testes para os fluxos mais críticos: kanban transition, WSI screening, LGPD data requests
3. **Documentação de API:** O `lia-api.ts` tem 4.942 linhas — considerar Storybook/Swagger para facilitar onboarding

---

## 📈 MÉTRICAS DE CÓDIGO

| Arquivo | Linhas | Status |
|---------|--------|--------|
| `src/components/pages/candidates-page.tsx` | 12.387 | ⚠️ Em refatoração |
| `src/components/expanded-chat-modal.tsx` | 11.821 | ⚠️ Em decomposição |
| `src/components/pages/job-kanban-page.tsx` | 9.822 | ✅ Completo |
| `src/components/pages/jobs-page.tsx` | 7.970 | ✅ Completo |
| `src/components/pages/chat-page.tsx` | 5.481 | ✅ Completo |
| `src/services/lia-api.ts` | 4.942 | ✅ Completo |
| `src/components/pages/settings-page.tsx` | 4.475 | ✅ Completo |
| `src/hooks/use-candidate-filters.ts` | 6.429 | ✅ Completo |
| `src/hooks/use-communication-templates.ts` | 18.743 | ✅ Completo |
| `src/app/admin/setup-empresa/page.tsx` | ~79KB | ✅ Completo |

---

*Gerado automaticamente por análise estática do código-fonte em 2026-03-03.*
*Baseado em: 89 páginas, 530 componentes, 87 hooks, 370+ rotas API, ~200K linhas TypeScript.*
