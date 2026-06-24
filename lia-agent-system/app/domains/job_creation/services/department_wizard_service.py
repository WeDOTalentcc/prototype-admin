"""
department_wizard_service.py — criação de departamento inline no wizard de vaga.

Invocado por intake_gate sub-estado 1.5 quando o recruiter confirma criação de
um departamento não encontrado no DB durante o intake de uma nova vaga.

Padrão canonical:
- company_id SEMPRE do contexto (JWT via state), NUNCA do payload LLM.
- Fail-closed: ValueError em company_id inválido (não silencia).
- Manager auto-linked a partir de parsed_manager_name / parsed_manager_email do state.
"""
import re
import logging
from typing import Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Criação de departamento
# ---------------------------------------------------------------------------

async def create_department_for_wizard(
    name: str,
    company_id: str,
    db: Any,
    *,
    code: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    headcount: Optional[int] = None,
    cost_center: Optional[str] = None,
    hiring_priority: str = "normal",
    manager_name: Optional[str] = None,
    manager_email: Optional[str] = None,
    manager_title: Optional[str] = None,
) -> dict:
    """Cria departamento e retorna {"id": str, "name": str}.

    Multi-tenancy canonical: company_id do state (JWT), injetado fail-closed.
    Manager auto-linked quando parsed_manager_name/email conhecidos.
    """
    # Multi-tenancy fail-closed
    try:
        resolved_cid = UUID(company_id)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"company_id inválido para criação de departamento: {company_id!r}") from exc

    from app.domains.company.repositories.department_repository import DepartmentRepository

    repo = DepartmentRepository(db)

    # Normaliza hiring_priority
    _valid_priorities = {"normal", "alta", "crítica", "critica", "urgente"}
    _hp = (hiring_priority or "normal").lower().strip()
    if _hp not in _valid_priorities:
        _hp = "normal"

    dept_data: dict[str, Any] = {
        "company_id": resolved_cid,
        "name": name.strip(),
        "is_active": True,
        "order": 0,
    }
    if code:
        dept_data["code"] = code.strip().upper()
    if description:
        dept_data["description"] = description.strip()
    if location:
        dept_data["location"] = location.strip()
    if headcount is not None:
        dept_data["headcount"] = int(headcount)
    if cost_center:
        dept_data["cost_center"] = cost_center.strip()
    if _hp != "normal":
        dept_data["hiring_priority"] = _hp
    # Manager auto-link
    if manager_name:
        dept_data["manager_name"] = manager_name.strip()
    if manager_email:
        dept_data["manager_email"] = manager_email.strip()
    if manager_title:
        dept_data["manager_title"] = manager_title.strip()

    dept = await repo.create(dept_data)
    logger.info(
        "[DeptWizardService] created department name=%s company=%s id=%s",
        dept.name, company_id, dept.id,
    )
    return {"id": str(dept.id), "name": dept.name}


# ---------------------------------------------------------------------------
# Parser da resposta do recruiter ao prompt de criação
# ---------------------------------------------------------------------------

_CONFIRM_PATTERNS = re.compile(
    r"\b(sim|s\b|pode|cria|criar|crie|confirmo|confirmar|yes|ok\b|vai|vamos|"
    r"cadastra|cadastrar|cadastre|quero|aceito)\b",
    re.IGNORECASE,
)
_DENY_PATTERNS = re.compile(
    r"\b(n[aã]o|no\b|cancelar|cancel|escolhe|escolher|escolho|usa\b|usar|seleciona)\b",
    re.IGNORECASE,
)
_CODE_PATTERN = re.compile(
    r"\bc[oó]digo[:\s]+([A-Z0-9_-]{1,10})\b|c[oó]digo\s+['\"]?([A-Z0-9_-]{1,10})['\"]?",
    re.IGNORECASE,
)
_DESC_PATTERN = re.compile(
    r"descri[çc][aã]o[:\s]+([^.,;!?\n]{5,120})",
    re.IGNORECASE,
)
_HEADCOUNT_PATTERN = re.compile(
    r"(\d{1,4})\s*(?:pessoa|colaborador|funcion|membro|head)",
    re.IGNORECASE,
)
_LOCATION_PATTERN = re.compile(
    r"localiza[çc][aã]o[:\s]+([^.,;!?\n]{3,60})|"
    r"(?:em|no|na)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç ]{2,30})",
    re.IGNORECASE,
)
_EXISTING_DEPT_PATTERN = re.compile(
    r"(?:usa?|escolhe?|seleciona?)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n.,;]{2,40})",
    re.IGNORECASE,
)
_PRIORITY_PATTERN = re.compile(
    r"\b(alta|cr[ií]tica|urgente|normal)\b",
    re.IGNORECASE,
)
_COST_CENTER_PATTERN = re.compile(
    r"(?:custo|cc)[:\s]+([A-Z0-9_-]{2,20})",
    re.IGNORECASE,
)


def parse_dept_creation_response(
    user_response: str,
    dept_candidate: str,
) -> dict:
    """Parseia resposta do recruiter ao prompt de criação de departamento.

    Retorna dict com:
        confirmed (bool): True se quer criar, False se recusar/escolher existente
        code, description, location, headcount, cost_center, hiring_priority (Optional)
        chosen_existing (Optional[str]): nome do dept existente se negação + escolha
    """
    text = user_response.strip()
    result: dict[str, Any] = {
        "confirmed": False,
        "code": None,
        "description": None,
        "location": None,
        "headcount": None,
        "cost_center": None,
        "hiring_priority": "normal",
        "chosen_existing": None,
    }

    # Detecção de confirmação / negação
    has_confirm = bool(_CONFIRM_PATTERNS.search(text))
    has_deny = bool(_DENY_PATTERNS.search(text))

    if has_deny and not has_confirm:
        result["confirmed"] = False
        # Tenta extrair departamento escolhido da negação
        m = _EXISTING_DEPT_PATTERN.search(text)
        if m:
            result["chosen_existing"] = (m.group(1) or "").strip()
        return result

    # Confirmation (com ou sem deny — confirm ganha quando ambos)
    result["confirmed"] = has_confirm

    # Extrai campos opcionais
    m = _CODE_PATTERN.search(text)
    if m:
        result["code"] = (m.group(1) or m.group(2) or "").strip().upper() or None

    m = _DESC_PATTERN.search(text)
    if m:
        result["description"] = m.group(1).strip() or None

    m = _HEADCOUNT_PATTERN.search(text)
    if m:
        try:
            result["headcount"] = int(m.group(1))
        except ValueError:
            pass

    m = _LOCATION_PATTERN.search(text)
    if m:
        result["location"] = (m.group(1) or m.group(2) or "").strip() or None

    m = _COST_CENTER_PATTERN.search(text)
    if m:
        result["cost_center"] = m.group(1).strip() or None

    m = _PRIORITY_PATTERN.search(text)
    if m:
        result["hiring_priority"] = m.group(1).lower()

    return result
