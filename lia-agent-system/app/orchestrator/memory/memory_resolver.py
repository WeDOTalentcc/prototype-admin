"""
Memory Resolver — Tier 0: resolução de pronomes/referências via WorkingMemory.

Enriquece mensagens ambíguas ANTES do roteamento, convertendo referências
implícitas em entidades concretas da memória de trabalho da sessão.

Exemplos:
  "mover ele para próxima fase"       → "mover candidato João Silva para próxima fase"
  "atualizar a vaga"                  → "atualizar a vaga Desenvolvedor Backend (ID: abc123)"
  "ver o relatório disso"             → "ver o relatório da triagem da vaga XYZ"
  "e o terceiro?"                     → "e o candidato na posição 3 da lista anterior?"
  "mostra mais"                       → sinaliza paginação (is_pagination=True)

Isso reduz chamadas LLM desnecessárias para clarificação e melhora a
precisão do roteamento nas etapas seguintes (Tier 1/2/3).
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pronomes e marcadores de referência que sinalizam ambiguidade
# ---------------------------------------------------------------------------

_PRONOUN_PATTERNS = re.compile(
    r"\b(ele|ela|eles|elas|esse|essa|isso|aquele|aquela|aquilo|"
    r"este|esta|isto|o mesmo|a mesma|os mesmos|as mesmas|"
    r"tal candidato|tal vaga|dito|mencionado)\b",
    re.IGNORECASE | re.UNICODE,
)

_ENTITY_REF_PATTERNS = re.compile(
    r"\b(a vaga|o candidato|a candidata|o processo|o pipeline|"
    r"a triagem|o relatório|os candidatos|a entrevista|o cargo)\b",
    re.IGNORECASE | re.UNICODE,
)

# Referências posicionais: "o primeiro", "o terceiro", "o 2º", "o 5°", etc.
_POSITIONAL_PATTERNS = re.compile(
    r"\b(o|a)\s+"
    r"(primeiro|segundo|terceiro|quarto|quinto|sexto|sétimo|oitavo|nono|décimo"
    r"|1[oº°]|2[oº°]|3[oº°]|4[oº°]|5[oº°]|6[oº°]|7[oº°]|8[oº°]|9[oº°]|10[oº°]"
    r"|1º|2º|3º|4º|5º|6º|7º|8º|9º|10º)\b",
    re.IGNORECASE | re.UNICODE,
)

_POSITIONAL_WORD_TO_INDEX: dict[str, int] = {
    "primeiro": 0, "1o": 0, "1º": 0, "1°": 0,
    "segundo": 1, "2o": 1, "2º": 1, "2°": 1,
    "terceiro": 2, "3o": 2, "3º": 2, "3°": 2,
    "quarto": 3, "4o": 3, "4º": 3, "4°": 3,
    "quinto": 4, "5o": 4, "5º": 4, "5°": 4,
    "sexto": 5, "6o": 5, "6º": 5, "6°": 5,
    "sétimo": 6, "7o": 6, "7º": 6, "7°": 6,
    "oitavo": 7, "8o": 7, "8º": 7, "8°": 7,
    "nono": 8, "9o": 8, "9º": 8, "9°": 8,
    "décimo": 9, "10o": 9, "10º": 9, "10°": 9,
}

# Palavras que indicam "mostra mais" / paginação
_PAGINATION_PATTERNS = re.compile(
    r"\b(mostra mais|ver mais|próximos|próximas|mais candidatos|mais vagas|"
    r"continue|continuar|seguintes|avançar|página seguinte|next page)\b",
    re.IGNORECASE | re.UNICODE,
)

# Palavras que indicam continuidade de contexto (manter filtros ativos)
_CONTINUITY_PATTERNS = re.compile(
    r"\b(e (ele|ela|eles|elas|esse|essa)|e (o|a) (candidato|vaga|cargo)|"
    r"e (o primeiro|o segundo|o terceiro)|também|agora (ele|ela)|"
    r"e agora|e depois|e o próximo|e a próxima|e (mais|outros))\b",
    re.IGNORECASE | re.UNICODE,
)

# Palavras de nova busca (resetar filtros/paginação)
_NEW_SEARCH_PATTERNS = re.compile(
    r"\b(busca(r)?|procura(r)?|encontra(r)?|quero ver|me mostra|"
    r"lista(r)? candidatos|filtra(r)?|nova busca|novo filtro|"
    r"agora quero|muda(r)? para|trocar para)\b",
    re.IGNORECASE | re.UNICODE,
)


def _extract_entity_label(entity: dict[str, Any]) -> str:
    """Formata um entity dict em string legível para injeção no prompt."""
    entity_id = entity.get("id", "")
    name = entity.get("name") or entity.get("title") or entity.get("label") or ""

    if not name and not entity_id:
        return ""

    if name and entity_id:
        return f"{name} (ID: {entity_id})"
    return name or str(entity_id)


def _should_resolve(message: str) -> bool:
    """Retorna True se a mensagem contém pronomes ou referências que precisam de resolução."""
    return bool(
        _PRONOUN_PATTERNS.search(message)
        or _ENTITY_REF_PATTERNS.search(message)
        or _POSITIONAL_PATTERNS.search(message)
    )


def is_pagination_request(message: str) -> bool:
    """Retorna True se a mensagem é uma solicitação de paginação ("mostra mais")."""
    return bool(_PAGINATION_PATTERNS.search(message))


def should_keep_filters(message: str) -> bool:
    """
    Retorna True se a mensagem indica continuidade de contexto (manter filtros ativos).

    Distingue entre:
    - Continuidade: "e ele?", "e o segundo?", "também aprova ela" → keep filters
    - Nova busca: "busca candidatos Python", "filtra por São Paulo" → reset filters
    """
    if _NEW_SEARCH_PATTERNS.search(message):
        return False
    if _CONTINUITY_PATTERNS.search(message):
        return True
    # Se tem pronome mas não é nova busca → provavelmente continuidade
    if _PRONOUN_PATTERNS.search(message) and not _NEW_SEARCH_PATTERNS.search(message):
        return True
    return False


def _resolve_positional(message: str, candidate_ids: list[int]) -> tuple[int, int] | None:
    """
    Detecta referência posicional e retorna (índice, candidate_id) ou None.
    Ex: "o terceiro" com lista [10, 20, 30] → (2, 30)
    """
    if not candidate_ids:
        return None

    match = _POSITIONAL_PATTERNS.search(message)
    if not match:
        return None

    positional_word = match.group(2).lower()
    idx = _POSITIONAL_WORD_TO_INDEX.get(positional_word)
    if idx is None:
        return None

    if idx >= len(candidate_ids):
        logger.debug(
            "[MemoryResolver] Positional index %d out of range (list size=%d)",
            idx, len(candidate_ids),
        )
        return None

    return idx, candidate_ids[idx]


class MemoryResolver:
    """
    Resolve referências implícitas em mensagens usando WorkingMemory da sessão.

    Usa memória de trabalho (último candidato, última vaga, último pipeline
    mencionado) para substituir pronomes por entidades concretas.

    Não bloqueia o fluxo se a memória não estiver disponível — retorna a
    mensagem original sem modificação.
    """

    async def resolve(
        self,
        message: str,
        session_id: str,
        domain: str | None = None,
        conversation_state: Any | None = None,
        candidate_list_store: Any | None = None,
    ) -> tuple[str, bool]:
        """
        Tenta enriquecer a mensagem com contexto da memória de trabalho.

        Args:
            message: Mensagem original do usuário.
            session_id: ID da sessão para busca na memória.
            domain: Domínio hint (otimiza a busca na memória).
            conversation_state: ConversationState opcional (para resolução posicional
                                sem depender do WorkingMemory async).

        Returns:
            Tuple (enriched_message, was_resolved):
                - enriched_message: mensagem com referências substituídas (ou original).
                - was_resolved: True se pelo menos uma substituição foi feita.
        """
        if not _should_resolve(message):
            return message, False

        # ── Resolução posicional ────────────────────────────────────────────
        # Prioridade: dados completos do Redis (CandidateListStore) > IDs do ConversationState
        positional_match = _POSITIONAL_PATTERNS.search(message)
        if positional_match:
            positional_word = positional_match.group(2).lower()
            idx = _POSITIONAL_WORD_TO_INDEX.get(positional_word)
            if idx is not None:
                # Tenta primeiro o Redis com dados completos
                candidate_full: dict[str, Any] | None = None
                if candidate_list_store is not None:
                    try:
                        candidate_full = await candidate_list_store.get_by_position(session_id, idx)
                    except Exception as exc:
                        logger.debug("[MemoryResolver] CandidateListStore error: %s", exc)

                if candidate_full is not None:
                    cid = candidate_full.get("id", "")
                    name = (
                        candidate_full.get("name")
                        or candidate_full.get("nome")
                        or candidate_full.get("full_name")
                        or ""
                    )
                    score = candidate_full.get("score") or candidate_full.get("lia_score")
                    score_str = f", score: {score:.0%}" if isinstance(score, float) else ""
                    label = f"candidato {name} (ID: {cid}{score_str})" if name else f"candidato ID: {cid}"
                    enriched = f"[Referência posicional resolvida: posição {idx + 1} = {label}]\n{message}"
                    logger.debug(
                        "[MemoryResolver] Positional resolved via Redis session=%s pos=%d cid=%s",
                        session_id, idx + 1, cid,
                    )
                    return enriched, True

                # Fallback: IDs do ConversationState
                if conversation_state is not None:
                    ids = conversation_state.last_candidates_shown
                    if 0 <= idx < len(ids):
                        candidate_id = ids[idx]
                        reverse_map = {v: k for k, v in conversation_state.mentioned_candidates.items()}
                        name = reverse_map.get(candidate_id, "")
                        label = f"candidato {name} (ID: {candidate_id})" if name else f"candidato ID: {candidate_id}"
                        enriched = f"[Referência posicional resolvida: posição {idx + 1} = {label}]\n{message}"
                        logger.debug(
                            "[MemoryResolver] Positional resolved via ConversationState session=%s pos=%d cid=%d",
                            session_id, idx + 1, candidate_id,
                        )
                        return enriched, True

        # ── Resolução via WorkingMemory (async, com I/O) ──
        try:
            from lia_agents_core.working_memory import WorkingMemoryService
            memory_service = WorkingMemoryService()
            context = await memory_service.get_context_summary(
                session_id=session_id,
                domain=domain or "recruiter_assistant",
            )
        except Exception as exc:
            logger.debug("[MemoryResolver] WorkingMemory unavailable: %s", exc)
            return message, False

        if not context:
            return message, False

        enriched = message
        resolved = False

        # Injeta entidades resolvidas como prefixo de contexto para o LLM
        # (mais seguro que substituição direta de string, que pode alterar semântica)
        context_lines = self._build_context_lines(context, conversation_state)
        if context_lines:
            enriched = f"[Contexto da sessão: {'; '.join(context_lines)}]\n{message}"
            resolved = True
            logger.debug(
                "[MemoryResolver] Resolved session=%s context_size=%d",
                session_id,
                len(context_lines),
            )

        return enriched, resolved

    def _build_context_lines(self, context: Any, conversation_state: Any | None = None) -> list:
        """Extrai linhas de contexto legíveis da memória de trabalho."""
        lines = []

        # Última entidade explícita do ConversationState (Phase 2)
        if conversation_state is not None and conversation_state.last_entity:
            entity = conversation_state.last_entity
            entity_type = entity.get("type", "entidade")
            label = _extract_entity_label(entity)
            if label:
                lines.append(f"último {entity_type} mencionado: {label}")

        if isinstance(context, str) and context.strip():
            lines.append(context.strip()[:300])
            return lines[:5]

        if not isinstance(context, dict):
            return lines[:5]

        # Candidato mais recente
        if candidate := context.get("last_candidate"):
            label = _extract_entity_label(
                candidate if isinstance(candidate, dict)
                else {"name": str(candidate)}
            )
            if label:
                lines.append(f"candidato atual: {label}")

        # Vaga mais recente
        if job := context.get("last_job") or context.get("current_job"):
            label = _extract_entity_label(
                job if isinstance(job, dict)
                else {"title": str(job)}
            )
            if label:
                lines.append(f"vaga atual: {label}")

        # Pipeline / etapa atual
        if stage := context.get("current_stage") or context.get("pipeline_stage"):
            lines.append(f"etapa atual: {stage}")

        # IDs coletados (wizard)
        if fields := context.get("collected_fields"):
            if isinstance(fields, dict):
                if job_title := fields.get("job_title") or fields.get("title"):
                    lines.append(f"título da vaga em edição: {job_title}")
                if candidate_name := fields.get("candidate_name"):
                    lines.append(f"candidato em foco: {candidate_name}")

        # LIA-R04: inject recent actions if available
        recent = self.get_recent_actions(limit=3)
        if recent:
            action_summary = "; ".join(
                f"{a['domain']}.{a['action']}" for a in recent
            )
            lines.append(f"ações recentes: {action_summary}")
        return lines[:5]  # Máximo 5 linhas para não poluir o prompt


    # ── LIA-R04: action_history ──────────────────────────────────────────────

    _MAX_ACTION_HISTORY: int = 20

    def _ensure_action_history(self) -> None:
        if not hasattr(self, "_action_history"):
            self._action_history: list = []

    def add_action(
        self,
        domain: str,
        action: str,
        metadata: dict | None = None,
    ) -> None:
        """Registra uma ação no histórico (LIA-R04).

        Args:
            domain: Domínio que executou a ação (ex: "cv_screening").
            action: Identificador da ação (ex: "shortlist_candidate").
            metadata: Dados adicionais opcionais (ex: candidate_id, job_id).
        """
        import datetime as _dt
        self._ensure_action_history()
        entry = {
            "domain": domain,
            "action": action,
            "timestamp": _dt.datetime.now(_dt.UTC).isoformat(),
            "metadata": metadata or {},
        }
        self._action_history.append(entry)
        if len(self._action_history) > self._MAX_ACTION_HISTORY:
            self._action_history = self._action_history[-self._MAX_ACTION_HISTORY:]

    def get_recent_actions(self, limit: int = 5) -> list:
        """Retorna as ações mais recentes do histórico (LIA-R04).

        Args:
            limit: Número máximo de ações a retornar (padrão 5).

        Returns:
            Lista de dicts com domain, action, timestamp, metadata.
        """
        self._ensure_action_history()
        return list(self._action_history[-limit:])

    def get_action_history(self) -> list:
        """Retorna o histórico completo de ações (até _MAX_ACTION_HISTORY)."""
        self._ensure_action_history()
        return list(self._action_history)


# Singleton compartilhado
memory_resolver = MemoryResolver()
