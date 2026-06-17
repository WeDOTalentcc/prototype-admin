# FASE 4 — KICKOFF (handoff para nova sessao)

> Objetivo: persistir TODOS os perfis Pearch pesquisados (modelo "pesquisou = do recrutador"),
> habilitar resgate congelado (sem re-rodar, sem credito) + supressao de credito, com guardrails LGPD.
> Decisao tomada por Paulo 2026-05-29. Este doc + .planning/funil-byok-plan.md sao a fonte da verdade.

## REGRAS (inquebraveis)
- Replit e a fonte da verdade. Editar SO via SSH `replit-wedo-0405` em /home/runner/workspace/.
- GitHub canonical = read-only. NUNCA git push. Commits no Replit so quando Paulo pede.
- Branch ativa: `feat/benefits-prv-canonical` (confirmar com `git branch --show-current`).
- PII de candidato => lia-compliance OBRIGATORIO. multi-tenancy: company_id do JWT, RLS fail-closed.
- Cada item: cascata canonical (canonical-fix -> feature-impact -> lia-testing Red/Green -> feature-audit).
- Migrations: REGRA 5 (rodar `alembic heads` antes de criar; numerar do proximo livre). Paulo roda `alembic upgrade head`.
- Comunicacao so com Paulo.

## ESTADO ATUAL (ja entregue nesta saga, commitado)
- Commits na branch: b91e19422 (Onda A + Fases 1-3), 69b72997e (fix re-hidratacao caminho principal), 8b47c36bb (Fase 3b).
- Migrations APLICADAS no DB: 222 (company_id+RLS em search_feedbacks), 225 (search_fingerprint em search_feedbacks). DB em 225.
- Onda A: RLS/company_id em search_feedbacks. Fase 1: re-ranker errado removido. Fase 2: fingerprint dos criterios + persistir + re-hidratar feedback (ambos caminhos de busca). Fase 3: filtros entram na referencia (re-score local + botao "refazer com filtros").
- Sensores verdes: test_search_fingerprint(8), test_rls_search_feedbacks(4), filter-match-rescore(6), table-filters-to-search-spec(7). tsc + i18n limpos.

## O QUE CONSTRUIR (spec completo em .planning/funil-byok-plan.md secao "FASE 4 — SPEC EXECUTAVEL")
1. Migration: coluna `search_fingerprint` (String, index) em `external_candidate_profiles` (RLS ja existe nessa tabela).
2. Persist-on-search: apos resultados Pearch, upsert por (company_id, source_profile_id) reusando o builder de ExternalCandidateProfile (import_export.py:219). Tag search_fingerprint. Idempotente. BEST-EFFORT (nao bloquear resposta da busca — hot path de alta concorrencia).
3. Supressao (B): antes da busca Pearch, query source_profile_id da empresa -> exclude_candidate_ids -> docid_blacklist (infra ja wirada em pearch_service.py:1263 + :335). Economiza credito.
4. Resgate congelado (A): endpoint GET resultados por search_fingerprint (carrega de external_candidate_profiles, SEM chamar Pearch). Frontend: reabrir historico/lista carrega snapshot (NAO re-roda — hoje history-tab.tsx onReExecuteSearch RE-RODA, gasta credito; corrigir). Re-hidrata feedback por docid (snapshot preserva docid -> casa direto, sem ponte de identidade).
5. LGPD (mandatorio): base legal (interesse legitimo, docstring/ADR) + retencao/TTL (purgar nao-engajados apos N meses) + erasure cascade (incluir external_candidate_profiles no fluxo data_subject; Art.18). RLS ja ativo.
6. Sensores: upsert idempotente; supressao exclui docids; resgate sem chamar Pearch (mock); RLS cross-tenant; erasure remove perfis.

## ENTRY POINTS (arquivos-chave)
- lia-agent-system/app/domains/sourcing/services/pearch_service.py (busca Pearch; docid_blacklist :335,:1263; le external_candidate_profiles :1024-1048).
- lia-agent-system/app/api/v1/candidate_search/import_export.py:219 (builder ExternalCandidateProfile — REUSAR).
- lia-agent-system/libs/models/lia_models/candidate.py (~560: ExternalCandidateProfile; 350: CandidateSearch analytics).
- lia-agent-system/app/api/v1/candidate_search/search.py (handler; computa search_fingerprint via _generate_search_fingerprint em _shared.py).
- lia-agent-system/app/api/v1/search_feedback.py (GET /by-search re-hidratacao ja existe).
- plataforma-lia/src/components/talent-funnel-tabs/history-tab.tsx (onReExecuteSearch — mudar p/ carregar snapshot).
- lia-agent-system/app/domains/data_subject/ (erasure cascade — adicionar external_candidate_profiles).

## CONTEXTO PEARCH (confirmado)
- Cobra por profile retornado/busca; re-rodar re-cobra; sem endpoint get-by-id gratis. docid (source_profile_id) e id estavel.
- Paulo confirmou com Pearch: candidatos pesquisados/persistidos sao do recrutador (pode armazenar+re-exibir). Supressao via docid_blacklist evita re-cobranca.

## RISCO PRINCIPAL
Persist-on-search toca o hot path de busca. Best-effort + idempotente + nao bloquear. Testar concorrencia. LGPD (retencao/erasure) e parte do escopo, nao opcional.
