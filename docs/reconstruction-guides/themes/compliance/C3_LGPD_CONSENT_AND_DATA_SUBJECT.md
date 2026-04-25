# Theme C3 — LGPD Consent & Data Subject Rights

**Layer:** Compliance  |  **Card Jira:** 2 (Compliance)
**Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/` no Replit

---

## O que é este tema

Operacionalização dos **direitos do titular** de dados pessoais sob LGPD:
- **Consentimento** (Arts. 7-9): captura, versionamento, granularidade por propósito, revogação
- **Acesso** (Art. 15): titular pede cópia dos dados
- **Exclusão / direito ao esquecimento** (Art. 17): titular pede remoção
- **Portabilidade** (Art. 18): titular pede dados em formato estruturado
- **Retenção** (Art. 16): deleção automática após período configurado
- **Notificação de incidentes** (Art. 48): breach reporting para ANPD
- **DPO** (Art. 41): registro e contato do Data Protection Officer

**Boundary com temas irmãos:**
- **C2 LGPD PII** — minimização de dados em logs/prompts; C3 é sobre direitos do titular
- **C4 LGPD Art. 20** — direito específico de contestação de decisão automatizada + candidate portal
- **C7 Audit Trail** — audit de operações sobre dados pessoais (quem acessou, quando)

---

## Arquivos conectados (11 Python + 0 YAMLs)

### Camada Persona (LLM vê — 0 arquivos)

Nenhum YAML específico para C3. Referências em `compliance_block.yaml` apontam apenas:
> `decision.lgpd`: "Se um candidato solicitar acesso ou exclusão de seus dados, utilize data_subject_request"

A instrução remete o LLM a **chamar uma tool** que opera sobre C3 — o tema em si é 100% código.

### Camada Código (Python — 11 arquivos)

**Consent domain (2 arquivos):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `dependencies.py` | `app/domains/consent/dependencies.py` | FastAPI dependency `get_consent_repo` |
| `consent_repository.py` | `app/domains/consent/repositories/consent_repository.py` | CRUD: ConsentVersion + ConsentEvent (granted/revoked/expired) |

**Data Subject domain (2 arquivos):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `dependencies.py` | `app/domains/data_subject/dependencies.py` | Dependency `get_data_subject_repo` |
| `data_subject_repository.py` | `app/domains/data_subject/repositories/data_subject_repository.py` | Fluxo completo DSR (Data Subject Request): create → assign → verify_identity → start_processing → complete/reject |

**LGPD domain (7 arquivos):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|------------------|
| `dependencies.py` | `app/domains/lgpd/dependencies.py` | Dependency `get_lgpd_repo` |
| `lgpd_repository.py` | `app/domains/lgpd/repositories/lgpd_repository.py` | DPO registry, breach notifications (ANPD), automated decisions (Art. 20) |
| `data_request_repository.py` | `app/domains/lgpd/repositories/data_request_repository.py` | Requests genéricos LGPD |
| `dsr_export_service.py` | `app/domains/lgpd/services/dsr_export_service.py` | **Art. 18 portabilidade** — exporta candidate data + gera JSON |
| `lgpd_cleanup_service.py` | `app/domains/lgpd/services/lgpd_cleanup_service.py` | **Art. 17 esquecimento** — TTL cleanup, deletion propagation (main DB + Redis + query embeddings + conversational memory) |
| `consent_checker_service.py` | `app/domains/lgpd/services/consent_checker_service.py` | Service helper: "titular X consentiu com propósito Y?" |
| `granular_consent_service.py` | `app/domains/lgpd/services/granular_consent_service.py` | **Consentimento granular por propósito** (marketing vs. product vs. third-party sharing) |

### Integration points

- **Candidate portal (C4)** expõe botões de DSR → cria `DataSubjectRequest` via `DataSubjectRepository.create_request()`
- **Background jobs (R4)** rodam `lgpd_cleanup_service.run_cleanup()` em cron diário
- **Audit log (C7)** recebe cada operação sobre dados pessoais (granted consent, revoke, delete, export)
- **Scoring services (C1)** consultam `GranularConsentService.check_purpose()` antes de usar dado para propósito específico

---

## Lógica IN → OUT

### Consent — versionamento

**Entidades** (da análise de `consent_repository.py`):
- `ConsentVersion`: versão ativa de texto de consentimento (ex.: "v1 - uso para recrutamento ativo")
- `ConsentEvent`: fato de consentimento por subject (granted / revoked / expired) ligado a uma version

**Lógica:**
```
Cliente (deployer) cria novas versões de consent_type (1 por propósito)
  ↓
Uma versão fica ativa (is_active=True)
  ↓
Subject (candidato) ao acessar portal vê o texto da versão ativa
  ↓
Aceita → create_event(subject_id, version_id, status=granted)
  ↓
Se revoga no futuro → create_event(status=revoked)
  ↓
consent_checker_service responde: "este subject consentiu com este propósito? (via última versão ativa)"
```

**Métodos-chave de `ConsentRepository`:**
- `get_active_version(company_uuid, consent_type)` — versão ativa atual
- `get_last_granted_event(...)` — último evento granted para um subject
- `create_event(...)` — registra granted/revoked/expired
- `count_granted`, `count_revoked`, `count_expired` — métricas para dashboard

### Data Subject Request (DSR) — fluxo

**Estados possíveis** (derivados de métodos de `DataSubjectRepository`):

```
CREATED (create_request)
   ↓
ASSIGNED (assign_request — atribui a um operator do compliance team)
   ↓
IDENTITY_VERIFIED (verify_identity — valida que o titular é quem diz ser)
   ↓
PROCESSING (start_processing — compliance começa a trabalhar)
   ↓
COMPLETED (complete_request) OR REJECTED (reject_request)
```

**Tipos de DSR** (Arts. 15, 17, 18):
- `access` — acesso aos dados (Art. 15)
- `erasure` — exclusão (Art. 17 — direito ao esquecimento)
- `portability` — exportação em formato estruturado (Art. 18)
- `rectification` — correção (Art. 18)
- `objection` — oposição a processamento (Art. 18)
- `automated_decision_review` — revisão de decisão automatizada (Art. 20 — **ver C4**)

**SLA legal:** LGPD exige resposta em **15 dias** (Art. 19 §1º).

### Art. 17 — Esquecimento (cleanup service)

**Propagação de deleção** (`lgpd_cleanup_service.py`):

```
Subject solicita exclusão
  ↓
schedule_deletion_for_candidate(candidate_id, reason, scheduled_for)
  → marca `deletion_scheduled_at` na tabela candidates
  ↓
Cron diário roda run_cleanup(dry_run=False) que:
  1. Hard delete da row principal
  2. _propagate_deletion_to_secondary_stores():
     - Rails API: DELETE /api/candidates/{id}
     - Gupy/Pandapé (ATS): API call de exclusão
     - HubSpot: remove da CRM
  3. _cleanup_query_embeddings_for_candidates: vector DB cleanup
  4. _flush_redis_candidate_cache: remove cache keys
  5. run_conversation_ttl_cleanup: remove memória conversacional (TTL)
  ↓
Audit log completo (C7) com cada store tocado + status
```

**Fail-safe:** se qualquer store falhar, a operação é marcada como `partial_deletion` com `retry_after` — compliance team recebe alerta.

### Art. 18 — Portabilidade (export service)

**Flow** (`dsr_export_service.py`):

```
DataSubjectRequest.type == 'portability'
  ↓
DsrExportService.export_candidate_data(candidate_id):
  1. Coleta dados de TODAS as fontes (candidate profile, pipeline history, WSI results, communications, consent events)
  2. Gera JSON estruturado (generate_portability_json)
  3. Encripta (C6 redis_crypto) com key de sessão
  4. Upload para S3/Storage temporário com TTL 24h
  5. Email para titular com link signed URL
  6. Audit log: quem exportou, para quem, quando, quais fontes
```

### Consent Granular (per purpose)

**Propósitos típicos** (definidos em `GranularConsentStatus`):
- `recruiting_active` — processar dados para vagas atuais
- `recruiting_future` — reter para vagas futuras (talent pool)
- `marketing` — comunicações de marketing
- `third_party_sharing` — compartilhar com empresas parceiras

**Lógica:**
- Candidato pode aceitar recruiting_active + recruiting_future, MAS negar marketing + third_party_sharing
- Antes de qualquer operação que use dado para propósito X, `consent_checker_service.check_purpose(subject_id, purpose=X)` retorna `True/False`
- Se `False` → operação é bloqueada + audit log registra

### Escalation / HITL

| Cenário | Ação | Responsável |
|---------|------|-------------|
| DSR criado sem identidade verificada | `verify_identity()` deve ser chamado antes de `start_processing()` | Compliance team (manual) |
| Cleanup falha em store externo (Rails/Gupy/HubSpot) | Marca `partial_deletion` + alerta | SRE + compliance retry |
| Breach (vazamento de dados detectado) | `create_breach()` + `mark_breach_anpd_notified()` em 72h (Art. 48) | DPO notifica ANPD |
| Consent version muda (novos termos) | Usuários ativos precisam re-aceitar ao próximo login | Product design + UI flow |
| Titular não responde verify_identity em 30 dias | DSR expira com status REJECTED + motivo documentado | Automático |

---

## Instruções para Claude Code / Cursor

### "Implementa LGPD Consent & Data Subject Rights no v5"

```
1. COPIE 11 arquivos Python (domains/consent/, data_subject/, lgpd/) com adaptação mínima

2. CRIE Alembic migrations para 8 tabelas:
   - consent_versions (version + type + is_active + text)
   - consent_events (subject_identifier + version_id + status + created_at)
   - data_subject_requests (type + status + subject_id + assigned_to + verified_at)
   - dpo_registry (company_id + dpo_name + dpo_email + updated_at)
   - breach_notifications (severity + anpd_notified_at + subjects_notified_at)
   - automated_decisions (subject_id + decision_type + human_reviewed + decision_snapshot)
   - data_requests (genérico — usado por LGPD repo)
   - candidate_deletion_schedules (candidate_id + scheduled_for + reason)

3. CONFIGURE scheduled jobs (ver R4):
   - lgpd_cleanup_service.run_cleanup: diário às 02h
   - run_conversation_ttl_cleanup: diário às 03h

4. EXPONHA endpoints no candidate portal (C4):
   - GET /api/v1/candidate/dsr-status (titular vê seus requests)
   - POST /api/v1/candidate/dsr/create (criar novo request)
   - POST /api/v1/candidate/consent/update (granular update)

5. INTEGRE com serviços consumidores:
   - Antes de scoring (C1): consultar granular_consent_service.check_purpose()
   - Antes de export/share: verificar consent `third_party_sharing`
   - Antes de marketing: verificar consent `marketing`

6. CONFIGURE DPO:
   - upsert_dpo() para registrar contato
   - Endpoint público /dpo-info para política de privacidade mostrar

7. VERIFIQUE:
   - pytest tests/integration/test_lgpd_flow.py (DSR completo end-to-end)
   - pytest tests/unit/test_consent_granular.py
   - pytest tests/unit/test_cleanup_propagation.py (deleção atinge todos os stores)
```

### "Adiciona LGPD compliance a uma feature nova"

```
Se feature coleta dado pessoal:
  → Definir consent_type específico
  → Criar ConsentVersion na tabela
  → UI captura consent antes de começar a processar
  → Log granted event

Se feature processa dado para novo propósito:
  → Verificar se consent_type existe (criar se não)
  → Consultar granular_consent_service.check_purpose() antes de cada operação
  → Se False → bloquear + mostrar mensagem ao usuário

Se feature cria/atualiza dado do titular:
  → Participar do cleanup flow (listar na `_propagate_deletion_to_secondary_stores`)

Se feature exporta dado:
  → Adicionar ao dsr_export_service.export_candidate_data (coleta completa)

Se feature toma decisão automatizada (scoring, ranking):
  → Criar record em automated_decisions table
  → Possibilitar human_review (ver C4 também)
```

### Setup em CLAUDE.md

```markdown
## Compliance: LGPD Consent & Data Subject Rights

- **Consent granular** por propósito — `granular_consent_service.check_purpose()` antes de cada operação
- **DSR flow** 6 estados: CREATED → ASSIGNED → IDENTITY_VERIFIED → PROCESSING → COMPLETED/REJECTED
- **SLA legal:** 15 dias (Art. 19 §1)
- **Deleção (Art. 17)** propaga em cascata: main DB + Rails + ATS + HubSpot + Redis + embeddings + memory
- **Portabilidade (Art. 18)** via `DsrExportService` com JSON assinado + S3 TTL 24h
- **DPO** registrado via `upsert_dpo()` — contato público para ANPD
- **Breach (Art. 48)** notificar ANPD em 72h via `mark_breach_anpd_notified()`

Consultar `themes/compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md`.
```

### Setup em `.cursor/rules/lgpd-rights.mdc`

```
---
description: "C3 LGPD Consent & Data Subject Rights"
alwaysApply: false
---

Quando o usuário mencionar: consent, DSR, right to be forgotten, data portability,
breach, DPO, ANPD, LGPD Arts. 7-9/15/17/18:

1. Leia themes/compliance/C3_LGPD_CONSENT_AND_DATA_SUBJECT.md
2. Consult granular_consent_service.check_purpose antes de processar
3. Propagate delete para TODOS os stores (lista verificada em lgpd_cleanup_service)
4. SEMPRE chame verify_identity ANTES de start_processing em DSR
5. SLA 15 dias — use scheduled jobs para garantir cumprimento
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Nomes de tabelas e classes
- Estrutura de dependency injection (FastAPI dependency vs constructor)
- Backend de storage para exports (S3 vs GCS vs Azure Blob)
- Email provider para notificações
- Formato de export (JSON vs CSV vs XML)
- Número de propósitos em granular consent (adaptar aos propósitos do produto)
- Intervalo do cleanup job (daily vs hourly)

### NÃO pode adaptar (base legal)

| Invariante | Por quê | Consequência se violar |
|-----------|---------|------------------------|
| 6 tipos de DSR (access, erasure, portability, rectification, objection, auto-decision-review) | LGPD Arts. 15, 17, 18, 20 | Negar direito do titular → multa ANPD |
| SLA de 15 dias para responder DSR | LGPD Art. 19 §1º | Multa + reputação |
| `verify_identity()` antes de `start_processing()` | LGPD Art. 18 §9º + proteção anti-fraude | Vazamento de dados para impostor |
| Propagação de deleção atinge TODOS os stores | LGPD Art. 17 (direito ao esquecimento é completo) | "Esquecimento" parcial = descumprimento |
| Breach notification ANPD em 72h | LGPD Art. 48 | Multa adicional por atraso |
| Consent granular por propósito (não global) | LGPD Art. 8 §4º + Art. 9 | Consent global não é válido legalmente |
| DPO registrado e público | LGPD Art. 41 | Sem DPO = violação estrutural |
| Audit log de todas operações sobre dados pessoais | LGPD Art. 37 | Rastreabilidade impossível = não conformidade |

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** 8 tabelas Alembic criadas e populadas com schema correto
- [ ] **(P0)** 11 arquivos Python implementados
- [ ] **(P0)** DSR flow completo (6 estados) funcionando end-to-end
- [ ] **(P0)** `verify_identity()` obrigatório antes de `start_processing()`
- [ ] **(P0)** Deleção propaga para Rails API + ATS + HubSpot + Redis + embeddings + memory
- [ ] **(P0)** SLA 15 dias monitorado (alerta se >13 dias sem ação)
- [ ] **(P0)** DPO registrado em `dpo_registry` para cada company
- [ ] **(P0)** Breach notification endpoint + timer 72h ANPD
- [ ] **(P1)** Granular consent por propósito (mínimo 4: active, future, marketing, sharing)
- [ ] **(P1)** Scheduled job de cleanup rodando diariamente
- [ ] **(P1)** Export JSON assinado com TTL (S3/GCS/Azure)
- [ ] **(P1)** UI no candidate portal (C4) para listar DSRs + consent status
- [ ] **(P1)** Email notifications (granted, revoked, expired, export ready)
- [ ] **(P2)** Dashboard de métricas (count granted/revoked/expired por period)
- [ ] **(P2)** Retenção automática configurável por consent_type

---

## Gotchas e erros comuns

| Sintoma | Causa raiz | Como evitar |
|---------|-----------|-------------|
| Consent "global" aceito cobre propósitos diversos | Design de UI mostra um único checkbox | Separar checkboxes por propósito (Art. 8 §4) |
| Deleção deixa embeddings órfãos | Cleanup apenas da row principal | `_cleanup_query_embeddings_for_candidates` obrigatório |
| DSR aprovado sem verificação de identidade | Skip do `verify_identity()` | Enforce no state machine — não permite start_processing sem verified_at |
| Breach notificado além de 72h | Manual delay, sem timer automático | Celery beat task monitora breaches não notificados |
| Export vaza PII no log de audit | `audit_service` logando payload completo | Log só `subject_id` + `export_type` + `sources_touched`, não payload |
| Titular revoga consent mas dado continua sendo usado | Scoring service não chama `check_purpose()` | Enforce via middleware (C5 Multi-tenancy intercepta) |
| Retroativo: dados antigos sem consent | Legacy data pré-LGPD | Migration de consent_bootstrap para titulares existentes |

---

## Testes obrigatórios

| Teste | Path | Cenário |
|-------|------|---------|
| Consent granted | `tests/unit/test_consent_repository.py::test_create_event_granted` | Event criado com status=granted |
| Consent revoked | `tests/unit/test_consent_repository.py::test_create_event_revoked` | Último event é revoked → checker retorna False |
| DSR state machine | `tests/integration/test_dsr_flow.py` | 6 estados em ordem, skips bloqueados |
| Cleanup propagation | `tests/integration/test_cleanup_all_stores.py` | Mock de todos os stores → assert calls |
| Portability export | `tests/integration/test_dsr_export.py` | JSON contém campos esperados, link TTL expira |
| Granular check | `tests/unit/test_granular_consent.py` | Titular com purpose=marketing=false → check retorna False |
| SLA monitoring | `tests/unit/test_dsr_sla.py` | Request com 14d sem ação → alerta gerado |
| Breach 72h timer | `tests/unit/test_breach_anpd_sla.py` | Breach >70h sem mark_anpd_notified → alerta |
| Audit LGPD operations | `tests/integration/test_lgpd_audit.py` | Toda operação LGPD gera audit log |

---

## Referências

### Bundles verbatim
- Nenhum YAML específico. Referência em `compliance_block.yaml` decision.lgpd cita `data_subject_request` genericamente.

### Reconstruction guides
- `COMPLIANCE_RECONSTRUCTION_GUIDE.md` §10.5 (LGPD requirements overview)

### Regulatório
- **LGPD Lei 13.709/2018:**
  - Art. 7, 8, 9 — base legal e consentimento
  - Art. 15 — acesso
  - Art. 16 — retenção
  - Art. 17 — direito ao esquecimento
  - Art. 18 — portabilidade, retificação, oposição
  - Art. 19 §1º — prazo 15 dias
  - Art. 37 — registro de operações
  - Art. 41 — DPO
  - Art. 48 — notificação ANPD 72h
- **ANPD (Autoridade Nacional de Proteção de Dados)** — guias oficiais
- **`responsible-ai/eu-ai-act-technical-documentation-pt.md`** §9.4 (acesso e exclusão)

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit em `lia-agent-system/`*
