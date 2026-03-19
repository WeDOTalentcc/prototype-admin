# LIA Agent System — API Reference

> Versão 3.0.0 | WeDOTalent | 15/03/2026
>
> Documentação interativa: `GET /docs` (Swagger UI) | `GET /docs/redoc` (ReDoc) | `GET /openapi.json`

---

## Autenticação

Todos os endpoints protegidos requerem **Bearer Token** via WorkOS SSO:

```
Authorization: Bearer <access_token>
```

Endpoints públicos (sem auth): `/health`, `/api/v1/candidate-portal/*`, `/api/v1/shared-searches/*`

---

## Convenções Gerais

| Campo | Formato |
|-------|---------|
| IDs | UUID v4 (`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`) |
| Datas | ISO 8601 UTC (`2026-03-15T10:00:00Z`) |
| Multi-tenant | `company_id` obrigatório em criação; `?company_id=<uuid>` em buscas |
| Paginação | `?page=1&page_size=20` |
| Erro | `{"error": true, "status_code": N, "message": "..."}` |

---

## Grupos de Endpoints

### 1. Agentes (Chat + HITL)

#### WebSocket — Chat Principal
```
WS /api/v1/agent-chat/{company_id}/{user_id}
```
Protocolo de mensagens:
- `→ {"type": "message", "content": "texto"}` — enviar mensagem
- `← {"type": "response", "content": "...", "agent": "..."}` — resposta do agente
- `← {"type": "approval_required", "thread_id": "...", "action": "...", "description": "..."}` — HITL interrupt
- `→ {"type": "approval_response", "thread_id": "...", "approved": true}` — responder HITL via WS

#### HITL — Aprovação via API REST
```
POST /api/v1/hitl/{thread_id}/approve
```
Body:
```json
{
  "pending_id": "uuid",
  "approved": true,
  "comment": "opcional"
}
```
Resposta (200):
```json
{
  "thread_id": "uuid",
  "pending_id": "uuid",
  "approved": true,
  "comment": null,
  "timestamp": "2026-03-15T10:00:00Z"
}
```

```
GET /api/v1/hitl/{thread_id}/pending
```
Retorna aprovação pendente mais recente ou `{"pending": null}`.

---

### 2. Candidatos

```
GET    /api/v1/candidates                    — listar (multi-tenant)
POST   /api/v1/candidates                    — criar
GET    /api/v1/candidates/{id}               — detalhe
PUT    /api/v1/candidates/{id}               — atualizar
DELETE /api/v1/candidates/{id}               — soft delete

GET    /api/v1/candidates/rag-search         — busca híbrida BM25 + pgvector
GET    /api/v1/candidates/{id}/toon          — TOON card por vaga
```

#### RAG Hybrid Search
```
GET /api/v1/candidates/rag-search?q=&company_id=&limit=20&alpha=0.5
```
Parâmetros:
- `q` (obrigatório): query em linguagem natural
- `company_id` (obrigatório): tenant ID
- `limit`: 1–100, padrão 20
- `alpha`: 0.0 = BM25 puro | 1.0 = semântico puro | 0.5 = híbrido (padrão)

Resposta (200):
```json
{
  "results": [{"candidate_id": "uuid", "score": 0.85, ...}],
  "query": "desenvolvedor python sênior",
  "total": 3,
  "source": "hybrid",
  "fairness_ok": true,
  "search_time_ms": 45.2
}
```

#### TOON Card
```
GET /api/v1/candidates/{candidate_id}/toon?job_id=&company_id=&anonymize=false
```
- Cache Redis TTL 1h
- `anonymize=true`: `name_display` mascarado como "Candidato X" (LGPD)

Resposta (200):
```json
{
  "candidate_id": "uuid",
  "job_id": "uuid",
  "headline": "Desenvolvedor Python Sênior",
  "highlights": ["5 anos de experiência em Python", "Liderança técnica"],
  "match_score": 87,
  "skills_match": ["Python", "FastAPI", "PostgreSQL"],
  "name_display": "João S.",
  "anonymized": false,
  "fairness_reviewed": true
}
```

---

### 3. Vagas

```
GET    /api/v1/job-vacancies                 — listar vagas
POST   /api/v1/job-vacancies                 — criar vaga
GET    /api/v1/job-vacancies/{id}            — detalhe
PUT    /api/v1/job-vacancies/{id}            — atualizar
DELETE /api/v1/job-vacancies/{id}            — fechar vaga

POST   /api/v1/import/upload-file            — importar JD (.txt/.md/.pdf/.docx, 5MB)
POST   /api/v1/jd-generation/generate        — gerar JD via IA
GET    /api/v1/job-analytics/{job_id}/funnel — funil da vaga
```

---

### 4. Guardrails

```
GET    /api/v1/guardrails                    — listar (?domain=&company_id=&level=&is_active=)
POST   /api/v1/guardrails                    — criar (201)
GET    /api/v1/guardrails/{id}               — detalhe (200 | 404)
PUT    /api/v1/guardrails/{id}               — atualizar (200 | 404)
PATCH  /api/v1/guardrails/{id}/toggle        — toggle is_active (200 | 404)
DELETE /api/v1/guardrails/{id}               — soft delete (204 | 404)
POST   /api/v1/guardrails/seed-defaults      — seed idempotente (9 defaults: 5 primários + 4 secundários)
```

Schema de resposta (GuardrailResponse):
```json
{
  "id": "uuid",
  "level": "primary | secondary",
  "domain": "cv_screening | communication | sourcing | job_management | null",
  "node": "string | null",
  "tool": "string | null",
  "rule": "Nunca discriminar por gênero...",
  "blocking_message": "Ação bloqueada por guardrail.",
  "is_active": true,
  "company_id": "uuid | null",
  "updated_by": "admin",
  "updated_at": "2026-03-15T10:00:00"
}
```

---

### 5. Compliance

#### Bias Audit
```
GET /api/v1/bias-audit/job/{job_id}          — Four-Fifths Rule por vaga (4 dimensões)
GET /api/v1/bias-audit/job/{job_id}/history  — histórico de snapshots (SOX/ISO 27001)
```

#### Model Drift
```
GET  /api/v1/drift/status                    — status atual de drift
POST /api/v1/drift/run-batch                 — executar batch check (admin)
```

#### LGPD / DSR
```
GET    /api/v1/data-subject-requests         — listar DSRs
POST   /api/v1/data-subject-requests         — criar solicitação (acesso/exclusão/portabilidade)
PUT    /api/v1/data-subject-requests/{id}/complete  — completar DSR
PUT    /api/v1/data-subject-requests/{id}/reject    — rejeitar DSR
GET    /api/v1/admin/lgpd/cleanup-status     — status da limpeza de retenção
```

#### Fairness Reports
```
GET /api/v1/fairness-reports                 — relatórios de fairness por vaga
```

---

### 6. Pipeline

```
GET  /api/v1/pipeline/stages/{job_id}        — stages do pipeline
POST /api/v1/pipeline/transition             — transição de stage (aciona agente)
GET  /api/v1/pipeline/velocity/{job_id}      — velocity metrics
```

---

### 7. Sourcing

```
POST /api/v1/sourcing/search                 — busca ativa (Pearch AI + internal)
POST /api/v1/sourcing/boolean-string         — gerar boolean string LinkedIn/Gupy
POST /api/v1/sourcing/outreach               — enviar abordagem (WhatsApp/email)
```

---

### 8. WSI — Entrevista Estruturada

```
POST /api/v1/wsi/start                       — iniciar sessão WSI
GET  /api/v1/wsi/session/{session_id}        — status da sessão
POST /api/v1/wsi/respond                     — resposta do candidato
GET  /api/v1/wsi/report/{session_id}         — relatório final WSI
```

---

### 9. Agendamento

```
GET  /api/v1/interviews/slots                — slots disponíveis
POST /api/v1/interviews/schedule             — agendar entrevista
PUT  /api/v1/interviews/{id}/reschedule      — reagendar
POST /api/v1/interviews/{id}/cancel          — cancelar
```

---

### 10. Analytics e ML

```
GET /api/v1/ml/insights                      — insights ML da vaga
GET /api/v1/ml/predict/time-to-fill          — previsão de fechamento
GET /api/v1/ml/predict/salary                — previsão de faixa salarial
GET /api/v1/reports/kpis                     — KPIs do recrutamento
GET /api/v1/reports/funnel                   — funil consolidado
```

---

### 11. Policy Engine

```
POST /api/v1/policy-engine/apply-sector/{company_id}?sector=tech|varejo|logistica|financeiro|saude|rpo
GET  /api/v1/policy-engine/blocks/{company_id}    — ver políticas ativas
```

---

### 12. Short Lists

```
GET    /api/v1/short-lists/{job_id}          — short list da vaga
POST   /api/v1/short-lists                   — criar short list
POST   /api/v1/short-lists/{job_id}/candidates  — adicionar candidato
DELETE /api/v1/short-lists/{job_id}/candidates/{candidate_id}  — remover candidato
```

---

### 13. Admin

```
GET  /api/v1/admin/circuit-breakers          — status de todos os circuit breakers
POST /api/v1/admin/circuit-breakers/{name}/reset   — reset de circuit breaker
POST /api/v1/admin/circuit-breakers/reset-all      — reset de todos
GET  /api/v1/admin/token-budget/{company_id} — orçamento de tokens LLM
```

---

### 14. Health

```
GET /health                                  — health check básico (sem auth)
GET /api/v1/health/langgraph                 — status LangGraph
GET /api/v1/observability/metrics            — métricas Prometheus
```

---

## Códigos de Erro

| Código | Significado |
|--------|-------------|
| 400 | Bad Request — parâmetros inválidos |
| 401 | Unauthorized — token ausente ou expirado |
| 403 | Forbidden — permissão insuficiente (multi-tenant) |
| 404 | Not Found — recurso não existe |
| 409 | Conflict — recurso já existe |
| 422 | Unprocessable Entity — validação Pydantic falhou |
| 429 | Too Many Requests — rate limit atingido |
| 500 | Internal Server Error — erro não tratado |
| 503 | Service Unavailable — circuit breaker aberto |

---

## Rate Limits

| Tier | Limite |
|------|--------|
| Default | 60 req/min por IP |
| Authenticated | 300 req/min por user |
| Agent Chat WS | 1 conexão por user |
| Upload (JD) | 10 uploads/hora |

---

## Changelog

| Versão | Data | Mudanças |
|--------|------|----------|
| 3.0.0 | 15/03/2026 | RAG híbrido (G6), TOON cards (G7), Guardrails CRUD (I1), HITL persistence (F1), PolicyEngine (Alpha 1) |
| 2.5.0 | 12/03/2026 | Bias Audit snapshots (G4), JD Import upload (P3-2), Drift batch job (G.2) |
| 2.0.0 | 08/03/2026 | 7 agentes ReAct, Short Lists (F4), FairnessGuard Layer 3 |
