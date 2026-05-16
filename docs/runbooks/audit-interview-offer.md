# Audit & Ownership Sealing — Interview + Offer (T-1157)

> Status: **ativo**. Owner: backend/compliance. Origem: Task #1157
> (follow-up de T-1149 / T-1129 sealing).

## 1. O que está protegido

| Domínio | Service | Por que precisa de audit |
|---|---|---|
| `interview_scheduling` | `scheduling_service.py`, `calendar_service.py` | Entrevista marcada/cancelada → evento de pipeline (LGPD; reconstrução de "quem agendou") |
| `interview_intelligence` | `transcription_service.py` (+ outros) | Transcrição é PII sensível (LGPD Art.46); decisão de pipeline downstream |
| `offer` | `offer_service.py` | Proposta de remuneração → **SOX 7-year retention** + EU AI Act (hiring decision) |

Os 3 domínios passaram a ter:

1. **Sentinela AST de audit obrigatório** —
   `tests/integration/security/test_audit_required_interview_offer_t_1157.py`.
   Visita todo `async def` público que faz mutação no DB
   (`db.commit`, `_repo.create/update/delete`, `db.add`, …) e exige
   chamada a `AuditService.log_decision[_in_session]`.
2. **Sentinela AST de ownership cross-validation** —
   `tests/integration/security/test_ownership_xvalidation_interview_offer_t_1157.py`.
   Visita rotas mutating em `interviews.py`, `interview_notes.py`,
   `interview_analysis.py`, `scheduling.py`, `offers.py`, `calendar.py`
   e exige que o handler **repasse** `company_id=` para a camada
   inferior (complementa o gate T-1149 que apenas garante recebimento).
3. **8 mutations agora auditadas** — `offer_service.{cancel_draft,mark_sent}`,
   `scheduling_service.create_interview`, `transcription_service.transcribe_and_persist`
   (4 nesta sessão; 4 restantes ficam na baseline para remoção em PR
   futuro — ver §4).
4. **Hardening `self_scheduling_public.py`** — 2 endpoints públicos
   tiveram `Depends(require_company_id)` errôneo removido (estavam
   quebrando o fluxo de candidato); endpoint do recrutador agora
   sobrescreve `body.company_id` com o claim do JWT (defesa contra
   tenant-spoofing via body).
5. **Middleware com regex pública EXPLÍCITA** em
   `app/middleware/auth_enforcement.py` — `PUBLIC_REGEX_PATHS` casa
   APENAS `GET /api/v1/scheduling/link/{token}` e
   `POST /api/v1/scheduling/link/{token}/confirm` (token 16-128 chars,
   `[A-Za-z0-9_-]`). O prefixo amplo `/api/v1/scheduling/link/` foi
   **REMOVIDO** de `PUBLIC_PREFIXES` para evitar que sub-rotas
   futuras (ex.: `/link/admin/X`, `/link/{token}/cancel`) fiquem
   acidentalmente auth-bypassed. Ver §5.1 para detalhes.

## 2. Padrão ratchet (igual T-1149)

```
.baseline_audit_missing_interview_offer.txt          ← débito audit
.baseline_ownership_xvalidation_interview_offer.txt  ← débito ownership
```

* **Entrada NOVA** (método/rota nova sem audit ou sem company_id) →
  build quebra com mensagem da sentinela.
* **Entrada FIXED** → remova manualmente da baseline no mesmo PR.
  `test_*_baseline_not_stale` falha se você esqueceu.

Estado inicial (data desta task): 7 audit + 26 ownership = 33 débitos
tracked. Plano: drenar em PRs incrementais de ≤5 entradas.

## 3. Como adicionar audit em um método novo

```python
from app.shared.compliance.audit_service import AuditService

async def cancel_interview(self, db, interview_id, company_id, reason):
    interview = await self._repo.get_by_id(interview_id, company_id)
    if not interview:
        return None
    interview.status = "cancelled"
    await db.commit()

    # ───── Audit (T-1157) ─────
    try:
        await AuditService().log_decision_in_session(
            session=db,
            company_id=company_id,
            agent_name="scheduling_service",
            decision_type="schedule_interview",   # ou "approve_hiring" / "generate_feedback"
            action="cancel_interview",
            decision="cancelled",
            reasoning=[reason or "no reason"],
            criteria_used=["interview_status_transition"],
            candidate_id=str(interview.candidate_id) if interview.candidate_id else None,
            job_vacancy_id=str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
        )
        await db.commit()
    except Exception as audit_err:
        logger.warning(f"[T-1157] audit failed: {audit_err}")
    return interview
```

**Convenções:**
* Sempre `try/except` fail-soft em torno do audit (não bloquear UX em
  falha de auditoria — só logar).
* `decision_type` ∈ `{schedule_interview, approve_hiring, generate_feedback, score_candidate}`
  (ver `app/shared/compliance/audit_service.py` `RETENTION_PERIODS`).
* `agent_name` = nome do service (`scheduling_service`,
  `offer_service`, `transcription_service`).
* `actor_user_id` é opcional na variante `_in_session` mas
  recomendado quando houver `user_id` no contexto da chamada.

## 4. Drenagem da baseline (backlog priorizado)

| Prioridade | Entrada | Risco | Esforço |
|---|---|---|---|
| **P0** | `offer_service:create_or_get_draft` | SOX — proposta criada sem trilha | XS |
| **P0** | `offer_service:update_draft` | SOX — alteração silenciosa de salário/condições | XS |
| **P1** | `scheduling_service:cancel_interview` | LGPD — cancelamento sem trilha | S |
| **P1** | `scheduling_service:complete_interview` | LGPD/WSI — conclusão sem trilha | S |
| **P2** | `scheduling_service:update_interview` | LGPD — reagendamento silencioso | S |
| **P2** | `scheduling_service:create_interview_with_teams` | LGPD — só wrapper; criar audit no caminho de sucesso | M |
| **P3** | `calendar_service:create_generic_event` | Generic event — baixo valor compliance | M |

Para rotas (ownership): drenar começando pelas que tocam
`offer_proposal` (4 rotas em `offers.py`), depois `interviews.py`
(11 rotas), `calendar.py` (7), `interview_notes.py` (4), `scheduling.py` (2),
`interview_analysis.py` (1).

## 5. CI gate

Adicione (ou confirme presença) no job `pytest` do CI:

```bash
cd lia-agent-system && pytest \
  tests/integration/security/test_multi_tenant_ownership_inventory_t_1129.py \
  tests/integration/security/test_audit_required_interview_offer_t_1157.py \
  tests/integration/security/test_ownership_xvalidation_interview_offer_t_1157.py \
  tests/integration/security/test_self_scheduling_public_properties_t_1157.py \
  -q
```

As 2 sentinelas AST rodam em **<2s** (sem DB). Os property tests
do self-scheduling público são hermeticos (mockam o service) e
cobrem **9 propriedades**:

* 404 quando token não existe (GET + POST/confirm)
* 410 quando `status="used"` (replay defense, GET)
* 410 quando `expires_at < now` (TTL defense, GET)
* 410 em `confirm/replay` e `confirm/expired` (replay no mutation path)
* GET **não** vaza `candidate_email`, `candidate_phone`, `company_id`,
  `candidate_id`, `interviewer_emails` (PII non-disclosure)
* POST `/link` (recrutador) sobrescreve `body.company_id` pelo claim
  do JWT (anti-spoofing)
* Middleware regex casa SÓ os 2 paths intencionais (rejeita
  `/link/admin/X`, `/link/{token}/cancel`, prefixo bare, tokens curtos)

## 5.1 Middleware: regex explícita vs prefixo amplo

O arquivo `app/middleware/auth_enforcement.py` mantém duas listas:

* `PUBLIC_PREFIXES` (tuple de strings) — match por `startswith()`. Uso
  amplo justificado para `/api/public/`, `/docs/`, etc.
* `PUBLIC_REGEX_PATHS` (tuple de `re.Pattern`) — match exato por
  regex. **OBRIGATÓRIO** para qualquer surface pública sob um prefixo
  que também hospeda endpoints autenticados (caso do
  `/api/v1/scheduling/link/...`).

A sentinela `test_middleware_no_longer_uses_broad_scheduling_prefix`
impede que alguém reintroduza `/api/v1/scheduling/link/` em
`PUBLIC_PREFIXES` (cobertura cega sub-rotas futuras).

## 6. Rollback / emergência

Se a sentinela bloquear um hotfix urgente:

1. **Não** desabilite o teste. Adicione a entrada ao arquivo
   `.baseline_*.txt` correspondente como **TEMPORÁRIO** com comentário
   `# TEMP T-1157 hotfix YYYY-MM-DD — remover até <data>`.
2. Abra issue de follow-up referenciando #1157 e a entrada.
3. Para o hotfix do `self_scheduling_public.py`: se o middleware
   precisar reverter, remova as duas regexes de `PUBLIC_REGEX_PATHS`
   E remova o arquivo de `tests/.allowlist_public_endpoints.txt`
   — os dois em conjunto restauram o estado "quebrado mas gated".
   **NÃO** reintroduza o prefixo amplo `/api/v1/scheduling/link/` em
   `PUBLIC_PREFIXES` (a sentinela
   `test_middleware_no_longer_uses_broad_scheduling_prefix` quebraria
   a build, e além disso reabre o gap original).

## 7. Pontos abertos (não cobertos por T-1157)

* **`SelfSchedulingLink` não tem coluna `company_id`** — confirm_slot
  resolve tenant via FK transitiva (candidate_id/job_vacancy_id). Risk
  de cross-tenant token forgery: BAIXO (token = `secrets.token_urlsafe(32)`,
  single-use, expira). Mitigação completa requer migração Alembic +
  backfill + RLS — encaminhado para Task de follow-up.
* **`zero_touch_scheduling_service` marcado `RAILS-DEPRECATED`** —
  será removido após handoff Rails (UC-P1-22). Não vale a pena
  hardenizar mais.

## 8. Referências

* T-1129 sealing: `tests/integration/security/test_multi_tenant_ownership_inventory_t_1129.py`
* AuditService: `app/shared/compliance/audit_service.py`
* `replit.md` § Contratos críticos (entrada "Audit obrigatório nos 3 domínios")
* Task: `.local/tasks/audit-interview-offer-ownership.md`
