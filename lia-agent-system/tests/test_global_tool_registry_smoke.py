"""
F12 smoke — pre-#351 canary state for `app/shared/global_tool_registry.py`.

Em 2026-04 (Task #350) o módulo `app.shared.global_tool_registry` foi deletado
após auditoria que confirmou zero callers em produção. Este teste é o canário
arquitetural enquanto a Task #351 não decide o destino final do conceito de
"global tool registry":

    - Estado canônico atual: módulo NÃO EXISTE → este teste passa silenciosamente.
    - Se o módulo voltar a existir (alguém recriou, talvez via merge): o teste
      exige que `_registry == {}` no boot. Isso prova que continua sendo "morto"
      e nenhuma rota canônica está dependendo dele.

Como evoluir conforme #351:
    - Decisão "ATIVAR" → inverter a asserção para exigir `_registry != {}` e
      garantir registro via lifecycle, removendo a parte do `not exists`.
    - Decisão "DELETAR" definitivamente → remover este arquivo de teste.

Cross-reference:
    - `tests/fitness/test_audit_2026_04_finals.py::TestF12GlobalToolRegistryDeadCanary`
      cobre o caso de "voltou a existir mas tem 0 callers" (anti-zumbi).
    - Esta smoke complementa exigindo o invariante de boot vazio quando o
      módulo está presente.
    - `scripts/check_forbidden_imports.py` bloqueia novos imports do módulo.
"""
from __future__ import annotations

import importlib
from pathlib import Path

_APP = Path(__file__).resolve().parent.parent / "app"
_MODULE_PATH = _APP / "shared" / "global_tool_registry.py"


def test_global_tool_registry_canonical_state():
    """Canário pré-#351: módulo deletado OU registry vazio no boot."""
    if not _MODULE_PATH.exists():
        # Estado canônico atual (Task #350). Nada a verificar.
        return

    # Se voltou a existir, exigimos invariante de boot: registry vazio.
    mod = importlib.import_module("app.shared.global_tool_registry")
    registry = getattr(mod, "_registry", None)
    assert registry is not None, (
        "Módulo `app.shared.global_tool_registry` voltou a existir mas não "
        "expõe atributo `_registry`. Defina o invariante explicitamente "
        "antes de reativar (F12 — pre-#351 canary)."
    )
    assert registry == {}, (
        f"Pre-#351 canary violado: `_registry` deveria estar vazio no boot, "
        f"mas tem {len(registry)} entrada(s): {list(registry.keys())[:5]}. "
        "Decida #351 (ativar com lifecycle real OU deletar) antes de popular."
    )
