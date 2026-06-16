import difflib
import logging
import re
from dataclasses import dataclass, field

from app.shared.memory.conversation_state import ConversationState

logger = logging.getLogger(__name__)

FUZZY_MATCH_THRESHOLD = 0.7


@dataclass
class ResolvedReference:
    resolved: bool
    reference_type: str
    resolved_id: int | None = None
    resolved_ids: list[int] = field(default_factory=list)
    original_text: str = ""
    confidence: float = 0.0
    action: str | None = None
    keep_filters: bool = False


class ReferenceResolver:

    PRONOUN_PATTERNS = [
        r"\b(esse|essa|este|esta)\s+(candidato|candidata|pessoa|profissional)\b",
        r"\b(fale|conte|mostre|detalhe)\s+(sobre|mais\s+sobre)\s+(ele|ela)\b",
        r"\b(perfil|cv|currículo|curri[cç]ulo)\s+(dele|dela|desse|dessa)\b",
        r"\b(chame|contate|entre\s+em\s+contato\s+com)\s+(ele|ela)\b",
        r"\b(dele|dela)\b",
        r"\b(desse|dessa|deste|desta)\s+(?!grupo|conjunto|resultado|lista)\b",
    ]

    POSITION_PATTERNS = [
        (r"\b[oa]\s+(primeir[oa])\b", 0),
        (r"\b[oa]\s+(segund[oa])\b", 1),
        (r"\b[oa]\s+(terceir[oa])\b", 2),
        (r"\b[oa]\s+(quart[oa])\b", 3),
        (r"\b[oa]\s+(quint[oa])\b", 4),
        (r"\b[oa]\s+(sext[oa])\b", 5),
        (r"\b[oa]\s+(sétim[oa])\b", 6),
        (r"\b[oa]\s+(oitav[oa])\b", 7),
        (r"\b[oa]\s+(non[oa])\b", 8),
        (r"\b[oa]\s+(décim[oa])\b", 9),
        (r"\b(número|posição|#)\s*(\d+)\b", None),
        (r"\b[oa]\s+últim[oa]\b", -1),
    ]

    PREVIOUS_PATTERNS = [
        r"\bo\s+anterior\b",
        r"\b(o\s+que|quem)\s+(vimos|analisamos|detalhamos)\s+(antes|anteriormente)\b",
        r"\bvolt[eao]r?\s+(para|ao)\s+(anterior|último)\b",
    ]

    SHORTLIST_PATTERNS_ADD = [
        r"\b(salve|salvar|favorite|favoritar|guardar)\b",
        r"\b(adicionar?\s+a[os]?\s+favoritos)\b",
        r"\b(colocar?\s+na\s+(lista|shortlist))\b",
    ]

    SHORTLIST_PATTERNS_SHOW = [
        r"\b(mostrar?|ver|listar?)\s+(favoritos|salvos|shortlist)\b",
        r"\b(meus?\s+favoritos)\b",
        r"\b(minha\s+shortlist)\b",
    ]

    SHORTLIST_PATTERNS_REMOVE = [
        r"\b(remover?|tirar?|excluir?)\s+(dos?\s+favoritos|da\s+shortlist)\b",
    ]

    CONTINUATION_PATTERNS = [
        r"\b(desse|deste|nesse|neste)\s+(grupo|conjunto|resultado|lista)\b",
        r"\b(dentre|entre)\s+(eles|elas|esses|essas)\b",
        r"\b(dos|das)\s+(que|quem)\s+(apareceram|listamos|vimos)\b",
        r"\b(filtrar?|buscar?)\s+(nesses|nesses)\s+(resultados?)\b",
    ]

    FILTER_KEEP_PATTERNS = [
        r"\b(mesm[oa]s?\s+filtros?)\b",
        r"\b(manter?\s+filtros?)\b",
        r"\b(com\s+os\s+mesmos\s+critérios)\b",
        r"\b(na\s+mesma\s+busca)\b",
    ]

    def resolve(self, query: str, state: ConversationState) -> ResolvedReference:
        normalized = self._normalize_query(query)

        if not normalized:
            return ResolvedReference(resolved=False, reference_type="none")

        resolvers = [
            self._resolve_shortlist,
            self._resolve_pronoun,
            self._resolve_position,
            self._resolve_previous,
            self._resolve_continuation,
            self._resolve_name,
        ]

        for resolver in resolvers:
            result = resolver(normalized, state)
            if result is not None:
                logger.info(
                    f"Reference resolved: type={result.reference_type} "
                    f"id={result.resolved_id} confidence={result.confidence:.2f} "
                    f"original='{result.original_text}'"
                )
                return result

        return ResolvedReference(resolved=False, reference_type="none", original_text=normalized)

    def _resolve_pronoun(self, query: str, state: ConversationState) -> ResolvedReference | None:
        for pattern in self.PRONOUN_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                candidate_id = state.last_candidate_detailed
                if candidate_id is None and state.last_candidates_shown:
                    candidate_id = state.last_candidates_shown[0]

                if candidate_id is None:
                    return ResolvedReference(
                        resolved=False,
                        reference_type="pronoun",
                        original_text=match.group(0),
                        confidence=0.0,
                    )

                return ResolvedReference(
                    resolved=True,
                    reference_type="pronoun",
                    resolved_id=candidate_id,
                    original_text=match.group(0),
                    confidence=0.9,
                )
        return None

    def _resolve_position(self, query: str, state: ConversationState) -> ResolvedReference | None:
        for pattern, index in self.POSITION_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if not state.last_candidates_shown:
                    return ResolvedReference(
                        resolved=False,
                        reference_type="position",
                        original_text=match.group(0),
                        confidence=0.0,
                    )

                if index is None:
                    pos = int(match.group(2)) - 1
                else:
                    pos = index

                candidates = state.last_candidates_shown

                if pos == -1:
                    pos = len(candidates) - 1

                if pos < 0 or pos >= len(candidates):
                    return ResolvedReference(
                        resolved=False,
                        reference_type="position",
                        original_text=match.group(0),
                        confidence=0.0,
                    )

                return ResolvedReference(
                    resolved=True,
                    reference_type="position",
                    resolved_id=candidates[pos],
                    original_text=match.group(0),
                    confidence=0.95,
                )
        return None

    def _resolve_previous(self, query: str, state: ConversationState) -> ResolvedReference | None:
        for pattern in self.PREVIOUS_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if len(state.detailed_history) < 2:
                    return ResolvedReference(
                        resolved=False,
                        reference_type="previous",
                        original_text=match.group(0),
                        confidence=0.0,
                    )

                previous_id = state.detailed_history[-2]
                return ResolvedReference(
                    resolved=True,
                    reference_type="previous",
                    resolved_id=previous_id,
                    original_text=match.group(0),
                    confidence=0.85,
                )
        return None

    def _resolve_shortlist(self, query: str, state: ConversationState) -> ResolvedReference | None:
        for pattern in self.SHORTLIST_PATTERNS_REMOVE:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                resolved_id = state.last_candidate_detailed
                return ResolvedReference(
                    resolved=True,
                    reference_type="shortlist",
                    resolved_id=resolved_id,
                    original_text=match.group(0),
                    confidence=0.9,
                    action="remove_shortlist",
                )

        for pattern in self.SHORTLIST_PATTERNS_SHOW:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return ResolvedReference(
                    resolved=True,
                    reference_type="shortlist",
                    resolved_ids=list(state.shortlist),
                    original_text=match.group(0),
                    confidence=0.95,
                    action="show_shortlist",
                )

        for pattern in self.SHORTLIST_PATTERNS_ADD:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                resolved_id = state.last_candidate_detailed
                if resolved_id is None and state.last_candidates_shown:
                    resolved_id = state.last_candidates_shown[0]

                return ResolvedReference(
                    resolved=True if resolved_id else False,
                    reference_type="shortlist",
                    resolved_id=resolved_id,
                    original_text=match.group(0),
                    confidence=0.9 if resolved_id else 0.0,
                    action="add_shortlist",
                )

        return None

    def _resolve_continuation(self, query: str, state: ConversationState) -> ResolvedReference | None:
        for pattern in self.CONTINUATION_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return ResolvedReference(
                    resolved=True,
                    reference_type="continuation",
                    resolved_ids=list(state.last_candidates_shown),
                    original_text=match.group(0),
                    confidence=0.8,
                    keep_filters=True,
                )
        return None

    def _resolve_name(self, query: str, state: ConversationState) -> ResolvedReference | None:
        if not state.mentioned_candidates:
            return None

        for name, candidate_id in state.mentioned_candidates.items():
            if name.lower() in query.lower():
                return ResolvedReference(
                    resolved=True,
                    reference_type="name",
                    resolved_id=candidate_id,
                    original_text=name,
                    confidence=0.95,
                )

        best_match = None
        best_ratio = 0.0
        best_name = ""

        query_words = query.lower().split()
        for name, candidate_id in state.mentioned_candidates.items():
            name_lower = name.lower()
            for i in range(len(query_words)):
                for j in range(i + 1, min(i + 5, len(query_words) + 1)):
                    segment = " ".join(query_words[i:j])
                    ratio = difflib.SequenceMatcher(None, segment, name_lower).ratio()
                    if ratio > best_ratio and ratio >= FUZZY_MATCH_THRESHOLD:
                        best_ratio = ratio
                        best_match = candidate_id
                        best_name = name

        if best_match is not None:
            return ResolvedReference(
                resolved=True,
                reference_type="name",
                resolved_id=best_match,
                original_text=best_name,
                confidence=best_ratio,
            )

        return None

    def should_keep_filters(self, query: str) -> bool:
        normalized = self._normalize_query(query)
        for pattern in self.FILTER_KEEP_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                return True
        for pattern in self.CONTINUATION_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                return True
        return False

    def _normalize_query(self, query: str) -> str:
        if not query:
            return ""
        normalized = query.strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized
