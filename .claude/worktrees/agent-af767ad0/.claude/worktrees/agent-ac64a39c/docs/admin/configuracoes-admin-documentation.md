# DOCUMENTACAO COMPLETA - CONFIGURACOES ADMIN WEDOTALENT

> **Versao:** 1.0  
> **Data:** Dezembro 2024  
> **Plataforma:** LIA - Learning Intelligence Assistant  
> **Stack Prototipo:** React/Next.js + Tailwind CSS + FastAPI  
> **Stack Producao:** Ruby on Rails + Vue.js/Nuxt + Vuetify

---

## INDICE

1. [Visao Geral do Modulo](#1-visao-geral-do-modulo)
2. [Arquitetura de Paginas](#2-arquitetura-de-paginas)
3. [Documentacao por Secao/Hub](#3-documentacao-por-secaohub)
4. [Cards de Especificacao (Jira)](#4-cards-de-especificacao-jira)
5. [Diagramas de Jornada](#5-diagramas-de-jornada)
6. [Roadmap por Fases](#6-roadmap-por-fases)
7. [Padroes de Design](#7-padroes-de-design)
8. [APIs e Integracao Backend](#8-apis-e-integracao-backend)
9. [Requisitos Funcionais](#9-requisitos-funcionais)
10. [Lista de Tasks Importavel](#10-lista-de-tasks-importavel)

---

## 1. VISAO GERAL DO MODULO

### 1.1 Nome do Modulo
**Configuracoes Admin WeDo Talent** (Settings Admin / Onboarding Configuration Hub)

### 1.2 Objetivo Principal
Centralizar todas as configuracoes administrativas da plataforma, incluindo dados da empresa, equipe, pipeline de recrutamento, comunicacao, metas e busca global. E o hub de setup inicial (onboarding) e manutencao continua das configuracoes organizacionais.

### 1.3 Posicao na Jornada do Usuario
```
Login -> Dashboard -> MENU CONFIGURACOES (Sidebar)
                           |
                           +-> Empresa & Equipe
                           |   +-> Dados da Empresa
                           |   +-> Departamentos
                           |   +-> Beneficios
                           |   +-> Usuarios
                           |   +-> Aprovadores
                           |
                           +-> Recrutamento
                           |   +-> Pipeline (etapas)
                           |   +-> Perguntas Screening
                           |
                           +-> Comunicacao & Alertas
                           |   +-> Templates Email
                           |   +-> Assinatura
                           |   +-> Horarios LGPD
                           |   +-> Alertas
                           |
                           +-> Metas & Planejamento
                           |   +-> Metas Individuais
                           |   +-> Workforce Planning
                           |
                           +-> Busca Global
                           |   +-> Limites
                           |   +-> Opcoes
                           |   +-> Custos/Creditos
                           |
                           +-> Painel de Controle ⚠️
                               +-> Tarefas
                               +-> Atividades

> ⚠️ **ATENÇÃO - SEÇÃO FUTURA:** O item "Painel de Controle" é uma seção futura do MENU PRINCIPAL e foi movida temporariamente para cá apenas para facilitar sua realocação posterior. **NÃO DEVE FAZER PARTE DO PLANEJAMENTO DE DESENVOLVIMENTO DO MENU CONFIGURAÇÕES.**
```

### 1.4 Duas Versoes de Interface

O modulo possui **duas implementacoes paralelas**:

| Versao | Arquivo | Descricao | Status |
|--------|---------|-----------|--------|
| **Enhanced (Principal)** | `settings-page-enhanced.tsx` | Nova UI com sidebar colapsavel, progress dashboard, onboarding wizard | Ativo |
| **Legacy** | `settings-page.tsx` | UI original com tabs verticais, categorias expandidas | Legado |

**Recomendacao:** Desenvolver novas features na versao Enhanced, manter Legacy para compatibilidade.

### 1.5 Dependencias do Modulo

**Modulos que este depende:**
- Sistema de Autenticacao (usuarios, roles)
- API Backend FastAPI (todas as operacoes CRUD)
- Sistema de Armazenamento (logos, arquivos)
- Integracao com ATS externos (opcional)

**Modulos que dependem deste:**
- Criacao de Vagas (usa pipeline, templates)
- Funil de Talentos (usa busca global, creditos)
- Comunicacao com Candidatos (usa templates, LGPD)
- Dashboard (usa metas, KPIs)
- Sistema de Aprovacoes (usa aprovadores)

### 1.6 Status de Definicao

**Claramente Definido:**
- 5 secoes principais (Hubs) + 1 seção futura (Painel de Controle - não incluída no escopo)
- Subsecoes com campos especificos
- Onboarding Wizard com templates
- Progress Dashboard com metricas
- Sidebar colapsavel com lock
- APIs de persistencia no backend

**Em Aberto / Mal Definido:**
- Validacao avancada de campos
- Sincronizacao com ATS externos
- Historico de alteracoes (audit log)
- Permissoes granulares por campo
- Modo multi-tenant completo

---

## 2. ARQUITETURA DE PAGINAS

### 2.1 Estrutura de Componentes

```
CONFIGURACOES (settings-page-enhanced.tsx)
|
+-- SIDEBAR COLAPSAVEL
|   +-- Header (icone, titulo, lock button)
|   +-- Progress Bar (geral)
|   +-- Botao Assistente de Configuracao
|   +-- Menu de Secoes (6 items)
|       +-- Cada secao com icone, titulo, badge de completude
|       +-- Subsecoes expandiveis
|
+-- AREA DE CONTEUDO
|   +-- Header dinamico (titulo, descricao, acoes)
|   +-- Renderizacao condicional por secao:
|       +-- company-team -> CompanyTeamHub
|       +-- recruitment -> RecruitmentHub
|       +-- communication -> CommunicationHub
|       +-- goals-planning -> GoalsPlanningHub
|       +-- global-search -> GlobalSearchHub
|       +-- control-panel -> TasksPage
|
+-- MODAIS:
    +-- OnboardingWizard (setup inicial)
    +-- ProgressDashboard (metricas detalhadas)
```

### 2.2 Arquivos de Componentes

```
plataforma-lia/src/components/
├── pages/
│   ├── settings-page-enhanced.tsx  # Pagina principal (nova)
│   └── settings-page.tsx           # Pagina legado
│
├── settings/
│   ├── CompanyTeamHub.tsx          # Hub Empresa & Equipe (~3200 linhas)
│   ├── RecruitmentHub.tsx          # Hub Recrutamento (~660 linhas)
│   ├── CommunicationHub.tsx        # Hub Comunicacao
│   ├── GoalsPlanningHub.tsx        # Hub Metas & Planejamento
│   ├── GlobalSearchHub.tsx         # Hub Busca Global
│   ├── onboarding-wizard.tsx       # Wizard de configuracao inicial
│   ├── progress-dashboard.tsx      # Dashboard de progresso
│   ├── user-management.tsx         # Gestao de usuarios
│   ├── BenefitsTab.tsx             # Tab de beneficios
│   ├── ApprovalsHub.tsx            # Hub de aprovadores
│   ├── goals-management.tsx        # Gestao de metas
│   ├── validation-system.tsx       # Sistema de validacao
│   ├── RecruitmentJourneyConfig.tsx # Configuracao do pipeline
│   ├── SmartImportZone.tsx         # Importacao inteligente
│   ├── BigFiveRadar.tsx            # Grafico Big Five cultura
│   └── CultureProfilePreview.tsx   # Preview perfil cultural
```

---

## 3. DOCUMENTACAO POR SECAO/HUB

---

### 3.1 HUB: EMPRESA & EQUIPE (company-team)

#### 3.1.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Empresa & Equipe |
| **Objetivo** | Configurar dados institucionais, departamentos, beneficios, usuarios e aprovadores |
| **Componente** | `CompanyTeamHub.tsx` |
| **Prioridade** | Alta (primeira secao do onboarding) |
| **Tempo Estimado** | 15 minutos |

#### 3.1.2 Subsecoes

| ID | Subsecao | Descricao | Campos |
|----|----------|-----------|--------|
| company-data | Dados da Empresa | Informacoes institucionais | company_name, cnpj, website, email, phone, logo |
| departments | Departamentos | Estrutura organizacional | departments[], hierarchy |
| benefits | Beneficios | Pacote de beneficios | benefits[], eligibility |
| users | Usuarios | Recrutadores e times | users[], roles, permissions |
| approvers | Aprovadores | Fluxo de aprovacao | approval_flow, approvers[] |

#### 3.1.3 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| EMP-001 | Editar dados basicos | Nome, CNPJ, site, contatos |
| EMP-002 | Upload de logo | Imagem da empresa |
| EMP-003 | Definir industria | Selecao de setor e categoria |
| EMP-004 | Configurar tamanho | Porte da empresa |
| EMP-005 | Missao, Visao, Valores | EVP da empresa |
| EMP-006 | Tech Stack | Tecnologias utilizadas |
| EMP-007 | Perfil Big Five | Cultura organizacional |
| EMP-008 | CRUD Departamentos | Criar, editar, excluir departamentos |
| EMP-009 | Gerenciar membros | Adicionar pessoas aos departamentos |
| EMP-010 | CRUD Beneficios | Gerenciar pacote de beneficios |
| EMP-011 | Elegibilidade | Definir quem recebe cada beneficio |
| EMP-012 | CRUD Usuarios | Convidar, editar, desativar usuarios |
| EMP-013 | Atribuir roles | Admin, Recrutador, Gestor, Visualizador |
| EMP-014 | Definir permissoes | Acesso granular por modulo |
| EMP-015 | CRUD Aprovadores | Configurar fluxo de aprovacao |
| EMP-016 | Niveis de aprovacao | Hierarquia de aprovadores |
| EMP-017 | Smart Import | Importacao inteligente de dados |

---

#### EMP-001: Editar Dados Basicos da Empresa

**Historia de Usuario:**
> "Como administrador, eu quero editar os dados institucionais da empresa para manter as informacoes atualizadas e exibi-las nas vagas."

**Regras de Negocio:**
1. Nome da empresa e obrigatorio
2. CNPJ deve ser valido (14 digitos, formatacao automatica)
3. Email deve ser corporativo (validacao de dominio opcional)
4. Website deve ser URL valida
5. Alteracoes sao persistidas automaticamente (autosave)
6. Logo aceita PNG, JPG ate 2MB

**Campos:**
```typescript
interface CompanyData {
  name: string           // obrigatorio, max 200
  tradeName: string      // nome fantasia
  cnpj: string          // formato XX.XXX.XXX/XXXX-XX
  website: string       // URL
  email: string         // email corporativo
  phone: string         // telefone principal
  address: string       // endereco sede
  logo?: string         // URL da imagem
  industry: string      // setor/industria
  size: string          // porte (startup, PME, enterprise)
  employee_count?: number
  founded_year?: number
  linkedin_url?: string
  work_model?: string   // remoto, hibrido, presencial
}
```

**Inputs:**
- Formulario com campos editaveis
- Upload de imagem para logo

**Outputs:**
- `CompanyData` atualizado
- Toast de confirmacao

**Validacoes:**
- CNPJ: algoritmo de validacao brasileiro
- Email: regex padrao + verificacao de dominio
- Website: URL valida com protocolo
- Telefone: formato brasileiro

---

#### EMP-008: CRUD Departamentos

**Historia de Usuario:**
> "Como administrador, eu quero criar e gerenciar departamentos para organizar a estrutura da empresa."

**Regras de Negocio:**
1. Nome do departamento e obrigatorio e unico
2. Cada departamento pode ter um gestor
3. Cor e selecionavel para identificacao visual
4. Departamentos podem ter membros vinculados
5. Excluir departamento nao exclui os membros

**Dados:**
```typescript
interface Department {
  id: string
  name: string          // obrigatorio
  description: string
  manager?: string      // nome do gestor
  manager_title?: string
  manager_email?: string
  manager_phone?: string
  headcount: number     // quantidade de pessoas
  color: string         // cor hex
  members?: DepartmentMember[]
}

interface DepartmentMember {
  id: string
  name: string
  title?: string
  email?: string
  phone?: string
  linkedin_url?: string
  level: string         // junior, pleno, senior, etc
  is_active: boolean
}
```

**APIs:**
```
GET    /api/backend-proxy/departments
POST   /api/backend-proxy/departments
PUT    /api/backend-proxy/departments/{id}
DELETE /api/backend-proxy/departments/{id}
```

---

#### EMP-012: CRUD Usuarios

**Historia de Usuario:**
> "Como administrador, eu quero convidar e gerenciar usuarios para controlar quem acessa a plataforma."

**Regras de Negocio:**
1. Email e obrigatorio e unico
2. Roles disponiveis: Admin, Recrutador, Gestor, Visualizador
3. Convite enviado por email com link de ativacao
4. Usuario desativado nao pode fazer login
5. Admin nao pode se auto-desativar

**Roles e Permissoes:**
```typescript
const ROLES = {
  admin: {
    name: 'Administrador',
    permissions: ['*'] // acesso total
  },
  recruiter: {
    name: 'Recrutador',
    permissions: ['candidates:*', 'jobs:*', 'reports:read']
  },
  manager: {
    name: 'Gestor',
    permissions: ['candidates:read', 'jobs:read', 'approvals:*']
  },
  viewer: {
    name: 'Visualizador',
    permissions: ['candidates:read', 'jobs:read']
  }
}
```

**APIs:**
```
GET    /api/backend-proxy/users
POST   /api/backend-proxy/users/invite
PUT    /api/backend-proxy/users/{id}
DELETE /api/backend-proxy/users/{id}
POST   /api/backend-proxy/users/{id}/deactivate
POST   /api/backend-proxy/users/{id}/reactivate
```

---

### 3.2 HUB: RECRUTAMENTO (recruitment)

#### 3.2.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Recrutamento |
| **Objetivo** | Configurar pipeline e perguntas de screening |
| **Componente** | `RecruitmentHub.tsx` |
| **Prioridade** | Alta (define fluxo de recrutamento) |
| **Tempo Estimado** | 20 minutos |
| **Dependencias** | company-team (precisa existir empresa) |

#### 3.2.2 Subsecoes

| ID | Subsecao | Descricao | Campos |
|----|----------|-----------|--------|
| pipeline | Pipeline | Etapas do processo seletivo | stages[], flow |
| screening | Perguntas Screening | Perguntas iniciais WhatsApp | screening_questions[] |

#### 3.2.3 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| REC-001 | Visualizar pipeline | Ver etapas configuradas |
| REC-002 | Editar pipeline | Modificar etapas (CS only) |
| REC-003 | Reordenar etapas | Drag and drop |
| REC-004 | CRUD perguntas screening | Gerenciar perguntas iniciais |
| REC-005 | Tipos de pergunta | Texto, Sim/Nao, Escala, Multipla |
| REC-006 | Perguntas obrigatorias | Marcar como required |
| REC-007 | Reordenar perguntas | Drag and drop |
| REC-008 | Perguntas default | Restaurar perguntas padrao |

---

#### REC-001: Visualizar Pipeline

**Historia de Usuario:**
> "Como recrutador, eu quero visualizar as etapas do pipeline para entender o fluxo de recrutamento da empresa."

**Regras de Negocio:**
1. Pipeline e configurado pelo Customer Success (CS)
2. Usuario comum visualiza em modo read-only
3. Cada etapa tem nome, cor e descricao
4. Etapas sao ordenadas sequencialmente

**Dados:**
```typescript
interface RecruitmentStage {
  id: string
  name: string          // ex: "Triagem", "Entrevista RH"
  description: string
  color: string         // hex
  order: number
  isActive: boolean
  type: 'screening' | 'interview' | 'test' | 'offer' | 'hired'
}

const DEFAULT_STAGES: RecruitmentStage[] = [
  { id: '1', name: 'Triagem', order: 1, type: 'screening' },
  { id: '2', name: 'Entrevista RH', order: 2, type: 'interview' },
  { id: '3', name: 'Teste Tecnico', order: 3, type: 'test' },
  { id: '4', name: 'Entrevista Gestor', order: 4, type: 'interview' },
  { id: '5', name: 'Proposta', order: 5, type: 'offer' },
  { id: '6', name: 'Contratado', order: 6, type: 'hired' }
]
```

---

#### REC-004: CRUD Perguntas Screening

**Historia de Usuario:**
> "Como recrutador, eu quero configurar perguntas de screening para qualificar candidatos via WhatsApp."

**Regras de Negocio:**
1. Perguntas default vem pre-configuradas
2. Usuario pode adicionar perguntas customizadas
3. Perguntas podem ser obrigatorias ou opcionais
4. Tipos: texto livre, sim/nao, escala 1-5, multipla escolha
5. Limite de 10 perguntas ativas

**Dados:**
```typescript
interface ScreeningQuestion {
  id: string
  question: string
  type: 'text' | 'yesno' | 'scale' | 'multiple'
  required: boolean
  order: number
  isDefault: boolean    // se e pergunta padrao do sistema
  options?: string[]    // para multipla escolha
}

const defaultQuestions: ScreeningQuestion[] = [
  { id: '1', question: 'Voce tem interesse real nesta vaga?', type: 'yesno', required: true },
  { id: '2', question: 'Qual sua disponibilidade para inicio?', type: 'text', required: true },
  { id: '3', question: 'Qual sua pretensao salarial?', type: 'text', required: true },
  { id: '4', question: 'Quantos anos de experiencia voce tem na area?', type: 'text', required: true },
  { id: '5', question: 'Voce aceita trabalhar no modelo hibrido/presencial?', type: 'yesno', required: true },
  { id: '6', question: 'Voce esta em algum outro processo seletivo?', type: 'yesno', required: false }
]
```

**APIs:**
```
GET    /api/backend-proxy/screening-questions
PUT    /api/backend-proxy/screening-questions
POST   /api/backend-proxy/screening-questions
DELETE /api/backend-proxy/screening-questions/{id}
```

---

### 3.3 HUB: COMUNICACAO & ALERTAS (communication)

#### 3.3.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Comunicacao & Alertas |
| **Objetivo** | Gerenciar templates de email, assinatura, horarios LGPD e alertas |
| **Componente** | `CommunicationHub.tsx` |
| **Prioridade** | Media |
| **Tempo Estimado** | 15 minutos |
| **Dependencias** | company-team |

#### 3.3.2 Subsecoes

| ID | Subsecao | Descricao | Campos |
|----|----------|-----------|--------|
| templates | Templates | Modelos de email | email_templates[] |
| signature | Assinatura | Assinatura padrao | signature_html |
| schedule | Horarios LGPD | Janela de envio | sending_hours |
| alerts | Alertas | Notificacoes LIA | alerts_config |

#### 3.3.3 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| COM-001 | Listar templates | Ver templates disponiveis |
| COM-002 | Criar template | Novo template de email |
| COM-003 | Editar template | Modificar template existente |
| COM-004 | Duplicar template | Copiar template |
| COM-005 | Excluir template | Remover template |
| COM-006 | Variaveis dinamicas | Usar {{nome}}, {{cargo}}, etc |
| COM-007 | Preview template | Ver como ficara o email |
| COM-008 | Editar assinatura | Configurar assinatura padrao |
| COM-009 | Horarios LGPD | Definir janela 8h-20h |
| COM-010 | Configurar alertas | Notificacoes e briefings LIA |

---

### 3.4 HUB: METAS & PLANEJAMENTO (goals-planning)

#### 3.4.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Metas & Planejamento |
| **Objetivo** | Definir metas individuais, de equipe e workforce planning |
| **Componente** | `GoalsPlanningHub.tsx` |
| **Prioridade** | Media |
| **Tempo Estimado** | 25 minutos |
| **Dependencias** | recruitment (precisa pipeline definido) |

#### 3.4.2 Subsecoes

| ID | Subsecao | Descricao | Campos |
|----|----------|-----------|--------|
| goals | Metas | Metas individuais e de equipe | goals[], kpis[] |
| workforce | Workforce Planning | Planejamento anual | workforce_plan |

#### 3.4.3 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| MET-001 | Definir metas individuais | Meta por recrutador |
| MET-002 | Definir metas de equipe | Meta agregada |
| MET-003 | KPIs de recrutamento | Time to hire, custo, qualidade |
| MET-004 | Periodos | Mensal, trimestral, anual |
| MET-005 | Acompanhamento | Dashboard de progresso |
| MET-006 | Workforce planning | Previsao de demanda |
| MET-007 | Headcount planning | Planejamento de vagas |

---

### 3.5 HUB: BUSCA GLOBAL (global-search)

#### 3.5.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Busca Global |
| **Objetivo** | Configurar limites, opcoes e custos da busca Pearch |
| **Componente** | `GlobalSearchHub.tsx` |
| **Prioridade** | Media |
| **Tempo Estimado** | 5 minutos |

#### 3.5.2 Subsecoes

| ID | Subsecao | Descricao | Campos |
|----|----------|-----------|--------|
| limits | Limites | Limite de candidatos por busca | search_limit |
| options | Opcoes | Configuracoes de busca | search_options |
| costs | Custos | Tabela de creditos | credit_costs |

#### 3.5.3 Lista de Funcionalidades

| ID | Funcionalidade | Descricao |
|----|----------------|-----------|
| BGL-001 | Definir limite | Max candidatos por busca |
| BGL-002 | Habilitar/desabilitar | Toggle busca global |
| BGL-003 | Ver saldo creditos | Creditos disponiveis |
| BGL-004 | Ver tabela custos | Custo por acao |
| BGL-005 | Historico de uso | Consumo de creditos |

---

### 3.6 HUB: PAINEL DE CONTROLE (control-panel)

> ⚠️ **ATENÇÃO - SEÇÃO FUTURA (FORA DO ESCOPO)**
> 
> Esta seção é parte do **MENU PRINCIPAL** e foi temporariamente documentada aqui apenas para facilitar sua movimentação posterior.
> 
> **NÃO DEVE SER INCLUÍDA NO PLANEJAMENTO DE DESENVOLVIMENTO DO MENU CONFIGURAÇÕES.**
> 
> Quando o desenvolvimento do Menu Principal iniciar, esta seção deve ser migrada para a documentação apropriada.

#### 3.6.1 Documentacao Basica

| Campo | Valor |
|-------|-------|
| **Nome** | Painel de Controle |
| **Objetivo** | Gestao de tarefas e atividades da equipe |
| **Componente** | `TasksPage` (integrado) |
| **Prioridade** | N/A (Fora do escopo Configurações) |
| **Tempo Estimado** | N/A |
| **Status** | ⚠️ SEÇÃO FUTURA - Menu Principal |

#### 3.6.2 Subsecoes

| ID | Subsecao | Descricao | Campos |
|----|----------|-----------|--------|
| tasks | Tarefas | Gerenciamento de tarefas | tasks[] |
| activities | Atividades | Historico de atividades | activities[] |

---

## 4. CARDS DE ESPECIFICACAO (JIRA)

---

### CARD EMP-001: Dados Basicos da Empresa

```yaml
Titulo: [FULL-STACK] Formulario de Dados Institucionais
Tipo: Feature
Sprint: 1
Pontos: 8

Descricao: |
  Implementar formulario completo para edicao dos dados
  institucionais da empresa com validacao e autosave.

Historia de Usuario: |
  Como administrador, eu quero editar os dados da empresa
  para manter as informacoes atualizadas nas vagas.

Regras de Negocio:
  1. Nome obrigatorio
  2. CNPJ validado (algoritmo brasileiro)
  3. Email corporativo
  4. Website URL valida
  5. Autosave com debounce 1s
  6. Logo upload ate 2MB

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/company/profile
    - PUT /api/backend-proxy/company/profile
    - POST /api/backend-proxy/company/logo (multipart)
  Frontend:
    - CompanyDataSection component
    - useForm hook com validacao
    - Debounced autosave
    - Toast de feedback
  Dados:
    - companies: id, name, trade_name, cnpj, website, email, phone, address, logo_url, industry, size, created_at, updated_at
  Validacoes:
    - CNPJ: lib cpf-cnpj-validator
    - Email: regex + dominio
    - Website: URL constructor

Riscos:
  - Upload de imagem pode ser lento
  - Validacao de CNPJ pode falhar em casos especiais

DoD:
  - [ ] Todos os campos editaveis
  - [ ] Validacoes funcionando
  - [ ] Autosave implementado
  - [ ] Upload de logo funciona
  - [ ] Testes unitarios
  - [ ] Testes E2E

Criterios de Aceitacao:
  - [ ] CNPJ invalido mostra erro
  - [ ] Dados salvam automaticamente
  - [ ] Logo aparece apos upload
  - [ ] Toast confirma salvamento
```

---

### CARD REC-004: Perguntas Screening

```yaml
Titulo: [FULL-STACK] CRUD de Perguntas Screening WhatsApp
Tipo: Feature
Sprint: 2
Pontos: 8

Descricao: |
  Implementar gerenciamento de perguntas de screening que
  serao enviadas aos candidatos via WhatsApp.

Historia de Usuario: |
  Como recrutador, eu quero configurar perguntas de screening
  para qualificar candidatos automaticamente.

Regras de Negocio:
  1. Perguntas default pre-configuradas
  2. Tipos: texto, sim/nao, escala, multipla escolha
  3. Perguntas podem ser obrigatorias
  4. Reordenacao com drag and drop
  5. Limite de 10 perguntas ativas
  6. Nao pode excluir perguntas default

Requisitos Tecnicos:
  Backend:
    - GET /api/backend-proxy/screening-questions
    - PUT /api/backend-proxy/screening-questions
    - POST /api/backend-proxy/screening-questions
    - DELETE /api/backend-proxy/screening-questions/{id}
  Frontend:
    - ScreeningQuestionsSection component
    - @dnd-kit para drag and drop
    - Modal de criacao/edicao
  Dados:
    - screening_questions: id, question, question_type, is_required, order, is_default, options, created_at
  Integracoes:
    - WhatsApp Business API (consumidor das perguntas)

Riscos:
  - Sincronizacao com WhatsApp pode ter delay
  - Reordenacao em lote pode causar conflitos

DoD:
  - [ ] CRUD completo
  - [ ] Drag and drop funciona
  - [ ] Validacoes
  - [ ] Testes

Criterios de Aceitacao:
  - [ ] Criar pergunta customizada
  - [ ] Editar pergunta
  - [ ] Reordenar com drag
  - [ ] Nao excluir default
```

---

### CARD EMP-012: Gestao de Usuarios

```yaml
Titulo: [FULL-STACK] Sistema de Gestao de Usuarios
Tipo: Feature
Sprint: 2
Pontos: 13

Descricao: |
  Implementar sistema completo de gestao de usuarios com
  convites, roles e permissoes.

Historia de Usuario: |
  Como administrador, eu quero gerenciar usuarios para
  controlar quem acessa a plataforma.

Regras de Negocio:
  1. Email obrigatorio e unico
  2. 4 roles: Admin, Recrutador, Gestor, Visualizador
  3. Convite por email com link de ativacao
  4. Usuario desativado nao pode logar
  5. Admin nao pode se auto-desativar
  6. Historico de login por usuario

Requisitos Tecnicos:
  Backend:
    - CRUD usuarios
    - Sistema de convites
    - Gestao de roles
    - Audit log de acessos
  Frontend:
    - UserManagement component
    - Modal de convite
    - Lista de usuarios com acoes
    - Filtros por role/status
  Dados:
    - users: id, email, name, role, status, last_login, created_at
    - user_invites: id, email, token, expires_at, accepted_at
    - user_activity_log: id, user_id, action, timestamp
  Seguranca:
    - Token de convite expira em 7 dias
    - Rate limiting em convites
    - Validacao de email corporativo

Riscos:
  - Email de convite pode cair em spam
  - Conflitos de permissao em edicao simultanea

DoD:
  - [ ] CRUD usuarios
  - [ ] Sistema de convites
  - [ ] Roles funcionando
  - [ ] Desativar/reativar
  - [ ] Testes

Criterios de Aceitacao:
  - [ ] Convidar usuario por email
  - [ ] Atribuir role
  - [ ] Desativar usuario
  - [ ] Admin nao pode se desativar
```

---

## 5. DIAGRAMAS DE JORNADA

### 5.1 Jornada: Onboarding Inicial

```
PONTO DE VISTA DO USUARIO:

INICIO
  +-- Primeiro acesso como Admin
       +-- Sistema detecta que configuracao esta incompleta
            +-- Modal "Assistente de Configuracao" aparece
                 +-- Escolhe template de empresa (Startup, PME, Enterprise)
                      +-- Preenche dados basicos
                           +-- Configura primeiros usuarios
                                +-- Define pipeline (ou usa default)
                                     +-- Completa wizard
                                          +-- Dashboard de Configuracoes
FIM

PONTO DE VISTA DO SISTEMA:

[FRONT] Detecta primeiro acesso (cookie + API)
[FRONT] Exibe OnboardingWizard modal
[BACK] GET /api/backend-proxy/settings/progress/
[IA] Sugere preenchimento com base em CNPJ (OPCIONAL)
[FRONT] Usuario seleciona template
[BACK] POST /api/backend-proxy/settings/apply-template
[BACK] Cria registros iniciais no banco
[FRONT] Navega por steps do wizard
[BACK] PUT /api/backend-proxy/company/profile
[BACK] POST /api/backend-proxy/users/invite
[BACK] PUT /api/backend-proxy/recruitment-journey/templates
[FRONT] Exibe dashboard com progresso
[BACK] GET /api/backend-proxy/settings/progress/
```

### 5.2 Jornada: Adicionar Usuario

```
PONTO DE VISTA DO USUARIO:

INICIO
  +-- Acessa Configuracoes -> Empresa & Equipe -> Usuarios
       +-- Clica em "Convidar Usuario"
            +-- Preenche email e seleciona role
                 +-- Clica em "Enviar Convite"
                      +-- Toast confirma envio
                           +-- Usuario aparece na lista como "Pendente"
FIM

PONTO DE VISTA DO SISTEMA:

[FRONT] Usuario clica "Convidar Usuario"
[FRONT] Abre modal com form
[FRONT] Valida email (formato e unicidade)
[BACK] POST /api/backend-proxy/users/invite
[BACK] Gera token de convite (UUID)
[BACK] Envia email com link de ativacao
[EMAIL] Template com link https://app.wedotalent.com/activate?token=xxx
[BACK] Cria registro user_invites
[FRONT] Atualiza lista de usuarios
[FRONT] Exibe toast de sucesso
```

---

## 6. ROADMAP POR FASES

### Fase 1: Core Setup (Sprint 1-2)

| Semana | Entrega |
|--------|---------|
| 1 | Dados da Empresa (EMP-001 a EMP-005) |
| 2 | Departamentos (EMP-008, EMP-009) |
| 3 | Usuarios e Roles (EMP-012 a EMP-014) |
| 4 | Pipeline e Screening (REC-001 a REC-008) |

### Fase 2: Comunicacao (Sprint 3)

| Semana | Entrega |
|--------|---------|
| 5 | Templates de Email (COM-001 a COM-007) |
| 6 | Assinatura e LGPD (COM-008, COM-009) |

### Fase 3: Metas e Busca (Sprint 4)

| Semana | Entrega |
|--------|---------|
| 7 | Metas Individuais (MET-001 a MET-005) |
| 8 | Busca Global Config (BGL-001 a BGL-005) |

### Fase 4: Avancado (Sprint 5+)

| Semana | Entrega |
|--------|---------|
| 9-10 | Beneficios (EMP-010, EMP-011) |
| 11-12 | Aprovadores (EMP-015, EMP-016) |
| 13+ | Workforce Planning (MET-006, MET-007) |

---

## 7. PADROES DE DESIGN

### 7.1 Layout

```tsx
// Estrutura padrao de Hub
<div className="flex h-screen overflow-hidden">
  {/* Sidebar colapsavel */}
  <aside className={cn(
    isCollapsed ? 'w-16' : 'w-64',
    'transition-all duration-200'
  )}>
    {/* Menu de secoes */}
  </aside>
  
  {/* Area de conteudo */}
  <main className="flex-1 overflow-auto p-6">
    {/* Header + Content */}
  </main>
</div>
```

### 7.2 Componentes

- **Cards**: `rounded-2xl`, sombra sutil, hover com elevacao
- **Botoes**: Variantes `default`, `outline`, `ghost`
- **Inputs**: Border sutil, focus com ring azul
- **Badges**: Status com cores semanticas (verde/amarelo/vermelho)

### 7.3 Cores de Status

```typescript
const statusColors = {
  completed: 'bg-green-100 text-green-700',
  incomplete: 'bg-red-100 text-red-700',
  pending: 'bg-yellow-100 text-yellow-700'
}
```

### 7.4 Tipografia

- **Titulos de secao**: `font-serif text-lg font-semibold`
- **Labels de menu**: `font-sans text-[11px] font-medium`
- **Descricoes**: `text-gray-600 text-xs`

---

## 8. APIS E INTEGRACAO BACKEND

### 8.1 Endpoints Principais

```
# Empresa
GET    /api/backend-proxy/company/profile
PUT    /api/backend-proxy/company/profile
POST   /api/backend-proxy/company/logo

# Departamentos
GET    /api/backend-proxy/departments
POST   /api/backend-proxy/departments
PUT    /api/backend-proxy/departments/{id}
DELETE /api/backend-proxy/departments/{id}

# Usuarios
GET    /api/backend-proxy/users
POST   /api/backend-proxy/users/invite
PUT    /api/backend-proxy/users/{id}
DELETE /api/backend-proxy/users/{id}
POST   /api/backend-proxy/users/{id}/deactivate

# Screening
GET    /api/backend-proxy/screening-questions
PUT    /api/backend-proxy/screening-questions

# Pipeline
GET    /api/backend-proxy/recruitment-journey/templates
PUT    /api/backend-proxy/recruitment-journey/templates

# Progresso
GET    /api/backend-proxy/settings/progress/
```

### 8.2 Formato de Resposta

```typescript
// Sucesso
{
  status: 'success',
  data: { ... },
  message?: string
}

// Erro
{
  status: 'error',
  error: {
    code: 'VALIDATION_ERROR',
    message: 'Campo X e obrigatorio',
    details?: { ... }
  }
}
```

---

## 9. REQUISITOS FUNCIONAIS

### 9.1 Requisitos de Seguranca

| ID | Requisito | Prioridade |
|----|-----------|------------|
| SEC-001 | Autenticacao JWT em todas as APIs | Alta |
| SEC-002 | Validacao de role para acoes admin | Alta |
| SEC-003 | Audit log de alteracoes | Media |
| SEC-004 | Rate limiting em convites | Media |
| SEC-005 | Token de convite expira em 7 dias | Media |

### 9.2 Requisitos de Performance

| ID | Requisito | Prioridade |
|----|-----------|------------|
| PERF-001 | Autosave com debounce 1s | Alta |
| PERF-002 | Carregamento < 2s por secao | Media |
| PERF-003 | Upload de logo < 5s | Media |
| PERF-004 | Lazy loading de subsecoes | Baixa |

### 9.3 Requisitos de UX

| ID | Requisito | Prioridade |
|----|-----------|------------|
| UX-001 | Sidebar colapsavel | Alta |
| UX-002 | Progress bar visual | Alta |
| UX-003 | Toast de feedback | Alta |
| UX-004 | Loading states | Media |
| UX-005 | Validacao inline | Media |

---

## 10. LISTA DE TASKS IMPORTAVEL

### 10.1 Epicos

```
EPIC-SET-001: Setup Inicial (Onboarding Wizard)
EPIC-SET-002: Empresa & Equipe
EPIC-SET-003: Recrutamento
EPIC-SET-004: Comunicacao
EPIC-SET-005: Metas & Planejamento
EPIC-SET-006: Busca Global
```

### 10.2 Tasks por Epico

```csv
epic_id,task_id,titulo,pontos,dependencias
EPIC-SET-002,EMP-001,Dados Basicos da Empresa,8,
EPIC-SET-002,EMP-002,Upload de Logo,3,EMP-001
EPIC-SET-002,EMP-003,Industria e Tamanho,3,EMP-001
EPIC-SET-002,EMP-004,Missao Visao Valores,5,EMP-001
EPIC-SET-002,EMP-005,Tech Stack,5,EMP-001
EPIC-SET-002,EMP-006,Perfil Big Five,8,EMP-001
EPIC-SET-002,EMP-008,CRUD Departamentos,8,EMP-001
EPIC-SET-002,EMP-009,Membros Departamentos,5,EMP-008
EPIC-SET-002,EMP-010,CRUD Beneficios,8,EMP-001
EPIC-SET-002,EMP-011,Elegibilidade Beneficios,5,EMP-010
EPIC-SET-002,EMP-012,CRUD Usuarios,13,EMP-001
EPIC-SET-002,EMP-013,Sistema de Roles,8,EMP-012
EPIC-SET-002,EMP-014,Permissoes Granulares,13,EMP-013
EPIC-SET-002,EMP-015,CRUD Aprovadores,8,EMP-012
EPIC-SET-002,EMP-016,Fluxo Aprovacao,8,EMP-015
EPIC-SET-003,REC-001,Visualizar Pipeline,5,
EPIC-SET-003,REC-002,Editar Pipeline (CS),8,REC-001
EPIC-SET-003,REC-003,Reordenar Etapas,3,REC-001
EPIC-SET-003,REC-004,CRUD Perguntas Screening,8,
EPIC-SET-003,REC-005,Tipos de Pergunta,5,REC-004
EPIC-SET-003,REC-006,Perguntas Obrigatorias,3,REC-004
EPIC-SET-003,REC-007,Reordenar Perguntas,3,REC-004
EPIC-SET-003,REC-008,Perguntas Default,3,REC-004
EPIC-SET-004,COM-001,Listar Templates,5,
EPIC-SET-004,COM-002,Criar Template,8,COM-001
EPIC-SET-004,COM-003,Editar Template,5,COM-001
EPIC-SET-004,COM-004,Variaveis Dinamicas,8,COM-002
EPIC-SET-004,COM-005,Preview Template,5,COM-002
EPIC-SET-004,COM-008,Editar Assinatura,5,
EPIC-SET-004,COM-009,Horarios LGPD,5,
EPIC-SET-004,COM-010,Configurar Alertas,8,
EPIC-SET-005,MET-001,Metas Individuais,8,
EPIC-SET-005,MET-002,Metas de Equipe,8,MET-001
EPIC-SET-005,MET-003,KPIs Recrutamento,8,
EPIC-SET-005,MET-004,Periodos,5,MET-001
EPIC-SET-005,MET-005,Dashboard Progresso,8,MET-001
EPIC-SET-005,MET-006,Workforce Planning,13,
EPIC-SET-006,BGL-001,Definir Limites,3,
EPIC-SET-006,BGL-002,Toggle Busca Global,3,
EPIC-SET-006,BGL-003,Saldo Creditos,5,
EPIC-SET-006,BGL-004,Tabela Custos,5,
EPIC-SET-006,BGL-005,Historico Uso,8,
```

### 10.3 Total de Pontos

| Epico | Pontos |
|-------|--------|
| Empresa & Equipe | 109 |
| Recrutamento | 38 |
| Comunicacao | 54 |
| Metas & Planejamento | 50 |
| Busca Global | 24 |
| **TOTAL** | **275 pontos** |

---

*Documento gerado em Dezembro 2024 - Versao 1.0*  
*WeDo Talent - Plataforma de Recrutamento com Agentes de IA*
