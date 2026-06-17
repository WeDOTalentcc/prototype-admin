"""
RecruiterProfileService — perfil de preferências do recrutador para personalização da LIA.
Aprende tom preferido, nível de detalhe e ferramentas favoritas a partir das interações.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, StrEnum

logger = logging.getLogger(__name__)


class TonePreference(StrEnum):
    DIRECT = "direct"        # Respostas curtas, direto ao ponto
    CONSULTIVE = "consultive"  # Mais explicações, sugestões proativas
    BALANCED = "balanced"    # Padrão


class DetailLevel(StrEnum):
    HIGH = "high"      # Dados brutos, tabelas, números
    MEDIUM = "medium"  # Equilíbrio entre narrativa e dados
    LOW = "low"        # Narrativa simples, sem muitos números


@dataclass
class RecruiterProfile:
    user_id: str
    company_id: str
    tone: TonePreference = TonePreference.BALANCED
    detail_level: DetailLevel = DetailLevel.MEDIUM
    favorite_tools: list[str] = field(default_factory=list)
    interaction_count: int = 0
    last_actions: list[str] = field(default_factory=list)

    def to_prompt_snippet(self) -> str:
        if self.interaction_count < 5:
            return ""  # Poucos dados, não personalizar ainda

        tone_instruction = {
            TonePreference.DIRECT: "Seja direto e conciso. Prefira bullet points e dados tabulados.",
            TonePreference.CONSULTIVE: "Forneça contexto e explicações. Sugira próximos passos proativamente.",
            TonePreference.BALANCED: "",
        }[self.tone]

        detail_instruction = {
            DetailLevel.HIGH: "Inclua dados numéricos detalhados e comparações.",
            DetailLevel.MEDIUM: "",
            DetailLevel.LOW: "Use linguagem simples. Evite tabelas complexas.",
        }[self.detail_level]

        parts = [p for p in [tone_instruction, detail_instruction] if p]
        if not parts:
            return ""

        return "## Preferências do Recrutador\n" + "\n".join(f"- {p}" for p in parts)

    def update_from_interaction(self, action: str, tool_used: str | None = None) -> None:
        self.interaction_count += 1
        self.last_actions.append(action)
        if len(self.last_actions) > 20:
            self.last_actions = self.last_actions[-20:]
        if tool_used and tool_used not in self.favorite_tools:
            if self.last_actions.count(f"tool:{tool_used}") >= 3:
                self.favorite_tools.append(tool_used)


class RecruiterProfileService:
    """Gerencia perfis de recrutadores para personalização da LIA."""

    def __init__(self) -> None:
        self._cache: dict[str, RecruiterProfile] = {}

    async def get_profile(self, user_id: str, company_id: str) -> RecruiterProfile:
        """Retorna perfil do recrutador. Cria um novo se não existir."""
        cache_key = f"{company_id}:{user_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Tentar buscar do Redis
        try:
            import json

            import redis
            from lia_config.config import settings
            _r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            data = _r.get(f"recruiter_profile:{cache_key}")
            if data:
                d = json.loads(data)
                profile = RecruiterProfile(
                    user_id=user_id,
                    company_id=company_id,
                    tone=TonePreference(d.get("tone", "balanced")),
                    detail_level=DetailLevel(d.get("detail_level", "medium")),
                    favorite_tools=d.get("favorite_tools", []),
                    interaction_count=d.get("interaction_count", 0),
                    last_actions=d.get("last_actions", []),
                )
                self._cache[cache_key] = profile
                return profile
        except Exception:
            pass

        profile = RecruiterProfile(user_id=user_id, company_id=company_id)
        self._cache[cache_key] = profile
        return profile

    async def save_profile(self, profile: RecruiterProfile) -> None:
        """Persiste o perfil no Redis."""
        try:
            import json

            import redis
            from lia_config.config import settings
            _r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5)
            cache_key = f"{profile.company_id}:{profile.user_id}"
            _r.setex(
                f"recruiter_profile:{cache_key}",
                86400 * 30,  # 30 dias TTL
                json.dumps({
                    "tone": profile.tone.value,
                    "detail_level": profile.detail_level.value,
                    "favorite_tools": profile.favorite_tools,
                    "interaction_count": profile.interaction_count,
                    "last_actions": profile.last_actions[-10:],
                }),
            )
            self._cache[cache_key] = profile
        except Exception as exc:
            logger.debug("[RecruiterProfileService] save failed: %s", exc)
