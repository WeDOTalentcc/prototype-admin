# Diagnóstico: Campos de Vaga - Banco de Dados vs Wizard de Criação

**Data:** Janeiro 2026  
**Objetivo:** Identificar gaps entre campos do banco de dados e campos preenchidos no wizard de criação de vagas

---

## 1. CAMPOS DO BANCO DE DADOS (JobVacancy)

### 1.1 Campos de Identificação (Automáticos)
| Campo | Tipo | Preenchimento | Notas |
|-------|------|---------------|-------|
| `id` | UUID | ✅ Automático | Gerado automaticamente |
| `job_id` | String | ⚠️ Gerado | Ex: WDT-2025-001 - deve ser gerado automaticamente |
| `company_id` | String | ✅ Automático | Multi-tenancy |
| `public_slug` | String | ✅ Automático | URL pública |

### 1.2 Campos Básicos da Vaga (Wizard - Etapa 1)
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `title` | String | ✅ Etapa 1 | OK - Obrigatório |
| `department` | String | ✅ Etapa 1 | OK |
| `location` | String | ✅ Etapa 1 | OK |
| `work_model` | String | ✅ Etapa 1 | OK (presencial/híbrido/remoto) |
| `employment_type` | String | ✅ Etapa 1 | OK (CLT/PJ) |
| `seniority_level` | String | ✅ Etapa 1 | OK (Júnior/Pleno/Sênior) |

### 1.3 Campos de Requisitos (Wizard - Etapas 2-3)
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `description` | Text | ✅ Etapa 6 | OK - Gerada por LIA |
| `requirements` | Array | ⚠️ Legacy | Usado como fallback |
| `technical_requirements` | JSON | ✅ Etapa 2 | OK |
| `languages` | JSON | ✅ Etapa 2 | OK |
| `behavioral_competencies` | JSON | ✅ Etapa 3 | OK |

### 1.4 Campos de Compensação (Wizard - Etapa 4)
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `salary` | String | ⚠️ Legacy | Usar salary_range |
| `salary_range` | JSON | ✅ Etapa 4 | OK (min/max/currency/bonus) |
| `benefits` | Array | ✅ Etapa 4 | OK |

### 1.5 Campos de Screening (Wizard - Etapa 5)
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `screening_questions` | JSON | ✅ Etapa 5 | OK - WSI questions |
| `eligibility_questions` | JSON | ✅ Etapa 5 | OK - Pré-triagem |
| `screening_config` | JSON | ⚠️ Parcial | Configurações avançadas |

### 1.6 Campos de Pessoas (Responsáveis)
| Campo | Tipo | Wizard | Status | **SOLUÇÃO IMPLEMENTADA** |
|-------|------|--------|--------|--------------------------|
| `manager` | String | ✅ Perguntado | **OK** | Wizard pergunta nome do gestor |
| `manager_email` | String | ✅ Inferido | **OK** | `manager_inference_service.py` busca email na estrutura da empresa |
| `recruiter` | String | ✅ Auto-preenchido | **OK** | Preenchido automaticamente do usuário logado |
| `recruiter_email` | String | ✅ Auto-preenchido | **OK** | Preenchido automaticamente do usuário logado |
| `created_by` | String | ✅ Automático | **OK** | Preenchido em `finalize_job_vacancy` |

**Serviços implementados:**
- `manager_inference_service.py`: Busca gestores na estrutura da empresa (Departments/DepartmentMembers)
- Endpoints `/api/v1/company/managers` e `/api/v1/company/managers/infer-email`
- Auto-preenchimento de recruiter no `job_vacancy_service.finalize_job_vacancy()`

### 1.7 Campos de Datas
| Campo | Tipo | Wizard | Status | **SOLUÇÃO IMPLEMENTADA** |
|-------|------|--------|--------|--------------------------|
| `open_date` | DateTime | ⚠️ Parcial | OK | Inferido da publicação |
| `deadline` | DateTime | ✅ Calculado | **OK** | Calculado via `deadline_calculator_service.py` usando SLAs do pipeline |
| `deadline_screening` | DateTime | ✅ Calculado | **OK** | Calculado via SLAs do pipeline template |
| `deadline_shortlist` | DateTime | ✅ Calculado | **OK** | Calculado via SLAs do pipeline template |
| `deadline_closing` | DateTime | ✅ Calculado | **OK** | Calculado via SLAs do pipeline template |

**Serviço implementado:**
- `deadline_calculator_service.py`: Calcula prazos baseado em `sla_days` de cada estágio do pipeline template
- Integrado em `job_vacancy_service.finalize_job_vacancy()`
- Fallback para defaults (30 dias) se não houver pipeline configurado

### 1.7.1 Campos de Data (Automáticos)
| Campo | Tipo | Preenchimento | Status |
|-------|------|---------------|--------|
| `created_at` | DateTime | ✅ Automático | OK |
| `updated_at` | DateTime | ✅ Automático | OK |
| `published_at` | DateTime | ✅ Automático | OK |
| `closed_at` | DateTime | ✅ Automático | OK |

### 1.8 Campos de Status e Workflow (Automáticos/Sistema)
| Campo | Tipo | Preenchimento | Status |
|-------|------|---------------|--------|
| `status` | String | ✅ Automático | OK (Rascunho/Ativa/etc) |
| `stage` | String | ✅ Automático | OK (Planejamento/etc) |
| `priority` | String | ⚠️ Opcional | Pode ser perguntado |
| `urgency_level` | Integer | ❌ NÃO | Deveria inferir ou perguntar |

### 1.9 Campos de Pipeline/Entrevistas (Wizard - Etapa 7)
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `interview_stages` | JSON | ✅ Etapa 7 | OK |
| `hiring_process` | Array | ⚠️ Legacy | Stages antigas |

### 1.10 Campos de Publicação
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `published_linkedin` | Boolean | ✅ Revisão Final | OK |
| `published_website` | Boolean | ✅ Revisão Final | OK |
| `published_indeed` | Boolean | ✅ Revisão Final | OK |
| `linkedin_post_id` | String | ✅ Automático | OK |
| `indeed_job_id` | String | ✅ Automático | OK |
| `last_published_at` | DateTime | ✅ Automático | OK |

### 1.11 Campos de Confidencialidade
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `is_confidential` | Boolean | ⚠️ Legacy | Usar visibility |
| `is_affirmative` | Boolean | ❌ NÃO | Deveria perguntar |
| `visibility` | String | ⚠️ Parcial | Pode ser perguntado |
| `access_list` | Array | ❌ NÃO | Para vagas confidenciais |
| `masked_company_name` | String | ❌ NÃO | Para vagas confidenciais |
| `confidentiality_config` | JSON | ❌ NÃO | Configurações avançadas |

### 1.12 Campos de Orçamento e Aprovação
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `budget` | Float | ❌ NÃO | Orçamento da vaga |
| `budget_used` | Float | ✅ Automático | Calculado |
| `approval_status` | String | ✅ Automático | Workflow de aprovação |
| `approval_requested_at` | DateTime | ✅ Automático | OK |
| `approval_requested_by` | String | ✅ Automático | OK |
| `approved_by` | String | ✅ Automático | OK |
| `approved_at` | DateTime | ✅ Automático | OK |
| `rejection_reason` | Text | ✅ Automático | OK |

### 1.13 Campos de Targeting/Segmentação
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `tags` | Array | ⚠️ Parcial | Pode ser sugerido |
| `target_audience` | String | ❌ NÃO | Público-alvo |
| `target_sector` | String | ❌ NÃO | Ex: "Fintechs" |
| `target_segment` | String | ❌ NÃO | Ex: "Meios de Pagamento" |

### 1.14 Campos de Métricas (Automáticos)
| Campo | Tipo | Preenchimento | Status |
|-------|------|---------------|--------|
| `nps` | Integer | ✅ Automático | OK |
| `funnel_data` | JSON | ✅ Automático | OK |
| `lia_metrics` | JSON | ✅ Automático | OK |
| `view_count` | Integer | ✅ Automático | OK |

### 1.15 Campos Avançados
| Campo | Tipo | Wizard | Status |
|-------|------|--------|--------|
| `organizational_structure` | JSON | ❌ NÃO | Estrutura da equipe |
| `timeline` | JSON | ✅ Calculado | Cronograma |
| `governance_rules` | JSON | ❌ NÃO | Regras de autonomia LIA |
| `next_actions` | Array | ✅ Automático | OK |
| `additional_data` | JSON | ✅ Flexível | OK |

---

## 2. GAPS CRÍTICOS IDENTIFICADOS

### 🔴 Campos CRÍTICOS que faltam no Wizard:

| Campo | Criticidade | Problema | Solução Recomendada |
|-------|-------------|----------|---------------------|
| **manager** | ALTA | Nunca é perguntado | Adicionar na Etapa 1 ou criar etapa de "Responsáveis" |
| **manager_email** | ALTA | Nunca é perguntado | Adicionar junto com manager (ou autocompletar de cadastro de gestores) |
| **recruiter** | ALTA | Não pega do usuário logado | Preencher automaticamente com usuário logado |
| **recruiter_email** | ALTA | Não pega do usuário logado | Preencher automaticamente com usuário logado |
| **created_by** | ALTA | Não é preenchido | Preencher automaticamente com usuário logado |
| **deadline** | MÉDIA | Prazo não é perguntado | Perguntar na Etapa 1 ou criar etapa de "Cronograma" |

### 🟡 Campos IMPORTANTES que poderiam ser adicionados:

| Campo | Importância | Justificativa |
|-------|-------------|---------------|
| `urgency_level` | MÉDIA | Ajuda na priorização |
| `deadline_screening` | MÉDIA | SLA de triagem |
| `deadline_shortlist` | MÉDIA | SLA de shortlist |
| `deadline_closing` | MÉDIA | Prazo final |
| `is_affirmative` | BAIXA | Vagas afirmativas |
| `budget` | BAIXA | Controle de custos |
| `target_sector` | BAIXA | Melhora o sourcing |

---

## 3. DIAGNÓSTICO POR ETAPA DO WIZARD

### Etapa 1 - Informações Básicas ✅
**Status:** Bom, mas incompleto

**Campos atuais:**
- title ✅
- department ✅
- location ✅
- work_model ✅
- employment_type ✅
- seniority_level ✅

**Campos faltando:**
- ❌ manager (gestor responsável)
- ❌ manager_email
- ❌ deadline (prazo geral)
- ⚠️ priority (opcional)

### Etapa 2 - Requisitos Técnicos ✅
**Status:** OK

### Etapa 3 - Competências Comportamentais ✅
**Status:** OK

### Etapa 4 - Benefícios e Compensação ✅
**Status:** OK

### Etapa 5 - Perguntas de Triagem (WSI) ✅
**Status:** OK

### Etapa 6 - Descrição da Vaga ✅
**Status:** OK

### Etapa 7 - Revisão Final ⚠️
**Status:** Bom, mas faltam campos de responsáveis

**Campos que deveriam ser validados/exibidos:**
- ❌ manager (exibir e permitir edição)
- ❌ manager_email (exibir e permitir edição)
- ❌ recruiter (exibir - pego automaticamente)
- ❌ recruiter_email (exibir - pego automaticamente)
- ❌ deadline (exibir e permitir edição)

---

## 4. RECOMENDAÇÕES DE IMPLEMENTAÇÃO

### Prioridade 1 - Crítico (Implementar imediatamente)

#### 4.1 Preencher automaticamente dados do recrutador
```typescript
// Ao iniciar o wizard, preencher:
const initializeWizard = async () => {
  const currentUser = await getCurrentUser();
  
  setJobData(prev => ({
    ...prev,
    recruiter: currentUser.name,
    recruiter_email: currentUser.email,
    created_by: currentUser.id
  }));
};
```

#### 4.2 Adicionar campo de Gestor na Etapa 1
```tsx
// Adicionar campos:
<FormField name="manager" label="Gestor da Vaga" required />
<FormField name="manager_email" label="Email do Gestor" type="email" />

// OU usar um Select com gestores cadastrados:
<ManagerSelect 
  onSelect={(manager) => {
    setJobData(prev => ({
      ...prev,
      manager: manager.name,
      manager_email: manager.email
    }));
  }}
/>
```

#### 4.3 Adicionar campo de Prazo na Etapa 1
```tsx
<FormField 
  name="deadline" 
  label="Prazo para Fechamento" 
  type="date"
  helperText="Data limite para preenchimento da vaga"
/>
```

### Prioridade 2 - Importante (Implementar em seguida)

#### 4.4 Adicionar prazos detalhados (opcional avançado)
- deadline_screening
- deadline_shortlist
- deadline_closing

Podem ser calculados automaticamente baseado no `deadline` principal ou perguntados em uma seção "Cronograma Avançado".

### Prioridade 3 - Desejável (Backlog)

- Campos de confidencialidade avançada
- Campos de orçamento
- Campos de targeting/segmentação

---

## 5. FLUXO ATUAL vs FLUXO IDEAL

### Fluxo ATUAL:
```
Etapa 1: Título, Departamento, Local, Modelo, Tipo, Senioridade
Etapa 2: Requisitos Técnicos + Idiomas
Etapa 3: Competências Comportamentais
Etapa 4: Salário + Benefícios
Etapa 5: Perguntas WSI
Etapa 6: Descrição
Etapa 7: Revisão Final
→ Publica
```

### Fluxo IDEAL (proposto):
```
Etapa 1: Informações Básicas
  - Título, Departamento, Local, Modelo, Tipo, Senioridade
  - **+ Gestor (nome + email)** ← NOVO
  - **+ Prazo de fechamento** ← NOVO
  - (recruiter preenchido automaticamente do usuário logado)

Etapa 2: Requisitos Técnicos + Idiomas

Etapa 3: Competências Comportamentais

Etapa 4: Salário + Benefícios

Etapa 5: Perguntas WSI

Etapa 6: Descrição

Etapa 7: Revisão Final
  - Mostrar todos os campos incluindo:
  - Gestor: João Silva (joao@empresa.com)
  - Recrutador: Maria Santos (maria@empresa.com) [automático]
  - Prazo: 15/03/2026
  
→ Publica
```

---

## 6. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] **Backend:** Garantir que `recruiter`, `recruiter_email`, `created_by` são preenchidos automaticamente na criação
- [ ] **Backend:** Validar campos obrigatórios no endpoint de criação
- [ ] **Frontend - Etapa 1:** Adicionar campo `manager` (Select ou Input)
- [ ] **Frontend - Etapa 1:** Adicionar campo `manager_email` (auto-preenchido se usar Select)
- [ ] **Frontend - Etapa 1:** Adicionar campo `deadline` (DatePicker)
- [ ] **Frontend - Wizard Init:** Preencher `recruiter` e `recruiter_email` do usuário logado
- [ ] **Frontend - Revisão:** Exibir todos os campos de responsáveis
- [ ] **API:** Criar endpoint para listar gestores da empresa (para Select)
- [ ] **Testes:** Adicionar testes E2E para novos campos

---

## 7. RESUMO EXECUTIVO

| Categoria | Total Campos | Preenchidos | Faltando | % Cobertura |
|-----------|--------------|-------------|----------|-------------|
| Identificação | 4 | 4 | 0 | 100% |
| Básicos | 6 | 6 | 0 | 100% |
| Requisitos | 5 | 4 | 1 | 80% |
| Compensação | 3 | 2 | 0 | 100% |
| Screening | 3 | 2 | 1 | 67% |
| **Pessoas** | **5** | **0** | **5** | **0%** ❌ |
| Datas | 8 | 4 | 4 | 50% |
| Status | 4 | 3 | 1 | 75% |
| Pipeline | 2 | 1 | 1 | 50% |
| Publicação | 6 | 6 | 0 | 100% |
| Confidencialidade | 6 | 1 | 5 | 17% |
| Orçamento | 7 | 6 | 1 | 86% |
| Targeting | 4 | 1 | 3 | 25% |
| Métricas | 4 | 4 | 0 | 100% |
| Avançados | 5 | 3 | 2 | 60% |

**Conclusão:** A categoria **"Pessoas"** (manager, manager_email, recruiter, recruiter_email, created_by) está com **0% de cobertura** e é o gap mais crítico a ser resolvido.
