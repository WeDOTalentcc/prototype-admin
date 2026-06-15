from app.middleware.request_id import get_correlation_id
from typing import Literal
"""
Company Benefits API endpoints.
CRUD operations for company-specific benefits management.
Migration 191 (2026-05-24): filiais, validade, historico, upload-extract.
"""
import json
import logging
import uuid as _uuid_module
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.company.repositories.company_benefit_repository import (
    CompanyBenefitRepository,
)
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel

# ============================================================================
# TAXONOMY LITERALS — single source of truth: benefits_service canonical v2
# ============================================================================
# Aceita 14 categorias canonical + 2 legacy aliases (quality_life, security)
# para backward-compat com dados antigos. resolve_benefit_category() normaliza
# no read path; aqui no write path apenas validamos contra o set conhecido.
BenefitCategoryLiteral = Literal[
    "health", "wellness", "food", "transport", "education",
    "financial", "retirement", "family", "parental", "flexibility",
    "equipment", "culture", "recognition", "other",
    # Legacy aliases (mantidos para backward-compat)
    "quality_life", "security",
]

BenefitValueTypeLiteral = Literal[
    "monetary", "percentage", "match", "reimbursement", "coverage", "informative",
]

router = APIRouter(prefix="/company/benefits", tags=["company-benefits"])
logger = logging.getLogger(__name__)


# Protected eligibility terms (LGPD + CLAUDE.md Fairness non-negotiable rule)
PROHIBITED_ELIGIBILITY_TERMS: frozenset[str] = frozenset({
    "genero", "genero", "sexo", "feminino", "masculino", "homem", "mulher",
    "raca", "raca", "etnia", "cor", "negro", "branco", "pardo",
    "idade", "jovem", "idoso", "velho", "anos",
    "religiao", "religiao", "catolico", "evangelico", "judeu",
    "estado_civil", "casado", "solteiro", "divorciado",
    "saude", "saude", "deficiencia", "gestante", "gravida",
    "gender", "sex", "male", "female",
    "race", "ethnicity", "color",
    "age", "young", "old", "senior_citizen",
    "religion", "religious",
    "marital", "married", "single",
    "health", "disability", "pregnancy", "pregnant",
})


def _check_fairness_eligibility(field_name: str, value) -> None:
    if value is None:
        return
    if isinstance(value, (list, tuple, set)):
        terms = {str(v).lower() for v in value}
    elif isinstance(value, dict):
        terms = {str(k).lower() for k in value}
    else:
        terms = {str(value).lower()}
    hits = terms & PROHIBITED_ELIGIBILITY_TERMS
    if hits:
        raise ValueError(
            f"FAIRNESS VIOLATION: campo {repr(field_name)} contém termos discriminatorios "
            f"{sorted(hits)}. Beneficios nao podem ter elegibilidade por atributo protegido "
            f"(LGPD Art. 11, CLAUDE.md #2/#3). Remova os termos e use criterios neutros "
            f"como cargo, nivel seniority canonical, ou tipo de contrato."
        )


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SubsidiaryEntry(BaseModel):
    """Filial aplicavel a um beneficio."""
    name: str
    cnpj: str | None = None


class CompanyBenefitCreate(WeDoBaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: BenefitCategoryLiteral | None = None
    description: str | None = None
    icon: str | None = None
    value: float | None = None
    percentage_value: float | None = None
    value_type: str | None = "informative"
    value_details: str | None = None
    applicable_to: list | None = None
    seniority_levels: list | None = None
    contract_types: list | None = None
    departments: dict | list | None = None
    provider: str | None = None
    provider_contact: str | None = None
    provider_cnpj: str | None = None  # migration 191
    subsidiaries: list[SubsidiaryEntry] | None = None  # migration 191
    valid_from: date | None = None  # migration 191
    valid_until: date | None = None  # migration 191
    review_frequency_months: int | None = None  # migration 191
    next_review_date: date | None = None  # migration 191
    waiting_period_days: int | None = None
    is_mandatory: bool = False
    is_discount: bool = False
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0

    from pydantic import model_validator

    @model_validator(mode="after")
    def validate_value_by_type(self) -> "CompanyBenefitCreate":
        vt = self.value_type or "informative"
        if vt == "monetary" and self.value is None:
            raise ValueError(
                "INVALID: value_type=monetary exige o campo value (valor numerico). "
                "Defina value=<float> ou mude value_type para informative."
            )
        if vt == "percentage" and self.percentage_value is None:
            raise ValueError(
                "INVALID: value_type=percentage exige o campo percentage_value. "
                "Defina percentage_value=<float> ou mude value_type."
            )
        if vt == "informative" and self.value_details is None and self.description is None:
            raise ValueError(
                "INVALID: value_type=informative exige value_details ou description. "
                "Adicione uma descricao textual do beneficio."
            )
        return self

    @model_validator(mode="after")
    def validate_fairness_eligibility(self) -> "CompanyBenefitCreate":
        _check_fairness_eligibility("applicable_to", self.applicable_to)
        _check_fairness_eligibility("seniority_levels", self.seniority_levels)
        _check_fairness_eligibility("contract_types", self.contract_types)
        _check_fairness_eligibility("departments", self.departments)
        return self


class CompanyBenefitUpdate(WeDoBaseModel):
    name: str | None = None
    category: BenefitCategoryLiteral | None = None
    description: str | None = None
    icon: str | None = None
    value: float | None = None
    value_type: BenefitValueTypeLiteral | None = None
    is_active: bool | None = None
    is_highlighted: bool | None = None
    order: int | None = None
    # New fields — migration 191
    provider_cnpj: str | None = None
    subsidiaries: list[SubsidiaryEntry] | None = None
    valid_from: date | None = None
    valid_until: date | None = None
    review_frequency_months: int | None = None
    next_review_date: date | None = None


class BenefitHistoryEntry(BaseModel):
    id: str
    changed_at: str
    changed_by: str | None = None
    change_type: str
    previous_snapshot: dict | None = None
    change_notes: str | None = None

    class Config:
        from_attributes = True


class CompanyBenefitResponse(BaseModel):
    id: str
    company_id: str
    name: str
    category: BenefitCategoryLiteral | None = None
    description: str | None = None
    icon: str | None = None
    value: float | None = None
    percentage_value: float | None = None
    value_type: BenefitValueTypeLiteral | None = None
    value_details: str | None = None
    applicable_to: list | None = None
    seniority_levels: list | None = None
    contract_types: list | None = None
    departments: str | None = None
    is_active: bool = True
    is_highlighted: bool = False
    order: int = 0
    # New fields — migration 191
    provider_cnpj: str | None = None
    subsidiaries: list | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    review_frequency_months: int | None = None
    next_review_date: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    history: list[BenefitHistoryEntry] | None = None
    # None fora do contexto de vaga; True/False quando consultado com criterios da vaga.
    matches_vaga: bool | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(b, history=None, matches_vaga=None) -> CompanyBenefitResponse:
    subs = getattr(b, "subsidiaries", None)
    if subs and not isinstance(subs, list):
        subs = None
    # Schema drift tolerance 2026-05-24: coluna `departments` foi alterada
    # de Text para jsonb em algum momento (seeders gravaram {} dict), mas o
    # response schema mantem str | None. Sem este normalize, GET /benefits/
    # devolve HTTP 500 em todo tenant que tem benefits seedados.
    # Migration canonical p/ normalizar a coluna fica como debito.
    deps_raw = getattr(b, "departments", None)
    if isinstance(deps_raw, (dict, list)):
        deps_resp = json.dumps(deps_raw) if deps_raw else None
    else:
        deps_resp = deps_raw
    return CompanyBenefitResponse(
        id=str(b.id),
        company_id=b.company_id,
        name=b.name,
        category=b.category,
        description=b.description,
        icon=b.icon,
        value=b.value,
        percentage_value=getattr(b, "percentage_value", None),
        value_type=b.value_type,
        value_details=getattr(b, "value_details", None),
        applicable_to=getattr(b, "applicable_to", None),
        seniority_levels=getattr(b, "seniority_levels", None),
        contract_types=getattr(b, "contract_types", None),
        departments=deps_resp,
        is_active=b.is_active,
        is_highlighted=b.is_highlighted,
        order=b.order,
        provider_cnpj=getattr(b, "provider_cnpj", None),
        subsidiaries=subs,
        valid_from=b.valid_from.isoformat() if getattr(b, "valid_from", None) else None,
        valid_until=b.valid_until.isoformat() if getattr(b, "valid_until", None) else None,
        review_frequency_months=getattr(b, "review_frequency_months", None),
        next_review_date=b.next_review_date.isoformat() if getattr(b, "next_review_date", None) else None,
        created_at=b.created_at.isoformat() if b.created_at else None,
        updated_at=b.updated_at.isoformat() if b.updated_at else None,
        history=history,
        matches_vaga=matches_vaga,
    )


def _build_prev_snapshot(b) -> dict:
    return {
        "name": b.name,
        "category": b.category,
        "description": b.description,
        "value": b.value,
        "value_type": b.value_type,
        "is_active": b.is_active,
        "is_highlighted": b.is_highlighted,
        "subsidiaries": getattr(b, "subsidiaries", None),
        "valid_from": b.valid_from.isoformat() if getattr(b, "valid_from", None) else None,
        "valid_until": b.valid_until.isoformat() if getattr(b, "valid_until", None) else None,
        "provider_cnpj": getattr(b, "provider_cnpj", None),
    }


async def _append_history(
    db,
    benefit_id,
    company_id: str,
    changed_by,
    change_type: str,
    previous_snapshot=None,
    change_notes=None,
) -> None:
    try:
        from lia_models.company_benefit import CompanyBenefitHistory
        entry = CompanyBenefitHistory(
            benefit_id=benefit_id,
            company_id=str(company_id),
            changed_by=changed_by,
            change_type=change_type,
            previous_snapshot=previous_snapshot,
            change_notes=change_notes,
        )
        db.add(entry)
    except Exception as hist_err:
        logger.error("History insert failed benefit_id=%s: %s", benefit_id, hist_err)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[CompanyBenefitResponse])
async def list_company_benefits(
    company_id: str | None = Query(None),
    category: str | None = Query(None),
    active_only: bool = Query(True),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — was: company_id or get_user_company_id(current_user) which used the raw query param and caused read/write tenant mismatch
        repo = CompanyBenefitRepository(db)
        benefits = await repo.list_for_company(
            effective_company_id,
            active_only=active_only,
            category=category,
            search=search,
        )
        return [_to_response(b) for b in benefits]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing company benefits: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/upload-extract", response_model=None)
async def upload_extract_benefits(
    file: UploadFile = File(...),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
):
    """
    Recebe um documento (Manual de Beneficios, PDF/DOCX/TXT) e extrai
    os beneficios usando LLM. Retorna lista de sugestoes para confirmacao.
    NAO persiste automaticamente — o usuario deve confirmar antes de salvar.
    Formatos suportados: .txt, .pdf (com texto selecionavel). Limite: 10 MB.
    """
    content = await file.read()
    if len(content) > 10_000_000:
        raise HTTPException(400, "Arquivo muito grande. Limite: 10MB.")

    text = ""
    fname = (file.filename or "").lower()
    if fname.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    elif fname.endswith(".pdf"):
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            text = content.decode("utf-8", errors="ignore")
        except Exception as pdf_err:
            logger.warning("PDF extraction failed (%s), fallback to raw decode", pdf_err)
            text = content.decode("utf-8", errors="ignore")
    else:
        text = content.decode("utf-8", errors="ignore")

    if len(text.strip()) < 50:
        raise HTTPException(
            422,
            "Nao foi possivel extrair texto do arquivo. "
            "Tente um arquivo .txt ou .pdf com texto selecionavel.",
        )

    prompt = f"""Analise o documento de beneficios abaixo e extraia uma lista estruturada.

DOCUMENTO:
{text[:8000]}

Retorne um JSON com a seguinte estrutura:
{{
  "benefits": [
    {{
      "name": "nome do beneficio",
      "category": "food|health|transport|financial|wellness|flexibility|education|family|other",
      "description": "descricao breve",
      "value": null,
      "value_type": "fixed|percentage|informative",
      "provider": null,
      "waiting_period_days": null,
      "is_mandatory": false
    }}
  ]
}}

Retorne APENAS o JSON, sem texto adicional."""

    try:
        from app.shared.providers.llm_factory import get_provider_for_tenant
        container = get_provider_for_tenant()
        raw = await container.generate_with_fallback(
            prompt,
            system="Voce e um especialista em RH. Extraia dados estruturados de beneficios corporativos.",
            company_id=str(company_id),
            domain="benefits",
            operation="upload_extract",
            agent_type="CompanyBenefitsAgent",
        )
        raw_stripped = raw.strip()
        if raw_stripped.startswith('```'):
            raw_stripped = raw_stripped.split('\n', 1)[-1]
            raw_stripped = raw_stripped.rsplit('```', 1)[0]
        data = json.loads(raw_stripped)
        extracted_benefits = data.get("benefits", [])
    except json.JSONDecodeError as jde:
        logger.error("LLM returned non-JSON for benefits extraction: %s", jde)
        raise HTTPException(503, "A IA nao retornou JSON valido. Tente novamente ou cadastre manualmente.")
    except Exception as llm_err:
        logger.error("LLM extraction failed: %s", llm_err, exc_info=True)
        raise HTTPException(
            503,
            f"Extracao por LLM falhou. Tente novamente ou cadastre manualmente. Detalhe: {str(llm_err)[:200]}",
        )

    return {
        "success": True,
        "extracted_count": len(extracted_benefits),
        "benefits": extracted_benefits,
        "message": f"{len(extracted_benefits)} beneficio(s) encontrado(s). Revise e confirme antes de salvar.",
        "source_chars": len(text),
    }


@router.post("/", response_model=CompanyBenefitResponse)
async def create_company_benefit(
    benefit: CompanyBenefitCreate,
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — was: company_id or get_user_company_id(current_user) which used the raw query param and caused read/write tenant mismatch
        repo = CompanyBenefitRepository(db)
        payload = benefit.model_dump()
        if payload.get("subsidiaries"):
            payload["subsidiaries"] = [
                s if isinstance(s, dict) else s.model_dump()
                for s in (payload["subsidiaries"] or [])
            ]
        # promote-back vaga->catalogo: nao duplica se ja existe (nome case-insensitive)
        existing = await repo.get_by_name_ci(effective_company_id, benefit.name)
        if existing is not None:
            logger.info(
                "Benefit dedup hit (promote-back) name=%s company=%s",
                benefit.name, effective_company_id,
            )
            return _to_response(existing)
        new_benefit = await repo.create(effective_company_id, payload)
        # pii-logs ok: new_benefit.name é nome de benefício (config metadata, não PII de pessoa)
        logger.info(f"Created company benefit: {new_benefit.name} for company: {effective_company_id}")

        await _append_history(
            db,
            benefit_id=new_benefit.id,
            company_id=str(effective_company_id),
            changed_by=getattr(current_user, "email", None) or getattr(current_user, "id", None),
            change_type="created",
            previous_snapshot=None,
        )

        try:
            from app.shared.compliance.audit_service import AuditService as _AS
            await _AS().log_action(
                trace_id=get_correlation_id(),
                company_id=str(effective_company_id),
                action_type="company_benefits_update",
                actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
                target_id=str(new_benefit.id),
                target_type="company_benefit",
                metadata={
                    "source": "rest_post_create_benefit",
                    "fields_updated": list(benefit.model_fields_set) if hasattr(benefit, "model_fields_set") else [],
                    "benefit_name": new_benefit.name,
                    "operation": "create",
                },
            )
        except Exception as _audit_err:
            logger.error("Audit log failed for company_benefits_update (create) company=%s: %s", effective_company_id, _audit_err)

        await db.commit()
        return _to_response(new_benefit)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating company benefit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/active", response_model=list[CompanyBenefitResponse])
async def list_active_company_benefits(
    company_id: str | None = Query(None),
    seniority_level: str | None = Query(None),
    department: str | None = Query(None),
    contract_type: str | None = Query(None),
    with_matches: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    """Must stay registered BEFORE /{benefit_id} to avoid path collision (regression bug B11)."""
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — was: company_id or get_user_company_id(current_user) which used the raw query param and caused read/write tenant mismatch
        if not effective_company_id or effective_company_id in ("default", "unknown"):
            return []
        repo = CompanyBenefitRepository(db)
        if with_matches or department or contract_type:
            # vaga: catalogo inteiro com flag matches_vaga (compativeis pre-marcados)
            pairs = await repo.list_matching(
                effective_company_id,
                seniority_level=seniority_level,
                department=department,
                contract_type=contract_type,
                active_only=True,
            )
            return [_to_response(b, matches_vaga=flag) for b, flag in pairs]
        # legado: filtra por senioridade (mantem comportamento de callers antigos)
        benefits = await repo.list_for_company(effective_company_id, active_only=True)
        if seniority_level and seniority_level != "all":
            benefits = [
                b for b in benefits
                if not b.seniority_levels
                or "all" in (b.seniority_levels or [])
                or seniority_level in (b.seniority_levels or [])
            ]
        return [_to_response(b) for b in benefits]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing active company benefits: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/highlighted", response_model=list[CompanyBenefitResponse])
async def list_highlighted_company_benefits(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    """Must stay declared BEFORE /{benefit_id} (route order)."""
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — was: company_id or get_user_company_id(current_user) which used the raw query param and caused read/write tenant mismatch
        if not effective_company_id or effective_company_id in ("default", "unknown"):
            return []
        repo = CompanyBenefitRepository(db)
        benefits = await repo.list_for_company(effective_company_id, active_only=True)
        return [_to_response(b) for b in benefits if b.is_highlighted]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing highlighted company benefits: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/summary", response_model=None)
async def get_company_benefits_summary(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    """AI-agent-friendly summary. Must stay declared BEFORE /{benefit_id}."""
    empty = {"total_count": 0, "active_count": 0, "highlighted_count": 0, "categories": {}, "formatted_text": "", "benefits": []}
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — was: company_id or get_user_company_id(current_user) which used the raw query param and caused read/write tenant mismatch
        if not effective_company_id or effective_company_id in ("default", "unknown"):
            return empty
        repo = CompanyBenefitRepository(db)
        all_benefits = await repo.list_for_company(effective_company_id, active_only=False)
        active_benefits = [b for b in all_benefits if b.is_active]
        highlighted_benefits = [b for b in active_benefits if b.is_highlighted]
        # Canonical labels from benefits_service SSOT (v2, 14 categories)
        categories: dict = {}
        for b in active_benefits:
            cat = b.category or "other"
            if cat not in categories:
                categories[cat] = {"name": BENEFIT_CATEGORIES.get(resolve_benefit_category(cat), cat), "count": 0, "benefits": []}
            categories[cat]["count"] += 1
            categories[cat]["benefits"].append({
                "name": b.name, "description": b.description, "value_type": b.value_type,
                "value": b.value, "percentage_value": b.percentage_value, "is_highlighted": b.is_highlighted,
            })
        formatted_lines = ["**Beneficios da Empresa:**"]
        for cat_data in categories.values():
            items = []
            for b in cat_data["benefits"]:
                if b["value_type"] == "monetary" and b["value"]:
                    items.append(f"{b['name']} (R\$ {b['value']:,.2f})")
                elif b["value_type"] == "percentage" and b["percentage_value"]:
                    items.append(f"{b['name']} ({b['percentage_value']}%)")
                else:
                    items.append(b["name"])
            if items:
                _sep = ", "
                formatted_lines.append("- " + cat_data['name'] + ": " + _sep.join(items))
        formatted_text = "\n".join(formatted_lines) if len(formatted_lines) > 1 else "Nenhum beneficio cadastrado."
        benefits_list = [
            {"id": str(b.id), "name": b.name, "description": b.description, "category": b.category,
             "value_type": b.value_type, "value": b.value, "percentage_value": b.percentage_value,
             "is_highlighted": b.is_highlighted}
            for b in active_benefits
        ]
        return {"total_count": len(all_benefits), "active_count": len(active_benefits),
                "highlighted_count": len(highlighted_benefits), "categories": categories,
                "formatted_text": formatted_text, "benefits": benefits_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company benefits summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{benefit_id}/history", response_model=list[BenefitHistoryEntry])
async def get_benefit_history(
    benefit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via require_company_id + company_id filter in WHERE
    """Retorna historico de alteracoes de um beneficio (max 50, mais recente primeiro)."""
    try:
        from lia_models.company_benefit import CompanyBenefitHistory
        result = await db.execute(
            select(CompanyBenefitHistory)
            .where(
                CompanyBenefitHistory.benefit_id == benefit_id,
                CompanyBenefitHistory.company_id == str(company_id),
            )
            .order_by(CompanyBenefitHistory.changed_at.desc())
            .limit(50)
        )
        rows = result.scalars().all()
        return [
            BenefitHistoryEntry(
                id=str(r.id),
                changed_at=r.changed_at.isoformat() if r.changed_at else "",
                changed_by=r.changed_by,
                change_type=r.change_type,
                previous_snapshot=r.previous_snapshot,
                change_notes=r.change_notes,
            )
            for r in rows
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching benefit history benefit_id=%s: %s", benefit_id, e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{benefit_id}", response_model=CompanyBenefitResponse)
async def get_company_benefit(
    benefit_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        return _to_response(benefit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company benefit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{benefit_id}", response_model=CompanyBenefitResponse)
async def update_company_benefit(
    benefit_id: UUID,
    updates: CompanyBenefitUpdate,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")

        prev_snapshot = _build_prev_snapshot(benefit)

        update_payload = updates.model_dump(exclude_unset=True)
        if "subsidiaries" in update_payload and update_payload["subsidiaries"]:
            update_payload["subsidiaries"] = [
                s if isinstance(s, dict) else s.model_dump()
                for s in update_payload["subsidiaries"]
            ]

        benefit = await repo.update(benefit, update_payload)
        # pii-logs ok: benefit.name é nome de benefício (config metadata, não PII de pessoa)
        logger.info(f"Updated company benefit: {benefit.name}")

        await _append_history(
            db,
            benefit_id=benefit.id,
            company_id=str(company_id),
            changed_by=getattr(current_user, "email", None) or getattr(current_user, "id", None),
            change_type="updated",
            previous_snapshot=prev_snapshot,
        )

        try:
            from app.shared.compliance.audit_service import AuditService as _AS
            await _AS().log_action(
                trace_id=get_correlation_id(),
                company_id=str(company_id),
                action_type="company_benefits_update",
                actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
                target_id=str(benefit_id),
                target_type="company_benefit",
                metadata={
                    "source": "rest_put_inline_edit",
                    "fields_updated": list(updates.model_fields_set) if hasattr(updates, "model_fields_set") else [],
                    "benefit_name": benefit.name,
                    "operation": "update",
                },
            )
        except Exception as _audit_err:
            logger.error("Audit log failed for company_benefits_update (update) company=%s: %s", company_id, _audit_err)

        await db.commit()
        return _to_response(benefit)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating company benefit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{benefit_id}", response_model=None)
async def delete_company_benefit(
    benefit_id: UUID,
    hard_delete: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        repo = CompanyBenefitRepository(db)
        benefit = await repo.get_by_id(benefit_id)
        if not benefit:
            raise HTTPException(status_code=404, detail="Benefit not found")
        if hard_delete:
            await repo.hard_delete(benefit)
            message = f"Benefit '{benefit.name}' permanently deleted"
        else:
            await _append_history(
                db,
                benefit_id=benefit.id,
                company_id=str(company_id),
                changed_by=getattr(current_user, "email", None) or getattr(current_user, "id", None),
                change_type="deactivated",
                previous_snapshot={"is_active": True},
            )
            await repo.soft_delete(benefit)
            message = f"Benefit '{benefit.name}' deactivated"
        logger.info(f"  {message}")

        try:
            from app.shared.compliance.audit_service import AuditService as _AS
            await _AS().log_action(
                trace_id=get_correlation_id(),
                company_id=str(company_id),
                action_type="company_benefits_update",
                actor=getattr(current_user, "email", None) or getattr(current_user, "id", "unknown"),
                target_id=str(benefit_id),
                target_type="company_benefit",
                metadata={
                    "source": "rest_delete_benefit",
                    "fields_updated": ["is_active"],
                    "operation": "hard_delete" if hard_delete else "soft_delete",
                    "message": message,
                },
            )
        except Exception as _audit_err:
            logger.error("Audit log failed for company_benefits_update (delete) company=%s: %s", company_id, _audit_err)

        return {"success": True, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting company benefit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/seed-defaults", response_model=None)
async def seed_default_benefits(
    company_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
gated_company_id: str = Depends(require_company_id_strict_match("query.company_id"))):
    try:
        effective_company_id = gated_company_id  # canonical client_account_id from JWT gate (auto-resolves company_profile_id) — was: company_id or get_user_company_id(current_user) which used the raw query param and caused read/write tenant mismatch
        repo = CompanyBenefitRepository(db)
        existing_count = await repo.count_for_company(effective_company_id)
        if existing_count > 0:
            return {"success": True, "message": f"Benefits already exist for company ({existing_count} benefits)", "created": 0, "total": existing_count}
        created_count = await repo.seed_defaults(effective_company_id)
        logger.info(f"Seeded {created_count} default benefits for company: {effective_company_id}")
        return {"success": True, "message": f"Successfully seeded {created_count} default benefits", "created": created_count, "total": created_count}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default benefits: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/categories/list", response_model=None)
async def list_benefit_categories(company_id: str = Depends(require_company_id)):
    """Taxonomy canonical v2 (14 categorias). Delegado a benefits_service canonical.

    multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143).
    canonical-fix: single source of truth em benefits_service.BENEFIT_CATEGORIES.
    """
    from app.domains.company.services.benefits_service import build_categories_response
    return build_categories_response()


@router.get("/value-types/list", response_model=None)
async def list_benefit_value_types(company_id: str = Depends(require_company_id)):
    """Tipos de valor canonical v2 (6 tipos: monetary, percentage, match, reimbursement, coverage, informative)."""
    from app.domains.company.services.benefits_service import build_value_types_response
    return build_value_types_response()


@router.get("/waiting-periods/list", response_model=None)
async def list_benefit_waiting_periods(company_id: str = Depends(require_company_id)):
    """Periodos de carencia canonical v2 (9 opcoes: 0/exp/30/60/90/180/365/540/730 dias)."""
    from app.domains.company.services.benefits_service import build_waiting_periods_response
    return build_waiting_periods_response()
