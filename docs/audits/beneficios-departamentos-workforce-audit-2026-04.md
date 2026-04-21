# Auditoria profunda — Benefícios, Departamentos e Workforce Planning
**Data:** 2026-04-21  
**Task origem:** #763  
**Escopo:** baseline obrigatório para as tarefas downstream
- Piloto Benefícios: lista item-a-item + formulário no Hub Minha Empresa
- Vaga: persistir benefícios estruturados em JSONB e corrigir herança no wizard
- Onboarding conversacional grava Benefícios com schema completo
- Remover Departamentos do Hub Minha Empresa e do onboarding conversacional
- Workforce Planning: visualização rica + captura conversacional

> Esta auditoria é **read-only**. Nenhum código foi alterado. As recomendações aqui são baseline; cada tarefa downstream deve referenciar a seção correspondente antes de implementar.

---

## Sumário executivo

| Domínio | Estado | Risco principal |
|---|---|---|
| **Benefícios** | Fragmentado em 2 modelos (`CompanyBenefit` simples vs `Benefit` rico), 2 listas-seed (25 vs 80+), 2 paths de gravação por agente (registry vs import_tools), `JobVacancy.benefits` é `ARRAY(String)` perdendo metadados, e há mismatch de coluna (`is_highlight` vs `is_highlighted`) que **quebra inserts hoje**. |
| **Departamentos** | Modelo canônico ok (`Department` em `company.py`), porém o Hub "Minha Empresa" e o onboarding **duplicam responsabilidade** com `UsuariosDepartamentosHub` (fonte da verdade). Two-fetch path (`useCompanyData` + `useCompanySettingsCards.fetchDepartments`). Remoção é segura desde que `UsuariosDepartamentosHub` permaneça como dono. |
| **Workforce** | `GoalsPlanningHub` (componente rico) está **órfão de navegação** e silenciosamente convive com bloco "workforce" simplificado em `use-company-settings-cards`. Modelos `WorkforceEntry` (simples) vs `PlannedHeadcount` (detalhado) divergem. Captura conversacional existe via `forecast_hiring_needs`, mas não persiste planejamento — só estima. |

**Ordem recomendada de execução das tarefas downstream** (com dependências):
1. **Piloto Benefícios** (Hub Minha Empresa) — não depende de schema; serve como template visual.
2. **Onboarding Benefícios schema completo** — depende do schema canônico definido no piloto.
3. **Vaga: benefits → JSONB** — depende de schema canônico + backfill (42 vagas com dados existentes).
4. **Workforce conversacional + visualização rica** — independente; pode rodar em paralelo a (1)–(3).
5. **Remover Departamentos do Hub Minha Empresa e onboarding** — última, depois que o piloto de Benefícios provar o padrão visual e que o contrato `UsuariosDepartamentosHub` está estável.

---

## 1. Benefícios

### 1.1 Mapa canônico (arquivo dono por responsabilidade)

| Responsabilidade | Arquivo canônico | Notas |
|---|---|---|
| Modelo de benefício de empresa (settings) | `lia-agent-system/libs/models/lia_models/company_benefit.py` (`CompanyBenefit`) | Modelo "simples". Tabela `company_benefits`. **Manter como canônico para settings.** |
| Modelo de benefício rico (com seniority, applicable_to, departments) | `lia-agent-system/libs/models/lia_models/company.py:146-187` (`Benefit`) | Sobreposição perigosa com `CompanyBenefit`. **Recomendação: deprecar `Benefit` ou fundir num único modelo.** |
| Templates globais (catálogo) | `lia-agent-system/libs/models/lia_models/company.py:455-474` (`BenefitTemplate`) + `app/api/v1/benefits.py` (`BENEFIT_TEMPLATES_DATA` 80+ items) | Mantém catálogo global de templates. |
| Lista de defaults para seed por empresa | `company_benefit.py:41-67` (`DEFAULT_BRAZILIAN_BENEFITS`, 25 items) | Seed de empresa. **Diverge** do catálogo global de 80+. |
| Router CRUD de empresa | `app/api/v1/company_benefits.py` | Canônico. |
| Router de templates + import CSV | `app/api/v1/benefits.py` | Canônico. |
| Repositório CRUD de empresa | `app/domains/company/repositories/company_benefit_repository.py` | Canônico. |
| Repositório do modelo rico | `app/domains/company/repositories/benefit_repository.py` | Usado pelo import CSV; cria `Benefit` (não `CompanyBenefit`). |
| Tool agente — gravar benefícios via chat | `app/domains/company_settings/agents/company_tool_registry.py:374-460` (`_wrap_save_company_benefits`) | **Canônico**: tem FairnessGuard L1 + audit_log + modes append/replace. |
| Tool agente — import bulk legado | `app/domains/company_settings/tools/import_tools.py:320-425` (`import_benefits_from_data`) | **DUPLICADO + QUEBRADO**: escreve `is_highlight` (coluna inexistente — o correto é `is_highlighted`) e ignora FairnessGuard. **Recomendação: remover ou redirecionar para `_wrap_save_company_benefits`.** |
| Type frontend | `plataforma-lia/src/types/benefits.ts` (`CompanyBenefit`) | Espelha o **modelo rico** (`Benefit`), não o `CompanyBenefit` simples. **Mismatch de nomenclatura.** |
| Hook frontend | `plataforma-lia/src/hooks/company/useCompanyBenefits.ts` | Canônico. |
| UI principal (settings) | `plataforma-lia/src/components/settings/BenefitsTab.tsx` | Canônico. |
| Modal de formulário | `plataforma-lia/src/components/settings/benefits/BenefitFormModal.tsx` | Padrão a replicar no piloto. |
| Card de item | `plataforma-lia/src/components/settings/benefits/BenefitItemCard.tsx` | Padrão a replicar. |
| Modal de templates | `plataforma-lia/src/components/settings/benefits/BenefitTemplateModal.tsx` | Padrão a replicar. |
| Wizard de vaga | `plataforma-lia/src/components/job-wizard/stages/SalaryStage.tsx` + `WizardContext.tsx:295-315,440-455` | Hidrata da empresa; produz `JobBenefit[]`. |
| Constantes de fallback do wizard | `plataforma-lia/src/components/job-wizard/constants.ts:200-210` (`INITIAL_BENEFITS`) | 10 items hardcoded — ativa-se quando empresa não tem nenhum. |
| Proxy frontend → backend | `src/app/api/backend-proxy/company/benefits/route.ts` + `[benefitId]/route.ts` | Canônico. |
| Onboarding conversacional | `plataforma-lia/src/components/onboarding/OnboardingChatPage.tsx` (+ `OnboardingActionOrchestrator.tsx`) | Hoje **não grava** schema completo — só passa nomes/strings. |

### 1.2 Duplicatas (com recomendação)

| # | Duplicata A | Duplicata B | Recomendação |
|---|---|---|---|
| D1 | `CompanyBenefit` (simples — 11 campos) | `Benefit` (rico — 20+ campos) | **Manter `CompanyBenefit` e estender** com os campos realmente usados (`waiting_period_days`, `seniority_levels`, `is_mandatory`, `provider`, `value_details`). Deprecar `Benefit` ou marcá-lo como interno do path CSV. |
| D2 | `DEFAULT_BRAZILIAN_BENEFITS` (25 items) em `company_benefit.py` | `BENEFIT_TEMPLATES_DATA` (80+ items) em `benefits.py` | **Unificar** em uma única fonte (`benefits_catalog.py`) e gerar ambos os subsets (popular vs seed-defaults) a partir dela. |
| D3 | `_wrap_save_company_benefits` (canônico, com Fairness+Audit) | `import_benefits_from_data` (sem Fairness, com bug de coluna) | **Remover `import_benefits_from_data`** e redirecionar callsites para o wrapper canônico. |
| D4 | Categorias em `company_benefits.py:233-246` (`health/food/transport/education/wellness/financial/family/flexibility/other`) | Categorias no template global (`benefits.py`: `quality_life/security`) e no type FE (`benefits.ts`) | **Padronizar enum único** (recomendação: manter conjunto de `company_benefits.py` por já ser o esperado pelos defaults). |
| D5 | `INITIAL_BENEFITS` (10 fallback hardcoded) no wizard | API `/company/benefits` | Eliminar fallback assim que onboarding garantir seed inicial; mantê-lo apenas como último recurso de runtime. |

### 1.3 Tabela de mismatches (DB × SQLAlchemy × Pydantic × TS)

| Campo | DB / `CompanyBenefit` | `Benefit` (rico) | Pydantic (`CompanyBenefitCreate/Response`) | TS (`benefits.ts`) | Mismatch |
|---|---|---|---|---|---|
| nome | `name: String(255)` | `name` | `name: str` | `name: string` | OK |
| categoria | `category: String(100)` | `category: BenefitCategory` (enum) | `category: str \| None` | `category: BenefitCategory` (enum strict) | **Enum FE strict vs string livre BE.** TS pode rejeitar valores válidos do BE. |
| destaque | `is_highlighted: Boolean` | `is_highlighted` | `is_highlighted` | `isHighlighted?` | `import_tools.py:396` escreve `is_highlight` → **erro de coluna**. |
| valor | `value: Float` + `value_type` | `value`, `value_type`, `percentage_value`, `value_details` | `value: float \| None` | `value?: number` | FE/Pydantic não expõem `percentage_value`/`value_details` que existem no modelo rico. |
| seniority | (não existe) | `seniority_levels: ARRAY(String)` | (não existe) | (não existe) | Perdido no settings simples. |
| ativo | `is_active: Boolean` | `is_active` | `is_active` | `isActive?` | OK |
| ordem | `order: Integer` | `display_order` | `order` | `order?` | **Nomes diferentes** entre os 2 modelos backend. |
| tenant | `company_id: String(255)` | `company_id: UUID` | `company_id: str` | n/a | **Tipo diferente** entre `CompanyBenefit` (string) e `Benefit` (UUID). Risca afeta queries de import. |
| `JobVacancy.benefits` | `ARRAY(String)` (apenas nomes) | n/a | `list[str]` | `string[]` ou `JobBenefit[]` | **Mismatch crítico**: FE produz `JobBenefit[]` estruturado, BE só armazena strings → metadata perdida. |

### 1.4 Fallbacks silenciosos / try-except mascarando

| Arquivo:linha | Padrão | Risco |
|---|---|---|
| `company_benefits.py:103-105, 122-125, 165-169, 195-198, 227-230` | `except Exception → 500 com str(e)` | OK, mas mascara stacktrace; não diferencia tenant/validation/db. |
| `BenefitsTab.tsx:172` | try/except silencioso ao buscar perfil da empresa | Edição segue sem perfil; usuário não percebe. |
| `useCompanyBenefits.ts:62` | Chamada a rota `/active` que **não existe** no router | Path inválido — só funciona porque o proxy provavelmente cai no `?active_only=true`. **Confirmar.** |
| `benefits.ts:27` (`toCompanyBenefit`) | `category ?? 'quality_life'` | Categoria silenciosamente trocada quando BE retorna `null`. |
| `import_tools.py:391-405` | `is_highlight=` (coluna inexistente) dentro de try/except → log "import_benefits failed" | **Bug latente**: nunca insere; só vê no log. |
| `_wrap_save_company_benefits:407-419` | FairnessGuard só roda em campos com `len > 10` | Strings curtas escapam. Aceitável, mas documentar. |
| `WizardContext.tsx:295-315` | Hidrata benefícios da empresa mas, se array vazio, cai em `INITIAL_BENEFITS` sem aviso | Recrutador pode não notar que está editando defaults globais, não da empresa. |

### 1.5 Callsites (quem grava / quem lê)

**Leituras (`company_benefits` table):**
- `company_tool_registry.py:140-149` (contexto do agente)
- `BenefitsTab.tsx:228` (settings)
- `useCompanyBenefits.ts:65` (hook)
- `WizardContext.tsx:295-315` (hidratar wizard)
- `app/api/v1/company_benefits.py:83-105` (`GET /`)

**Escritas (`company_benefits` table):**
- `company_tool_registry.py:_wrap_save_company_benefits:434` (chat)
- `import_tools.py:import_benefits_from_data:391` (broken — `is_highlight`)
- `app/api/v1/company_benefits.py:108-125, 148-169, 172-198, 201-230` (REST)
- `BenefitsTab.tsx:347` (UI manual)
- `OnboardingActionOrchestrator.tsx` (intenção `configure_benefits` → roteia ao chat → `_wrap_save_company_benefits`)

**Escritas em `job_vacancies.benefits`:**
- Wizard via endpoint de criação/edição de vaga (`POST /jobs`) — perde estrutura.
- Tools de criação de vaga via agente (verificar `tool_registry` de jobs).

### 1.6 Padrões de design já presentes (replicar)

- **Card list + Modal de form** (`BenefitItemCard` + `BenefitFormModal`) — padrão para o piloto.
- **Modal de templates** (`BenefitTemplateModal`) com filtragem por categoria/popular — replicar.
- **Hooks de settings** (`useCompanyBenefits` + invalidate por mutação) — manter.
- **Edit Mode com `pendingChanges`/`backup`** (`BenefitsTab.tsx:144-145`) — útil para batch edit.
- **Hidratação empresa→vaga** (`WizardContext.tsx:295-315`) — padrão de herança.

### 1.7 Riscos de migração `JobVacancy.benefits` → JSONB

- **Volume:** 42 vagas hoje têm `benefits` populado (`array_length > 0`).
- **Forma atual:** `ARRAY(String)` — só nomes.
- **Estratégia de backfill recomendada:**
  1. Adicionar coluna `benefits_json JSONB DEFAULT '[]'::jsonb` (nova coluna, sem destruir `benefits`).
  2. Script de backfill: para cada nome, fazer match (normalizado) com `company_benefits` da mesma empresa; se achar, copiar `category/description/icon/value`. Caso contrário, gerar `{name, category: 'other', source: 'legacy_string'}`.
  3. Dual-write por 1 release: continuar escrevendo `benefits` (nomes) **e** `benefits_json` (estruturado).
  4. Após validação de leitura no FE, dropar `benefits` e renomear `benefits_json → benefits`.
- **Risco baixo** (volume pequeno) mas exige cuidado com tenant scoping no backfill.

---

## 2. Departamentos

### 2.1 Mapa canônico

| Responsabilidade | Arquivo canônico |
|---|---|
| Modelo SQLAlchemy | `lia-agent-system/libs/models/lia_models/company.py:77` (`Department`) |
| Modelo de membro | `company.py:117` (`DepartmentMember`) |
| Schemas Pydantic | `lia-agent-system/app/schemas/company.py` (`DepartmentCreate/Update/Response`) |
| Router | `lia-agent-system/app/api/v1/company_departments.py` (CRUD + import CSV/Excel `:418`) |
| Repositório | `app/domains/company/repositories/department_repository.py` |
| Hook gestão | `plataforma-lia/src/hooks/settings/useDepartmentManagement.ts` |
| Hook leitura inicial | `src/hooks/settings/useCompanyData.ts:80-142` (`initialDepartments`) |
| **UI canônica** | `src/components/settings/UsuariosDepartamentosHub.tsx` + `DepartmentsTab.tsx` + `DepartmentGrid.tsx` + `DepartmentFormCard.tsx` |
| Onboarding (configure_workforce) | `OnboardingActionOrchestrator.tsx:75-80` (prompt "departamento, cargo, quantidade") |

### 2.2 Duplicatas

| # | Duplicata A | Duplicata B | Recomendação |
|---|---|---|---|
| D1 | `useCompanyData.fetchDepartments` (init em UsuariosDepartamentosHub) | `use-company-settings-cards.ts:323` (`fetchDepartments` próprio para o card "Benefícios & Departamentos") | **Remover o card de departamentos do MinhaEmpresaHub** (alinhado com a tarefa downstream) — elimina o segundo fetch. |
| D2 | Field `department: String` em `JobVacancy` (legado) | `department_id: UUID` (relacional) | **Já em transição.** Não escopo desta task — anotar para tarefa futura. |
| D3 | Departments aparece como contexto no agente via `configure_workforce` (em vez de `configure_departments` próprio) | UI de Departments dedicada | Onboarding deve **parar de coletar `departamento`** dentro do `configure_workforce` (será movido para fluxo próprio quando/se necessário). |

### 2.3 Mismatches DB × Pydantic × TS

| Campo | DB | Pydantic | TS |
|---|---|---|---|
| `id` | UUID | UUID | string | OK |
| `parent_id` | UUID nullable | UUID nullable | string nullable | OK |
| `manager_name`, `manager_email` | String nullable | str nullable | string nullable | OK |
| `budget_*` | numeric nullable | float nullable | number nullable | OK |
| `headcount_*` | int nullable | int nullable | number nullable | OK |
| Member roles | string enum livre | string | enum TS | **Enum TS strict** vs free string BE — risco baixo (lista pequena). |

### 2.4 Fallbacks silenciosos

- `use-company-settings-cards.ts:172` — se `departments` vazio, render `null` → `computeBlockStatus` marca como "pending" (sem mensagem). Após remoção, deixar de existir.
- `company_departments.py:260` — endpoints contextuais que aceitam `department` por string e caem em `None` — deixar como está (não é alvo da remoção).

### 2.5 Callsites (read/write)

**Reads:**
- `useDepartmentManagement.ts` (UsuariosDepartamentosHub)
- `DepartmentGrid.tsx`
- `JobListItem.tsx:61`
- `JobCreationPanel.tsx:26`
- `workforce.py:535` (analytics)
- `use-company-settings-cards.ts:323` ← **a remover**

**Writes:**
- `useDepartmentManagement.ts:173` (POST/PUT/DELETE via proxy)
- `company_departments.py:418` (import CSV/Excel)

### 2.6 Plano de remoção segura (Hub MinhaEmpresa + onboarding)

1. **Remover** o bloco `departamentos` do array em `use-company-settings-cards.ts:172` (e o fetch em `:323`).
2. **Remover** referência a "departamento" no prompt do `configure_workforce` em `OnboardingActionOrchestrator.tsx:80`.
3. **Manter intactos**: `UsuariosDepartamentosHub`, `useDepartmentManagement`, `useCompanyData.fetchDepartments`, router e modelo.
4. **Validar**: smoke-test em `MinhaEmpresaHub` (não deve mais aparecer "Departamentos") e em `UsuariosDepartamentosHub` (deve continuar funcionando idêntico).

---

## 3. Workforce Planning

### 3.1 Mapa canônico

| Responsabilidade | Arquivo canônico |
|---|---|
| Modelos SQLAlchemy | `lia_models/workforce` (`HiringPlan`, `PlannedHeadcount`, `WorkforceEntry`, `ImportJob`) |
| Schemas Pydantic | `lia-agent-system/app/schemas/workforce.py` |
| Router | `lia-agent-system/app/api/v1/workforce.py` (`/plans`, `/headcounts`, `/import/upload`, `/import/confirm`) |
| Repositório | `app/domains/workforce/repositories/workforce_repository.py` |
| Tool agente | `app/domains/talent_intelligence/tools/workforce_planning_tools.py:15` (`forecast_hiring_needs`) — **só estima**, não persiste plano |
| UI rica | `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx` + `WorkforceSection.tsx` + `GoalsWorkforceSection.tsx` + `useGoalsPlanningHub.ts` |
| Bloco simplificado em settings cards | `src/hooks/settings/use-company-settings-cards.ts:206` (block "workforce") |
| Importador | `src/components/settings/SmartImportZone.tsx:42` → `/api/backend-proxy/workforce/entries/import` |
| Detector de intent | `src/hooks/shared/use-action-intent.ts:33` ("headcount") |

### 3.2 Duplicatas / problemas estruturais

| # | Item | Recomendação |
|---|---|---|
| D1 | `WorkforceEntry` (yearly/monthly totais simples) vs `PlannedHeadcount` (com `title`, `salary`, `hiring_manager`) | **Definir o canônico** antes da tarefa downstream. Sugestão: `PlannedHeadcount` para o plano detalhado, `WorkforceEntry` apenas como agregação derivada. |
| D2 | `GoalsPlanningHub` órfão de navegação | A tarefa downstream "Workforce: visualização rica" precisa **devolver-lhe entrada de menu** ou embuti-lo na nova UI. |
| D3 | Bloco `workforce` em `use-company-settings-cards.ts:206` é simplificado e divergente do `GoalsPlanningHub` | **Substituir** pelo componente rico ou alinhar dados. |
| D4 | `forecast_hiring_needs` só calcula; não há tool agente que **grave** o plano (`save_workforce_plan`) | **Criar `_wrap_save_workforce_plan`** análogo a `_wrap_save_company_benefits`. |

### 3.3 Mismatches

| Camada | `WorkforceEntry` | `PlannedHeadcount` | TS |
|---|---|---|---|
| chave | (yearly/monthly) | título + salário + manager | mistura — UI usa ambos |
| `department` | string | `department_id` UUID | string em maioria dos componentes |
| importação | aceita CSV/Excel via fuzzy match (`SmartImportZone.tsx:148`) | API estruturada | mismatch silencioso quando headers ambíguos |

### 3.4 Fallbacks silenciosos

| Arquivo:linha | Padrão | Risco |
|---|---|---|
| `workforce_planning_tools.py:100` | turnover default 15% se não houver dado | Estimativa pode desviar muito sem aviso. |
| `workforce_planning_tools.py:132` | benchmark de 45 dias hardcoded | Idem. |
| `SmartImportZone.tsx:148` | match de header por substring lowercase | Mapeamento errado silencioso. |
| `use-company-settings-cards.ts:596` | mapeia `configure_workforce` → section "workforce" mas componente real é diferente do rico | Usuário cai numa UI simplificada sem perceber. |

### 3.5 Callsites

- **Reads:** `useGoalsPlanningHub.ts`, `WorkforceSection.tsx:187,220`, `use-company-settings-cards.ts:206`, `workforce.py:535`.
- **Writes:** `SmartImportZone.tsx:42`, `workforce.py` POST endpoints.
- **Conversacional:** `forecast_hiring_needs` (só leitura/estimativa) e `LiaFieldToggle` em `WorkforceSection.tsx:64` ("Lia consome dados").

### 3.6 Lacunas para tarefa downstream

- Ponto de entrada de navegação para `GoalsPlanningHub`.
- Tool de gravação conversacional (`save_workforce_plan`).
- Schema canônico (decidir entre `WorkforceEntry` e `PlannedHeadcount`).
- Aceitar 3 modos de captura: planilha (já existe), texto livre (precisa parser), colagem (textarea com parser).

---

## 4. Matriz de impacto sistêmico (feature-impact)

| Mudança planejada | Vagas | Candidatos | Screening | Billing | Audit log | Onboarding | LIA chat | Compliance/DEI |
|---|---|---|---|---|---|---|---|---|
| Piloto Benefícios (Hub) | nenhum | nenhum | nenhum | nenhum | já gravado | indireto | leitura | reforça FairnessGuard |
| Vaga: benefits → JSONB | **alto** (model + form + listing) | médio (display) | baixo | nenhum | médio | nenhum | médio (tool de criar vaga) | mantém |
| Onboarding grava schema completo | nenhum | nenhum | nenhum | nenhum | **alto** (audit log) | **alto** | **alto** (tools) | **alto** (PII masking + Fairness) |
| Remover Departamentos do Hub/onboarding | nenhum | nenhum | nenhum | nenhum | baixo | médio (prompt change) | baixo | nenhum |
| Workforce conversacional + UI rica | nenhum | nenhum | nenhum | nenhum | médio | médio | **alto** (nova tool) | médio |

---

## 5. Achados de compliance (lia-compliance)

- **PII no path conversacional de benefícios**: `_wrap_save_company_benefits` aplica FairnessGuard L1 mas **não aplica `mask_pii`** sobre `name/description`. Recomendação: adicionar mascaramento como em `_wrap_process_uploaded_document:705` (CPF/email/phone).
- **AuditTrail**: `save_benefits` registra actor + count (`company_tool_registry.py:458`). OK. Onboarding precisa garantir o mesmo.
- **FairnessGuard**: hoje só roda em strings com `len > 10`. Aceitável; documentar.
- **Four-Fifths Rule / Bias audit**: não afeta benefícios diretamente, mas `Benefit.applicable_to` (modelo rico) pode discriminar — auditar uso futuro.
- **LGPD**: `Department.manager_email` é PII; já está em `company.py:117`. Sem alterações.
- **EU AI Act**: tools agente `_wrap_save_company_benefits` e futura `save_workforce_plan` são "decisões assistidas" → manter audit log + FairnessGuard.

---

## 6. Guardrails recomendados (harness-engineering)

Para evitar regressões recorrentes, adicionar antes/depois das implementações:

1. **Lint customizado**: proibir `is_highlight` em qualquer arquivo Python (`scripts/lint_benefit_columns.sh`) — fixar o bug latente em `import_tools.py`.
2. **Schema test** (CI): comparar campos de `CompanyBenefit` model × Pydantic schema × TS type. Falhar PR em mismatch.
3. **Sensor de fallback silencioso**: grep por `except Exception:\s*pass` e `?? '` em `benefits.ts`/`BenefitsTab.tsx` deve resultar em zero.
4. **Tool permission**: `save_company_benefits` só permitido para agentes `company_settings`, `recruiter_assistant`, `orchestrator` — já configurado, manter.
5. **Checkpoint humano** no path conversacional de benefícios para `mode=replace` (destrutivo) — confirmar com recrutador antes de desativar atuais.
6. **CLAUDE.md / AGENTS.md**: registrar regra "JobVacancy.benefits é JSONB estruturado, nunca array de string" assim que a migração rodar.
7. **Guide**: documentar em `replit.md` o modelo canônico (`CompanyBenefit` é o dono; `Benefit` é interno do path CSV).

---

## 7. Lacunas de teste (lia-testing)

| Domínio | Cobertura atual | Lacunas |
|---|---|---|
| Benefícios | CRUD básico via REST tem teste de fumaça; tool agente sem eval | Adicionar eval golden para `_wrap_save_company_benefits` (append/replace + Fairness block); test de migração JSONB; test do hook `useCompanyBenefits`. |
| Departamentos | Hook `useDepartmentManagement` parcialmente testado | Test de regressão garantindo que remoção do card no MinhaEmpresaHub **não** quebra `UsuariosDepartamentosHub`. |
| Workforce | `forecast_hiring_needs` sem eval; importer com testes parciais | Eval para `forecast_hiring_needs`; test de parser de texto livre/colagem; test de roundtrip planilha → confirm. |
| Onboarding | E2E mínimo | E2E "configure_benefits" gravando 5 itens com schema completo + audit log + Fairness. |

---

## 8. Feature-audit (14 dimensões) — estado atual

| # | Dimensão | Benefícios | Departamentos | Workforce |
|---|---|---|---|---|
| 1 | Integração FE↔BE | parcial (rota `/active` suspeita) | OK | OK (rico) / divergente (simplificado) |
| 2 | Dados (modelo único) | **fragmentado** (2 modelos) | OK | **fragmentado** (2 modelos) |
| 3 | UI/Design System v4.2.1 | OK | OK | parcial (UI rica órfã) |
| 4 | Backend | OK | OK | OK |
| 5 | Tipos | mismatch FE/BE | OK | mismatch |
| 6 | Fluxo do usuário | quebrado em onboarding | quebrado (duplicado em 2 hubs) | quebrado (sem nav) |
| 7 | Consistência | baixa | média | baixa |
| 8 | Documentação | escassa | escassa | escassa |
| 9 | Arquitetura de agentes | duplicada (2 paths) | OK | incompleta (sem save) |
| 10 | Qualidade LLM | FairnessGuard ok | n/a | sem eval |
| 11 | Serviços IA | OK | n/a | OK |
| 12 | Governança IA | parcial (sem PII mask em benefits) | OK | parcial |
| 13 | Segurança | bug coluna `is_highlight` | OK | OK |
| 14 | Performance | OK | OK | OK |

---

## 9. Ordem de execução consolidada (com dependências e riscos)

| Ordem | Tarefa | Depende de | Riscos |
|---|---|---|---|
| 1 | **Piloto Benefícios** (Hub Minha Empresa, lista item-a-item + form) | nada | baixo — só UI; precisa fixar `is_highlight`→`is_highlighted` antes de qualquer import. |
| 2 | **Onboarding conversacional grava Benefícios com schema completo** | Schema canônico do piloto (1) | médio — adicionar `mask_pii` ao path; usar `_wrap_save_company_benefits` (não `import_benefits_from_data`). |
| 3 | **Vaga: persistir benefícios JSONB + herança no wizard** | Schema canônico (1) | médio-alto — migração de 42 linhas; dual-write por release; backfill com normalização de nomes. |
| 4 | **Workforce: visualização rica + captura conversacional** | nada (paralelo a 1–3) | médio — precisa decidir `WorkforceEntry` vs `PlannedHeadcount`; criar tool `save_workforce_plan`; restaurar nav. |
| 5 | **Remover Departamentos do Hub Minha Empresa e onboarding** | confirmação de que (1) é referência visual estável | baixo — só remover bloco em `use-company-settings-cards.ts:172,323` e prompt em `OnboardingActionOrchestrator.tsx:80`. |

---

## 10. Apêndice — referências rápidas

- `lia-agent-system/libs/models/lia_models/company_benefit.py:12-39`
- `lia-agent-system/libs/models/lia_models/company.py:77,117,146-187,455-474`
- `lia-agent-system/libs/models/lia_models/job_vacancy.py:55-60,184-188`
- `lia-agent-system/app/api/v1/benefits.py`
- `lia-agent-system/app/api/v1/company_benefits.py`
- `lia-agent-system/app/api/v1/company_departments.py`
- `lia-agent-system/app/api/v1/workforce.py`
- `lia-agent-system/app/domains/company_settings/agents/company_tool_registry.py:140-178,374-460,564-725,858-957`
- `lia-agent-system/app/domains/company_settings/tools/import_tools.py:320-475` ← bug `is_highlight`
- `lia-agent-system/app/domains/talent_intelligence/tools/workforce_planning_tools.py:15`
- `lia-agent-system/app/domains/company_settings/config/capabilities.yaml:50-66`
- `plataforma-lia/src/types/benefits.ts`
- `plataforma-lia/src/hooks/company/useCompanyBenefits.ts:62`
- `plataforma-lia/src/hooks/settings/use-company-settings-cards.ts:172,206,323,596`
- `plataforma-lia/src/hooks/settings/useCompanyData.ts:80-142`
- `plataforma-lia/src/hooks/settings/useDepartmentManagement.ts:173`
- `plataforma-lia/src/components/settings/MinhaEmpresaHub.tsx`
- `plataforma-lia/src/components/settings/BenefitsTab.tsx:144,145,172,228,347`
- `plataforma-lia/src/components/settings/benefits/BenefitFormModal.tsx`
- `plataforma-lia/src/components/settings/benefits/BenefitItemCard.tsx`
- `plataforma-lia/src/components/settings/benefits/BenefitTemplateModal.tsx`
- `plataforma-lia/src/components/settings/UsuariosDepartamentosHub.tsx`
- `plataforma-lia/src/components/settings/DepartmentsTab.tsx`
- `plataforma-lia/src/components/settings/DepartmentGrid.tsx`
- `plataforma-lia/src/components/settings/DepartmentFormCard.tsx`
- `plataforma-lia/src/components/settings/GoalsPlanningHub.tsx`
- `plataforma-lia/src/components/settings/WorkforceSection.tsx:64,187,220`
- `plataforma-lia/src/components/settings/GoalsWorkforceSection.tsx`
- `plataforma-lia/src/components/settings/SmartImportZone.tsx:42,148`
- `plataforma-lia/src/components/job-wizard/WizardContext.tsx:295-315,440-455`
- `plataforma-lia/src/components/job-wizard/stages/SalaryStage.tsx`
- `plataforma-lia/src/components/job-wizard/constants.ts:200-210`
- `plataforma-lia/src/components/onboarding/OnboardingChatPage.tsx`
- `plataforma-lia/src/components/onboarding/OnboardingActionOrchestrator.tsx:75-80`
- `plataforma-lia/src/app/api/backend-proxy/company/benefits/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/company/benefits/[benefitId]/route.ts`

**Volumetria atual (snapshot):** 42 vagas com `benefits` populado · 25 `company_benefits` · 15 `departments`.
