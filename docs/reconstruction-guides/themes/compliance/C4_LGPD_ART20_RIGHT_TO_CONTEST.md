# Theme C4 — LGPD Art. 20 Right to Contest + Candidate Portal

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance) + cross-ref Card 5 (Frontend)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit

---

## O que é este tema

Direito do candidato de **contestar decisão automatizada** e **receber explicação estruturada** dos critérios considerados. Implementa dois marcos legais sobrepostos:
- **LGPD Art. 20** — revisão de decisão automatizada + fornecimento de critérios
- **EU AI Act Art. 86** — direito à explicação em sistemas de IA de alto risco (recrutamento enquadra — Anexo III categoria 4)

A LIA atende este direito através do **Candidate Portal** — canal autenticado via JWT do candidato (separado do JWT do recrutador), rate-limited, anti-IDOR, com sanitização obrigatória de output (nunca expor scoring bruto).

**Boundary com temas irmãos:**
- **C1 Fairness** — bloqueia decisão enviesada ANTES dela existir; C4 trata da decisão APÓS existir
- **C3 Consent & DSR** — DSR cobre 5 outros tipos de direito; C4 é o 6º tipo (`automated_decision_review`)
- **I8 Auth** — valida JWT do candidato (token separado); C4 consome o fluxo de auth
- **I6 API Layer** — endpoint patterns; C4 é um caso específico

---

## Arquivos conectados (14 arquivos + 2 YAMLs)

### Camada Persona (LLM vê — 2 arquivos)

| Arquivo | Bundle | Como é injetado |
|---------|--------|-----------------|
| `candidate_self_service.yaml` | LIA_YAMLS_CANONICAL_BUNDLE §domains | system_prompt do `CandidateSelfServiceAgent`. Regra 8 explicitamente cita Art. 86 + instrução "chamar explain_candidate_decision" |
| `compliance_block.yaml` (seção `right_to_contest` em `decision` e `communication`) | LIA_YAMLS_CANONICAL_BUNDLE §shared | Injetado via `ComplianceDomainPrompt` — orienta LLM a aceitar pedidos de contestação sem descartar |

### Camada Código (Python — 12 arquivos)

**API Layer (3 arquivos):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `candidate_portal.py` | `app/api/v1/candidate_portal.py` (174L) | 2 endpoints públicos: `POST /api/v1/candidate/chat` + `GET /api/v1/candidate/applications`. Auth: JWT candidate_token. Rate limit: 10/hora, 30/dia |
| `candidate_portal_explanation.py` | `app/api/v1/candidate_portal_explanation.py` (154L, verificado SSH 2026-04-24) | **Endpoint-ponte Art. 86.** `GET /api/v1/candidate/decisions/explain?candidate_token=...&vacancy_id=...` — reusa `decision_explanation.py` lógica mas com sanitização candidate-facing |
| `decision_explanation.py` | `app/api/v1/decision_explanation.py` (233L) | Endpoint **para recrutadores** (`get_current_user`): retorna reasoning, factors, confidence, fairness_check, calibration_weights. Usado internamente — candidate version sanitiza |

**Agent & Tools (7 arquivos):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `candidate_react_agent.py` | `app/domains/candidate_self_service/agents/candidate_react_agent.py` | Agente LLM específico do portal. Herda `LangGraphReActBase` |
| `candidate_tool_registry.py` | `app/domains/candidate_self_service/agents/candidate_tool_registry.py` | Whitelist de 4 tools: `get_application_status`, `get_interview_info`, `get_wsi_feedback`, `explain_candidate_decision` |
| `candidate_system_prompt.py` | `app/domains/candidate_self_service/agents/candidate_system_prompt.py` | System prompt builder para agente candidate |
| `explain_candidate_decision.py` | `app/domains/candidate_self_service/tools/explain_candidate_decision.py` (novo 2026-04-23) | Tool que chama a lógica de decision explanation + `_sanitize_decision()` + `_FORBIDDEN_FIELDS` SSoT + `_ART_86_NOTICE` |
| `get_application_status.py` | `app/domains/candidate_self_service/tools/get_application_status.py` | Retorna etapa atual, data da última movimentação. SEM wsi_score/lia_score |
| `get_interview_info.py` | `app/domains/candidate_self_service/tools/get_interview_info.py` | Detalhes de entrevista agendada (data, hora, formato) |
| `get_wsi_feedback.py` | `app/domains/candidate_self_service/tools/get_wsi_feedback.py` | Feedback construtivo disponibilizado pela empresa (opt-in) |

**Services & Repositories (2 arquivos):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `candidate_status_service.py` | `app/domains/candidate_self_service/services/candidate_status_service.py` (70L) | `validate_token(candidate_token, secret)` + `check_rate_limit(candidate_id)` via Redis |
| `candidate_status_repository.py` | `app/domains/candidate_self_service/repositories/candidate_status_repository.py` (73L) | `log_portal_access(candidate_id, vacancy_id, company_id, channel, tools_called, fairness_triggered)` — audit log específico |

### Integration points

- **Candidate JWT é SEPARADO** do recruiter JWT (key: `CANDIDATE_PORTAL_JWT_SECRET`)
- **Rate limit** via Redis keys: `css_rate:{candidate_id}:hour` + `:day`
- **Audit log** em `candidate_portal_audit_logs` table — NUNCA tem PII, só IDs + `tools_called` + `fairness_triggered`
- **`_FORBIDDEN_FIELDS`** é SSoT de campos que jamais vão ao candidato (compartilhado entre tools)

---

## Lógica IN → OUT

### Input (endpoint explanation)

```python
# GET /api/v1/candidate/decisions/explain
candidate_token: str  # JWT — CANDIDATE_PORTAL_JWT_SECRET
vacancy_id: str       # qual vaga específica (subset do que JWT permite)
```

JWT payload esperado:
```python
{
  "candidate_id": "uuid",
  "vacancy_id": "uuid",
  "company_id": "uuid",  # anti-IDOR — SEMPRE do token
  "iat": ..., "exp": ...
}
```

### Processing

**Fluxo completo** (do endpoint-ponte `candidate_portal_explanation.py`):

```
1. Recebe candidate_token + vacancy_id
2. CandidateStatusService.validate_token(token, secret) — retorna token_data ou None
   - Se None → HTTPException 401
3. CandidateStatusService.check_rate_limit(candidate_id)
   - Se limite estourado → HTTPException 429
4. Extrai candidate_id + company_id do TOKEN (anti-IDOR)
5. Chama internal lógica de decision_explanation:
   - Query AuditLog por candidate_id + vacancy_id + company_id
   - Retorna raw reasoning, factors, confidence, fairness_flags, calibration_weights
6. Sanitização via _sanitize_decision():
   - REMOVE campos em _FORBIDDEN_FIELDS
   - MANTÉM criteria_evaluated (lista em linguagem natural)
   - MANTÉM criteria_ignored (PROTECTED_CRITERIA_LABELS — transparência)
   - Agrega fairness_check em string simples ("passed"|"under_review")
7. Adiciona _ART_86_NOTICE sempre
8. CandidateSelfServiceRepository.log_portal_access():
   - tools_called=["explain_candidate_decision"]
   - fairness_triggered=True se algum decision tinha fairness_flags
9. Retorna APIResponse (ADR-008 envelope)
```

### Output

```python
{
  "decisions": [
    {
      "decision_type": "cv_screening" | "wsi_evaluation" | "pipeline_transition" | ...,
      "timestamp": "ISO8601",
      "criteria_evaluated": ["Experiência em Python", "5+ anos backend"],
      "criteria_ignored": ["Idade", "Gênero", "Etnia/raça", "Estado civil", ...],  # transparência ativa
      "reasoning_summary": "Análise baseada em N critério(s) objetivo(s).",  # nunca raw reasoning
      "fairness_check": "passed" | "under_review",
      "human_reviewed": bool
    }
  ],
  "transparency_note": "Os seguintes critérios foram EXCLUÍDOS de toda análise por proteção legal: ...",
  "art_86_notice": "De acordo com o EU AI Act (Art. 86) e a LGPD (Art. 20), você tem direito de solicitar revisão humana desta decisão dentro de 30 dias. Para isso, responda a este canal ou contate o canal oficial de compliance da empresa.",
  "total_decisions": N
}
```

### Campos NUNCA retornados ao candidato

**`_FORBIDDEN_FIELDS` SSoT** em `explain_candidate_decision.py`:

```python
_FORBIDDEN_FIELDS = frozenset([
    "wsi_score", "lia_score", "wsi_final_score", "match_percentage",
    "red_flags", "confidence", "score", "factors_weights",
    "calibration_weights_used", "calibration_weights",
    "recruiter_notes", "rejection_code", "is_private",
    "cpf", "current_salary", "desired_salary",
    "diversity_race_ethnicity", "diversity_disability", "diversity_lgbtqia",
])
```

**Razão de cada exclusão:**
- `wsi_score`, `lia_score`, `confidence` — scoring bruto não é apropriado (candidato pode inferir ranking)
- `red_flags`, `rejection_code` — linguagem interna do produto
- `factors_weights`, `calibration_weights` — segredo comercial (LGPD Art. 18 §4º permite manter)
- `cpf`, `current_salary` — PII / dado sensível
- `diversity_*` — atributos protegidos (LGPD Art. 11)

### Side effects

- **Audit log** em `candidate_portal_audit_logs`:
  - `tools_called = ["explain_candidate_decision"]`
  - `fairness_triggered = True/False`
  - `channel = "web"` (ou "whatsapp", "email")
- **Rate limit contador** incrementado em Redis
- **Metrics:** contador `candidate_art86_requests_total{company_id}`

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Candidato solicita revisão humana via portal | Agente LLM sugere contato via canal formal (configurado por `company_id` em `CompanyComplianceSettings.contato_revisao`) |
| Rate limit atingido (candidato "farma" requests) | 429 + mensagem "Limite atingido, tente mais tarde" |
| JWT expirado ou inválido | 401 + mensagem genérica (não revela causa exata — anti-enumeration) |
| Nenhuma decisão encontrada | 200 com `"message": "Ainda não há decisões registradas..."` |
| Decisão ainda `under_review` (fairness) | Retorna `fairness_check: "under_review"` + orientação de aguardar |
| Candidato contesta por escrito via email | Compliance team recebe email → abre DSR tipo `automated_decision_review` (C3) |

---

## EU AI Act Art. 86 vs LGPD Art. 20

**LGPD Art. 20** (vigente desde 2020):
- Direito de revisão por pessoa natural de decisões automatizadas que afetem interesses
- Direito a receber critérios e procedimentos utilizados
- Controlador pode manter segredo comercial (§4º)

**EU AI Act Art. 86** (vigente 02/08/2026 para sistemas high-risk):
- Direito a explicação clara e significativa do papel da IA na decisão
- Para sistemas enquadrados no Anexo III (recrutamento enquadra na categoria 4)
- Prazo de contestação: razoável (recomendado 30 dias)

**Interseção:**
- Ambos exigem transparência sobre critérios
- Art. 86 é mais específico para IA; Art. 20 é genérico para automação
- LIA atende **ambos** via o mesmo endpoint — ganha cobertura dupla

**Texto canônico do aviso** (`_ART_86_NOTICE` em `explain_candidate_decision.py` linha 46 — **não** em `candidate_portal_explanation.py` e **não** `_ART_86_NOTICE_PT`):
```
"De acordo com o EU AI Act (Art. 86) e a LGPD (Art. 20), você tem direito 
de solicitar revisão humana desta decisão dentro de 30 dias. Para isso, 
responda a este canal ou contate o canal oficial de compliance da empresa."
```

---

## Anti-IDOR Pattern

**Threat:** candidato A tenta acessar decisões do candidato B.

**Mitigação canônica:**

```python
# candidate_portal_explanation.py
token_data = await CandidateStatusService().validate_token(candidate_token, _JWT_SECRET)
candidate_id = token_data["candidate_id"]      # ALWAYS from token
company_id = token_data["company_id"]          # ALWAYS from token — anti-IDOR
resolved_vacancy_id = vacancy_id or token_data["vacancy_id"]  # vacancy_id do query string VALIDADO contra token
```

**Nunca:**
```python
# ❌ PROIBIDO — candidate_id do body/query
candidate_id = request.body["candidate_id"]
```

**Audit logging** captura tentativas de IDOR (vacancy_id query ≠ vacancy_id do token → log `"idor_attempt"` + 403).

---

## Instruções para Claude Code / Cursor

### "Implementa Right to Contest + Candidate Portal no v5"

```
1. COPIE 12 arquivos Python (agents + tools + services + repositories + APIs)

2. IMPLEMENTE 2 migrations:
   - candidate_portal_audit_logs (id, candidate_id, vacancy_id, company_id, channel, tools_called, fairness_triggered, accessed_at)
   - Se não existir: audit_log com columns (criteria_used, criteria_ignored, reasoning, fairness_flags)

3. CONFIGURE .env:
   - CANDIDATE_PORTAL_JWT_SECRET=<secret separado do recruiter JWT>
   - Redis configurado (rate limit)

4. GERE JWTs de candidato:
   - Flow: recrutador compartilha link → backend gera JWT com candidate_id+vacancy_id+company_id
   - Exp: 30 dias (alinhado ao prazo de contestação)
   - Assinado com CANDIDATE_PORTAL_JWT_SECRET (HS256)

5. REGISTRE router no app/api/routes.py:
   app.include_router(candidate_portal_router, prefix="/api/v1", tags=["candidate-self-service"])
   app.include_router(candidate_portal_explanation_router, tags=["candidate-portal-explanation"])

6. SETUP agent:
   - CandidateSelfServiceAgent herda de LangGraphReActBase
   - Whitelist 4 tools em candidate_tool_registry.py
   - system_prompt via candidate_system_prompt.py — deve ler candidate_self_service.yaml

7. FE INTEGRATION (responsabilidade do Card 5):
   - Tela render do response
   - NUNCA mostrar campos em _FORBIDDEN_FIELDS (mesmo que acidentalmente vierem)
   - Botão "Solicitar revisão humana" abre email compose ou form

8. VERIFIQUE:
   - pytest tests/test_candidate_portal_explanation.py (contract tests)
   - Smoke: gerar JWT válido → GET /api/v1/candidate/decisions/explain → response sanitizada
   - Smoke: JWT inválido → 401
   - Smoke: rate limit → 429 após 10 requests em 1h
   - IDOR test: JWT de A tenta acessar vacancy_id de B → bloqueado
```

### "Adiciona novo tool candidate-facing"

```
1. Criar tool em app/domains/candidate_self_service/tools/<novo>.py
2. Registrar via @tool_handler("candidate_self_service", require_company=True)
3. Adicionar ao _CANDIDATE_TOOLS whitelist em candidate_tool_registry.py
4. SEMPRE sanitizar output via _FORBIDDEN_FIELDS check
5. SEMPRE log via log_portal_access
6. Atualizar candidate_self_service.yaml se o fluxo de uso mudou
7. Add test em tests/unit/test_<tool_name>.py
```

### Setup em CLAUDE.md

```markdown
## Compliance: Right to Contest (LGPD Art. 20 + EU AI Act Art. 86)

- **Candidate JWT é SEPARADO** do recruiter JWT (CANDIDATE_PORTAL_JWT_SECRET)
- **company_id SEMPRE do token**, nunca do payload (anti-IDOR)
- **Rate limit** 10/hora, 30/dia via Redis
- **Sanitização obrigatória** — usar `_FORBIDDEN_FIELDS` SSoT antes de responder
- **Art. 86 notice** OBRIGATÓRIO em toda resposta
- **Audit log** em candidate_portal_audit_logs (IDs only, zero PII)

Consultar `themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md` antes de criar tools ou endpoints candidate-facing.
```

### Setup em `.cursor/rules/candidate-portal.mdc`

```
---
description: "C4 Right to Contest + Candidate Portal"
alwaysApply: false
---

Quando o usuário pedir para:
- Implementar endpoint candidate-facing
- Criar tool que roda no portal do candidato
- Expor dados de decisão automatizada

1. Leia themes/compliance/C4_LGPD_ART20_RIGHT_TO_CONTEST.md completo
2. USE candidate_token JWT, NUNCA recruiter token
3. company_id SEMPRE derivado do token (anti-IDOR)
4. Sanitize via _FORBIDDEN_FIELDS (importar de explain_candidate_decision.py)
5. Include _ART_86_NOTICE em toda resposta
6. Log via log_portal_access SEMPRE (tools_called + fairness_triggered)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Nomes de funções/classes (mantidos legíveis)
- JWT library (PyJWT, jose, etc.)
- Rate limit backend (Redis, Memcached, in-memory com cuidado)
- Formato de response (JSON, XML se cliente exigir)
- Idioma do `_ART_86_NOTICE` (adaptar ao mercado)
- TTL do JWT (30 dias é recomendado mas configurável)
- Número de tools candidate-facing (pode ter mais ou menos que 4)

### NÃO pode adaptar (base legal)

| Invariante | Por quê | Consequência se violar |
|-----------|---------|------------------------|
| Endpoint candidate-facing AUTENTICADO (nunca público open) | Anti-enumeration + LGPD Art. 18 §9º (verificar identidade) | Vazamento de dados de outros candidatos |
| `company_id` do token, nunca do payload | LGPD Art. 6 minimização + isolamento tenant | IDOR pattern + breach |
| `_FORBIDDEN_FIELDS` sempre aplicado | LGPD Art. 18 §4º (segredo comercial) + proteção de atributos C1 | Revelar scoring bruto = prejudica ranking / dano reputacional |
| `_ART_86_NOTICE` em toda resposta | EU AI Act Art. 86 + LGPD Art. 20 | Violação direta de obrigação legal |
| Prazo 30 dias para contestação | Recomendado por EU AI Act (prazo "razoável") | Prazo muito curto viola Art. 86 |
| Audit log em `candidate_portal_audit_logs` | LGPD Art. 37 + Art. 38 | Falha de rastreabilidade |
| Rate limit 10/hora, 30/dia | Anti-abuse + DoS prevention | Ataque de farming de dados |
| Canal formal de compliance para revisão humana | LGPD Art. 20 (revisão humana é direito) | Candidato sem canal = violação |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** CANDIDATE_PORTAL_JWT_SECRET configurado (separado do recruiter)
- [ ] **(P0)** Endpoint `/api/v1/candidate/decisions/explain` funcional
- [ ] **(P0)** `validate_token()` rejeita JWT inválido/expirado (401)
- [ ] **(P0)** Rate limit 10/hora, 30/dia funcional (429)
- [ ] **(P0)** `_FORBIDDEN_FIELDS` aplicado — assert em testes
- [ ] **(P0)** `_ART_86_NOTICE` presente em toda resposta
- [ ] **(P0)** Audit log em `candidate_portal_audit_logs` registra cada request
- [ ] **(P0)** anti-IDOR: `company_id` do token, vacancy_id validado
- [ ] **(P1)** 4 tools candidate-facing registradas no tool_registry
- [ ] **(P1)** `candidate_self_service.yaml` regra 8 ativa (chama explain tool quando solicitado)
- [ ] **(P1)** Frontend consumindo endpoint (Card 5)
- [ ] **(P1)** Email flow: link com JWT gerado ao notificar candidato
- [ ] **(P2)** Métricas `candidate_art86_requests_total` no Prometheus
- [ ] **(P2)** Alerta quando `fairness_triggered=True` em >N% dos requests
- [ ] **(P2)** Dashboard compliance mostra "tempo médio de resposta a contestações"

---

## Gotchas e erros comuns

| Sintoma | Causa raiz | Como evitar |
|---------|-----------|-------------|
| Candidato vê wsi_score em response | Dev adicionou novo campo sem conferir `_FORBIDDEN_FIELDS` | Adicionar `_FORBIDDEN_FIELDS` check em linter CI |
| IDOR permitido (A acessa B) | `candidate_id` do payload em vez do token | Code review + contract test |
| Rate limit falha silenciosamente (Redis down) | `check_rate_limit()` entra em fail-open: retorna `{"allowed": True, "remaining_hour": -1, "remaining_day": -1}` — candidato passa mesmo com Redis indisponível | Monitorar Redis health; alertar quando `remaining_hour == -1` em métricas (indica modo fail-open ativo) |
| JWT sem exp ou com exp muito longo | Config errada | Obrigatório: exp <= 30 dias; assinatura HS256 |
| Candidato não recebe link por email | JWT gerado mas SMTP falhou | Job de retry + alerta compliance team |
| `_ART_86_NOTICE` em idioma errado | Hardcoded PT-BR mas candidato está em EN | Template i18n baseado em candidate locale |
| Audit log com PII (regressão) | Campo novo passa por log sem sanitize | Schema limita audit a IDs only |
| Tentativa de contestação sem endpoint (email direto) | Canal formal não configurado por company | `CompanyComplianceSettings.contato_revisao` obrigatório |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| Valid token → 200 sanitized | `tests/test_candidate_portal_explanation.py::test_valid_token` | JWT válido retorna response sem _FORBIDDEN_FIELDS |
| Invalid token → 401 | `tests/test_candidate_portal_explanation.py::test_invalid_token` | JWT mal formado → 401 |
| Rate limit → 429 | `tests/test_candidate_portal_explanation.py::test_rate_limit` | 11th request em 1h → 429 |
| IDOR attempt → blocked | `tests/test_candidate_portal_explanation.py::test_idor_blocked` | JWT candidate A + vacancy_id B (de outra company) → falha |
| Sanitize removes forbidden | `tests/test_candidate_portal_explanation.py::test_sanitize_removes` | Input com wsi_score → output não tem |
| Art. 86 notice present | `tests/test_candidate_portal_explanation.py::test_art86_notice` | Response sempre contém art_86_notice |
| Audit log created | `tests/test_candidate_portal_explanation.py::test_audit_logged` | Request → row em candidate_portal_audit_logs |
| No decisions → friendly msg | `tests/test_candidate_portal_explanation.py::test_empty_decisions` | 200 com message ajustada |

---

## Referências

### Bundles verbatim
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 2 (candidate_self_service.yaml completo)
- `LIA_YAMLS_CANONICAL_BUNDLE.md` §Parte 1 (compliance_block.yaml — seção right_to_contest)

### Reconstruction guides
- `LIA_PERSONA_RECONSTRUCTION_GUIDE.md` §9.8 (candidate portal architecture)
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §11.1 (plano do endpoint-ponte)

### Handoff dev
- `COMPLIANCE_DEV_HANDOFF_2026-04-23.md` — invariante #6 (right_to_contest)
- `FRONTEND_DEV_HANDOFF_2026-04-23.md` — UI integration (Card 5)

### Regulatório
- **LGPD Art. 20** — revisão de decisão automatizada
- **LGPD Art. 18 §9º** — verificação de identidade do titular
- **LGPD Art. 18 §4º** — segredo comercial (permite não revelar pesos)
- **EU AI Act Art. 86** — direito à explicação (vigente 02/08/2026)
- **EU AI Act Anexo III categoria 4** — recrutamento é high-risk
- **`responsible-ai/eu-ai-act-technical-documentation-pt.md`** §9 — explicabilidade

### Runbook
- **FAIRNESS_LAYER3_RUNBOOK.md** §B (relação com fairness_triggered)

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit em `lia-agent-system/`*
