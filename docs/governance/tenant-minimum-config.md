# Tenant Minimum Config — Contrato Canônico

> **Status:** Spec ativa (Task #816, abr/2026)
> **Escopo:** Plataforma LIA (lia-agent-system + plataforma-lia)
> **Idioma:** PT-BR
> **Audiência:** time de plataforma, agentes IA que escrevem código de seeding/onboarding, revisores de compliance.

---

## 1. Sumário Executivo

Este documento define **o que é "configuração mínima viável" para um tenant da Plataforma LIA**: o conjunto canônico de tabelas, defaults e políticas que precisam estar populadas para que o chat com a LIA opere sem ser sequestrado por hints de onboarding, e para que os agentes principais (criação de vaga, sourcing, triagem, pipeline) executem suas intents primárias sem fricção.

**Por que existe?** A Task #813 populou o tenant demo (`DEMO_COMPANY_UUID = 00000000-0000-4000-a000-000000000001`) via `seed_demo_company_settings(db)`. Esse seed grava em **9 tabelas** (descritas como "8 críticas" no commit original porque o helper `_seed_demo_skills_catalog` toca 2 tabelas — `company_skills_catalog` + `behavioral_competencies_catalog`). Isso resolveu o sintoma local — a demo deixou de emitir 3 hints `info` repetidamente — mas **o problema é geral**: qualquer tenant novo (real ou de homologação) chega com essas tabelas vazias, dispara as mesmas hints e, dependendo da severidade, pode ser desviado para o agente `company_settings` perdendo a intent original do usuário (ex.: "criar vaga" virando "configurar empresa"). Nas demais seções deste doc, **"9 tabelas" é a contagem canônica**.

Este doc é o **contrato** para qualquer tarefa futura de seeding/onboarding/bootstrap de tenant. Implementação fica em tarefas separadas (ver §8).

**Princípios não-negociáveis (ver §7):**

- Privacy-by-default (LGPD): defaults nunca contêm PII de pessoa física real. Apenas placeholders genéricos ou estruturas vazias.
- Fairness-by-default (DEI): defaults de política de recrutamento e benefícios precisam passar pelo `FairnessGuard` antes de serem persistidos. **Nota de implementação:** a API atual `FairnessGuard.check(query: str)` (`app/shared/compliance/fairness_guard.py:723`) é síncrona e recebe **texto livre**, não dict. Para validar defaults estruturados, a implementação precisa serializar os campos textuais (mission, vision, values, evp_bullets, descrições de policy) e rodar `guard.check(text)` em cada um — OU especificar uma nova interface estruturada (`check_policy_dict`/`check_culture_profile`) como pré-requisito de implementação. O contrato exige a validação; a forma exata fica para a tarefa de implementação resolver.
- Determinismo (Crença #10): a decisão "este tenant tem o mínimo" precisa ser uma query SQL determinística, não uma chamada de LLM.
- Sem fallback silencioso (canonical-fix): seed que falha levanta exceção; nunca grava parcialmente nem mascara erro.
- Tenant-isolation: nenhum default vaza entre tenants. Defaults universais (catálogo de skills baseline, benefícios brasileiros padrão) são copiados por tenant, não compartilhados.

---

## 2. Conceito de "Mínimo Viável"

Um tenant é considerado **mínimamente configurado** quando:

1. **`PreConditionChecker` não emite hints `warning`/`critical` de onboarding** para nenhuma intent comum (ver §3 para o catálogo completo).
2. **Os agentes core (orchestrator + 5 chats principais) operam sua intent primária** sem que o roteamento `_decide_agent_type_from_hints` desvie para `company_settings`.
3. **As tabelas auxiliares** (catálogo de skills, competências comportamentais, retenção LGPD, controles de compliance) têm seed baseline para que ferramentas como WSI scoring, `bias_audit`, `analyze_company_culture` tenham contexto utilizável.
4. **Os campos canônicos do `company_profiles`** (id = company_id do tenant, name, industry, company_size) estão presentes — pelo menos com placeholders honestos ("Não informado") para o admin completar. **Exceção: `website`** permanece NULL por design (ver §5.1) — é o sinal legítimo que dispara o offer `analyze_company_website`, então preencher com placeholder mascararia uma feature do produto.

**O que "mínimo viável" NÃO inclui:**

- Vagas reais (`job_vacancies`), candidatos (`candidates`), pipeline (`vacancy_candidates`) — esses são dados de operação, não configuração.
- Integrações externas (Gupy, Pandapé, Merge.dev, WhatsApp Business, MS Teams) — opt-in pelo cliente.
- LLM customizado por tenant (`llm_configs`) — herda do default global se omitido.
- Usuários adicionais — apenas o admin inicial precisa existir (criado pelo provisioning, fora deste contrato).

---

## 3. Mapeamento Hint → Tabela → Query → Default

Fonte da verdade: `lia-agent-system/app/orchestrator/precondition_checker.py` (D10 Proactive Contextual Assistance).

### 3.1 Catálogo completo das 8 hints

| # | `type` | Severity | Tabela alvo | Query do checker | Bloqueia rota? | Coberto pela #813? |
|---|--------|----------|-------------|------------------|----------------|--------------------|
| 1 | `missing_company_id` | **warning** | `company_profiles` (presença do company_id no contexto) | `getattr(ctx, "company_id", None)` — não chega ao DB | **SIM** (único bloqueante "always-on") | N/A — é checagem de contexto, não de schema |
| 2 | `incomplete_company_profile` | info | `company_profiles` | `SELECT name, industry, company_size FROM company_profiles WHERE id::text=:cid OR client_account_id::text=:cid LIMIT 1` | Não | **SIM** — #813 garante a row, #819 preenche `name/industry/company_size` na própria row e remove `website` da query (website tem hint dedicada #4 — evita duplicar o sinal) |
| 3 | `vacancy_no_screening_questions` | warning | `screening_questions` | `SELECT COUNT(*) FROM screening_questions WHERE vacancy_id=:vid AND company_id=:cid` | **SIM** (mas só dispara se `intent ∈ {screening, wsi, tria, triagem}` E `vacancy_id` presente) | Não — é por-vaga, não por-tenant. #813 popula `company_screening_questions` (catálogo), não `screening_questions` (por vaga) |
| 4 | `company_website_missing` | info | `company_profiles.website` | `SELECT website FROM company_profiles WHERE id::text=:cid OR client_account_id::text=:cid LIMIT 1` | Não | **Não** — #813 não escreve website na row canônica de `company_profiles`; o site `https://demo.lia.local` está apenas dentro do payload de `company_culture_profiles` |
| 5 | `culture_profile_missing` | info | `company_culture_profiles` | `SELECT COUNT(*) FROM company_culture_profiles WHERE company_id::text=:cid` | Não | **SIM** — `_seed_demo_culture_profile(db)` insere row completa para DEMO_COMPANY_UUID |
| 6 | `benefits_catalog_empty` | info | `company_benefits` | `SELECT COUNT(*) FROM company_benefits WHERE company_id::text=:cid AND is_active=true` | Não | **SIM** — `_seed_demo_company_benefits(db)` insere os 25 benefícios de `DEFAULT_BRAZILIAN_BENEFITS` |
| 7 | `hiring_policy_missing` | info | `company_hiring_policies` | `SELECT COUNT(*) FROM company_hiring_policies WHERE company_id::text=:cid` | Não | **SIM** — `_seed_demo_hiring_policy(db)` insere row a partir de `HIRING_POLICY_DEFAULTS` |
| 8 | `candidates_missing_contact` | warning | `candidates` | `SELECT COUNT(*) FROM candidates WHERE company_id::text=:cid AND email IS NULL/empty AND phone IS NULL/empty AND status NOT IN ('rejected','archived','hired')` | **SIM** (mas só dispara se `intent` casar `sourcing|outreach|contact|contato|enviar|mensagem` E `count >= 3`) | Não aplicável — é dado operacional, não config |

### 3.2 Lógica de roteamento (orquestrador)

`_decide_agent_type_from_hints()` em `main_orchestrator.py:103-152` aplica em ordem:

1. **Intent explícito** ∈ `_COMPANY_SETTINGS_INTENTS = {"company_settings", "configure_company", "settings_config", "hiring_policy"}` → delega para `company_settings` independente de hints. (O usuário pediu.)
2. **Hint `type ∈ _ONBOARDING_HINT_TYPES` AND `severity ∈ {"warning","critical"}`** → delega para `company_settings`. Pré-requisito real.
3. **Caso contrário** → mantém `orchestrator`. Hints `info` viram sugestão anexada ao prompt, intent primária do usuário roda normalmente.

`_ONBOARDING_HINT_TYPES` (subconjunto das 8): `{missing_company_id, incomplete_company_profile, company_website_missing, culture_profile_missing, benefits_catalog_empty, hiring_policy_missing}`. As hints `vacancy_no_screening_questions` e `candidates_missing_contact` **não** estão neste conjunto — são contextuais por intent, não onboarding-wide.

**Consequência prática:** das 6 hints onboarding-wide, **apenas `missing_company_id` (warning) bloqueia hoje**. As 5 demais são `info` e nunca sequestram a rota. **Logo, a única coisa que `seed_demo_company_settings` precisava fazer para "destravar o chat" era garantir o `company_id` válido** — as outras 4 tabelas que silenciam hints `info` foram populadas para reduzir ruído no prompt e fornecer contexto rico, não para destravar fluxo.

---

## 4. Cobertura Atual da Task #813

`seed_demo_company_settings(db)` em `lia-agent-system/app/shared/services/seed_service.py:1640-1718` popula 9 tabelas (a 9ª — `behavioral_competencies_catalog` — vem da mesma função `_seed_demo_skills_catalog` que popula `company_skills_catalog`).

| # | Tabela | Helper | Volume | Hint silenciada | Justificativa adicional |
|---|--------|--------|--------|-----------------|-------------------------|
| 1 | `company_benefits` | `_seed_demo_company_benefits` | 25 (DEFAULT_BRAZILIAN_BENEFITS) | `benefits_catalog_empty` | Atração de candidatos (Crença #1 — Humano em Primeiro Lugar) |
| 2 | `company_culture_profiles` | `_seed_demo_culture_profile` | 1 row + ensure `company_profiles(id=DEMO_COMPANY_UUID)` | `culture_profile_missing` | Match cultural na triagem WSI dimensão `contextual` (15%) |
| 3 | `company_hiring_policies` | `_seed_demo_hiring_policy` | 1 row (HIRING_POLICY_DEFAULTS) | `hiring_policy_missing` | Confidence-based decision engine (Crença #12 — Autonomia Progressiva começa como assistente) |
| 4 | `company_compliance_controls` | `_seed_demo_compliance_controls` | até 5 controles × 3 frameworks (LGPD, SOX, ISO_27001) — máximo 15 rows; insere menos se `ComplianceControlLibrary` tiver menos itens. Status inicial = `"not_started"` (`seed_service.py:1472`) | — (não há hint específica) | Dashboard `admin/compliance/auditoria/bias`, FRIA EU AI Act |
| 5 | `company_responsibilities` | `_seed_demo_responsibilities` | 5 rows | — | Catálogo para criação de vaga (autocomplete) |
| 6 | `company_skills_catalog` | `_seed_demo_skills_catalog` | 6 técnicas | — | WSI dimensão `technical` (50%) — autocomplete + scoring baseline |
| 7 | `behavioral_competencies_catalog` | `_seed_demo_skills_catalog` | 5 comportamentais | — | WSI dimensão `behavioral` (20%) — BARS scoring |
| 8 | `company_retention_policies` | `_seed_demo_retention_policy` | 1 row com `retention_months=24, auto_anonymize=False` (`seed_service.py:1603-1604`) | — | LGPD Art. 16 — política opt-in (anonimização desativada por default; recrutador habilita) |
| 9 | `company_screening_questions` | `_seed_demo_screening_questions` | DEFAULT_SCREENING_QUESTIONS | — | Banco de perguntas baseline. Não confundir com `screening_questions` (per-vaga, hint #3) |

**Observação crítica:** Das 9 tabelas, **apenas 3 silenciam hints** (#1, #2, #3 da tabela acima). As outras 6 são "boa prática" / "contexto rico", não invariantes do `PreConditionChecker`.

### 4.1 Gaps remanescentes vs §3

Após #813 + #819 aplicadas, apenas uma hint `info` ainda aparece no tenant demo, e isso é por design:

- **`company_website_missing`** (info): `company_profiles.website` segue NULL deliberadamente (§5.1). É o sinal legítimo que dispara o offer `analyze_company_website`. Preencher com placeholder mascararia uma feature do produto. → **gap intencional**.

`incomplete_company_profile` está coberto pela #819 em duas frentes complementares:
1. `_ensure_demo_company_profile` agora escreve `name`, `industry` e `company_size` na row canônica via `ON CONFLICT DO UPDATE` + `COALESCE/NULLIF` (idempotente, não sobrescreve dados de admin) e usa `RETURNING (xmax = 0)` para distinguir insert real de update.
2. `_check_company_profile_completeness` removeu `website` da query e da lista de campos faltantes — o sinal de website fica exclusivamente em `company_website_missing` (hint #4), evitando emitir o mesmo gap em duas hints diferentes.

`missing_company_id` está coberto pelo provisioning de tenant (fora deste seed), e `vacancy_no_screening_questions` + `candidates_missing_contact` são contextuais por turno — não fazem parte do mínimo do tenant.

---

## 5. Defaults Canônicos por Item

Cada item tem (a) **valor default** sugerido, (b) **justificativa governance**, (c) **fairness/LGPD check**. Defaults marcados `[FAIR]` precisam passar por `FairnessGuard.check()` antes de persistência.

### 5.1 `company_profiles` (row canônica)

| Campo | Default sugerido | Justificativa |
|-------|------------------|---------------|
| `id` | UUID gerado pelo provisioning | Chave primária, RLS depende disso |
| `client_account_id` | mesmo UUID OU referência ao client_account de origem | `_check_company_profile_completeness` consulta por id OR client_account_id |
| `name` | `"<nome cadastrado no signup>"` ou `"Empresa em Configuração"` (placeholder explícito) | Nunca string vazia — vira hint `info`. Placeholder honesto > campo vazio. |
| `industry` | `"Não informado"` (placeholder) ou inferido por IA com `confidence < 0.70` exigindo confirmação humana (Crença #12) | Confidence < 0.70 = ASK_USER (lia-compliance §1) |
| `company_size` | `"Não informado"` ou faixa estimada via website scrape com confirmação | Idem |
| `website` | NULL se não fornecido (em vez de placeholder) — hint `company_website_missing` é o gatilho legítimo do `analyze_company_website` | Manter NULL é o sinal correto para o offer auto-scrape |

**Fairness/LGPD:** nenhum campo canônico contém PII. O `name` placeholder não identifica pessoa física. ✅

### 5.2 `company_culture_profiles` `[FAIR]`

Default igual ao `_DEMO_CULTURE_PROFILE` em `seed_service.py:51-77`, mas com **nome e missão genéricos** (não copiar literal do demo "Transformar a forma como empresas atraem..."). Sugestão para tenants reais:

```python
{
    "mission": "[Pendente — completar via onboarding]",
    "vision": "[Pendente — completar via onboarding]",
    "values": ["Transparência", "Colaboração", "Aprendizado contínuo"],  # baseline neutro, FAIR-safe
    "evp_bullets": [],  # vazio até onboarding preencher
    "core_competencies": ["Comunicação", "Pensamento Analítico", "Colaboração", "Adaptabilidade"],
    "culture_description": "[Pendente — perfil cultural será completado via onboarding conversacional]",
    "work_model": "Hybrid",  # default mais comum, ajustável
    "default_languages": [{"code": "pt-BR", "label": "Português (Brasil)"}],
    "openness_score": 50, "conscientiousness_score": 50, "extraversion_score": 50,
    "agreeableness_score": 50, "stability_score": 50,  # OCEAN neutro até dados reais
    "source": "tenant_minimum_default",
    "confidence_score": 0.0,  # forçar ASK_USER em qualquer uso pelo agente
}
```

**Justificativa:** silenciar a hint `culture_profile_missing` sem mentir sobre a calibração. `confidence_score=0.0` força `ConfidencePolicyService` para ASK_USER em todo uso, preservando Crença #3 (Transparente e Explicável).

### 5.3 `company_benefits`

Default: copiar `DEFAULT_BRAZILIAN_BENEFITS` (25 itens) com `is_active=true` e `source="tenant_minimum_default"`.

**Justificativa:** lista é canônica do mercado BR (VR/VA, plano de saúde, transporte, PLR, home office, gympass, etc), não favorece empresa específica. Recrutador edita/desativa via UI conforme contrato real do tenant.

**Fairness:** lista não menciona atributos protegidos. ✅

### 5.4 `company_hiring_policies` `[FAIR]`

Default: usar `HIRING_POLICY_DEFAULTS` em `lia_models.company_hiring_policy` com **autonomia ajustada para baseline mais conservador** que o demo:

- `automation_level = "assistant"` (Crença #12 — começa como assistente, escala com confiança)
- `confidence_threshold_apply_silent = 0.85`
- `confidence_threshold_apply_notify = 0.70`
- `require_human_approval_for = ["rejection", "hire", "salary_change"]` (Inegociável #2)
- `fairness_audit_enabled = true` (Inegociável #3)
- `pii_masking_enabled = true` (Inegociável #4)

**Validação obrigatória pré-persistência:** rodar `FairnessGuard().check(text)` (síncrono, recebe string — ver §1 nota de implementação) sobre cada campo textual da policy serializado: descrição da política, lista de critérios, prompts de aprovação automática, mensagens de feedback. Qualquer resultado bloqueante aborta o seed (sem fallback silencioso). Se a implementação preferir uma interface estruturada, ela é pré-requisito da tarefa #818 (ver §8 item 1) e não invalida o contrato.

### 5.5 `company_compliance_controls`

Default: até 5 controles por framework × {LGPD, SOX, ISO_27001} (máximo 15 rows; pode ser menos se `ComplianceControlLibrary` tiver menos itens), copiados filtrando por framework. Status inicial: `"not_started"` (valor real usado em `seed_service.py:1472` — não fingir que está implementado).

**Justificativa:** dashboard `admin/compliance/auditoria/bias` precisa de rows para renderizar; status honesto é `"not_started"` até auditoria humana avaliar cada controle.

### 5.6 `company_responsibilities` / `company_skills_catalog` / `behavioral_competencies_catalog`

Defaults: copiar `_DEMO_RESPONSIBILITIES` (5), `_DEMO_TECHNICAL_SKILLS` (6), `_DEMO_BEHAVIORAL_COMPETENCIES` (5) **renomeando rótulos genéricos**. Para skills técnicas, manter as 6 do demo (Python, SQL, React, AWS, Git, Docker — todas genéricas o suficiente para qualquer tenant tech-adjacent). Para tenants não-tech, o admin substitui via UI.

**Alternativa preferida:** disponibilizar **3 packs de skills baseline** (`tech`, `commercial`, `general`) escolhidos no onboarding pelo admin. Reduz ruído de skills irrelevantes no autocomplete.

### 5.7 `company_retention_policies`

**Default real (#813, hoje):** 1 row com `retention_months=24, auto_anonymize=False`. Esquema atual da tabela é flat (uma política única por tenant), não per-tipo.

**Gap vs lia-compliance §4 (recomendado):** o guia recomenda granularidade por tipo de dado:

| Tipo | Retenção (dias) | Status hoje |
|------|-----------------|-------------|
| Candidatos rejeitados | 90 | não modelado (única política de 24m cobre tudo) |
| Notas de entrevista / CVs | 180 | idem |
| Logs de screening | 365 | idem |
| Logs de IA | 365 | idem |
| Contratados — contrato | 2555 (7 anos) | idem |
| Contratados — CV | 365 | idem |

**Justificativa do default conservador atual (24m, opt-in):** LGPD Art. 16 exige base legal e prazo definido para retenção. O default `auto_anonymize=False` é opt-in deliberado — o sistema nunca apaga sem ação explícita do recrutador/DPO. Isso é **mais conservador** que apagar por engano, mas **menos aderente ao guia** que prevê per-tipo.

**Recomendação para implementação:** evoluir o schema para per-tipo (`CompanyRetentionPolicyByType`) numa tarefa separada (não bloqueia este contrato). Enquanto isso, manter a row única `retention_months=24, auto_anonymize=False` como default AUTO seguro.

### 5.8 `company_screening_questions`

Default: `DEFAULT_SCREENING_QUESTIONS` (banco baseline, não atrelado a vaga). Alimenta autocomplete na criação de `screening_questions` per-vaga.

---

## 6. Matriz de Política de Seeding

Para cada item do mínimo, definir **quando** o default é inserido:

- **AUTO** = inserido automaticamente na criação do tenant pelo provisioning. Sem perguntar.
- **ONBOARDING** = inserido durante wizard conversacional no primeiro acesso do admin. Pergunta-se ao admin.
- **MANUAL** = não inserido por default. Permanece como hint `info` até o admin completar via UI/chat.

| Item | AUTO | ONBOARDING | MANUAL | Trade-off |
|------|------|------------|--------|-----------|
| `company_profiles` row canônica | ✅ | — | — | É invariante do RLS — sem isso, nada roda |
| `company_profiles.name/industry/company_size` | placeholder | ✅ refinar | — | AUTO com placeholder evita hint bloqueante; ONBOARDING para qualidade |
| `company_profiles.website` | — | ✅ | ✅ | NULL preserva semântica de "offer scrape"; admin pode pular |
| `company_culture_profiles` (baseline neutro) | ✅ | ✅ refinar | — | AUTO silencia hint `info`; ONBOARDING calibra OCEAN/EVP |
| `company_benefits` (25 BR) | ✅ | ✅ revisar | — | AUTO porque lista é canônica do mercado; admin desativa irrelevantes |
| `company_hiring_policies` (assistant baseline) | ✅ | ✅ ajustar | — | AUTO conservador (Crença #12); ONBOARDING permite escalar autonomia |
| `company_compliance_controls` (15 rows `not_assessed`) | ✅ | — | ✅ avaliar | AUTO popula dashboard; avaliação humana é manual |
| `company_responsibilities` | — | ✅ pack | ✅ | ONBOARDING via pack escolhido (tech/commercial/general); MANUAL extensível |
| `company_skills_catalog` | — | ✅ pack | ✅ | Idem (3 packs baseline) |
| `behavioral_competencies_catalog` (5) | ✅ | ✅ revisar | — | AUTO baseline universal; ONBOARDING customiza pesos |
| `company_retention_policies` | ✅ | — | ✅ ajustar | AUTO porque LGPD exige existência; ajustes só com aprovação DPO |
| `company_screening_questions` (banco) | ✅ | — | ✅ | AUTO baseline; admin adiciona perguntas customizadas |
| `screening_questions` (por vaga) | — | — | ✅ | Sempre per-vaga via `suggest_screening_questions` no chat |

**Princípio orientador:** quanto mais um default toca **decisão sobre pessoa** (policy, screening, culture), mais a coluna ONBOARDING ganha peso — para o admin assumir responsabilidade pelo conteúdo. Defaults estruturais (retention, compliance controls) podem ser AUTO porque o admin valida depois sem mudar comportamento do agente.

---

## 7. Cross-Reference: WeDO Talent Guide v3.3 + lia-compliance

Toda decisão de default neste contrato é rastreável aos princípios do guia. Tabela de referência cruzada:

| Default / Decisão | Princípio | Referência |
|-------------------|-----------|------------|
| `name` placeholder ≠ string vazia | Crença #3 — Transparente e Explicável | Guia v3.3 §2 (linhas ~150) |
| `culture.confidence_score = 0.0` força ASK_USER | ConfidencePolicyService 3 níveis | lia-compliance §1, Guia v3.3 §10 |
| `automation_level = "assistant"` baseline | Crença #12 — Autonomia Progressiva | lia-compliance §1, Guia v3.3 §11 |
| `require_human_approval_for = [rejection, hire, salary_change]` | Inegociável #2 — Nenhuma rejeição automática sem review | lia-compliance §1 |
| `FairnessGuard.check()` obrigatório em policy/culture pré-persistência | Inegociável #3 — FairnessGuard ativo em 100% das decisões | lia-compliance §3 (3 camadas) |
| `pii_masking_enabled = true` baseline | Inegociável #4 — PII masking em todos os logs | lia-compliance §4, pilar 3 |
| `retention_policy` defaults derivam do guia | LGPD Art. 16 + lia-compliance §4 | Guia v3.3 PARTE V |
| `compliance_controls` status `not_assessed` (não fingir) | Crença #6 — Em Melhoria Contínua, sem dívida que comprometa fairness/segurança | Guia v3.3 §2 |
| Defaults nunca contêm PII de pessoa real | Crença #4 — Segura e Respeitosa com Privacidade + LGPD pilar 1 (consentimento) | lia-compliance §4 |
| Skills baseline genéricas (Python/SQL/React…), não favorecem instituição | DEI §4 (formação acadêmica é alto risco de viés) | lia-compliance §3 (Formação Acadêmica) |
| Sem fallback silencioso no seed (rollback + raise) | canonical-fix; Crença #8 — Observável e Rastreável | skill canonical-fix; Guia v3.3 §2 |
| Tenant-isolation (defaults copiados, não compartilhados) | RLS PostgreSQL; Inegociável de multi-tenancy | replit.md §System Architecture |

**Production Readiness Gate (lia-compliance §1.6):** este contrato endereça os critérios:
- #3 PII Masking ativo (defaults respeitam)
- #4 Rate Limiting (não afetado, ortogonal)
- #6 Token budget (defaults ok não geram chamadas LLM)
- #7 Consent management (defaults não criam dado de candidato — não há consent a obter)
- #8 FairnessGuard em interações (validação obrigatória de policy/culture)
- #16 LGPD checklist (retention defaults aderentes)

---

## 8. Próximas Tarefas Habilitadas

Este doc não cria tarefas — apenas as enumera para serem propostas ao usuário em ciclos futuros de Plan. Em ordem sugerida de prioridade:

1. **Generalizar `seed_demo_company_settings` para qualquer tenant**
   Renomear para `ensure_tenant_minimum_config(db, company_id, *, packs=("general",))` e remover hardcode de `DEMO_COMPANY_UUID`. Aceitar `company_id` arbitrário, validar que pertence a tenant existente, aplicar todos os defaults AUTO da matriz §6. Idempotente, com validação fairness obrigatória onde marcado `[FAIR]`. Plugar no provisioning de tenant.
   **Sub-decisão necessária antes de implementar:** como invocar `FairnessGuard.check()` em defaults estruturados — serializar campos textuais (mission, vision, values, evp_bullets, descrições de policy) e rodar `guard.check(text)` em cada um, OU criar interface estruturada (`check_policy_dict(policy: dict)` / `check_culture_profile(profile: dict)`) que internamente serializa e agrega resultados. Recomendação: começar com serialização textual (zero mudança de API), promover para interface estruturada se surgir necessidade de regras compostas.

2. **Wizard de onboarding conversacional**
   Implementar fluxo guiado no agente `company_settings` que percorre os itens ONBOARDING da §6 (refinamento de `company_profiles`, escolha de pack de skills, calibração de OCEAN, ajuste de `automation_level`). Cada confirmação atualiza `confidence_score` da row correspondente.

3. **Endpoint `POST /api/v1/admin/tenants/{id}/bootstrap-defaults`**
   Re-trigger manual do `ensure_tenant_minimum_config` para tenants já criados pré-spec. Idempotente. Retorna summary de tabelas tocadas (parecido com retorno atual de `seed_demo_company_settings`).

4. ~~**Fechar gaps `incomplete_company_profile` e `company_website_missing` no demo**~~ — **CONCLUÍDO na #819**
   Duas frentes complementares: (a) `_ensure_demo_company_profile` preenche `name/industry/company_size` na row canônica via `ON CONFLICT DO UPDATE` + `COALESCE/NULLIF` (idempotente, não sobrescreve dados de admin), com `RETURNING (xmax = 0)` para distinguir insert real de update; (b) `_check_company_profile_completeness` removeu `website` da query — o sinal fica exclusivamente em `company_website_missing` (hint #4), evitando duplicar o mesmo gap em duas hints. `website` permanece NULL deliberadamente (§5.1).

5. **Bias audit baseline pós-bootstrap** (Production Readiness #9)
   Após cada `ensure_tenant_minimum_config`, rodar `BiasAuditService.establish_baseline(company_id)` para que comparações de drift tenham referência inicial.

6. **Migrar `_DEMO_CULTURE_PROFILE` / `DEFAULT_BRAZILIAN_BENEFITS` / `HIRING_POLICY_DEFAULTS` para módulo único `app.shared.tenant_defaults`**
   Hoje os defaults ficam espalhados entre `seed_service.py` e `lia_models/*`. Centralizar simplifica auditoria e versionamento (cada default ganha `version: int` para tracking de qual baseline cada tenant tem).

7. **Documentar/aceitar a regra "vacancy_no_screening_questions é por-vaga"**
   Esclarecer no painel de criação de vaga que essa hint não é coberta pelo bootstrap — sempre roda no contexto de triagem. Pode virar um lint visual no editor de vaga.

---

## 9. Anexo — Glossário rápido

| Termo | Significado |
|-------|-------------|
| `DEMO_COMPANY_UUID` | `00000000-0000-4000-a000-000000000001` — tenant fixo de desenvolvimento, ver `app/core/tenant.py` |
| `_ONBOARDING_HINT_TYPES` | Set de 6 hints que o orquestrador considera para roteamento por severidade |
| `_BLOCKING_HINT_SEVERITIES` | `{"warning", "critical"}` — só esses sequestram a rota |
| `_COMPANY_SETTINGS_INTENTS` | Intents do classifier que delegam para `company_settings` independente de hints |
| `[FAIR]` | Default que precisa passar por `FairnessGuard.check()` antes de persistência |
| AUTO / ONBOARDING / MANUAL | Política de seeding (§6) |
| ASK_USER | Nível de `ConfidencePolicyService` que exige confirmação humana (`confidence < 0.70`) |
| `confidence_score` | Campo em culture/policy que controla comportamento de IA (0.0 = sempre perguntar) |

---

**Fim do contrato.** Este documento é a fonte da verdade para qualquer tarefa de seeding/bootstrap/onboarding de tenant. Mudanças neste contrato exigem nova spec, não edits ad-hoc.
