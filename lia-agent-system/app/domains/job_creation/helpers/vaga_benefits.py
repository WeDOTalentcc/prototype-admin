"""Contrato canonical do "beneficio da vaga" (snapshot + referencia).

Por que existe (2026-05-31): a area de beneficios da vaga guardava apenas
`List[str]` / `{id,name}`, perdendo todo o metadado rico do catalogo
(`CompanyBenefit`: categoria, valor, escopo de senioridade/contrato/dept). Este
modulo define o shape unico `VagaBenefit` (snapshot do catalogo no momento do
vinculo + referencia `benefit_id`) e o parser backward-compat que aceita os
formatos legados sem NUNCA descartar um item (fail-loud: item desconhecido vira
`inline`, jamais sumindo silenciosamente).

Espelha o padrao snapshot+ref ja usado em eligibility_question_template
(`customize_master`: copia o `data` do master + mantem `parent_template_id`).
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

BenefitSource = Literal["catalog", "inline"]

# Campos do CompanyBenefit copiados para o snapshot da vaga (escopo + display).
_SNAPSHOT_FIELDS = (
    "name", "description", "category", "icon",
    "value_type", "value", "percentage_value", "value_details",
    "seniority_levels", "contract_types", "departments",
    "is_highlighted", "is_mandatory",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VagaBenefit(BaseModel):
    """Beneficio vinculado a uma vaga. Snapshot dos campos do catalogo +
    referencia opcional ao CompanyBenefit de origem."""

    model_config = ConfigDict(extra="ignore")  # tolerante a ruido legado no read

    benefit_id: Optional[str] = None  # ref ao CompanyBenefit; None = inline puro
    source: BenefitSource = "inline"

    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None

    value_type: Optional[str] = None
    value: Optional[float] = None
    percentage_value: Optional[float] = None
    value_details: Optional[str] = None

    # snapshot do escopo de elegibilidade (para exibicao/analytics; nao re-filtra)
    seniority_levels: List[str] = Field(default_factory=list)
    contract_types: List[str] = Field(default_factory=list)
    departments: Dict[str, Any] = Field(default_factory=dict)

    is_highlighted: bool = False
    is_mandatory: bool = False

    attached_at: str = Field(default_factory=_utcnow_iso)
    # ajustes especificos da vaga sobre o snapshot (nao alteram o catalogo)
    catalog_overrides: Optional[Dict[str, Any]] = None


def snapshot_from_catalog(
    benefit: Any,
    *,
    overrides: Optional[Dict[str, Any]] = None,
) -> VagaBenefit:
    """Cria um VagaBenefit a partir de um CompanyBenefit (ORM ou dict),
    copiando os campos de snapshot e mantendo a referencia `benefit_id`."""
    get = (benefit.get if isinstance(benefit, dict) else lambda k, d=None: getattr(benefit, k, d))
    data: Dict[str, Any] = {f: get(f) for f in _SNAPSHOT_FIELDS}
    data = {k: v for k, v in data.items() if v is not None}
    if overrides:
        data.update(overrides)
    return VagaBenefit(
        benefit_id=str(get("id")) if get("id") is not None else None,
        source="catalog",
        attached_at=_utcnow_iso(),
        catalog_overrides=overrides or None,
        **data,
    )


def _coerce_one(item: Union[str, dict, VagaBenefit]) -> Optional[VagaBenefit]:
    if isinstance(item, VagaBenefit):
        return item
    # legado: beneficio como string solta -> inline
    if isinstance(item, str):
        name = item.strip()
        return VagaBenefit(name=name, source="inline") if name else None
    if isinstance(item, dict):
        bid = item.get("benefit_id") or item.get("id")
        bid = str(bid) if bid else None
        name = (item.get("name") or "").strip()
        if not name and not bid:
            return None  # nada utilizavel, mas tambem nada a preservar
        payload = dict(item)
        payload.pop("id", None)
        payload["benefit_id"] = bid
        payload["name"] = name or "(sem nome)"
        # source: se ha referencia ao catalogo -> catalog, senao inline
        payload["source"] = item.get("source") or ("catalog" if bid else "inline")
        return VagaBenefit(**payload)
    return None


def parse_vaga_benefits(raw: Any) -> List[VagaBenefit]:
    """Normaliza o shape de beneficios da vaga (aceita formatos legados).

    Aceita: None, str unica, lista de (str | {id,name,...} | VagaBenefit | dict
    completo). NUNCA descarta um item com conteudo: item com `benefit_id`
    invalido/ausente cai para `inline` em vez de sumir.
    """
    if raw is None:
        return []
    if isinstance(raw, (str, dict, VagaBenefit)):
        raw = [raw]
    out: List[VagaBenefit] = []
    for item in raw:
        try:
            vb = _coerce_one(item)
        except Exception:
            # fail-loud sem perder o dado: preserva como inline pelo str()
            name = str(item).strip()
            vb = VagaBenefit(name=name, source="inline") if name else None
        if vb is not None:
            out.append(vb)
    return out


def vaga_benefits_to_jsonb(benefits: List[VagaBenefit]) -> List[dict]:
    """Serializa para persistencia na coluna JSONB `job_vacancies.benefits`."""
    return [b.model_dump() for b in benefits]


def to_rails_names(raw: Any) -> List[str]:
    """Compat Rails: lista de nomes (string) derivada dos VagaBenefit.

    O caminho de publish dev-local persiste o shape rico; o Rails (fora de foco)
    recebe apenas os nomes para nao quebrar com o schema novo.
    """
    return [b.name for b in parse_vaga_benefits(raw) if b.name]
