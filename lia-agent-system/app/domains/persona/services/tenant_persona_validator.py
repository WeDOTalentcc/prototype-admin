"""
Tenant persona override validator — canonical entry-point for any code that
accepts a YAML override blob that may modify the LIA persona for one tenant.

Registrado 2026-05-21 (audit P1-7 / E4-prep). Substitui o validator inline
em ``admin_prompts.py:_validate_yaml_payload`` + ``_scan_pii`` por um único
ponto que também garante **ethics invariants**.

## O que este módulo enforça

1. **YAML syntax válida** (yaml.safe_load não levanta)
2. **metadata.version presente** (T-05 enforcement)
3. **PII scan** (warnings, não bloqueia — comportamento existente preservado)
4. **Ethics invariants imutáveis** (NOVO): determinadas âncoras textuais
   referentes a compliance LGPD / fairness / anti-bias DEVEM continuar no
   override. Se o admin (WeDOTalent staff OU futuro caller automático)
   tentar enviar override que apague esses anchors, validator rejeita 422.

## Por que ethics invariants são âncoras textuais e não hash do bloco inteiro

Hash de bloco inteiro força admin a copiar-colar texto exato — friccional
e quebra com qualquer reordenação cosmética. Âncoras textuais são frases
ou termos curtos que precisam APARECER no override; admin pode reformular
a redação mas não pode apagar o conceito. Trade-off explícito: aceita
modificações superficiais, bloqueia remoção semântica.

A lista de âncoras vive aqui (versionada no código) — quando produto
decidir alterar o que é "imutável", a mudança vira commit reviewable em
vez de configuração silenciosa.

## Contract estável para o admin WeDOTalent (E4-prep)

Este validator é chamado pelo backend ANTES de qualquer write — o admin
WeDOTalent UI em ``admin2.wedotalent.cc`` não precisa replicar nenhuma
desta lógica. Eles enviam o YAML cru e recebem ou 200 (aceito) ou 422
(detail = quais invariants faltam, com fix suggestion).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import yaml


# ----------------------------------------------------------------------------
# Ethics invariants — anchor strings that MUST appear in any tenant override.
# Adding a new anchor is a deliberate product decision (a new commit). Each
# entry has a (anchor, friendly_name, fix_suggestion) tuple so the 422
# response can be actionable rather than cryptic.
# ----------------------------------------------------------------------------

@dataclass(frozen=True)
class EthicsInvariant:
    anchor: str
    friendly_name: str
    fix_suggestion: str


ETHICS_INVARIANTS: tuple[EthicsInvariant, ...] = (
    EthicsInvariant(
        anchor="Diretrizes Éticas",
        friendly_name="Bloco 'Diretrizes Éticas' (LGPD / fairness)",
        fix_suggestion=(
            "Preserve a seção 'Diretrizes Éticas (inegociáveis)' do persona "
            "canonical. Você pode reformular o texto mas não pode remover "
            "a seção — ela contém os critérios anti-bias exigidos por "
            "LGPD e EU AI Act."
        ),
    ),
    EthicsInvariant(
        anchor="IGNORE COMPLETAMENTE",
        friendly_name="Lista de fatores proibidos na avaliação",
        fix_suggestion=(
            "Mantenha a lista que começa com 'IGNORE COMPLETAMENTE' enumerando "
            "fatores proibidos (nome, idade, foto, etc.). Esses são gates "
            "anti-discriminação requeridos por compliance."
        ),
    ),
    EthicsInvariant(
        anchor="Linguagem inclusiva",
        friendly_name="Diretriz de linguagem inclusiva",
        fix_suggestion=(
            "Inclua a sub-seção 'Linguagem inclusiva' (linguagem neutra de "
            "gênero, sem estereótipos profissionais)."
        ),
    ),
    EthicsInvariant(
        anchor="Transparência",
        friendly_name="Bloco de Transparência (registro de pareceres)",
        fix_suggestion=(
            "Preserve a seção 'Transparência' — documentar critérios + "
            "explicar raciocínio + manter registro é requisito EU AI Act."
        ),
    ),
)


# Padrões PII canonical — alinha com app.shared.pii_masking.PII_PATTERNS.
# Replicamos a subset aqui para tornar este validator autocontido (admin
# integration contract não pode depender de imports internos profundos).
_PII_PATTERNS_FOR_OVERRIDE_SCAN: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("cpf", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")),
    ("cnpj", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("phone_br", re.compile(r"\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b")),
)


@dataclass
class ValidationResult:
    """Outcome of a single validator call.

    ``is_valid``: True iff no ``errors``. Warnings do NOT invalidate (legacy
    behavior preserved — PII matches were warning-only previously).

    Callers should raise HTTP 422 with ``errors`` as detail when invalid;
    warnings can be returned alongside a 200 so the staff editor can
    annotate the result inline.
    """

    is_valid: bool
    parsed_yaml: dict[str, Any] | None = None
    version: str | None = None
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)


def validate_tenant_persona_override(
    content: str,
    *,
    path: str | None = None,
) -> ValidationResult:
    """Single canonical validator for tenant-override YAML blobs.

    Args:
        content: Raw YAML text the caller wants to persist as a tenant
            override.
        path: Optional canonical path (e.g. ``shared/lia_persona``) — used
            only for log/error context.

    Returns:
        :class:`ValidationResult` with the parsed YAML (or None on syntax
        error), the metadata.version (or None), a list of structured errors
        (dict with ``code`` + ``message`` + ``fix`` keys when applicable),
        and a list of warnings.

    Never raises. Callers translate ``errors`` into HTTP 422.
    """
    result = ValidationResult(is_valid=True)
    path_label = f" (path={path})" if path else ""

    # Step 1: YAML syntax + structure
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        result.is_valid = False
        result.errors.append({
            "code": "yaml_syntax_error",
            "message": f"YAML inválido{path_label}: {exc}",
            "fix": "Corrija a sintaxe YAML (indentação, quotes, two-space indent).",
        })
        return result
    if not isinstance(parsed, dict):
        result.is_valid = False
        result.errors.append({
            "code": "yaml_not_object",
            "message": f"YAML root deve ser objeto/dict{path_label}.",
            "fix": "O arquivo deve começar com chaves no topo (metadata:, prompts:, ...).",
        })
        return result
    result.parsed_yaml = parsed

    # Step 2: metadata.version required (T-05)
    metadata = parsed.get("metadata")
    if not isinstance(metadata, dict):
        result.is_valid = False
        result.errors.append({
            "code": "metadata_missing",
            "message": "Bloco 'metadata' ausente ou não é um objeto.",
            "fix": "Adicione 'metadata:' com 'version', 'domain', e 'description'.",
        })
        return result
    version = metadata.get("version")
    if not version or not isinstance(version, str):
        result.is_valid = False
        result.errors.append({
            "code": "version_missing",
            "message": "'metadata.version' é obrigatório (string semver-like).",
            "fix": "Adicione 'version: \"1.0.0-tenant\"' (ou outro semver) no bloco metadata.",
        })
        return result
    result.version = version

    # Step 3: ethics invariants — REJECT if any anchor missing
    missing_anchors: list[EthicsInvariant] = []
    for inv in ETHICS_INVARIANTS:
        if inv.anchor not in content:
            missing_anchors.append(inv)
    if missing_anchors:
        result.is_valid = False
        for inv in missing_anchors:
            result.errors.append({
                "code": "ethics_invariant_missing",
                "message": (
                    f"Override remove o invariant '{inv.friendly_name}'. "
                    f"Esse bloco é imutável por compliance (LGPD / EU AI Act / "
                    f"anti-bias). Restaure antes de persistir."
                ),
                "fix": inv.fix_suggestion,
                "anchor": inv.anchor,
            })
        # We can still continue to surface PII warnings, but is_valid stays False.

    # Step 4: PII scan — warnings only (legacy posture preserved)
    for label, pattern in _PII_PATTERNS_FOR_OVERRIDE_SCAN:
        matches = pattern.findall(content)
        if matches:
            result.warnings.append({
                "code": f"pii_{label}",
                "message": (
                    f"Possível {label.upper()} no override "
                    f"({len(matches)} ocorrência(s))."
                ),
                "fix": (
                    "Verifique se a inclusão é intencional. Conteúdo "
                    "persistido em prompts é injetado em LLMs e pode vazar "
                    "em logs/eval — prefira placeholders."
                ),
            })

    return result


__all__ = [
    "ETHICS_INVARIANTS",
    "EthicsInvariant",
    "ValidationResult",
    "validate_tenant_persona_override",
]
