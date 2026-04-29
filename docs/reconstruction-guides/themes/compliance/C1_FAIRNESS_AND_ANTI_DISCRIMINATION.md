# Theme C1 — Fairness & Anti-Discrimination

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance) + cross-ref Card 1 (Persona)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit (caminhos confirmados via SSH)

---

## O que é este tema

Fairness na LIA é o conjunto de mecanismos que **bloqueia** (pré-LLM) e **monitora** (pós-LLM) decisões discriminatórias baseadas em atributos protegidos. Opera em 3 camadas sequenciais com fallback lenient, e é complementado por audit pós-deploy com a four-fifths rule (NYC LL144 + EEOC). É a camada mais crítica legalmente — falha aqui gera exposição a Lei 9.029/95, CLT Art. 373-A, LGPD Art. 20 e EU AI Act.

**Boundary com temas irmãos:**
- **C2 LGPD PII** — PII strip roda ANTES do FairnessGuard L3 (para não enviar dados pessoais ao Haiku). Aqui não cobrimos PII.
- **C3 LGPD Consent** — consentimento informado; não cobre bias.
- **C4 LGPD Art. 20** — direito de contestação de decisão automatizada; C1 cobre a decisão, C4 cobre a contestação.
- **C6 Prompt Injection** — defesa contra manipulação adversarial; diferente de fairness.
- **C7 Audit Trail** — log de decisões; C1 produz o log, C7 gerencia a infraestrutura de log.

---

## Arquivos conectados (22 total)

### Camada Persona (LLM vê — 9 arquivos)

YAMLs com texto que é injetado no prompt do LLM:

| Arquivo | Bundle | Como é injetado |
|---------|--------|-----------------|
| `compliance_block.yaml` (seções `decision.fairness`, `decision.bias`) | LIA_YAMLS_CANONICAL_BUNDLE §shared | `ComplianceDomainPrompt` injeta variante `decision` para agentes de decisão |
| `cv_screening.yaml` (seção `behavioral_rules`) | LIA_YAMLS §domains | Regra: "Nunca rejeitar sem verificar FairnessGuard primeiro" |
| `pipeline_transition.yaml` (`behavioral_rules` #5, 8) | LIA_YAMLS §domains | "Para rejeições: SEMPRE use check_rejection_fairness ANTES de responder" |
| `hiring_policy.yaml` (`counter_argumentation`) | LIA_YAMLS §domains | Cita Lei 9.029/95 em réplicas educativas; explicita que ação afirmativa é permitida |
| `autonomous.yaml` (`behavioral_rules`, após fix 2026-04-23) | LIA_YAMLS §domains | Fairness obrigatório em rejeições cross-domain; ref. Lei 9.029/95 + CLT 373-A + LGPD Art. 20 |
| `culture_analysis.yaml` (bloco `<compliance_hr>`, após fix 2026-04-23) | LIA_YAMLS §domains | Cultural fit não pode ser proxy para exclusão; scores Big Five não podem isolar decisão de contratação |
| `wsi_evaluation.yaml` | LIA_YAMLS §domains | FairnessGuard mandated antes de scoring final |
| `protected_attributes.yaml` (versão 6, 14 atributos) | COMPLIANCE_YAMLS_CANONICAL_BUNDLE | **SSoT legal** — nunca duplicar a lista em outros YAMLs |
| `fairness_post_check.yaml` | COMPLIANCE_YAMLS_CANONICAL_BUNDLE | Define 7 decision_domains + 6 score_fields + 5 ranking_fields monitorados pós-LLM |

### Camada Código (Python lê — 7 arquivos)

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `fairness_guard.py` | `app/shared/compliance/fairness_guard.py` (1278L) | **Núcleo.** 3 layers (L1 regex + L2 lexical + L3 semantic Haiku). Classe `FairnessGuard` com 12 métodos públicos |
| `fairness_guard_middleware.py` | `app/shared/compliance/fairness_guard_middleware.py` (194L) | Middleware reusável (FastAPI dependency) para checks em request/response |
| `bias_audit_service.py` | `app/shared/compliance/bias_audit_service.py` (525L) | **Pós-deploy audit.** Calcula adverse impact ratio + chi-square test + four-fifths rule. ⚠️ **DEPRECADO** desde 2026-04-17 (`@deprecated since=2026-04-17, @remove-after=2026-07-16`). Replacement: `integrations_hub/rails_adapter::bias_audit`. Manter ativo até migração Rails completar. |
| `protected_attributes.py` | `app/shared/compliance/protected_attributes.py` (105L) | Loader do YAML SSoT; expõe `PROTECTED_ATTRIBUTE_IDS`, `PROTECTED_DB_FIELDS`, `BIAS_AUDIT_DIMENSIONS`, `LEARNING_PROTECTED_FIELDS` |
| `scoring_safeguards.py` | `app/shared/compliance/scoring_safeguards.py` (163L) | Helpers que garantem FairnessGuard + AuditService em scoring services (cv_screening, lia_score, etc.) |
| `domain_validators.py` | `app/shared/compliance/domain_validators.py` (142L) | FactChecker domain-specific (ex.: `validate_cv_score_claim`) — evita alucinação de scores |
| `compliance_base.py` | `app/domains/compliance_base.py` (704L) | Classe `ComplianceDomainPrompt` + `StageContext` + `HiringStage` enum. **Todo domínio LIA DEVE herdar.** |

### Integration points

- **Decision agents** herdam de `ComplianceDomainPrompt` → chamam `pre_process()` antes do LLM (linha 275 de `compliance_base.py`)
- **`_DECISION_DOMAINS` frozenset** em `compliance_base.py` (linha 139) → define quais domínios recebem variante `decision` do compliance_block. Valor atual: `{"pipeline", "pipeline_transition", "cv_screening", "sourcing", "autonomous", "talent_pool", "recruiter_assistant"}`
- **Scoring services** (cv_screening, wsi_evaluation) chamam helpers de `scoring_safeguards.py`
- **FastAPI endpoints** podem usar `fairness_guard_middleware.py` como dependency
- **`_LEARNING_PROTECTED_FIELDS`** protege o learning loop (R2) de aprender padrões sobre atributos protegidos

---

## Lógica IN → OUT

### Input

```python
# Típico
text: str              # query do recrutador ou texto de decisão
action: str            # ex.: "rejection", "shortlist", "wsi_score" — direciona L3
context: str = ""      # contexto opcional (vaga, candidato)
company_id: str        # SEMPRE do JWT (via TenantGuard — ver C5)
```

### Processing (3 layers sequenciais)

**Constantes canônicas** (lidas de `fairness_guard.py`):
- `_PATTERNS_VERSION = 8` (v8: FASE 2 — mae solo hard block + socioeconômico + message improvements)
- `IMPLICIT_BIAS_TERMS` dict (43 termos PT-BR)
- `IMPLICIT_BIAS_TERMS_EN` dict (EN)
- `HIGH_IMPACT_ACTIONS` frozenset: `{"rejection", "shortlist", "wsi_score", "policy_save", "bulk_rejection", "sourcing_search", "jd_import", "pipeline_move", "analytics_query", "job_create", "job_edit", "bulk_automation", "policy_check", "diversity_check"}`

**L1 — Regex blocker** (`FairnessGuard.check()`, sempre roda)
- Normaliza texto via `_normalize_text()` (NFD + ASCII strip de acentos)
- Compila patterns em runtime via `_ensure_compiled()`
- Retorna `FairnessCheckResult(is_blocked=True, blocked_terms=[...], category=<str>, educational_message=<str>)` em match
- Categorias (19 total: 13 PT-BR + 6 EN)

**L2 — Lexical / Implicit bias** (`check_implicit_bias()`, sempre roda)
- Busca em `IMPLICIT_BIAS_TERMS` após normalização
- Retorna `list[str]` de `soft_warnings` (não bloqueia — educativo)
- Exemplos de termos: `"boa aparencia"`, `"bairros nobres"`, `"universidades de primeira linha"`, `"periferia"`, `"sem adaptacoes"`

**L3 — Semantic (Claude Haiku)** (`check_semantic()` + `check_with_layer3()`)
- Condicional: `FAIRNESS_LAYER3_ENABLED=true` AND `action ∈ HIGH_IMPACT_ACTIONS`
- Modelo pinned: `claude-haiku-4-5-20251001`
- Cache Redis 1h (key inclui hash do texto + context)
- Idioma detectado via `_detect_language()` (heurística ASCII) para escolher prompt correto
- **Fallback lenient**: se exceção (circuit breaker aberto, timeout, etc.) → retorna `is_blocked=False, confidence=0.5, soft_warnings=implicit_warnings` (preserva L1+L2)

**Roda antes do LLM do agente**: `pre_compliance()` em `ComplianceDomainPrompt` orquestra as 3 layers + PII strip (C2) + PromptInjection (C6) + FactCheck.

### Output

```python
@dataclass
class FairnessCheckResult:
    is_blocked: bool
    blocked_terms: list[str]
    category: str | None
    educational_message: str | None
    original_query: str = ""
    confidence: float = 0.0  # default 0.0 (verificado SSH 2026-04-24, linha 125)
    soft_warnings: list[str] = []

    @property
    def is_biased(self) -> bool: ...
```

**Side effects:**
- Sempre: `audit_service.log_decision(...)` (ver C7 para detalhes) com `criteria_used`, `score_breakdown`, `subject_id`, `timestamp`
- Se `is_blocked=True`: agente recusa ação + retorna `educational_message`
- Se `soft_warnings` populated: ação continua, warnings logados para análise semanal
- `fairness_audit_log` table (Alembic migration `015_add_fairness_audit_log.py`) recebe o registro

### Escalation / HITL

Cenários de escalação (definidos em `guardrails_block.yaml` seção `escalation` + triggers em `bias_audit_service.py`):

| Trigger | Ação | Responsável |
|---------|------|-------------|
| L1 bloqueou input do recrutador | Retorna `educational_message` + registra incidente | — (recrutador vê feedback) |
| Pattern sistêmico de rejeição por grupo (p-value < 0.05 + ratio < 0.80) | Alerta compliance team | Compliance team revisa |
| `risk_score > 0.8` em policy validation | `hiring_policy.yaml` → não salva política + notifica compliance | Compliance team |
| L3 falha 5× seguidas (circuit breaker abre) | Fallback lenient + alert para SRE | SRE / engenharia |
| Learning loop tenta aprender sobre atributo protegido | Bloqueio em `validate_learning_batch()` | Automático |

---

## 4/5 Rule / Disparate Impact Ratio (NYC LL144 + EEOC)

**Implementação canônica:** `bias_audit_service.py` funções `_adverse_impact_ratio()` (linha 241) e `_audit_dimension()` (linha 260).

**Threshold:** `FOUR_FIFTHS_THRESHOLD = 0.80` (constante).

**Cálculo:**
```python
# Simplificado de _adverse_impact_ratio
rates = [v["rate"] for v in groups.values() if v["count"] > 0]
if len(rates) < 2: return 1.0
max_rate = max(rates)
if max_rate == 0.0: return 1.0
return round(min(rates) / max_rate, 4)
```

**Interpretação:**
- ratio ≥ 0.80 AND chi-square p-value ≥ 0.05 → `eeoc_compliant=True`
- ratio < 0.80 → `alert_level="warning"` + `below_threshold=True`
- chi-square test via `_chi_square_test()` + `_chi_square_fallback()` (fallback se scipy não disponível — implementação própria de survival function)

**Dimensões auditadas** (de `BIAS_AUDIT_DIMENSIONS`, carregada de `protected_attributes.yaml`):
- Gênero, Raça/Etnia, Idade (grupo via `_age_group()` — buckets), Deficiência, + interseções opcionais

**Quando roda:**
- Em tempo real no ranking de candidatos (método `BiasAuditService.audit_ranking()`)
- Em relatórios periódicos (scheduled job em R4)
- Em bias audit externo (Q3/2026 — ver COMPLIANCE §11.3)

---

## Ação Afirmativa (Lei 8.213/91 + Lei 12.990/2014)

**Base legal:**
- **Lei 8.213/91 Art. 93** — cotas PCD: 2-5% (>100 funcionários)
- **Lei 12.990/2014** — cotas pretos e pardos em concursos federais (20%)
- **CLT Art. 373-A §2**: vaga afirmativa para mulher é permitida quando justificada (STEM, diretoria)
- **Lei 9.029/95** — prática discriminatória é proibida; **mas ação afirmativa NÃO é discriminação** (STF/STJ pacificado)

**Como a LIA trata:**
- `hiring_policy.yaml` seção `counter_argumentation`: orientação educativa sobre distinção entre discriminação (excluir grupo) vs. equidade (incluir grupo sub-representado)
- `intent_classification.yaml` detecta termos: `PCD`, `pessoa com deficiência`, `mulheres`, `negros`, `afrodescendentes`, `LGBTQIA+`, `50+`, `inclusiva`, `diversidade`, `ação afirmativa` → `is_afirmativa=true`, `criterio_afirmativo_primario=<critério>`
- Quando `is_afirmativa=true`, FairnessGuard **permite** filtros positivos pelos grupos reconhecidos (com audit log explícito)
- `compliance_block.yaml` seção `decision.fairness` lista: "AÇÃO AFIRMATIVA É PERMITIDA: Metas de diversidade PCD (Lei 8.213/91), pretos/pardos (Lei 12.990/2014), mulheres em STEM. Diferencie: discriminação (excluir grupo) ≠ equidade (incluir grupo sub-representado)"

---

## AffirmativeActionService — Verificação e Documentação de Ação Afirmativa

> ⚠️ **DEPRECADO** desde 2026-04-17 (`@deprecated since=2026-04-17, @remove-after=2026-07-16`). Replacement: `integrations_hub/rails_adapter::affirmative`. **Manter ativo até migração Rails completar** — candidatos podem ter documentos pendentes.

**Arquivo canônico:** `app/shared/services/affirmative_service.py` (375L)

Este serviço gerencia dois fluxos complementares de ação afirmativa:
1. **Verificação de elegibilidade** — avalia se candidato atende critérios da vaga afirmativa
2. **Gestão de documentação** — solicita, recebe e verifica documentos comprobatórios

### 8 Critérios afirmativos (`AFFIRMATIVE_CRITERIA`)

```python
AFFIRMATIVE_CRITERIA = {
    "gender":        {"label": "Gênero", "options": ["Mulheres", "Mulheres Negras", "Mulheres Trans"], "document_types": ["autodeclaracao"]},
    "race_ethnicity": {"label": "Raça/Etnia", "options": ["Pessoas Negras", "Pessoas Pardas", "Pessoas Pretas"], "document_types": ["autodeclaracao_racial"]},
    "disability":    {"label": "Pessoa com Deficiência (PcD)", "options": ["PcD - Física", "PcD - Visual", "PcD - Auditiva", "PcD - Intelectual", "PcD - Múltipla"], "document_types": ["laudo_pcd", "certificado_reabilitacao"]},
    "age":           {"label": "Idade 50+", "options": ["50+ anos"], "document_types": ["documento_identidade"]},
    "lgbtqia":       {"label": "LGBTQIA+", "options": ["LGBTQIA+"], "document_types": ["autodeclaracao"]},
    "refugee":       {"label": "Pessoa Refugiada", "options": ["Refugiados", "Solicitantes de Refúgio"], "document_types": ["documento_refugio", "protocolo_conare"]},
    "indigenous":    {"label": "Pessoa Indígena", "options": ["Indígenas"], "document_types": ["autodeclaracao_indigena", "rani"]},
    "other":         {"label": "Outro", "options": ["Outro grupo minorizado"], "document_types": ["autodeclaracao"]},
}
DOCUMENT_UPLOAD_DEADLINE_HOURS = 24
```

### Mapeamento de campos do candidato por critério

```python
check_map = {
    "gender":        lambda c: c.gender and c.gender.lower() in ["feminino", "mulher", "female", "trans"],
    "race_ethnicity": lambda c: c.diversity_race_ethnicity in ["black", "brown", "preta", "parda", "negra"],
    "disability":    lambda c: c.diversity_disability,
    "age":           lambda c: c.diversity_age_50_plus,
    "lgbtqia":       lambda c: c.diversity_lgbtqia,
    "refugee":       lambda c: c.diversity_refugee,
    "indigenous":    lambda c: c.diversity_indigenous,
    "other":         lambda c: True,  # candidato autodeclara
}
```

### Métodos principais

| Método | Retorno | Descrição |
|--------|---------|-----------|
| `get_criteria_options()` | `dict` | Lista todos os 8 critérios + opções |
| `check_candidate_eligibility(candidate, vacancy)` | `dict` | Verifica elegibilidade + quais docs são necessários |
| `create_document_request(candidate_id, vacancy_id, company_id, criteria_type)` | `CandidateAffirmativeDocument` | Cria solicitação com prazo de 24h |
| `upload_document(document_id, url, filename, doc_type)` | `CandidateAffirmativeDocument` | Registra upload |
| `verify_document_lia(document_id, verification_result)` | `CandidateAffirmativeDocument` | Verificação automática por LIA |
| `verify_document_recruiter(document_id, recruiter_email, approved, notes)` | `CandidateAffirmativeDocument` | Aprovação manual pelo recrutador |
| `get_pending_documents(company_id, vacancy_id)` | `list[dict]` | Documentos aguardando verificação |
| `check_expired_documents(company_id)` | `int` | Marca expirados + retorna contagem |

### 7 Endpoints API (`app/api/v1/affirmative.py`)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/affirmative/criteria` | Lista critérios e opções |
| `POST` | `/affirmative/check-eligibility` | Verifica elegibilidade |
| `GET` | `/affirmative/pending-documents/{company_id}` | Documentos pendentes |
| `POST` | `/affirmative/documents/request` | Solicita documento |
| `POST` | `/affirmative/documents/verify-lia` | Verificação automática |
| `POST` | `/affirmative/documents/verify-recruiter` | Aprovação manual |
| `POST` | `/affirmative/check-expired/{company_id}` | Expira documentos vencidos |

### Modelos de dados

**`AffirmativeAuditLog` (tabela `affirmative_audit_logs`):**
- `id`, `company_id`, `vacancy_id`, `candidate_id` — multi-tenant + referências
- `action` (String 100), `criteria_checked` (JSON), `result` (bool nullable), `reason` (Text)
- `performed_by`, `performed_by_type` ("system" default), `action_metadata` (JSON)
- `created_at` indexado

**`CandidateAffirmativeDocument`:**
- Lifecycle: criação → upload → verificação LIA → verificação recrutador
- `status`, `upload_deadline`, `is_expired`, `uploaded_at`
- `verified_by_lia`, `lia_verification_result`, `lia_verified_at`
- `verified_by_recruiter`, `recruiter_email`, `recruiter_notes`, `recruiter_verified_at`

### Integração com FairnessGuard

O `AffirmativeActionService` **não importa** `FairnessGuard` diretamente. A integração é indireta:
- `check_candidate_eligibility()` retorna `{"eligible": bool, "requires_document": bool, "document_types": [...]}` — callers (agentes/routers) são responsáveis por encaminhar ao FairnessGuard
- `_log_action()` alimenta `AffirmativeAuditLog` que é consumido pelo `BiasAuditService` nos relatórios de fairness

---

## Cultural Fit como Proxy de Viés

**Risco documentado:**
- "Cultural fit" mal definido = proxy para discriminação etária, classista, racial ou de gênero
- `compliance_block.yaml` seção `decision.bias` menciona explicitamente: `"Cultural fit" → pode mascarar preferência por perfil homogêneo`
- `culture_analysis.yaml` bloco `<compliance_hr>` (injetado após fix 2026-04-23) proíbe usar Big Five como critério isolado de rejeição

**Mitigação na LIA:**
1. Scores Big Five (openness, conscientiousness, etc.) são **informativos**, nunca eliminatórios
2. Pesos configurados via `CalibrationWeight` (per tenant) — default 70% técnico / 30% comportamental
3. `behavioral_rules` em `culture_analysis.yaml`: "Inference over LLM para proxy demográfico é proibida"
4. Audit log captura `criteria_used` → se "cultural_fit" domina rejeições, trigger compliance review

---

## Bias Audit: Pre-deploy vs Post-deploy

**Pre-deploy** (antes de ativar agente novo):
- Bias probes em `tests/eval/bias_probes/pairs.yaml` (ver O1 Testing)
- Adversarial scenarios em `tests/eval/datasets/adversarial/attack_scenarios.yaml`
- Red team tests em `tests/security/test_red_team_*`

**Post-deploy** (runtime contínuo):
- `fairness_post_check.yaml` monitora 7 decision_domains + 6 score_fields + 5 ranking_fields
- `BiasAuditService` roda em cron job (R4) sobre `fairness_audit_log`
- Alertas quando `below_threshold=True` por 3 ciclos consecutivos
- Relatório trimestral para compliance team

**Externo** (auditor independente — planejado Q3/2026):
- Modelo Eightfold (BABL AI): auditor lê dados anonimizados + atesta four-fifths rule
- Output: PDF público + site (modelo `responsible-ai/bias-audit-2026.html`)
- Ver COMPLIANCE §11.3 para plano de 3 sprints

---

## Instruções para Claude Code / Cursor

### "Implementa fairness no v5"

```
1. COPIE os 2 YAMLs SSoT (verbatim, sem alteração):
   - protected_attributes.yaml → <v5>/config/
   - fairness_post_check.yaml → <v5>/config/

2. IMPLEMENTE 7 arquivos Python (copiar de LIA com adaptação mínima):
   - fairness_guard.py  → core das 3 layers
   - fairness_guard_middleware.py → decorator FastAPI
   - bias_audit_service.py → adverse impact ratio + chi-square
   - protected_attributes.py → loader YAML + constants
   - scoring_safeguards.py → helpers para scoring services
   - domain_validators.py → fact-checking por domínio
   - compliance_base.py → ComplianceDomainPrompt + StageContext

3. CRIE Alembic migration para `fairness_audit_log`
   (copiar schema de `alembic/versions/015_add_fairness_audit_log.py`)

4. CONFIGURE .env:
   - FAIRNESS_LAYER3_ENABLED=true (prod) / false (dev)
   - ANTHROPIC_API_KEY=<key> (para L3)
   - REDIS_URL=<url> (cache L3 1h)

5. GARANTA que todo agente de decisão:
   - Herda de ComplianceDomainPrompt (não de DomainPrompt direto)
   - Chama `await self.pre_process(input)` ANTES de invocar LLM (método em compliance_base.py:275)
   - O domínio aparece em `_DECISION_DOMAINS` frozenset (compliance_base.py:139)

6. TESTE:
   - pytest tests/test_fairness_guard_l1.py (19 regex patterns)
   - pytest tests/test_fairness_guard_l2.py (43 lexical terms)
   - pytest tests/test_fairness_guard_l3_flag_on.py
   - pytest tests/test_bias_audit_four_fifths.py
   - pytest tests/integration/test_cv_screening_fairness_gate.py
```

### "Adiciona fairness a uma feature nova"

```
1. Se feature produz decisão sobre candidato:
   a. Herda de ComplianceDomainPrompt no agent class
   b. Adiciona o domain_id ao `_DECISION_DOMAINS` frozenset em compliance_base.py:139
   c. Adiciona entry no agent_prompts.yaml com seção fairness_rules

2. Se feature chama scoring:
   a. Import helpers de scoring_safeguards.py:
      from app.shared.compliance.scoring_safeguards import (
          run_fairness_guard, audit_scoring_decision
      )
   b. Sempre: audit_scoring_decision(..., criteria_used=[...])

3. Se feature usa HIGH_IMPACT action (rejection, shortlist, etc.):
   a. Adiciona o action em HIGH_IMPACT_ACTIONS frozenset
   b. L3 semântico será acionado automaticamente (se flag on)
```

### Setup em CLAUDE.md

```markdown
## Compliance: Fairness

Este repo implementa 3 camadas de fairness (L1 regex + L2 lexical + L3 semantic).
Ao modificar código relacionado:

- **Decision agents** DEVEM herdar de `ComplianceDomainPrompt`
- **Scoring services** DEVEM usar helpers de `scoring_safeguards.py`
- **14 atributos protegidos** são SSoT em `protected_attributes.yaml` — NÃO duplicar
- **4/5 rule** via `bias_audit_service._adverse_impact_ratio()` — threshold 0.80
- **Ação afirmativa** permitida quando `is_afirmativa=true` (Lei 8.213/91, 12.990/2014)
- **FAIRNESS_LAYER3_ENABLED=true** em prod; fallback lenient se API falhar

Consultar `themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md` antes de replicar ou adicionar fairness a uma feature nova.
```

### Setup em `.cursor/rules/fairness.mdc`

```
---
description: "C1 Fairness & Anti-Discrimination — LIA compliance layer"
alwaysApply: false
---

Quando o usuário pedir para implementar/modificar/auditar fairness, bias, atributos protegidos,
disparate impact, ou cultural fit como critério:

1. Leia themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md completo
2. Leia os 9 YAMLs referenciados em LIA_YAMLS_CANONICAL_BUNDLE + COMPLIANCE_YAMLS_CANONICAL_BUNDLE
3. Leia os 7 arquivos Python de app/shared/compliance/ + app/domains/compliance_base.py
4. SEMPRE referenciar protected_attributes.yaml (SSoT dos 14 atributos)
5. NUNCA sugerir atributo protegido como critério de scoring ou filtro
6. Ação afirmativa é permitida — não confundir com discriminação
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- **Class names** (`FairnessGuard` pode virar `FairnessService`, `ComplianceDomainPrompt` pode virar `ComplianceBaseAgent`)
- **Paths de arquivo** (se v5 usa `src/compliance/` em vez de `app/shared/compliance/`)
- **Backend de cache** (se sem Redis, usar in-memory ou desabilitar cache L3)
- **Provider de LLM no L3** (pode trocar `claude-haiku-4-5-20251001` por OpenAI/Azure, desde que preserve prompt)
- **Linguagem de mensagens educativas** (adaptar para o idioma do mercado)
- **Estrutura de dataclasses** (pode usar Pydantic BaseModel em vez de `@dataclass`)
- **Número de arquivos** (pode consolidar tudo em 2-3 módulos se preferir; o importante é preservar as 3 layers)

### NÃO pode adaptar (base legal ou arquitetural)

| Invariante | Por quê | Consequência se violar |
|-----------|---------|------------------------|
| 14 atributos protegidos | Lista derivada de Lei 9.029/95 + CLT 373-A + LGPD Art. 11 | Exposição legal direta |
| Bloqueio de L1 (`is_blocked=True`) quando match | Obrigação legal (Lei 9.029/95) | Permitir discriminação explícita |
| Four-fifths rule threshold = 0.80 | NYC Local Law 144 + EEOC | Não conformidade NYC |
| Audit log completo em cada decisão | LGPD Art. 20 + EU AI Act Art. 12 | Decisão não contestável |
| `company_id` do JWT, nunca do payload | LGPD Art. 6 minimização + isolamento tenant | Vazamento entre tenants |
| Ação afirmativa é permitida (Lei 8.213/91, 12.990/2014) | Direito constitucional + legislação específica | Bloquear diversity hire = violação |
| Formato de `educational_message` (cita lei aplicável) | Requisito de transparência regulatória | Decisão arbitrária |
| L1+L2 rodam sempre; L3 é condicional | Se L3 falhar, L1+L2 são última linha de defesa | Bypass completo se L3 for único gate |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `protected_attributes.yaml` com 14 atributos presente e na versão 6+
- [ ] **(P0)** `FairnessGuard.check()` bloqueia input antes de chegar ao LLM para agentes de decisão
- [ ] **(P0)** `ComplianceDomainPrompt` é a classe base de todo decision agent (não `DomainPrompt`)
- [ ] **(P0)** `audit_service.log_decision()` rodando em cada decisão (com `criteria_used`, `criteria_ignored`)
- [ ] **(P0)** `fairness_audit_log` table criada via Alembic migration
- [ ] **(P0)** `_LEARNING_PROTECTED_FIELDS` bloqueia learning loop de aprender sobre atributo protegido
- [ ] **(P1)** L3 (Haiku) ativado via `FAIRNESS_LAYER3_ENABLED=true` em produção
- [ ] **(P1)** Cache Redis L3 com TTL 1h configurado
- [ ] **(P1)** `BiasAuditService` calcula four-fifths rule (threshold 0.80)
- [ ] **(P1)** Chi-square test implementado (fallback próprio se scipy indisponível)
- [ ] **(P1)** `HIGH_IMPACT_ACTIONS` frozenset inclui todas as ações críticas do produto
- [ ] **(P1)** `IMPLICIT_BIAS_TERMS` em PT-BR + EN traduzidos para idiomas do mercado
- [ ] **(P2)** `INTERVIEW_BIAS_INDICATORS` detecta viés em transcrições de entrevista
- [ ] **(P2)** `apply_inclusive_language()` sugere reescrita inclusiva
- [ ] **(P2)** Scripts de lint: `check_c3b_compliance.py`, `check_fairness_consolidation.py` rodando em CI

---

## Gotchas e erros comuns

| Sintoma | Causa raiz | Como evitar |
|---------|-----------|-------------|
| "FairnessGuard blocks legitimate recruitment query" | Regex muito amplo capturou termo contextual (ex.: "sênior" pode pegar "idade") | Revisar categoria e adicionar `exclusions` no match |
| "Cache hit rate baixo em L3" | Key de cache inclui timestamp ou dado volátil | Key deve ser hash(text + context + action) apenas |
| "Ação afirmativa sendo bloqueada como discriminação" | Intent classifier não detectou `is_afirmativa=true` | Adicionar termos novos em `intent_classification.yaml` + atualizar `capabilities.yaml` do hiring_policy |
| "Learning loop aprendeu padrão sobre gênero" | `_LEARNING_PROTECTED_FIELDS` não foi checado antes de salvar | Sempre passar batch por `validate_learning_batch()` antes de aplicar |
| "Chi-square retorna nan" | Fallback próprio de gammainc overflow em grupos muito grandes | Usar scipy quando disponível (`_chi_square_test` tem try/except); ou cap em 10k samples |
| "L3 roda em todo request, custo explode" | `FAIRNESS_LAYER3_ENABLED=true` sem respeitar `HIGH_IMPACT_ACTIONS` | Verificar que `action` é passado corretamente em `check_with_layer3()` |
| "FairnessGuard não roda em feature nova" | Agent herda de `DomainPrompt` em vez de `ComplianceDomainPrompt` | Adicionar lint em CI: `scripts/check_c3b_compliance.py` |
| "Audit log falha silenciosamente" | `scoring_safeguards` é tolerante a falhas de audit (não bloqueia flow) | OK por design; monitorar logs de erro de audit separadamente |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| L1 regex completo | `tests/unit/test_fairness_guard_l1.py` | 19 categorias × amostras positivas e negativas |
| L2 lexical | `tests/unit/test_fairness_guard_l2.py` | 43 termos PT-BR + EN equivalentes |
| L3 flag on | `tests/unit/test_fairness_guard_l3_flag_on.py` | Mock Haiku + assert que é chamado em HIGH_IMPACT |
| L3 flag off | `tests/unit/test_fairness_guard_l3_flag_off.py` | Assert que Haiku NÃO é chamado |
| L3 circuit breaker aberto | `tests/unit/test_fairness_guard_l3_fallback.py` | Exception → retorna `is_blocked=False, confidence=0.5` |
| Four-fifths rule | `tests/unit/test_bias_audit_four_fifths.py` | Grupos conhecidos → ratio esperado |
| Chi-square | `tests/unit/test_bias_audit_chi_square.py` | Tabela de contingência conhecida → p-value esperado |
| Learning batch validation | `tests/unit/test_fairness_learning_guard.py` | Batch com atributo protegido → `is_clean=False` |
| Integration CV screening | `tests/integration/test_cv_screening_fairness_gate.py` | Rejeição com termo discriminatório → educational_message retornado |
| Persona invariants | `tests/integration/test_persona_invariants.py` | Decision agent sem `ComplianceDomainPrompt` → teste falha |
| Bias probes | `tests/eval/bias_probes/pairs.yaml` | Pares adversariais (mesmo CV com atributo trocado) — scoring deve ser equivalente |

---

## Referências

### Bundles verbatim
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 2 (cv_screening, pipeline_transition, hiring_policy, autonomous, culture_analysis, wsi_evaluation)
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 1 (compliance_block.yaml)
- `COMPLIANCE_YAMLS_CANONICAL_BUNDLE.md` (protected_attributes.yaml + fairness_post_check.yaml)

### Reconstruction guides
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.2 (arquitetura 8 camadas C1-C8) — Fairness é C1+C2+C3 do modelo 8-layer
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.3 (matriz de cobertura por domain YAML)
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.1 (plano de ação P0/P1)

### Handoff dev
- `COMPLIANCE_DEV_HANDOFF_2026-04-23.md` — invariantes 1-6

### Runbook operacional
- `docs/operations/FAIRNESS_LAYER3_RUNBOOK.md` — ativação Layer 3 + métricas + rollback

### Regulatório
- **Lei 9.029/95** — proibição de discriminação em relações de trabalho
- **CLT Art. 373-A** — discriminação de gênero proibida; §2 permite vaga afirmativa justificada
- **Lei 8.213/91 Art. 93** — cotas PCD
- **Lei 12.990/2014** — cotas pretos e pardos em concursos federais
- **LGPD Lei 13.709/2018 Art. 11** — dados sensíveis; **Art. 20** — direito de revisão
- **EU AI Act** Art. 10 (data governance), Art. 14 (human oversight), Art. 15 (accuracy/robustness)
- **NYC Local Law 144** — four-fifths rule obrigatória desde 05/07/2023
- **EEOC Uniform Guidelines on Employee Selection Procedures** — origem da four-fifths rule
- **eu-ai-act-technical-documentation-pt.md** §6 — métricas consolidadas

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit em `lia-agent-system/`*
