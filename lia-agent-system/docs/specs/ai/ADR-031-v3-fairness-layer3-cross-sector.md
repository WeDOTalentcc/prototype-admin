# ADR-031-v3: FairnessGuard L3 Default ON Cross-Sector

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (decisão D1 em PLANO_ACAO_REPLIT_V3)
**Substitui:** parcialmente ADR-031-v2 (config setorial inicial)
**Relaciona:** ADR-031 (protected attributes YAML governance), ADR-031-v2 (loader fix)

## Contexto

`FairnessGuard.check_with_sector()` em `app/shared/compliance/fairness_guard.py`
implementa Layer 3 (LLM semantic check via Haiku) sector-aware. Estado anterior
(ADR-031-v2):

- Global default `FAIRNESS_LAYER3_ENABLED = True` (P1-3 defense-in-depth)
- Sector default em `check_with_sector()`: `False` (line 915)
- Sector explicito ON: tech, financeiro, saude, rpo
- Sector explicito OFF: varejo, logistica (justificativa: custo x beneficio)
- Sector desconhecido (construcao, agricultura, governo, ONG): caia em default OFF

## Problema

3 gaps operacionais identificados via auditoria SSH 2026-05-20:

1. **Setor desconhecido cai em OFF silenciosamente** — qualquer setor novo
   (e.g. cliente em construcao civil) entra com L3 desligado sem audit trail
2. **Varejo + logistica OFF cria inconsistencia compliance** — LGPD Art. 6/11
   nao distingue setor; EU AI Act Annex III item 4 (recrutamento high-risk)
   nao tem clausula sectoral
3. **Premissa custo x beneficio nao validada empiricamente** — assumia-se que
   varejo/logistica tinham menos vies fino, mas vies de aparencia (varejo) e
   de genero em operacionais (logistica) sao reais

## Decisao

L3 LLM semantic check default **ON** para TODOS setores:

1. `fairness_guard.py:915`: `sector_config.get("fairness_layer3_enabled", True)`
   (era `False`)
2. `policy_engine_service.py` ALPHA1_SECTOR_RULES:
   - `varejo`: `fairness_layer3_enabled: True` (era `False`)
   - `logistica`: `fairness_layer3_enabled: True` (era `False`)
   - tech, financeiro, saude, rpo: mantem `True` (sem mudanca)

Exceptions futuras permitidas APENAS com:
- Comment explicito `# ADR-EXEMPT: <reason canonical>` no codigo
- Nova ADR documentando trade-off

## Consequencias

**Positivas:**
- Compliance LGPD + EU AI Act consistente cross-sector
- Setor desconhecido tem cobertura L3 automatica
- Auditabilidade explicita (ADR-EXEMPT pattern canonical)
- Detecção de vieses implicitos em varejo (aparencia) e logistica (genero operacional)

**Negativas:**
- Custo Haiku adicional: ~$0.01-0.05 por candidato top-10 em RAG sector check
- Estimado ~$30-150/mes em producao moderada (1000 queries/dia)
- Latencia: 5-10s adicional em RAG sector check (L3 sequencial por candidato)

**Mitigacao latencia (followup):**
- T-19 (A/B testing expand) pode incluir batch L3 calls em paralelo
- Considerar threshold de candidatos (e.g. so top 5 em vez de top 10)
- Cache de L3 results por (query_hash, sector) hash

## Compliance frameworks

| Framework | Justificativa |
|---|---|
| LGPD Art. 6 | Principio de finalidade (decisao automatizada precisa ser justificavel) |
| LGPD Art. 11 | Dados sensiveis (raca, idade, deficiencia) protegidos via L3 semantic |
| LGPD Art. 20 | Direito a explicacao em decisao automatizada (L3 log audit_trail) |
| EU AI Act Annex III item 4 | Recrutamento e high-risk system (exige fairness check) |
| NYC LL144 | Bias audit anual (L3 logs feedem audit framework T-20) |

## Sensores

- `scripts/check_fairness_layer3_default_on.py` — AST check rejeita
  `fairness_layer3_enabled: False` sem ADR-EXEMPT comment
- Modo inicial: WARN-ONLY
- Promover para BLOCKING em T-14 (Sprint 13) apos Sprint 1 estabilizar

## Testes

- `tests/unit/test_t01_fairness_l3_default_on.py`:
  - `test_unknown_sector_triggers_l3`
  - `test_varejo_triggers_l3`
  - `test_logistica_triggers_l3`

## Verification

```bash
# Validar mudancas inline
grep -A 1 '"fairness_layer3_enabled"' app/domains/policy/services/policy_engine_service.py

# Rodar sensor
python scripts/check_fairness_layer3_default_on.py

# Rodar testes
python -m pytest tests/unit/test_t01_fairness_l3_default_on.py -v
```

## Referencias

- PLANO_ACAO_REPLIT_V3_2026-05-20.md T-01
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md secao 6 (exemplo T-01)
- AUDITORIA_ARQUITETURA_V4_CORRECTED_2026-05-20.md L4 Input Guards
- ADR-031-v2: protected attributes loader fix
- CLAUDE.md REGRA "ADR-LGPD-001 - Aggregates derived from candidate data"
