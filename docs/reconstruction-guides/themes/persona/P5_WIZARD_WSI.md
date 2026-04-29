# Theme P5 — Wizard WSI: Criação de Vaga — Persona Layer

**Layer:** Persona  |  **Última verificação de código:** 2026-04-24
**Fontes:** `app/domains/job_creation/` (13 arquivos, 3898 linhas)

---

## O que é este tema

O **Wizard WSI** é o domínio de **criação conversacional de vagas** da LIA. Um recrutador conversa com a LIA que, internamente, executa um **grafo LangGraph de 11 nós** para enriquecer a descrição da vaga, extrair competências Big Five, gerar perguntas de triagem WSI validadas e publicar a vaga no ATS (Rails API).

O nome "WSI" no contexto do wizard refere-se às **fases F1-F6 da metodologia de geração de perguntas** (Workplace Skills Index) — distinto do scoring WSI de candidatos (que é o domínio `cv_screening`). O wizard **gera** perguntas; o cv_screening **aplica e pontua** as respostas.

**Dois HITL (Human-in-the-Loop) obrigatórios:**
1. **Ponto 1 — `jd_enrichment`:** recrutador aprova a JD enriquecida antes de continuar
2. **Ponto 2 — `wsi_questions`:** recrutador aprova (ou pede regeneração de) cada pergunta WSI

**Feature flag:** `is_wizard_enabled(workspace_id)` com gradual rollout por workspace (`ENABLE_UNIFIED_WIZARD` env var → per-workspace override → rollout% → False).

**Boundary com temas irmãos:**
- **I12 Voice Screening** — consome perguntas WSI geradas neste wizard via `wsi_repository`
- **C1 Fairness** — FairnessGuard é chamada em **7 gates** ao longo do grafo
- **C2 LGPD PII** — `mask_pii_for_llm()` aplicado antes de F1, F2 e F6
- **C7 Audit Trail** — 1 `log_decision(decision_type="job_creation")` por run via `AuditService`
- **I3 Orchestration** — domínio `job_creation` roteado pelo Orchestrator via `capabilities.yaml`
- **O3 External Integrations** — `JobCreationAPIClient` chama Rails API (create/publish/screening_config)

---

## Arquivos conectados (13 total)

### Camada Persona (LLM vê — 0 YAMLs de produção)

O domínio `job_creation` **não consome YAMLs de prompt diretamente**. Os prompts de F1, F2 e F6 são construídos inline em Python:
- `_build_enrichment_prompt()` em `jd_enrichment.py`
- `_build_bigfive_prompt()` em `wsi_question_generator.py`
- `_build_questions_prompt()` em `wsi_question_generator.py`

**Exceção:** existe YAML de experimento A/B:
```yaml
# app/prompts/experiments/job_wizard_field_extraction.yaml
experiment_id: "job_wizard_field_extraction"
variants:
  - variant_id: "control"      # weight: 0.5
  - variant_id: "treatment_structured"  # weight: 0.5 (tabular com normalização)
```

### Camada Código (13 arquivos Python)

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|--------------|:---:|-----------------|
| `graph.py` | `app/domains/job_creation/graph.py` | 1348 | LangGraph: 11 nós, 7 routers, HITL, singleton + checkpointer |
| `domain.py` | `app/domains/job_creation/domain.py` | 724 | `JobCreationDomain`: entry point, 11 actions, routing por `current_stage` |
| `wsi_question_generator.py` | `app/domains/job_creation/services/wsi_question_generator.py` | 483 | F2 Big Five, F3 trait ranking, F6 question generation |
| `jd_enrichment.py` | `app/domains/job_creation/services/jd_enrichment.py` | 288 | F1: enriquecimento + quality score + FairnessGuard |
| `compliance.py` | `app/domains/job_creation/compliance.py` | 236 | PII mask, FairnessGuard wrapper, audit emission |
| `api_client.py` | `app/domains/job_creation/api_client.py` | 206 | HTTP client Rails API (jobs + screening config + calibration) |
| `state.py` | `app/domains/job_creation/state.py` | 221 | `JobCreationState` TypedDict acumulativo |
| `schemas.py` | `app/domains/job_creation/schemas.py` | 117 | Pydantic: EnrichedJobDescription, BigFiveExtraction, GeneratedQuestion |
| `feature_flag.py` | `app/domains/job_creation/feature_flag.py` | 86 | Feature flag B.6 com rollout% |
| `file_router.py` | `app/domains/job_creation/services/file_router.py` | 173 | SmartFileRouter: classifica uploads CV/JD/generic |
| `actions/__init__.py` | `app/domains/job_creation/actions/__init__.py` | 6 | — |
| `services/__init__.py` | `app/domains/job_creation/services/__init__.py` | 1 | — |
| `__init__.py` | `app/domains/job_creation/__init__.py` | 9 | Registra `JobCreationDomain` no registry |

### Integration points

- **C1 Fairness** → `FairnessGuard().check(text)` via `compliance.py` em 7 gates
- **C2 LGPD PII** → `strip_pii_for_llm_prompt()` via `compliance.py` antes de F1, F2, F6
- **C7 Audit** → `AuditService.log_decision(decision_type="job_creation")` em `handoff_node`
- **R1 Circuit Breakers** → 4 circuit keys: `job_creation:jd_enrichment`, `job_creation:wsi_technical`, `job_creation:wsi_behavioral`, `job_creation:publish`
- **I3 Orchestration** → `JobCreationDomain` registrado via `@register_domain`; `process_intent()` faz keyword match
- **I9 Data Layer** → `wsi_questions`, `wsi_sessions`, `job_vacancies` (via Rails API)
- **O3 External** → `JobCreationAPIClient` para Rails: `POST /api/v1/jobs`, `POST .../publish`, `POST .../screening_config`
- **cv_screening** → `seniority_resolver.resolve_seniority_full()` em `competency_node` (único acoplamento direto)

---

## Lógica IN → OUT

### Input (via WebSocket conversacional)

```json
// WS message para agent_chat_ws.py
{
    "type": "message",
    "content": "Preciso criar uma vaga de Engenheiro de Software Sênior",
    "context": {
        "workspace_id": "empresa-123",  // do JWT / session
        "auth_token": "Bearer ..."      // para JobCreationAPIClient
    },
    "domain": "wizard"                  // ou "job_creation"
}
```

O wizard não tem rotas REST próprias — é acionado via WebSocket através do `agent_chat_ws.py` com `panel_type: "job_creation"`.

### Processing — Fluxo de 11 Nós

```
intake
  └─► jd_enrichment [HITL 1]
        ├── FairnessGuard pre (input do recrutador)
        ├── PII mask → JdEnrichmentService (LLM temp=0.3, max_tokens=4000)
        ├── FairnessGuard post (output do LLM)
        └── Quality Score F1.B:
              D3: ≥9 skills → 30pts | D4: ≥5 comportamentais → 25pts
              D5: ≥5 responsabilidades → 20pts | about_role → 10pts
              context_signals completo → 10pts | fairness corrections → 5pts bonus
              < 30: BLOCKED | 30-49: warning | ≥ 50: OK

  route_after_jd:
    fairness_blocked → END(error)
    approved=None   → END(aguarda recrutador)
    approved=False  → intake(loop)
    quality < 30    → END(blocked)
    approved + quality ≥ 50 ──►

bigfive [F2+F3]
  ├── FairnessGuard pre + post
  ├── BigFiveExtraction via LLM (temp=0.1)
  └── rank_traits: score = 0.40*LLM + 0.35*ONET_PRIOR + 0.25*seniority_boost

salary
  └── passa faixa salarial para ws_stage_payload

competency [F4+F5]
  ├── resolve_seniority_full() (5 sinais: JD + recrutador + O*NET + histórico + cargo)
  └── tabelas determinísticas:
        compact (7q): junior/pleno 5T+2B | senior/lead 4T+3B | diretor 3T+4B
        full (12q):   junior/pleno 9T+3B | senior/lead 7T+5B | diretor 7T+5B

  route_after_competency:
    sem screening_mode → END(aguarda)
    tem mode ──►

wsi_questions [F6 — HITL 2]
  ├── FairnessGuard pre (JD enriquecida)
  ├── PII mask → WSIQuestionGenerator
  │     tech (temp=0.7) + behav (temp=0.75)
  ├── FairnessGuard per-question (rejeita hipotéticas + cultural fit)
  └── wsi_dropped_questions: perguntas bloqueadas com motivo

  route_after_questions:
    all blocked → END(sem perguntas para aprovar)
    approved=None   → END(aguarda recrutador)
    approved=False  → wsi_questions(regenera)
    approved=True ──►

eligibility
  └── perguntas eliminatórias sim/não

review
  ├── _build_readiness_check: jd_approved + questions_approved + has_questions + quality≥50
  └── carrega company defaults via Rails API (/workspaces/{id}/recruitment_config)

  route_after_review:
    not ready → END
    ready ──►

publish [circuit_breaker="job_creation:publish"]
  1. JobCreationAPIClient.create_job(job_data)       → POST /api/v1/jobs
  2. JobCreationAPIClient.save_screening_config(...)  → POST /api/v1/jobs/{id}/screening_config
  3. JobCreationAPIClient.publish_job(...)            → POST /api/v1/jobs/{id}/publish
  4. JobCreationAPIClient.get_share_link(job_id)      → GET /api/v1/jobs/{id}/share_link

calibration
  └── GET /api/v1/jobs/{id}/calibration_candidates (limit=5)
      conta aprovados vs threshold (3+) → calibration_complete

handoff
  └── emit_job_creation_audit() (background thread, timeout=5s, fail-open) → END
```

### Output

```python
# ws_stage_payload a cada nó (enviado ao frontend via WebSocket):
{
    "ws_payload": {
        "stage": "jd_enrichment",      # nó atual
        "completeness": 0.18,          # idx / (len(STAGE_ORDER) - 1)
        "requires_approval": True,     # True nos HITL stages
        "data": { ... }                # output específico do nó
    }
}

# Após handoff (final):
{
    "job_id": int,          # Rails job ID
    "share_link": str,      # URL pública da vaga
    "completeness": 1.0,
    "stage": "done"
}
```

### Escalation / HITL

- **HITL 1 — `jd_enrichment`:** `jd_approved = None` → retorna controle ao frontend. Recrutador decide via `approve_jd` action. Se `approved=False`, loop para `intake`.
- **HITL 2 — `wsi_questions`:** `questions_approved = None` → retorna controle. Recrutador decide via `approve_questions` action (pode passar `edited_questions` para substituir perguntas individuais). Se `approved=False`, regenera.
- **FairnessGuard bloqueia input:** `educational_message` em PT-BR enviado ao recrutador com explicação do que foi bloqueado.

---

## Componentes Críticos

### JobCreationState — TypedDict Acumulativo

```python
# app/domains/job_creation/state.py
class JobCreationState(TypedDict, total=False):
    # Session
    session_id, user_id, workspace_id: str
    auth_token: str          # para JobCreationAPIClient

    # Progress
    current_stage: WizardStage   # "intake"|"jd_enrichment"|...|"done"
    stage_history: List[WizardStage]
    completeness: float      # idx / (len(STAGE_ORDER) - 1)
    requires_approval: bool
    ws_stage_payload: Optional[Dict]

    # F1 HITL
    jd_approved: Optional[bool]       # None=aguardando, True=aprovado, False=rejeitado
    jd_quality_score: float            # ≥50 para prosseguir
    jd_fairness_blocked: bool
    fairness_blocked_terms: List[str]

    # F6 HITL
    questions_approved: Optional[bool]
    wsi_questions: List[ScreeningQuestion]
    wsi_dropped_questions: List[Dict]  # perguntas removidas pela FairnessGuard

    # Publish
    job_id: Optional[int]    # Rails job ID
    share_link: Optional[str]

    # Compliance
    readiness_check: Optional[Dict]
    company_defaults_applied: List[str]

STAGE_ORDER = ["intake","jd_enrichment","bigfive","salary","competency",
               "wsi_questions","eligibility","review","publish","calibration","handoff","done"]
HITL_STAGES = {"jd_enrichment", "wsi_questions"}
```

### JdEnrichmentService — Schemas de Output

```python
# app/domains/job_creation/schemas.py
class EnrichedJobDescription(BaseModel):
    titulo_padronizado: str
    senioridade_confirmada: str     # enum de seniority
    about_role: str
    responsabilidades: List[str]
    skills_obrigatorias: List[TechnicalSkill]
    competencias_comportamentais: List[BehavioralCompetency]
    context_signals: ContextSignals     # nivel_autonomia/inovacao/pressao/colaboracao
    fairness_corrections: List[str]     # linguagem inclusiva aplicada
    wsi_quality_score: float            # F1.B score 0-100

class TechnicalSkill(BaseModel):
    skill: str
    contexto: str
    proficiency_level: str
    market_demand_trend: str

class BehavioralCompetency(BaseModel):
    competencia: str
    contexto: str
    trait_big_five: TraitOCEAN     # O/C/E/A/N enum

class ContextSignals(BaseModel):
    nivel_autonomia: float    # 0.0-1.0
    nivel_inovacao: float
    nivel_pressao: float
    nivel_colaboracao: float
```

### WSIQuestionGenerator — Schema de Output

```python
class GeneratedQuestion(BaseModel):
    question: str
    ideal_answer: str
    scoring_rubric: Dict[str, str]    # {"1-3": "...", "4-6": "...", "7-9": "...", "10": "..."}
    framework: str                    # "CBI" | "Bloom" | "Dreyfus" | "BigFive"
    block: str                        # "technical" | "behavioral"
    skill: str
    trait_ocean: Optional[TraitOCEAN]
    bloom_level: Optional[str]        # Remembering → Creating
    dreyfus_level: Optional[str]      # Novice → Expert
    weight: float                     # 0.0-1.0, soma por bloco = 1.0
```

### WSI Question Validation

```python
# app/domains/job_creation/services/wsi_question_generator.py
def _validate_question(q: GeneratedQuestion) -> bool:
    # Rejeita hipotéticas (CBI regra):
    HYPOTHETICAL_PATTERNS = ["o que você faria se", "imagine que", "what would you do",
                              "se você estivesse", "supondo que", "caso você"]
    # Rejeita cultural fit:
    CULTURAL_FIT_PATTERNS = ["fit cultural", "valores da empresa", "cultura da empresa",
                              "se encaixa no time", "nosso jeito de trabalhar"]
    # Retorna False se qualquer padrão detectado
```

### F3 — Fórmula de Ranking de Traits

```python
TRAIT_FORMULA_WEIGHTS = {"llm": 0.40, "prior": 0.35, "seniority_boost": 0.25}
# score_final = 0.40 * LLM_score + 0.35 * ONET_PRIOR_score + 0.25 * seniority_boost_score
```

### Feature Flag B.6

```python
# app/domains/job_creation/feature_flag.py
def is_wizard_enabled(workspace_id=None) -> bool:
    # Prioridade:
    # 1. env ENABLE_UNIFIED_WIZARD="true" → sempre habilitado
    # 2. per-workspace override (enable_for_workspace / disable_for_workspace)
    # 3. rollout%: workspace_id % 100 < rollout_percentage
    # 4. False (default)

def enable_for_workspace(workspace_id: str) -> None
def disable_for_workspace(workspace_id: str) -> None
def set_rollout_percentage(pct: int) -> None    # 0-100
def get_status() -> dict    # {enabled_globally, rollout_percentage, workspace_overrides_count}
```

---

## FairnessGuard — 7 Gates

```python
# app/domains/job_creation/compliance.py
@dataclass
class FairnessCheck:
    is_blocked: bool = False
    category: Optional[str] = None
    blocked_terms: List[str] = field(default_factory=list)
    educational_message: Optional[str] = None
```

| Gate | Nó | Input/Output | Ação se bloqueado |
|------|-----|------------|-------------------|
| 1 | `jd_enrichment_node` | **input** (texto do recrutador) | `jd_fairness_blocked=True` + erro com `educational_message` |
| 2 | `jd_enrichment_node` | **output** (JD enriquecida) | `jd_enriched=None`, `jd_quality_score=0.0`, `jd_output_blocked=True` |
| 3 | `bigfive_node` | **input** (about_role + responsabilidades) | Preserva bigfive anterior + appends warning |
| 4 | `bigfive_node` | **output** (evidências Big Five) | Appends warning a `bigfive_warnings` |
| 5 | `wsi_questions_node` | **input** (JD enriquecida) | `questions_data=[]` + `input_block` com mensagem educativa |
| 6 | `wsi_questions_node` | **per-question** | Remove pergunta + adiciona a `wsi_dropped_questions` |
| 7 | `JdEnrichmentService.enrich()` | **LLM input + output** | `apply_inclusive_language()` (correção, não bloqueio) |

**Política fail-open:** todos os 7 gates são `try/except` — se FairnessGuard não disponível (test env), fluxo continua.

```python
# Estrutura de wsi_dropped_questions:
{
    "question": str,           # texto da pergunta (160 chars max no audit)
    "category": str,           # "technical" | "behavioral"
    "blocked_terms": List[str],
    "fairness_category": str,  # categoria da FairnessGuard (ex: "genero", "raca")
    "message": str,            # mensagem educativa em PT-BR
}
```

---

## Compliance por Nó

### AuditService — 1 Row por Wizard Run

```python
# Emitido em handoff_node via emit_job_creation_audit()
# Thread separada, timeout=5s, fail-open (erro de audit não aborta handoff)
service.log_decision(
    company_id=str(workspace_id),       # do JWT/session, nunca do payload
    agent_name="job_creation_wizard",
    decision_type="job_creation",
    action="create_job",
    decision="completed" | "failed",
    reasoning=[
        f"prompt_hash={sha256[:16]}",
        f"model={model}",
        f"seniority={seniority_resolved}",
        f"screening_mode={compact|full}",
        f"questions_generated={len(wsi_questions)}",
        # se drops: {"wsi_dropped_questions": [...]}
        # se bloqueios: {"fairness_blocked": [...]}
    ],
    criteria_used=["jd_quality_score","seniority","screening_mode","wsi_distribution"],
    job_vacancy_id=str(job_id),
    confidence=jd_quality_score / 100.0,
    human_review_required=False,
)
```

### AuditCallback — Rastreamento de Cada LLM Call

```python
# Passado como config["callbacks"] = [cb] em todo invoke() e resume()
AuditCallback(
    user_id=str(state["user_id"]),
    company_id=str(state["workspace_id"]),
    session_id=thread_id,
    domain="job_creation",
    agent_type="wizard",
)
```

### Circuit Breaker Keys

| Circuit Key | Usado em |
|-------------|---------|
| `"job_creation:jd_enrichment"` | `JdEnrichmentService.enrich()` |
| `"job_creation:wsi_technical"` | `WSIQuestionGenerator._generate_block("technical")` |
| `"job_creation:wsi_behavioral"` | `WSIQuestionGenerator._generate_block("behavioral")` |
| `"job_creation:publish"` | `publish_node` (todas as chamadas Rails API) |

---

## Regras WSI Absolutas (Enforced Computacionalmente)

| Regra | Enforcement | Arquivo |
|-------|------------|---------|
| **CBI only** — sem perguntas hipotéticas | `_validate_question()` regex reject | `wsi_question_generator.py` |
| **No cultural fit** | `_validate_question()` regex reject | `wsi_question_generator.py` |
| **Quality score mínimo 50** | `route_after_jd()` → END se <30, prossegue só ≥50 | `graph.py` |
| **Recrutador aprova TODAS perguntas** | `route_after_questions()` → END se None | `graph.py` |
| **Sem perguntas → não pede aprovação** | `requires_approval = bool(questions_data)` | `graph.py` |
| **1 audit row por run** | `emit_job_creation_audit()` em handoff, não editável | `compliance.py` |
| **PII mask antes de cada LLM call** | `mask_pii_for_llm()` em F1, F2, F6 | `compliance.py` |
| **workspace_id do context (JWT/session)** | `state["workspace_id"]` de `context.workspace_id` | `domain.py` |

---

## Instruções para Claude Code / Cursor

### "Implementa Wizard WSI no v5"

**Passo 1 — Feature flag primeiro**
```python
# app/domains/job_creation/feature_flag.py
# is_wizard_enabled() verifica antes de qualquer execução
# Em dev: ENABLE_UNIFIED_WIZARD=true para habilitar para todos
```

**Passo 2 — State TypedDict**
```python
# app/domains/job_creation/state.py
# Campos HITL obrigatórios:
# jd_approved: Optional[bool] = None  (None = aguardando)
# questions_approved: Optional[bool] = None
# wsi_dropped_questions: List[Dict] = []  (nunca None)
```

**Passo 3 — LangGraph com checkpointer**
```python
graph = StateGraph(JobCreationState)
# Adicionar todos os 11 nós
# Adicionar todos os 7 routers condicionais
# SEMPRE compilar com checkpointer (PostgresSaver em prod, MemorySaver em dev)
# Singleton: JobCreationGraph._instance + _graph
```

**Passo 4 — FairnessGuard em todos os nós LLM**
```python
# compliance.py
def check_input_fairness(text: str) -> FairnessCheck:
    return _run_fairness_guard(text)

def check_output_fairness(text: str) -> FairnessCheck:
    return _run_fairness_guard(text)

# NUNCA pular os gates — wrapping em try/except para fail-open, não skip:
try:
    result = check_input_fairness(text)
    if result.is_blocked:
        state["jd_fairness_blocked"] = True
        return state
except Exception:
    pass  # fail-open em test env
```

**Passo 5 — Quality Score F1.B (determinístico)**
```python
# 5 critérios → score 0-100
# <30 → blocked (END); 30-49 → warning (pode continuar com override); ≥50 → OK
# Limiar de prosseguimento = 50 (não configurável)
```

**Passo 6 — JobCreationAPIClient**
```python
# app/domains/job_creation/api_client.py
# base_url = settings.ats_api.base_url  (Rails API)
# Auth: Bearer token de context + refresh 401 automático
# NUNCA hardcodar URL ou token
```

**Passo 7 — Audit em handoff (background thread)**
```python
# emit_job_creation_audit() via thread separada com timeout=5s
# Fail-open: erro de audit não deve abortar o handoff_node
import threading
t = threading.Thread(target=emit_job_creation_audit, args=(state, ...))
t.start()
t.join(timeout=5.0)
# Se t.is_alive() → log warning + continue
```

### "Adiciona pergunta nova ao Wizard"

1. Verificar que o novo tipo de pergunta NÃO é hipotética e NÃO menciona cultural fit
2. Adicionar à lista de fallback em `_fallback_questions()` se for novo bloco
3. Atualizar `scoring_rubric` com escalas 1-3/4-6/7-9/10
4. Testar que `_validate_question()` não rejeita a pergunta

### Setup em CLAUDE.md (snippet)

```markdown
## Wizard WSI (P5)
- Fonte: themes/persona/P5_WIZARD_WSI.md
- LangGraph 11 nós: intake → jd_enrichment → bigfive → salary → competency → wsi_questions → ...
- 2 HITL: jd_enrichment (HITL 1) + wsi_questions (HITL 2)
- FairnessGuard em 7 gates — fail-open (try/except), nunca skip
- Quality score F1.B: <30=blocked; 30-49=warning; ≥50=OK; prossegue só ≥50
- Sem YAMLs de prompt — tudo inline em Python
- workspace_id SEMPRE do context/JWT, nunca do payload
- 1 audit row por run via AuditService em handoff_node (background thread, fail-open)
```

### Setup em Cursor rules

```
---
description: Wizard WSI (job creation) rules
globs: ["*job_creation*", "*wizard*", "*wsi_question_generator*"]
---
# Wizard WSI Rules
- LangGraph StateGraph with 2 HITL: jd_enrichment + wsi_questions
- FairnessGuard at 7 gates (all try/except fail-open)
- Quality score threshold: 50 to proceed (NOT configurable)
- NO hypothetical questions (_validate_question rejects them)
- NO cultural fit questions (_validate_question rejects them)
- workspace_id from context/JWT (never payload)
- 1 AuditService.log_decision per wizard run (background thread)
- Prompts inline in Python (no YAML files for F1/F2/F6)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexível porque |
|------|----------------|
| LLM model per stage (F1 vs F6) | Parâmetro de configuração — só afeta qualidade, não compliance |
| Temperaturas (F1=0.3, F6_tech=0.7, F6_behav=0.75) | Parâmetros de tuning |
| Limiares da question distribution table | Ajuste de produto (compact/full não é legal) |
| Timeout do audit background thread (5s) | Operacional |
| `_fallback_questions()` conteúdo | Fallback de UX, não contrato |
| STAGE_ORDER nomes de string | Desde que HITL_STAGES = {"jd_enrichment", "wsi_questions"} seja preservado |
| `api_client.py` endpoints | Contrato com Rails — mudar com migration de API |
| Número de competências default no WSI | Produto |

### NÃO pode adaptar

| Item | Por quê é imutável |
|------|--------------------|
| `_validate_question()` rejeitar hipotéticas + cultural fit | Metodologia WSI CBI (Competency-Based Interviewing) — contrato com o produto |
| `jd_approved=None` como estado "aguardando" (não False) | HITL pattern: None=pendente, True=aprovado, False=rejeitado — confundir None/False quebra roteamento |
| Quality score mínimo 50 para prosseguir | Produto: vaga abaixo de 50 tem JD insuficiente para gerar perguntas WSI válidas |
| FairnessGuard em TODOS os 7 gates | C1 Fairness + LGPD — remover qualquer gate abre risco legal |
| `workspace_id` de `context.workspace_id` (JWT) | Multi-tenancy (C5) — payload pode ser forjado |
| `emit_job_creation_audit()` em `handoff_node` | C7 Audit Trail (LGPD + EU AI Act) — sem audit não há rastreabilidade de decisões |
| `mask_pii_for_llm()` antes de F1, F2, F6 | LGPD Art. 12 — dados pessoais do recrutador ou candidato não vão para LLM |
| `requires_approval = bool(questions_data)` | FairnessGuard pode bloquear TODAS as perguntas → não pedir aprovação de lista vazia |

---

## Checklist de completude

### P0 — Críticos (bloqueiam deploy)

- [ ] (P0) `is_wizard_enabled(workspace_id)` verificado antes de executar qualquer nó
- [ ] (P0) HITL 1 (`jd_approved=None`) retorna controle ao frontend antes de `bigfive`
- [ ] (P0) HITL 2 (`questions_approved=None`) retorna controle ao frontend antes de `eligibility`
- [ ] (P0) FairnessGuard em todos os 7 gates (mesmo que fail-open)
- [ ] (P0) `workspace_id` de `context.workspace_id` (JWT/session) — nunca do payload
- [ ] (P0) `emit_job_creation_audit()` com `decision_type="job_creation"` em `handoff_node`
- [ ] (P0) `mask_pii_for_llm()` aplicado antes de F1, F2, F6

### P1 — Importantes

- [ ] (P1) `_validate_question()` rejeita hipotéticas + cultural fit (CBI compliance)
- [ ] (P1) Quality score F1.B: <30 → blocked, 30-49 → warning, ≥50 → prossegue
- [ ] (P1) `wsi_dropped_questions` populado com motivo para cada pergunta bloqueada
- [ ] (P1) Circuit breakers nos 4 pontos de chamada LLM + Rails API
- [ ] (P1) `JobCreationGraph` singleton com checkpointer (MemorySaver em dev)
- [ ] (P1) `AuditCallback` passado em `config["callbacks"]` em todo `invoke()` e `resume()`
- [ ] (P1) Prioridade de perguntas: versioned → WSI dynamic → Gemini autonomous (fallback)

### P2 — Qualidade

- [ ] (P2) `completeness` calculado como `idx / (len(STAGE_ORDER) - 1)` (não hardcoded)
- [ ] (P2) `ws_stage_payload` presente em toda resposta de nó (frontend depende)
- [ ] (P2) Tabelas de distribuição F5 (compact/full × seniority) determinísticas (não LLM)
- [ ] (P2) `scoring_rubric` em toda pergunta gerada (1-3 / 4-6 / 7-9 / 10)
- [ ] (P2) `feature_flag.get_status()` endpoint de monitoramento disponível

---

## Gotchas e Erros Comuns

### 1. `jd_approved=None` vs `jd_approved=False`

```python
# ❌ ERRADO — confunde aguardando com rejeitado
if not state.get("jd_approved"):    # None → também entra aqui!
    return "end"

# ✅ CORRETO
if state.get("jd_approved") is None:    # aguardando
    return "end"
if not state.get("jd_approved"):        # False → rejeitado
    return "intake"
```

### 2. Quality score `0.0` vs `None`

```python
# Se FairnessGuard bloquear o output do LLM:
state["jd_quality_score"] = 0.0   # NÃO None
# route_after_jd verifica: if quality < 30: return "end"
# Se for None, a comparação lança TypeError
```

### 3. workspace_id vs user_id

```python
# ❌ ERRADO — user_id não é company_id
company_id = str(state["user_id"])

# ✅ CORRETO
company_id = str(state["workspace_id"])  # workspace = empresa/tenant
```

### 4. Checkpointer MemorySaver não persiste entre restarts

```python
# Em dev: MemorySaver() → sessão perdida em restart
# Em prod: get_checkpointer() retorna AsyncPostgresSaver
# Resultado: thread_id deve ser salvo no frontend para resume()
```

### 5. Perguntas com scoring_rubric faltando

```python
# GeneratedQuestion.scoring_rubric é OBRIGATÓRIO:
# Se ausente → WSIVoiceOrchestrator não consegue fazer scoring
# Mínimo necessário: {"1-3": "...", "4-6": "...", "7-9": "...", "10": "..."}
```

### 6. Audit thread com timeout curto em deploy lento

```python
t.join(timeout=5.0)
# Se AuditService.log_decision demora > 5s (DB lento, network spike):
# → thread ainda executando após timeout → pode gerar duplicate inserts
# → log warning + monitorar taxa de timeouts em prod
```

### 7. `apply_inclusive_language` vs FairnessGuard block

```python
# Gate 7 (JdEnrichmentService) NÃO bloqueia — aplica correções:
# apply_inclusive_language("candidatos masculinos") → "candidatos"
# FairnessGuard gates 1-6 bloqueiam e param o fluxo
# São mecanismos distintos — não intercambiar
```

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| HITL 1 aguardando | `tests/unit/test_job_creation_graph.py` | `jd_approved=None` → route_after_jd retorna "end" |
| HITL 1 rejeitado | `tests/unit/test_job_creation_graph.py` | `jd_approved=False` → route_after_jd retorna "intake" |
| HITL 2 regenerar | `tests/unit/test_job_creation_graph.py` | `questions_approved=False` → route_after_questions retorna "wsi_questions" |
| FairnessGuard bloqueia input | `tests/unit/test_jd_enrichment_node.py` | JD com termo discriminatório → `jd_fairness_blocked=True` |
| FairnessGuard remove pergunta | `tests/unit/test_wsi_questions_node.py` | Pergunta hipotética → em `wsi_dropped_questions`, não em `wsi_questions` |
| Quality score <30 bloqueia | `tests/unit/test_job_creation_graph.py` | JD muito rasa → route_after_jd retorna "end" |
| workspace_id do JWT | `tests/security/test_job_creation_tenant.py` | Payload com workspace_id diferente → ignorado, usa JWT |
| Validate question — hipotética | `tests/unit/test_wsi_question_generator.py` | "o que você faria se..." → _validate_question() retorna False |
| Validate question — cultural fit | `tests/unit/test_wsi_question_generator.py` | "fit cultural" → _validate_question() retorna False |
| Audit emitido em handoff | `tests/integration/test_job_creation_audit.py` | Run completo → 1 row decision_type="job_creation" |
| Feature flag desabilitado | `tests/unit/test_job_creation_feature_flag.py` | is_wizard_enabled() = False → wizard não executa |
| Distribuição F5 determinística | `tests/unit/test_wsi_question_generator.py` | compact + senior → 4T+3B (não varia entre runs) |

---

## Referências

| Recurso | Localização |
|---------|------------|
| I12 Voice Screening (consome perguntas geradas aqui) | `themes/infrastructure/I12_VOICE_SCREENING.md` |
| C1 Fairness (FairnessGuard 7 gates) | `themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md` |
| C2 LGPD PII (mask_pii_for_llm) | `themes/compliance/C2_LGPD_PII_AND_DATA_MINIMIZATION.md` |
| C7 Audit Trail (emit_job_creation_audit) | `themes/compliance/C7_AUDIT_TRAIL_AND_COMPLIANCE_LINT.md` |
| I3 Orchestration (JobCreationDomain routing) | `themes/infrastructure/I3_ORCHESTRATION.md` |
| R1 Circuit Breakers (4 circuit keys) | `themes/resilience/R1_CIRCUIT_BREAKERS.md` |
| O3 External Integrations (JobCreationAPIClient → Rails) | `themes/operational/O3_EXTERNAL_INTEGRATIONS.md` |
| Handoff LIA Partes A-F | `DEVELOPER_HANDOFF.md` (1204 linhas) |
