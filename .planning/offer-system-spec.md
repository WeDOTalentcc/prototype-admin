# SPEC DEFINITIVO — Sistema de Proposta de Oferta WeDOTalent
**Versão:** 1.0 | **Data:** 2026-06-13 | **Autor:** Paulo Moraes via Claude Code
**Branch:** feat/benefits-prv-canonical | **Repo:** lia-agent-system + plataforma-lia

---

## Visão Geral: 3 Níveis de Produto

| Nível | Nome | O que faz | Fase |
|---|---|---|---|
| **N1** | Portal + Aceitação | Candidato recebe link real, abre carta, aceita/recusa digitalmente | Fase 1 |
| **N2** | Concierge Informacional | LIA proativa: status tracker, Teams cards, chat contextual, sincronização com painel "Decidir" | Fase 2 |
| **N3** | Agente Negociador | IA autonomamente conduz rodadas de negociação com aprovação HITL | Fase 3 |

---

## HARNESS ENGINEERING — Análise de Falhas

### Falhas de Harness Identificadas (pré-implementação)

| Bug | Tipo de Falha | Célula Harness | Guide Ausente | Sensor Ausente |
|---|---|---|---|---|
| **P0-1** `offer_link` nunca gerado | Falha de guide: nenhuma convenção exigia que `render_offer_template_variables` retornasse `offer_link` | Computacional×Guide | Template de variáveis obrigatórias | Teste de contrato que verifica keys obrigatórias no dict |
| **P0-2** Portal inexistente | Falha de guide: feature marcada como "enviada" sem portal existindo | Computacional×Guide | Checklist de feature-complete (wiring E2E) | Smoke test: GET `/portal/proposta/{token}` retorna 200 |
| **P1-5** `mark_sent` após falha | Falha de sensor: email falha silenciosamente, status vira "sent" sem entrega | Computacional×Sensor | REGRA 4 CLAUDE.md (sem fallback silencioso) | Teste: delivery.success=False → mark_sent NÃO chamado |
| **P1-2** `OfferHITLBanner` ghost | Falha de sensor: componente criado mas jamais importado | Computacional×Sensor | Nenhuma regra de "ghost component" | `check_capability_catalog_sync.py` pattern (já existe para tools) |
| **P1-4** URL mismatch hyphen/underscore | Falha de guide: sem convenção de naming de URLs | Computacional×Guide | Convenção: endpoints FastAPI = hyphen, proxy Next.js = hyphen | Sensor regex: `grep -rn "send_auto"` → deve retornar 0 |

### Guides Novos (feedforward — previnem recorrência)

```
GUIDE-1 (Computacional): Template de variáveis obrigatórias de oferta
  Arquivo: lia-agent-system/app/domains/offer/services/OFFER_TEMPLATE_VARS.md
  Regra: render_offer_template_variables() DEVE retornar pelo menos:
    {offer_link, candidate_name, job_title, salary, start_date, response_deadline}
  Enforcement: teste de contrato test_offer_template_vars_contract.py

GUIDE-2 (Computacional): Convenção de URLs de endpoints de oferta
  Arquivo: lia-agent-system/app/api/v1/offers.py (docstring)
  Regra: Todos os sub-endpoints usam hyphen (send-auto, prepare-manual).
    Proxy Next.js espelha exatamente. Nunca underscore.
  Enforcement: grep sensor no CI

GUIDE-3 (Computacional): mark_sent gate canônico
  Arquivo: CLAUDE.md (seção Offer Domain) + offer_service.py
  Regra: mark_sent(offer_id) NUNCA é chamado se delivery_result.success != True.
    Todo path de envio retorna explicitamente o resultado de entrega.
  Enforcement: teste test_offer_mark_sent_only_on_success.py

GUIDE-4 (Inferencial): Argumento para recusa de ghost components
  Arquivo: CLAUDE.md (seção Frontend)
  Regra: Componente criado mas não importado em nenhuma page/layout = ghost.
    Sensor existente check_capability_catalog_sync.py deve cobrir também components/*.tsx

GUIDE-5 (Computacional): offer_link obrigatório no template vars
  Arquivo: app/schemas/offer.py (OfferTemplateVarsResponse)
  Regra: offer_link: str — campo required (não Optional) no schema de resposta.
    Pydantic extra='forbid' + required forçam implementação.
```

### Sensores Novos (feedback — detectam regressão)

```
SENSOR-1 (Computacional): test_offer_template_vars_contract.py
  tests/contract/test_offer_template_vars.py
  assert "offer_link" in vars_dict
  assert "acceptance_url" in vars_dict
  assert vars_dict["offer_link"].startswith("http")
  Mensagem LLM: "offer_link ausente em render_offer_template_variables().
    Adicionar: draft.acceptance_url = f'{settings.PLATAFORMA_LIA_URL}/portal/proposta/{draft.candidate_token}'"

SENSOR-2 (Computacional): test_offer_portal_e2e.py
  tests/contract/test_offer_portal_public.py
  GET /portal/offers/{valid_token} → 200
  GET /portal/offers/{invalid_token} → 404
  POST /portal/offers/{token}/accept quando status=sent → 200
  POST /portal/offers/{token}/accept quando status!=sent → 409
  Resposta NUNCA contém: company_id, negotiation_notes, candidate_email_encrypted

SENSOR-3 (Computacional): test_offer_mark_sent_delivery.py
  tests/unit/test_offer_send_flow.py
  mock delivery.success=False → assert mark_sent NOT called
  mock delivery.success=True → assert mark_sent called exactly once
  Mensagem LLM: "mark_sent chamado sem confirmar delivery.success.
    Padrão correto: if delivery_result.success: await svc.mark_sent(...)"

SENSOR-4 (Computacional): CI grep sensor para URL mismatch
  .github/workflows/backend-ci.yml
  grep -rn "send_auto\|prepare_manual" src/ → exit 1 se encontrar underscore
  Mensagem LLM: "URL com underscore detectada. Padronizar para hyphen: send-auto, prepare-manual"

SENSOR-5 (Computacional): test_offer_multitenancy.py
  GET /portal/offers/{token_de_outro_tenant} → 404 (não vaza cross-tenant)
  POST com company_id no payload → 422 (Pydantic forbid)
  Mensagem LLM: "Cross-tenant leak em portal público. Token deve resolver company_id
    internamente — nunca aceitar company_id de params externos."
```

---

## 1. BANCO DE DADOS

### Migration 250 — `offer_proposals` campos novos

```sql
-- Fase 1: token + acceptance_url + tracking candidato
ALTER TABLE offer_proposals
  ADD COLUMN candidate_token UUID UNIQUE,
  ADD COLUMN acceptance_url VARCHAR(512),
  ADD COLUMN candidate_viewed_at TIMESTAMP,
  ADD COLUMN candidate_response_notes TEXT,
  ADD COLUMN negotiation_context_notes TEXT,  -- INTERNO, nunca exposto ao candidato
  ADD COLUMN offer_link_sent_at TIMESTAMP;

CREATE UNIQUE INDEX ix_offer_proposals_candidate_token
  ON offer_proposals(candidate_token)
  WHERE candidate_token IS NOT NULL;
```

### Migration 251 — `offer_negotiation_events` (nova tabela)

```sql
CREATE TABLE offer_negotiation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_id UUID NOT NULL REFERENCES offer_proposals(id) ON DELETE CASCADE,
    company_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    round_number INTEGER NOT NULL DEFAULT 0,
    actor VARCHAR(32) NOT NULL,      -- 'candidate' | 'recruiter' | 'lia' | 'manager'
    salary_proposed NUMERIC(12,2),
    salary_counter NUMERIC(12,2),
    benefits_snapshot JSONB DEFAULT '{}',
    notes TEXT,
    fairness_snapshot JSONB DEFAULT '{}',  -- obrigatório — FairnessGuard checkpoint
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_offer_neg_event_type CHECK (
        event_type IN (
            'sent','viewed','accepted','declined','counter_proposed',
            'concierge_touchpoint','negotiation_round','approved_by_manager',
            'expired','cancelled'
        )
    ),
    CONSTRAINT chk_offer_neg_actor CHECK (
        actor IN ('candidate','recruiter','lia','manager')
    )
);
CREATE INDEX ix_offer_neg_events_offer_id ON offer_negotiation_events(offer_id);
CREATE INDEX ix_offer_neg_events_company ON offer_negotiation_events(company_id, created_at DESC);
```

### Migration 252 — `company_hiring_policies.offer_rules` (novo bloco JSON)

```sql
ALTER TABLE company_hiring_policies
  ADD COLUMN offer_rules JSONB NOT NULL DEFAULT '{
    "allowed_start_day_of_month": [1, 15],
    "onboarding_blackout_periods": [],
    "min_notice_days": 30,
    "negotiation_enabled": false,
    "salary_flex_pct_max": 0,
    "benefits_flex_items": [],
    "negotiation_hitl_threshold_pct": 5,
    "counter_proposal_max_rounds": 2
  }';
```

**Constantes canônicas em Python:**
```python
# libs/models/lia_models/company_hiring_policy.py
OFFER_RULES_DEFAULTS = {
    "allowed_start_day_of_month": [1, 15],  # dias válidos para início
    "onboarding_blackout_periods": [],       # [{from, to, reason}]
    "min_notice_days": 30,                   # aviso prévio mínimo em dias
    "negotiation_enabled": False,            # master switch N3
    "salary_flex_pct_max": 0,               # % flex autônoma sem HITL
    "benefits_flex_items": [],               # ids de Benefits negociáveis
    "negotiation_hitl_threshold_pct": 5,     # acima de X% → HITL obrigatório
    "counter_proposal_max_rounds": 2,        # máx rodadas antes de escalar
}
```

---

## 2. BACKEND — `lia-agent-system`

### 2.1 Modelo atualizado — `OfferProposal`

```python
# libs/models/lia_models/offer_proposal.py — ADICIONAR (não remover nada)
candidate_token = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)
acceptance_url = Column(String(512), nullable=True)
candidate_viewed_at = Column(DateTime, nullable=True)
candidate_response_notes = Column(Text, nullable=True)
negotiation_context_notes = Column(Text, nullable=True)  # INTERNO
offer_link_sent_at = Column(DateTime, nullable=True)
```

### 2.2 Correções P0/P1 — `offer_service.py`

#### P0-1: gerar candidate_token + offer_link
```python
# Em create_or_get_draft, após gravar o draft:
import uuid as _uuid
from app.config import settings

if not draft.candidate_token:
    draft.candidate_token = _uuid.uuid4()
    draft.acceptance_url = (
        f"{settings.PLATAFORMA_LIA_URL}/portal/proposta/{draft.candidate_token}"
    )

# Em render_offer_template_variables — campos OBRIGATÓRIOS:
return {
    # ... campos existentes ...
    "offer_link": draft.acceptance_url or "",          # [P0-1 FIX]
    "candidate_token": str(draft.candidate_token) if draft.candidate_token else "",
}
```

#### P1-5: mark_sent gate
```python
# Em send_offer.py — NUNCA chamar mark_sent sem confirmar delivery:
delivery_result = await email_service.send(...)

if not delivery_result.success:
    logger.error("Offer email delivery failed", extra={
        "offer_id": str(offer_id), "error": delivery_result.error
    })
    raise HTTPException(503, detail={
        "error": "email_delivery_failed",
        "message": "Falha ao entregar email da proposta. Tente novamente.",
        "retry_suggested": True,
    })

await offer_service.mark_sent(offer_id, via="email")
```

### 2.3 Endpoints públicos — portal candidato

```python
# app/api/public/offer_portal.py
# NOTA: sem Depends(require_company_id) — empresa resolvida pelo token

router = APIRouter(prefix="/portal/offers", tags=["offer-portal-public"])

@router.get("/{token}", response_model=OfferPortalResponse)
async def get_offer_by_token(token: UUID, db: AsyncSession = Depends(get_public_db)):
    """Portal público — dados da proposta para o candidato."""
    offer = await OfferRepository(db).get_by_candidate_token(token)
    if not offer:
        raise HTTPException(404, "Proposta não encontrada ou expirada")

    # Track view (idempotente)
    if not offer.candidate_viewed_at:
        offer.candidate_viewed_at = datetime.utcnow()
        await OfferNegotiationEventRepository(db).create(
            offer_id=offer.id, company_id=offer.company_id,
            event_type="viewed", actor="candidate",
            round_number=offer.current_round or 0,
            fairness_snapshot={"check": "not_applicable_public_view"},
        )
        await db.commit()

    return OfferPortalResponse.from_offer(offer)
    # Retorna APENAS: cargo, empresa, salário, benefícios, datas, prazo, status
    # NUNCA: company_id, IDs internos, negotiation_context_notes

@router.post("/{token}/accept", response_model=OfferAcceptResponse)
async def accept_offer(
    token: UUID,
    payload: OfferAcceptRequest,
    request: Request,
    db: AsyncSession = Depends(get_public_db),
):
    offer = await _get_valid_offer_or_raise(token, db)
    svc = OfferService(db)
    await svc.candidate_accept(
        offer=offer,
        notes=payload.notes,
        ip_address=request.client.host,
    )
    await db.commit()
    return {"status": "accepted", "message": "Proposta aceita com sucesso!"}

@router.post("/{token}/decline", response_model=OfferDeclineResponse)
async def decline_offer(token: UUID, payload: OfferDeclineRequest, db: ...):
    offer = await _get_valid_offer_or_raise(token, db)
    svc = OfferService(db)
    await svc.candidate_decline(
        offer=offer, reason=payload.reason,
        counter_salary=payload.counter_salary,
    )
    await db.commit()
    return {"status": "declined"}
```

### 2.4 Novos métodos em `OfferService`

```python
async def candidate_accept(self, offer: OfferProposal, notes: str, ip_address: str):
    """State machine: sent → accepted. NUNCA aceita em outro status."""
    if offer.status != "sent":
        raise OfferStateError(f"Cannot accept offer in status '{offer.status}'")

    offer.status = "accepted"
    offer.accepted_at = datetime.utcnow()
    offer.candidate_response_notes = notes

    # Audit LGPD obrigatório
    await AuditService.log_decision(
        action="offer_accepted", offer_id=str(offer.id),
        company_id=offer.company_id, actor="candidate",
        reasoning=["Candidato aceitou proposta via portal público"],
        metadata={"ip": ip_address},
    )
    await self._trigger_e11(offer)
    await teams_service.on_offer_accepted(offer)
    await communication_service.notify_recruiter_offer_accepted(offer)

async def candidate_decline(self, offer, reason, counter_salary=None):
    """State machine: sent → declined. Opcionalmente inicia contra-proposta."""
    if offer.status != "sent":
        raise OfferStateError(f"Cannot decline offer in status '{offer.status}'")

    offer.status = "declined"
    offer.declined_at = datetime.utcnow()
    offer.decline_reason = reason

    await self._trigger_e12(offer)
    await teams_service.on_offer_declined(offer, reason)

    if counter_salary:
        await self._handle_counter_proposal(offer, counter_salary, reason)

async def compute_next_start_date(self, company_id: str, db: AsyncSession) -> date:
    """Calcula próxima data de início respeitando offer_rules da empresa."""
    policy = await HiringPolicyRepository(db).get_by_company_id(company_id)
    rules = (policy.offer_rules or {}) if policy else {}

    today = date.today()
    min_start = today + timedelta(days=rules.get("min_notice_days", 30))
    allowed_days = rules.get("allowed_start_day_of_month", [])
    blackouts = rules.get("onboarding_blackout_periods", [])

    if not allowed_days:
        return _next_working_day_after(min_start, blackouts)

    return _next_allowed_day(min_start, allowed_days, blackouts)
```

### 2.5 Endpoint Settings — Contratação

```python
# app/api/v1/settings/offer_rules.py
router = APIRouter(prefix="/settings/offer-rules", tags=["settings"])

@router.get("", response_model=OfferRulesResponse)
async def get_offer_rules(
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_tenant_db),
):
    policy = await HiringPolicyRepository(db).get_by_company_id(company_id)
    return (policy.offer_rules or {}) if policy else OFFER_RULES_DEFAULTS

@router.put("", response_model=OfferRulesResponse)
async def update_offer_rules(
    data: OfferRulesUpdate,   # WeDoBaseModel: extra='forbid', sem company_id
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_tenant_db),
):
    if data.allowed_start_day_of_month:
        for day in data.allowed_start_day_of_month:
            if not 1 <= day <= 31:
                raise HTTPException(422, f"Dia inválido: {day}. Use 1-31.")

    policy = await HiringPolicyRepository(db).get_by_company_id(company_id)
    policy.offer_rules = {**(policy.offer_rules or OFFER_RULES_DEFAULTS),
                          **data.model_dump(exclude_unset=True)}
    await db.commit()
    return policy.offer_rules
```

### 2.6 Repositório de eventos

```python
# app/domains/offer/repositories/offer_negotiation_event_repository.py
class OfferNegotiationEventRepository:
    def _require_company_id(self, company_id: str):
        if not company_id:
            raise ValueError("company_id obrigatório — ADR-001 multi-tenancy")

    async def create(self, offer_id, company_id, event_type, actor, **kwargs):
        self._require_company_id(company_id)
        event = OfferNegotiationEvent(
            offer_id=offer_id, company_id=company_id,
            event_type=event_type, actor=actor, **kwargs,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_by_offer(self, offer_id: UUID) -> list[OfferNegotiationEvent]:
        result = await self.db.execute(
            select(OfferNegotiationEvent)
            .where(OfferNegotiationEvent.offer_id == offer_id)
            .order_by(OfferNegotiationEvent.created_at)
        )
        return result.scalars().all()

    async def get_learning_data(self, company_id: str, limit=100) -> list[dict]:
        """Retorna agregados anonimizados para learning loop (N >= 10 gate ADR-LGPD-001)."""
        self._require_company_id(company_id)
        # Sem PII de candidatos individuais — apenas event_type, round, salários
        result = await self.db.execute(
            select(
                OfferNegotiationEvent.event_type,
                OfferNegotiationEvent.round_number,
                OfferNegotiationEvent.salary_proposed,
                OfferNegotiationEvent.salary_counter,
                OfferNegotiationEvent.created_at,
            )
            .where(OfferNegotiationEvent.company_id == company_id)
            .order_by(OfferNegotiationEvent.created_at.desc())
            .limit(limit)
        )
        return [row._asdict() for row in result]
```

---

## 3. CAMADA DE IA — Agente `offer_concierge`

### 3.1 Arquitetura canônica (3 heranças obrigatórias)

```
OfferConciergeAgent
├── TenantAwareAgentMixin       — multi-tenancy automático, company_id validado
├── EnhancedAgentMixin          — FairnessGuard, PII strip, AuditCallback, WorkingMemory, LearningExtractor
├── LangGraphReActBase          — ReAct loop, streaming, tool dispatch, checkpointing
├── @register_agent("offer_concierge")  — auto-aparece no Agent Studio
├── Domain: "offer"
├── HITL invariante: NUNCA muta status de proposta diretamente
│   Toda ação → HITLService.create_pending_action → aprovação recrutador → executa
└── Tools:
    ├── get_offer_status           — status + histórico de eventos
    ├── get_negotiation_context    — margens configuradas (NUNCA expor ao candidato)
    ├── suggest_next_start_date    — respeita offer_rules.allowed_start_day_of_month
    ├── draft_response_to_candidate — rascunho de comunicação (recrutador aprova antes de enviar)
    ├── escalate_to_recruiter      — HITL obrigatório para qualquer decisão
    ├── log_negotiation_event      — registra evento no offer_negotiation_events
    └── get_benefit_details        — lê Benefits.value_details (argumentário LIA)
```

### 3.2 Implementação canônica

```python
# app/domains/offer/agents/offer_concierge.py

from app.agents.base.tenant_aware_mixin import TenantAwareAgentMixin
from app.agents.base.enhanced_agent_mixin import EnhancedAgentMixin
from app.agents.langgraph_react_base import LangGraphReActBase
from app.agents.registry import register_agent
from app.shared.services.lia_agent_context_builder import build_company_agent_context

OFFER_CONCIERGE_PERSONA = """
Você é o concierge de propostas da {ai_name}. Sua função:
1. Manter recrutadores informados sobre status de propostas em tempo real
2. Sugerir próximas ações contextuais (data de início, benefícios relevantes, comunicação)
3. Preparar argumentário para negociação (baseado em Benefits.value_details configurados)
4. NUNCA revelar margens internas de negociação ao candidato
5. NUNCA tomar decisões sem aprovação HITL do recrutador
6. Toda ação sensível → escalar via escalate_to_recruiter → aguardar aprovação
"""

@register_agent("offer_concierge")
class OfferConciergeAgent(TenantAwareAgentMixin, EnhancedAgentMixin, LangGraphReActBase):
    """Concierge de propostas — N2 informacional (default) + N3 negociador (gateado)."""

    AGENT_NAME = "offer_concierge"
    DOMAIN = "offer"
    ALLOWED_TOOLS = [
        "get_offer_status", "get_negotiation_context", "suggest_next_start_date",
        "draft_response_to_candidate", "escalate_to_recruiter",
        "log_negotiation_event", "get_benefit_details", "get_compensation_policy",
    ]

    async def build_system_prompt(self, db, job_context=None) -> str:
        # Context canônico: carrega benefits, culture, lia_field_toggles filtrados
        company_ctx = await build_company_agent_context(
            company_id=self.company_id, db=db, job_context=job_context,
        )
        offer_rules = await self._load_offer_rules(db)
        negotiation_mode = (
            "Você PODE propor contra-ofertas dentro dos limites configurados, "
            "sempre com HITL para aprovação antes de enviar ao candidato."
            if offer_rules.get("negotiation_enabled", False)
            else
            "MODO INFORMACIONAL. Não negocie — apenas informe e escale via escalate_to_recruiter."
        )
        return f"{OFFER_CONCIERGE_PERSONA}\n\n{company_ctx}\n\n{negotiation_mode}"

    async def _pre_action_check(self, action: str, context: dict) -> None:
        """FairnessGuard obrigatório antes de qualquer ação que envolva candidato."""
        if "candidate" in context:
            await self._fairness_pre_check(
                action=action,
                candidate_context=context["candidate"],
                protected_fields=["salary", "benefits", "start_date"],
            )
```

### 3.3 Learning Loop (ADR-LGPD-001 compliant)

```python
# app/domains/offer/services/offer_learning_service.py

class OfferLearningService:
    MIN_SAMPLES = 10  # Gate LGPD Art. 12 §1 — igual ao BigFiveDepartmentService

    async def extract_patterns(self, company_id: str, db: AsyncSession) -> dict:
        """Padrões anonimizados de negociação per-tenant."""
        events = await OfferNegotiationEventRepository(db).get_learning_data(company_id)

        if len(events) < self.MIN_SAMPLES:
            return {"sufficient_data": False, "samples": len(events)}

        # Agregados sem PII individual
        accepted = [e for e in events if e["event_type"] == "accepted"]
        return {
            "sufficient_data": True,
            "acceptance_rate": len(accepted) / len(events),
            "avg_rounds_to_accept": ...,     # média de rodadas
            "salary_flex_p50": ...,          # mediana de flex salarial aceita
            "common_decline_reasons": [...], # categorias sem PII
        }
```

---

## 4. FRONTEND — `plataforma-lia`

### 4.1 Portal público do candidato

**Rota:** `src/app/[locale]/portal/proposta/[token]/page.tsx` (NOVA — sem dashboard layout)

```tsx
// Sem auth, responsivo mobile-first
// Layout próprio: OfferPortalLayout (sem sidebar/navbar do app)

export default function OfferPortalPage({ params }: { params: { token: string } }) {
  const { data: offer, error, isLoading } = usePublicOffer(params.token)

  if (isLoading) return <OfferPortalSkeleton />
  if (error || !offer) return <OfferNotFound />
  if (offer.status === "accepted") return <OfferAlreadyAccepted />
  if (["expired", "cancelled"].includes(offer.status)) return <OfferExpired status={offer.status} />

  return (
    <OfferPortalLayout companyLogo={offer.companyLogo} companyName={offer.companyName}>
      <OfferLetterDisplay
        candidateName={offer.candidateName}
        jobTitle={offer.jobTitle}
        salary={offer.salary}
        benefits={offer.benefits}
        startDate={offer.startDate}
        letterMarkdown={offer.letterMarkdown}
        responseDeadline={offer.responseDeadline}
      />
      <OfferStatusTimeline events={offer.events} />
      <OfferDecisionPanel
        token={params.token}
        allowCounterProposal={offer.counterProposalAllowed}
        onAccepted={() => router.replace("./aceito")}
        onDeclined={() => router.replace("./recusado")}
      />
    </OfferPortalLayout>
  )
}
```

**Sub-páginas:**
```
portal/proposta/[token]/aceito/page.tsx    — confirmação de aceite
portal/proposta/[token]/recusado/page.tsx  — confirmação + campo motivo
portal/proposta/[token]/expirado/page.tsx  — proposta expirada
```

**Proxy public routes (sem auth):**
```
src/app/api/public/offers/[token]/route.ts          — GET
src/app/api/public/offers/[token]/accept/route.ts   — POST
src/app/api/public/offers/[token]/decline/route.ts  — POST
```

**Design System:** usar tokens wedo-*, sem shadows, rounded-md, cores neutras.
Referência: `src/components/settings/_shared/` para primitivas de HubHeader/LoadingState.

### 4.2 Settings — Sub-aba "Contratação" em Minha Empresa

**Arquivo:** `src/components/settings/ContratacaoTab.tsx`

```tsx
export function ContratacaoTab() {
  const { data: rules, isLoading } = useQuery({
    queryKey: SETTINGS_QUERY_KEYS.offerRules(),
    queryFn: () => fetch("/api/backend-proxy/settings/offer-rules").then(r => r.json()),
    staleTime: 30_000,
  })
  const mutation = useMutation({
    mutationFn: (data) => fetch("/api/backend-proxy/settings/offer-rules", {
      method: "PUT", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(data),
    }).then(r => r.json()),
    onSuccess: () => {
      dispatchSettingsUpdate({ section: "minha-empresa", source: "ui" })
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEYS.offerRules() })
    },
  })

  if (isLoading) return <HubLoadingState />
  return (
    <div className="space-y-6">
      <HubHeader title="Contratação" description="Datas de início, aviso prévio e parâmetros de proposta" />

      {/* Datas de início */}
      <SettingsCard title="Datas de Início Permitidas">
        <p className="text-sm text-muted-foreground mb-4">
          Dias do mês em que novos colaboradores podem iniciar.
          A LIA sugere automaticamente a próxima data ao montar propostas.
        </p>
        <AllowedStartDaysPicker
          value={rules?.allowed_start_day_of_month ?? []}
          onChange={(days) => mutation.mutate({ allowed_start_day_of_month: days })}
        />
        {/* Chips 1–31, múltipla seleção. Ex: ●1 ○2 ... ●15 ○16 ... */}
      </SettingsCard>

      {/* Aviso prévio */}
      <SettingsCard title="Aviso Prévio Mínimo">
        <NumberInput label="Dias" value={rules?.min_notice_days ?? 30} min={0} max={90}
          onChange={(v) => mutation.mutate({ min_notice_days: v })} />
      </SettingsCard>

      {/* Períodos bloqueados */}
      <SettingsCard title="Períodos Bloqueados para Início">
        <BlackoutPeriodsList
          value={rules?.onboarding_blackout_periods ?? []}
          onChange={(periods) => mutation.mutate({ onboarding_blackout_periods: periods })}
        />
        {/* Ex: Recesso (20/12/2026 – 05/01/2027) */}
      </SettingsCard>

      {/* N3 — visível mas bloqueado até Fase 3 */}
      <SettingsCard title="Negociação Autônoma" badge="Em breve">
        <p className="text-sm text-muted-foreground">
          Permita que a LIA conduza rodadas de negociação salarial dentro dos limites configurados.
        </p>
        <div className="opacity-40 pointer-events-none mt-4">
          <Toggle label="Ativar negociação autônoma" disabled />
        </div>
      </SettingsCard>
    </div>
  )
}
```

**Wire em MinhaEmpresaHub:**
```tsx
// Adicionar ao array de tabs em MinhaEmpresaHub.tsx:
{ id: "contratacao", label: "Contratação", component: <ContratacaoTab /> }
```

**Query key canônica:**
```ts
// hooks/settings/useSettingsBroadcast.ts — adicionar:
offerRules: () => ["offer-rules"] as const,
```

### 4.3 Correções no `OfferReviewModal`

```tsx
// P1-2 fix: conectar OfferHITLBanner
import { OfferHITLBanner } from "./OfferHITLBanner"

// P0-1: exibir link copiável quando disponível
{offer.acceptanceUrl && (
  <OfferLinkCopyField url={offer.acceptanceUrl} />
)}

// Status tracker sincronizado com estado real
<OfferStatusTracker
  status={offer.status}
  sentAt={offer.sentAt}
  viewedAt={offer.candidateViewedAt}   // tracking view (novo)
  responseDeadline={offer.responseDeadline}
  respondedAt={offer.candidateRespondedAt}
/>

// Data de início: sugerida pelo backend
<StartDateField
  value={form.startDate}
  suggestedDate={offer.suggestedStartDate}  // compute_next_start_date
  onChange={(v) => form.setField("startDate", v)}
/>
```

### 4.4 Sincronização com painel "Decidir"

```tsx
// src/components/pages/job-kanban/DecidirPanel/OfferStatusBadge.tsx
// Polling mais frequente quando proposta está "sent" (aguardando candidato):
const { data } = useQuery({
  queryKey: ["offer-status", offerId],
  queryFn: () => offersApi.getStatus(offerId),
  staleTime: offer?.status === "sent" ? 30_000 : 300_000,
  refetchInterval: offer?.status === "sent" ? 60_000 : false,
})
// Badge contextual: [Enviada] [Visualizada ✓] [Aceita ✓] [Recusada ✗] [Pendente aprovação]
```

---

## 5. INTEGRAÇÃO TEAMS

### 5.1 Seis novos triggers em `TeamsProactivityEngine`

```python
# app/domains/communication/services/teams_service.py

async def on_offer_sent(self, offer: OfferProposal) -> None:
    """Proposta enviada ao candidato."""
    # Card com link para acompanhar + botão "Ver proposta"

async def on_offer_viewed(self, offer: OfferProposal) -> None:
    """Candidato abriu o portal pela primeira vez."""
    # Card: "📬 {nome} visualizou a proposta" + prazo de resposta

async def on_offer_accepted(self, offer: OfferProposal) -> None:
    """HITL: candidato aceitou — recrutador confirma contratação."""
    # Card com SubmitAction("Confirmar contratação") + OpenUrlAction("Ver detalhes")

async def on_offer_declined(self, offer: OfferProposal, reason: str) -> None:
    """Candidato recusou — contexto para próximo passo."""
    # Card com SubmitAction("Ver candidatos alternativos")

async def on_offer_escalation(self, pending: PendingAction) -> None:
    """HITL: LIA precisa de aprovação para prosseguir negociação."""
    # Card com SubmitAction("Aprovar") + SubmitAction("Recusar")

async def on_offer_deadline_approaching(self, offer: OfferProposal, hours_left: int) -> None:
    """Proativo: proposta prestes a expirar (notifica em 24h e 4h antes)."""
    # Card com SubmitAction("Prorrogar prazo")
```

### 5.2 Scheduler de lembretes

```python
# tasks/offer_deadline_scheduler.py
@periodic_task(run_every=timedelta(hours=1))
async def check_offer_deadlines():
    offers = await OfferRepository.get_expiring_soon(hours=24)
    for offer in offers:
        hours_left = int((offer.response_deadline - datetime.utcnow()).total_seconds() / 3600)
        if hours_left in [24, 4]:
            await teams_service.on_offer_deadline_approaching(offer, hours_left)
```

---

## 6. CROSS-CUTTING (obrigatório)

### Multi-tenancy
- `company_id` sempre do JWT via `Depends(require_company_id)` — nunca do payload nem `X-Company-ID` header
- Portal público: sem `company_id` no request — resolvido internamente via `offer.company_id` (token identifica a proposta + tenant)
- `OfferPortalResponse` serializado sem campos internos de tenant

### LGPD

| Dado | Tratamento |
|---|---|
| `candidate_email` | Encrypted at rest (EncryptedFieldMixin — já implementado) |
| `candidate_name` no portal | Visível ao próprio candidato (Art. 7 II) |
| `candidate_response_notes` | PII — apenas para recrutador autenticado |
| `ip_address` no aceite | Somente em AuditService log, não no modelo |
| `negotiation_context_notes` | INTERNO — nunca no OfferPortalResponse |
| `offer_negotiation_events` | Anonimizados no learning (N ≥ 10 gate, ADR-LGPD-001 Art. 12 §1) |
| LGPD snapshots | Imutáveis após status=sent (já implementado) |

### FairnessGuard
- `offer_concierge._pre_action_check()` invocado antes de qualquer ação com candidato
- Sensor: `tests/contract/test_offer_fairness_guard.py`

### Audit LGPD
```python
await AuditService.log_decision(
    action="offer_accepted",  # | offer_declined | offer_sent | etc.
    offer_id=str(offer.id), company_id=offer.company_id,
    actor="candidate",
    reasoning=["Candidato aceitou via portal público"],
    metadata={"ip": ip_address},
)
```

### HITL Invariante
- `offer_concierge` **nunca** muta status diretamente
- Toda ação → `HITLService.create_pending_action` → recrutador aprova → executa
- `negotiation_enabled=False` (default) = modo informacional puro

### ADR-001 Repository Pattern
- `OfferNegotiationEventRepository` com `_require_company_id` em todo método público
- Sem SQL inline em services — toda query via repositório

---

## 7. SENSORES TDD (Red antes de implementar)

### Backend
```
tests/contract/test_offer_template_vars.py          — offer_link obrigatório no dict
tests/contract/test_offer_portal_public.py          — endpoints públicos E2E
tests/unit/test_offer_send_flow.py                  — mark_sent gate
tests/contract/test_offer_multitenancy.py           — cross-tenant leak
tests/unit/test_offer_rules_start_date.py           — compute_next_start_date
tests/contract/test_offer_fairness_guard.py         — FairnessGuard chamado
tests/unit/test_offer_negotiation_event_repo.py     — _require_company_id
tests/contract/test_offer_state_machine.py          — accepted/declined em status errado → erro
```

### Frontend
```
src/components/settings/__tests__/ContratacaoTab.test.tsx    — render + mutation + i18n
src/app/portal/proposta/__tests__/OfferPortalPage.test.tsx   — estados: loading/not-found/expired/valid
src/components/offer-review-modal/__tests__/OfferReviewModal.test.tsx — P1-2 OfferHITLBanner conectado
```

### CI Guards
```yaml
# backend-ci.yml
- name: Check offer URL naming (hyphen only)
  run: |
    if grep -rn "send_auto\|prepare_manual" src/ --include="*.ts" --include="*.tsx"; then
      echo "❌ URL com underscore detectada. Use hyphen: send-auto, prepare-manual"
      exit 1
    fi
```

---

## 8. AGENT STUDIO

`offer_concierge` aparece **automaticamente** no Studio ao ser registrado via `@register_agent`:
- `LiveAgentsList` — monitora execuções ativas (polling 5s)
- `RecentExecutionsTable` — histórico de ações do agente
- `LgpdAuditPanel` — todas as ações auditadas
- `StudioComplianceView` — snapshot de compliance

Nenhuma mudança no Studio — arquitetura canônica resolve o wiring.

---

## 9. FASES DE IMPLEMENTAÇÃO

### FASE 1 — Fundação (estimativa: 3-4 dias)
> **Blocker absoluto: sem Fase 1, N2 e N3 são impossíveis**

| # | Entrega | Arquivo | Tipo | Prioridade |
|---|---|---|---|---|
| 1.1 | Migration 250: candidate_token + acceptance_url + campos | `alembic/versions/250_offer_token.py` | BE | Bloqueante |
| 1.2 | P0-1: gerar token no create_or_get_draft | `offer_service.py` | BE | Bloqueante |
| 1.3 | P0-1: offer_link em render_offer_template_variables | `offer_service.py` | BE | Bloqueante |
| 1.4 | Endpoints públicos /portal/offers/{token} | `app/api/public/offer_portal.py` | BE | Bloqueante |
| 1.5 | Página portal candidato | `portal/proposta/[token]/page.tsx` | FE | Bloqueante |
| 1.6 | P1-4: URL hyphen padronizado | `offers-api.ts` + proxy routes | FE | Alto |
| 1.7 | P1-5: mark_sent gate delivery.success | `send_offer.py` | BE | Alto |
| 1.8 | P1-2: OfferHITLBanner conectado | `OfferReviewModal.tsx` | FE | Alto |
| 1.9 | Link copiável no modal | `OfferReviewModal.tsx` | FE | Alto |
| 1.10 | Sensores TDD Fase 1 (8 testes) | `tests/contract/` | TEST | Bloqueante |

### FASE 2 — Concierge N2 (estimativa: 1-2 semanas)

| # | Entrega | Arquivo | Tipo |
|---|---|---|---|
| 2.1 | Migration 251: offer_negotiation_events | `alembic/versions/251_...py` | BE |
| 2.2 | Migration 252: offer_rules em company_hiring_policies | `alembic/versions/252_...py` | BE |
| 2.3 | OfferNegotiationEventRepository | `repositories/offer_negotiation_event_repository.py` | BE |
| 2.4 | Endpoint GET/PUT settings/offer-rules | `app/api/v1/settings/offer_rules.py` | BE |
| 2.5 | compute_next_start_date + helpers | `offer_service.py` | BE |
| 2.6 | ContratacaoTab + AllowedStartDaysPicker | `ContratacaoTab.tsx` | FE |
| 2.7 | Wire ContratacaoTab em MinhaEmpresaHub | `MinhaEmpresaHub.tsx` | FE |
| 2.8 | SETTINGS_QUERY_KEYS.offerRules() | `useSettingsBroadcast.ts` | FE |
| 2.9 | Proxy route settings/offer-rules | `api/backend-proxy/settings/offer-rules/route.ts` | FE |
| 2.10 | OfferStatusTracker + OfferLinkCopyField no modal | `OfferReviewModal.tsx` | FE |
| 2.11 | OfferStatusBadge + polling no painel Decidir | `OfferStatusBadge.tsx` | FE |
| 2.12 | Teams: 6 triggers novos | `teams_service.py` | BE |
| 2.13 | Scheduler deadline reminders | `tasks/offer_deadline_scheduler.py` | BE |
| 2.14 | offer_concierge agent (modo informacional) | `app/domains/offer/agents/offer_concierge.py` | AI |
| 2.15 | Tools: get_offer_status, suggest_next_start_date, escalate_to_recruiter | `tools/` | AI |
| 2.16 | Deprecation headers em Sistema B (job_offers) | `app/api/v1/job_offers.py` | BE |
| 2.17 | Sensores TDD Fase 2 (12 testes) | `tests/` | TEST |

### FASE 3 — Agente Negociador N3 (estimativa: 2-3 semanas)
> **Gateado em `negotiation_enabled=True`**

| # | Entrega | Tipo |
|---|---|---|
| 3.1 | UI Negociação Autônoma desbloqueada em ContratacaoTab | FE |
| 3.2 | OfferLearningService + padrões anonimizados (N ≥ 10) | BE |
| 3.3 | Tool draft_response_to_candidate | AI |
| 3.4 | Tool log_negotiation_event | AI |
| 3.5 | Multi-round negotiation state machine | BE |
| 3.6 | HITL gate negotiation_hitl_threshold_pct | BE |
| 3.7 | Teams card HITL para aprovação de rodada | BE |
| 3.8 | Benefits argumentário injetado em system prompt | AI |
| 3.9 | OfferConciergeAgent modo negociador | AI |
| 3.10 | Sistema B aposentadoria completa | BE |
| 3.11 | Sensores TDD Fase 3 (15 testes) | TEST |

---

## 10. DECISÕES PENDENTES — Paulo decide

| ID | Questão | Impacto |
|---|---|---|
| **D1** | Fase 1 imediata (só P0/P1, ~2 dias) ou Fase 1+2 em sprint único? | Escopo do sprint |
| **D2** | Aceite digital: portal simples (gratuito) ou Clicksign (~R$5-15/envelope)? | Feature do portal de aceite |
| **D3** | WhatsApp para envio da proposta: Fase 2 ou Fase 3? | Tools de envio multi-canal |
| **D4** | Sistema B sunset: deprecar na Fase 2 ou manter em paralelo? | Data de desligamento de /job-offers |
| **D5** | N3 Negociador: meta Q3 ou Q4 2026? | Calendário de sprints |

---

## HARNESS ENGINEERING — Resumo de Entregáveis

```
─────────────────────────────────────────────────
GUIDES propostos (feedforward computacional):
  - offer_service.py: candidate_token gerado em create_or_get_draft (sempre)
  - offer_service.py: render_offer_template_variables retorna offer_link (required field)
  - send_offer.py: mark_sent gateado em delivery_result.success=True
  - OfferRulesUpdate schema: WeDoBaseModel (extra='forbid', sem company_id)
  - CLAUDE.md: seção "Offer Domain" com 3 regras canônicas

SENSORS propostos (feedback computacional):
  - tests/contract/test_offer_template_vars.py — offer_link obrigatório
  - tests/contract/test_offer_portal_public.py — E2E público
  - tests/unit/test_offer_send_flow.py — mark_sent gate
  - tests/contract/test_offer_multitenancy.py — cross-tenant
  - CI grep: underscore em URLs de oferta → exit 1

DÉBITO TÉCNICO DE HARNESS registrado:
  - Propagar para CLAUDE.md: "Offer Domain — 3 regras canônicas"
    (offer_link required, mark_sent gate, portal E2E antes de marcar como ready)
  - check_capability_catalog_sync.py: estender para cobrir components/*.tsx (ghost components)
  - OfferPortalResponse: schema Pydantic com campos públicos explicitamente listados
    (proteção estrutural contra leak de dados internos)
─────────────────────────────────────────────────
```
