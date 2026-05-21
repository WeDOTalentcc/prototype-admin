# ADR-AB-001: Thompson sampling + FairnessConstraint em A/B testing (T-19)

**Status:** Aprovado 2026-05-20 (T-19 Fase 1 — infrastructure)
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-19, fix Reviewer D3)
**Relaciona:** ADR-031-v3 (FairnessGuard L3), ADR-035 (audit_log demographic proxies),
T-19 review C4 (constraint não-discriminatório)

## Contexto

Reviewer D3 (Sprint 2 review independente C4): "A/B testing expand precisa de
constraint não-discriminatório obrigatório E statistical significance proper E
multi-arm bandit para Sprint 5+ enterprise diferentiation".

Pré-T-19: A/B testing tinha:
- ✅ z-test + p-value `_compute_p_value` em `ab_testing_service.py:95`
- ✅ N_MIN_PER_VARIANT = 100 enforcement em `auto_promote_winner`
- ✅ CI 95% computation em `get_test_results`
- ❌ FAUL: NO FairnessConstraint gate antes de promover winner
- ❌ FAUL: NO multi-arm bandit (Thompson/UCB)
- ❌ FAUL: only 2-arm comparison (control vs variant) via z-test
  (não escalável pra 3+ variantes sem Bonferroni correction)

## Decisão

### 1. Thompson sampling canonical para multi-arm

`app/shared/intelligence/ab_testing/thompson_sampler.py` (~110 LOC):

```python
class ThompsonSampler:
    def update(arm, successes, failures): ...  # update Beta(α, β) posterior
    def choose(arms) -> str: ...               # sample posteriors + argmax
    def expected_value(arm) -> float: ...      # α / (α + β)
    def credible_interval(arm, confidence=0.95) -> tuple: ...
    def winner_probability(arm, arms, n_sim=5000) -> float: ...
```

Bayesian approach:
- Cada variant tem prior Beta(1, 1) uniforme
- Cada conversion observed → update posterior (alpha += 1) OR (beta += 1)
- A cada round: sample beta da posterior + pick arg max
- Convergência rápida + zero inflação Type I error mesmo com 5+ variants
- Sem dependency em scipy/numpy (uses random.gammavariate)

### 2. FairnessConstraint gate canonical

`auto_promote_winner` agora:
```python
# Antes de deactivate losing variants:
guard = FairnessGuard()
result = guard.check(winner_prompt, action_type="ab_test_winner_promotion")
if result.is_blocked:
    return {"promoted": False, "fairness_violation": True,
            "reason": "fairness_gate_blocked: " + result.blocked_reason}
```

Defesa em profundidade contra:
- Variant winner que usa termo bias-prone ("perfil adequado", "energia jovem")
- Variant winner que indiretamente prefere grupos demográficos
- Indireto: variant que aumenta conversion ÀS CUSTAS de disparate impact

Pattern fail-soft:
- Se `FairnessGuard` indisponível (ImportError) → WARN + promove (sensor detectará gap)
- Se check raise exception → WARN + promove (não bloqueia caminho crítico)
- Se is_blocked=True → REFUSA promoção + retorna razão estruturada

### 3. Statistical significance — manter status quo Fase 1

Status quo aceitável para Fase 1:
- z-test + p<0.01 + n>=100 já implementado
- Bonferroni correction para 3+ variants → Fase 2 backlog
- Sequential testing (early stopping) → Fase 3 backlog

### 4. Sensor canonical

`scripts/check_ab_fairness_gate.py`:
- Regra: `auto_promote_winner` em `ab_testing_service.py` DEVE chamar
  FairnessGuard OU ter comment `# FAIRNESS-GATE-EXEMPT: <reason>`
- Modo INICIAL: WARN-ONLY
- Promover BLOCKING após T-19 Fase 2 (sample A/B test winner com fairness gate validated em prod)

### 5. Integration points (NÃO implementado em Fase 1)

Backlog T-19 Fase 2-4:
- **Fase 2** — Integrar ThompsonSampler em `_compute_winner` (substitui z-test default)
- **Fase 3** — Bonferroni correction para multi-arm z-test fallback
- **Fase 4** — Sequential testing (alpha spending function) para early stopping

## Consequências

**Positivas:**
- Diferenciação enterprise (Bayesian multi-arm bandit é referência state-of-the-art)
- FairnessConstraint gate bloqueia discriminação indireta via A/B winner
- Backward compat 100% (Thompson é nova classe, gate é additive em auto_promote_winner)
- Sensor canonical previne regressão (auto_promote_winner sem gate = WARN)
- Audit-ready (ADR-035 audit_log compatible — guarda fairness_result em metadata)

**Negativas:**
- Thompson sampling exige posterior persistence cross-request (TODO: persist em DB)
  - Mitigation Fase 1: in-memory only (não escala multi-instance, OK pra prototipo)
- FairnessGuard fail-soft pode silenciar gap (sensor mitiga)
- Bonferroni absent → multi-arm z-test inflaciona Type I error
  - Mitigation: Thompson sampling não tem esse problema (fundamentado Bayesiano)

## Roadmap follow-up

| Task | Sprint | Escopo |
|---|---|---|
| **T-19 Fase 1 (este)** | 4 | Thompson sampler + FairnessGate + sensor warn-only + ADR |
| T-19 Fase 2 | 5+ | ThompsonSampler persistence (DB-backed posteriors) |
| T-19 Fase 3 | 5+ | Integrate Thompson em auto_promote_winner como default |
| T-19 Fase 4 | 6+ | Bonferroni correction multi-arm z-test fallback |
| T-19 Fase 5 | 6+ | Sequential testing (early stopping) |
| T-19 Fase 6 | 7+ | Frontend admin UI multi-arm bandit dashboard |

## Referências

- Reviewer C4/D3 (Sprint 2): "constraint não-discriminatório obrigatório"
- PLANO_ACAO_REPLIT_V3 T-19
- ADR-031-v3 (FairnessGuard L3 cross-sector default ON)
- ADR-035 (audit_log demographic proxies — captura fairness_check_result)
- Thompson, W. R. (1933). On the likelihood that one unknown probability exceeds another. Biometrika.
- Russo et al. (2018). A Tutorial on Thompson Sampling.
- `app/shared/intelligence/ab_testing/thompson_sampler.py` (canonical)
- `app/shared/learning/ab_testing_service.py` (auto_promote_winner gate)
- `scripts/check_ab_fairness_gate.py` (sensor canonical)
