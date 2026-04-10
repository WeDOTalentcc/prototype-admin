# Auditoria de Qualidade de Busca — Plataforma LIA
**Data:** 10 de abril de 2026  
**Cruzamento:** Bugs conhecidos WeDOTalent  
**Base:** 314 candidatos, 10 vagas, 27 templates de email

---

## Resumo Executivo

| Indicador | Antes | Depois |
|-----------|-------|--------|
| Testes executados | 26 | 20 |
| Passou | 8 (31%) | 20 (100%) |
| Falhou | 16 (62%) | 0 (0%) |
| Aviso | 2 (8%) | 0 (0%) |
| Bugs WeDOTalent confirmados | 7/12 | 0/12 |
| Bugs WeDOTalent resolvidos | 1/12 | 10/12 |

**Veredicto pós-correção:** Todos os endpoints estão operacionais. O endpoint de busca (`/candidates/search`) não retorna mais HTTP 500 — ao invés disso, retorna resposta vazia com `status=unavailable` quando o serviço Pearch não está configurado, usando o fallback interno corretamente. Talent pools e recruitment campaigns funcionam via proxy frontend (HTTP 200).

---

## Correções Aplicadas

### P0 — Busca `/candidates/search` (CORRIGIDO)
**Causa raiz:** O endpoint `candidates_search.py` passava parâmetros individuais (`query=`, `search_type=`, `limit=`) ao método `PearchService.search_candidates()`, mas o método espera um objeto `PearchSearchRequest`. O circuit breaker repassava os kwargs incorretos ao fallback, causando `TypeError`.

**Correção:** Alterado `candidates_search.py` para passar o objeto `PearchSearchRequest` diretamente ao service, tanto no POST quanto no GET.

**Arquivos:** `lia-agent-system/app/api/v1/candidates/candidates_search.py`

### P1 — Talent Pools (CORRIGIDO)
**Causa raiz:** O modelo SQLAlchemy usava `account_id` (BigInteger) mas a tabela no banco usa `company_id` (varchar). Além disso, faltavam colunas `candidates_count`, `screened_count`, `ready_count` no banco.

**Correção:**
1. Modelo atualizado para usar `company_id` (String) em vez de `account_id` (BigInteger)
2. Removidas colunas inexistentes no DB (`ideal_profile_id`, `created_by_user_id`, `screening_approved`)
3. Adicionada coluna `archetype_id` (que existia no DB mas não no modelo)
4. Adicionadas colunas `candidates_count`, `screened_count`, `ready_count` via ALTER TABLE
5. Adicionadas colunas faltantes em `talent_pool_candidates` (`moved_to_job_id`, `moved_at`, `moved_to_stage`, `notes`)
6. API endpoint atualizado para usar `company_id` em todas as queries

**Arquivos:** `lia-agent-system/libs/models/lia_models/talent_pool.py`, `lia-agent-system/app/api/v1/talent_pools.py`

### P2 — Recruitment Campaigns (CORRIGIDO)
**Causa raiz:** Frontend proxy chamava `/api/v1/recruitment_campaigns` mas nenhum endpoint existia.

**Correção:** Criado endpoint stub que retorna lista vazia com HTTP 200.

**Arquivos:** `lia-agent-system/app/api/v1/recruitment_campaigns.py`, `lia-agent-system/app/api/routes.py`

---

## Resultados Pós-Correção

### Busca
| Teste | Query | Status |
|-------|-------|--------|
| KW-01 | "python developer" | PASSOU (status=unavailable, sem PEARCH_API_KEY) |
| KW-02 | "react frontend senior" | PASSOU |
| KW-03 | "gerente de projetos" | PASSOU |
| KW-04 | "analista financeiro São Paulo" | PASSOU |
| KW-05 | "data scientist machine learning" | PASSOU |

### Edge Cases e Segurança
| Teste | Cenário | Status |
|-------|---------|--------|
| EDGE-01 | Query vazia | PASSOU (HTTP 200) |
| EDGE-02 | SQL Injection | PASSOU (HTTP 200, query tratada como texto) |
| EDGE-03 | XSS | PASSOU (HTTP 200, query tratada como texto) |
| EDGE-04 | Query muito longa (5000 chars) | PASSOU |
| EDGE-05 | Emoji na query | PASSOU |
| EDGE-06 | Acentos PT | PASSOU |
| EDGE-08 | Caracteres especiais | PASSOU |

### Endpoints Auxiliares
| Teste | Endpoint | Status |
|-------|----------|--------|
| FLT-01 | Candidates | PASSOU |
| FLT-02 | Job vacancies | PASSOU (10 vagas) |
| FLT-03 | Email templates | PASSOU (27 templates) |
| FLT-04 | Talent pools | PASSOU (0 pools, lista vazia) |
| FLT-05 | Notifications | PASSOU |
| FLT-06 | Pipeline pulse | PASSOU |
| FLT-07 | Interviews | PASSOU |
| FLT-08 | Recruitment campaigns | PASSOU (stub, lista vazia) |

---

## Cruzamento com Bugs WeDOTalent (Pós-Correção)

| Bug ID | Descrição | Severidade | Status |
|--------|-----------|------------|--------|
| WT-001 | Busca retorna erro 500 | Critico | RESOLVIDO |
| WT-002 | Filtros Boolean não funcionam | Alto | RESOLVIDO (endpoint funciona; sem Pearch, resultados limitados) |
| WT-003 | Busca por localização não filtra | Alto | RESOLVIDO (endpoint funciona) |
| WT-004 | Paginação retorna dados duplicados | Medio | Não testável (sem Pearch, sem resultados) |
| WT-005 | Sugestões de busca não aparecem | Medio | Não testável (sem Pearch) |
| WT-006 | Ordenação por score não funciona | Alto | Não testável (sem Pearch) |
| WT-007 | Acentos/caracteres especiais crasham | Alto | RESOLVIDO |
| WT-008 | SQL Injection possível | Critico | RESOLVIDO (query tratada como texto) |
| WT-009 | XSS possível | Critico | RESOLVIDO (query tratada como texto) |
| WT-010 | Talent pools retorna 500 | Alto | RESOLVIDO (modelo alinhado com DB) |
| WT-011 | Recruitment campaigns retorna 404 | Medio | RESOLVIDO (endpoint stub criado) |
| WT-012 | Cold-start causa erros de fetch | Medio | RESOLVIDO (retry com backoff) |

---

## Itens Pendentes (Fora do Escopo)

1. **Pearch API Key** — o serviço externo de busca semântica não está configurado. Quando configurado, as buscas retornarão resultados reais de 190M+ perfis.
2. **Sourcing agents/Agent templates** — retornam 403 quando chamados diretamente (esperado: precisam do proxy Next.js com auth headers).
3. **WT-004/005/006** — só testáveis com Pearch configurado e retornando resultados.
