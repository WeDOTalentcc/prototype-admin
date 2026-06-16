"""Task #1123 — Sentinela arquitetural: NUNCA hardcode literal Haiku.

A canonical Haiku model constant ``CANONICAL_HAIKU_MODEL`` vive em
``lia-agent-system/app/shared/llm_models.py``. O literal antigo
``"claude-3-5-haiku-20241022"`` retorna ``UNSUPPORTED_MODEL`` no
modelfarm proxy local (localhost:1106) — qualquer reintrodução
faz o ``IntakeIntentClassifier`` e o ``WizardGateClassifier``
fail-OPEN silenciosamente em todo turno (origem do bug do wizard
non-conversacional auditado em D-2026-05).

Esta sentinela escaneia ``lia-agent-system/app/`` por ocorrências
do literal e falha o build se encontrar fora de:

  - ``app/shared/llm_models.py`` (único arquivo canônico)
  - Comentários (linhas iniciando com ``#`` após strip)
  - Strings de docstring/explicação histórica claramente marcadas

Esquece-se de centralizar? O CI falha aqui antes de chegar em
produção.
"""
from __future__ import annotations

import re
from pathlib import Path

# Literais proibidos fora do módulo canônico.
_FORBIDDEN_HAIKU = "claude-3-5-haiku-20241022"
_FORBIDDEN_PATTERN = re.compile(re.escape(_FORBIDDEN_HAIKU))

# Único arquivo onde o literal canônico (CANONICAL_HAIKU_MODEL = "...")
# pode ser definido como string. Não confundir com o valor atual:
# ``CANONICAL_HAIKU_MODEL`` aponta para ``claude-haiku-4-5-20251001``,
# então o literal proibido NÃO deve aparecer nem aqui.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_APP_ROOT = _REPO_ROOT / "lia-agent-system" / "app"


def _is_comment_or_doc(line: str) -> bool:
    """Linhas de comentário Python (``#``) ou docstring são permitidas
    (referência histórica). Identificamos heuristicamente.
    """
    stripped = line.strip()
    if stripped.startswith("#"):
        return True
    # Linhas dentro de docstring são difíceis de classificar
    # estaticamente; aceitamos qualquer linha cujo literal apareça
    # em comentário rationale (palavras-chave históricas).
    lower = stripped.lower()
    historical_markers = (
        "antigo", "anterior", "histórico", "historico", "legacy",
        "deprecated", "task #1123", "task #1089",
    )
    return any(marker in lower for marker in historical_markers)


def test_no_hardcoded_haiku_model_in_app_tree() -> None:
    """Falha se algum ``.py`` dentro de ``lia-agent-system/app/`` contém o
    literal proibido fora de comentários/docstring rationale.
    """
    violations: list[str] = []
    if not _APP_ROOT.exists():
        # Estrutura inesperada — fail-loud para revisar layout.
        raise AssertionError(f"App root not found: {_APP_ROOT}")

    for py in _APP_ROOT.rglob("*.py"):
        # Permitido apenas no módulo canônico (referência histórica em
        # comentário/docstring). O VALOR atual da constante NÃO é o
        # literal proibido — então mesmo aqui esperamos zero matches
        # fora de comentário.
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not _FORBIDDEN_PATTERN.search(text):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _FORBIDDEN_PATTERN.search(line) and not _is_comment_or_doc(line):
                rel = py.relative_to(_REPO_ROOT)
                violations.append(f"{rel}:{lineno}: {line.strip()[:200]}")

    if violations:
        raise AssertionError(
            "Hardcoded Haiku literal detected (Task #1123 — use "
            "app.shared.llm_models.CANONICAL_HAIKU_MODEL instead):\n  "
            + "\n  ".join(violations)
        )


def test_canonical_module_exists_and_exports() -> None:
    """Importa o módulo canônico e garante que os símbolos esperados
    estão exportados com valores não-vazios.
    """
    from app.shared.llm_models import (
        CANONICAL_HAIKU_MODEL,
        CANONICAL_SONNET_MODEL,
    )
    assert isinstance(CANONICAL_HAIKU_MODEL, str) and CANONICAL_HAIKU_MODEL
    assert isinstance(CANONICAL_SONNET_MODEL, str) and CANONICAL_SONNET_MODEL
    # Sanity: o canônico atual não pode ser o literal proibido (regressão).
    assert CANONICAL_HAIKU_MODEL != _FORBIDDEN_HAIKU
