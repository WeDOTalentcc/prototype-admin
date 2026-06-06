"""
Canonical wizard session thread_id derivation (Task #1080).

Single source of truth that maps ``(company_id, session_id)`` to a stable
LangGraph checkpoint thread_id. ALL transports (WS, SSE, REST orchestrator)
import from here — there is no other valid place to compute the wizard
thread_id in the codebase.

Design contract (canonical-fix):
  - Pure function of ``(company_id, session_id)``. No I/O, no Redis, no
    ``msg["thread_id"]`` honor, no heuristic fallback list.
  - Two companies that share a ``session_id`` MUST produce different
    thread_ids (multi-tenant isolation invariant).
  - Same ``(company_id, session_id)`` pair MUST always produce the same
    thread_id, across processes and restarts (LangGraph checkpointer key
    stability — required for resuming a wizard after page reload).
  - Missing/unparseable ``company_id`` falls back to a stable ``"anon"``
    token. Strict tenant mode at the call-site is responsible for refusing
    to pin against an anonymous thread.

Why this replaces the legacy 4-priority logic in WizardSessionService:
  The previous design had 5 concurrent sources of truth for "this
  conversation belongs to the wizard" (msg.thread_id custom + Redis marker
  ``lia:wizard:active:*`` + checkpointer + Tier 0.5 router pin + heuristic
  ``wiz-{token}-{sid}`` candidates). Every page reload mid-wizard lost the
  custom thread_id, the Redis marker eventually expired (TTL 2h), and the
  router's Tier 0.5 was the wrong layer (transport-specific concern in a
  domain-agnostic router). Collapsing to one deterministic function +
  checkpointer-only "is active" check eliminates the entire class of
  resume bugs B2/B3/B4 (originally observed under Task #1051's design) and
  the pw-cenario-D2 reload bug. Canonical refactor: Task #1080.
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import re
import unicodedata
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

_WIZ_PREFIX = "wiz"
_ANON_TOKEN = "anon"
# 16 hex chars = 64 bits of entropy from SHA-256(normalized_company_id).
# Replaces the previous "first 8 chars of company_id" scheme which was only
# 32 bits for UUIDs and prone to prefix collisions for slug-based ids.
# Birthday-bound: ~2^32 distinct tenants before 50% collision risk.
_COMPANY_TOKEN_LEN = 16


# Staleness do wizard (fix 2026-05-31): um wizard ABANDONADO (usuário saiu
# no meio) deixa o checkpoint não-terminal. Sem expiração ele sequestra
# mensagens não-relacionadas ("oi") em logins futuros. Restaura o TTL que
# antes vivia num marker Redis (2h), removido na migração p/ checkpoint
# direto. Configurável via env. 0 = desliga o gate (comportamento legado).
_WIZARD_SESSION_TTL_HOURS = float(os.environ.get("LIA_WIZARD_SESSION_TTL_HOURS", "2"))


def _company_token(company_id: str) -> str:
    """Stable 16-hex-char token of normalized ``company_id`` (SHA-256 prefix)."""
    digest = hashlib.sha256(company_id.encode("utf-8")).hexdigest()
    return digest[:_COMPANY_TOKEN_LEN]


def derive_thread_id(company_id: str | None, session_id: str) -> str:
    """Deterministic wizard thread_id for ``(company_id, session_id)``.

    Format: ``wiz-{company_token}-{session_id}`` where ``company_token``
    is a 16-char SHA-256 hex prefix of ``CompanyId.parse(company_id).as_str()``
    or the literal ``"anon"`` when ``company_id`` is missing/unparseable.

    Why hash and not the raw id prefix: a raw 8-char UUID prefix only carried
    32 bits of entropy and slug ids could collide on shared prefixes
    (e.g. ``"acme-br"`` / ``"acme-us"``). SHA-256 truncated to 64 bits gives
    cross-tenant isolation that is collision-safe for any realistic tenant
    count (~2^32 distinct tenants before 50% birthday risk).

    Raises:
        ValueError: when ``session_id`` is empty — wizard sessions always
            require a session id; no silent default.
    """
    if not session_id:
        raise ValueError("derive_thread_id requires a non-empty session_id")

    company_token = _ANON_TOKEN
    if company_id:
        try:
            from app.shared.value_objects.company_id import CompanyId

            normalized = CompanyId.parse(company_id).as_str()
            if normalized:
                company_token = _company_token(normalized)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning(
                "[derive_thread_id] company_id=%r unparseable (%s) — "
                "falling back to '%s' token. Strict tenant mode should "
                "prevent this branch in production.",
                company_id,
                type(exc).__name__,
                _ANON_TOKEN,
            )

    return f"{_WIZ_PREFIX}-{company_token}-{session_id}"


async def is_wizard_session_active(
    company_id: str | None, session_id: str
) -> bool:
    """Return True iff the LangGraph checkpoint for this session is OPEN.

    "Open" means: a checkpoint exists AND ``current_stage != "completed"``.
    A finished wizard MUST allow follow-up messages to be routed elsewhere.

    Reads the canonical checkpoint directly via JobCreationGraph's compiled
    graph — single thread_id derived from ``(company_id, session_id)``.
    No Redis marker, no candidate fallbacks.

    Fail-open: any exception (checkpointer outage, graph not initialized)
    returns False so chat routing never blocks on infra failures.
    """
    if not session_id:
        return False
    try:
        thread_id = derive_thread_id(company_id, session_id)
    except ValueError:
        return False

    try:
        from app.domains.job_creation.graph import get_job_creation_graph

        wiz_g = get_job_creation_graph()
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await asyncio.to_thread(wiz_g._graph.get_state, config)
    except Exception as exc:  # pragma: no cover — fail-open
        logger.debug(
            "[is_wizard_session_active] checkpointer read failed for "
            "thread=%s (%s) — treating as inactive.",
            thread_id,
            type(exc).__name__,
        )
        return False

    if snapshot is None:
        return False

    # Staleness gate — wizard abandonado não deve sequestrar mensagens
    # futuras. Usa o created_at do próprio checkpoint (sem infra extra).
    if _WIZARD_SESSION_TTL_HOURS > 0:
        try:
            _created = getattr(snapshot, "created_at", None)
            if _created:
                _ts = datetime.fromisoformat(str(_created).replace("Z", "+00:00"))
                if _ts.tzinfo is None:
                    _ts = _ts.replace(tzinfo=timezone.utc)
                _age_h = (datetime.now(timezone.utc) - _ts).total_seconds() / 3600.0
                if _age_h > _WIZARD_SESSION_TTL_HOURS:
                    logger.info(
                        "[is_wizard_session_active] checkpoint stale (%.1fh > %.1fh) "
                        "thread=%s — inativo (wizard abandonado, não sequestra chat).",
                        _age_h, _WIZARD_SESSION_TTL_HOURS, thread_id,
                    )
                    return False
        except Exception as _stale_exc:  # noqa: BLE001 — fail-open
            logger.debug(
                "[is_wizard_session_active] staleness parse falhou (%s) — ignorando",
                _stale_exc,
            )

    # Task #1094 — sessão pausada em ``langgraph.types.interrupt()`` conta
    # como ATIVA mesmo que o values esteja vazio (raro: ocorreria se um
    # interrupt fosse o primeiro step, antes de qualquer state.update).
    # Em prática os gates wizard são alcançados após intake/jd_enrichment
    # já terem populado state, mas a checagem é defensiva e barata.
    has_pending_interrupt = any(
        getattr(t, "interrupts", None) for t in (snapshot.tasks or [])
    )
    if has_pending_interrupt:
        return True

    if not snapshot.values:
        return False
    values = snapshot.values
    stage = (values.get("current_stage") or "").lower()
    if stage == "completed":
        return False
    # Active iff there is conversational state OR a non-terminal stage.
    return bool(values.get("conversation_messages") or stage)


# Gate de INTENÇÃO de entrada no wizard (fix 2026-05-31): uma SAUDAÇÃO pura
# ("oi", "bom dia") NUNCA deve reentrar/retomar um wizard ativo — só pedidos
# relacionados a vaga ou continuações ("sim", "muda a pergunta 3"). Pega só
# saudações/smalltalk PUROS (ancorado em $), então mensagens com conteúdo
# ("oi, quero criar uma vaga") passam normalmente. Computacional, sem LLM:
# risco ZERO de misroutear continuações curtas (que não são saudações).
_GREETING_RE = re.compile(
    r"^(oi+|ol[áa]+|opa+|e\s?a[íi]|hey+|hello+|hi+|salve|al[ôo]+|oie+|"
    r"bom dia|boa tarde|boa noite|tudo bem|tudo certo|tudo bom|tudo joia|"
    r"como vai|como voc[êe] est[áa]|beleza|blz|fala|fala a[íi]|menu|start|começar)"
    r"[\s,.!?]*$",
    re.IGNORECASE,
)


def is_greeting_only(message: str | None) -> bool:
    """True se a mensagem é uma saudação/smalltalk PURA (sem conteúdo extra).

    Usado pelo gate de entrada do wizard: saudação não resume wizard.
    Mensagens longas (>30 chars) ou com conteúdo além da saudação retornam False.
    """
    if not message:
        return False
    text = message.strip()
    if len(text) > 30:
        return False
    # remove emojis / símbolos de borda antes de casar
    text = "".join(
        ch for ch in text if not unicodedata.category(ch).startswith(("So", "Sk"))
    ).strip().lower()
    if not text:
        return False
    return bool(_GREETING_RE.match(text))


# Tags de ação estruturadas do FE para superfícies NÃO-wizard (Configurações /
# dados da empresa). São sinais determinísticos do chat de Configurações — não
# podem ser sequestrados por um wizard de vaga ativo/recente. Espelha o
# short-circuit de `[action:...]` já honrado pelo fast_router.
_NON_WIZARD_ACTION_TAGS = (
    "[action:prefill_section]",
    "[action:configure_",
    "[action:analyze_website]",
    "[action:process_document]",
)


def _is_non_wizard_action(message: str | None) -> bool:
    """True se a mensagem começa com uma tag de ação de Configurações."""
    if not message:
        return False
    head = message.lstrip().lower()
    return any(head.startswith(tag) for tag in _NON_WIZARD_ACTION_TAGS)


# Release do pin por intenção de QUERY/navegação (fix 2026-06-06): um wizard
# abandonado (checkpoint não-completed dentro do TTL) sequestrava pedidos de
# LEITURA de dados existentes -- "liste os candidatos da vaga", "abrir a vaga X",
# "rankeie os melhores", "me leve pro funil", "ver kanban" (transcript Paulo).
# O usuário não escapava. Espelha a intenção do CR-3 (navigation_intent); local
# aqui porque o pin vive na camada shared (importar orchestrator = layering
# violation). Conservador: exige verbo de consulta + alvo de dado, OU
# pipeline/funil/kanban standalone (palavras que não aparecem em criação de
# vaga) -- então continuações do wizard (descrições, "sim", "muda a pergunta 3",
# "liste as perguntas de triagem") NÃO casam.
_NON_WIZARD_QUERY_RE = re.compile(
    r"\b(?:pipeline|funil|kanban)\b"
    r"|\b(?:list\w*|ranke\w*|ranque\w*|busc\w*|compar\w*|abr\w*|mostr\w*|"
    r"ve(?:ja|r)\b|resum\w*|quais|quant\w*|leve|leva)\b"
    r"[^.?!\n]{0,40}?\b"
    r"(?:candidat\w*|vagas?|pipeline|funil|kanban|ranking|talento\w*|perfil)\b",
    re.IGNORECASE,
)


def _is_non_wizard_query(message: str | None) -> bool:
    """True se a msg pede LEITURA/navegação de dados existentes (não é
    continuação do wizard de criação). Libera o pin pro agente de domínio."""
    if not message:
        return False
    return bool(_NON_WIZARD_QUERY_RE.search(message))


async def should_pin_to_wizard(
    company_id: str | None,
    session_id: str,
    message: str | None,
    *,
    domain_hint: str | None = None,
) -> bool:
    """Decide se a mensagem deve ser roteada/pinada ao wizard.

    Canônico (fix 2026-05-31): combina (a) sessão wizard ATIVA e não-stale
    (is_wizard_session_active, com TTL) + (b) gate de INTENÇÃO — uma saudação
    pura não resume o wizard mesmo que ativo. Greeting check vem primeiro
    (barato) para evitar o get_state quando a msg é só "oi".

    Fix 2026-06-01: intenção explícita do FE para um domínio NÃO-wizard vence
    o pin implícito (mesma regra já aplicada ao `domain` hard no transport).
    Sem isso, após abrir um wizard de vaga, o chat de Configurações ficava
    sequestrado por até 2h (TTL) e os saves de empresa via chat nunca
    chegavam ao agente `company_settings`. Cobre dois sinais:
      (a) `domain_hint` (metadata do FE, ex.: "company_settings");
      (b) tag de ação estruturada na mensagem (turno 1 do deeplink).
    """
    if is_greeting_only(message):
        return False
    if domain_hint and domain_hint != "wizard":
        return False
    if _is_non_wizard_action(message):
        return False
    if _is_non_wizard_query(message):
        return False
    return await is_wizard_session_active(company_id, session_id)

