# Integração do Fluxo de Gestão de Vagas

> **Objetivo:** Garantir que todos os campos fluam corretamente entre:
> Menu Configurações → Wizard de Criação de Vagas → job_vacancies (backend) → EditJobModal (Visão Geral + Roteiro de Triagem) → Interview Notes

**Data:** 19 de Janeiro de 2026  
**Versão:** 1.0  
**Status:** Em Planejamento

---

## 1. Arquitetura de Dados

### 1.1 Fonte Única de Dados (Single Source of Truth)

A tabela `job_vacancies` no backend é a **fonte única e centralizada** de todos os dados de vagas.

**Localização:** `lia-agent-system/app/models/job_vacancy.py`

### 1.2 Campos Principais da Tabela job_vacancies

| Campo | Tipo | Descrição | Origem |
|-------|------|-----------|--------|
| `title` | String | Título da vaga | Wizard |
| `department` | String | Departamento | Wizard + Settings |
| `location` | String | Localização | Wizard + Settings |
| `work_model` | String | Modelo de trabalho (presencial/híbrido/remoto) | Settings |
| `employment_type` | String | Tipo de contratação (CLT/PJ) | Wizard |
| `seniority_level` | String | Senioridade | Wizard |
| `description` | Text | Descrição da vaga | Wizard (LIA) |
| `requirements` | Array | Requisitos básicos (legacy) | Wizard (LIA) |
| `technical_requirements` | JSON | Skills técnicas estruturadas | Wizard + Settings (tech_stack) |
| `languages` | JSON | Idiomas necessários | **Settings** (auto-preenchido) |
| `behavioral_competencies` | JSON | Competências comportamentais | **Wizard** (deve gerar) |
| `salary_range` | JSON | Faixa salarial | Wizard |
| `benefits` | Array | Benefícios | Settings |
| `interview_stages` | JSON | Etapas do processo seletivo | **Settings** (recruitment journey) |
| `screening_questions` | JSON | Perguntas de triagem | Wizard (LIA gera) |
| `screening_config` | JSON | Configuração de triagem (canais, wsi_skills) | Sistema |
| `manager` | String | Gestor responsável | Wizard + Settings |
| `recruiter` | String | Recrutador responsável | Wizard |
| `organizational_structure` | JSON | Estrutura do time | Wizard (LIA) |
| `timeline` | JSON | Cronograma | Wizard (LIA) |
| `governance_rules` | JSON | Regras de autonomia LIA | Settings |
| `target_sector` | String | Setor alvo | Wizard |
| `target_segment` | String | Segmento alvo | Wizard |

---

## 2. Mapeamento: Settings → Campos Auto-Preenchidos

### 2.1 Campos do Menu Configurações que Devem Auto-Preencher Vagas

| Tab/Seção em Settings | Campo | Endpoint API | Campo em job_vacancies |
|----------------------|-------|--------------|------------------------|
| **Company Profile** | `work_model` | `/api/backend-proxy/company/profile` | `work_model` |
| **Company Profile** | `headquarters` | `/api/backend-proxy/company/profile` | `location` (default) |
| **Company Profile** | `locations` | `/api/backend-proxy/company/profile` | `location` (opções) |
| **Company Profile** | `tech_stack` | `/api/backend-proxy/company/profile` | `technical_requirements` |
| **Benefits** | Lista de benefícios | `/api/backend-proxy/company/benefits` | `benefits` |
| **Departments** | Lista de áreas | `/api/backend-proxy/company/departments` | `department` (dropdown) |
| **Recruitment Journey** | Etapas do processo | `/api/backend-proxy/recruitment-journey/templates` | `interview_stages` |
| **Culture Profile** | Big Five | `/api/backend-proxy/company/culture-profile` | Usado em fit cultural |
| **Managers** | Lista de gestores | `/api/backend-proxy/company/users?role=manager` | `manager` (dropdown) |

### 2.2 Campos que NÃO São Gerados pelo Wizard (Auto-Preenchimento Obrigatório)

| Campo | Origem | Status Atual | Ação Necessária |
|-------|--------|--------------|-----------------|
| `languages` | Settings (perfil empresa) | ❌ Não implementado | Criar campo em Settings e auto-preencher |
| `interview_stages` | Settings (Recruitment Journey) | ⚠️ Parcial | Sincronizar com wizard |
| `work_model` | Settings (Company Profile) | ✅ Implementado | Manter |
| `benefits` | Settings (Benefits Tab) | ✅ Implementado | Manter |
| `governance_rules` | Settings (Approvals/Autonomy) | ❌ Não implementado | Criar campo em Settings |

---

## 3. Matriz de Integração Completa

### 3.1 Fluxo de Dados por Componente

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MENU CONFIGURAÇÕES                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │ Company     │ │ Benefits    │ │ Recruitment │ │ Culture     │        │
│  │ Profile     │ │ Tab         │ │ Journey     │ │ Profile     │        │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘        │
│         │               │               │               │                │
│  - work_model    - benefits[]    - stages[]      - big_five             │
│  - locations     - categories    - SLAs          - values               │
│  - tech_stack                    - types                                 │
│  - departments                                                           │
│  - languages*                                                            │
└─────────┬───────────────┴───────────────┴───────────────┴───────────────┘
          │ Auto-preenchimento (hooks)
          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      JOB CREATION WIZARD                                 │
│                                                                          │
│  GERA:                              PUXA DE SETTINGS:                   │
│  ✅ title                           ✅ work_model                       │
│  ✅ description                     ✅ location (options)               │
│  ✅ seniority_level                 ✅ tech_stack → technical_reqs      │
│  ✅ employment_type                 ✅ benefits                         │
│  ✅ salary_range                    ✅ departments                      │
│  ✅ manager (seleção)               ✅ interview_stages                 │
│  ✅ screening_questions             ⚠️ languages (FALTA)               │
│  ✅ organizational_structure        ⚠️ governance_rules (FALTA)        │
│  ⚠️ behavioral_competencies (FALTA)                                    │
│  ✅ target_sector/segment                                               │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ POST/PUT /api/v1/job-vacancies
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     job_vacancies (Backend DB)                           │
│                      SINGLE SOURCE OF TRUTH                              │
│                                                                          │
│  Campos JSON:                      Campos Simples:                       │
│  - technical_requirements[]        - title, department, location         │
│  - behavioral_competencies[]       - work_model, employment_type         │
│  - languages[]                     - seniority_level, status            │
│  - screening_questions[]           - manager, recruiter                  │
│  - interview_stages[]              - salary, priority                    │
│  - screening_config{}                                                    │
│  - organizational_structure{}                                            │
│  - timeline{}                                                            │
│  - governance_rules{}                                                    │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ GET /api/v1/job-vacancies/{id}
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EDIT JOB MODAL                                   │
│  ┌────────────────────────┐    ┌────────────────────────────────────┐   │
│  │     TAB VISÃO GERAL    │    │      TAB ROTEIRO DE TRIAGEM        │   │
│  │                        │    │                                     │   │
│  │ ✅ title               │    │ ✅ technical_requirements (NOVO)   │   │
│  │ ✅ department          │    │ ✅ behavioral_competencies (NOVO)  │   │
│  │ ✅ location            │    │ ⚠️ screening_questions (FALTA)    │   │
│  │ ✅ work_model          │    │ ⚠️ interview_stages (FALTA edit)  │   │
│  │ ✅ seniority_level     │    │ ⚠️ wsi_skills sync (FALTA)        │   │
│  │ ✅ employment_type     │    │                                     │   │
│  │ ✅ salary_range        │    │                                     │   │
│  │ ✅ languages           │    │                                     │   │
│  │ ✅ manager             │    │                                     │   │
│  │ ⚠️ interview_stages   │    │                                     │   │
│  │    (view only)         │    │                                     │   │
│  └────────────────────────┘    └────────────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ Dados usados para gerar perguntas
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      INTERVIEW NOTES CARD                                │
│                                                                          │
│  Gera perguntas baseadas em:                                            │
│  POST /api/v1/interview-notes/generate-questions                        │
│                                                                          │
│  ⚠️ PROBLEMA ATUAL:                                                     │
│  - Usa screening_config.wsi_skills (separado)                           │
│  - NÃO usa technical_requirements/behavioral_competencies               │
│  - Desconectado das edições feitas no EditJobModal                      │
│                                                                          │
│  Fontes de perguntas:                                                   │
│  1. Vaga/WSI: screening_config.wsi_skills ou screening_questions        │
│  2. Gap Analysis: Comparação CV vs requisitos                           │
│  3. Fit Cultural: culture_profile vs candidato                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Status de Cada Campo por Componente

| Campo | Settings | Wizard | job_vacancies | EditJobModal | Interview Notes |
|-------|----------|--------|---------------|--------------|-----------------|
| `title` | - | ✅ Gera | ✅ Armazena | ✅ Edita | ✅ Usa |
| `department` | ✅ Lista | ✅ Seleciona | ✅ Armazena | ✅ Edita | - |
| `location` | ✅ Options | ✅ Seleciona | ✅ Armazena | ✅ Edita | - |
| `work_model` | ✅ Default | ✅ Puxa | ✅ Armazena | ✅ Edita | - |
| `seniority_level` | - | ✅ Gera | ✅ Armazena | ✅ Edita | - |
| `employment_type` | - | ✅ Gera | ✅ Armazena | ✅ Edita | - |
| `technical_requirements` | ✅ tech_stack | ✅ Puxa/Gera | ✅ Armazena | ✅ Edita | ❌ Não usa |
| `behavioral_competencies` | - | ✅ Gera (seleção + Big Five fallback) | ✅ Armazena | ✅ Edita | ✅ Usa via wsi_skills sync |
| `languages` | ❌ **FALTA** | ❌ **FALTA** | ✅ Armazena | ✅ Edita | - |
| `benefits` | ✅ Lista | ✅ Seleciona | ✅ Armazena | ⚠️ View | - |
| `interview_stages` | ✅ Config | ✅ Auto-preenche de Settings | ✅ Armazena | ⚠️ View only | - |
| `screening_questions` | - | ✅ LIA gera | ✅ Armazena | ✅ Edita | ✅ Usa |
| `screening_config.wsi_skills` | - | - | ✅ Armazena | ✅ Sincroniza auto | ✅ Usa (agora conectado!) |
| `manager` | ✅ Lista | ✅ Seleciona | ✅ Armazena | ✅ Edita | - |
| `timeline` | - | ✅ LIA gera | ✅ Armazena | ❌ **FALTA** | - |
| `governance_rules` | ❌ **FALTA** | ❌ **FALTA** | ✅ Armazena | ❌ **FALTA** | - |

---

## 4. Problemas Críticos Identificados

### 4.1 Desconexão: screening_config.wsi_skills

**PROBLEMA:** O `wsi_skills` está armazenado dentro de `screening_config` (objeto separado), mas as skills editáveis no EditJobModal estão em `technical_requirements` e `behavioral_competencies`.

**CONSEQUÊNCIA:** 
- Editar skills no EditJobModal **NÃO** atualiza `wsi_skills`
- Interview Notes **continua usando** o `wsi_skills` antigo
- Perguntas de entrevista ficam **desatualizadas**

**SOLUÇÃO:** Ao salvar skills no EditJobModal, sincronizar automaticamente com `screening_config.wsi_skills`.

### 4.2 behavioral_competencies Não Geradas pelo Wizard

**PROBLEMA:** O Wizard de Criação de Vagas não coleta/gera competências comportamentais.

**SOLUÇÃO:** Adicionar etapa no Wizard para coletar competências comportamentais baseadas em:
- Análise do cargo pela LIA
- Perguntas situacionais
- Seleção manual pelo recrutador

### 4.3 languages Não Existe em Settings

**PROBLEMA:** Não há campo de idiomas no Menu Configurações para auto-preencher vagas.

**SOLUÇÃO:** 
- Criar campo `default_languages` em Company Profile
- Auto-preencher no Wizard quando criar nova vaga
- Permitir edição no EditJobModal

### 4.4 screening_questions Não Editáveis

**PROBLEMA:** As perguntas de triagem geradas pela LIA não podem ser editadas no EditJobModal.

**SOLUÇÃO:** Adicionar seção na Tab "Roteiro de Triagem" para visualizar/editar perguntas de triagem.

---

## 5. Plano de Implementação

### Fase 1: Correções Críticas (Prioridade Alta)

| # | Tarefa | Arquivos | Complexidade |
|---|--------|----------|--------------|
| 1.1 | Wizard gerar `behavioral_competencies` | `job-creation-wizard.tsx` | Média |
| 1.2 | Sincronizar skills editadas com `wsi_skills` | `edit-job-modal.tsx`, API route | Média |
| 1.3 | Adicionar edição de `screening_questions` na Tab Roteiro | `edit-job-modal.tsx` | Alta |

### Fase 2: Auto-Preenchimento de Settings (Prioridade Alta)

| # | Tarefa | Arquivos | Complexidade |
|---|--------|----------|--------------|
| 2.1 | Criar campo `languages` em Settings | Novo componente, API | Média |
| 2.2 | Wizard puxar `interview_stages` de Settings | `job-creation-wizard.tsx` | Baixa |
| 2.3 | Wizard puxar `languages` de Settings | `job-creation-wizard.tsx` | Baixa |
| 2.4 | Validar auto-preenchimento existente (work_model, benefits, etc) | Testes | Baixa |

### Fase 3: Melhorias no EditJobModal (Prioridade Média)

| # | Tarefa | Arquivos | Complexidade |
|---|--------|----------|--------------|
| 3.1 | Adicionar edição de `interview_stages` | `edit-job-modal.tsx` | Alta |
| 3.2 | Mostrar origem do campo (Settings icon + tooltip) | `edit-job-modal.tsx` | Baixa |
| 3.3 | Adicionar seção `timeline` (view/edit) | `edit-job-modal.tsx` | Média |

### Fase 4: Backend/Interview Notes (Prioridade Média)

| # | Tarefa | Arquivos | Complexidade |
|---|--------|----------|--------------|
| 4.1 | Interview Notes usar `technical_requirements` + `behavioral_competencies` | Backend Python | Média |
| 4.2 | Remover dependência isolada de `wsi_skills` | Backend Python | Média |
| 4.3 | Criar endpoint unificado de "job profile" para Interview Notes | Backend Python | Alta |

---

## 6. Indicadores Visuais

### 6.1 Campo Auto-Preenchido de Settings

Quando um campo é auto-preenchido a partir do Menu Configurações:

- **Ícone:** ⚙️ (Settings) ao lado do label
- **Tooltip (preto):** "Este valor foi preenchido automaticamente com base nas Configurações da sua empresa."
- **Banner (se múltiplos campos):** Banner sutil cyan no topo da seção

### 6.2 Campo Gerado pelo Wizard/LIA

Quando um campo é gerado pela LIA durante criação:

- **Ícone:** ✨ (Sparkles) ao lado do label
- **Tooltip:** "Este valor foi sugerido pela LIA durante a criação da vaga."

---

## 7. Validações

### 7.1 Campos Obrigatórios para Publicação

| Campo | Obrigatório | Pode vir de Settings |
|-------|-------------|---------------------|
| `title` | ✅ Sim | Não |
| `department` | ✅ Sim | ✅ Sim (lista) |
| `seniority_level` | ✅ Sim | Não |
| `work_model` | ✅ Sim | ✅ Sim (default) |
| `technical_requirements` | ✅ Sim (min 1) | ✅ Sim (tech_stack) |
| `behavioral_competencies` | ⚠️ Recomendado | Não |
| `interview_stages` | ✅ Sim | ✅ Sim (obrigatório) |

### 7.2 Fallback Behavior

Se um campo de Settings estiver vazio:
1. Wizard mostra campo para preenchimento manual
2. Valor informado durante o chat com LIA é usado
3. Campo aparece em branco no EditJobModal (editável)

---

## 8. Próximos Passos

1. ✅ Documento de diagnóstico criado (este arquivo)
2. ⏳ Implementar Fase 1 (Correções Críticas)
3. ⏳ Implementar Fase 2 (Auto-Preenchimento)
4. ⏳ Implementar Fase 3 (Melhorias EditJobModal)
5. ⏳ Implementar Fase 4 (Backend/Interview Notes)
6. ⏳ Testes de integração end-to-end
7. ⏳ Documentação de usuário

---

## Apêndice A: Arquivos Principais

| Componente | Arquivo |
|------------|---------|
| Job Creation Wizard | `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx` |
| Edit Job Modal | `plataforma-lia/src/components/modals/edit-job-modal.tsx` |
| Interview Note Card | `plataforma-lia/src/components/interview-notes/interview-note-card.tsx` |
| Jobs Page | `plataforma-lia/src/components/pages/jobs-page.tsx` |
| Screening Config Hook | `plataforma-lia/src/hooks/useScreeningConfig.ts` |
| Recruitment Stages Hook | `plataforma-lia/src/hooks/use-recruitment-stages.ts` |
| Backend Model | `lia-agent-system/app/models/job_vacancy.py` |
| Backend API | `lia-agent-system/app/api/v1/job_vacancies.py` |
| LIA API Service | `plataforma-lia/src/services/lia-api.ts` |

## Apêndice B: Hooks de Settings Existentes

| Hook | Arquivo | Dados |
|------|---------|-------|
| `useRecruitmentStages` | `use-recruitment-stages.ts` | Etapas do processo |
| `useCompanyBenefits` | `use-company-benefits.ts` | Lista de benefícios |
| `useCompanyTechStack` | `use-company-tech-stack.ts` | Stack tecnológica |
| `useCompanyCulture` | `use-company-culture.ts` | Perfil cultural (Big Five) |
| `useCompanyManagers` | `use-company-managers.ts` | Lista de gestores |
| `useWorkforcePlanning` | `use-workforce-planning.ts` | Planejamento de headcount |

---

*Documento gerado em 19/01/2026 - Plataforma LIA v3.0*
