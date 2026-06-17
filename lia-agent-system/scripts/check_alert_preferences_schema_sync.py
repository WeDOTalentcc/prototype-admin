"""Schema-sync sensor: alert_preferences catalog ↔ detector contract.

ADR-WT-2025 (2026-05-22): AlertPreference é canonical para threshold detectors.
Cada detector em _DETECTOR_ALERT_TYPE_MAP precisa ter o alert_type correspondente
em DEFAULT_ALERT_PREFERENCES (catálogo seed do UI catálogo) E ter default em
_DEFAULT_TENANT_OVERRIDE (fallback quando tenant não tem row).

Sem isso, detector roda, mas UI catálogo (PUT /alerts/preferences) não tem entry,
então usuário NÃO consegue customizar — ghost setting inverso (consumer existe,
UI falta).

Mode:
  - Default: warn-only (exit 0 mesmo se houver mismatches).
  - Com --strict: BLOCKING (exit 1 em qualquer mismatch).
  - Baseline target: zero mismatches → promover pra strict no CI.

Uso:
  python scripts/check_alert_preferences_schema_sync.py
  python scripts/check_alert_preferences_schema_sync.py --strict

Output otimizado pra LLM (PT-BR + fix sugerido inline).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ALERTS_PY = REPO_ROOT / "app" / "api" / "v1" / "alerts.py"
DETECTOR_PY = REPO_ROOT / "app" / "shared" / "services" / "proactive_detector_service.py"


def _extract_alert_types_from_default_prefs(src: str) -> set[str]:
    """Parse DEFAULT_ALERT_PREFERENCES = [...] and extract alert_type values."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_ALERT_PREFERENCES":
                    if isinstance(node.value, ast.List):
                        out: set[str] = set()
                        for elt in node.value.elts:
                            if not isinstance(elt, ast.Dict):
                                continue
                            for k, v in zip(elt.keys, elt.values):
                                if (
                                    isinstance(k, ast.Constant)
                                    and k.value == "alert_type"
                                    and isinstance(v, ast.Constant)
                                    and isinstance(v.value, str)
                                ):
                                    out.add(v.value)
                        return out
    return set()


def _extract_map_values(src: str, var_name: str) -> set[str]:
    """Parse a dict literal var_name: dict[str, str] = {...} returning the set of values."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == var_name:
            value = node.value
            if isinstance(value, ast.Dict):
                out: set[str] = set()
                for v in value.values:
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        out.add(v.value)
                return out
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    value = node.value
                    if isinstance(value, ast.Dict):
                        out2: set[str] = set()
                        for v in value.values:
                            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                                out2.add(v.value)
                        return out2
    return set()


def _extract_default_override_keys(src: str) -> set[str]:
    """Parse _DEFAULT_TENANT_OVERRIDE keys (detector names).

    Suporta dois formatos:
      1. Dict literal estatico: _DEFAULT_TENANT_OVERRIDE = {"name": ...}.
      2. Builder dinamico: _DEFAULT_TENANT_OVERRIDE = _build_default_tenant_overrides()
         — a funcao itera _DETECTOR_ALERT_TYPE_MAP.items() e cria um override por
         detector, entao a cobertura == chaves do map POR CONSTRUCAO.
    (Fix 2026-06-05: sensor era stale apos refactor do epico de detectores p/ builder.)
    """
    def _from_value(value):
        if isinstance(value, ast.Dict):
            return {
                k.value
                for k in value.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "_build_default_tenant_overrides"
        ):
            return _extract_map_keys(src, "_DETECTOR_ALERT_TYPE_MAP")
        return None

    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_DEFAULT_TENANT_OVERRIDE":
            r = _from_value(node.value)
            if r is not None:
                return r
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_DEFAULT_TENANT_OVERRIDE":
                    r = _from_value(node.value)
                    if r is not None:
                        return r
    return set()


def _extract_map_keys(src: str, var_name: str) -> set[str]:
    """Parse a dict literal returning the set of keys."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == var_name:
            value = node.value
            if isinstance(value, ast.Dict):
                out: set[str] = set()
                for k in value.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        out.add(k.value)
                return out
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    value = node.value
                    if isinstance(value, ast.Dict):
                        out2: set[str] = set()
                        for k in value.keys:
                            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                                out2.add(k.value)
                        return out2
    return set()


def main() -> int:
    strict = "--strict" in sys.argv

    if not ALERTS_PY.exists():
        print(f"[skip] {ALERTS_PY} não encontrado (ambiente não-canonical?)")
        return 0
    if not DETECTOR_PY.exists():
        print(f"[skip] {DETECTOR_PY} não encontrado")
        return 0

    alerts_src = ALERTS_PY.read_text(encoding="utf-8")
    detector_src = DETECTOR_PY.read_text(encoding="utf-8")

    catalog_types = _extract_alert_types_from_default_prefs(alerts_src)
    detector_map_values = _extract_map_values(detector_src, "_DETECTOR_ALERT_TYPE_MAP")
    detector_map_keys = _extract_map_keys(detector_src, "_DETECTOR_ALERT_TYPE_MAP")
    default_override_keys = _extract_default_override_keys(detector_src)

    print(f"[info] DEFAULT_ALERT_PREFERENCES catalog: {len(catalog_types)} alert_types")
    print(f"[info] _DETECTOR_ALERT_TYPE_MAP values:  {len(detector_map_values)} alert_types")
    print(f"[info] _DETECTOR_ALERT_TYPE_MAP keys:    {len(detector_map_keys)} detector names")
    print(f"[info] _DEFAULT_TENANT_OVERRIDE keys:    {len(default_override_keys)} detector names")

    violations: list[str] = []

    # R1: Toda alert_type usada por detector MUST estar em catálogo (senão UI não permite customizar)
    detector_uses_not_in_catalog = detector_map_values - catalog_types
    if detector_uses_not_in_catalog:
        for atype in sorted(detector_uses_not_in_catalog):
            violations.append(
                f"R1 schema-sync: detector usa alert_type '{atype}' (em _DETECTOR_ALERT_TYPE_MAP) "
                f"mas catálogo DEFAULT_ALERT_PREFERENCES em app/api/v1/alerts.py NÃO tem entry. "
                f"Fix: adicionar entry com {{alert_type: '{atype}', name: ..., description: ..., "
                f"threshold, channels, cooldown_hours}}."
            )

    # R2: Detector names em _DETECTOR_ALERT_TYPE_MAP MUST ter default em _DEFAULT_TENANT_OVERRIDE
    map_keys_missing_default = detector_map_keys - default_override_keys
    if map_keys_missing_default:
        for name in sorted(map_keys_missing_default):
            violations.append(
                f"R2 schema-sync: detector '{name}' em _DETECTOR_ALERT_TYPE_MAP "
                f"mas SEM entry em _DEFAULT_TENANT_OVERRIDE. "
                f"Fix: adicionar TenantThresholdOverride(is_enabled=..., threshold=..., cooldown_hours=...) "
                f"em proactive_detector_service.py:_DEFAULT_TENANT_OVERRIDE."
            )

    # R3: Reverse — _DEFAULT_TENANT_OVERRIDE não pode ter detector name que não está em _DETECTOR_ALERT_TYPE_MAP
    default_missing_map = default_override_keys - detector_map_keys
    if default_missing_map:
        for name in sorted(default_missing_map):
            violations.append(
                f"R3 schema-sync: detector '{name}' tem default em _DEFAULT_TENANT_OVERRIDE "
                f"mas NÃO está em _DETECTOR_ALERT_TYPE_MAP. "
                f"Fix: adicionar mapping {name} -> alert_type em _DETECTOR_ALERT_TYPE_MAP, "
                f"ou remover entry orfã de _DEFAULT_TENANT_OVERRIDE."
            )

    if violations:
        print(f"\n[FAIL] {len(violations)} schema-sync violation(s):")
        for v in violations:
            print(f"  - {v}")
        if strict:
            return 1
        else:
            print("\n[warn-only mode] use --strict para falhar o build")
            return 0

    print("\n[OK] alert_preferences schema-sync: catalog ↔ detector contract aligned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
