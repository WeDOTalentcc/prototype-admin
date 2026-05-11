"""
Company Settings Tools — D1.

LIA-callable tools for company profile management:
  - check_company_completeness — verify which profile fields are empty
  - suggest_recruiting_policy — baseline policy suggestion with FairnessGuard validation
  - import_benefits_from_data — bulk upsert company benefits
  - save_hiring_policy — persist hiring policy in company_hiring_policies (PR2 / Task #1002)

All tools use ToolExecutionContext for multi-tenant isolation.
suggest_recruiting_policy runs through FairnessGuard to prevent
discriminatory policies.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.tools.registry import ToolDefinition, tool_registry
from app.shared.compliance.fairness_guard import FairnessGuard
from app.shared.compliance.fairness_recursive import (
    RecursiveFairnessResult,
    validate_fairness_recursive,
)

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)

_fairness_guard = FairnessGuard()


def _fairness_violation_payload(
    result: RecursiveFairnessResult,
    *,
    fallback_field: str | None = None,
) -> dict[str, Any]:
    """PR3 (Task #1003) — formato canônico de resposta quando o
    FairnessGuard recursivo veta um payload nesse módulo. Espelha o helper
    em ``company_tool_registry.py``: a LIA verbaliza ``educational_message``
    + oferece reformulação inclusiva (rule #4 do YAML).
    """
    field_label = result.offending_field or fallback_field or "<root>"
    signal = result.offending_signal or ""
    base_msg = (
        result.educational_message
        or "Trecho com sinal de viés detectado pelo FairnessGuard."
    )
    return {
        "success": False,
        "reason": "fairness_violation",
        "offending_field": field_label,
        "offending_signal": signal,
        "category": result.category,
        "blocked_terms": result.blocked_terms or [],
        "message": (
            f"Bloqueio de compliance em '{field_label}': {base_msg} "
            f"Trecho sinalizado: «{signal}». Quer reescrever de forma inclusiva?"
        ),
    }


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    return kwargs.pop("_context", None)


COMPANY_CORE_FIELDS = [
    "name", "trading_name", "cnpj", "website", "industry",
    "company_size", "employee_count", "linkedin_url",
]

COMPANY_CULTURE_FIELDS = [
    "mission", "vision", "values", "work_model",
    "growth_opportunities",
]


# ───────────────────────────────────────────────────────────────────
# Tool 1 — check_company_completeness
# ───────────────────────────────────────────────────────────────────

async def check_company_completeness(**kwargs) -> dict[str, Any]:
    """
    Inspect which core fields of the company profile are empty.
    LIA uses this to offer proactive help (D10 proactivity).

    Returns:
        {
            "success": bool,
            "profile_completeness_pct": float,
            "culture_completeness_pct": float,
            "overall_pct": float,
            "missing_profile_fields": [str],
            "missing_culture_fields": [str],
            "recommendation": str,
            "has_website": bool,  # enables auto-scrape suggestion
        }
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    try:
        async with AsyncSessionLocal() as db:
            profile = await db.execute(
                text("""
                    SELECT name, trading_name, cnpj, website, industry,
                           company_size, employee_count, linkedin_url
                    FROM company_profiles
                    WHERE id::text = :cid
                    LIMIT 1
                """),
                {"cid": company_id},
            )
            prof_row = profile.mappings().first()

            culture = await db.execute(
                text("""
                    SELECT mission, vision, values, work_model, growth_opportunities
                    FROM company_culture_profiles
                    WHERE company_id::text = :cid
                    LIMIT 1
                """),
                {"cid": company_id},
            )
            cult_row = culture.mappings().first()

            missing_profile = []
            if prof_row:
                for f in COMPANY_CORE_FIELDS:
                    v = prof_row.get(f)
                    if v is None or v == "":
                        missing_profile.append(f)
            else:
                missing_profile = list(COMPANY_CORE_FIELDS)

            missing_culture = []
            if cult_row:
                for f in COMPANY_CULTURE_FIELDS:
                    v = cult_row.get(f)
                    if v is None or v == "" or (isinstance(v, list) and not v):
                        missing_culture.append(f)
            else:
                missing_culture = list(COMPANY_CULTURE_FIELDS)

            profile_pct = round(1.0 - len(missing_profile) / len(COMPANY_CORE_FIELDS), 2)
            culture_pct = round(1.0 - len(missing_culture) / len(COMPANY_CULTURE_FIELDS), 2)
            overall = round((profile_pct + culture_pct) / 2, 2)

            has_website = bool(prof_row and prof_row.get("website"))

            if overall >= 0.9:
                reco = "Perfil completo — pronto para buscas e triagens refinadas."
            elif has_website and len(missing_profile) + len(missing_culture) > 3:
                reco = (
                    "Perfil incompleto mas você tem website cadastrado. "
                    "Posso usar analyze_company_website para preencher automaticamente "
                    "nome/setor/cultura/benefícios via scraping."
                )
            elif not has_website:
                reco = (
                    f"Perfil {overall*100:.0f}% completo e sem website cadastrado. "
                    "Peça a URL da empresa ao recrutador para permitir auto-preenchimento. "
                    "Caminho: Menu → Configurações → Dados Básicos."
                )
            else:
                reco = (
                    f"Perfil {overall*100:.0f}% completo. "
                    "Navegar para Configurações para completar manualmente."
                )

            return {
                "success": True,
                "company_id": company_id,
                "profile_completeness_pct": profile_pct,
                "culture_completeness_pct": culture_pct,
                "overall_pct": overall,
                "missing_profile_fields": missing_profile,
                "missing_culture_fields": missing_culture,
                "has_website": has_website,
                "website": prof_row.get("website") if prof_row else None,
                "recommendation": reco,
            }
    except Exception as e:
        logger.error("check_company_completeness failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": "db_error",
            "message": f"Erro ao verificar perfil da empresa: {e}",
        }


# ───────────────────────────────────────────────────────────────────
# Tool 2 — suggest_recruiting_policy
# ───────────────────────────────────────────────────────────────────

RECRUITING_POLICY_TEMPLATES: dict[str, dict[str, Any]] = {
    "default": {
        "description": "Processo seletivo justo e estruturado",
        "stages": [
            "Triagem automática por WSI (70% técnico + 30% comportamental)",
            "Entrevista comportamental CBI/STAR via WhatsApp",
            "Entrevista técnica ou teste prático",
            "Entrevista final com gestor da área",
            "Proposta com transparência de faixa salarial",
        ],
        "principles": [
            "Decisões baseadas em critérios objetivos definidos na JD",
            "Fairness guard ativo: zero coleta de raça, religião, gênero, saúde",
            "Feedback transparente para candidatos aprovados e reprovados",
            "Diversidade via programas afirmativos estruturados quando aplicável",
            "Compliance LGPD Art. 20 (direito à explicação de decisões automatizadas)",
        ],
        "time_to_hire_days_target": 30,
    },
    "tech_startup": {
        "description": "Processo ágil para startups de tecnologia (< 50 funcionários)",
        "stages": [
            "Triagem WSI",
            "Conversa inicial com recrutador (30min)",
            "Entrevista técnica (live coding ou take-home)",
            "Conversa com o time (cultural fit)",
            "Proposta",
        ],
        "principles": [
            "Feedback em até 48h após cada etapa",
            "Transparência total sobre remuneração, equity e benefícios",
            "Zero discriminação por universidade, idade ou bairro de origem",
        ],
        "time_to_hire_days_target": 15,
    },
    "enterprise": {
        "description": "Processo estruturado para empresas enterprise (> 500 funcionários)",
        "stages": [
            "Triagem WSI + Dreyfus (níveis de expertise)",
            "Entrevista comportamental estruturada (CBI/STAR)",
            "Bateria técnica",
            "Entrevista com gestor",
            "Entrevista com diretoria/VP",
            "Proposta com benchmark de mercado",
        ],
        "principles": [
            "Painel de entrevistadores diverso (mín. 2 avaliadores por etapa)",
            "Decisão colegiada após todas etapas (reduz viés individual)",
            "Programa afirmativo ativo para D&I onde legalmente permitido",
            "Documentação completa de decisões (audit trail LGPD)",
        ],
        "time_to_hire_days_target": 60,
    },
}


async def suggest_recruiting_policy(
    sector: str | None = None,
    company_size: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    Suggest a baseline recruiting policy based on sector + company size.
    Every suggestion is validated through FairnessGuard to ensure
    no discriminatory criteria (gender, race, age, religion, disability, socioeconomic).

    Args:
        sector: e.g. "tecnologia", "saúde", "financeiro"
        company_size: "startup" | "small" | "medium" | "enterprise"

    Returns:
        {
            "success": bool,
            "template_used": str,
            "policy": {...},
            "fairness_check": {passed: bool, issues: [str]},
            "customization_notes": [str],
        }
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    # Pick template
    template_id = "default"
    normalized_size = (company_size or "").lower()
    if normalized_size in ("startup", "small") or "startup" in (sector or "").lower():
        template_id = "tech_startup"
    elif normalized_size in ("enterprise", "large", "big"):
        template_id = "enterprise"

    tmpl = RECRUITING_POLICY_TEMPLATES[template_id]
    policy = dict(tmpl)

    # Run fairness guard on the policy text
    try:
        policy_text = (
            policy.get("description", "")
            + " "
            + " ".join(policy.get("stages", []))
            + " "
            + " ".join(policy.get("principles", []))
        )
        fairness_result = _fairness_guard.check(policy_text)
        passed = not fairness_result.is_biased
        issues = (fairness_result.blocked_terms + fairness_result.soft_warnings) if not passed else []
    except Exception as e:
        logger.debug("Fairness check skipped: %s", e)
        passed = True
        issues = []

    notes: list[str] = []
    if sector:
        notes.append(f"Template ajustado para setor: {sector}")
    if company_size:
        notes.append(f"Tamanho da empresa considerado: {company_size}")
    notes.append("Revise e customize antes de adotar — esta é uma baseline.")
    notes.append("FairnessGuard validou o texto da política.")

    return {
        "success": True,
        "template_used": template_id,
        "policy": policy,
        "fairness_check": {
            "passed": passed,
            "issues": issues,
        },
        "customization_notes": notes,
        "next_action_suggestion": (
            "Revise a política sugerida. Se quiser adotá-la, posso salvá-la "
            "na tabela company_hiring_policies via save_hiring_policy(rules=...)."
        ),
    }


# ───────────────────────────────────────────────────────────────────
# Tool 2b — save_hiring_policy (PR2 / Task #1002, fix C1)
# ───────────────────────────────────────────────────────────────────

# Whitelist canônica dos 5 blocos JSONB de `company_hiring_policies`.
# Espelha a DDL em `app/core/database.py::create_company_hiring_policies_table`
# e o `_VALID_POLICY_BLOCKS` em `hiring_policy/agents/policy_tool_registry.py`.
_HIRING_POLICY_BLOCKS = frozenset({
    "pipeline_rules",
    "scheduling_rules",
    "communication_rules",
    "screening_rules",
    "automation_rules",
})

# Açúcar sintático: o LLM costuma gerar campos atômicos (sem nesting). Mapeamos
# para o bloco correto. Espelha as 5 famílias de regra do hub Políticas.
_ATOMIC_FIELD_TO_BLOCK: dict[str, str] = {
    # screening_rules
    "min_interviews_before_offer": "screening_rules",
    "auto_screening": "screening_rules",
    "manager_approval_for_offer": "screening_rules",
    # scheduling_rules
    "allowed_days": "scheduling_rules",
    "allowed_hours": "scheduling_rules",
    # communication_rules
    "auto_rejection_feedback": "communication_rules",
    "lia_tone": "communication_rules",
    # automation_rules
    "autonomy_level": "automation_rules",
}

# PR3 (Task #1003): removido `_TEXTUAL_POLICY_FIELDS` — agora ``save_hiring_policy``
# delega a validação ao ``validate_fairness_recursive`` que cobre TODOS os campos
# textuais (incluindo strings curtas e nested em pipeline_rules/scheduling_rules
# como `allowed_days = ["seg", "qua", "Sem mães solteiras"]`).


async def save_hiring_policy(
    rules: dict[str, Any],
    **kwargs,
) -> dict[str, Any]:
    """
    Persist (upsert) the company's hiring policy into `company_hiring_policies`.

    Accepts either a flat dict of atomic fields (e.g.
    {"min_interviews_before_offer": 3, "lia_tone": "amigável"}) or a structured
    dict keyed by the 5 canonical blocks (pipeline_rules, scheduling_rules,
    communication_rules, screening_rules, automation_rules), or a mix of both.
    Atomic fields are routed to the correct block via `_ATOMIC_FIELD_TO_BLOCK`.

    Tenant scoping is mandatory (company_id from `_context`). FairnessGuard runs
    over textual fields (auto_rejection_feedback, lia_tone). Best-effort audit
    log via try/except (PR4 will replace with the canonical wrapper).

    Returns:
        {success, fields_saved, blocks_touched, fairness_blocked, message}
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    user_id = context.user_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    if not rules or not isinstance(rules, dict):
        return {
            "success": False,
            "error": "invalid_input",
            "message": "`rules` must be a non-empty dict.",
        }

    # Normaliza: agrega tudo nos 5 blocos JSONB.
    block_updates: dict[str, dict[str, Any]] = {}
    rejected: list[str] = []

    for key, value in rules.items():
        if key in _HIRING_POLICY_BLOCKS:
            if not isinstance(value, dict):
                rejected.append(f"{key}: deve ser dict, recebeu {type(value).__name__}")
                continue
            block_updates.setdefault(key, {}).update(value)
        elif key in _ATOMIC_FIELD_TO_BLOCK:
            target_block = _ATOMIC_FIELD_TO_BLOCK[key]
            block_updates.setdefault(target_block, {})[key] = value
        else:
            rejected.append(f"{key}: campo não reconhecido (fora da whitelist)")

    if not block_updates:
        return {
            "success": False,
            "error": "no_valid_fields",
            "message": (
                "Nenhum campo válido em `rules`. Aceitos: blocos "
                f"{sorted(_HIRING_POLICY_BLOCKS)} ou campos atômicos "
                f"{sorted(_ATOMIC_FIELD_TO_BLOCK)}."
            ),
            "rejected": rejected,
        }

    # PR3 (Task #1003) — FairnessGuard recursivo. Cobre TODOS os campos
    # textuais (incluindo nested em pipeline_rules/scheduling_rules e strings
    # curtas como `lia_tone="só homens"`). Substitui o filtro restrito
    # `_TEXTUAL_POLICY_FIELDS` (bypass parcial do C3 do audit T1-T6).
    fairness = validate_fairness_recursive(
        block_updates, guard=_fairness_guard, root_label="rules"
    )
    if fairness.is_blocked:
        return _fairness_violation_payload(fairness)

    # Upsert: lê o bloco atual, faz merge superficial, grava de volta.
    fields_saved: list[str] = []
    blocks_touched: list[str] = []
    try:
        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                text(
                    "SELECT pipeline_rules, scheduling_rules, communication_rules, "
                    "screening_rules, automation_rules "
                    "FROM company_hiring_policies WHERE company_id = :cid LIMIT 1"
                ),
                {"cid": company_id},
            )
            row = existing.mappings().first()

            merged: dict[str, dict[str, Any]] = {}
            for block_name in _HIRING_POLICY_BLOCKS:
                current = (row[block_name] if row else None) or {}
                if isinstance(current, str):
                    try:
                        current = json.loads(current)
                    except (json.JSONDecodeError, TypeError):
                        current = {}
                if not isinstance(current, dict):
                    current = {}
                if block_name in block_updates:
                    current = {**current, **block_updates[block_name]}
                    blocks_touched.append(block_name)
                    fields_saved.extend(block_updates[block_name].keys())
                merged[block_name] = current

            params = {
                "cid": company_id,
                "pipeline_rules": json.dumps(merged["pipeline_rules"], ensure_ascii=False),
                "scheduling_rules": json.dumps(merged["scheduling_rules"], ensure_ascii=False),
                "communication_rules": json.dumps(merged["communication_rules"], ensure_ascii=False),
                "screening_rules": json.dumps(merged["screening_rules"], ensure_ascii=False),
                "automation_rules": json.dumps(merged["automation_rules"], ensure_ascii=False),
            }

            if row:
                await db.execute(
                    text(
                        "UPDATE company_hiring_policies SET "
                        "pipeline_rules = :pipeline_rules::json, "
                        "scheduling_rules = :scheduling_rules::json, "
                        "communication_rules = :communication_rules::json, "
                        "screening_rules = :screening_rules::json, "
                        "automation_rules = :automation_rules::json, "
                        "updated_at = NOW() "
                        "WHERE company_id = :cid"
                    ),
                    params,
                )
            else:
                await db.execute(
                    text(
                        "INSERT INTO company_hiring_policies "
                        "(company_id, pipeline_rules, scheduling_rules, communication_rules, "
                        "screening_rules, automation_rules, created_at, updated_at) "
                        "VALUES (:cid, :pipeline_rules::json, :scheduling_rules::json, "
                        ":communication_rules::json, :screening_rules::json, "
                        ":automation_rules::json, NOW(), NOW())"
                    ),
                    params,
                )
            await db.commit()
    except Exception as exc:
        logger.error("save_hiring_policy failed: %s", exc, exc_info=True)
        return {
            "success": False,
            "error": "db_error",
            "message": f"Erro ao salvar política de recrutamento: {exc}",
        }

    # PR4 substitui pelo wrapper canônico _audit_company_change com Sentry capture.
    try:
        from app.shared.compliance.audit_service import AuditService
        service = AuditService()
        coro = service.log_decision(
            company_id=str(company_id),
            agent_name="company_settings_tools",
            decision_type="company_settings_change",
            action="save_hiring_policy",
            decision="completed",
            reasoning=[
                f"blocks_touched={blocks_touched}",
                f"fields_saved={fields_saved}",
                f"user_id={user_id}",
            ],
            criteria_used=["hiring_policy_whitelist", "company_scoped", "fairness_guard_textual"],
            job_vacancy_id=None,
            confidence=1.0,
            human_review_required=False,
            criteria_ignored=None,
        )
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(coro)
        except Exception:
            pass
    except Exception as exc:
        logger.debug("[save_hiring_policy] audit emission deferred: %s", exc)

    logger.info(
        "[save_hiring_policy] tenant=%s user=%s blocks=%s fields=%d rejected=%d",
        company_id, user_id, blocks_touched, len(fields_saved), len(rejected),
    )

    return {
        "success": True,
        "data": {
            "blocks_touched": blocks_touched,
            "fields_saved": fields_saved,
            "rejected": rejected,
        },
        "message": (
            f"Política de recrutamento salva: {len(fields_saved)} campos em "
            f"{len(blocks_touched)} blocos."
        ),
    }


# ───────────────────────────────────────────────────────────────────
# Tool 3 — import_benefits_from_data
# ───────────────────────────────────────────────────────────────────

async def import_benefits_from_data(
    benefits: list[dict[str, Any]],
    replace_existing: bool = False,
    **kwargs,
) -> dict[str, Any]:
    """
    Bulk insert company benefits from structured data (parsed spreadsheet or form).

    Each benefit item must have at least 'name'; 'category' and 'description' optional.
    category: health | food | transport | education | financial | quality_life | family | security

    Args:
        benefits: list of {name, category, description, is_highlight}
        replace_existing: if True, deactivates existing benefits before insert

    Returns:
        {success, inserted_count, skipped_count, errors}
    """
    context = _extract_context(kwargs)
    company_id = context.company_id if context else None
    user_id = context.user_id if context else None

    if not company_id:
        return {
            "success": False,
            "error": "company_id_required",
            "message": "Tenant isolation compromised — company_id is required.",
        }

    if not benefits or not isinstance(benefits, list):
        return {
            "success": False,
            "error": "invalid_input",
            "message": "`benefits` must be a non-empty list of objects.",
        }

    # PR3 (Task #1003) — bug C3 do audit T1-T6: import_benefits_from_data NUNCA
    # passava pelo FairnessGuard. Agora cada item ({name, category, description})
    # é varrido recursivamente. Cobre casos como
    # `[{"name": "Vale-creche apenas para mães casadas"}]` ou descrições com
    # exclusão por estado civil/religião/etc.
    fairness = validate_fairness_recursive(
        benefits, guard=_fairness_guard, root_label="benefits"
    )
    if fairness.is_blocked:
        return _fairness_violation_payload(fairness)

    try:
        from lia_models.company_benefit import CompanyBenefit
    except ImportError as e:
        return {
            "success": False,
            "error": "model_unavailable",
            "message": f"CompanyBenefit model not importable: {e}",
        }

    inserted = 0
    skipped = 0
    errors: list[str] = []

    try:
        async with AsyncSessionLocal() as db:
            if replace_existing:
                await db.execute(
                    text("UPDATE company_benefits SET is_active = false WHERE company_id::text = :cid"),
                    {"cid": company_id},
                )

            for idx, b in enumerate(benefits):
                if not isinstance(b, dict):
                    errors.append(f"item {idx}: not a dict")
                    skipped += 1
                    continue
                name = b.get("name") or b.get("nome")
                if not name:
                    errors.append(f"item {idx}: missing 'name'")
                    skipped += 1
                    continue
                try:
                    record = CompanyBenefit(
                        company_id=company_id,
                        name=str(name)[:200],
                        category=b.get("category", "other"),
                        description=b.get("description", "")[:1000] if b.get("description") else None,
                        is_highlight=bool(b.get("is_highlight", False)),
                        is_active=True,
                    )
                    db.add(record)
                    inserted += 1
                except Exception as e:
                    errors.append(f"item {idx} ('{name}'): {e}")
                    skipped += 1

            await db.commit()

        # P2-4 fix (2026-05-10): audit log para SOX/ISO 27001 compliance
        # NB: benefits = CONFIG da empresa (entidade jurídica), NÃO PII de pessoa natural.
        # Consent LGPD não aplica (Art.5 V — titular = pessoa natural).
        # Audit é tracking de ALTERAÇÕES DE CONFIG corporativa, não de dados pessoais.
        try:
            from app.shared.compliance.audit_service import AuditService
            import asyncio
            service = AuditService()
            coro = service.log_decision(
                company_id=str(company_id),
                agent_name="company_settings_tools",
                decision_type="company_settings_change",
                action="import_benefits_from_data",
                decision="completed",
                reasoning=[
                    f"inserted_count={inserted}",
                    f"skipped_count={skipped}",
                    f"replace_existing={replace_existing}",
                    f"user_id={user_id}",
                ],
                criteria_used=["benefit_validation", "company_scoped"],
                job_vacancy_id=None,
                confidence=1.0,
                human_review_required=False,
                criteria_ignored=None,
            )
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(coro)
            except Exception:
                pass
        except Exception as exc:
            logger.debug("[import_benefits] audit emission deferred: %s", exc)

        logger.info(
            "[import_benefits] tenant=%s user=%s inserted=%d skipped=%d",
            company_id, user_id, inserted, skipped,
        )
        return {
            "success": True,
            "inserted_count": inserted,
            "skipped_count": skipped,
            "errors": errors[:10],
            "message": f"Importados {inserted} benefícios ({skipped} ignorados).",
        }
    except Exception as e:
        logger.error("import_benefits_from_data failed: %s", e, exc_info=True)
        return {
            "success": False,
            "error": "db_error",
            "message": f"Erro ao importar benefícios: {e}",
        }


# ───────────────────────────────────────────────────────────────────
# Registration
# ───────────────────────────────────────────────────────────────────

def register_company_settings_tools() -> None:
    tool_registry.register(ToolDefinition(
        name="check_company_completeness",
        description=(
            "Verifica quais campos do perfil da empresa (dados básicos + cultura) "
            "estão vazios. LIA usa para oferecer ajuda proativa. "
            "Retorna missing_fields, overall_pct, has_website e recomendação."
        ),
        parameters_schema={"type": "object", "properties": {}},
        handler=check_company_completeness,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "orchestrator",
        ],
    ))

    tool_registry.register(ToolDefinition(
        name="suggest_recruiting_policy",
        description=(
            "Sugere uma política de recrutamento baseline apropriada para o setor e "
            "tamanho da empresa. Sempre valida via FairnessGuard — zero discriminação "
            "por gênero, raça, idade, religião, deficiência ou socioeconômico. "
            "Retorna template + validação fairness + customization_notes."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "Setor da empresa (ex: tecnologia, saúde, financeiro)",
                },
                "company_size": {
                    "type": "string",
                    "enum": ["startup", "small", "medium", "enterprise"],
                    "description": "Tamanho da empresa",
                },
            },
        },
        handler=suggest_recruiting_policy,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "job_planner", "orchestrator",
        ],
    ))

    tool_registry.register(ToolDefinition(
        name="import_benefits_from_data",
        description=(
            "Bulk insert de benefícios da empresa a partir de dados estruturados "
            "(planilha já parseada ou formulário). Cada item: name + category + description. "
            "Use replace_existing=true para zerar antes de importar."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "benefits": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["health", "food", "transport", "education",
                                         "financial", "quality_life", "family", "security", "other"],
                            },
                            "description": {"type": "string"},
                            "is_highlight": {"type": "boolean"},
                        },
                        "required": ["name"],
                    },
                    "description": "Lista de benefícios",
                },
                "replace_existing": {
                    "type": "boolean",
                    "default": False,
                    "description": "Se true, desativa benefícios existentes antes",
                },
            },
            "required": ["benefits"],
        },
        handler=import_benefits_from_data,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "orchestrator",
        ],
    ))

    tool_registry.register(ToolDefinition(
        name="save_hiring_policy",
        description=(
            "Persiste (upsert) a política de recrutamento da empresa em "
            "company_hiring_policies. Aceita dict com blocos canônicos "
            "(pipeline_rules, scheduling_rules, communication_rules, "
            "screening_rules, automation_rules) ou campos atômicos "
            "(min_interviews_before_offer, manager_approval_for_offer, "
            "allowed_days, allowed_hours, auto_rejection_feedback, lia_tone, "
            "auto_screening, autonomy_level) — campos atômicos são roteados "
            "para o bloco correto. Aplica FairnessGuard nos campos textuais. "
            "Use APÓS confirmação humana (HITL) da política sugerida por "
            "suggest_recruiting_policy."
        ),
        parameters_schema={
            "type": "object",
            "properties": {
                "rules": {
                    "type": "object",
                    "description": (
                        "Dict com blocos canônicos (pipeline_rules, "
                        "scheduling_rules, communication_rules, screening_rules, "
                        "automation_rules) e/ou campos atômicos."
                    ),
                },
            },
            "required": ["rules"],
        },
        handler=save_hiring_policy,
        allowed_agents=[
            "recruiter_assistant", "company_settings", "orchestrator",
        ],
    ))

    logger.info(
        "✅ Registered 4 company_settings tools "
        "(check_company_completeness, suggest_recruiting_policy, "
        "import_benefits_from_data, save_hiring_policy)"
    )
