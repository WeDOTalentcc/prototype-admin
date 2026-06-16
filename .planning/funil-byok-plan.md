# Plano de Implementação — Funil de Talentos + BYOK/LLM Factory

**Branch Replit:** `feat/benefits-prv-canonical`
**Data:** 2026-05-29
**Codebases:** `lia-agent-system/` (IA, porta 8001) + `plataforma-lia/` (front, porta 3000)
**Disciplina por item:** cascata canonical Replit (`canonical-fix` → `feature-impact` → `lia-testing` → `feature-audit`) antes de cada edit. Harness-engineering (guide×sensor) para cada sensor novo.

## Decisões confirmadas (Paulo, 2026-05-29)
1. **routing.voice** → REMOVER da UI (voice é sempre Gemini por razão técnica de Speech-to-Text). Não tentar "fazer funcionar".
2. **P0-01 feedback→ranking** → ajuste **POR VAGA** (feedback daquela vaga ajusta ranking daquela busca), não aprendizado cross-vaga global.
3. **Ordem das ondas** → livre (Claude decide).

## Bugs já corrigidos (sessão anterior, commits Replit)
- BUG-01 `use-talent-funnel.ts` — setState-during-render via Zustand em updaters. Fix com useRef. Commit `e60a1210e`.
- BUG-02 `useCandidatesPageCore.tsx` — tableFilters stale entre buscas. Fix limpando filtros. Commit `e48cf622a`.

---

## Modelos LLM padrão (libs/config/lia_config/config.py)
- `LLM_PRIMARY_MODEL = claude-sonnet-4-6` — chat LIA + maioria das gerações
- `LLM_FAST_MODEL = gemini-2.5-flash` — tier 1 do cascade router
- `LLM_POWERFUL_MODEL = claude-opus-4-6` — tier 3 do cascade
- `FALLBACK_ORDER = [claude, gemini, openai]` — Claude primeiro pq proxy Replit modelfarm quebrado p/ Gemini/OpenAI

---

## ONDA 0 — Surfacing (dados existem no backend, não renderizam) — frontend
Baixo risco, valor imediato.

| Item | Problema | Produtor canonical | Sensor |
|---|---|---|---|
| P0-02 | Circuit breaker Pearch OPEN sem aviso na UI | componente resultados de busca (plataforma-lia) | smoke render circuit_open=true |
| P1-02 | warning_message do backend não renderizado | mesmo componente | render test |
| P2-04 | expansion_message não renderizado | mesmo componente | render test |
| P2-01 | SearchFeedbackButtons não recarrega estado like/dislike no remount | SearchFeedbackButtons.tsx | test mount→fetch initial |

## ONDA 1 — Completude de dados — backend + frontend
| Item | Problema | Produtor canonical | Sensor |
|---|---|---|---|
| P0-03 | 7 campos faltando no CandidateSearchResultDTO: big_five, soft_skills, certifications, work_model, willing_to_relocate, seniority_level, updated_at | DTO de busca + mapper (lia-agent-system) | contract test DTO |
| P1-03 | handleLoadMore só incrementa contador, não busca API | use-talent-funnel / useCandidatesPageCore | test handleLoadMore dispara fetch |

## ONDA 2 — Inteligência de ranking (coração) — backend
Maior valor, maior cuidado (fairness — lia-compliance obrigatório).
| Item | Problema | Produtor canonical | Sensor |
|---|---|---|---|
| P0-01 | searchFeedbacks (like/dislike) persistido mas nunca lido p/ ajustar ranking. POR VAGA. | search.py consome SearchFeedback | test feedback histórico altera ordem |
| P1-01 | Padrões de calibração (CalibrationSession) não injetados no scoring | search.py + calibration.py | test padrões aplicados ao score |
| P1-04 | Rubric scoring absoluto, não comparativo | rubric_evaluation_service.py | test normalização relativa |
| P2-03 | Candidatos Pearch pulam rubric eval (sem job_id) | search.py _evaluate_candidates_with_rubrics | test Pearch+job_id→rubric roda |

## ONDA 3 — BYOK/LLM routing correto — backend + UI admin
Fecha "ghost setting" (config editável sem efeito — mesmo padrão lia_field_toggles).
| Item | Problema | Decisão | Produtor canonical |
|---|---|---|---|
| Gap 1a | routing.screening ignorado (rubric hardcodeia [claude,gemini]) | WIRE: usar get_provider_for_tenant(routing=screening) | rubric_evaluation_service.py |
| Gap 1b | routing.embedding ignorado | WIRE: embedding_factory lê config | embedding_factory.py |
| Gap 1c | routing.voice ignorado (voice sempre Gemini por STT) | REMOVER da UI | UI admin + llm_config.py |
| Gap 3 | routing.chat escolhe provider mas não modelo | WIRE: modelo por tenant | main_orchestrator.py + factory |
| P2-02 | should_expand_to_global threshold hardcoded (<25) | configurável por tenant | search.py |

Sensor canonical Gap 1: AST checker check_routing_config_consumed.py (detecta routing.X órfão), espelha check_agent_respects_lia_toggles.

## ONDA 4 — Hardening / infra — backend
| Item | Problema | Notas |
|---|---|---|
| P1-05 | Sem rate limiting nos endpoints de busca | middleware/dependency em candidate_search/search.py |
| Gap 2 | Proxy Replit modelfarm quebrado p/ Gemini/OpenAI fallback | INVESTIGAR primeiro — pode ser infra, não código |

---

## AUDITORIA PRÉ-IMPLEMENTAÇÃO (autoplan adaptado, single-voice)
_(preenchido após revisores CEO + Eng lerem código real no Replit)_

### Achados CEO/estratégia
_(pendente)_

### Achados Eng/arquitetura+testes
_(pendente)_

### Taste decisions (surfaced ao Paulo)
_(pendente)_

### User challenges (ambos modelos discordam da direção do Paulo)
_(pendente)_

---
## RESULTADO DA AUDITORIA (2026-05-29, autoplan adaptado single-voice + 2 revisores independentes lendo Replit)

### TEMA CROSS-PHASE 1 (ambos revisores) — DOIS sistemas de feedback concorrentes
- `SearchFeedback` (like/dislike, search_feedback.py) E `CalibrationFeedback`/`learned_criteria` (calibration.py) são AMBOS write-only e órfãos do scoring (grep vazio em search/_shared/sourcing).
- P0-01 e P1-01 operam sobre o MESMO vacancy_id+user_id+like/dislike → vão DOUBLE-COUNT / brigar (like vira boost direto em P0-01 E alimenta padrão LLM em P1-01).
- `learned_criteria` é ghost-setting write-only (mesmo anti-pattern lia_field_toggles do CLAUDE.md).
- RECOMENDAÇÃO: unificar P0-01+P1-01 num ÚNICO re-ranker (learned_criteria como features + feedback bruto como sinal), precedência explícita. NÃO dois multiplicadores independentes. Decidir fonte da verdade ANTES de codar.

### TEMA CROSS-PHASE 2 (ambos) — routing.screening/embedding: REMOVER, não WIRE
- routing.chat JÁ é consumido (main_orchestrator.py:805) → Gap 3 é "estender ao modelo", não criar.
- routing.screening/embedding genuinamente órfãos, MAS wire é over-engineering + foot-gun (cliente seta embedding=OpenAI sem key → busca quebra silenciosa).
- embedding_factory.py é env-based puro (sem tenant nem routing) → Gap 1b é refator MAIOR que o plano sugere.
- get_provider_for_tenant (llm_factory.py:538) não aceita routing → wire exige nova assinatura.
- RECOMENDAÇÃO: REMOVER routing.screening/embedding/voice da UI (igual decisão voice). Manter só primary_provider + keys. Gap 1a/1b viram "remover", Gap 3 vira "estender routing.chat ao modelo".

### CRÍTICOS (Eng) — prerequisitos antes da Onda 2
1. `SearchFeedbackRepository.list_for_company`/`get_stats` referenciam campos inexistentes no modelo (company_id, search_type, rating) → CRASH runtime. Código morto/divergente. Limpar ANTES de wirar P0-01.
2. `SearchFeedback` NÃO tem company_id → multi-tenancy 100% via RLS Postgres. Read no scoring em contexto async/batch sem RLS setado = vazamento cross-tenant. CRÍTICO LGPD.
3. ID mismatch: Pearch usa docid/linkedin slug, local usa UUID. Match de feedback por candidate_id falha silenciosamente (mesma raiz do P2-03). Falso "funciona".
4. Loop degenerado: 1 like → boost permanente sem decay/cap. Precisa boost relativo CAPADO + min_feedbacks (espelhar CalibrationSession.min_feedbacks_required=5).

### FAIRNESS/LGPD (Eng) — guardrails obrigatórios
- Rubric JÁ mascara PII (strip_pii_for_llm_prompt, rubric_evaluation_service.py:892). Bom.
- Feedback do recrutador codifica preferências = proxy de viés (universidade/empresa). Re-ranking por feedback toca decisão de candidato → FairnessGuard + audit_service.log_decision OBRIGATÓRIO em todo re-rank. Nunca alterar ranking por campo sensível. CRÍTICO.
- CandidateProfile carrega gender + estimated_age (pearch.py:152) → NÃO derivar nada deles, NÃO vazar pro DTO/LLM.
- Verificar strip_pii no candidate_snapshot da calibração antes de P1-01.

### P0-03 DTO — PARCIAL
- 7 campos confirmados faltando (_shared.py:215). MAS big_five/soft_skills/etc NÃO existem na origem Pearch (CandidateProfile, pearch.py:129) — só na tabela candidates local.
- Para Pearch: sempre None. Para local: estender enrich_and_filter_candidates (enrich_batch já em lote, evita N+1).
- Declarar P0-03 como parcial. Verificar se o frontend renderiza os 7 campos (senão é ghost reverso).

### REAPROVEITAR (CEO)
- analyze_calibration_patterns_for_session (candidate_goal_service.py:172) já deriva padrões — reusar, não reescrever.
- session.learned_criteria já populado (calibration.py:196) — só falta injetar.
- EmbeddingFactory.embed_with_fallback já tem chain.

### SENSORES (harness) — viáveis
- check_routing_config_consumed.py: VIÁVEL (molde AST check_agent_respects_lia_toggles.py existe). Detecta routing.X órfão.
- check consumer de learned_criteria: molde check_lia_field_toggle_consumers.py existe.
- RLS contract test cross-tenant feedback; anti-loop cap test; DTO contract test (7 campos, Pearch=None explícito).

### SEQUENCIAMENTO revisado (CEO) — proposta
0. (NOVA) Decisão consolidação feedback (SearchFeedback vs CalibrationFeedback) + limpar repo crash + company_id/RLS
1. Onda 2 (ranking unificado) com FairnessGuard
2. Onda 1 (DTO + paginação)
3. Onda 3 reduzida (remover routing órfão da UI + estender routing.chat ao modelo)
4. Onda 0 (surfacing — cosmético, por último)
5. Onda 4 (hardening; Gap 2 fica fora do código = infra)

---
## DECISÕES FINAIS (Paulo, 2026-05-29) — PLANO TRAVADO

1. **Re-ranker único** — P0-01 + P1-01 consolidados num só ponto de re-ranking. Decidir fonte da verdade (SearchFeedback vs CalibrationFeedback) antes de codar. learned_criteria = features; feedback bruto = sinal; precedência explícita.
2. **Remover routing órfão da UI** — screening/embedding/voice saem da UI admin. Mantém só primary_provider + keys. Gap 1a/1b = REMOVER (não wire). Gap 3 = estender routing.chat ao modelo.
3. **Sequenciamento delegado ao Claude** — ordem revisada aplicada.
4. **Obrigatórios embutidos (não opcionais):**
   - Limpar SearchFeedbackRepository (campos inexistentes → crash) antes da Onda 2.
   - Adicionar company_id + garantir RLS no SearchFeedback (anti-vazamento cross-tenant).
   - Resolver ID mismatch Pearch(docid) vs local(uuid) no match de feedback.
   - FairnessGuard + audit_service.log_decision em todo re-rank. Nunca rankear por campo sensível. Não vazar gender/estimated_age.
   - Boost relativo CAPADO + min_feedbacks (anti-loop degenerado).
   - P0-03 declarado parcial (Pearch=None nos campos sem origem).

## ROADMAP FINAL DE EXECUÇÃO (ordem revisada)
- **Onda A (prerequisitos Onda 2):** limpar repo crash + company_id/RLS no SearchFeedback + resolver ID mismatch. Cascata canonical por item.
- **Onda B (ranking unificado):** re-ranker único consumindo feedback + learned_criteria, com FairnessGuard + audit + boost capado. Sensores: anti-loop, RLS cross-tenant, consumer-de-learned_criteria. (= P0-01+P1-01+P1-04+P2-03)
- **Onda C (dados):** P0-03 DTO (parcial, enrich_batch) + P1-03 handleLoadMore fetch real. Sensor: contract test DTO.
- **Onda D (BYOK):** remover screening/embedding/voice da UI + llm_config.py; estender routing.chat ao modelo. Sensor: check_routing_config_consumed.py.
- **Onda E (surfacing — cosmético):** P0-02 circuit OPEN + P1-02 warning_message + P2-04 expansion_message + P2-01 reload feedback state.
- **Onda F (hardening):** P1-05 rate limit (verificar: revisor Eng diz que rate limiter por user/company JÁ existe — confirmar antes). Gap 2 (proxy modelfarm) = infra, fora do código.

Cada item: canonical-fix → feature-impact → lia-testing (Red→Green) → feature-audit. Harness para cada sensor.

---
## STATUS DE EXECUÇÃO — ONDA A (2026-05-29)

### A.1 — canonical-fix SearchFeedbackRepository ✅ FEITO
- Removidos 3 métodos dead code: list_for_company, get_stats (crashavam: campos company_id/search_type/rating inexistentes), get_by_id (UUID, unused). Imports órfãos UUID/func limpos.
- Confirmado zero callers antes de remover. Import smoke test OK.
- Arquivo: app/domains/recruitment/repositories/search_feedback_repository.py (único repo; não havia duplicata).

### A.2 — company_id + RLS no SearchFeedback ✅ CÓDIGO PRONTO (aguarda Paulo rodar migration)
- Migration: alembic/versions/222_add_company_id_rls_search_feedbacks.py (down_revision=221, head). Adiciona company_id varchar, deleta 9 órfãos pré-RLS, NOT NULL+index, ENABLE+FORCE RLS + 4 policies (espelha 118_rls_candidates), GRANT lia_app.
- Modelo: libs/models/lia_models/search_feedback.py — company_id NOT NULL + to_dict.
- Produtor: app/api/v1/search_feedback.py — submit_feedback grava company_id (do require_company_id, antes ignorado).
- Sensor: tests/integration/test_rls_search_feedbacks.py (RED até migration; GREEN depois). RLS enabled + cross-tenant SELECT/INSERT bloqueados + same-tenant OK.
- Plumbing confirmado: get_db (libs/config/lia_config/database.py:93) já faz SET ROLE lia_app + set_config('app.company_id') — RLS funciona automático nos endpoints.
- ⚠️ AÇÃO PAULO: `cd lia-agent-system && alembic upgrade head` antes de servir tráfego com o código novo (modelo NOT NULL assume coluna existente).

### A.3 — ID mismatch Pearch(docid) vs local(uuid) → RECLASSIFICADO para Onda B
- DTO id = profile.docid (Pearch) ou UUID (local). Consistente dentro da mesma representação; mismatch só na mesma-pessoa-em-duas-representações (edge).
- Não há crash/quebra atual. A lógica de matching feedback↔candidato vive no re-ranker (Onda B). Resolver lá, com fingerprint (_shared.py:78 _generate_fingerprint) como chave de identidade estável opcional + teste e2e.
- Sem edit isolado em Onda A.

### A.2 — APLICADA E VERIFICADA (2026-05-29)
- alembic_version=222, company_id presente, RLS habilitado, 4 policies, 9 orfaos deletados (rows=0).
- Sensor test_rls_search_feedbacks.py: 4 passed (GREEN). Gap LGPD de isolamento cross-tenant FECHADO.
- ONDA A 100% completa.

## STATUS ONDA B (2026-05-29)

### B-step1 — re-ranker por feedback (nucleo P0-01) FEITO
- search.py: _rerank_candidates_by_feedback (pura) + _apply_feedback_reranking (async I/O), call site apos rubric eval.
- Regra: dislike->fim, like->boost capado (+5/like, teto 15), agrega entre recrutadores (anti-loop). Por vaga.
- RLS isola feedback por company (list_for_job sob sessao tenant). audit_service.log_decision em todo re-rank. Attribute-blind.
- Sensor: tests/unit/test_search_rerank_feedback.py — 9 passed.
- Decisao Paulo: feedback agora, calibracao depois (precedencia: feedback per-candidato = verdade).

### Restante Onda B (proximo)
- B-step2: P1-01 injecao de learned_criteria da calibracao (prior secundario; casar padroes textuais x candidato).
- P1-04: rubric scoring comparativo (normalizacao relativa).
- P2-03: candidatos Pearch passam por rubric eval (precisam job_id + match de id).

## ACHADO PIVOTAL ONDA B (2026-05-29) — busca e GLOBAL, nao por-vaga

- Frontend NUNCA envia job_id na busca de candidatos (candidate-search.ts / useCandidatesExecuteSearch.ts mandam so query/limit/search_pearch). SearchFeedbackButtons tem prop jobId mas CandidatesTable nao passa -> feedback gravado com job_id=NULL.
- Consequencia: rubric eval (if request.job_id) NUNCA roda na busca principal; feedback e global (por recrutador), nao por-vaga.
- DECISAO Paulo: re-rank por recrutador, global. Re-ranker re-keyado job_id->user_id (list_for_user), user_id de http_request.state.user_id (mesma fonte do submit_feedback; current_user.id divergiria — em dev e "dev-user").

### Reclassificacao dos itens restantes:
- P2-03 (Pearch no rubric): NAO-APLICAVEL. _evaluate_candidates_with_rubrics ja avalia TODOS (inclui Pearch) quando roda; o gate real e job_id, que a busca global nao tem. Rubric e job-scoped por natureza.
- P1-04 (rubric comparativo): NAO-APLICAVEL na busca global (sem rubric scores) + mudanca de produto debativel (absoluto e mais estavel/justo). Nao e defeito.
- P1-01 (injecao calibracao): GHOST SETTING REAL, mas calibracao e job-scoped (vacancy_id). Pertence ao fluxo de sourcing/calibracao por-vaga, NAO a busca global. Wirar aqui nao faz sentido. Requer investigar AQUELE surface separadamente.

### Onda B resultado: o que se aplica a busca global = feedback re-ranker (P0-01). FEITO e correto.
- search.py: _apply_feedback_reranking(candidates, user_id, db, company_id) via list_for_user; call site usa http_request.state.user_id. 9 testes verdes.

## STATUS EXECUCAO PLANO (2026-05-29)

### Fase 1 — reverter re-ranker backend ✅
- search.py ja estava revertido (checkpoint Replit). Removido teste orfao test_search_rerank_feedback.py. search.py limpo (0 refs), sintaxe OK.

### Fase 2 — fingerprint + persistir + re-hidratar (BACKEND ✅ / FRONTEND pendente)
- _shared.py: _generate_search_fingerprint(query, search_spec) + SearchResponseDTO.search_fingerprint. Sensor tests/unit/test_search_fingerprint.py: 8 passed.
- search.py: computa _search_fp + retorna nos 2 returns (early timeout + principal).
- Modelo search_feedback.py: coluna search_fingerprint (nullable, index).
- Migration 225_add_search_fingerprint_to_search_feedbacks.py (down=224). NOTA: colisao evitada — outro workstream adicionou 223_agent_studio_perf_indexes + 224_fk_closure_agent_studio; DB ja em 224. Renumerei minha migration de 223->225 (REGRA 5).
- search_feedback.py API: SubmitFeedbackRequest.search_fingerprint; create grava company_id (perdido no revert da Onda A!) + search_fingerprint; novo GET /search/feedback/by-search?fingerprint= (re-hidratacao).
- repo: list_for_user_and_fingerprint.
- Import smoke OK.

### ACAO PAULO (destrava): rodar migration 225
  cd lia-agent-system && alembic upgrade head
  (adiciona search_fingerprint. SEM ela, submit_feedback quebra: API referencia a coluna.)

### Pendente Fase 2 (frontend re-hidratacao):
- candidate-search.ts: SearchResponse.search_fingerprint.
- SearchFeedbackButtons.tsx: enviar search_fingerprint no POST.
- useCandidatesSearch.ts: apos setCandidates, GET /by-search?fingerprint -> setSearchFeedbacks (re-hidrata o tier-sort existente). Fecha P2-01.
- rota proxy Next /api/backend-proxy/search/feedback/by-search.

### Fase 2 frontend — PARCIAL (contrato pronto, fiacao de estado pendente)
- candidate-search.ts: SearchResponse.search_fingerprint ✅
- rota proxy src/app/api/backend-proxy/search/feedback/by-search/route.ts (GET) ✅
- PENDENTE (unidade focada, disciplina de hooks):
  - useCandidatesUIState.ts: estado searchFingerprint (espelhar searchThreadId:96 + export:168)
  - useCandidatesSearch.ts: setSearchFingerprint da resposta (espelhar setSearchThreadId:328) + apos setCandidates, GET /by-search?fingerprint -> setSearchFeedbacks (re-hidrata)
  - threading searchFingerprint -> CandidatesTable + CandidateTableCellRenderer -> SearchFeedbackButtons (mirror do searchFeedbacks)
  - SearchFeedbackButtons.tsx: prop searchFingerprint + enviar no POST body
- Sensores frontend a adicionar: teste re-hidratacao (mount com fingerprint -> searchFeedbacks populado); smoke rerender do botao.

### Fase 2 frontend — COMPLETA (code-complete, tsc limpo)
- SearchFingerprintContext.tsx (provider + useSearchFingerprint).
- candidates-page.tsx: envolve com SearchFingerprintProvider value={searchFingerprint}.
- SearchFeedbackButtons.tsx: consome via useSearchFingerprint() + envia search_fingerprint no POST (write-path).
- useCandidatesSearch.ts: read-path (GET /by-search -> setSearchFeedbacks) + setSearchFingerprint da resposta.
- Fiacao de estado: UIState.searchFingerprint -> composition (setter) -> PageCore (destructure + deps + return).
- tsc --noEmit: 0 erros nos arquivos tocados.
- LOOP COMPLETO: busca -> fingerprint -> feedback ancorado (POST) -> re-hidrata ao voltar/resgatar (GET). Fecha P2-01.

### PENDENTE Fase 2:
- Sensor frontend (smoke re-hidratacao mock fetch) — lia-testing.
- E2E manual apos migration 225: like -> reload -> ranking persiste.

### Fases 3 (filtros na referencia) e 4 (viajar com lista/pool) — nao iniciadas.

### AUDITORIA UI/UX (Paulo pediu antes de criar botoes) + decisao
- Padrao de botao: pill custom (px-4 py-2 rounded-full + tokens lia-*), NAO shadcn Button. Fonte: SearchControlsBar.tsx.
- Controles existentes: selecionar todos, Filtros (toggle painel), colunas. NAO existe refazer/aplicar.
- CandidatesFilterPanel: rodape com onClearAll + onClose.
- DECISAO Paulo: botao refazer busca com filtros NO RODAPE do CandidatesFilterPanel (ao lado de Limpar tudo), reusando pill.
- i18n: namespace candidates controls.*, chaves em pt-BR + en.

### Fase 3 — design do re-score local (nuance)
- Filtros hoje sao HARD (removem nao-match). Re-score so diferencia por GRAU de match (ex: skills [python,aws] -> match 2 > match 1), capado, dentro do conjunto filtrado, feedback tier por cima.
- Local re-score: funcao pura em useCandidatesFilterSort + teste. Refazer server-side: tableFiltersToSearchSpec + extender pearch_service search_spec mapping + botao rodape.

### Fase 3a — re-score local por grau de match ✅ (code-complete, testado)
- useCandidatesFilterSort.ts: countActiveFilterMatches (pura, exportada) + integrada no searchDisplayCandidates (apos switch de sort, antes do tier de feedback; estavel). Deps do memo: +tableFilters, +advancedFilters.
- Conta condicoes satisfeitas (skills/locations/jobTitles/companies/seniority, table+advanced). Mais match = sobe. Feedback tier ainda domina.
- Sensor: src/components/pages/candidates/__tests__/filter-match-rescore.test.ts — 6/6 passed. tsc limpo.

### Fase 3b — refazer busca server-side: PENDENTE
- tableFiltersToSearchSpec(filters) no frontend.
- botao no rodape do CandidatesFilterPanel (pill) -> re-executa busca com search_spec.
- estender pearch_service.py search_spec->query mapping p/ campos novos.
- i18n controls.* (pt-BR+en).

### Fase 3b — PARCIAL
- tableFiltersToSearchSpec.ts (puro) ✅ + teste 7/7. Mapeia skills/location/job_title/seniority/companies/industries/languages/experiencia/salario/work_model/is_open_to_work -> search_spec (que to_pearch_custom_filters ja consome). Backend NAO precisa mudar p/ esses campos.
- PENDENTE (fiacao UI, chunk final):
  - executeSearch: param opcional searchSpecOverride + merge no bloco searchSpec (useCandidatesSearch.ts:301) + tipo no ctx (108).
  - PageCore: handleReSearchWithFilters = executeSearch(lastSearchQuery, lastSearchEntities, lastSearchMode, metadata, true, tableFiltersToSearchSpec(tableFilters, advancedFilters)). Expor.
  - threading onReSearch: PageCore -> candidates-page -> CandidateSearchResultsView -> CandidatesFilterPanel.
  - CandidatesFilterPanel: botao pill no rodape (ao lado de onClearAll) chamando onReSearch. i18n controls.reSearchWithFilters (pt-BR+en).

### Fase 3b — COMPLETA (code-complete, tsc + i18n limpos)
- executeSearch ganhou param opcional searchSpecOverride (merge sobre o spec das entities).
- PageCore: handleReSearchWithFilters (constroi tableFiltersToSearchSpec ANTES do executeSearch que reseta filtros) -> executeSearch(query, entities, mode, metadata, true, spec).
- Threading: PageCore -> candidates-page:169 -> CandidateSearchResultsView -> CandidatesFilterPanel (curto, 2 hops).
- Botao pill no rodape do painel (reusa tokens lia-btn-primary), so quando ha filtros ativos. i18n candidates.filters.reSearchWithFilters (pt-BR + en).
- FASE 3 COMPLETA. Falta so Fase 4 (viajar com lista/pool).

### Fase 4 — ACHADO: caso histórico JA COBERTO pela Fase 2
- Resgatar busca = re-executar (CandidatesSearchModals edit-query:263, LIA chat, archetypes todos chamam executeSearch com mesmos criterios). Histórico guarda query+entities+metadata.
- Re-executar -> mesmo fingerprint -> re-hidratacao (GET /by-search) roda -> feedback volta. JA FUNCIONA.
- Gap real restante: CandidateList/TalentPool CONGELADOS (nao re-executam). Ressalvas: (1) listas guardam so candidatos locais UUID; feedback Pearch(docid) nao casa; (2) lista = conjunto curado, nao busca.
- DECISAO pendente Paulo: implementar fingerprint em lista congelada (baixo valor + caveat ID) OU considerar Fase 4 coberta pela Fase 2.

### Fase 4 — DESCOBERTA ARQUITETURAL (candidate.py:350 CandidateSearch)
- candidate_searches NAO persiste resultados completos — so analytics (query, filtros, counts, creditos, clicked/contacted ids). Descartados vem de staging separado.
- Logo: resgatar = re-executar e a unica opcao hoje -> onReExecuteSearch (history-tab.tsx) RE-RODA a busca -> gasta credito. RISCO DO PAULO CONFIRMADO, arquitetural.
- Fase 4 do jeito certo (resgatar = snapshot congelado, sem re-rodar, sem credito) EXIGE capacidade NOVA: persistir o conjunto completo de resultados por busca (com ids originais preservados p/ casar feedback) + fluxo de load-sem-re-rodar + re-hidratacao.
- Isso e um PROJETO (maior que Fases 1-3). NAO iniciar no fim da sessao; alinhar escopo.
- CandidateList curada (handleAddToList importa Pearch->UUID novo) e caso separado, precisa ponte de identidade.
- Opcao interim p/ o risco de credito: history reopen re-rodar LOCAL-only (gratis) por padrao + confirmar antes de global/Pearch.

### Fase 4 — PESQUISA PEARCH (creditos + armazenamento)
- Credito: cobra por profile retornado/busca; contatos+analise = extra. Re-rodar re-cobra. Sem endpoint publico get-profile-by-id gratis (so /search pago).
- Tecnicamente viavel: recebemos profile completo + docid estavel -> guardar PearchSearchResult por busca -> resgate sem re-rodar (sem credito) -> feedback casa por docid. SEM ponte de identidade pro caso snapshot.
- BLOQUEIO (acao Paulo): TOS de retencao/armazenamento da Pearch NAO e publico. Precisa confirmar com Pearch (f@pearch.ai / contrato platform.pearch.ai): podemos persistir+re-exibir perfis? prazo? restricoes? Questao contratual+LGPD, gating da arquitetura.
- Se SIM: construir persistencia de snapshot. Se NAO/limitado: TTL ou guard de credito interim (re-run local gratis + confirmar antes de global).
- Fontes: pearch.ai/pricing, /frequently-asked-questions, github Pearch-ai/mcp_pearch.

---
## FASE 4 — SPEC EXECUTAVEL (decisoes travadas 2026-05-29)

DECISAO Paulo: persistir TODOS os perfis Pearch pesquisados (modelo "pesquisou = do recrutador").
Storage existente reaproveitado: external_candidate_profiles (docid=source_profile_id, linkedin_url,
raw_payload, company_id, RLS JA ativo + 4 policies). Supressao: docid_blacklist JA wirado
(exclude_candidate_ids -> pearch_service:1263). Hoje a tabela so e populada no IMPORT (import_export.py:219), nao na busca.

### Passos
1. Migration: add coluna search_fingerprint (String, index) em external_candidate_profiles (down_revision=head atual; checar REGRA 5). RLS ja existe.
2. Persist-on-search: em pearch_service/_shared apos resultados Pearch, upsert por (company_id, source_profile_id) reusando o builder de ExternalCandidateProfile (import_export.py:219). Tag search_fingerprint. Idempotente (upsert, nao duplica). CUIDADO: hot path de busca — teste + nao bloquear resposta (best-effort/async).
3. Supressao (B): antes da busca Pearch, query source_profile_id da empresa (opcional: recentes/TTL) -> exclude_candidate_ids -> docid_blacklist. Economiza credito. Toggle de UX? (Paulo decide se sempre-on).
4. Resgate congelado (A): endpoint GET resultados por search_fingerprint (carrega de external_candidate_profiles, SEM chamar Pearch, SEM credito). Frontend: reabrir historico/lista carrega snapshot (nao re-roda). Re-hidrata feedback por docid (casa: snapshot preserva docid original).
5. LGPD (OBRIGATORIO — lia-compliance):
   - Base legal: interesse legitimo recrutamento (docstring + ADR).
   - Retencao/TTL: purgar perfis nao-engajados apos N meses (definir N). 
   - Erasure: incluir external_candidate_profiles no cascade de eliminacao do data_subject (Art. 18). Hoje NAO esta.
   - RLS: ja ativo (isolamento empresa). Manter.
6. Sensores: teste upsert idempotente; teste supressao (docids excluidos da request); teste resgate carrega sem chamar Pearch (mock); contract test RLS; teste erasure remove perfis.

### Risco: persist-on-search toca o hot path de busca (alta concorrencia). Best-effort + idempotente + nao bloquear a resposta da busca.
