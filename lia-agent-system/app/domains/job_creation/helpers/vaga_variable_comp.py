"""Contrato canonical da "verba variavel da vaga" (snapshot + referencia).

Espelha vaga_benefits.py: liga o catalogo CompensationComponent a vaga
preservando o que foi ofertado (snapshot) + referencia `component_id`. Parser
backward-compat NUNCA descarta item (desconhecido vira inline). Persistido na
coluna JSONB job_vacancies.variable_compensation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

CompSource = Literal["catalog", "inline"]

_SNAPSHOT_FIELDS = (
    "kind", "name", "description", "icon",
    "value_type", "target_pct", "min_pct", "max_pct",
    "min_amount", "max_amount", "currency", "frequency", "trigger", "spec",
    "seniority_levels", "contract_types", "departments", "subsidiaries",
    "is_highlighted",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VagaCompComponent(BaseModel):
    """Verba variavel vinculada a uma vaga (snapshot do catalogo + ref)."""

    model_config = ConfigDict(extra="ignore")

    component_id: Optional[str] = None
    source: CompSource = "inline"

    kind: str = "bonus"
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

    value_type: Optional[str] = None
    target_pct: Optional[float] = None
    min_pct: Optional[float] = None
    max_pct: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    frequency: Optional[str] = None
    trigger: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None

    seniority_levels: List[str] = Field(default_factory=list)
    contract_types: List[str] = Field(default_factory=list)
    departments: Dict[str, Any] = Field(default_factory=dict)
    subsidiaries: List[Any] = Field(default_factory=list)

    is_highlighted: bool = False
    attached_at: str = Field(default_factory=_utcnow_iso)
    catalog_overrides: Optional[Dict[str, Any]] = None


def snapshot_from_catalog(component: Any, *, overrides: Optional[Dict[str, Any]] = None) -> VagaCompComponent:
    get = (component.get if isinstance(component, dict) else lambda k, d=None: getattr(component, k, d))
    data: Dict[str, Any] = {f: get(f) for f in _SNAPSHOT_FIELDS}
    data = {k: v for k, v in data.items() if v is not None}
    if overrides:
        data.update(overrides)
    return VagaCompComponent(
        component_id=str(get("id")) if get("id") is not None else None,
        source="catalog",
        attached_at=_utcnow_iso(),
        catalog_overrides=overrides or None,
        **data,
    )


def _coerce_one(item: Union[str, dict, VagaCompComponent]) -> Optional[VagaCompComponent]:
    if isinstance(item, VagaCompComponent):
        return item
    if isinstance(item, str):
        name = item.strip()
        return VagaCompComponent(name=name, source="inline") if name else None
    if isinstance(item, dict):
        cid = item.get("component_id") or item.get("id")
        cid = str(cid) if cid else None
        name = (item.get("name") or "").strip()
        if not name and not cid:
            return None
        payload = dict(item)
        payload.pop("id", None)
        payload["component_id"] = cid
        payload["name"] = name or "(sem nome)"
        payload["source"] = item.get("source") or ("catalog" if cid else "inline")
        return VagaCompComponent(**payload)
    return None


def parse_vaga_variable_comp(raw: Any) -> List[VagaCompComponent]:
    """Normaliza o shape (aceita legado). NUNCA descarta item com conteudo."""
    if raw is None:
        return []
    if isinstance(raw, (str, dict, VagaCompComponent)):
        raw = [raw]
    out: List[VagaCompComponent] = []
    for item in raw:
        try:
            vc = _coerce_one(item)
        except Exception:
            name = str(item).strip()
            vc = VagaCompComponent(name=name, source="inline") if name else None
        if vc is not None:
            out.append(vc)
    return out


def vaga_variable_comp_to_jsonb(items: List[VagaCompComponent]) -> List[dict]:
    return [c.model_dump() for c in items]
