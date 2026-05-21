"""Wizard Gate Service — contrato canônico único para resume de gates HITL do wizard.

Task #1084 (T1): consolida o seam de aprovação humana do wizard de criação de vaga.

**Por que existe:**
Hoje o wizard tem dois pontos de entrada de "approval":
  - frame WS ``approval_response`` (botão clicado pelo recrutador no FE);
  - eventualmente, o classifier LLM-based de chat livre (Task #1085 / T2).

Sem um contrato comum, esses dois caminhos divergem em (a) mutação de state,
(b) audit row emitido (SOX/EU AI Act) e (c) re-entrada no graph LangGraph,
abrindo race conditions e violando a Inegociável "uma fonte de verdade por
conceito" da skill ``canonical-fix``.

``WizardGateService.resume_gate`` é o único entry point legítimo para resumir
um gate do wizard a partir de qualquer transport (WS hoje, REST/SSE no futuro).

**Contrato:**

::

    result = await wizard_gate_service.resume_gate(
        thread_id=...,        # LangGraph thread_id (= wiz-<token8>-<session>)
        pending_id=...,       # UUID4 emitido pelo hitl_service.request_approval
        decision="approved" | "rejected",
        comment=...,
        ws_session_id=...,    # WS session usado para enviar o frame de resposta
        company_id=...,
        user_id=...,
        gate_id=None,         # opcional; se ausente é derivado de (thread_id, pending_id)
    )

Retorna ``{"status": ..., "message": ..., "gate_id": ..., "cached": bool}``.

**Idempotência (CAS via Redis, fallback in-memory):**
Cada gate tem um ``gate_id`` determinístico ``"gate:{thread_id}:{pending_id}"``.
A primeira chamada para um ``gate_id`` executa o resume real e emite **1**
audit row em ``audit_logs`` (decision_type=``wizard_step_completed``). Chamadas
subsequentes para o mesmo ``gate_id`` retornam o resultado cacheado e NÃO
emitem novo audit row — o que protege contra duplo-clique no botão e contra
o usuário aprovar via chat depois de já ter aprovado via botão (e vice-versa).

**Engine de resume (Task #1085 / T2):**
``_resume_engine`` agora delega para ``JobCreationGraph.aresume_with_message``
— o grafo canônico do wizard, baseado em ``langgraph.types.interrupt()``.
Quando o checkpoint está pausado em um ``interrupt()`` (HITL gate canônico:
intake / jd_enrichment / wsi / review), o resume injeta a decisão do
aprovador via ``Command(resume=<msg>)`` e o nó pausado retoma exatamente
no ponto da pergunta com a resposta como input estruturado, eliminando o
loop "wizard repete a mesma pergunta 4× ignorando o que o recrutador
respondeu" originalmente causado pelo path legacy ``JobWizardGraph.ainvoke(None)``.
O contrato público ``resume_gate(...)`` permanece inalterado — apenas o
engine interno trocou.

Constraints arquiteturais herdadas:
  - NÃO mexer no MRO ``TenantAwareAgentMixin → LangGraphReActBase → EnhancedAgentMixin``.
  - NÃO mexer em ``_heal_legacy_demo_company_id``.
  - Sentinelas T-D / no-regression continuam verdes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# TTL do CAS — alinhado com o TTL do hitl_service (24h). Após isso o gate_id
# expira do cache; nova chamada com o mesmo gate_id volta a ser tratada como
# primeira (raríssimo na prática, exige usuário reaproveitar pending_id após 24h).
_GATE_CAS_TTL_SECONDS = 86400

# Lease em segundos para o marker "in_progress" — janela máxima durante a qual
# uma chamada concorrente verá outro worker executando o engine. Após isso o
# Redis solta a key e a próxima chamada vira a "primeira" (defesa contra worker
# crashado mid-execution).
_GATE_INPROGRESS_LEASE_SECONDS = 300

# Polling para chamadas concorrentes que perderam a corrida do CAS — esperam
# o vencedor publicar o resultado final.
_GATE_POLL_INTERVAL_SECONDS = 0.05
_GATE_POLL_MAX_WAIT_SECONDS = 95.0  # > _AGENT_TIMEOUT default (90s)

# Marker namespace para Redis. Separado do namespace ``hitl:*`` para evitar
# colisão com chaves do hitl_service.
_GATE_CAS_KEY_PREFIX = "wizard:gate:resolved:"
_GATE_INPROGRESS_PREFIX = "in_progress:"

# ---------------------------------------------------------------------------
# Lua scripts para finalize/release token-aware (CAS atômico end-to-end)
# ---------------------------------------------------------------------------
# Sem Lua, há race entre worker A (lease expirado, ainda rodando) sobrescrevendo
# o resultado já publicado por worker B (que adquiriu o novo lease). Com Lua,
# finalize/release só aplicam se o valor atual da key for o token esperado.
#
# KEYS[1] = key do gate
# ARGV[1] = token esperado (in_progress:<uuid>)
# ARGV[2] = novo valor (json final)            [só finalize]
# ARGV[3] = TTL do novo valor em segundos      [só finalize]
#
# Retorno: 1 = sucesso (token bateu); 0 = no-op (token mudou ou key não existe)
_LUA_FINALIZE_IF_OWNED = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    redis.call("SET", KEYS[1], ARGV[2], "EX", ARGV[3])
    return 1
end
return 0
"""

_LUA_DELETE_IF_OWNED = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    redis.call("DEL", KEYS[1])
    return 1
end
return 0
"""


def _get_redis():
    """Cliente Redis ou None — mesmo padrão de ``hitl_service._get_redis``.

    Mantido inline (não importado do hitl_service) para não criar acoplamento
    cíclico e para permitir que esta service seja testada offline.
    """
    try:
        import redis as redis_lib  # type: ignore
        redis_url = os.environ.get("REDIS_URL")
        if not redis_url:
            return None
        client = redis_lib.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        return client
    except Exception as exc:  # pragma: no cover — fail-open path
        logger.debug("[WizardGateService] Redis indisponível: %s", exc)
        return None


class WizardGateService:
    """Serviço canônico de resume de gates HITL do wizard. Singleton process-wide."""

    def __init__(self) -> None:
        # Fallback in-memory CAS (dev / Redis-down). Process-local: NÃO compartilhado
        # entre workers — em prod, Redis é a verdade. Aqui é defesa extra.
        self._memory_cas: dict[str, dict[str, Any]] = {}
        # Locks por gate_id para serializar chamadas concorrentes intra-processo
        # quando o Redis está indisponível. Lazy: só criados quando o gate é tocado.
        self._memory_locks: dict[str, asyncio.Lock] = {}
        self._memory_locks_guard = asyncio.Lock()

    # ------------------------------------------------------------------
    # Helpers públicos
    # ------------------------------------------------------------------

    @staticmethod
    def derive_gate_id(thread_id: str, pending_id: str) -> str:
        """Derivação determinística de ``gate_id``.

        Usar ``pending_id`` direto não basta porque dois threads diferentes
        poderiam (em teoria) reusar o mesmo UUID se o cliente enviar lixo.
        Concatenar com ``thread_id`` blinda contra colisão e mantém a chave
        estável para CAS.
        """
        if not pending_id:
            return ""
        return f"gate:{thread_id}:{pending_id}"

    # ------------------------------------------------------------------
    # CAS atômico (idempotência sob concorrência real)
    # ------------------------------------------------------------------
    #
    # Protocolo:
    #   1. ``_cas_acquire(gate_id)`` tenta ``SET key "in_progress:<token>" NX EX
    #      <lease>`` no Redis. Vencedor recebe o ``token`` (string); perdedores
    #      recebem ``None`` E precisam aguardar o vencedor publicar o resultado
    #      final via ``_cas_wait_for_final``.
    #   2. Se Redis indisponível, ``_memory_locks[gate_id]`` (asyncio.Lock)
    #      serializa intra-processo. Após adquirir, checa ``_memory_cas``;
    #      se vazio, é o vencedor; senão é cache hit.
    #   3. ``_cas_finalize(gate_id, payload)`` sobrescreve o marker com o
    #      payload final via ``SETEX`` (TTL 24h).
    #   4. ``_cas_release_failed(gate_id)`` derruba o marker em caso de
    #      timeout/erro do engine — assim o usuário pode tentar de novo
    #      sem ficar preso ao lease de 5 min.
    #   5. ``_cas_peek(gate_id)`` lê estado SEM tentar adquirir — usado por
    #      perdedores para diferenciar "in_progress" vs "final".
    #
    # ``_cas_acquire`` retorna uma das três tags:
    #   ``("won", token)``    → este caller deve executar engine + audit
    #   ``("cached", payload)`` → outro caller já finalizou; payload é o final
    #   ``("wait", None)``    → outro caller está executando; aguardar peek
    #

    async def _get_memory_lock(self, gate_id: str) -> asyncio.Lock:
        async with self._memory_locks_guard:
            lock = self._memory_locks.get(gate_id)
            if lock is None:
                lock = asyncio.Lock()
                self._memory_locks[gate_id] = lock
            return lock

    def _cas_peek(self, gate_id: str) -> tuple[str, dict[str, Any] | None]:
        """Lê o estado atual de um gate sem mutar.

        Returns:
            ``("absent", None)``      → key não existe
            ``("in_progress", None)`` → outro worker executando
            ``("final", payload)``    → resultado já publicado
        """
        if not gate_id:
            return ("absent", None)
        key = f"{_GATE_CAS_KEY_PREFIX}{gate_id}"
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                raw = redis_client.get(key)
                if raw is None:
                    return ("absent", None)
                data = raw.decode() if isinstance(raw, bytes) else raw
                if isinstance(data, str) and data.startswith(_GATE_INPROGRESS_PREFIX):
                    return ("in_progress", None)
                try:
                    return ("final", json.loads(data))
                except (json.JSONDecodeError, TypeError):
                    return ("absent", None)
        except Exception as exc:
            logger.debug("[WizardGateService] CAS peek Redis falhou: %s", exc)
        # Fallback in-memory: só guarda final, nunca in_progress
        memo = self._memory_cas.get(key)
        return ("final", memo) if memo is not None else ("absent", None)

    def _cas_acquire(self, gate_id: str) -> tuple[str, str | dict[str, Any] | None]:
        """Tenta adquirir o lease de execução para um gate via SET NX EX atômico.

        Returns:
            ``("won", token)``     → executar engine; passar token para finalize
            ``("cached", payload)`` → final já publicado; retornar
            ``("wait", None)``     → outro worker rodando; aguardar peek
        """
        if not gate_id:
            return ("won", "")
        key = f"{_GATE_CAS_KEY_PREFIX}{gate_id}"
        token = f"{_GATE_INPROGRESS_PREFIX}{uuid.uuid4().hex}"
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                acquired = redis_client.set(
                    key, token, nx=True, ex=_GATE_INPROGRESS_LEASE_SECONDS
                )
                if acquired:
                    return ("won", token)
                # Não adquiriu: ler o estado atual para diferenciar in_progress vs final
                state, payload = self._cas_peek(gate_id)
                if state == "final":
                    return ("cached", payload)
                if state == "in_progress":
                    return ("wait", None)
                # Race: key sumiu entre o NX e o peek (TTL/del). Tentar de novo.
                acquired2 = redis_client.set(
                    key, token, nx=True, ex=_GATE_INPROGRESS_LEASE_SECONDS
                )
                return ("won", token) if acquired2 else ("wait", None)
        except Exception as exc:
            logger.debug("[WizardGateService] CAS acquire Redis falhou: %s", exc)
        # Fallback: caller serializa via _memory_lock no resume_gate; aqui apenas
        # checa se já há final. Se houver, devolve cached.
        memo = self._memory_cas.get(key)
        if memo is not None:
            return ("cached", memo)
        return ("won", token)

    def _cas_finalize(self, gate_id: str, payload: dict[str, Any], token: str = "") -> bool:
        """Publica o resultado final, **só se ainda formos donos do lease**.

        Args:
            gate_id: chave canônica.
            payload: resultado final a publicar.
            token: token retornado por ``_cas_acquire`` quando este worker venceu.
                Vazio significa "não houve token" (in-memory fallback OU rejeição
                sem acquire prévio — caminhos legacy/test). Sem token, escreve
                incondicionalmente para preservar compat (o Lua só roda quando
                temos token + Redis up).

        Returns:
            ``True`` se o write foi aplicado, ``False`` se outro worker já
            sobrescreveu (lease expirado mid-execution; resultado descartado).
        """
        if not gate_id:
            return False
        key = f"{_GATE_CAS_KEY_PREFIX}{gate_id}"
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                if token:
                    # Token-aware: só escreve se valor atual == token (CAS real).
                    res = redis_client.eval(
                        _LUA_FINALIZE_IF_OWNED,
                        1,
                        key,
                        token,
                        json.dumps(payload),
                        str(_GATE_CAS_TTL_SECONDS),
                    )
                    if int(res or 0) == 1:
                        return True
                    logger.warning(
                        "[WizardGateService] finalize no-op gate=%s — lease expirou",
                        gate_id,
                    )
                    return False
                redis_client.setex(key, _GATE_CAS_TTL_SECONDS, json.dumps(payload))
                return True
        except Exception as exc:
            logger.debug("[WizardGateService] CAS finalize Redis falhou: %s", exc)
        self._memory_cas[key] = payload
        return True

    def _cas_release_failed(self, gate_id: str, token: str = "") -> bool:
        """Libera o lease em caso de timeout/erro, **só se ainda formos donos**.

        Sem token (legacy/in-memory), faz delete incondicional. Com token,
        usa Lua para garantir que NÃO vamos derrubar o lease de outro worker
        que já reentrou no gate após nosso lease expirar.
        """
        if not gate_id:
            return False
        key = f"{_GATE_CAS_KEY_PREFIX}{gate_id}"
        try:
            redis_client = _get_redis()
            if redis_client is not None:
                if token:
                    res = redis_client.eval(_LUA_DELETE_IF_OWNED, 1, key, token)
                    return int(res or 0) == 1
                redis_client.delete(key)
                return True
        except Exception as exc:
            logger.debug("[WizardGateService] CAS release Redis falhou: %s", exc)
        # in-memory: nunca persistiu in_progress, nada a remover
        return False

    async def _cas_wait_for_final(self, gate_id: str) -> dict[str, Any] | None:
        """Polling curto: aguarda o vencedor publicar o resultado final.

        Returns o payload final, ou ``None`` se o lease expirar antes.
        """
        elapsed = 0.0
        while elapsed < _GATE_POLL_MAX_WAIT_SECONDS:
            await asyncio.sleep(_GATE_POLL_INTERVAL_SECONDS)
            elapsed += _GATE_POLL_INTERVAL_SECONDS
            state, payload = self._cas_peek(gate_id)
            if state == "final":
                return payload
            if state == "absent":
                # Vencedor crashou e liberou o lease — ninguém vai publicar.
                return None
        return None

    # ------------------------------------------------------------------
    # Audit emission
    # ------------------------------------------------------------------

    async def _emit_gate_audit(
        self,
        *,
        gate_id: str,
        thread_id: str,
        company_id: str,
        decision: str,
        comment: str | None,
        resume_domain: str,
        actor_user_id: str | None = None,
    ) -> None:
        """Emite **um** audit row em ``audit_logs`` por gate resolvido.

        Best-effort: falha NÃO bloqueia o resume. Mapeia para
        ``decision_type='wizard_step_completed'`` que já existe em
        ``DECISION_TYPE_MAPPING`` (-> ``DecisionType.GENERATE_FEEDBACK``,
        retenção 730 dias). Reasoning inclui ``gate_id`` e ``thread_id``
        para correlação.
        """
        if not company_id:
            logger.debug("[WizardGateService] audit skipped — sem company_id (gate=%s)", gate_id)
            return
        try:
            from app.shared.compliance.audit_service import audit_service
            await audit_service.log_decision(  # AUDIT-NO-DEMO: wizard HITL gate (job creation flow, no candidate decision; LGPD Art.20 N/A)
                company_id=str(company_id),
                agent_name="wizard_gate_service",
                decision_type="wizard_step_completed",
                action=f"resume_gate:{resume_domain}",
                decision=decision,
                reasoning=[
                    f"gate_id={gate_id}",
                    f"thread_id={thread_id}",
                    f"comment={comment or ''}",
                ],
                criteria_used=["wizard_hitl_unified_contract", resume_domain],
                human_review_required=False,
                # Task #1092 — propaga aprovador para permitir verificação
                # de idempotência via /admin/audit-decisions/by-user/{id}.
                actor_user_id=actor_user_id or None,
            )
        except Exception as exc:
            logger.warning("[WizardGateService] audit emit falhou (best-effort): %s", exc)

    # ------------------------------------------------------------------
    # Engine de resume (encapsulado p/ Task #1085 trocar implementação)
    # ------------------------------------------------------------------

    async def _resume_engine(
        self,
        *,
        thread_id: str,
        resume_domain: str,
        agent_timeout: float,
        resume_message: str = "approved",
    ) -> str:
        """Retoma o grafo LangGraph pausado e devolve a mensagem final.

        T2 (Task #1085): delega para ``JobCreationGraph.aresume_with_message``
        — o grafo canônico do wizard, que pausa em ``langgraph.types.interrupt()``
        nos HITL gates e retoma via ``Command(resume=<msg>)`` no ponto exato
        da pergunta. Esse contrato substitui o legacy ``JobWizardGraph.ainvoke(None)``,
        que perdia a resposta do recrutador entre turnos e fazia o wizard
        repetir a mesma pergunta em loop.

        Args:
            thread_id: thread LangGraph (canonical via ``derive_thread_id``).
            resume_domain: domínio do gate (``"wizard"`` etc) — preservado
                para audit/observability; só wizard é coberto hoje.
            agent_timeout: timeout do ``ainvoke`` (segundos).
            resume_message: payload textual entregue ao ``interrupt()`` que
                pausou o grafo. Default ``"approved"`` cobre o fluxo de
                aprovação via botão (sem comentário). Quando o aprovador
                deixou um comentário livre, o caller passa o comentário
                como ``resume_message`` para que o nó pausado consiga
                interpretar o conteúdo da decisão.
        """
        from app.domains.job_creation.graph import JobCreationGraph
        graph = JobCreationGraph()
        result = await asyncio.wait_for(
            graph.aresume_with_message(thread_id, resume_message),
            timeout=agent_timeout,
        )
        if isinstance(result, dict):
            stage_payload = result.get("ws_stage_payload") or {}
            stage_data = stage_payload.get("data") or {}
            return (
                result.get("gate_clarify_message", "")
                or stage_data.get("message", "")
                or stage_data.get("response_text", "")
                or result.get("response", "")
                or result.get("user_message", "")
                or "Vaga criada com sucesso."
            )
        return "Vaga criada com sucesso."

    # ------------------------------------------------------------------
    # Entry point canônico
    # ------------------------------------------------------------------

    async def resume_gate(
        self,
        *,
        thread_id: str,
        pending_id: str,
        decision: str,
        ws_session_id: str,
        company_id: str = "",
        user_id: str = "",
        comment: str | None = None,
        gate_id: str | None = None,
        resume_domain: str = "wizard",
        agent_timeout: float = 90.0,
    ) -> dict[str, Any]:
        """Resume um gate HITL do wizard de forma idempotente sob concorrência real.

        Args:
            thread_id: thread LangGraph (canonical via ``derive_thread_id``).
            pending_id: UUID4 do hitl_service.request_approval.
            decision: ``"approved"`` ou ``"rejected"``.
            ws_session_id: session ID do WS para enviar frames.
            company_id: tenant scope (obrigatório em strict mode).
            user_id: aprovador (preenche ``resolved_by`` no audit trail).
            comment: comentário opcional do aprovador.
            gate_id: opcional. **Se fornecido, DEVE ser exatamente igual ao
                ``derive_gate_id(thread_id, pending_id)``** — caso contrário
                ``ValueError`` é levantado. Esta validação estrita impede que
                um cliente malicioso/buggy force colisão de chave de
                idempotência ou suprima audit rows ao injetar um ``gate_id``
                divergente do canônico.
            resume_domain: ``"wizard"`` ou ``"cv_screening"`` etc — só wizard
                por ora; outros domínios continuam no caminho legacy.
            agent_timeout: timeout do ``ainvoke`` (segundos).

        Returns:
            ``{"status", "message", "gate_id", "cached", "decision"}``.
            ``cached=True`` indica que este gate_id já tinha sido resolvido
            anteriormente — chamada idempotente, audit row NÃO emitido novamente.

        Raises:
            ValueError: ``gate_id`` foi fornecido mas não bate com o derivado.
        """
        gid = self.derive_gate_id(thread_id, pending_id)
        if gate_id is not None and gate_id != gid:
            # Tampering / bug do caller: rejeitar fail-LOUD para preservar
            # integridade do contrato canônico e do audit trail.
            raise ValueError(
                f"gate_id mismatch: caller passou {gate_id!r} mas derive_gate_id"
                f"(thread_id={thread_id!r}, pending_id={pending_id!r}) = {gid!r}. "
                f"Não passe gate_id custom — a derivação canônica é a única fonte de verdade."
            )

        # ---------- 1. Tentar adquirir o lease (CAS atômico) ----------
        # Em Redis: SET NX EX. Em fallback in-memory: serializa via asyncio.Lock
        # por gate_id e checa _memory_cas após adquirir o lock.
        memory_lock: asyncio.Lock | None = None
        if _get_redis() is None:
            memory_lock = await self._get_memory_lock(gid)
            await memory_lock.acquire()
        try:
            tag, info = self._cas_acquire(gid)
            # Token do lease que ESTE worker venceu — passado para finalize/release
            # para garantir que só sobrescrevemos/derrubamos o marker se ainda
            # somos os donos (defesa contra lease expirado mid-execution).
            winner_token: str = info if (tag == "won" and isinstance(info, str)) else ""

            if tag == "cached":
                logger.info(
                    "[WizardGateService] gate %s já resolvido (cached) — skip resume + audit",
                    gid,
                )
                cached_resp = dict(info or {})
                cached_resp["cached"] = True
                return cached_resp

            if tag == "wait":
                # Outro worker está executando este gate em outro processo.
                # Aguardar peek até ver o final ou timeout do lease.
                logger.info(
                    "[WizardGateService] gate %s in_progress por outro worker — aguardando", gid,
                )
                final = await self._cas_wait_for_final(gid)
                if final is not None:
                    final_resp = dict(final)
                    final_resp["cached"] = True
                    return final_resp
                # Vencedor crashou; cair para tentar novamente como vencedor.
                tag2, info2 = self._cas_acquire(gid)
                if tag2 != "won":
                    # Ainda não conseguiu — devolve erro determinístico.
                    return {
                        "status": "error",
                        "message": "Não foi possível retomar este gate após contenção. Tente novamente.",
                        "gate_id": gid,
                        "cached": False,
                        "decision": decision,
                        "resolved_at": datetime.now(UTC).isoformat(),
                    }
                winner_token = info2 if isinstance(info2, str) else ""

            # ---------- 2. Vencedor — executa engine + audit + finalize ----------
            if decision != "approved":
                await self._emit_gate_audit(
                    gate_id=gid,
                    thread_id=thread_id,
                    company_id=company_id,
                    decision="rejected",
                    comment=comment,
                    resume_domain=resume_domain,
                    actor_user_id=user_id or None,
                )
                payload = {
                    "status": "rejected",
                    "message": "Ação cancelada pelo aprovador. Nenhuma alteração foi feita.",
                    "gate_id": gid,
                    "cached": False,
                    "decision": "rejected",
                    "resolved_at": datetime.now(UTC).isoformat(),
                }
                self._cas_finalize(gid, payload, token=winner_token)
                return payload

            try:
                message = await self._resume_engine(
                    thread_id=thread_id,
                    resume_domain=resume_domain,
                    agent_timeout=agent_timeout,
                    resume_message=(comment or "approved"),
                )
                status = "ok"
            except asyncio.TimeoutError:
                logger.error("[WizardGateService] resume engine timeout gate=%s", gid)
                message = "O processamento demorou demais. Tente novamente."
                status = "timeout"
            except Exception as exc:
                logger.error(
                    "[WizardGateService] resume engine erro gate=%s: %s", gid, exc, exc_info=True
                )
                message = "Erro ao retomar execução após aprovação."
                status = "error"

            if status == "ok":
                await self._emit_gate_audit(
                    gate_id=gid,
                    thread_id=thread_id,
                    company_id=company_id,
                    decision="approved",
                    comment=comment,
                    resume_domain=resume_domain,
                    actor_user_id=user_id or None,
                )

            payload = {
                "status": status,
                "message": message,
                "gate_id": gid,
                "cached": False,
                "decision": decision,
                "resolved_at": datetime.now(UTC).isoformat(),
            }
            if status == "ok":
                self._cas_finalize(gid, payload, token=winner_token)
            else:
                # Timeout/erro: solta o lease para permitir retry sem esperar TTL
                self._cas_release_failed(gid, token=winner_token)
            return payload
        finally:
            if memory_lock is not None and memory_lock.locked():
                memory_lock.release()


# Singleton — import como ``from ... import wizard_gate_service``
wizard_gate_service = WizardGateService()
