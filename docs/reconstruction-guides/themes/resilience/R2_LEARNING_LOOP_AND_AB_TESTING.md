# Theme: Learning Loop + Calibration + A/B Testing — Resilience Layer

## O que é este tema

Learning Loop é a camada de **melhoria contínua** da LIA: observa silenciosamente o que recrutadores aceitam, modificam ou rejeitam (sem UI de feedback explícita), extrai padrões por empresa, e usa esses padrões para melhorar sugestões futuras. É complementado por A/B Testing de prompts, calibração de scoring de candidatos, predição de time-to-fill (ML), e exportação de dados de fine-tuning.

**5 sub-sistemas:**
1. **LearningLoopService** — captura de feedback + extração de padrões por empresa
2. **ABTestingService** + **ExperimentManager** — experimentos de prompt com significância estatística
3. **LearningSnapshotService** — snapshots Redis para rollback de batches problemáticos
4. **TTFPredictor** — ML (XGBoost) + fallback heurístico para predição de time-to-fill
5. **FineTuningExportService** + **LearningExtractor** — exportação de dados de treinamento com PII masking

**Boundary com temas irmãos:**
- **R4 Background Jobs**: `LearningLoopService.analyze_patterns()` roda como Celery worker
- **P3 Memory**: `LearningExtractor` alimenta `LongTermMemory` (P3) após cada ReAct loop
- **C1 Fairness**: `capture_feedback()` com REJECTED/IGNORED dispara `ModelDriftService.check_drift_trigger()` — conecta feedback de rejeição ao monitoramento de viés
- **I5 Observability**: `ModelDriftService` é chamado ao detectar feedback negativo

---

## Arquivos conectados (8 total)

### Camada Código (8 arquivos Python)

| Arquivo | Path canônico | Responsabilidade |
|---------|--------------|-----------------|
| `learning_loop_service.py` | `app/shared/learning/learning_loop_service.py` | Captura silenciosa + extração de padrões. 1133 linhas |
| `ab_testing_service.py` | `app/shared/learning/ab_testing_service.py` | A/B de prompts com PostgreSQL, significância estatística. 340 linhas |
| `learning_snapshot_service.py` | `app/shared/learning/learning_snapshot_service.py` | Snapshots Redis com rollback. TTL 30 dias, max 5/empresa |
| `template_learning_service.py` | `app/shared/learning/template_learning_service.py` | Aprende templates de vagas após ≥ 3 jobs similares |
| `finetuning_export.py` | `app/shared/learning/finetuning_export.py` | Exportação JSONL com PII masking completo para fine-tuning |
| `learning_extractor.py` | `libs/agents-core/lia_agents_core/learning_extractor.py` | Extrai aprendizados de ReActState pós-execução → LongTermMemory |
| `ttf_predictor.py` | `app/shared/ml/ttf_predictor.py` | XGBoost TTF predictor v2.0.0 + fallback heurístico por senioridade |
| `ab_testing.py` | `app/shared/ab_testing.py` | ExperimentManager in-memory (singleton), PromptVariant, PromptExperiment |

### Modelos de dados conectados

| Modelo | Tabela | Uso |
|--------|--------|-----|
| `FeedbackEvent` | `feedback_events` | `lia_models.intelligent_cache` — evento de feedback silent capture |
| `ABTestResult` | `ab_test_results` | `lia_models.ab_testing` — métrica por variante/sessão |
| `PromptVariant` | `prompt_variants` | `lia_models.ab_testing` — variante com traffic_percentage |
| `CalibrationFeedback` | `calibration_feedback` | `lia_models.calibration` — feedback de scoring de candidato |
| `CalibrationSession` | `calibration_sessions` | `lia_models.calibration` — sessão de calibração com status |
| `SuggestionFeedback` | — | `lia_models.feedback_learning` — para finetuning export |
| `WizardFeedback` | — | `lia_models.feedback_learning` — para finetuning export |
| `JobOutcome` | — | `lia_models.feedback_learning` — resultado de contratação |
| `LearningPattern` | — | patterns extraídos pela LearningLoopService |
| `JobTemplate` | `job_templates` | templates aprendidos por TemplateLearningService |

### Integration points

- `app/jobs/celery_tasks.py` → `LearningLoopService.analyze_patterns()` como Celery task
- `app/domains/job_management/agents/wizard_react_agent.py` → `capture_from_wizard_update()` ao salvar cada campo
- `libs/agents-core/lia_agents_core/react_loop.py` → `LearningExtractor.extract()` ao finalizar loop
- `libs/agents-core/lia_agents_core/long_term_memory.py` → destino dos aprendizados do LearningExtractor
- `app/shared/observability/model_drift_service.py` → disparado por feedback REJECTED/IGNORED

---

## Lógica IN → OUT

### 1. LearningLoopService — captura silenciosa

#### Input

```python
FeedbackCapture(
    company_id="...",      # OBRIGATÓRIO — partição por empresa
    field_name="salary_max",
    suggested_value=18000,
    final_value=20000,
    outcome=FeedbackOutcome.MODIFIED,  # calculado por _determine_outcome()
    session_id="...", job_id="...", stage="stage_2",
    role="desenvolvedor", seniority="senior", ...
)
```

#### Determinação de outcome (automática)

```python
def _determine_outcome(suggested, final, explicitly_rejected=False):
    if explicitly_rejected:         → REJECTED
    if final_value is None:         → IGNORED
    if _values_match(suggested, final): → ACCEPTED  # str comparison, JSON sort, set comparison
    else:                           → MODIFIED
```

#### Processing — capture_feedback()

1. Se `outcome == MODIFIED` → `_calculate_modification_delta()` (calcula % mudança salarial, skills adicionadas/removidas, benefits delta)
2. Cria `FeedbackEvent` e persiste via `db.add(event) + await db.commit()`
3. Se `outcome in (REJECTED, IGNORED)` → `asyncio.create_task(ModelDriftService().check_drift_trigger())` (non-blocking)

#### Convenience: capture_from_wizard_update()

Wrapper chamado pelo wizard ao finalizar campos. Recebe `suggested_value + final_value + explicitly_rejected` e calcula outcome automaticamente.

#### Pattern Extraction — CONFIDENCE_THRESHOLDS

| Nível | Mínimo de amostras | Score base |
|-------|:-:|:-:|
| `high` | 20 | 0.9 |
| `medium` | 10 | 0.7 |
| `low` | 5 | 0.5 |
| `very_low` | < 5 | 0.3 |

**ACCEPTANCE_THRESHOLDS:** `promote=0.75` (pattern promovido), `demote=0.25` (pattern demovido).

**Score adjustment:** acceptance_rate > 0.8 → score × 1.1 (cap 1.0); < 0.5 → score × 0.8; high confidence com rate baixo → downgrade para medium.

#### 7 PatternTypes

```python
class PatternType(StrEnum):
    SALARY_PREFERENCE = "salary_preference"
    SKILL_PREFERENCE = "skill_preference"
    BENEFIT_PREFERENCE = "benefit_preference"
    WORK_MODEL_PREFERENCE = "work_model_preference"
    SCREENING_PREFERENCE = "screening_preference"
    JD_STYLE_PREFERENCE = "jd_style_preference"
    SOURCE_TRUST = "source_trust"
```

### 2. ABTestingService — A/B de prompts (PostgreSQL-backed)

#### Assignment

```python
def _hash_assignment(test_name, session_id) -> int:
    combined = f"{test_name}:{session_id}"
    hash_val = hashlib.md5(combined.encode()).hexdigest()
    return int(hash_val, 16)
# bucket = hash_val % 10000
# cumulative traffic_percentage × 100 → threshold
# determinístico: mesma session_id sempre cai na mesma variante
```

#### get_variant()

1. Query `PromptVariant` where `test_name == test_name AND is_active == True` ORDER BY variant_name
2. MD5 hash do `(test_name, session_id)` → bucket 0-9999
3. Varredura cumulativa de `traffic_percentage`: primeiro variant onde `cumulative × 100 > bucket`
4. Retorna `{test_name, variant_name, prompt_template, variant_id}`

#### record_metric()

Cria `ABTestResult(test_name, variant_name, session_id, company_id, metric_name, metric_value, context)`.

#### get_test_results()

Para cada variante e métrica: calcula `mean`, `std_dev`, `SE`, `CI_95 = (mean ± 1.96 × SE)`, `p_value = 1 - 0.5 × (1 + erf(|z|/√2))`.

**N_MIN_PER_VARIANT = 30** — recomendação mínima para significância; resultado retorna `recommendation: "insufficient_data"` se abaixo.

#### ExperimentManager (ab_testing.py) — in-memory singleton

```python
@dataclass
class PromptVariant:
    variant_id, prompt, weight, impressions, outcomes: list
    avg_satisfaction: float  # property: media de outcomes["satisfaction"]

class ExperimentManager:
    _instance: Optional['ExperimentManager'] = None  # singleton
    # create_experiment() → PromptExperiment
    # get_variant(name, user_id) → PromptVariant (MD5 hash de user_id)
    # record_outcome(name, user_id, metrics)
```

Diferença da `ABTestingService`: ExperimentManager é in-memory (sem DB), para experimentos efêmeros ou pré-produção. `ABTestingService` persiste no PostgreSQL.

### 3. LearningSnapshotService — rollback de batches

**Redis keys:**
- `learning_snapshot:{company_id}:{timestamp}` — payload JSON dos LearningPatterns
- `learning_snapshot:{company_id}:index` — lista JSON dos últimos N snapshot keys

```python
SNAPSHOT_TTL_SECONDS = 30 * 24 * 3600  # 30 dias
MAX_SNAPSHOTS = 5  # LRU implícito via index por empresa
```

**save_snapshot():** chamado *antes* de cada batch de learning ser aplicado. Fail-safe: se Redis indisponível, retorna `None` sem erro.

**rollback_to_latest():** restaura `LearningPattern`s do snapshot mais recente. Chamado por endpoint admin ou manualmente.

**Por que existe:** se um batch de learning apresentar viés detectado posteriormente (drift), é possível reverter para o estado anterior sem reprocessar todo o histórico.

### 4. TTFPredictor — predição de time-to-fill

**Modelo:** XGBoost v2.0.0, path `app/shared/ml/models/ttf_model.joblib` + `app/shared/ml/models/ttf_encoder.joblib`.

**Inicialização:** `_load_model()` → se arquivo não existe → log info + usa heurístico. Se falha ao carregar → warning + heurístico.

**Feature vector (ML):**
```python
[
    _SENIORITY_ORDINAL[seniority],       # ordinal: estagiário=0 ... c-level=8
    _WORK_MODEL_MAP[work_model],          # presencial=0, híbrido=1, remoto=2
    urgency_level,                         # 1-5
    num_candidates,                        # int
    num_pipeline_stages,                   # default 4
    salary_min / 1000,                     # normalizado
]
```

**Heurístico (fallback):**

| Seniority | Base (dias) |
|-----------|:-----------:|
| estagiário | 20 |
| júnior | 25 |
| pleno | 35 |
| sênior | 45 |
| especialista | 50 |
| lead | 55 |
| gerente | 60 |
| diretor | 90 |
| vp / c-level | 120 |

Ajustes heurístico: `remoto × 0.9`, `presencial × 1.05`.

**Output:**
```python
TTFPrediction(
    predicted_days=42,
    confidence=0.75,       # ML fixo; heurístico varia
    source="ml_model",     # ou "heuristic"
    features_used=["seniority", "work_model", ...],
    model_version="2.0.0", # ou None para heurístico
)
```

**ModelRegistry:** após load, registra como `"time_to_fill_predictor"` versão `"2.0.0"` em `app.services.ml.model_registry`.

### 5. FineTuningExportService + LearningExtractor

#### PII masking (FineTuningExportService)

4 regexes para anonimização antes de exportar training data:

```python
EMAIL_PATTERN  = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'     → [EMAIL]
PHONE_PATTERN  = r'\(?\d{2}\)?\s?\d{4,5}[-.\s]?\d{4}'                    → [PHONE]
CPF_PATTERN    = r'\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}'                       → [CPF]
NAME_PATTERN   = r'\b[A-ZÁÉÍÓÚÂÊÎÔÛÃÕÇ][a-z...]+...'                     → [NAME]
```

`TECHNICAL_TERMS` (40+ termos): preservados no pattern de nomes — "Senior", "Python", "React" etc não são marcados como `[NAME]`.

`export_wizard_interactions()`: filtra por `min_quality_score=0.7`, exporta apenas interações de vagas com `JobOutcomeType.FILLED` (contratação concluída).

#### LearningExtractor (agents-core)

Analisa `ReActState` pós-execução de ReAct loop e extrai 3 categorias:

```python
def extract(state: ReActState, domain: str, context: dict) -> List[dict]:
    learnings = []
    learnings.extend(_extract_patterns(state, domain))      # tool-usage patterns
    learnings.extend(_extract_preferences(state, domain, context))  # domain preferences
    learnings.extend(_extract_outcomes(state, domain))      # score outcomes
    return _deduplicate(learnings)
# Cada learning: {"type": ..., "key": ..., "value": ..., "tags": [...]}
```

`SCORE_KEYS = {"fit_score", "wsi_score", "match_score", "culture_score", "technical_score", "overall_score"}` — scores rastreados para outcome extraction.

Fail-safe: cada extrator tem `try/except → logger.warning` — falha de extração não quebra o loop.

Destino: `LongTermMemory.upsert()` por empresa+domínio (P3).

### 6. TemplateLearningService

**Goal:** "80% faster 10th job creation" via templates aprendidos automaticamente.

`learn_from_job_creation()`:
1. `JobTemplate.normalize_title(title)` — normaliza o cargo
2. `_find_similar_jobs(company_id, normalized_title, days=365)` — busca jobs similares do último ano
3. Se `len(similar_jobs) >= 3` E template ainda não existe → `_create_learned_template()`
4. Se `template_used` fornecido → `_record_template_usage()` para tracking de efetividade

### 7. CalibrationWeight model

`CalibrationFeedback` — feedback do recrutador sobre candidatos específicos (aceito/rejeitado com reason).

`CalibrationSession` — sessão com status granular:

```python
class CalibrationSessionStatus(str, Enum):
    AWAITING_FEEDBACK = "awaiting_feedback"
    LEARNING = "learning"
    CONFIRMED = "confirmed"
    SOURCING_IN_PROGRESS = "sourcing_in_progress"
    COMPLETED = "completed"
```

---

## Instruções para Claude Code / Cursor

### "Implementa Learning Loop no v5"

```
1. Criar app/shared/learning/__init__.py (vazio)

2. Criar app/shared/learning/learning_loop_service.py
   - FeedbackOutcome (StrEnum: 4 valores), PatternType (StrEnum: 7 valores)
   - FeedbackCapture (dataclass: 16 campos), LearnedPattern (dataclass: 7 campos)
   - LearningLoopService com CONFIDENCE_THRESHOLDS + ACCEPTANCE_THRESHOLDS
   - capture_feedback(): escreve FeedbackEvent, dispara drift check se REJECTED/IGNORED
   - _determine_outcome(): explicitly_rejected→REJECTED, None→IGNORED, match→ACCEPTED, else→MODIFIED
   - _calculate_modification_delta(): delta numérico para salary, skills delta para lists

3. Criar app/shared/learning/ab_testing_service.py
   - ABTestingService: get_variant() (MD5 hash, bucket 10000), record_metric(), get_test_results()
   - N_MIN_PER_VARIANT = 30; _compute_p_value() via math.erf
   - Depende de lia_models.ab_testing: ABTestResult, PromptVariant

4. Criar app/shared/learning/learning_snapshot_service.py
   - LearningSnapshotService: save_snapshot(), rollback_to_latest()
   - Redis keys: learning_snapshot:{company_id}:{ts} + index
   - SNAPSHOT_TTL_SECONDS=30×24×3600, MAX_SNAPSHOTS=5
   - Fail-safe: retorna None se Redis indisponível

5. Criar app/shared/ml/ttf_predictor.py
   - TTFPredictor: _load_model() via joblib, predict() → ML ou heurístico
   - _SENIORITY_DEFAULTS dict (10 entries) + _SENIORITY_ORDINAL + _WORK_MODEL_MAP
   - TTFPrediction dataclass (predicted_days, confidence, source, features_used, model_version)
   - Register em ModelRegistry como "time_to_fill_predictor" v2.0.0

6. Criar app/shared/learning/finetuning_export.py
   - FineTuningExportService: mask_pii() com 4 regexes + TECHNICAL_TERMS exclusion
   - export_wizard_interactions() com min_quality_score=0.7, formato JSONL

7. Criar libs/agents-core/lia_agents_core/learning_extractor.py
   - LearningExtractor: extract(state, domain, context) → list[dict]
   - 3 extractors: _extract_patterns, _extract_preferences, _extract_outcomes
   - SCORE_KEYS frozenset; _deduplicate(); fail-safe por extractor

8. Criar app/shared/ab_testing.py
   - PromptVariant + PromptExperiment dataclasses
   - ExperimentManager singleton: create_experiment, get_variant (MD5 user_id), record_outcome

9. Wiring em Celery (R4):
   - @app.task def run_learning_loop(company_id): LearningLoopService().analyze_patterns()
   - @app.task def export_finetuning_data(): FineTuningExportService().export_wizard_interactions()
```

### Setup em CLAUDE.md (snippet pronto)

```markdown
## Learning Loop — R2
- LearningLoopService.capture_from_wizard_update() ao salvar QUALQUER campo do wizard
- FeedbackOutcome determinado automaticamente — não passar explicitamente (exceto explicitly_rejected=True)
- ABTestingService.N_MIN_PER_VARIANT=30 — não declarar winner antes de atingir mínimo
- LearningSnapshotService.save_snapshot() ANTES de aplicar qualquer batch de patterns
- TTFPredictor.predict() — sempre fail-safe (heurístico se modelo ausente); confidence 0.75 ML / variável heurístico
- FineTuningExportService.mask_pii() OBRIGATÓRIO antes de exportar qualquer dado de treinamento
- LearningExtractor: fail-safe por extrator — falha de extração nunca quebra ReAct loop
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

| Item | Flexibilidade |
|------|--------------|
| `PatternType` valores | Adicionar novos tipos conforme domínios do v5 |
| `_SENIORITY_DEFAULTS` / `_SENIORITY_ORDINAL` | Ajustar se v5 usa nomenclatura diferente de senioridade |
| `CONFIDENCE_THRESHOLDS` | Ajustar mínimos de amostras |
| `ACCEPTANCE_THRESHOLDS` (promote/demote) | Ajustar sensibilidade do learning |
| `MAX_SNAPSHOTS` | Aumentar/diminuir conforme capacidade Redis |
| `ExperimentManager` (in-memory) | Substituir por Redis-backed se precisar persistência |
| PII `TECHNICAL_TERMS` | Expandir conforme stack tecnológico do v5 |
| XGBoost model artifacts (`ttf_model.joblib`) | Substituir por modelo re-treinado com dados do v5 |

### NÃO pode adaptar (contrato ou LGPD)

| Item | Razão |
|------|-------|
| `mask_pii()` com 4 regexes obrigatórias (EMAIL, PHONE, CPF, NAME) | LGPD Art. 9 (finalidade) + Art. 6 (minimização) — training data não pode conter PII de candidatos |
| `company_id` em todos os `FeedbackCapture` + `_sessions` partitioning | Multi-tenancy — patterns de uma empresa jamais devem contaminar outra |
| `explicitly_rejected=True` como override de outcome | Segurança de dados — usuário que explicitamente rejeita sugestão não pode ter outcome calculado como MODIFIED |
| `N_MIN_PER_VARIANT = 30` como mínimo estatístico | Viés de decisão — declarar winner prematuramente pode viesar prompts para segmento não-representativo |
| Fail-safe em todos os extractors e no save_snapshot() | Resiliência — learning nunca pode quebrar o fluxo principal de produção |

---

## Silver Medalist Service — Reengajamento de Candidatos Quase Aprovados

> **Verificado via SSH 2026-04-24.** Fonte: `app/shared/services/silver_medalist_service.py` (297 linhas).

O **Silver Medalist Service** ressurface candidatos que chegaram à etapa de entrevista em processos anteriores mas não foram contratados — os "quase aprovados" (medalhistas de prata). É um subsistema de **learning de pipeline**: o sistema aprende quais candidatos já foram qualificados pela empresa e os reutiliza como leads quentes para novas vagas similares.

> ⚠️ **DEPRECATED** — `@deprecated since=2026-04-17, @remove-after=2026-07-16`  
> `@replacement = integrations_hub/rails_adapter::silver_medalist`  
> **Não migrar para um domain** — rotear via `integrations_hub/rails_adapter`. Será deletado após o handoff rails.

### Definição de Silver Medalist

Um candidato é Silver Medalist se:
1. Chegou em pelo menos `'interview_hr'` em uma vaga anterior (qualquer etapa de entrevista)
2. **Não** foi contratado nessa vaga (`stage != 'hired'` e `status != 'hired'`)
3. **Não** está atualmente ativo na vaga alvo (não aparece em `vacancy_candidates WHERE vacancy_id = :target`)

### INTERVIEW_STAGES — Estágios Elegíveis

```python
INTERVIEW_STAGES = {
    "interview_hr", "entrevista_hr", "entrevista_rh",
    "interview_technical", "entrevista_tecnica",
    "interview_manager", "entrevista_gestor",
    "interview_final", "entrevista_final",
    "offer", "proposta",
}
```

### STAGE_WEIGHTS — Pesos de Relevância por Etapa

```python
STAGE_WEIGHTS = {
    "offer": 1.0,           "proposta": 1.0,
    "interview_final": 0.9, "entrevista_final": 0.9,
    "interview_manager": 0.8, "entrevista_gestor": 0.8,
    "interview_technical": 0.7, "entrevista_tecnica": 0.7,
    "interview_hr": 0.5,    "entrevista_hr": 0.5, "entrevista_rh": 0.5,
}
```

### Fórmula de Relevância Composta

```python
# Três componentes ponderados — resultado em [0, 1]
relevance = round(
    0.4 * stage_weight(reached_stage)   # etapa mais profunda = sinal mais forte
    + 0.35 * recency_score(days_ago)    # candidatura mais recente = mais relevante
    + 0.25 * lia_score_normalized,      # score LIA do processo anterior
    3
)

def _recency_score(days_ago: float) -> float:
    """Decaimento linear: 1.0 em 0 dias → 0.1 em 180 dias."""
    if days_ago <= 0:
        return 1.0
    return max(0.1, 1.0 - (days_ago / 180.0))

# LIA score normalization (SSOT: lia_score_service.py:139):
lia_score_normalized = max(0.0, min(1.0, raw_lia_score / 100.0))
# raw_lia_score vem de vacancy_candidates.lia_score — já em escala /100
# clamp defensivo cobre dados corrompidos (#524 fechado)
```

### Métodos da Classe

```python
class SilverMedalistService:
    singleton = silver_medalist_service  # módulo-level

    async def find_for_vacancy(
        target_vacancy_id: str,
        company_id: str,       # SEMPRE do JWT — isola tenant
        limit: int = 20,
        max_days_lookback: int = 180,
        db: AsyncSession | None = None,
    ) -> list[dict]:
        """
        Candidatos quase aprovados relevantes para a vaga alvo.
        Retorna lista rankeada por relevance_score DESC.
        Cada item: {candidate_id, candidate_name, candidate_email, candidate_phone,
                    past_vacancy_id, past_vacancy_title, reached_stage,
                    past_lia_score, days_since_process, relevance_score, last_activity}
        """

    async def find_for_company(
        company_id: str,
        limit: int = 50,
        max_days_lookback: int = 90,  # janela menor — pool geral
        db: AsyncSession | None = None,
    ) -> list[dict]:
        """
        Pool geral de silver medalists da empresa (não específico por vaga).
        Usado pelo ProactiveAgentWorker para sugerir candidatos em vagas ativas.
        """
```

### SQL — Tabelas consultadas

```sql
-- find_for_vacancy:
FROM vacancy_candidates vc
JOIN candidates c ON c.id = vc.candidate_id
JOIN job_vacancies jv ON jv.id = vc.vacancy_id
WHERE jv.company_id::text = :company_id          -- isolamento multi-tenant
  AND vc.vacancy_id::text != :target_vacancy_id  -- excluir vaga atual
  AND vc.stage NOT IN ('hired', 'contratado')    -- não contratados
  AND vc.status NOT IN ('hired', 'contratado')
  AND vc.updated_at >= :cutoff                   -- max_days_lookback
  AND vc.stage IN (<INTERVIEW_STAGES>)           -- chegaram em entrevista
  AND vc.candidate_id NOT IN (                   -- não estão na vaga alvo
      SELECT candidate_id FROM vacancy_candidates
      WHERE vacancy_id::text = :target_vacancy_id
  )
-- Resultado: limit * 3 rows → rank in Python → return top limit
-- Dedup: apenas o melhor processo anterior por candidato (seen_candidates set)
```

### Comportamento de Falha

Ambos os métodos têm `try/except Exception → return []` com `logger.warning`. O serviço é **fail-open** — falha silenciosa sem propagação para o fluxo principal.

### Integração com Learning Loop

```
ProactiveAgentWorker.run()
  └─► silver_medalist_service.find_for_company(company_id)
        └─► Resultados injetados como "warm candidates" em insights proativos
            (via TastingEngine ou ProactiveWorker.emit_insight)
```

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `mask_pii()` chamado em TODOS os exports de training data — LGPD Art. 9
- [ ] **(P0)** `company_id` presente em todos os `FeedbackCapture` — sem learning cross-tenant
- [ ] **(P0)** `save_snapshot()` chamado ANTES de qualquer batch de patterns — rollback disponível
- [ ] **(P1)** `capture_from_wizard_update()` wired em wizard agent ao salvar cada campo
- [ ] **(P1)** `LearningExtractor.extract()` chamado ao finalizar ReAct loop → salvar em LongTermMemory
- [ ] **(P1)** `N_MIN_PER_VARIANT = 30` respeitado antes de declarar winner em A/B test
- [ ] **(P1)** `TTFPredictor` com heurístico funcional mesmo sem modelo treinado
- [ ] **(P1)** `ModelDriftService.check_drift_trigger()` chamado por feedback REJECTED/IGNORED
- [ ] **(P2)** `TemplateLearningService.learn_from_job_creation()` chamado ao finalizar cada vaga
- [ ] **(P2)** `ABTestResult` + `PromptVariant` models em `lia_models.ab_testing`
- [ ] **(P2)** `CalibrationSession` com 5 status granulares documentados para o frontend
- [ ] **(P2)** `TTFPredictor` registrado em ModelRegistry com version e features

---

## Gotchas e erros comuns

### 1. `capture_from_wizard_update()` sem company_id → cross-tenant leak

**Problema:** Se `company_id` vier do payload da requisição (em vez do JWT), uma empresa pode poluir os patterns de outra — ou deliberadamente injetar patterns falsos.

**Correto:** `company_id` sempre do JWT (`request.state.company_id` / `get_verified_company_id()`), nunca do body.

### 2. Modificar `_determine_outcome()` para retornar ACCEPTED quando `final_value == None`

**Problema:** Quando `final_value is None`, o correto é IGNORED (usuário não confirmou). Retornar ACCEPTED inflaria artificialmente a taxa de aceitação.

**Correto:** `if final_value is None: return FeedbackOutcome.IGNORED` antes de comparar valores.

### 3. `ExperimentManager` singleton ≠ `ABTestingService` (PostgreSQL)

**Problema:** Usar `ExperimentManager.get_variant()` em produção perde os dados ao reiniciar o processo (in-memory). `ABTestingService` persiste no PostgreSQL e deve ser usado para experimentos de produção.

**Correto:** `ExperimentManager` para testes locais/ephemeral; `ABTestingService` para experimentos de produção com análise estatística.

### 4. `save_snapshot()` fail-safe pode dar falsa sensação de segurança

**Problema:** Se Redis estiver down e `save_snapshot()` retornar `None`, o batch é aplicado sem snapshot. Se o batch for problemático, não há rollback disponível.

**Correto:** Logar warning quando snapshot não disponível. Considerar bloquear batch em ambiente produtivo se snapshot falhar (tradeoff reliability × safety).

### 5. `TTFPredictor.predict()` confidence=0.75 fixo para ML

**Problema:** O modelo XGBoost retorna confidence fixo de 0.75 independente do input. Para inputs fora da distribuição de treinamento (cargos raros, salários extremos), a confiança real pode ser bem menor.

**Correto:** Em v5, implementar `predict_proba()` ou usar calibração de confiança por SHAP values.

### 6. `TemplateLearningService`: template criado com dados "stale"

**Problema:** O template é criado com base em jobs dos últimos 365 dias. Se o mercado mudou (stack tecnológico, benefícios), o template pode refletir práticas desatualizadas.

**Correto:** `days=365` é configurável — considerar `days=180` para contextos de alto dinamismo.

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| `test_capture_feedback_accepted` | `tests/unit/test_learning_loop.py` | Suggested=final → ACCEPTED |
| `test_capture_feedback_modified` | `tests/unit/test_learning_loop.py` | Suggested=15000, final=18000 → MODIFIED com delta |
| `test_capture_feedback_ignored` | `tests/unit/test_learning_loop.py` | final_value=None → IGNORED |
| `test_capture_triggers_drift` | `tests/unit/test_learning_loop.py` | REJECTED → ModelDriftService chamado |
| `test_no_cross_tenant_patterns` | `tests/integration/test_learning_isolation.py` | Patterns empresa A não vazam para empresa B |
| `test_ab_deterministic_assignment` | `tests/unit/test_ab_testing.py` | Mesma session_id sempre cai na mesma variante |
| `test_ab_insufficient_data` | `tests/unit/test_ab_testing.py` | n < 30 → recommendation='insufficient_data' |
| `test_snapshot_rollback` | `tests/integration/test_learning_snapshot.py` | save + apply batch + rollback → patterns restaurados |
| `test_snapshot_fail_safe` | `tests/unit/test_learning_snapshot.py` | Redis down → save_snapshot() retorna None sem exception |
| `test_ttf_heuristic_fallback` | `tests/unit/test_ttf_predictor.py` | Sem modelo → heurístico correto por seniority |
| `test_ttf_ml_predict` | `tests/unit/test_ttf_predictor.py` | Com modelo mockado → source='ml_model', confidence=0.75 |
| `test_mask_pii_complete` | `tests/unit/test_finetuning_export.py` | Email, telefone, CPF, nome mascarados; "Python" preservado |
| `test_learning_extractor_failsafe` | `tests/unit/test_learning_extractor.py` | Extractor falha → warning logado, outros extractors continuam |
| `test_template_created_after_3_jobs` | `tests/unit/test_template_learning.py` | 3+ jobs similares → template criado automaticamente |

---

## Referências

### Código (SSoT)
- `app/shared/learning/learning_loop_service.py` (1133 linhas)
- `app/shared/learning/ab_testing_service.py` (340 linhas)
- `app/shared/learning/learning_snapshot_service.py`
- `app/shared/learning/template_learning_service.py`
- `app/shared/learning/finetuning_export.py`
- `libs/agents-core/lia_agents_core/learning_extractor.py`
- `app/shared/ml/ttf_predictor.py`
- `app/shared/ab_testing.py`
- `libs/models/lia_models/calibration.py`

### Bundles e Guides
- Reconstruction Guide `RESILIENCE_LEARNING` Parte B — Learning Loop (overview de sub-sistemas)
- Thematic Doc P3 (`P3_CONVERSATION_MEMORY.md`) — `LongTermMemory` recebe aprendizados do `LearningExtractor`
- Thematic Doc R4 (`R4_BACKGROUND_JOBS_AND_SCHEDULERS.md`) — Celery tasks que executam `analyze_patterns()` e `export_finetuning_data()`
- Thematic Doc C1 (`C1_FAIRNESS_AND_ANTI_DISCRIMINATION.md`) — `ModelDriftService` disparado por feedback REJECTED

### Regulatório
- **LGPD Art. 9** — dados usados para fine-tuning devem ter finalidade declarada; `mask_pii()` é requisito mínimo de minimização
- **LGPD Art. 6 §I** — finalidade específica e legítima para coleta de feedback silencioso
