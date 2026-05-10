"""
CompanyId — value object canônico para identificadores de tenant.

Substitui o uso solto de ``str | UUID | None | "default" | "demo_company"``
espalhado pelo backend. Construir um CompanyId é a forma garantida de:

1. Parsear/validar a entrada (UUID v4 ou slug ``^[a-z][a-z0-9_-]{2,63}$``)
2. Normalizar (lowercase para UUID, strip)
3. Falhar fechado em valores inválidos (``""``, ``None``, ``"default"``, etc.)
4. Expor conversão segura para ``UUID`` quando aplicável

Não substitui ``str`` no schema do banco — é um wrapper de domínio para uso
em camadas de serviço e agentes (TenantAwareAgentMixin, MainOrchestrator,
WizardSessionService).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final
from uuid import UUID

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

# Slugs válidos: começam com letra, 3-64 chars, [a-z0-9_-]
_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")

# Valores que historicamente vazaram como company_id e devem ser rejeitados.
# "default" é o legado mais comum (ver migrate-default-company-id task — MERGED).
_FORBIDDEN_LITERALS: Final[frozenset[str]] = frozenset({
    "default",
    "none",
    "null",
    "undefined",
    "system",
    "anonymous",
})


@dataclass(frozen=True, slots=True)
class CompanyId:
    """Identificador imutável e validado de tenant.

    Use ``CompanyId.parse(raw)`` em vez do construtor — o construtor é
    mantido apenas para casos em que o caller já validou.

    Attributes:
        value: forma normalizada (UUID em lowercase ou slug em lowercase).
    """

    value: str

    # --- factory --------------------------------------------------------

    @classmethod
    def parse(cls, raw: str | UUID | None) -> CompanyId:
        """Parseia/normaliza/valida a entrada.

        Aceita:
            - ``UUID`` → ``CompanyId("00000000-...-...-...-............")``
            - ``str`` em formato UUID (qualquer case, com ou sem hífens)
            - ``str`` em formato slug ``^[a-z][a-z0-9_-]{2,63}$``

        Rejeita (``InvalidCompanyIdError``):
            - ``None`` ou string vazia/whitespace
            - Literais reservados: ``"default"``, ``"none"``, ``"null"``,
              ``"undefined"``, ``"system"``, ``"anonymous"`` (case-insensitive)
            - Strings que não são UUID nem slug válido

        Raises:
            InvalidCompanyIdError: com ``error_code='INVALID_COMPANY_ID'`` e
                payload ``{'company_id_raw': <repr>, 'reason': <str>}``.
        """
        if raw is None:
            raise InvalidCompanyIdError(
                "company_id é obrigatório (recebido None)",
                details={"company_id_raw": None, "reason": "none"},
            )

        if isinstance(raw, UUID):
            # Mesma política aplicada ao branch string: v4 only.
            if raw.version != 4:
                raise InvalidCompanyIdError(
                    f"company_id deve ser UUID v4, recebido v{raw.version}: {raw!s}",
                    details={
                        "company_id_raw": repr(raw),
                        "reason": "uuid_version",
                        "uuid_version": raw.version,
                    },
                )
            return cls(value=str(raw).lower())

        if not isinstance(raw, str):
            raise InvalidCompanyIdError(
                f"company_id deve ser str ou UUID, recebido {type(raw).__name__}",
                details={"company_id_raw": repr(raw), "reason": "type"},
            )

        normalized = raw.strip().lower()
        if not normalized:
            raise InvalidCompanyIdError(
                "company_id vazio ou apenas whitespace",
                details={"company_id_raw": repr(raw), "reason": "empty"},
            )

        if normalized in _FORBIDDEN_LITERALS:
            raise InvalidCompanyIdError(
                f"company_id reservado/proibido: {normalized!r}",
                details={"company_id_raw": repr(raw), "reason": "forbidden_literal"},
            )

        # Tenta UUID primeiro (mais comum em produção). REQUER versão 4 —
        # outras versões (v1/v3/v5) carregam metadata previsível (MAC, namespace)
        # que vaza tenant info ou abre enumeration. Política do projeto: v4 only.
        try:
            parsed_uuid = UUID(normalized)
        except (ValueError, AttributeError):
            parsed_uuid = None
        if parsed_uuid is not None:
            if parsed_uuid.version != 4:
                raise InvalidCompanyIdError(
                    f"company_id deve ser UUID v4, recebido v{parsed_uuid.version}: {normalized!r}",
                    details={
                        "company_id_raw": repr(raw),
                        "reason": "uuid_version",
                        "uuid_version": parsed_uuid.version,
                    },
                )
            return cls(value=str(parsed_uuid).lower())

        # Caso slug (ex.: "demo_company")
        if _SLUG_RE.match(normalized):
            return cls(value=normalized)

        raise InvalidCompanyIdError(
            f"company_id não é UUID válido nem slug ^[a-z][a-z0-9_-]{{2,63}}$: {normalized!r}",
            details={"company_id_raw": repr(raw), "reason": "format"},
        )

    # --- predicates -----------------------------------------------------

    @property
    def is_uuid(self) -> bool:
        try:
            return UUID(self.value).version == 4
        except ValueError:
            return False

    @property
    def is_slug(self) -> bool:
        return not self.is_uuid

    # --- accessors ------------------------------------------------------

    def as_str(self) -> str:
        """Retorna a forma canônica para persistência/logging."""
        return self.value

    def as_uuid(self) -> UUID:
        """Retorna ``UUID`` v4. Levanta se for slug.

        Raises:
            InvalidCompanyIdError: quando o valor é slug e o caller exige UUID.
        """
        try:
            parsed = UUID(self.value)
        except ValueError as exc:
            raise InvalidCompanyIdError(
                f"company_id é slug, não UUID: {self.value!r}",
                details={"company_id_raw": self.value, "reason": "slug_not_uuid"},
            ) from exc
        return parsed

    def __str__(self) -> str:
        return self.value
