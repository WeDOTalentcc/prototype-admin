# Sprint V — Delete V1 (LIA-D06 Final Cleanup)

> **Standalone document**. Pode ser executado lendo APENAS este arquivo +  
> [`MIGRATION_REGRESSION_BASELINE.md`](./MIGRATION_REGRESSION_BASELINE.md).
>
> Para visão geral da migração, ver
> [`ORCHESTRATOR_MIGRATION_MASTER_PLAN.md`](./ORCHESTRATOR_MIGRATION_MASTER_PLAN.md).

**Sprint**: V (último da migração)  
**Pré-requisito crítico**: Sprint III.E canary 100% estável por **7 dias consecutivos**  
**Status atual**: 🔮 PLANEJADO — execução depende de Sprint III.E  
**Risco**: 🟢 BAIXO (após Sprint III.E validar V2 em prod)  
**Duração estimada**: 1-2 dias úteis

---

## 1. Objetivo

Remover fisicamente o `app/orchestrator/orchestrator.py` (V1, atualmente 532 LoC,
marcado `LIA-D06: DEPRECATED`) e atualizar todos os callers para usar
`MainOrchestrator` (V2) diretamente.

---

## 2. Pré-requisitos (DEVE estar 100%)

### 2.1 — Sprint III.E executado e estável

- [ ] `LIA_V2_USE_PLAN_SERVICE=true` em **100%** dos pods por **7 dias**
- [ ] `LIA_V2_USE_FALLBACK_REACT=true` em **100%** dos pods por **7 dias**
- [ ] Zero CRITICAL alerts relacionados aos services V2 em 7 dias
- [ ] Zero rollbacks dos canary stages
- [ ] Latência p95 dentro dos limites de `MIGRATION_REGRESSION_BASELINE.md`
- [ ] Error rate dentro dos limites

### 2.2 — Decisão de produto sobre callers legados

5 callers diretos do V1 a migrar (mapeamento em
`docs/migrations/orchestrator-v1-references-2026-04-26.md`):

| Caller | Tipo de migração necessária | Decisão produto |
|--------|----------------------------|-----------------|
| `app/api/orchestrator_routes.py` (5 endpoints públicos) | **Decisão**: depreciar OU redirecionar internamente para V2 | ⏳ Paulo decidir |
| `app/api/v1/chat.py` `_invoke_orchestrator_legacy()` | Substituir por `MainOrchestrator.process()` direto | Sprint V |
| `app/api/v1/lia_assistant/insights.py` Phase 3 | Trocar `get_orchestrator()` por `get_main_orchestrator()` | Sprint V |
| `app/domains/communication/services/teams_orchestrator_bridge.py` (descoberto Sprint I) | Avaliar se Teams integration ainda usa | ⏳ Paulo decidir |
| `app/orchestrator/main_orchestrator.py` (V2 wrapping) | Remover wrapping, V2 não precisa mais de V1 | Sprint V |

**Decisões necessárias antes de iniciar Sprint V**:
- [ ] `/api/orchestrator/*` — manter retrocompatível ou depreciar publicamente?
- [ ] Teams bridge — ainda em uso? Pode migrar?

---

## 3. Plano de execução (1-2 dias)

### Fase 1 — Validação final (1h)

```bash
# Confirmar zero importers diretos do V1 fora dos 5 callers conhecidos
ssh ... 'cd /home/runner/workspace/lia-agent-system && \
  python3 tools/migration/ast_orchestrator_inventory.py | \
  grep -v "orchestrator_routes\|chat.py\|insights.py\|teams_orchestrator_bridge\|main_orchestrator"'
# Esperado: zero matches

# Confirmar canary 100% estável
ssh ... 'tail -100 /var/log/lia-agent/orchestrator.log | grep "Sprint III"'
# Esperado: zero CRITICAL

# Health check final
ssh ... 'tools/canary/canary_health_check.sh 100pct'
# Esperado: exit 0 (HEALTHY)
```

### Fase 2 — Migrar callers diretos (4h)

Para cada caller, criar PR isolado com testes:

**2.1 — `chat.py` `_invoke_orchestrator_legacy()`**
```python
# ANTES (chat.py:712):
ws_orch = await _invoke_orchestrator_legacy(...)

# DEPOIS:
v2 = get_main_orchestrator()
result = await v2.process(ctx, db)
```

**2.2 — `lia_assistant/insights.py` Phase 3**
```python
# ANTES (insights.py:382-400):
from app.api.orchestrator_routes import get_orchestrator
orchestrator = get_orchestrator()
result = await orchestrator.process_request(...)

# DEPOIS:
from app.api.orchestrator_routes import get_main_orchestrator
v2 = get_main_orchestrator()
result_response = await v2.process(ctx, db)
result = result_response.model_dump()
```

**2.3 — `orchestrator_routes.py`** (depende decisão produto)

Opção A — Manter retrocompatível (recomendado):
```python
# Endpoints públicos /api/orchestrator/* continuam funcionando
# Internamente: redirecionar para V2 (sem mudar API externa)
@router.post("/process")
async def process(req: ProcessRequest, v2: MainOrchestrator = Depends(get_main_orchestrator)):
    ctx = UniversalContext.from_legacy_request(req)
    response = await v2.process(ctx, db)
    return ProcessResponse.from_v2_response(response)  # adapter
```

Opção B — Depreciar:
```python
# Adicionar header Deprecation + Sunset
# Após 30 dias com warning, remover
```

**2.4 — `teams_orchestrator_bridge.py`** (depende decisão produto)

Investigar se Teams integration ainda está ativa. Se sim, migrar pattern.
Se não, deletar arquivo.

**2.5 — `main_orchestrator.py`** (V2 standalone)
```python
# ANTES:
def __init__(self, orchestrator: Any, ...):
    self._orchestrator = orchestrator  # V1 reference

# DEPOIS:
def __init__(self, plan_service, fallback_react_service, ...):
    # Sem V1 reference. Self._orchestrator removido.
    # _route_with_tenant_llm usa apenas services.
```

Reescrever `_route_with_tenant_llm` para não delegar a V1:
```python
async def _route_with_tenant_llm(self, ctx, conv_id, db, orchestrator_context):
    # Plan path
    plan_result = await self._try_plan_via_service(ctx, conv_id, orchestrator_context)
    if plan_result is not None:
        return plan_result

    # Domain routing path (substituir V1.process_request)
    domain_response = await self._cascaded_router.route(ctx.message, orchestrator_context)
    if domain_response.handled:
        return self._convert_domain_response(domain_response)

    # Fallback ReAct path
    return await self._fallback_react_service.handle_directly(
        intent="general_chat",
        message=ctx.message,
        entities={},
        context=orchestrator_context,
    )
```

### Fase 3 — Deletar V1 (30 min)

```bash
# Backup primeiro (paranoia)
cp app/orchestrator/orchestrator.py /tmp/orchestrator_v1_BACKUP_$(date +%Y%m%d).py

# Confirmar zero referências
grep -rn "from app.orchestrator.orchestrator\|class Orchestrator\b" app/ \
  --include="*.py" | grep -v "main_orchestrator\|__pycache__"
# Deve retornar APENAS app/orchestrator/__init__.py (re-export)

# Deletar
rm app/orchestrator/orchestrator.py

# Atualizar __init__.py
cat > app/orchestrator/__init__.py <<'EOF'
"""Orchestrator package — V2 canonical (post Sprint V)."""
from .main_orchestrator import MainOrchestrator

__all__ = ["MainOrchestrator"]
EOF

# Atualizar registry.py se ainda existe
# (V1 usava registry para singleton — V2 usa get_main_orchestrator factory)
```

### Fase 4 — Cleanup tests (1h)

Tests de characterization que testavam V1 inline:
- `tests/characterization/test_v1_smoke.py` — converter para test V2 ou deletar
- `tests/characterization/test_v1_internal_methods.py` — métodos internos não existem mais
- `tests/characterization/test_v1_admin_methods.py` — manter para regression contract
- `tests/characterization/test_v1_process_request.py` — converter para V2 process()

Arquivar (não deletar) characterization tests em
`tests/characterization/_archive/` para auditoria histórica.

### Fase 5 — Validação final (1h)

```bash
# Full regression
pytest tests/ -v
# Esperado: 100% passing

# Coverage
pytest --cov=app/orchestrator
# Esperado: >= 80% (sem V1 inflando)

# Smoke E2E
pytest tests/integration/test_orchestrator_consolidation.py
# Esperado: passing
```

### Fase 6 — Deploy + monitoring (24h)

```bash
# Deploy gradual (mesmo padrão de canary)
# 5% → 25% → 50% → 100% ao longo de 24h

# Monitorar:
# - Latência (mesmas thresholds de Sprint III.E)
# - Error rate
# - Audit log integrity
```

---

## 4. Critérios de Sucesso (DoD)

- [ ] `app/orchestrator/orchestrator.py` deletado
- [ ] `grep "from app.orchestrator.orchestrator"` retorna 0 matches em produção
- [ ] `grep "class Orchestrator\b"` retorna 0 matches (exceto comentários históricos)
- [ ] CI 100% verde
- [ ] Latência p95 dentro dos limites por 24h pós-deploy
- [ ] Error rate dentro dos limites por 24h
- [ ] ADR-019 promovido a status **Accepted** com data + commit hash
- [ ] Tag de release `v2.X.X-orchestrator-consolidation-complete`
- [ ] BASELINE.md atualizado com métricas finais V2
- [ ] Comparação ANTES (V1+V2 ~2200L) vs DEPOIS (V2 ~1700L) documentada
- [ ] CANONICAL_FILES_BY_THEME.md atualizado removendo V1 entries

---

## 5. Plano de rollback

Se algo der errado em qualquer fase:

```bash
# Restore backup
cp /tmp/orchestrator_v1_BACKUP_$(date +%Y%m%d).py app/orchestrator/orchestrator.py

# Reverter __init__.py
git checkout HEAD~1 app/orchestrator/__init__.py

# Reverter callers
git revert <commits>

# Re-deploy V1+V2 (estado anterior)
```

Tempo de rollback: ~5 min.

---

## 6. Pós-Sprint V (cleanup adicional)

Após V1 deletado, há cleanup de **dívidas técnicas** que ficaram no caminho:

### 6.1 — Documentation cleanup
- [ ] `AUDITORIA_CANONICA_2026_Q2.md` — remover entradas de V1
- [ ] `CANONICAL_FILES_BY_THEME.md` — atualizar índice
- [ ] `CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md` — fechar entrada LIA-D06

### 6.2 — ADR cleanup
- [ ] ADR-019 promote a "Accepted"
- [ ] Tag git `migration-complete-v2`

### 6.3 — Observability cleanup
- [ ] Remover spans `orchestrator.v1.*` de Honeycomb queries
- [ ] Remover dashboard widgets de V1 metrics

### 6.4 — Service registry cleanup
- [ ] `app/orchestrator/_observability.py` — remover V1Spans constants
- [ ] `tools/migration/ast_orchestrator_inventory.py` — pode ser deletado (não há mais V1)

---

## 7. Sign-off necessário

Sprint V só pode iniciar após sign-off explícito de:

- [ ] **Backend lead**: Pré-requisitos 2.x verificados, plano revisado
- [ ] **Paulo (founder/produto)**: Decisões 2.2 tomadas
- [ ] **DevOps**: Backup + monitoring + rollback validados em staging

---

## 8. Histórico de execução (preencher quando executar)

| Fase | Data início | Data fim | Status | Notas |
|------|-------------|----------|--------|-------|
| 1 — Validação | _TBD_ | — | — | — |
| 2 — Migração callers | _TBD_ | — | — | — |
| 3 — Delete V1 | _TBD_ | — | — | — |
| 4 — Cleanup tests | _TBD_ | — | — | — |
| 5 — Validação final | _TBD_ | — | — | — |
| 6 — Deploy + monitor | _TBD_ | — | — | — |

---

**Status atual deste documento**: 📋 PLANO  
**Última atualização**: 2026-04-26  
**Próxima ação**: Aguardar Sprint III.E completar 7 dias estável a 100%
