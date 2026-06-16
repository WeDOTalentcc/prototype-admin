# Plano canônico — Reconciliação dos catálogos de tools (Opção 2)

**Alvo (Paulo 2026-06-05):** convergir execução no **Sistema B** (LangGraph ReAct + domain registries / DDD) + **UM catálogo de metadata canônico** (scope/permission/group/chat_exposed) como fonte única; deletar Sistema C; os 2 chats (page+bolha) consomem B + catálogo, selecionando por scope.
**Auditoria fonte:** `~/Documents/wedotalent_audit_2026-06-05/RRP_tool_catalog_reconciliation_AUDITORIA.md`
**Disciplina por fase:** canonical-fix (produtor único) → feature-impact → lia-testing (Red→Green) → lia-compliance → feature-audit → harness (guide+sensor). Commit atômico no Replit, **sem push**. Cada fase tem gate de verificação antes da próxima.

## Princípio-âncora
A **fonte única da verdade** é o catálogo de metadata, **derivado** dos domain registries (B) — nunca hand-maintained em paralelo (anti-drift). Scope vem do PromptScope (migrado do YAML-A). Execução continua LangGraph ReAct (B). Nada de mover handlers entre domínios (DDD preservado).

## Sequência por risco (fundação → valor → consolidação → migração profunda)

### Fase 1 — Catálogo canônico (fundação, ADITIVO, zero risco)
- **S1.1** `ToolMeta` schema (Pydantic, `extra=forbid`): `name, domain, scope (PromptScope), permission (read/write/admin), chat_exposed, source_registry, version`.
- **S1.2** `tool_catalog.py` (produtor único): **deriva** ToolMeta de TODOS os domain registries (B) via os `get_*_tools()`. Scope: seed do YAML-A (76) onde existir; default por heurística de nome (get_/list_/view_ = read+GLOBAL) com flag `scope_inferred=True` (proveniência honesta, sem fabricar).
- **S1.3 SENSOR** (lia-testing): `test_tool_catalog_sync` — todo tool dos domain registries tem entrada no catálogo; zero órfão; nomes únicos OU colisão explicitamente registrada. Blocking.
- **Gate:** catálogo lista 100% dos tools de B, sync verde. Nada consumido ainda.

### Fase 2 — Federado consome o catálogo + tool-set dinâmico (VALOR, médio risco, isolado ao copilot)
- **S2.1** `recruiter_copilot` deixa de hardcodar `_FEDERATION_SPEC`; passa a **selecionar do catálogo por scope** (PromptScope derivado de `view_context`+intent leve) → ~10-15 tools ativas/turno. Fallback determinístico: scope GLOBAL núcleo (vagas+candidatos+pipeline) quando sem contexto.
- **S2.2** mecanismo de toolset por-turno: confirmar se `LangGraphReActBase._get_tools` pode receber scope por chamada; se não, pré-seletor computacional antes do loop (spike documentado).
- **S2.3 SENSOR:** `test_copilot_dynamic_scope` — set por turno ≤ teto; sempre inclui core seguro; multi-tenancy preservada (company_id fail-closed herdado).
- **Gate (LIVE):** Paulo valida na bolha — rank/compare/funil/perfil + cobertura. Eficiência sentida.

### Fase 3 — Polish near-term (baixo risco)
- **S3.1** prompt enxuto do federado (cortar few-shot "Lucas/Desenvolvedor" — custo + alucinação). Sensor: no-PII-examples + budget de tokens.
- **S3.2** `list_jobs` → emitir `comparison_table` (RRP; mata "tabela design antigo"). Sensor render + contract.

### Fase 4 — Consolidar fonte única (S2 strategic)
- **S4.1** o catálogo derivado vira a fonte; o `tool_registry_metadata.yaml` (A) deixa de ser mantido à mão — ou é **gerado** do catálogo (codegen) com `git diff --exit-code`, ou deprecado.
- **S4.2 SENSOR anti-drift blocking:** catálogo ↔ YAML-A ↔ domain registries em sync (1 fonte).

### Fase 5 — Higiene de domínio (S4 strategic)
- **S5.1** resolver colisões de nome (`get_pipeline_summary` ×2, `generate_report` ×N) — namespacing ou dedup canônico.
- **S5.2** fronteira dos 2 "pipeline" (cv_screening vs pipeline domain) — feature-impact + decisão de boundary.

### Fase 6 — Deletar dead code (baixo risco)
- **S6.1** remover Sistema C (`global_tool_registry.py`) — zero consumidores (provado). tsc/pytest como rede.

### Fase 7 — Migração profunda A→B (RISCO ALTO — por último, com gates + coordenação)
- **S7.1** chat-page/supervisor (MainOrchestrator/agentic_loop, Sistema A) passa a consumir o catálogo único — OU executa via B. Decisão de faseamento + coordenação com sessão paralela (supervisor é trabalho ativo deles).
- **S7.2** aposentar o que de A virar redundante (executor/registry) sem quebrar consumidores.
- **Gate:** paridade chat-page validada live; rollback documentado (flag/revert).

## Riscos & mitigação
- **Sessão paralela mexe no supervisor (Sistema A):** Fase 7 coordena (REGRA 6 hot files); Fases 1-6 não tocam o supervisor.
- **Drift do catálogo:** sensor blocking desde a Fase 1.
- **Eficiência (Paulo):** Fase 2 entrega; teto de tools/turno medido.
- **Big-bang:** proibido — cada fase commit atômico + gate. Near-term (1-3) destrava; strategic (4-7) é incremental.

## Estado
- ✅ N4 WorkingDots (`cde627485`). Flag bolha→supervisor OFF (Paulo).
- ▶️ PRÓXIMO: Fase 1 (catálogo canônico) — TDD Red primeiro.
