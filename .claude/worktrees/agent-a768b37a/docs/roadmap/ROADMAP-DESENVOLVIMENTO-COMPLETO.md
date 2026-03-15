# Roadmap de Desenvolvimento - WeDo Talent
## Análise Estratégica, Mapeamento de Funcionalidades e Planejamento

**Versão**: 1.0  
**Data**: Dezembro 2024  
**Plataforma**: WeDo Talent / Plataforma LIA

---

## Índice

1. [Análise Estratégica: Admin vs Gestão de Vagas](#1-análise-estratégica-admin-vs-gestão-de-vagas)
2. [Roadmap em 3 Streams](#2-roadmap-em-3-streams)
3. [Escopo para Freelancer Vue.js](#3-escopo-para-freelancer-vuejs)
4. [Roadmap Proposto](#4-roadmap-proposto)
5. [Mapeamento: Menu Configurações (Admin Cliente)](#5-mapeamento-menu-configurações-admin-cliente)
6. [Mapeamento: Gestão de Vagas](#6-mapeamento-gestão-de-vagas)
7. [Mapeamento: Admin WeDo Talent (Multi-Tenant)](#7-mapeamento-admin-wedo-talent-multi-tenant)
8. [Análise WorkOS: Funcionalidades Substituíveis](#8-análise-workos-funcionalidades-substituíveis)
9. [Comparativo Final e Recomendações](#9-comparativo-final-e-recomendações)

---

## 1. Análise Estratégica: Admin vs Gestão de Vagas

### 1.1 Contexto

- **Time interno**: Desenvolvendo Funil de Talentos (React/TypeScript atual)
- **Pendente de desenvolvimento**: Admin/Configurações e Gestão de Vagas
- **Terceirização**: Dev freelancer Vue.js/Vuetify/Nuxt para parte do frontend
- **Gestão de Vagas**: Mais complexa (muita IA: wizard 8 etapas, clusterização, WSI)
- **Admin**: Serve como base para funcionalidades de Vagas

### 1.2 Recomendação: Admin Primeiro, Depois Vagas

**Por quê?** Gestão de Vagas depende de entidades que o Admin provê:

| Dependência do Admin | Usado em Gestão de Vagas |
|---------------------|--------------------------|
| Empresas/Tenants | Vaga pertence a um tenant |
| Usuários/Permissões | Quem pode criar/aprovar vagas |
| Templates de comunicação | Notificações de vaga publicada |
| Políticas de compliance | LGPD, aprovações, audit trail |
| Integrações (ATS, Pearch) | Publicação e sourcing |
| Benefícios | Seleção no wizard de vaga |
| Departamentos | Hierarquia e aprovadores |
| Pipeline de Recrutamento | Etapas do processo seletivo |

### 1.3 Grafo de Dependências

```
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (APIs REST)                       │
│              Domínio compartilhado entre módulos             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
    ┌─────────────────┐ ┌─────────────┐ ┌─────────────────┐
    │  CONFIGURAÇÕES  │ │ ADMIN WEDO  │ │  FUNIL TALENTOS │
    │  (Admin Cliente)│ │   TALENT    │ │   (Em desenv.)  │
    └────────┬────────┘ └──────┬──────┘ └─────────────────┘
             │                 │
             └────────┬────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │   GESTÃO DE VAGAS   │
           │  (Depende de Admin) │
           └─────────────────────┘
```

---

## 2. Roadmap em 3 Streams

### 2.1 Estrutura de Streams

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAM 1: BACKEND                         │
│              (Time Interno - APIs REST/FastAPI)              │
│  Domínio compartilhado: Admin + Vagas + Funil de Talentos   │
└─────────────────────────────────────────────────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│   STREAM 2: ADMIN   │     │   STREAM 3: GESTÃO DE VAGAS     │
│  (Freelancer Vue)   │     │  (Interno + Freelancer parcial) │
│  Baixa complexidade │     │      Alta complexidade IA       │
│  Vue.js + Vuetify   │     │   React (atual) → Vue (futuro)  │
└─────────────────────┘     └─────────────────────────────────┘
```

### 2.2 Responsabilidades por Stream

| Stream | Responsável | Tecnologia | Escopo |
|--------|-------------|------------|--------|
| **Backend** | Time interno | FastAPI + Python | APIs, serviços IA, integrações |
| **Admin** | Freelancer | Vue.js + Vuetify + Nuxt | UI CRUD, forms, listagens |
| **Vagas** | Interno + Freelancer | React → Vue | Wizard (freelancer UI), IA (interno) |

---

## 3. Escopo para Freelancer Vue.js

### 3.1 Ideal para Freelancer (UI/CRUD, sem lógica de negócio complexa)

| Módulo | Componentes | Complexidade | Prioridade |
|--------|-------------|--------------|------------|
| **Shell/Navigation** | Layout base, sidebar, header, breadcrumbs | Baixa | P0 |
| **Dashboard Tenant** | Métricas e overview | Baixa | P1 |
| **Gestão de Usuários** | CRUD + listagem + filtros + convites | Média | P0 |
| **Gestão de Permissões** | Matriz de roles/permissions | Média | P1 |
| **Departamentos** | CRUD + hierarquia visual | Média | P1 |
| **Benefícios** | CRUD + categorias + elegibilidade | Média | P1 |
| **Templates Comunicação** | Editor + preview + variáveis | Média | P2 |
| **Config. Integrações** | Forms de API keys + status | Baixa | P2 |
| **Visualizador Audit Log** | Listagem + filtros + export | Baixa | P2 |
| **Configurações Gerais** | Forms de preferências | Baixa | P2 |

### 3.2 Parcialmente Freelancer (UI sim, lógica IA interno)

| Módulo Vagas | Freelancer Faz | Time Interno Faz |
|--------------|----------------|------------------|
| **Wizard 8 etapas** | UI dos steps, forms, validação | Orquestração AI, clusterização |
| **Painel Clusterização** | Visualização de insights | Serviço AI que gera insights |
| **Builder Perguntas WSI** | UI de arrastar/editar | Engine de geração de perguntas |
| **Publicação Multi-canal** | Formulário de canais | Integração com Pearch/ATS |
| **Kanban de Vagas** | Board + drag-drop | Regras de negócio de status |

### 3.3 Manter 100% Interno

- Orquestração de agentes AI (LangGraph)
- Serviços de clusterização/WSI
- Policy Engine e regras de negócio
- Compliance LGPD/Audit
- Integrações Pearch, ATS, Microsoft Graph
- Backend APIs completo

### 3.4 Estratégia API-First

Para o freelancer trabalhar bem, definir contratos de API antes:

```
/api/v1/admin/
  ├── /tenants          # Multi-tenant management
  ├── /users            # Gestão de usuários
  ├── /roles            # Roles e permissões
  ├── /permissions      # Matriz de permissões
  ├── /departments      # Departamentos e hierarquia
  ├── /benefits         # Benefícios da empresa
  ├── /templates        # Templates de comunicação
  ├── /integrations     # Configuração de integrações
  └── /audit-logs       # Logs de auditoria

/api/v1/jobs/
  ├── /                 # CRUD de vagas
  ├── /wizard/steps     # Dados do wizard
  ├── /wizard/ai-suggestions  # Sugestões IA
  ├── /clustering       # Análise de clusterização
  ├── /wsi-questions    # Perguntas WSI geradas
  └── /publications     # Publicação multi-canal
```

**Regra**: Freelancer consome APIs, não implementa lógica de negócio.

---

## 4. Roadmap Proposto

### 4.1 Timeline Geral

```
         Mês 1          Mês 2          Mês 3          Mês 4          Mês 5
    ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
    │   FASE 1     │   FASE 2     │   FASE 3     │   FASE 4     │   FASE 5     │
    │ Setup + Base │Admin Completo│ Vagas UI     │ Vagas IA     │ Integração   │
    │              │              │              │              │ + Polish     │
    └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
         Backend        Freelancer     Freelancer     Interno        Todos
         + WorkOS       Vue.js         + Interno      IA Core
```

### 4.2 Fase 1: Setup + Base (Semanas 1-4)

| Semana | Backend | Frontend (Freelancer) |
|--------|---------|----------------------|
| 1 | Setup APIs base, WorkOS integration | Setup projeto Vue/Nuxt, Design System |
| 2 | APIs Usuários, Roles, Permissions | Shell + Navigation + Auth (WorkOS) |
| 3 | APIs Departamentos, Benefícios | Dashboard + Componentes base |
| 4 | APIs Templates, Integrações | Testes + Ajustes |

**Entregável**: Estrutura base funcional com auth WorkOS

### 4.3 Fase 2: Admin Completo (Semanas 5-10)

| Semana | Backend | Frontend (Freelancer) |
|--------|---------|----------------------|
| 5-6 | APIs Empresa & Equipe completas | CRUD Usuários + Permissões |
| 7-8 | APIs Comunicação, Alertas | Templates + Departamentos + Benefícios |
| 9-10 | APIs Metas, Busca Global | Metas + Configurações + Audit Log |

**Entregável**: Admin/Configurações 100% funcional

### 4.4 Fase 3: Vagas UI (Semanas 11-16)

| Semana | Backend | Frontend |
|--------|---------|----------|
| 11-12 | APIs Wizard steps 1-4 | Wizard etapas 1-4 (Freelancer) |
| 13-14 | APIs Wizard steps 5-8 | Wizard etapas 5-8 (Freelancer) |
| 15-16 | APIs Listagem, Kanban | Listagem + Kanban (Freelancer) |

**Entregável**: UI de Gestão de Vagas (sem IA)

### 4.5 Fase 4: Vagas IA (Semanas 17-22)

| Semana | Backend (Interno) | Frontend (Interno) |
|--------|-------------------|-------------------|
| 17-18 | Serviço extração JD, clusterização | Integração AI no wizard |
| 19-20 | Serviço geração perguntas WSI | Calibração + Sourcing |
| 21-22 | Big Five, análise de mercado | Relatórios + Insights |

**Entregável**: Gestão de Vagas com IA completa

### 4.6 Fase 5: Integração + Polish (Semanas 23-26)

| Semana | Atividade |
|--------|-----------|
| 23-24 | Integração end-to-end, testes |
| 25-26 | Bug fixes, performance, polish |

**Entregável**: Produto pronto para produção

---

## 5. Mapeamento: Menu Configurações (Admin Cliente)

### 5.1 Estrutura de Seções

O menu Configurações possui **6 seções principais** com **18 subseções**:

```
Configurações/
├── 1. Empresa & Equipe (5 subseções)
│   ├── Dados da Empresa
│   ├── Departamentos
│   ├── Benefícios
│   ├── Usuários
│   └── Aprovadores
├── 2. Recrutamento (2 subseções)
│   ├── Pipeline
│   └── Perguntas Screening
├── 3. Comunicação & Alertas (4 subseções)
│   ├── Templates
│   ├── Assinatura
│   ├── Horários LGPD
│   └── Alertas
├── 4. Metas & Planejamento (2 subseções)
│   ├── Metas
│   └── Workforce Planning
├── 5. Busca Global (3 subseções)
│   ├── Limites
│   ├── Opções
│   └── Custos
└── 6. Painel de Controle (2 subseções)
    ├── Tarefas
    └── Atividades
```

### 5.2 Mapeamento Detalhado de Funcionalidades

#### 5.2.1 Empresa & Equipe (15 funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | Campos |
|---|---------------|------|--------------|--------|
| 1.1 | CRUD Dados da Empresa (nome, CNPJ, logo, site) | Form | Baixa | company_name, cnpj, website, email, phone |
| 1.2 | Upload e preview de logo | Upload | Baixa | logo |
| 1.3 | CRUD Departamentos | CRUD | Média | departments |
| 1.4 | Hierarquia organizacional (árvore) | UI complexa | Alta | hierarchy |
| 1.5 | CRUD Benefícios da empresa | CRUD | Média | benefits |
| 1.6 | Elegibilidade de benefícios por cargo/dept | Regras | Média | eligibility |
| 1.7 | CRUD Usuários/Recrutadores | CRUD | Média | users |
| 1.8 | Convite de novos usuários (email) | Integração | Média | - |
| 1.9 | Gestão de Roles (Admin, Recrutador, Viewer) | CRUD | Média | roles |
| 1.10 | Matriz de Permissões | UI complexa | Alta | permissions |
| 1.11 | CRUD Aprovadores | CRUD | Média | approvers |
| 1.12 | Configuração de Fluxo de Aprovação | Workflow | Alta | approval_flow |
| 1.13 | Notificações de aprovação pendente | Notif | Média | - |
| 1.14 | Histórico de aprovações | Listagem | Baixa | - |
| 1.15 | Validação de dados obrigatórios | Validação | Baixa | - |

#### 5.2.2 Recrutamento (8 funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | Campos |
|---|---------------|------|--------------|--------|
| 2.1 | Visualização do Pipeline (etapas) | UI | Média | stages |
| 2.2 | Configuração de etapas (CS only) | Config | Média | flow |
| 2.3 | Ordenação de etapas (drag & drop) | UI | Média | - |
| 2.4 | CRUD Perguntas de Screening | CRUD | Média | screening_questions |
| 2.5 | Editor de perguntas com preview | Editor | Média | - |
| 2.6 | Categorização de perguntas | Tags | Baixa | - |
| 2.7 | Ativação/desativação por vaga | Toggle | Baixa | - |
| 2.8 | Templates de perguntas pré-definidas | Templates | Média | - |

#### 5.2.3 Comunicação & Alertas (12 funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | Campos |
|---|---------------|------|--------------|--------|
| 3.1 | CRUD Templates de Email | CRUD | Média | email_templates |
| 3.2 | Editor rich text para templates | Editor | Alta | - |
| 3.3 | Variáveis dinâmicas ({{nome}}, {{vaga}}) | Parser | Média | - |
| 3.4 | Preview de template renderizado | Preview | Média | - |
| 3.5 | Configuração de assinatura padrão | Form | Baixa | signature |
| 3.6 | Upload de imagem na assinatura | Upload | Baixa | - |
| 3.7 | Configuração de horários LGPD | Form | Baixa | sending_hours |
| 3.8 | Fuso horário por tenant | Config | Baixa | - |
| 3.9 | CRUD Tipos de Alertas | CRUD | Média | alerts |
| 3.10 | Configuração de frequência | Form | Baixa | - |
| 3.11 | Canais de notificação (email, bell, Teams) | Multiselect | Média | notifications |
| 3.12 | Preview de alertas | Preview | Baixa | - |

#### 5.2.4 Metas & Planejamento (10 funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | Campos |
|---|---------------|------|--------------|--------|
| 4.1 | CRUD Metas individuais | CRUD | Média | goals |
| 4.2 | CRUD Metas de equipe | CRUD | Média | - |
| 4.3 | Atribuição de metas a usuários | Assign | Média | - |
| 4.4 | Períodos de meta (mensal, trimestral) | Config | Baixa | - |
| 4.5 | Tipos de KPI (vagas fechadas, SLA, etc) | Config | Média | kpis |
| 4.6 | Dashboard de progresso de metas | Charts | Alta | - |
| 4.7 | Comparativo meta vs realizado | Charts | Média | - |
| 4.8 | Workforce Planning (headcount anual) | Form complexo | Alta | workforce_plan |
| 4.9 | Calendário de contratações | Calendar | Alta | - |
| 4.10 | Alertas de metas em risco | Notif | Média | - |

#### 5.2.5 Busca Global (7 funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | Campos |
|---|---------------|------|--------------|--------|
| 5.1 | Configuração de limite por busca | Form | Baixa | search_limit |
| 5.2 | Limite por usuário/período | Form | Baixa | - |
| 5.3 | Toggle de opções de busca | Toggles | Baixa | search_options |
| 5.4 | Filtros padrão da empresa | Config | Média | - |
| 5.5 | Tabela de custos (créditos) | Display | Baixa | credit_costs |
| 5.6 | Histórico de consumo | Listagem | Média | - |
| 5.7 | Alertas de limite atingido | Notif | Média | - |

#### 5.2.6 Painel de Controle (6 funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | Campos |
|---|---------------|------|--------------|--------|
| 6.1 | CRUD Tarefas | CRUD | Média | tasks |
| 6.2 | Atribuição de tarefas | Assign | Média | - |
| 6.3 | Status de tarefas (Kanban) | UI | Alta | - |
| 6.4 | Histórico de atividades | Timeline | Média | activities |
| 6.5 | Filtros por usuário/período | Filtros | Baixa | - |
| 6.6 | Exportação de relatório | Export | Média | - |

### 5.3 Resumo: Menu Configurações

| Seção | Funcionalidades | Baixa | Média | Alta |
|-------|-----------------|-------|-------|------|
| Empresa & Equipe | 15 | 4 | 8 | 3 |
| Recrutamento | 8 | 2 | 6 | 0 |
| Comunicação & Alertas | 12 | 5 | 6 | 1 |
| Metas & Planejamento | 10 | 1 | 5 | 4 |
| Busca Global | 7 | 4 | 3 | 0 |
| Painel de Controle | 6 | 1 | 4 | 1 |
| **TOTAL** | **58** | **17** | **32** | **9** |

### 5.4 Componentes Existentes (Referência)

```
plataforma-lia/src/components/settings/
├── CompanyTeamHub.tsx      # Empresa & Equipe
├── RecruitmentHub.tsx      # Recrutamento  
├── CommunicationHub.tsx    # Comunicação
├── GoalsPlanningHub.tsx    # Metas & Planejamento
├── GlobalSearchHub.tsx     # Busca Global
├── ApprovalsHub.tsx        # Aprovações
├── BenefitsTab.tsx         # Benefícios
├── user-management.tsx     # Gestão de Usuários
├── goals-management.tsx    # Gestão de Metas
├── onboarding-wizard.tsx   # Assistente de Configuração
├── progress-dashboard.tsx  # Dashboard de Progresso
├── validation-system.tsx   # Sistema de Validação
├── BigFiveRadar.tsx        # Radar Big Five
├── CultureAnalyzer.tsx     # Analisador de Cultura
├── CultureProfilePreview.tsx # Preview de Cultura
├── SmartImportZone.tsx     # Importação Inteligente
└── RecruitmentJourneyConfig.tsx # Jornada de Recrutamento
```

---

## 6. Mapeamento: Gestão de Vagas

### 6.1 Estrutura Geral

Gestão de Vagas é composta por **5 módulos principais** com **83 funcionalidades**:

```
Gestão de Vagas/
├── 1. Wizard de Criação (9 etapas) - 35 funcionalidades
├── 2. Listagem e Gestão - 18 funcionalidades
├── 3. Kanban de Vagas - 10 funcionalidades
├── 4. Publicação e Sourcing - 12 funcionalidades
└── 5. Relatórios e Análise - 8 funcionalidades
```

### 6.2 Wizard de Criação (9 Etapas) - 35 Funcionalidades

#### Etapa 1: Descrição Inicial

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 1.1 | Input de descrição em linguagem natural | Form | Média | ✅ |
| 1.2 | Extração automática de critérios via IA | AI | Alta | ✅ |
| 1.3 | Upload de JD (PDF/DOCX) | Upload | Média | |
| 1.4 | Parsing de JD com IA | AI | Alta | ✅ |
| 1.5 | Preview de critérios extraídos | UI | Média | |
| 1.6 | Edição inline de critérios | Edit | Baixa | |

#### Etapa 2: Informações Básicas

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 2.1 | Título da vaga (com sugestões IA) | Input + AI | Média | ✅ |
| 2.2 | Seleção de departamento | Select | Baixa | |
| 2.3 | Seleção de senioridade | Select | Baixa | |
| 2.4 | Seleção de gestor (dropdown busca) | Search Select | Média | |
| 2.5 | Localização / Modelo de trabalho | Form | Baixa | |
| 2.6 | Verificação Workforce Planning | AI Check | Alta | ✅ |

#### Etapa 3: Remuneração

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 3.1 | Range salarial (min/max) | Slider | Baixa | |
| 3.2 | Seleção de moeda | Select | Baixa | |
| 3.3 | Configuração de bônus | Form | Média | |
| 3.4 | Seleção de benefícios (do Admin) | Multi-select | Média | |
| 3.5 | Benefícios por elegibilidade/senioridade | Regras | Média | |

#### Etapa 4: Competências Técnicas

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 4.1 | CRUD skills técnicas | CRUD | Média | |
| 4.2 | Nível por skill (básico/inter/avançado) | Select | Baixa | |
| 4.3 | Obrigatório vs desejável | Toggle | Baixa | |
| 4.4 | Sugestões de skills relacionadas (IA) | AI | Alta | ✅ |
| 4.5 | Tech stack da empresa (do Admin) | Multi-select | Média | |

#### Etapa 5: Competências WSI

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 5.1 | Seleção de competências comportamentais | Multi-select | Média | |
| 5.2 | Peso por competência (essencial/importante) | Select | Baixa | |
| 5.3 | Big Five ideal para o perfil (IA) | AI | Alta | ✅ |
| 5.4 | Radar de perfil comportamental | Chart | Alta | |

#### Etapa 6: Requisitos

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 6.1 | Idiomas e níveis | Multi-select | Média | |
| 6.2 | Formação acadêmica | Multi-select | Média | |
| 6.3 | Certificações | Tags | Média | |

#### Etapa 7: Scorecard/Perguntas

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 7.1 | CRUD perguntas de triagem | CRUD | Média | |
| 7.2 | Geração de perguntas WSI (IA) | AI | Alta | ✅ |
| 7.3 | Editor de peso/pontuação | Form | Média | |
| 7.4 | Preview do scorecard | Preview | Média | |

#### Etapa 8: Pipeline

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 8.1 | Seleção de etapas do processo | Multi-select | Média | |
| 8.2 | Ordenação de etapas (drag & drop) | DnD | Média | |
| 8.3 | Configuração por etapa (formato, duração) | Form | Média | |
| 8.4 | Entrevistadores por etapa | Assign | Média | |

#### Etapa 9: Revisão Final

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 9.1 | Resumo completo da vaga | Preview | Média | |
| 9.2 | Validação de campos obrigatórios | Validação | Baixa | |
| 9.3 | Feedback IA sobre a vaga (clusterização) | AI | Alta | ✅ |
| 9.4 | Publicação em canais | Actions | Média | |

### 6.3 Listagem e Gestão (18 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 2.1 | Listagem de vagas com filtros | Table | Média |
| 2.2 | Filtros por status (8+ status) | Filtros | Média |
| 2.3 | Filtros por departamento | Filtros | Baixa |
| 2.4 | Filtros por recrutador/gestor | Filtros | Média |
| 2.5 | Busca por título/ID | Search | Baixa |
| 2.6 | Ordenação multi-coluna | Sort | Média |
| 2.7 | Visualização lista vs cards | Toggle | Baixa |
| 2.8 | Ações em lote (status, recrutador) | Batch | Média |
| 2.9 | Edição rápida inline | Edit | Média |
| 2.10 | Duplicar vaga | Action | Média |
| 2.11 | Arquivar/cancelar vaga | Action | Baixa |
| 2.12 | Métricas por vaga (funil) | Display | Média |
| 2.13 | Indicadores de urgência | UI | Baixa |
| 2.14 | Tags customizáveis | Tags | Média |
| 2.15 | Exportação de vagas | Export | Média |
| 2.16 | Modal de detalhes da vaga | Modal | Média |
| 2.17 | Histórico de alterações | Timeline | Média |
| 2.18 | Compartilhamento de vaga | Share | Média |

### 6.4 Kanban de Vagas (10 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 3.1 | Board Kanban por status/etapa | UI | Alta |
| 3.2 | Drag & drop entre colunas | DnD | Alta |
| 3.3 | Cards com métricas resumidas | Cards | Média |
| 3.4 | Filtros no Kanban | Filtros | Média |
| 3.5 | Configuração de colunas visíveis | Config | Média |
| 3.6 | Ações rápidas no card | Actions | Média |
| 3.7 | Contador por coluna | Display | Baixa |
| 3.8 | Cores por prioridade | UI | Baixa |
| 3.9 | Limite WIP por coluna | Config | Média |
| 3.10 | Alerta de vagas paradas | Notif | Média |

### 6.5 Publicação e Sourcing (12 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 4.1 | Publicação multi-canal (LinkedIn, Indeed) | Integração | Alta | |
| 4.2 | Preview de publicação por canal | Preview | Média | |
| 4.3 | Agendamento de publicação | Scheduler | Média | |
| 4.4 | Busca local de candidatos | Search | Média | |
| 4.5 | Busca global Pearch | Integração | Alta | |
| 4.6 | Estimativa de créditos | Cálculo | Média | |
| 4.7 | Confirmação de créditos | Modal | Baixa | |
| 4.8 | Calibração de candidatos | AI | Alta | ✅ |
| 4.9 | Aprovação/rejeição rápida | Actions | Média | |
| 4.10 | Adicionar candidatos à vaga | Action | Média | |
| 4.11 | Notificação Teams de publicação | Notif | Média | |
| 4.12 | Métricas de sourcing | Dashboard | Média | |

### 6.6 Relatórios e Análise (8 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade | IA |
|---|---------------|------|--------------|-----|
| 5.1 | Relatório da vaga (PDF) | Export | Média | |
| 5.2 | Métricas de funil | Charts | Média | |
| 5.3 | Tempo médio por etapa | Analytics | Média | |
| 5.4 | Comparativo com vagas similares | AI | Alta | ✅ |
| 5.5 | Análise de mercado (salários) | AI | Alta | ✅ |
| 5.6 | Sugestões de melhoria da JD | AI | Alta | ✅ |
| 5.7 | NPS da vaga | Form | Baixa | |
| 5.8 | Histórico de contratações similares | Analytics | Média | |

### 6.7 Resumo: Gestão de Vagas

| Módulo | Funcionalidades | Com IA | Sem IA |
|--------|-----------------|--------|--------|
| Wizard de Criação (9 etapas) | 35 | 12 | 23 |
| Listagem e Gestão | 18 | 0 | 18 |
| Kanban | 10 | 0 | 10 |
| Publicação e Sourcing | 12 | 1 | 11 |
| Relatórios e Análise | 8 | 4 | 4 |
| **TOTAL** | **83** | **17** | **66** |

**Distribuição por Complexidade:**
- Baixa: 15 (18%)
- Média: 53 (64%)
- Alta: 15 (18%)

---

## 7. Mapeamento: Admin WeDo Talent (Multi-Tenant)

### 7.1 Estrutura Geral

O Admin WeDo Talent (área de superadmin) possui **5 módulos** com **48 funcionalidades**:

```
Admin WeDo Talent/
├── 1. Dashboard Admin - 8 funcionalidades
├── 2. Gestão de Clientes - 12 funcionalidades
├── 3. Consumo de IA - 10 funcionalidades
├── 4. Configurações Globais - 8 funcionalidades
└── 5. Compliance & Auditoria - 10 funcionalidades
```

### 7.2 Dashboard Admin (8 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 1.1 | Métricas consolidadas de clientes | Charts | Média |
| 1.2 | Cards de métricas (MRR, churn, etc) | Cards | Baixa |
| 1.3 | Filtro por período | Filtros | Baixa |
| 1.4 | Activity feed recente | Timeline | Média |
| 1.5 | Quick actions (criar cliente, etc) | Actions | Baixa |
| 1.6 | Alertas de sistema | Notif | Média |
| 1.7 | Consumo de serviços geral | Chart | Média |
| 1.8 | Status de integrações | Display | Baixa |

### 7.3 Gestão de Clientes (12 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 2.1 | Listagem de clientes | Table | Média |
| 2.2 | Filtros (status, plano, região) | Filtros | Média |
| 2.3 | CRUD Cliente | CRUD | Média |
| 2.4 | Card de cliente com métricas | Card | Média |
| 2.5 | Upload de logo do cliente | Upload | Baixa |
| 2.6 | Configuração de domínio | Form | Média |
| 2.7 | Gestão de plano/assinatura | Form | Média |
| 2.8 | Histórico de pagamentos | Listagem | Média |
| 2.9 | Gestão de limites (vagas, usuários) | Form | Média |
| 2.10 | Ativação/desativação de tenant | Toggle | Baixa |
| 2.11 | Impersonar cliente (login as) | Action | Alta |
| 2.12 | Exportação de clientes | Export | Baixa |

### 7.4 Consumo de IA (10 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 3.1 | Dashboard de consumo geral | Charts | Média |
| 3.2 | Consumo por agente | Breakdown | Média |
| 3.3 | Consumo por cliente | Breakdown | Média |
| 3.4 | Gráfico de tendência | Chart | Média |
| 3.5 | Alertas de consumo alto | Notif | Média |
| 3.6 | Limites por cliente | Config | Média |
| 3.7 | Histórico de consumo | Table | Média |
| 3.8 | Exportação de relatório | Export | Baixa |
| 3.9 | Detalhamento por operação | Drill-down | Média |
| 3.10 | Projeção de consumo | Analytics | Alta |

### 7.5 Configurações Globais (8 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 4.1 | Templates padrão (herança) | CRUD | Média |
| 4.2 | Políticas globais | Form | Média |
| 4.3 | Integrações globais (Pearch, APIs) | Config | Alta |
| 4.4 | Configuração de créditos | Form | Média |
| 4.5 | Regras de compliance | Form | Média |
| 4.6 | Feature flags | Toggles | Média |
| 4.7 | Manutenção de sistema | Actions | Alta |
| 4.8 | Logs de sistema | Listagem | Média |

### 7.6 Compliance & Auditoria (10 Funcionalidades)

| # | Funcionalidade | Tipo | Complexidade |
|---|---------------|------|--------------|
| 5.1 | Audit log global | Table | Média |
| 5.2 | Filtros por ação/usuário/cliente | Filtros | Média |
| 5.3 | Exportação de logs | Export | Média |
| 5.4 | Dashboard LGPD | Charts | Média |
| 5.5 | Solicitações de titulares | Listagem | Média |
| 5.6 | Relatório de compliance | Export | Alta |
| 5.7 | Controles SOX | Checklist | Alta |
| 5.8 | Bias audit dashboard | Charts | Alta |
| 5.9 | Trust Center público | Page | Alta |
| 5.10 | Gestão de subprocessadores | CRUD | Média |

### 7.7 Resumo: Admin WeDo Talent

| Módulo | Funcionalidades | Baixa | Média | Alta |
|--------|-----------------|-------|-------|------|
| Dashboard Admin | 8 | 3 | 5 | 0 |
| Gestão de Clientes | 12 | 3 | 8 | 1 |
| Consumo de IA | 10 | 1 | 8 | 1 |
| Configurações Globais | 8 | 0 | 5 | 3 |
| Compliance & Auditoria | 10 | 0 | 5 | 5 |
| **TOTAL** | **48** | **7** | **31** | **10** |

### 7.8 Componentes Existentes (Referência)

```
plataforma-lia/src/components/admin/
├── ai-consumption/
│   ├── AgentBreakdown.tsx
│   ├── ConsumptionChart.tsx
│   ├── ConsumptionGrid.tsx
│   ├── ConsumptionSummaryCard.tsx
│   └── index.ts
├── clients/
│   ├── ClientCard.tsx
│   ├── ClientFilters.tsx
│   ├── ClientTable.tsx
│   ├── CreateClientDialog.tsx
│   ├── index.ts
│   └── types.ts
├── dashboard/
│   ├── ActivityFeed.tsx
│   ├── index.ts
│   ├── MetricCard.tsx
│   ├── PeriodFilter.tsx
│   ├── QuickActions.tsx
│   └── ServiceConsumption.tsx
├── Breadcrumbs.tsx
├── ClientSelector.tsx
└── index.ts
```

---

## 8. Análise WorkOS: Funcionalidades Substituíveis

### 8.1 Funcionalidades WorkOS Disponíveis

| Feature WorkOS | Descrição | Preço Estimado |
|----------------|-----------|----------------|
| **SSO** | Login único via Okta, Entra, Google Workspace | $125/conexão/mês |
| **Directory Sync (SCIM)** | Provisioning/deprovisioning automático de usuários | $125/conexão/mês |
| **Admin Portal** | UI white-label para cliente configurar SSO/SCIM sozinho | Incluso |
| **MFA/AuthKit** | Autenticação multi-fator, passkeys | Incluso |
| **Audit Logs** | Logs de segurança/compliance | Incluso |
| **RBAC/FGA** | Roles e permissões fine-grained | Incluso |
| **Domain Verification** | Verificação de domínio via DNS/email | Incluso |

### 8.2 Mapeamento: Funcionalidades Eliminadas com WorkOS

#### 8.2.1 No Menu Configurações (Admin Cliente)

| # | Funcionalidade Atual | WorkOS Substitui | Economia Dev |
|---|---------------------|------------------|--------------|
| 1.7 | CRUD Usuários/Recrutadores | ✅ Directory Sync | Alta |
| 1.8 | Convite de novos usuários | ✅ SSO + SCIM | Alta |
| 1.9 | Gestão de Roles | ✅ RBAC | Alta |
| 1.10 | Matriz de Permissões | ✅ FGA | Alta |
| - | Login/Autenticação | ✅ SSO | Alta |
| - | MFA | ✅ AuthKit | Alta |

**Total eliminado no Configurações: 6 funcionalidades**

#### 8.2.2 No Admin WeDo Talent

| # | Funcionalidade Atual | WorkOS Substitui | Economia Dev |
|---|---------------------|------------------|--------------|
| 2.10 | Ativação/desativação tenant | ✅ SCIM lifecycle | Média |
| 2.11 | Impersonar cliente | ✅ Admin Portal | Média |
| 4.2 | Políticas globais (auth) | ⚠️ Parcial | Média |
| 5.1 | Audit log global | ✅ Audit Logs | Alta |
| 5.2 | Filtros por ação/usuário | ✅ Audit Logs | Média |
| 5.3 | Exportação de logs | ✅ Audit Logs | Média |
| - | Gestão multi-tenant auth | ✅ Organizations | Alta |

**Total eliminado no Admin WeDo: 10 funcionalidades**

### 8.3 Funcionalidades que MANTEMOS (Não Substituíveis)

| Categoria | Funcionalidade | Por quê manter? |
|-----------|---------------|-----------------|
| **Negócio RH** | Dados da Empresa | Dados específicos (CNPJ, logo) |
| **Negócio RH** | Departamentos/Hierarquia | Estrutura organizacional custom |
| **Negócio RH** | Benefícios | Lógica de elegibilidade RH |
| **Negócio RH** | Fluxo de Aprovação | Workflow específico de vagas |
| **Comunicação** | Templates de email | Conteúdo de negócio |
| **Planejamento** | Metas & KPIs | Métricas de recrutamento |
| **Integração** | Busca Global (Pearch) | Integração proprietária |
| **Billing** | Consumo de IA | Métricas específicas |
| **Billing** | Configuração de créditos | Modelo de negócio custom |
| **Compliance** | LGPD específico BR | Regulação brasileira |
| **Compliance** | BCB 498, SOX | Frameworks específicos |

### 8.4 Impacto Quantitativo

#### Antes (sem WorkOS)

| Área | Funcionalidades |
|------|-----------------|
| Configurações (Cliente) | 58 |
| Admin WeDo Talent | 48 |
| **TOTAL auth-related** | **106** |

#### Depois (com WorkOS)

| Área | Original | Removido | Restante |
|------|----------|----------|----------|
| Configurações (Cliente) | 58 | 6 | 52 |
| Admin WeDo Talent | 48 | 10 | 38 |
| **TOTAL** | **106** | **16** | **90** |

**Redução: 16 funcionalidades (15%)**

### 8.5 Benefícios Adicionais WorkOS

| Benefício | Impacto |
|-----------|---------|
| **Tempo de desenvolvimento** | -4 a 6 semanas (auth/permissions) |
| **Manutenção** | Zero para SSO/SCIM |
| **Segurança** | Enterprise-grade out-of-box |
| **Onboarding clientes** | Self-service via Admin Portal |
| **Compliance** | SOC 2, ISO 27001 já incluso |
| **Suporte** | Direto com WorkOS engineers |
| **Time to Market** | Acelera lançamento enterprise |

### 8.6 Custo vs Benefício

| Item | Valor |
|------|-------|
| **Custo WorkOS** | ~$250/cliente/mês (SSO + SCIM) |
| **Economia desenvolvimento** | ~4-6 semanas = R$ 30-50k |
| **Economia manutenção/ano** | ~R$ 20-30k |
| **Break-even** | ~10-15 clientes enterprise |

### 8.7 Recomendação

| Decisão | Recomendação |
|---------|--------------|
| **Usar WorkOS para** | SSO, SCIM, Roles, Permissions, Audit Logs, MFA |
| **Manter interno** | Dados de negócio RH, Workflows, Integrações específicas |
| **Prioridade** | Integrar WorkOS antes de desenvolver auth/permissions |
| **Timeline** | Fase 1 (Setup) - 1-2 semanas de integração |

---

## 9. Comparativo Final e Recomendações

### 9.1 Comparativo Geral de Funcionalidades

| Módulo | Funcionalidades | Com IA | Complexidade Alta | Prioridade |
|--------|-----------------|--------|-------------------|------------|
| **Configurações (Admin Cliente)** | 58 → 52* | 0 | 9 (16%) | P0 |
| **Admin WeDo Talent** | 48 → 38* | 0 | 10 (21%) | P1 |
| **Gestão de Vagas** | 83 | 17 (20%) | 15 (18%) | P2 |
| **TOTAL** | **189 → 173*** | **17** | **34** | - |

*Com WorkOS integrado

### 9.2 Distribuição de Trabalho

| Responsável | Módulos | Funcionalidades | % Total |
|-------------|---------|-----------------|---------|
| **Freelancer Vue.js** | Configurações + Admin UI | ~70 | 40% |
| **Time Interno (Backend)** | APIs + Integrações | ~40 | 23% |
| **Time Interno (IA)** | Serviços IA Vagas | ~17 | 10% |
| **Time Interno (Frontend)** | Vagas complexas | ~30 | 17% |
| **WorkOS** | Auth/Permissions | ~16 | 9% |

### 9.3 Timeline Consolidado

```
         Mês 1          Mês 2          Mês 3          Mês 4          Mês 5
    ┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
    │   FASE 1     │   FASE 2     │   FASE 3     │   FASE 4     │   FASE 5     │
    │ Setup+WorkOS │Config Completo│ Vagas UI    │ Vagas IA     │ Integração   │
    ├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
    │ Backend APIs │ Freelancer   │ Freelancer   │ Interno      │ Todos        │
    │ WorkOS Auth  │ Vue.js       │ + Interno    │ IA Core      │ E2E Tests    │
    │ Design System│ Admin UI     │ Wizard UI    │ Agentes      │ Polish       │
    └──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
    
    Funcionalidades: 20        52            40            17            Testes
    Pessoas:         2-3       Freelancer    3-4           2-3           Todos
```

### 9.4 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Atraso APIs backend | Média | Alto | Definir contratos API-first antes |
| Freelancer não entrega | Baixa | Alto | Milestone payments, código review semanal |
| Complexidade IA subestimada | Média | Médio | POCs antes de commits |
| Integração WorkOS problemática | Baixa | Médio | Sandbox testing primeiro |
| Dependências entre módulos | Média | Médio | Grafo de dependências atualizado |

### 9.5 Métricas de Sucesso

| Fase | Métrica | Target |
|------|---------|--------|
| Fase 1 | APIs base funcionando + WorkOS integrado | 100% |
| Fase 2 | Configurações 100% funcional | 52 funcionalidades |
| Fase 3 | Wizard de Vagas sem IA funcionando | 35 funcionalidades |
| Fase 4 | Wizard com IA completo | 17 funcionalidades IA |
| Fase 5 | Testes E2E passando, bugs críticos = 0 | 100% coverage crítico |

### 9.6 Próximos Passos Imediatos

1. **Semana 1**: Definir contratos de API para Admin/Configurações
2. **Semana 1**: Iniciar integração WorkOS (SSO + SCIM)
3. **Semana 2**: Setup projeto Vue.js/Nuxt + Design System Vuetify
4. **Semana 2**: Onboarding do freelancer com documentação
5. **Semana 3**: Primeiras entregas do freelancer (Shell + Navigation)
6. **Semana 3**: APIs Usuários/Roles prontas para consumo

---

## Anexo A: Checklist de Onboarding Freelancer

### A.1 Documentação Necessária

- [ ] Este documento (ROADMAP-DESENVOLVIMENTO-COMPLETO.md)
- [ ] Design System Tokens (cores, tipografia, componentes)
- [ ] Contratos de API (OpenAPI/Swagger)
- [ ] Figma/Mockups das telas
- [ ] Guia de estilo de código Vue.js
- [ ] Acesso ao repositório

### A.2 Setup Técnico

- [ ] Repositório Vue.js/Nuxt criado
- [ ] Vuetify configurado com tema WeDo
- [ ] ESLint/Prettier configurados
- [ ] CI/CD básico funcionando
- [ ] Ambiente de desenvolvimento pronto
- [ ] Mock server para APIs

### A.3 Primeiras Entregas Esperadas

| Semana | Entrega | Critério de Aceite |
|--------|---------|-------------------|
| 1 | Shell + Navigation | Layout responsivo, sidebar funcional |
| 2 | Dashboard + Usuários | CRUD completo com paginação |
| 3 | Permissões + Departamentos | Matriz visual, hierarquia |
| 4 | Benefícios + Templates | Editor rich text funcionando |

---

## Anexo B: Glossário

| Termo | Definição |
|-------|-----------|
| **Admin Cliente** | Menu Configurações dentro do tenant do cliente |
| **Admin WeDo Talent** | Área de superadmin multi-tenant |
| **Configurações** | Sinônimo de Admin Cliente |
| **Freelancer** | Desenvolvedor frontend Vue.js terceirizado |
| **Funil de Talentos** | Módulo de busca e gestão de candidatos |
| **Gestão de Vagas** | Módulo de criação e gestão de vagas |
| **Pearch** | API externa de banco de candidatos (40M+) |
| **Tenant** | Cliente/empresa na plataforma multi-tenant |
| **WorkOS** | Plataforma de auth enterprise (SSO, SCIM) |
| **WSI** | Work Sample Interview - metodologia de triagem |
| **Wizard** | Fluxo guiado de criação de vagas (9 etapas) |

---

## Anexo C: Pendências e Ajustes Futuros

### C.1 Interview Notes / Score Card WSI

| Data | Pendência | Status | Descrição |
|------|-----------|--------|-----------|
| 15/01/2026 | **Pilares Perguntas Contextuais** | 🔴 Pendente | Definir pilares/categorias para as perguntas genéricas do Bloco 4 (Contextuais) do Score Card. Perguntas geradas pela LIA com base em CV, vaga e triagens para avaliar pontos fora do contexto das competências técnicas/comportamentais. |

### C.2 Estrutura Score Card WSI (Aprovada)

**4 Blocos de Perguntas:**
- Bloco 1: Competências Técnicas (Peso: 50%)
- Bloco 2: Competências Comportamentais (Peso: 20%)
- Bloco 3: Gap Analysis (Peso: 15%)
- Bloco 4: Contextuais/Genéricas (Peso: 15%) - *Pilares pendentes*

**Faixas de Decisão:**
- WSI ≥ 4.2: Aprovado Automático
- WSI 3.8-4.1: Revisão Humana
- WSI < 3.8: Reprovado

---

*Documento gerado em Dezembro 2024*
*WeDo Talent - Plataforma de Recrutamento com Agentes de IA*
