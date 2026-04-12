# T2 Fase 1 — Diagnostico de Endpoints de Busca

**Data**: 2026-04-12
**Pre-requisito**: T1 validada (docs/audit/apify-t1-fase3-output.md — todos OK)

---

## 2.1 INVENTARIO COMPLETO DE ENDPOINTS DE BUSCA

| # | Arquivo | Rota | Metodo | Escopo | Usa Pearch? | Enrichment hook? |
|---|---------|------|--------|--------|-------------|-----------------|
| 1 | `search.py` | `/search/` | POST | Busca NLP | Sim (Pearch FAST) | **Sim** (enrich_and_filter) |
| 2 | `jd_search.py` | `/search/jd-search/` | POST | Busca por JD | Sim (Pearch FAST) | **Sim** (enrich_and_filter) |
| 3 | `similar_search.py` | `/search/similar-profile/` | POST | Busca perfil similar | Sim (Pearch FAST) | **Sim** (enrich_and_filter) |
| 4 | `archetypes.py` | `/search/archetypes/` | GET | Listar arquetipos | Nao | Nao |
| 5 | `archetypes.py` | `/search/archetypes/{id}/search` | POST | Busca por arquetipo | Sim (Pearch FAST) | Pendente (usa ArchetypeSearchResultDTO) |
| 6 | `core_search.py` | `/search/core/` | POST | Busca core | Sim (Pearch FAST) | **Sim** (via _shared) |

### Funcao compartilhada: `enrich_and_filter_candidates`

**Arquivo**: `app/api/v1/candidate_search/_shared.py`

Funcao adicionada que:
1. Recebe lista de candidatos (qualquer tipo)
2. Identifica candidatos sem email/phone
3. Chama `ContactEnrichmentService.enrich_search_results_and_filter()`
4. Retorna apenas candidatos COM pelo menos email ou phone
5. Candidatos sem contato apos enrichment sao FILTRADOS

**Usada em**: search.py, jd_search.py, similar_search.py, core_search.py

---

## 2.2 MAPEAMENTO DO FLUXO PEARCH

### SearchType.PRO — onde existia e impacto de remover

| Arquivo | Uso | Status |
|---------|-----|--------|
| `libs/models/lia_models/pearch.py` | `SearchType.PRO` no enum | **REMOVIDO** |
| `pearch_service.py` | `base_cost` calculo | **ATUALIZADO** (sempre = 1) |
| `credits.py` | Validacao Pro | **REMOVIDO** |
| Todos endpoints search | `searchType` param | **ATUALIZADO** (sempre FAST) |
| Frontend tipos | `'fast' \| 'pro'` | **ATUALIZADO** (apenas 'fast') |

### estimate_credits hoje (sem Pro)

- Base cost: 1 credito (sempre FAST)
- Insights + Scoring: 2 creditos
- Email/Phone via Pearch: removido (Apify = $0.01)
- Freshness: +2 creditos (opcional)
- **Total base por candidato: 3 creditos**

---

## 2.3 MAPEAMENTO DO REVEAL DE CONTATO

### Fluxo completo em contact.py

1. `POST /search/reveal-contact/` recebe `{candidate_id, reveal_type, linkedin_slug}`
2. **Passo 1 (Apify)**: Se linkedin_slug, tenta `ContactEnrichmentService` ($0.01, 0 creditos)
3. **Passo 2 (Pearch fallback)**: Se Apify falha, usa Pearch FAST
   - Email: 2 creditos
   - Phone: 14 creditos
4. Persiste via `persist_revealed_contact`
5. Retorna `{email, phone, credits_used, source}`

### Onde inserir Apify como alternativa

Ja implementado! contact.py tenta Apify PRIMEIRO, so cai no Pearch se:
- Nao tem linkedin_slug
- Apify falha (circuit open, timeout, etc)

---

## 2.4 MAPEAMENTO DO SOURCING AGENT

### System prompt (sourcing_system_prompt.py)

- Menciona custos de busca na instrucao do agente
- Referencia "busca rapida (1 credito)" e "contatos via Apify"

### Tools de busca

| Tool | Arquivo | Usa Pearch? |
|------|---------|-------------|
| `search_candidates` | `sourcing_tool_registry.py` | Sim (FAST) |
| `search_by_jd` | `sourcing_tool_registry.py` | Sim (FAST) |
| `search_similar_profile` | `sourcing_tool_registry.py` | Sim (FAST) |
| `reveal_contact` | `sourcing_tool_registry.py` | Sim (Apify first, Pearch fallback) |

---

## 2.5 PONTO DE INSERCAO DO ENRICHMENT

### search.py

- **Ponto**: Apos receber `response` do Pearch, antes do `return`
- **Variavel**: `response.profiles` (lista de CandidateSearchResultDTO)
- **Hook**: `enrich_and_filter_candidates(db, response.profiles)` — **JA IMPLEMENTADO**

### jd_search.py

- **Ponto**: Apos receber resultados da busca JD
- **Variavel**: lista de candidatos retornada
- **Hook**: `enrich_and_filter_candidates(db, candidates)` — **JA IMPLEMENTADO**

### similar_search.py

- **Ponto**: Apos receber perfis similares
- **Variavel**: lista de candidatos retornada
- **Hook**: `enrich_and_filter_candidates(db, candidates)` — **JA IMPLEMENTADO**

### archetypes.py (arquetipo search)

- **Ponto**: Apos busca por arquetipo, antes do return
- **Variavel**: lista de `ArchetypeSearchResultDTO`
- **Hook**: PENDENTE — usa DTO diferente (ArchetypeSearchResultDTO vs CandidateSearchResultDTO)
- **Nota**: `enrich_search_results_and_filter` usa `getattr` generico, deve funcionar com qualquer objeto que tenha `id`, `email`, `linkedin_url`

---

## RESUMO

| Item | Status |
|------|--------|
| SearchType.PRO removido | OK (backend + frontend) |
| Enrichment hook em search.py | OK |
| Enrichment hook em jd_search.py | OK |
| Enrichment hook em similar_search.py | OK |
| Enrichment hook em archetypes.py | PENDENTE |
| reveal_contact com Apify first | OK |
| Frontend tipos atualizados | OK |
| Custos atualizados no frontend | OK |
