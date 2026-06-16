# Theme: I7 — Intent Classification & Routing — Infrastructure Layer

## O que é este tema

Intent Classification & Routing é a camada que converte texto livre do usuário em uma instrução estruturada (`domain_id` + `action_id` + `confidence`) que o pipeline de orquestração pode executar. O sistema tem **três subsistemas independentes** com propósitos distintos:

1. **FastRouter** (`fast_router.py`) — classificador regex/keyword de Tier 4 no `CascadedRouter`. Resolve ~80% das queries sem LLM. Lê padrões de `domain_routing.yaml` em startup.

2. **Domain-level Intent Matching** (`KeywordIntentMatcher` + 17 × `capabilities.yaml`) — cada domain classifica a query que já chegou até ele em um `action_id` específico. Lida com o nível fino ("gerar relatório KPI" → `generate_kpi_report`).

3. **Wizard Intent Classifiers** (`IntentClassifierService` + `EnhancedIntentClassifierService`) — classificadores de intent para o fluxo de criação de vagas (Job Wizard). Determinam se o usuário está fornecendo dados, corrigindo, desviando ou querendo reaproveitar uma vaga anterior.

Separado dos três: **`NavigationIntentDetector`** — classifica mensagens do Float Chat em páginas de navegação da plataforma (`Vagas`, `Funil de Talentos`, `Indicadores`, etc.). Exposto via `POST /api/v1/navigation-intent`.

**Boundary com I3 (Orchestration):** I3 documenta o pipeline de alto nível do `CascadedRouter` (8 tiers). I7 documenta os componentes que implementam os Tiers 4 (FastRouter), 3.5 (domain process_intent) e a camada de wizard + navigation separada.

---

## Arquivos conectados (23 total)

### Camada Config (Python/YAML lê)

| Arquivo | Path canônico | Quando é consumido |
|---------|--------------|---------------------|
| `domain_routing.yaml` | `app/orchestrator/config/domain_routing.yaml` | FastRouter startup (módulo-load) |
| `capabilities.yaml` × 17 | `app/domains/<X>/config/capabilities.yaml` | Domain `__init__` (módulo-load) |
| `intent_classification.yaml` (prompt) | `app/prompts/intent_classification/` | `EnhancedIntentClassifierService` via `PromptLoader` |
| `platform_manifest.yaml` | Lido via `app/shared/platform_manifest.py` | `NavigationIntentDetector._get_patterns()` at startup |

**17 domains com `capabilities.yaml`:**
`sourcing`, `job_management`, `cv_screening`, `communication`, `analytics`, `interview_scheduling`, `ats_integration`, `automation`, `recruiter_assistant`, `pipeline`, `hiring_policy`, `agent_studio`, `digital_twin`, `recruitment_campaign`, `talent_pool`, `company_settings`, `candidate_self_service`

### Camada Código (Python — 6 arquivos principais)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `fast_router.py` | `app/orchestrator/fast_router.py` | Tier 4 regex router; lê domain_routing.yaml |
| `keyword_intent_matcher.py` | `app/shared/services/keyword_intent_matcher.py` | Motor compartilhado de keyword/regex matching + info detection |
| `intent_classifier.py` (shim) | `app/shared/services/intent_classifier.py` | Backwards-compat shim → `app/domains/ai/services/intent_classifier.py` |
| `enhanced_intent_classifier.py` (shim) | `app/shared/services/enhanced_intent_classifier.py` | Backwards-compat shim → `app/domains/ai/services/enhanced_intent_classifier.py` |
| `intent_classifier.py` (real) | `app/domains/ai/services/intent_classifier.py` | Wizard classifier: 5 tipos, quick rules + LLM |
| `enhanced_intent_classifier.py` (real) | `app/domains/ai/services/enhanced_intent_classifier.py` | Enhanced wizard classifier: 10 tipos + rich entity extraction |
| `navigation_intent.py` | `app/orchestrator/navigation_intent.py` | Float Chat page navigation; 7 pages + weight scoring |
| `navigation_intent.py` (API) | `app/api/v1/navigation_intent.py` | `POST /api/v1/navigation-intent` endpoint |

### Domain samples com `domain.py` + `capabilities.yaml` pattern

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `domain.py` (analytics) | `app/domains/analytics/domain.py` | `AnalyticsDomain.process_intent()` com KeywordIntentMatcher |
| `capabilities.yaml` (analytics) | `app/domains/analytics/config/capabilities.yaml` | 70+ keyword→action mapeamentos em `intent_keywords` |
| `job_wizard_graph.py` | `app/domains/job_management/agents/job_wizard_graph.py` | LangGraph com `intent_classifier` como START_NODE |
| `wizard_step_service.py` | `app/domains/job_management/services/wizard_step_service.py` | Consumidor de `intent_classifier_service` + `enhanced_intent_classifier` |

### Integration points

- **CascadedRouter** (`app/orchestrator/cascaded_router.py`, linha 24) importa `FastRouter` — Tier 4
- **Domain `process_intent()`** em 17 domains usa `KeywordIntentMatcher` — resolução de action_id
- **`WizardStepService`** usa `intent_classifier_service` + `enhanced_intent_classifier` — fluxo wizard
- **`POST /api/v1/navigation-intent`** — frontend Float Chat chama para sugestões de navegação

---

## Subsistema 1 — FastRouter (Tier 4 do CascadedRouter)

### Estrutura de dados

```python
# app/orchestrator/fast_router.py

@dataclass
class FastRouteResult:
    domain_id: str           # ex: "analytics", "job_management"
    confidence: float        # 0.0–0.95
    matched_pattern: str     # regex que casou
    matched_text: str        # substring da query que casou
```

### Carregamento de padrões

```python
# fast_router.py — _load_domain_patterns() (L397)

def _load_domain_patterns() -> dict[str, list[str]]:
    _yaml_path = Path(__file__).parent / "config" / "domain_routing.yaml"
    # lê YAML → data.get("domains", {})
    # valida: domain_id str, patterns list[str]
    # fallback: _HARDCODED_DOMAIN_PATTERNS se YAML ausente/inválido
    # retorna: dict[domain_id → list[regex_str]]

DOMAIN_PATTERNS: dict[str, list[str]] = _load_domain_patterns()  # module-level singleton
```

O `domain_routing.yaml` tem 22+ domains com listas de regexes. Exemplos de domínios:
`job_management`, `sourcing`, `sourcing_planner`, `sourcing_search`, `sourcing_enrich`, `sourcing_engagement`, `cv_screening`, `wsi_assessment`, `interviewing`, `scheduling`, `communication`, `kanban_search`, `kanban_insight`, `kanban_action`, `pipeline_context`, `pipeline_decision`, `pipeline_action`, `analytics`, `ats_integration`, `recruiter_assistant`, `task_planning`, `interview_scheduling`, `talent_pool`, `agent_studio`, `digital_twin`, `recruitment_campaign`, `company_settings`

### Compilação de padrões

```python
# fast_router.py — _ensure_compiled() (L468)

_COMPILED_PATTERNS: dict[str, list[re.Pattern]] = {}

def _ensure_compiled() -> None:
    if not _COMPILED_PATTERNS:
        for domain_id, patterns in DOMAIN_PATTERNS.items():
            _COMPILED_PATTERNS[domain_id] = [
                re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns
            ]
        # loga: "FastRouter compiled N patterns for M domains"

class FastRouter:
    def __init__(self):
        _ensure_compiled()  # chamado no __init__
```

### Normalização de domain_id

Alguns IDs no YAML são aliases que mapeiam para o agent canonical ID:

```python
# fast_router.py — _DOMAIN_ID_NORMALIZE (L450)

_DOMAIN_ID_NORMALIZE: dict[str, str] = {
    "wsi_assessment": "cv_screening",
    "interviewing": "interview_scheduling",
    "scheduling": "interview_scheduling",
    "task_planning": "automation",
    # subagentes kanban/pipeline passam sem normalização
}

def normalize_domain_id(domain_id: str) -> str:
    return _DOMAIN_ID_NORMALIZE.get(domain_id, domain_id)
```

### Algoritmo de match

```python
# fast_router.py — FastRouter.match() (L554)

def match(self, message: str) -> FastRouteResult | None:
    message_lower = message.lower().strip()

    # Para cada domain × pattern: re.search → specificity = len(m.group())
    # confidence = min(0.95, 0.7 + specificity * 0.02)
    # best_for_domain = pattern com maior specificity

    # Coleta todos os matches → ordena por confidence DESC

    # Penalidade de ambiguidade: se gap < 0.1 entre top 2:
    #   confidence = max(0.3, confidence - 0.15)
    #   loga WARNING "FastRouter ambiguity detected"

    # Deduplicação P06: _deduplicate_matches()
    #   - agrupa em buckets de 0.1
    #   - dentro do top bucket: mantém pattern mais longo
    #   - strip do sufixo "|pattern" antes de retornar

    # Shadow comparison (telemetria — fail-open):
    #   _get_domain_matcher().match(message)
    #   se diverge: loga DEBUG "[LIA-I05] Domain routing disagreement"

    return FastRouteResult(domain_id=normalize_domain_id(domain_id), ...)
```

### Shadow KeywordIntentMatcher

```python
# fast_router.py — _get_domain_matcher() (L25)

# Constrói um KeywordIntentMatcher a partir de DOMAIN_PATTERNS
# convertendo regex → literal keyword (best-effort, stripa special chars)
# Resultado salvo em _DOMAIN_MATCHER (singleton)
# Usado em match() para comparar resultado regex vs keyword (só telemetria)
```

---

## Subsistema 2 — KeywordIntentMatcher (motor compartilhado)

### Classes e tipos

```python
# app/shared/services/keyword_intent_matcher.py

class IntentType(str, Enum):
    INFO = "info"        # user quer explicação
    ACTION = "action"    # user quer executar
    NAVIGATION = "navigation"
    UNKNOWN = "unknown"

@dataclass
class IntentMatch:
    action: str
    confidence: float
    intent_type: IntentType = IntentType.ACTION
    domain_id: str = ""
    matched_keyword: str = ""

@dataclass
class IntentPattern:
    keywords: list[str]
    action: str
    intent_type: IntentType = IntentType.ACTION
    confidence_base: float = 0.8
    description: str = ""
```

### Construção

```python
# Opção 1: a partir de capabilities.yaml (novo formato)
matcher = KeywordIntentMatcher.from_yaml("app/domains/X/config/capabilities.yaml")
# YAML precisa ter: intents: [{keywords: [...], action: str, type: str, confidence: float}]

# Opção 2: a partir de dict legado (migração gradual)
matcher = KeywordIntentMatcher.from_keyword_map({"keyword": "action_id"}, domain_id="X")
# Converte cada entrada em IntentPattern com confidence_base=0.8
```

### Detecção de INFO query

```python
# 15 padrões de INFO (regex compilados)
_INFO_PATTERNS = [
    r"como\s+funciona",
    r"o\s+que\s+[eé]",
    r"me\s+explic[ae]",
    r"me\s+cont[ae]",
    r"quero\s+saber",
    r"quero\s+entender",
    r"como\s+faz",
    r"como\s+(?:eu\s+)?(?:posso|consigo|devo)",
    r"para\s+que\s+serve",
    r"qual\s+(?:a\s+)?diferen[cç]a",
    r"me\s+d[aá]\s+(?:uma\s+)?(?:vis[aã]o|ideia|resumo)",
    r"o\s+que\s+significa",
    r"como\s+usar",
    r"tutorial",
    r"ajuda\s+(?:com|sobre|para)",
]

def is_info_query(self, query: str) -> bool:
    q_lower = query.lower().strip()
    return any(p.search(q_lower) for p in _INFO_COMPILED)
```

### Algoritmo de match

```python
def match(self, query: str, default_action: str = "general_help") -> IntentMatch:
    q_lower = query.lower().strip()
    is_info = self.is_info_query(query)

    best_match = IntentMatch(action=default_action, confidence=0.3, ...)

    for pattern in self.patterns:
        for keyword in pattern.keywords:
            if keyword.lower() in q_lower:
                conf = min(0.95, pattern.confidence_base + len(keyword) * 0.01)
                if conf > best_match.confidence:
                    best_match = IntentMatch(
                        action=pattern.action,
                        confidence=conf,
                        intent_type=IntentType.INFO if is_info else pattern.intent_type,
                        domain_id=self.domain_id,
                        matched_keyword=keyword,
                    )
    return best_match
```

### Padrão de uso nos domains

```python
# app/domains/analytics/domain.py — padrão replicado em 17 domains

# 1. Carrega capabilities.yaml no módulo (startup)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP = yaml.safe_load(path.read_text()).get('intent_keywords', {})
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="analytics")

# 2. process_intent() — chamado pelo CascadedRouter após Tier 4 rotear
async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
    if _matcher.is_info_query(query):
        match = _matcher.match(query, default_action="get_dashboard_data")
        return IntentResult(
            intent_id=f"analytics.{match.action}",
            action_id=match.action,
            confidence=match.confidence,
            extracted_params={"raw_query": query, "is_info_query": True},
        )

    match = _matcher.match(query, default_action="get_dashboard_data")
    return IntentResult(
        intent_id=f"analytics.{match.action}",
        action_id=match.action,
        confidence=match.confidence,
        extracted_params={"raw_query": query},
        reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
    )
```

### Formato do `capabilities.yaml` (analytics como referência)

```yaml
# app/domains/analytics/config/capabilities.yaml
domain: analytics

intent_keywords:
  relatório kpi: generate_kpi_report
  relatório de kpi: generate_kpi_report
  kpi report: generate_kpi_report
  gerar kpi: generate_kpi_report
  # ... ~70 entradas total
  dashboard: get_dashboard_data
  dados dashboard: get_dashboard_data
  monitoramento agentes: get_agent_monitoring
```

**Nota:** O analytics usa o **formato legado** (`intent_keywords: dict`). O `from_yaml()` do `KeywordIntentMatcher` espera o **formato novo** (`intents: list`). Os domains usam `from_keyword_map()` com o dict legado. Os dois formatos coexistem.

---

## Subsistema 3 — Wizard Intent Classifiers

### IntentClassifierService (wizard básico)

```python
# app/domains/ai/services/intent_classifier.py (real)
# app/shared/services/intent_classifier.py (shim — backwards compat)

class IntentType(StrEnum):
    DATA_INPUT = "DATA_INPUT"     # user fornecendo dados
    QUESTION = "QUESTION"         # user perguntando
    CORRECTION = "CORRECTION"     # "na verdade, não era isso"
    DEVIATION = "DEVIATION"       # "pula", "próximo passo"
    REUSE_VACANCY = "REUSE_VACANCY"  # "aproveitar vaga anterior"

class ClassificationResult(BaseModel):
    intent_type: IntentType
    confidence: float          # 0.0–1.0
    extracted_entities: dict[str, Any]
    original_text: str
    reasoning: str | None
```

**Hierarquia de classificação:**
1. `_quick_classify()` — regras por indicadores (CORRECTION_INDICATORS, DEVIATION_INDICATORS, etc.)
2. Se quick = CORRECTION ou DEVIATION com confidence ≥ 0.9 → retorna imediatamente (sem LLM)
3. LLM via `_classify_with_llm()` — prompt com stage_context + JSON output
4. Fallback regex se LLM falhar

**Entidades extraídas por regex:** salary (R$, K), work_model (remoto/híbrido/presencial), location (estados BR), seniority (júnior/pleno/sênior/lead), skills (Python/React/etc.)

**Custo rastreado:** `build_usage_callback(tracking_context, agent_type="intent_classifier", default_operation="intent_classification")`

### EnhancedIntentClassifierService (wizard rico)

```python
# app/domains/ai/services/enhanced_intent_classifier.py (real)

class EnhancedIntentType(StrEnum):
    CREATE_JOB = "CREATE_JOB"
    UPDATE_FIELD = "UPDATE_FIELD"
    QUESTION = "QUESTION"
    CORRECTION = "CORRECTION"
    NAVIGATION = "NAVIGATION"
    REUSE_VACANCY = "REUSE_VACANCY"
    CONFIRM = "CONFIRM"        # "sim", "ok", "pode ser"
    REJECT = "REJECT"          # "não", "cancela"
    HELP = "HELP"              # "ajuda", "como funciona"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"

@dataclass
class ExtractedEntities:
    cargo: str | None
    area: str | None
    senioridade: str | None
    salario_min: float | None
    salario_max: float | None
    bonus: str | None
    modelo_trabalho: str | None    # Remoto/Híbrido/Presencial
    localizacao: str | None
    tipo_contrato: str | None      # CLT/PJ/Estágio/Temporário/Freelancer
    skills_tecnicas: list[str]     # Python, React, AWS, etc.
    skills_comportamentais: list[str]
    idiomas: list[str]             # Inglês, Espanhol, etc.
    beneficios: list[str]          # VR, VA, Plano de Saúde, etc.
    is_afirmativa: bool            # vaga afirmativa PCD/Mulheres/Negros/LGBTQIA+
    criterio_afirmativo_primario: str | None
    criterio_afirmativo_secundario: str | None
    gestor: str | None
    gestor_email: str | None
    recrutador: str | None
    prazo: str | None
    urgencia: str | None           # "Alta" se detectar "urgente"/"asap"
    filtro_busca: dict[str, Any]
```

**AFFIRMATIVE_PATTERNS (8 grupos):** PCD, Mulheres, Pessoas Negras, LGBTQIA+, 50+, Indígena, Pessoas Trans, Diversidade.

**Fusão de entidades (LLM + regex):**
```python
def _merge_entities(self, regex_entities, llm_entities):
    # Campos simples: LLM vence se não-None/não-empty
    # Campos list: union (set concatenado)
    # filtro_busca: LLM vence
    # raw_entities: dict do LLM raw
```

**Prompt carregado dinamicamente:**
```python
CLASSIFICATION_PROMPT = PromptLoader.get_domain_prompt("intent_classification")
# Prompt em app/prompts/intent_classification/
```

### Uso no Job Wizard

```python
# app/domains/job_management/services/wizard_step_service.py

# Etapas iniciais (stage ≤ 2): usa enhanced_intent_classifier
enhanced_classification = await enhanced_intent_classifier.classify(
    user_input=message,
    stage=current_stage,
    filled_fields=filled_fields,
    tracking_context=tracking_ctx,
)

# Etapas intermediárias: usa intent_classifier_service (mais rápido)
classification = await intent_classifier_service.classify(
    user_input=message,
    stage_context=stage_name,
    use_llm=True,
    tracking_context=tracking_ctx,
)
```

**LangGraph wizard (job_wizard_graph.py):**
```python
# START_NODE = "intent_classifier"
# Nodes: "intent_classifier" → "field_extractor" → "tool_router"
# Edges condicionais: route_intent_classifier() → DATA_INPUT/CORRECTION/DEVIATION/QUESTION/REUSE
# Loop: route_intent_classifier pode retornar target_node="intent_classifier" para novo turno
builder.set_entry_point("intent_classifier")
builder.add_conditional_edges("intent_classifier", route_intent_classifier, {
    "field_extractor": "field_extractor",
    "continue": "intent_classifier",
    "end": END,
})
```

---

## Subsistema 4 — NavigationIntentDetector

### Estrutura

```python
# app/orchestrator/navigation_intent.py

@dataclass
class NavigationIntentResult:
    page: str | None           # "Vagas" | "Funil de Talentos" | "Painel de Controle"
                               # "Configurações" | "Indicadores" | None
    confidence: float          # 0.0–0.95
    hint: str | None           # "Quer que eu abra os Indicadores?"
    matched_pattern: str | None  # keyword que casou
```

### 7 páginas com pesos de keywords

| Página | Keyword forte (1.0) | Keyword genérica (0.2–0.4) |
|--------|--------------------|-----------------------------|
| Configurações | "critérios de triagem", "configurar triagem" | "configurações" (1.0), "política" (0.5) |
| Funil de Talentos (WSI) | "iniciar entrevista", "entrevista wsi", "triagem por voz" | "wsi" (0.5), "assessment" (0.5) |
| Vagas | "criar vaga", "abrir vaga", "publicar vaga", "nova vaga" | "vagas" (0.3), "vaga" (0.3) |
| Funil de Talentos | "buscar candidato", "banco de talentos" | "candidato" (0.2), "cv" (0.3) |
| Funil de Talentos (Kanban) | "mover candidato" | "kanban" (0.7), "pipeline" (0.5) |
| Painel de Controle | "painel de controle", "tarefas pendentes" | "dashboard" (0.7), "atividades" (0.4) |
| Indicadores | "indicadores", "kpis", "kpi" | "relatório" (0.5), "analytics" (0.5) |

### Algoritmo de scoring

```python
def detect(self, message: str) -> NavigationIntentResult:
    text = message.lower().strip()

    # Detecta: is_nav_imperative — "me leva pra X", "abra X", "quero ver X"
    is_nav_imperative = bool(_NAV_IMPERATIVE_PREFIXES.search(text))
    
    # Detecta: is_question — "como funciona X?", "o que é X?"
    is_question = bool(_INTERROGATIVE_PREFIXES.search(text) or text.endswith("?")) and not is_nav_imperative

    # Para cada grupo de patterns:
    #   score += weight de cada keyword que aparece no texto
    #   has_strong = True se algum weight >= 0.7

    # Filtro: se not has_strong and score < 0.6 → retorna None (sem sugestão)

    # Confidence base: min(0.95, 0.5 + score * 0.2)
    # BUG-18 fix:
    if is_nav_imperative:
        confidence = min(0.95, confidence + 0.15)   # imperativo claro = boost
    elif is_question:
        confidence *= 0.75    # pergunta = reduz (antes era 0.45 — muito agressivo)

    # Threshold final: _FINAL_CONFIDENCE_MIN = 0.50
    # Frontend consome com threshold = 0.75 para disparar navegação automática
```

### Carregamento de padrões (platform_manifest.yaml)

```python
# navigation_intent.py — _get_patterns() (chamada no module-load)

def _get_patterns():
    try:
        from app.shared.platform_manifest import get_navigation_patterns
        patterns = get_navigation_patterns()
        if patterns: return patterns
    except Exception as exc:
        logger.warning("[NavigationIntent] Manifest load failed: %s", exc)
    return _PATTERNS_FALLBACK   # 7 grupos hardcoded
```

### Endpoint REST

```python
# app/api/v1/navigation_intent.py

POST /api/v1/navigation-intent
Body:    { "message": "quero ver minhas vagas abertas" }
Response: { "page": "Vagas", "confidence": 0.82, "hint": "Quer que eu abra a página de Vagas?", "matched_pattern": "minhas vagas" }
```

---

## Lógica IN → OUT (fluxo completo de routing)

### Input

| Contexto | Input | Produtor |
|---------|-------|---------|
| Float Chat | `message: str` | `MainOrchestrator.process()` |
| Wizard | `user_input: str + stage: int + filled_fields: dict` | `WizardStepService` |
| Float navigation | `message: str` | Frontend float panel |

### Processing (by subsystem)

**FastRouter (Tier 4 do CascadedRouter):**
```
message → lowercase + strip
→ para cada (domain, patterns): re.search → specificity = len(match.group())
→ confidence = min(0.95, 0.7 + specificity * 0.02)
→ coleta todos matches → ordena DESC
→ penalidade se gap entre top-2 < 0.1 (confidence -= 0.15)
→ deduplicação por bucket + longest pattern
→ normalize_domain_id()
→ FastRouteResult (ou None se nenhum match)
```

**Domain process_intent() (Tier ≈ 4.5, após FastRouter rotear):**
```
query → is_info_query() check
→ KeywordIntentMatcher.match(query, default_action)
→ IntentResult(intent_id, action_id, confidence, extracted_params)
```

**Wizard IntentClassifier:**
```
user_input → _quick_classify() (regras)
→ se CORRECTION/DEVIATION ≥ 0.9 confidence: retorna imediatamente
→ _extract_entities_regex()
→ LLM classify (prompt com stage_context)
→ ClassificationResult(intent_type, confidence, extracted_entities)
```

**EnhancedIntentClassifier:**
```
user_input → _quick_classify() → se ≥ 0.9: retorna
→ _extract_entities_regex() (affirmative patterns, skills, languages, benefits, salary, seniority)
→ PromptLoader.get_domain_prompt("intent_classification") → LLM → JSON
→ _merge_entities(regex, llm) → LLM vence campos simples, union para listas
→ EnhancedClassificationResult(intent_type, confidence, entities, needs_clarification)
```

### Output

| Subsistema | Output | Destino |
|-----------|--------|---------|
| FastRouter | `FastRouteResult(domain_id, confidence)` | `CascadedRouter` seleciona agent |
| domain.`process_intent()` | `IntentResult(intent_id, action_id, confidence)` | Agent recebe action_id para chamar tool |
| `IntentClassifierService` | `ClassificationResult(IntentType, confidence, entities)` | `WizardStepService` decide próximo passo |
| `EnhancedIntentClassifierService` | `EnhancedClassificationResult(EnhancedIntentType, entities)` | `WizardStepService` extrai campos para vaga |
| `NavigationIntentDetector` | `NavigationIntentResult(page, confidence, hint)` | API `/navigation-intent` → Frontend |

### Escalação

Nenhum destes classifiers envolve HITL diretamente. Escalação ocorre no nível do orchestrator (FairnessGuard, Policy Engine) — fora do escopo deste tema.

---

## Instruções para Claude Code / Cursor

### "Implementa intent routing no v5"

**Passo 1 — FastRouter:**
```python
# 1. Cria app/orchestrator/config/domain_routing.yaml com formato:
#    version: "1.0"
#    domains:
#      job_management:
#        - "criar?\\s+\\w*\\s*vaga"
#      ...

# 2. Cria app/orchestrator/fast_router.py:
#    - _load_domain_patterns() lê domain_routing.yaml com fallback hardcoded
#    - DOMAIN_PATTERNS = _load_domain_patterns()  # module-level
#    - _COMPILED_PATTERNS compilado em _ensure_compiled()
#    - FastRouter.match() com confidence = min(0.95, 0.7 + len(match) * 0.02)
#    - normalize_domain_id() para aliases
```

**Passo 2 — KeywordIntentMatcher:**
```python
# 3. Cria app/shared/services/keyword_intent_matcher.py
#    - Classes: IntentType, IntentMatch, IntentPattern
#    - _INFO_PATTERNS (14 regex compilados)
#    - from_yaml() para novo formato
#    - from_keyword_map() para legado
#    - is_info_query() + match()

# 4. Para cada domain, cria:
#    app/domains/<X>/config/capabilities.yaml
#    com: intent_keywords: {keyword: action_id}

# 5. Em cada domain.py:
#    _matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="X")
#    async def process_intent(self, query, context):
#        if _matcher.is_info_query(query): ...
#        match = _matcher.match(query)
#        return IntentResult(...)
```

**Passo 3 — Wizard classifiers (apenas se v5 tem wizard):**
```python
# 6. Cria app/domains/ai/services/intent_classifier.py
#    - IntentType enum (5 tipos)
#    - IntentClassifierService com _quick_classify() + LLM fallback

# 7. Cria app/domains/ai/services/enhanced_intent_classifier.py
#    - EnhancedIntentType (10 tipos)
#    - ExtractedEntities dataclass (30+ campos)
#    - AFFIRMATIVE_PATTERNS (8 grupos — obrigatório por Lei 8.213/91 + Lei 12.990/2014)
```

**Passo 4 — Navigation:**
```python
# 8. Cria app/orchestrator/navigation_intent.py
#    - _PATTERNS_FALLBACK com 7 páginas e pesos
#    - _get_patterns() lê platform_manifest.yaml → fallback
#    - NavigationIntentDetector.detect() com interrogative dampening

# 9. Cria app/api/v1/navigation_intent.py
#    POST /api/v1/navigation-intent
```

### "Adiciona novo domain ao routing"

```python
# 1. Adiciona ao domain_routing.yaml:
#    new_domain:
#      - "novo\\s+pattern"

# 2. Cria app/domains/new_domain/config/capabilities.yaml:
#    intent_keywords:
#      "ação x": action_x

# 3. Em domain.py, adiciona:
#    _matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="new_domain")
#    async def process_intent(...): usa _matcher

# Sem restart obrigatório: DOMAIN_PATTERNS carrega em módulo-load
# Para reload: reiniciar o worker Uvicorn
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Intent Routing — v5

- **FastRouter:** `app/orchestrator/config/domain_routing.yaml` → regex Tier 4, sem LLM
- **Domain actions:** `app/domains/<X>/config/capabilities.yaml` → `intent_keywords` dict
- **Motor compartilhado:** `app/shared/services/keyword_intent_matcher.py`
- **Wizard:** `app/domains/ai/services/{intent_classifier,enhanced_intent_classifier}.py`
- **Navigation:** `app/orchestrator/navigation_intent.py` → POST /api/v1/navigation-intent
- Confidence FastRouter: `min(0.95, 0.7 + len(matched_text) * 0.02)`
- Penalidade de ambiguidade: gap < 0.1 → confidence -= 0.15
- normalize_domain_id(): wsi_assessment→cv_screening, interviewing→interview_scheduling
```

### Setup em Cursor rules

```
# .cursor/rules/intent-routing.mdc
- FastRouter confidence: 0.7+len(match)*0.02, capped 0.95
- Domain routing YAML: app/orchestrator/config/domain_routing.yaml
- capabilities.yaml format: intent_keywords: {keyword: action_id}
- KeywordIntentMatcher: from_keyword_map() for legacy dicts, from_yaml() for new format
- INFO query detection: 15 patterns in _INFO_PATTERNS (keyword_intent_matcher.py)
- NavigationIntentDetector: interrogative dampening *0.75, imperative boost +0.15
- AFFIRMATIVE_PATTERNS: required by Lei 8.213/91 (PCD), Lei 12.990/2014 (Negros)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| O que | Como adaptar |
|-------|-------------|
| Páginas do `NavigationIntentDetector` | Mudar `_PATTERNS_FALLBACK` para as páginas do v5 |
| Regex no `domain_routing.yaml` | Adicionar/remover padrões por domain — sem código |
| Keywords nos `capabilities.yaml` | Editar intent_keywords — sem código |
| `normalize_domain_id()` | Adicionar aliases para novos subagentes |
| Confidence thresholds | Ajustar `0.7` (base) e `0.02` (fator de especificidade) |
| INFO_PATTERNS | Adicionar mais padrões de portugûes/inglês |
| Tipos de IntentType/EnhancedIntentType | Adicionar novos tipos preservando os existentes |
| TECH_SKILLS / SOFT_SKILLS | Adicionar skills relevantes ao setor do v5 |

### NÃO pode adaptar (base arquitetural)

| O que | Por quê |
|-------|---------|
| **AFFIRMATIVE_PATTERNS nos 8 grupos** | Lei 8.213/91 (PCD ≥ 2%), Lei 12.990/2014 (pretos/pardos ≥ 20%), Convenção OIT sobre igualdade de oportunidades — a detecção de critérios afirmativos é obrigatória no fluxo de criação de vaga |
| **Shim `app/shared/services/` → `app/domains/ai/services/`** | Módulos externos importam via `app/shared/` — quebrar o shim quebra o wizard |
| **FastRouter como componente sem LLM** | Tier 4 existe para evitar custo de LLM nos 80% de queries óbvias — adicionar LLM aqui destroça o budget de tenant |
| **`normalize_domain_id()` para wsi/interviewing/scheduling** | Esses sub-IDs do YAML mapeiam para agents reais — mudança quebra o dispatch |
| **`_FINAL_CONFIDENCE_MIN = 0.50`** | Threshold mínimo para o NavigationIntentDetector retornar page — abaixo disso retorna `page=None` (comportamento deliberado para não sugerir navegação espúria) |
| **`build_usage_callback(tracking_context, agent_type="intent_classifier")`** | Rastreamento de custo por empresa — necessário para billing por tenant |

---

## Checklist de completude

- [ ] (P0) `domain_routing.yaml` tem padrões para todos os domains do v5
- [ ] (P0) `normalize_domain_id()` cobre todos os aliases de sub-agents
- [ ] (P0) `AFFIRMATIVE_PATTERNS` tem PCD, Pessoas Negras, Mulheres — obrigatório para wizard de vagas
- [ ] (P1) `capabilities.yaml` criado para todos os domains com agent
- [ ] (P1) `process_intent()` em todos os domains usa `KeywordIntentMatcher` (não loop manual)
- [ ] (P1) FastRouter tem fallback hardcoded (funciona sem YAML)
- [ ] (P1) `NavigationIntentDetector._get_patterns()` tem fallback (funciona sem platform_manifest.yaml)
- [ ] (P1) Shims em `app/shared/services/` apontam para implementações reais
- [ ] (P2) Shadow `_DOMAIN_MATCHER` no FastRouter para telemetria de migração
- [ ] (P2) Ambiguity penalty logada como WARNING para monitoramento
- [ ] (P2) `is_info_query()` chamado antes de `match()` em todos os domains
- [ ] (P2) `POST /api/v1/navigation-intent` registrado em `app/api/routes.py`
- [ ] (P2) Custo do wizard rastreado via `build_usage_callback`

---

## Gotchas e erros comuns

### 1. Regex case-sensitive no domain_routing.yaml

O YAML é carregado com `re.IGNORECASE | re.UNICODE`. Mas ao **escrever os padrões**, evite assumir isso — use `[Vv]aga` ou `vaga` (lowercase). Se tiver caracteres especiais regex no YAML (`\s`, `\b`, `\w`), use `\\s`, `\\b`, `\\w` no YAML (dupla barra).

### 2. `capabilities.yaml` vs `from_yaml()` vs `from_keyword_map()`

O analytics usa `intent_keywords: dict` (formato legado) com `from_keyword_map()`. O `from_yaml()` espera `intents: list[{keywords, action, type, confidence}]`. Se criar novo domain com formato novo, use `from_yaml()`. Se migrar legado, use `from_keyword_map()`. **Não misture** num mesmo domain.

### 3. FastRouter confidence vs domain.process_intent confidence

FastRouter retorna confidence 0.70–0.95 (regex). `process_intent()` retorna 0.30–0.95 (keyword). São escalas diferentes usadas em contextos diferentes. O `CascadedRouter` usa FastRouter confidence para decidir se pula para Tier 5 (LLM) ou não. A confidence de `process_intent()` vai para o `AgentOutput` e para métricas de qualidade.

### 4. normalize_domain_id() esquecido

Se criar sub-domain no YAML (`sourcing_enrich`, `kanban_search`) sem adicionar ao `_DOMAIN_ID_NORMALIZE`, o dispatch funciona — mas o agent lookup pode falhar se o `ReactAgentRegistry` não tiver um agent registrado para `sourcing_enrich`. Dois comportamentos possíveis: (a) sub-domain routing é intencional e o agent existe, ou (b) deve normalizar para o agent pai.

### 5. NavigationIntentDetector usa keyword simples, não regex

Os padrões em `_PATTERNS_FALLBACK` são keyword substring (não regex compilado). `"vagas" in text` é substring match, não regex. Ao adicionar novos patterns, o peso deve refletir a especificidade: palavras genéricas (0.2–0.3), frases de ação (0.7–1.0).

### 6. Wizard classifier em staging — LLM via `llm_service`

`IntentClassifierService` e `EnhancedIntentClassifierService` usam `llm_service` direto (de `app/domains/ai/services/llm`), **não** via `get_provider_for_tenant()`. Isso significa que o provider do wizard não é o BYOK por tenant — é o provider padrão configurado em `llm_service`. No v5, se BYOK for necessário no wizard, trocar para `get_provider_for_tenant(tenant_id)`.

### 7. Interrogative dampening vs imperative boost

BUG-18: antes do fix, frases como "me leva pra vagas?" tinham confidence *= 0.45 porque terminavam com "?". O fix detecta `_NAV_IMPERATIVE_PREFIXES` primeiro e aplica +0.15 em vez de *0.75. Se customizar os prefixes, preservar esta lógica — é difícil de debugar no frontend.

---

## Testes obrigatórios

```
tests/unit/services/test_keyword_intent_matcher.py
  - test_info_query_detection: "como funciona triagem?" → is_info=True
  - test_action_query: "criar vaga de engenheiro" → IntentType.ACTION
  - test_confidence_scales_with_length: keyword de 20 chars > keyword de 5 chars
  - test_from_yaml_vs_from_keyword_map: mesmo resultado para mesmo input

tests/unit/orchestrator/test_fast_router.py
  - test_yaml_load: domain_routing.yaml carrega sem erro
  - test_hardcoded_fallback: funciona se YAML ausente
  - test_ambiguity_penalty: gap < 0.1 → confidence decreases
  - test_normalize_domain_id: wsi_assessment → cv_screening
  - test_match_returns_none_for_unknown: query sem padrão → None

tests/unit/orchestrator/test_navigation_intent.py
  - test_imperative_nav_boost: "me leva pra vagas" → confidence ≥ 0.75
  - test_question_dampening: "o que é vagas?" → confidence < 0.75
  - test_interrogative_imperative_exception: "me leva pra vagas?" → NOT dampened (BUG-18)
  - test_all_7_pages: cada página tem pelo menos 1 pattern strong

tests/unit/services/test_intent_classifier.py
  - test_correction_quick: "na verdade não é isso" → CORRECTION confidence ≥ 0.9
  - test_reuse_vacancy_indicators: "aproveitar vaga anterior" → REUSE_VACANCY
  - test_affirmative_patterns: "vaga para PCD" → is_afirmativa=True
  - test_salary_extraction: "R$ 15k-20k" → salario_min=15000, salario_max=20000
  - test_entity_merge_llm_wins: LLM entity sobrescreve regex para campos simples

tests/integration/test_routing_e2e.py
  - test_full_routing_pipeline: query → FastRouter → domain.process_intent → action_id
  - test_fallback_to_llm_cascade: query sem padrão regex → Tier 5 ativado
```

---

## Referências

- **CascadedRouter 8 tiers:** `themes/infrastructure/I3_ORCHESTRATION.md` (Tier 4 = FastRouter)
- **Domain Architecture:** `themes/infrastructure/I1_AGENT_ARCHITECTURE.md` (domains como consumers do routing)
- **Tool Architecture:** `themes/infrastructure/I2_TOOL_ARCHITECTURE.md` (action_id → tool_id mapeamento)
- **Compliance:** `themes/compliance/C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md` (AFFIRMATIVE_PATTERNS — Lei 8.213/91, Lei 12.990/2014)
- **Reconstruction Guide:** `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §E (cascade tier 1-3)
- **LIA-I01:** `keyword_intent_matcher.py` module docstring — `LIA-I01: Shared Keyword Intent Matcher`
- **LIA-I05:** Log tag em fast_router.py e domain.py — Fase 5 migration para YAML-driven routing
- **LIA-I06:** Log tag em fast_router.py — YAML load warnings
- **LIA-I07:** Log tag em domain.py — `[LIA-I07] Check if query is an info request`
