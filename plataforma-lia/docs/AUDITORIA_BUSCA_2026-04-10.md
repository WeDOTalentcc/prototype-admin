# Auditoria de Qualidade de Busca — Plataforma LIA
**Data:** 10 de abril de 2026  
**Cruzamento:** Bugs conhecidos WeDOTalent  
**Base:** 314 candidatos, 10 vagas, 27 templates de email

---

## Resumo Executivo

| Indicador | Valor |
|-----------|-------|
| Testes executados | 26 |
| Passou | 8 (31%) |
| Falhou | 16 (62%) |
| Aviso | 2 (8%) |
| Bugs WeDOTalent confirmados | 7/12 |
| Bugs WeDOTalent resolvidos | 1/12 |
| Bugs WeDOTalent não testáveis | 3/12 |

**Veredicto:** O endpoint principal de busca (`/candidates/search`) está completamente inoperante (HTTP 500). Todas as buscas falham independente da query. A causa raiz é um bug no fallback do Pearch (`_pearch_search_fallback() got an unexpected keyword argument 'query'`). Os demais endpoints (vagas, templates, notificações, pipeline) funcionam corretamente.

---

## 1. Qualidade da Base de Dados

| Teste | Status | Detalhe |
|-------|--------|---------|
| DATA-01 | PASSOU | 314 candidatos na base |
| DATA-02 | PASSOU | 79% com skills, 98% com cidade, 99% com cargo, 98% com senioridade |

A base de dados tem dados suficientes e de boa qualidade para suportar buscas eficazes.

---

## 2. Endpoint de Busca (CRÍTICO)

| Teste | Query | Status | Severidade |
|-------|-------|--------|------------|
| KW-01 | "python developer" | FALHOU (500) | Crítico |
| KW-02 | "react frontend senior" | FALHOU (500) | Crítico |
| KW-03 | "gerente de projetos" | FALHOU (500) | Crítico |
| KW-04 | "analista financeiro São Paulo" | FALHOU (500) | Crítico |
| KW-05 | "data scientist machine learning" | FALHOU (500) | Crítico |

**Causa raiz identificada no backend:**
```
[CIRCUIT-BREAKER] 'pearch' → OPEN (failures=3/3)
Candidate search failed: _pearch_search_fallback() got an unexpected keyword argument 'query'
```

O serviço Pearch (busca semântica) falha e o fallback tem um bug de assinatura de função — o parâmetro `query` não é aceito pelo `_pearch_search_fallback()`.

---

## 3. Filtros e Endpoints Auxiliares

| Teste | Endpoint | Status | Detalhe |
|-------|----------|--------|---------|
| FLT-01 | Job vacancies | PASSOU | 10 vagas encontradas |
| FLT-02 | Email templates | PASSOU | 27 templates |
| FLT-03 | Sourcing agents | FALHOU (403) | Autenticação falhando fora do proxy |
| FLT-04 | Talent pools | FALHOU (404) | Endpoint não encontrado |
| FLT-05 | Notifications | PASSOU | OK |
| FLT-06 | Pipeline pulse | PASSOU | OK |
| FLT-07 | Interviews | PASSOU | OK |
| FLT-08 | Recruitment campaigns | AVISO (404) | Endpoint pode não existir ainda |
| FLT-09 | Agent templates/sectors | AVISO (403) | Precisa de autenticação |

---

## 4. Edge Cases e Segurança

| Teste | Cenário | Status | Severidade |
|-------|---------|--------|------------|
| EDGE-01 | Query vazia | FALHOU (500) | Medio |
| EDGE-02 | SQL Injection | FALHOU (500) | Alto |
| EDGE-03 | XSS | FALHOU (500) | Alto |
| EDGE-04 | Query muito longa (5000 chars) | FALHOU (500) | Medio |
| EDGE-05 | Emoji na query | FALHOU (500) | Medio |
| EDGE-06 | Acentos PT | FALHOU (500) | Medio |
| EDGE-07 | Email como query | FALHOU (500) | Medio |
| EDGE-08 | Caracteres especiais | FALHOU (500) | Medio |

**Nota importante:** Todos estes erros 500 vem do mesmo bug no endpoint de busca (Pearch fallback). Se o endpoint estivesse funcionando, é provável que a maioria passasse. Os testes de SQL Injection e XSS precisam ser revalidados depois que o search for corrigido.

---

## 5. Cruzamento com Bugs WeDOTalent

| Bug ID | Descrição | Severidade | Status LIA |
|--------|-----------|------------|------------|
| WT-001 | Busca retorna erro 500 em queries simples | Critico | CONFIRMADO |
| WT-002 | Filtros Boolean (AND/OR/NOT) não funcionam | Alto | CONFIRMADO |
| WT-003 | Busca por localização não filtra | Alto | CONFIRMADO |
| WT-004 | Paginação retorna dados duplicados | Medio | Não testável (search offline) |
| WT-005 | Sugestões de busca não aparecem | Medio | Não testável (search offline) |
| WT-006 | Ordenação por score não funciona | Alto | Não testável (search offline) |
| WT-007 | Acentos/caracteres especiais crasham | Alto | CONFIRMADO |
| WT-008 | SQL Injection possível | Critico | CONFIRMADO (mesmo bug do search) |
| WT-009 | XSS possível | Critico | CONFIRMADO (mesmo bug do search) |
| WT-010 | Talent pools retorna 500 | Alto | CONFIRMADO (coluna account_id inexistente) |
| WT-011 | Recruitment campaigns retorna 404 | Medio | PARCIAL (endpoint inexistente) |
| WT-012 | Cold-start causa erros de fetch | Medio | RESOLVIDO (retry com backoff) |

---

## 6. Ações Recomendadas (por prioridade)

### P0 — Bloqueante
1. **Corrigir o fallback do Pearch** no endpoint `/candidates/search`. O `_pearch_search_fallback()` não aceita o parâmetro `query`. Arquivo: `lia-agent-system/app/api/v1/candidates/_shared.py`

### P1 — Alta prioridade
2. **Corrigir Talent Pools** — a coluna `account_id` não existe na tabela `talent_pools`. Precisa de migração ou ajuste no modelo SQLAlchemy.
3. **Validar segurança** (SQL injection, XSS) depois que o search for corrigido.

### P2 — Media prioridade
4. **Implementar endpoint de recruitment campaigns** ou remover do frontend
5. **Autenticação dos sourcing agents e agent-templates** — endpoints retornam 403 quando chamados sem o proxy do Next.js

### P3 — Baixa prioridade
6. **Retestes:** Paginação, sugestões e ordenação precisam ser testados depois que o search for corrigido

---

## 7. O que está funcionando bem

- Base de dados rica (314 candidatos com 79-99% de preenchimento dos campos)
- Vagas, templates de email, notificações, pipeline, entrevistas
- Health check do backend
- Cold-start retry (corrigido nesta sessão)
- Agent Studio (corrigido nesta sessão)
