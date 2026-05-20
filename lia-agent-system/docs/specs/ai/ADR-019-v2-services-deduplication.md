# ADR-019-v2: Services Deduplication + Canonical Locations (T-08)

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-08)
**Suplementa:** ADR-019 (Orchestrator Consolidation)
**Relaciona:** ADR-LGPD-001, T-10 (Feedback wire), T-11 (RLHF)

## Contexto

V4 audit identificou drift ADR-019 com duplicações de feedback+learning services.
Auditoria SSH 2026-05-20 (T-08 Fase A) revelou estado real mais nuançado:

**Para os 4 services listados em V3 plan:**
- Shims em `app/shared/services/{feedback,feedback_learning,learning_loop,training_data}_service.py`
- Eram apenas 2-line re-exports `from <canonical> import *`
- Limpeza inicial JÁ foi feita em commits anteriores

**Para o codebase inteiro (descoberta nova T-08):**
- Sensor `check_no_duplicate_services.py` identificou **85 service basenames** duplicados em 2+ paths
- Pattern recorrente: `app/services/X.py` (legacy global) + `app/shared/services/X.py` (intermediate) + `app/domains/<D>/services/X.py` (canonical novo)
- Maioria são shims em transição — não duplicação lógica real

## Decisão

### T-08 escopo (sprint 2 — fechado):

1. **3 migrations canonical:**
   - `outcome_tracker.py`: `app.shared.services.feedback_learning_service` → `app.domains.analytics.services.feedback_learning_service`
   - `wizard_step_service.py`: idem
   - `intelligent_data_orchestrator.py`: `app.shared.services.learning_loop_service` → `app.shared.learning.learning_loop_service`

2. **4 shim files DELETADOS:**
   - `app/shared/services/feedback_service.py`
   - `app/shared/services/feedback_learning_service.py`
   - `app/shared/services/learning_loop_service.py`
   - `app/shared/services/training_data_service.py`

3. **1 rename para eliminar class collision:**
   - `app/shared/learning/learning_loop.py` → `app/shared/learning/correction_capture.py`
   - `class LearningLoopService` (UC-P3-05 stub) → `class CorrectionCaptureService`
   - Test reference atualizada

### Canonical paths finais (decisão correção V3):

- **Feedback / training data → `app/domains/analytics/services/`**
  (V3 sugeriu `app/shared/learning/` mas analytics domain é mais correto — LGPD aggregates, dept profiles, recruiter outcomes pertencem a analytics)
- **Learning loops / A/B testing → `app/shared/learning/`**
  (cross-domain primitives)
- **NÃO consolidar tudo em `app/shared/learning/`** como V3 sugeria

### Sensor canonical novo (T-08):

`scripts/check_no_duplicate_services.py` com 3 regras:

| Regra | Descrição | Modo |
|---|---|---|
| **R1** | Shim re-exports em `app/shared/services/*_service.py` para os 4 cleaned files | BLOCKING |
| **R2** | Basename `_service.py` duplicado em 2+ paths | **WARN-ONLY** (baseline 85) |
| **R3** | Class collision em `app/shared/learning/*.py` | BLOCKING |

R2 baseline 85 é técnica débito documentada — viraT-08b sprint futuro
(consolidação massiva services duplicados). Promover para `--strict` quando
contagem chegar a ≤5 com whitelist explícita.

## Consequências

**Positivas:**
- 4 shim files removidos (-8 lines)
- Canonical paths claros (analytics vs shared/learning)
- Sensor warn-only previne novas duplicações sem bloquear pipeline existente
- ADR documenta baseline 85 → T-08b roadmap futuro

**Negativas:**
- T-08b sprint dedicado necessário para consolidar 85 duplicações restantes
- Risco: durante T-08b, callers diferentes podem importar versões diferentes

**Mitigações:**
- Sensor R2 warn-only mostra contagem em cada PR — pressure incremental
- Whitelist explícita pode adicionar `WHITELIST_DUPLICATE_BASENAMES` para domain-scoped legítimos

## Verification

```bash
# Sensor R1+R3 BLOCKING (zero deveria existir)
python scripts/check_no_duplicate_services.py --strict 2>&1 | grep "^[A-Z]" 
# Esperado: OK ou só R2

# Imports work
python -c "
from app.domains.job_management.services.outcome_tracker import *
from app.domains.job_management.services.wizard_step_service import *
from app.domains.analytics.services.intelligent_data_orchestrator import *
from app.shared.learning.correction_capture import CorrectionCaptureService
"
# Esperado: All imports OK
```

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-08 (este)** | 2 | 4 shim cleanup + sensor warn-only + canonical paths decidido |
| **T-08b** | Future | Consolidação massiva 85 services duplicados (basename canonical único) |
| **T-08c** | Future | Promover sensor R2 para `--strict` BLOCKING |

## Referências

- ADR-019 Orchestrator Consolidation (canonical original)
- PLANO_ACAO_REPLIT_V3 T-08
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md Fase A (descobriu state real)
- Sensor: `scripts/check_no_duplicate_services.py`
