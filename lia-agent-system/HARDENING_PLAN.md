# LIA Agent System — Hardening Plan

> Auditoria: 2026-04-06 | 1.820 arquivos Python | 428K LOC

---

## Sumário Executivo

| Prioridade | Bloco | Issues | Status |
|---|---|---|---|
| P0 | Segurança Crítica | 3 itens | pendente |
| P1 | Estabilidade do Banco | 3 itens | pendente |
| P2 | Qualidade / LGPD | 2 itens | pendente |
| P3 | Arquitetura (long-term) | 3 itens | backlog |

---

## P0 — Segurança Crítica

### P0.1 — SQL Injection no RLS
**Arquivo:** app/core/database.py linha 28
**Severidade:** CRÍTICO
**Status:** pendente

Problema: f-string interpolada direto no SET LOCAL do PostgreSQL RLS.
Vetor: company_id forjado no JWT pode injetar SQL no contexto de sessão.

ANTES (vulnerável):
    await db.execute(sa.text(f"SET LOCAL app.company_id = {company_id}"))

DEPOIS (parameterizado):
    await db.execute(sa.text("SET LOCAL app.company_id = :cid"), {"cid": company_id})

Teste pós-fix: rodar query multi-tenant e confirmar que RLS continua isolando por company_id.

---

### P0.2 — Vazamento de stack traces em 500s
**Arquivo:** app/main.py linha 317
**Severidade:** ALTO — 958 endpoints afetados em 125 arquivos
**Status:** pendente

Problema: raise HTTPException(status_code=500, detail=str(e)) expõe mensagens
internas (SQLAlchemy errors, paths, schema names) para o cliente.

Fix no handler global (cobre os 958 de uma vez):
    # linha 322 do http_exception_handler
    detail = exc.detail if exc.status_code < 500 else "Internal server error"

Regra: 4xx mantém mensagens descritivas (UX). 5xx sempre retorna genérico.
Detalhe real fica em logs + Sentry apenas.

---

### P0.3 — python-jose com CVEs ativos
**Arquivos:** app/auth/security.py, app/auth/rails_jwt.py, app/auth/dependencies.py
**Severidade:** ALTO
**CVEs:** CVE-2024-33664 (algorithm confusion), CVE-2024-33663 (key confusion)
**Status:** pendente

Migrar de python-jose para PyJWT (já presente no pyproject.toml).

Mudanças na API:
  - from jose import jwt, JWTError
  + import jwt
  + from jwt.exceptions import InvalidTokenError as JWTError

  - jwt.encode(payload, secret, algorithm="HS256")    # retornava bytes em versões antigas
  + jwt.encode(payload, secret, algorithm="HS256")    # retorna str diretamente

  - jwt.decode(token, secret, algorithms=["HS256"])
  + jwt.decode(token, secret, algorithms=["HS256"])   # API idêntica

Remover python-jose do pyproject.toml após migração.

---

## P1 — Estabilidade do Banco

### P1.1 — N+1 queries em candidate_lists.py
**Arquivo:** app/api/v1/candidate_lists.py linhas 389 e 481
**Severidade:** ALTO
**Status:** pendente

Problema: loop sobre candidate_ids com 2 queries individuais por ID.
100 candidatos = 200 queries. 1.000 candidatos = 2.000 queries.

Fix: buscar todos com WHERE id IN (...), depois processar em memória.

---

### P1.2 — N+1 queries em workforce.py
**Arquivo:** app/api/v1/workforce.py linha 1001
**Severidade:** ALTO
**Status:** pendente

Mesmo padrão do P1.1. Fix idêntico.

---

### P1.3 — Endpoints sem paginação (547 .all() sem .limit())
**Severidade:** ALTO — pode causar OOM e timeouts
**Status:** pendente

Arquivos prioritários:
  - app/api/v1/candidate_lists.py:81  (lista todas as listas)
  - app/api/v1/workforce.py:75,252    (planos e headcounts)
  - app/api/v1/recruitment_journey.py:154 (templates)

Fix: adicionar skip: int = 0, limit: int = 100 como query params.

---

## P2 — Qualidade / LGPD

### P2.1 — 14 bare except sem tipo
**Severidade:** ALTO — captura KeyboardInterrupt, SystemExit, MemoryError
**Status:** pendente

Arquivos:
  - app/api/v1/billing.py:1012,1050
  - app/api/v1/candidates.py:211
  - app/domains/job_management/services/job_context_service.py:298,314,324,336
  - app/domains/cv_screening/services/wsi_voice_orchestrator.py:267

Fix: except: -> except Exception:

---

### P2.2 — PII em logs (LGPD Art. 46)
**Severidade:** MÉDIO
**Status:** pendente

Arquivos:
  - app/api/v1/email.py:118           (loga recipient_email)
  - app/api/v1/automation/event_handlers.py:632  (loga candidate_email)
  - app/api/v1/data_subject_requests.py:88       (loga subject_email)

Fix: substituir email por candidate_id nos logs.

---

## P3 — Arquitetura (backlog)

### P3.1 — Split candidate_search.py (5.708 linhas, 45 funções)
Seguir padrão do split do wsi.py.
Módulos: core_search.py (já existe), filters.py, ranking.py, contact.py (já existe), export.py.

### P3.2 — Split job_vacancies.py (4.951 linhas)
Módulos: creation.py, editing.py, publishing.py, analytics.py, templates.py.

### P3.3 — Consolidar observability.py duplicado
libs/models/lia_models/observability.py e app/domains/analytics/models/observability.py
diferem apenas em 1 import. Consolidar com alias de retrocompatibilidade.

---

## Changelog

| Data | Item | Descrição | Arquivos |
|---|---|---|---|
| 2026-04-06 | Plano criado | Auditoria profunda de 1.820 arquivos | HARDENING_PLAN.md |
| 2026-04-06 | P0.1 | SQL Injection no RLS corrigido — SET LOCAL → set_config parameterizado | app/core/database.py |
| 2026-04-06 | P0.2 | Vazamento de stack traces bloqueado em 958 endpoints 5xx | app/main.py |
| 2026-04-06 | P0.3 | python-jose (CVE-2024-33664/33663) → PyJWT 2.10.1 | app/auth/{security,rails_jwt,dependencies}.py |
| 2026-04-06 | P1.1 | N+1 queries em candidate_lists: N×2 → 2 queries + bulk insert | app/api/v1/candidate_lists.py |
| 2026-04-06 | P1.2 | N+1 queries em workforce: N×1 → 1 query + in-memory upsert | app/api/v1/workforce.py |
| 2026-04-06 | P1.3 | Paginação adicionada em list_templates (skip/limit) | app/api/v1/recruitment_journey.py |
| 2026-04-06 | P2.1 | 14 bare except: → except Exception: em 9 arquivos | billing, candidates, job_context_service, etc. |
| 2026-04-06 | P2.2 | 26 PII em logs removidos (LGPD Art. 46) — emails de candidatos | event_handlers, email_service, automation_*, etc. |
