#!/usr/bin/env python3
"""
AST checker canonical — enforça convenções Pydantic em request schemas.

Registrado 2026-05-20 pós-audit E2E (sensor #3 do harness analysis).

Regras enforced (todas Replit-only; output otimizado pra consumo de LLM):

  R1 — extra='forbid' em request body schemas
       Schemas (Create|Update|Request suffix) DEVEM ter model_config = ConfigDict(extra='forbid')
       OU herdar de WeDoBaseModel (canonical em app/shared/types.py).
       Por quê: audit F1.O2 — POST /job-vacancies aceitou silenciosamente fields fantasma
       (city, state, country, industry). Default Pydantic é 'extra=ignore' — anti-canonical.

  R2 — company_id PROIBIDO em request body
       Nenhum BaseModel pode ter field 'company_id'. Multi-tenancy canonical (CLAUDE.md):
       company_id SEMPRE vem do JWT via Depends(require_company_id).
       Por quê: audit F4.O1, F5.O1 — endpoints recentes pediam company_id no payload,
       abrindo brecha cross-tenant. Violação direta de canonical existente.

  R3 — Path UUID + pattern combo PROIBIDO
       Nenhum `: UUID = Path(..., pattern=...)` — Pydantic 2.10+ não aceita.
       Use `: JobIdParam` (alias canonical em app/shared/types.py) ou `: str = Path(...)`.
       Por quê: audit F2.B1 — 24 endpoints quebrados pelo mesmo copy-paste pattern.

  R4 — x_company_id Header anti-pattern PROIBIDO (multi-tenancy cross-tenant)
       Nenhum handler pode declarar `x_company_id: ... = Header(..., alias="X-Company-ID")`
       NEM atribuir `company_id = x_company_id ...` (overwrite do JWT canonical).
       Use sempre `company_id: str = Depends(require_company_id)` canonical.
       Por quê: audit SMOKE-#2 LGPD (2026-05-20) — 28 sites em 21 arquivos permitiam
       user mandar X-Company-ID em header e operar sobre dados de OUTRA company
       (cross-tenant data manipulation, LGPD compliance break). Infrastructure canonical
       em app/shared/tenant_guard.get_verified_company_id existia mas era ignorada.

Uso:
    python3 scripts/check_pydantic_conventions.py [DIR]   # default: lia-agent-system/app
    Exit 0 = clean, Exit 1 = violations encontradas (mensagens com fix sugerido).

Integração canonical:
    - pre-commit hook (.pre-commit-config.yaml)
    - CI/CD step (backend-ci.yml ou equivalente)
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# ─────────────────────────────────────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────────────────────────────────────
REQUEST_BODY_SUFFIXES = ("Create", "Update", "Request", "Payload", "Input")
"""Heurística: schemas com esses sufixos são request bodies. Override via SKIP_R1."""

SKIP_R1: set[str] = {
    # Classes que legitimamente precisam de extra=allow (externas, schema drift)
    # Formato: "ModelName" ou "module.path:ModelName"
    # Sempre adicionar com motivo + ticket associado.
}

SKIP_R2: set[str] = {
    # Schemas onde company_id no payload é LEGÍTIMO (public endpoints sem JWT,
    # schemas internos não-HTTP, ou DB record models reutilizados como sufixo Create).
    # Sempre adicionar com motivo + ticket associado.
    "DataSubjectRequestCreate",  # Portal do Titular LGPD Art.18 — endpoint público sem JWT, company_id é tenant alvo da request (recebido via form do titular)
    "PersonalizationEventCreate",  # Schema interno (service-to-service), NÃO HTTP body. PersonalizationEventResponse herda dele.
    "IntelligenceInsightCreate",   # Schema interno (service-to-service), NÃO HTTP body. IntelligenceInsightResponse herda dele.
    "JDGenerationRequest",         # Schema interno service-to-service (jd_template_service), NÃO HTTP body.
    "EnrichmentRequest",           # Schema interno service-to-service (jd_enrichment_service, job_wizard_tools), NÃO HTTP body. Há outra EnrichmentRequest em candidates_crud.py que é separada e legítima.
    "CompanyHiringPolicyCreate",   # Schema interno (apenas test usa), CompanyHiringPolicyResponse herda dele.
    "PersonalizedFeedbackRequest", # Schema interno service-to-service (personalized_feedback_service), NÃO HTTP body.
    "ToolExecutionRequest",        # Schema interno service-to-service (orchestrator_routes constrói internamente), NÃO HTTP body.
    "GuardrailCreate",             # Schema interno (guardrail_repository) usado por seeds + handler que constrói internamente — company_id é argumento legítimo do método create.
    "SSOAuditLogCreate",           # Schema interno (audit log record), NÃO HTTP body — usado por WorkOS SSO service para persistir.
    "CultureAnalysisRequest",      # Schema interno service-to-service (analytics culture), tem handler mas company_id vem do JWT — verificar.
    "CultureAnalysisDirectRequest",# Schema sem requerer company_id em DB — usado para análise direta sem persistir.
}

CANONICAL_BASE_CLASSES = {"WeDoBaseModel"}
"""Subclasses dessas têm extra='forbid' herdado — passam R1 sem model_config explícito."""

EXCLUDE_PATHS = (
    "__pycache__",
    ".bak",
    "tests/fixtures",
    "alembic/versions",  # migrations geram models temporários
)

# R4 skip filter — canonical defense functions/files que LEGITIMAMENTE usam Header
# (e.g., tenant_guard.get_verified_company_id compara header vs JWT e retorna 403
# se mismatch — esse é o pattern CORRETO, não anti-pattern).
SKIP_R4_FILES: set[str] = {
    "app/shared/tenant_guard.py",  # canonical defense: get_verified_company_id
    "app/shared/policy_middleware.py",  # canonical policy middleware
}

SKIP_R4_FUNCTIONS: set[str] = {
    "get_verified_company_id",  # canonical defense em tenant_guard.py
    # Webhook canonical defense-in-depth: HMAC-signed (X-Teams-Signature),
    # usa Depends(require_company_id) para JWT auth, e x_company_id Header
    # serve apenas para cross-check (403 se mismatch vs JWT — Task #1146).
    # NÃO é o anti-pattern R4 (não há overwrite do JWT — apenas validação).
    "teams_adaptive_card_webhook",  # canonical webhook defense em app/api/v1/teams.py
}


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Violation:
    rule: str  # R1, R2, R3
    file: str
    line: int
    target: str  # class name or symbol
    message: str  # multi-line, LLM-friendly fix instructions


# ─────────────────────────────────────────────────────────────────────────────
# AST checkers
# ─────────────────────────────────────────────────────────────────────────────
def _is_pydantic_basemodel(class_node: ast.ClassDef) -> bool:
    """Heurística: classe é Pydantic BaseModel (direto ou via alias canonical)."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id in {"BaseModel"} | CANONICAL_BASE_CLASSES:
            return True
        if isinstance(base, ast.Attribute) and base.attr == "BaseModel":
            return True
    return False


def _inherits_canonical_base(class_node: ast.ClassDef) -> bool:
    """True se herda de WeDoBaseModel (que já tem extra='forbid')."""
    for base in class_node.bases:
        if isinstance(base, ast.Name) and base.id in CANONICAL_BASE_CLASSES:
            return True
    return False


def _has_extra_forbid(class_node: ast.ClassDef) -> bool:
    """True se classe declara model_config = ConfigDict(extra='forbid')."""
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "model_config" for t in stmt.targets):
            continue
        # Verifica se valor contém extra='forbid'
        if isinstance(stmt.value, ast.Call):
            for kw in stmt.value.keywords:
                if kw.arg == "extra" and isinstance(kw.value, ast.Constant):
                    if kw.value.value == "forbid":
                        return True
    return False


def _is_request_body_schema(class_name: str) -> bool:
    return any(class_name.endswith(suffix) for suffix in REQUEST_BODY_SUFFIXES)


def check_r1(class_node: ast.ClassDef, filepath: str) -> Violation | None:
    """R1: request body schemas precisam de extra='forbid'."""
    if not _is_pydantic_basemodel(class_node):
        return None
    if not _is_request_body_schema(class_node.name):
        return None
    if class_node.name in SKIP_R1:
        return None
    if _inherits_canonical_base(class_node):
        return None  # WeDoBaseModel já tem
    if _has_extra_forbid(class_node):
        return None
    return Violation(
        rule="R1",
        file=filepath,
        line=class_node.lineno,
        target=class_node.name,
        message=(
            f"❌ R1 violation: {class_node.name} em {filepath}:{class_node.lineno}\n"
            f"   Request body schema sem extra='forbid' — Pydantic default 'ignore' aceita "
            f"silenciosamente fields fantasma (audit F1.O2).\n"
            f"\n"
            f"   Fix canonical (escolher 1):\n"
            f"   (a) Herdar de WeDoBaseModel:\n"
            f"       from app.shared.types import WeDoBaseModel\n"
            f"       class {class_node.name}(WeDoBaseModel):\n"
            f"           ...\n"
            f"\n"
            f"   (b) Adicionar model_config explícito:\n"
            f"       from pydantic import ConfigDict\n"
            f"       class {class_node.name}(BaseModel):\n"
            f"           model_config = ConfigDict(extra='forbid')\n"
            f"           ...\n"
        ),
    )


def check_r2(class_node: ast.ClassDef, filepath: str) -> Iterable[Violation]:
    """
    R2: nenhum request body schema pode ter field company_id (multi-tenancy canonical).

    Refinement 2026-05-20-v2: aplica suffix check Create|Update|Request|Payload|Input
    (mesmo critério do R1). Antes apitava em qualquer BaseModel com company_id —
    isso incluia event/result schemas (PlatformEvent, AgentChatMessage, CrewExecutionResult)
    onde company_id é contexto legítimo, não payload. Baseline R2 caiu de 274 → ~N
    true positives focados em request bodies.

    Resultado: agora apita SÓ quando o nome da classe sugere request body (Create/Update/...).
    Event schemas que NÃO chegam via HTTP body passam.
    """
    if not _is_pydantic_basemodel(class_node):
        return
    if not _is_request_body_schema(class_node.name):
        return  # R2 só se aplica a request body schemas, não event/result/internal
    if class_node.name in SKIP_R2:
        return  # Schema legitimo (public endpoint sem JWT)
    for stmt in class_node.body:
        if not isinstance(stmt, ast.AnnAssign):
            continue
        if not isinstance(stmt.target, ast.Name):
            continue
        if stmt.target.id == "company_id":
            yield Violation(
                rule="R2",
                file=filepath,
                line=stmt.lineno,
                target=f"{class_node.name}.company_id",
                message=(
                    f"❌ R2 violation: {class_node.name}.company_id em {filepath}:{stmt.lineno}\n"
                    f"   Multi-tenancy canonical (CLAUDE.md) proíbe company_id em request payload.\n"
                    f"   Audit F4.O1, F5.O1: endpoints com company_id no body abrem brecha cross-tenant.\n"
                    f"\n"
                    f"   Fix canonical:\n"
                    f"   1. Remova o field 'company_id' do schema {class_node.name}.\n"
                    f"   2. No handler que usa este schema, adicione:\n"
                    f"        from app.shared.security.require_company_id import require_company_id\n"
                    f"        async def my_handler(\n"
                    f"            payload: {class_node.name},\n"
                    f"            company_id: str = Depends(require_company_id),  # extraído do JWT\n"
                    f"        ):\n"
                    f"   3. Use `company_id` extraído do JWT, NUNCA do `payload`.\n"
                ),
            )


def check_r3(tree: ast.AST, filepath: str) -> Iterable[Violation]:
    """R3: nenhum `: UUID = Path(..., pattern=...)` combo."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign):
            continue
        # type annotation == UUID?
        ann = node.annotation
        is_uuid = isinstance(ann, ast.Name) and ann.id == "UUID"
        if not is_uuid:
            continue
        # value = Path(..., pattern=...)?
        if not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        is_path_call = isinstance(func, ast.Name) and func.id == "Path"
        if not is_path_call:
            continue
        has_pattern = any(kw.arg == "pattern" for kw in node.value.keywords)
        if not has_pattern:
            continue
        target_name = node.target.id if isinstance(node.target, ast.Name) else "<unknown>"
        yield Violation(
            rule="R3",
            file=filepath,
            line=node.lineno,
            target=target_name,
            message=(
                f"❌ R3 violation: {target_name}: UUID = Path(..., pattern=...) em {filepath}:{node.lineno}\n"
                f"   Pydantic 2.10+ não permite constraint 'pattern' em type UUID — só em str (audit F2.B1).\n"
                f"\n"
                f"   Fix canonical (escolher 1):\n"
                f"   (a) Use o type alias canonical:\n"
                f"       from app.shared.types import JobIdParam  # ou CandidateIdParam, CompanyIdParam\n"
                f"       async def my_handler({target_name}: JobIdParam, ...):\n"
                f"           ...\n"
                f"\n"
                f"   (b) Substitua type por `str` mantendo pattern:\n"
                f"       {target_name}: str = Path(..., pattern=r'^(?:[0-9a-fA-F-]{{36}}|[0-9]+)$')\n"
                f"\n"
                f"   Se precisar de UUID no body do handler, converta dentro:\n"
                f"       from uuid import UUID\n"
                f"       _uuid = UUID({target_name})  # raises ValueError se não for UUID v4\n"
            ),
        )


def _is_header_call(node: ast.AST) -> bool:
    """True se node é call `Header(...)` (FastAPI Header dependency)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (isinstance(func, ast.Name) and func.id == "Header") or (
        isinstance(func, ast.Attribute) and func.attr == "Header"
    )


def _is_x_company_id_header_alias(call: ast.Call) -> bool:
    """True se Header(..., alias='X-Company-ID') — case-insensitive."""
    for kw in call.keywords:
        if kw.arg == "alias" and isinstance(kw.value, ast.Constant):
            if isinstance(kw.value.value, str) and kw.value.value.lower() == "x-company-id":
                return True
    return False


def check_r4(tree: ast.AST, filepath: str) -> Iterable[Violation]:
    """
    R4: x_company_id Header anti-pattern (multi-tenancy cross-tenant).

    Detecta 2 sub-padrões:
      R4a — declaração `x_company_id: ... = Header(...)` em function signature
            OU qualquer `: ... = Header(..., alias="X-Company-ID")` (mesmo com nome diferente)
      R4b — assignment `company_id = x_company_id ...` no body do handler
            (overwriting JWT canonical com header value)

    Registrado 2026-05-20 pós-fix SMOKE-#2 LGPD. 28 sites em 21 arquivos
    descobertos. Anti-pattern viola CLAUDE.md "company_id sempre via JWT,
    nunca payload/header".
    """
    # R4 skip filter: check file path
    if any(skip in filepath for skip in SKIP_R4_FILES):
        return

    # R4a — function arg `x_company_id: ... = Header(...)` ou `... = Header(alias="X-Company-ID")`
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # skip canonical defense functions
        if node.name in SKIP_R4_FUNCTIONS:
            continue
        # walk args.args + args.kwonlyargs com defaults
        all_args = list(node.args.args) + list(node.args.kwonlyargs)
        all_defaults = list(node.args.defaults) + list(node.args.kw_defaults)
        for arg, default in zip(all_args[-len(all_defaults):] if all_defaults else [], all_defaults):
            if default is None:
                continue
            # Default é Header(...) call?
            if not _is_header_call(default):
                continue
            # arg.arg == "x_company_id"? OU Header tem alias="X-Company-ID"?
            arg_name = arg.arg
            has_x_company_alias = _is_x_company_id_header_alias(default)
            if arg_name == "x_company_id" or has_x_company_alias:
                yield Violation(
                    rule="R4",
                    file=filepath,
                    line=arg.lineno,
                    target=f"{node.name}({arg_name})",
                    message=(
                        f"❌ R4 violation: {node.name}({arg_name}: ... = Header(...)) em {filepath}:{arg.lineno}\n"
                        f"   Multi-tenancy canonical (CLAUDE.md) PROÍBE company_id via Header.\n"
                        f"   Audit SMOKE-#2 LGPD: 28 sites permitiam cross-tenant data manipulation.\n"
                        f"\n"
                        f"   Fix canonical:\n"
                        f"   1. Remova o parameter `{arg_name}: ... = Header(...)` do handler signature.\n"
                        f"   2. Mantenha apenas `company_id: str = Depends(require_company_id)`:\n"
                        f"        from app.shared.security.require_company_id import require_company_id\n"
                        f"        async def {node.name}(\n"
                        f"            ...,\n"
                        f"            company_id: str = Depends(require_company_id),  # do JWT\n"
                        f"        ):\n"
                        f"   3. Se precisar verificar header (estilo defesa em profundidade), use:\n"
                        f"        from app.shared.tenant_guard import get_verified_company_id\n"
                        f"        company_id: str = Depends(get_verified_company_id)\n"
                        f"      (este compara header com JWT e retorna 403 se mismatch)\n"
                    ),
                )

    # R4b — assignment `company_id = x_company_id ...` no body
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        # target tem que ser Name "company_id"
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)):
            continue
        if node.targets[0].id != "company_id":
            continue
        # value contém referência a "x_company_id"?
        contains_x_company_id = False
        for sub in ast.walk(node.value):
            if isinstance(sub, ast.Name) and sub.id == "x_company_id":
                contains_x_company_id = True
                break
        if not contains_x_company_id:
            continue
        yield Violation(
            rule="R4",
            file=filepath,
            line=node.lineno,
            target="company_id = x_company_id ...",
            message=(
                f"❌ R4 violation: `company_id = x_company_id ...` em {filepath}:{node.lineno}\n"
                f"   Assignment sobrescreve company_id do JWT canonical com valor de header.\n"
                f"   Audit SMOKE-#2 LGPD: ataque cross-tenant via X-Company-ID header.\n"
                f"\n"
                f"   Fix canonical:\n"
                f"   1. REMOVA esta linha completamente. O company_id já vem do JWT via\n"
                f"      `Depends(require_company_id)` no signature do handler.\n"
                f"   2. Se há lógica que precisa override LEGÍTIMO (e.g., admin atuando em\n"
                f"      nome de outra company), use:\n"
                f"        from app.shared.tenant_guard import get_verified_company_id\n"
                f"        company_id: str = Depends(get_verified_company_id)\n"
                f"      Este Dep retorna 403 se header não bate com JWT (canonical).\n"
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────
def scan_file(filepath: Path) -> list[Violation]:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        # Skip files que não parseiam (não é nosso problema reportar — outros linters pegam)
        return []

    violations: list[Violation] = []

    # R3: file-level (qualquer AnnAssign UUID+Path)
    violations.extend(check_r3(tree, str(filepath)))

    # R4: file-level (x_company_id Header anti-pattern + JWT overwrite)
    violations.extend(check_r4(tree, str(filepath)))

    # R1 e R2: class-level
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            r1 = check_r1(node, str(filepath))
            if r1:
                violations.append(r1)
            violations.extend(check_r2(node, str(filepath)))

    return violations


def should_skip_file(filepath: Path) -> bool:
    return any(excl in str(filepath) for excl in EXCLUDE_PATHS)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "lia-agent-system/app")
    if not root.exists():
        print(f"⚠ Path não existe: {root}")
        return 2

    all_violations: list[Violation] = []
    files_scanned = 0

    for py_file in root.rglob("*.py"):
        if should_skip_file(py_file):
            continue
        files_scanned += 1
        all_violations.extend(scan_file(py_file))

    if not all_violations:
        print(f"✅ Pydantic conventions OK ({files_scanned} arquivos verificados)")
        return 0

    print(f"❌ {len(all_violations)} violações em {files_scanned} arquivos:\n")
    # Group by rule
    by_rule: dict[str, list[Violation]] = {}
    for v in all_violations:
        by_rule.setdefault(v.rule, []).append(v)

    for rule in sorted(by_rule):
        violations = by_rule[rule]
        print(f"\n{'=' * 70}")
        print(f"{rule} — {len(violations)} violação(ões)")
        print("=" * 70)
        for v in violations:
            print(v.message)

    print(f"\n📊 Resumo: {len(all_violations)} violações total")
    for rule in sorted(by_rule):
        print(f"   {rule}: {len(by_rule[rule])} violação(ões)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
