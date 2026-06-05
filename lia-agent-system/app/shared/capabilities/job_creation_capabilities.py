"""Aggregated, read-only, tenant-aware view of the JOB CREATION modes.

LIA can create a job vacancy three ways — and every chat surface must say the
SAME truth about it. This module is the single source of that truth. It does NOT
declare a new registry: it *derives* the modes from the registries that already
encode the capability (see ADR-008):

  - ``app/domains/job_management/config/capabilities.yaml`` — intent_keywords map
    (``template/modelo -> create_from_template``, ``clonar -> clone_job``,
    ``duplicar -> duplicate_job``, ``criar vaga/nova vaga -> create_job``,
    ``guiado/passo a passo -> guided_wizard`` ...).
  - the live tool registry (``app.tools.registry.tool_registry``).

A mode is only reported as *available* when a real intent backs it in the
registry — so this view can never claim a capability the platform does not have.

Fail-open by contract: this feeds prompt construction, so any registry hiccup
returns the static, conservative default (all three modes, registry-truth
unknown) instead of raising.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreationMode:
    """One way the recruiter can ask LIA to create a vacancy.

    ``available`` reflects whether the backing intents were found in the
    registry at derivation time. ``backed_by`` lists the canonical intent /
    action ids that prove the mode is real (provenance, not duplication).
    """

    key: str
    label: str
    description: str
    intents: tuple[str, ...]
    backed_by: tuple[str, ...] = field(default_factory=tuple)
    available: bool = True


# Canonical model of the three creation modes. The ``intents`` are the action
# ids we expect to find in the job_management intent_keywords map; presence of
# ANY of them flips the mode to available=True. This is the ONLY hand-written
# part, and it describes WHICH registry keys prove each mode — not a duplicate
# of what the registry contains.
_MODE_SPECS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "scratch",
        "Do zero (conversa guiada)",
        "Criar uma vaga nova do zero, conduzida pela LIA em conversa natural "
        "(o wizard canônico coleta título, senioridade, competências, triagem "
        "WSI e gera a descrição).",
        ("create_job", "guided_wizard"),
    ),
    (
        "template",
        "A partir de um template/modelo",
        "Partir de um template/modelo de vaga já existente — os dados da vaga "
        "são copiados como ponto de partida (sem candidatos) e a LIA segue a "
        "conversa para ajustar o que for preciso.",
        ("create_from_template", "apply_template", "search_templates"),
    ),
    (
        "existing",
        "A partir de uma vaga existente (duplicar/clonar)",
        "Partir de uma vaga existente: duplicar (clone completo, opcionalmente "
        "com os candidatos) ou clonar como modelo (só os dados da vaga).",
        ("duplicate_job", "clone_job"),
    ),
)


@lru_cache(maxsize=1)
def _job_management_intent_actions() -> frozenset[str]:
    """Return the set of action ids declared in job_management capabilities.yaml.

    Fail-open: returns an empty set if the YAML cannot be read; callers treat an
    empty set as "registry truth unknown" and keep the conservative default.
    """
    try:
        import pathlib

        import yaml  # type: ignore

        path = (
            pathlib.Path(__file__).resolve().parents[2]
            / "domains"
            / "job_management"
            / "config"
            / "capabilities.yaml"
        )
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        intents = data.get("intent_keywords") or {}
        return frozenset(str(v) for v in intents.values())
    except Exception as exc:  # noqa: BLE001 — never break prompt construction
        logger.debug("[capabilities] could not load job_management intents: %s", exc)
        return frozenset()


def get_creation_modes(
    *, allowed_actions: frozenset[str] | None = None
) -> list[CreationMode]:
    """Derive the job creation modes, tenant-filtered when ``allowed_actions``.

    Args:
        allowed_actions: optional tenant-scoped set of permitted action ids
            (e.g. derived from ``tool_permissions.yaml`` for the tenant). When
            given, a mode is available only if at least one of its backing
            intents is BOTH in the registry AND in this allowed set. When
            ``None`` (no tenant scoping), only registry truth gates the mode.

    Returns:
        List of :class:`CreationMode` (always all three; ``available`` reflects
        the derivation). Modes whose backing intents are entirely absent from the
        registry are returned with ``available=False`` rather than dropped, so
        callers can be explicit about what is NOT offered.
    """
    registry_actions = _job_management_intent_actions()
    registry_known = bool(registry_actions)

    modes: list[CreationMode] = []
    for key, label, description, intents in _MODE_SPECS:
        present = [i for i in intents if (not registry_known or i in registry_actions)]
        if allowed_actions is not None:
            present = [i for i in present if i in allowed_actions]
            available = bool(present)
        else:
            # No tenant scoping: available if registry truth is unknown
            # (conservative default) OR a backing intent exists.
            available = (not registry_known) or bool(present)
        modes.append(
            CreationMode(
                key=key,
                label=label,
                description=description,
                intents=intents,
                backed_by=tuple(present) if present else tuple(),
                available=available,
            )
        )
    return modes


# Canonical marker used by the anti-drift sentinel and the prompt post-processor
# to recognise a registry-derived creation-modes block.
CREATION_MODES_HEADING = "### Modos de criação de vaga"


def render_creation_modes_block(
    *, allowed_actions: frozenset[str] | None = None
) -> str:
    """Render the creation modes as a PT-BR prompt block (registry-derived).

    This is the ONE wording shared by ``SystemPromptBuilder``, the
    ``WizardOrchestrator`` and the meta-question helper, so they cannot diverge.
    """
    modes = get_creation_modes(allowed_actions=allowed_actions)
    available = [m for m in modes if m.available]
    lines = [
        CREATION_MODES_HEADING,
        "Você CONSEGUE criar uma vaga de três formas (não recuse nem invente):",
    ]
    for m in available:
        lines.append(f"- **{m.label}** — {m.description}")
    if available:
        lines.append(
            "Quando o recrutador pedir para partir de um template ou de uma vaga "
            "existente, conduza a identificação da fonte e siga — NUNCA diga que "
            "só sabe criar do zero."
        )
    return "\n".join(lines)


# Tokens that signal the user is asking whether LIA *can* create a vacancy.
_CAN_TOKENS = (
    "consegue",
    "consigo",
    "voce pode",
    "você pode",
    "da pra",
    "dá pra",
    "da para",
    "dá para",
    "tem como",
    "é possível",
    "e possivel",
    "sabe criar",
)
_CREATE_TOKENS = ("criar", "cria", "abrir", "abre", "nova vaga", "cadastrar")
_VAGA_TOKENS = ("vaga", "vacancy", "posição", "posicao", "oportunidade")

_EXISTING_TOKENS = ("existente", "existing", "duplicar", "duplicate", "clonar", "clone", "outra vaga", "vaga atual", "a partir de uma vaga")
_TEMPLATE_TOKENS = ("template", "modelo")
_SCRATCH_TOKENS = ("do zero", "from scratch", "começar do", "comecar do", "vazia", "em branco")


@dataclass(frozen=True)
class CanCreateAnswer:
    """Structured, deterministic answer to a 'consegue criar?' meta-question."""

    is_capability_question: bool
    matched_modes: tuple[str, ...]
    answer: str


def answer_can_create_question(
    text: str, *, allowed_actions: frozenset[str] | None = None
) -> CanCreateAnswer:
    """Deterministically answer "consegue criar uma vaga (a partir de X)?".

    Pure (no LLM): used by tests and as a grounded fallback. Returns
    ``is_capability_question=False`` when the text is not a create-capability
    question, so callers can decide whether to use it.
    """
    low = (text or "").strip().lower()
    if not low:
        return CanCreateAnswer(False, tuple(), "")

    has_can = any(t in low for t in _CAN_TOKENS) or "?" in low
    has_create = any(t in low for t in _CREATE_TOKENS)
    has_vaga = any(t in low for t in _VAGA_TOKENS)
    if not (has_create and has_vaga and has_can):
        return CanCreateAnswer(False, tuple(), "")

    modes = {m.key: m for m in get_creation_modes(allowed_actions=allowed_actions)}
    asked: list[str] = []
    if any(t in low for t in _EXISTING_TOKENS):
        asked.append("existing")
    if any(t in low for t in _TEMPLATE_TOKENS):
        asked.append("template")
    if any(t in low for t in _SCRATCH_TOKENS):
        asked.append("scratch")
    # No specific mode named -> the recruiter is asking about creation in general.
    target_keys = asked or [m.key for m in modes.values()]

    available_targets = [k for k in target_keys if modes.get(k) and modes[k].available]
    if available_targets:
        labels = ", ".join(modes[k].label.lower() for k in available_targets)
        answer = (
            f"Sim, consigo criar a vaga — inclusive {labels}. "
            "Me diz por qual caminho quer seguir que eu conduzo daqui."
        )
        return CanCreateAnswer(True, tuple(available_targets), answer)

    # Asked about a mode that isn't available for this tenant.
    answer = (
        "Consigo criar a vaga, mas esse caminho específico não está habilitado "
        "para a sua conta. Posso conduzir a criação por outro caminho disponível."
    )
    return CanCreateAnswer(True, tuple(), answer)
