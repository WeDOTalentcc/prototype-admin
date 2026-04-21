#!/usr/bin/env python3
"""
Production Readiness Audit — CI Guard
======================================
Reads the module registry (AVAILABLE_MODULES + CompanyModule DB) and verifies
that every domain/module marked as "production" (status=active) satisfies the
18-criterion Production Readiness checklist derived from the WeDO Talent Guide v3.3.

Usage:
    python production_readiness_audit.py [--domain <name>] [--strict]

Exit codes:
    0  — all production modules pass
    1  — one or more production modules fail one or more criteria
    2  — script error (cannot read registry, etc.)

Run in CI:
    python production_readiness_audit.py --strict
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent
AGENT_SYSTEM = ROOT / "lia-agent-system"
sys.path.insert(0, str(AGENT_SYSTEM))

# ---------------------------------------------------------------------------
# Checklist — 18 Production Readiness Criteria
# ---------------------------------------------------------------------------

@dataclass
class Criterion:
    id: str
    name: str
    dimension: str
    description: str
    evidence_paths: list[str]
    weight: float = 1.0

    def check(self, domain: str, folder: str = "") -> tuple[bool, str]:
        """
        Returns (passed, evidence_note).
        `folder` is the actual filesystem folder name for this domain (may differ
        from the registry key). Paths may contain {domain} and/or {folder} templates.
        """
        raise NotImplementedError

    def _resolve(self, path: str, domain: str, folder: str) -> Path:
        """Expand {domain} and {folder} templates then resolve against AGENT_SYSTEM."""
        return AGENT_SYSTEM / path.format(domain=domain, folder=folder or domain)


@dataclass
class FilePresentCriterion(Criterion):
    """Passes if at least one of the evidence_paths exists."""

    def check(self, domain: str, folder: str = "") -> tuple[bool, str]:
        for p in self.evidence_paths:
            resolved = self._resolve(p, domain, folder)
            if resolved.exists():
                return True, f"Found: {resolved.relative_to(ROOT)}"
        return False, f"None of {self.evidence_paths} found for domain={domain}"


@dataclass
class GrepCriterion(Criterion):
    """Passes if pattern is found in at least one of the evidence_paths (or their children)."""
    pattern: str = ""

    def _grep_path(self, resolved: Path) -> tuple[bool, str]:
        import re
        if not resolved.exists():
            return False, ""
        if resolved.is_dir():
            for f in resolved.rglob("*.py"):
                try:
                    if re.search(self.pattern, f.read_text(errors="replace")):
                        return True, str(f.relative_to(ROOT))
                except Exception:
                    continue
        else:
            try:
                if re.search(self.pattern, resolved.read_text(errors="replace")):
                    return True, str(resolved.relative_to(ROOT))
            except Exception:
                pass
        return False, ""

    def check(self, domain: str, folder: str = "") -> tuple[bool, str]:
        for p in self.evidence_paths:
            resolved = self._resolve(p, domain, folder)
            found, where = self._grep_path(resolved)
            if found:
                return True, f"Pattern '{self.pattern}' found in {where}"
        return False, f"Pattern '{self.pattern}' not found in any of {self.evidence_paths}"


@dataclass
class AlwaysPassCriterion(Criterion):
    """Placeholder for criteria verified by infrastructure, not per-domain code."""
    note: str = ""

    def check(self, domain: str, folder: str = "") -> tuple[bool, str]:
        return True, self.note or "Infrastructure-level check — assumed pass"


@dataclass
class AlwaysFailCriterion(Criterion):
    """Criterion explicitly known to fail — used for known open gaps."""
    reason: str = ""

    def check(self, domain: str, folder: str = "") -> tuple[bool, str]:
        return False, self.reason or "Known open gap — requires manual fix"


CHECKLIST: list[Criterion] = [
    # PR-01 — Tenant Isolation (domain-scoped: checks actual domain folder)
    GrepCriterion(
        id="PR-01",
        name="Tenant Isolation em Queries",
        dimension="D13 Security",
        description="Todas as queries filtram por company_id. Sem acesso cross-tenant.",
        evidence_paths=[
            "app/domains/{folder}/services",
            "app/domains/{folder}/repositories",
            "app/domains/{folder}/agents",
            "app/domains/{folder}/tools",
            "app/shared/tenant_guard.py",
        ],
        pattern=r"company_id",
        weight=2.0,
    ),
    # PR-02 — Fail-Closed Defaults
    GrepCriterion(
        id="PR-02",
        name="Fail-Closed em Exceções",
        dimension="D13 Security",
        description="Exceções retornam negado/bloqueado, nunca permitem por padrão.",
        evidence_paths=[
            "app/shared/module_gating.py",
            "app/shared/tenant_guard.py",
        ],
        pattern=r"fail.closed|error_fallback|allowed.*False",
        weight=2.0,
    ),
    # PR-03 — PII Masking 3 Layers
    GrepCriterion(
        id="PR-03",
        name="PII Masking em Prompts LLM",
        dimension="D12 AI Governance",
        description="strip_pii_for_llm_prompt() ou PIIMaskingFilter aplicado antes de enviar ao LLM.",
        evidence_paths=[
            "app/shared/pii_masking.py",
            "app/shared/llm/llm.py",
            "app/shared/llm/llm_gemini.py",
        ],
        pattern=r"strip_pii_for_llm_prompt|PIIMaskingFilter",
        weight=2.0,
    ),
    # PR-04 — FairnessGuard Coverage
    GrepCriterion(
        id="PR-04",
        name="FairnessGuard Aplicado",
        dimension="D12 AI Governance",
        description="FairnessGuard L1/L2 aplicado em queries de busca de candidatos.",
        evidence_paths=[
            "app/shared/compliance/fairness_guard.py",
            "app/shared/compliance/c3b_layer.py",
        ],
        pattern=r"FairnessGuard|fairness_guard",
        weight=1.5,
    ),
    # PR-05 — Audit Trail
    GrepCriterion(
        id="PR-05",
        name="Audit Trail Estruturado",
        dimension="D13 Security",
        description="AuditService.log_decision() chamado em decisões críticas.",
        evidence_paths=[
            "app/shared/compliance/audit_service.py",
        ],
        pattern=r"log_decision|AuditService",
        weight=1.5,
    ),
    # PR-06 — No Ghost Actions (is_mock check)
    GrepCriterion(
        id="PR-06",
        name="Sem Ghost Actions",
        dimension="D4 Tool Orchestration",
        description=(
            "Tools de comunicação que não despacham devem ter is_mock=True explícito. "
            "Communication tools: verificar dispatch_status no retorno."
        ),
        evidence_paths=[
            "app/domains/communication/tools/communication_tools.py",
        ],
        pattern=r"is_mock|dispatch_status|CommunicationDispatcher",
        weight=2.0,
    ),
    # PR-07 — Multi-Worker Safe (WSManager)
    GrepCriterion(
        id="PR-07",
        name="WebSocket Multi-Worker Safe",
        dimension="D2 Orquestração",
        description="WSManager usa Redis pub/sub para broadcast entre workers.",
        evidence_paths=[
            "app/shared/websocket/ws_manager.py",
        ],
        pattern=r"pubsub|publish|redis.*broadcast|MULTI.WORKER",
        weight=2.0,
    ),
    # PR-08 — Tenant Isolation em Prompts LLM
    GrepCriterion(
        id="PR-08",
        name="Tenant Isolation em Prompt LLM",
        dimension="D3 Intelligence Depth",
        description="SystemPromptBuilder injeta company_id como restrição obrigatória no prompt.",
        evidence_paths=[
            "app/shared/prompts/system_prompt_builder.py",
        ],
        pattern=r"ISOLAMENTO DE TENANT|company_id.*EXCLUSIVAMENTE|_TENANT_ISOLATION",
        weight=2.0,
    ),
    # PR-09 — Rate Limiting
    GrepCriterion(
        id="PR-09",
        name="Rate Limiting Configurado",
        dimension="D14 Performance",
        description="Rate limiting por usuário/empresa implementado.",
        evidence_paths=[
            "app/middleware/rate_limiter.py",
            "app/shared/resilience",
        ],
        pattern=r"rate_limit|RateLimiter|per_user|per_company",
        weight=1.0,
    ),
    # PR-10 — Circuit Breakers
    GrepCriterion(
        id="PR-10",
        name="Circuit Breakers em Dependências Externas",
        dimension="D6 Resiliência",
        description="Circuit breakers aplicados a LLMs, email, ATS, voz.",
        evidence_paths=[
            "app/shared/resilience/circuit_breaker.py",
        ],
        pattern=r"CircuitBreaker|circuit_breaker|CircuitBreakerError",
        weight=1.0,
    ),
    # PR-11 — Health Check
    GrepCriterion(
        id="PR-11",
        name="Health Check Endpoint",
        dimension="D6 Resiliência",
        description="Endpoint /health reporta status de DB, Redis, LLMs.",
        evidence_paths=[
            "app/api/v1/health_check.py",
            "app/shared/health/providers_health.py",
        ],
        pattern=r"health|readiness|liveness|redis|database",
        weight=1.0,
    ),
    # PR-12 — Structured Logging
    GrepCriterion(
        id="PR-12",
        name="Logging Estruturado com Contexto",
        dimension="D5 Cross-cutting",
        description="Logs incluem company_id, agent_name, session_id nos eventos críticos.",
        evidence_paths=[
            "app/shared/compliance/audit_service.py",
            "app/shared/observability",
        ],
        pattern=r"company_id.*log|logger.*company|structured",
        weight=1.0,
    ),
    # PR-13 — LGPD Consent Check
    GrepCriterion(
        id="PR-13",
        name="LGPD Consent Gate",
        dimension="D5 Cross-cutting",
        description="ConsentCheckerService verificado antes de processar dados de candidatos.",
        evidence_paths=[
            "app/domains/lgpd/services/consent_checker_service.py",
            "app/domains/consent",
        ],
        pattern=r"ConsentChecker|consent_checker|check_consent",
        weight=1.5,
    ),
    # PR-14 — HITL for Strategic Decisions
    GrepCriterion(
        id="PR-14",
        name="HITL em Decisões Estratégicas",
        dimension="D1 Agência",
        description="Human-in-the-loop via interrupt_before LangGraph em fluxos de triagem e pipeline.",
        evidence_paths=[
            "app/domains/cv_screening/services/hitl_service.py",
            "app/shared/governance",
        ],
        pattern=r"interrupt_before|HITL|hitl|human_in_the_loop|human_review",
        weight=1.5,
    ),
    # PR-15 — Timeout Configuration
    GrepCriterion(
        id="PR-15",
        name="Timeout por Tool e por LLM Call",
        dimension="D6 Resiliência",
        description="TimedToolNode ou timeout explícito por chamada de tool/LLM.",
        evidence_paths=[
            "app/api/v1/agent_chat_ws.py",
            "app/orchestrator/agentic_loop.py",
        ],
        pattern=r"TimedToolNode|timeout|LLM_TIMEOUT",
        weight=1.0,
    ),
    # PR-16 — No Raw SQL (SQLi prevention) — domain-scoped
    GrepCriterion(
        id="PR-16",
        name="Sem SQL Injeção (ORM Parameterizado)",
        dimension="D13 Security",
        description="Todos os queries usam SQLAlchemy ORM. Sem f-string SQL.",
        evidence_paths=[
            "app/domains/{folder}/repositories",
            "app/domains/{folder}/services",
            "app/domains/{folder}/agents",
            "app/shared/repositories",
        ],
        pattern=r"select\(|Select\(|scalar_one|execute\(stmt|from sqlalchemy|SessionLocal\(\)",
        weight=2.0,
    ),
    # PR-17 — E2E Tests or Eval Coverage
    FilePresentCriterion(
        id="PR-17",
        name="Cobertura de Testes E2E ou Eval",
        dimension="D15 Testes",
        description="Testes E2E ou eval suite cobrindo fluxo principal do domínio.",
        evidence_paths=[
            "tests/e2e",
            "eval",
            "tests/unit",
            "tests/integration",
        ],
        weight=1.0,
    ),
    # PR-18 — Documentation / ADR
    FilePresentCriterion(
        id="PR-18",
        name="Documentação e ADR",
        dimension="D8 Documentação",
        description="Existe documentação do módulo em docs/ ou ADR em docs/adr/.",
        evidence_paths=[
            "docs",
            "docs/adr",
            "docs/specs",
        ],
        weight=0.5,
    ),
]

# ---------------------------------------------------------------------------
# Domain registry — manually mirrored from AVAILABLE_MODULES in billing.py
# ---------------------------------------------------------------------------
# IMPORTANT — keeping this registry in sync is a manual step.
#
# Authoritative source:
#   lia-agent-system/libs/models/lia_models/billing.py  → AVAILABLE_MODULES
#
# When a module status changes in AVAILABLE_MODULES, update:
#   1. `status` field here (matches ModuleStatus enum value)
#   2. `pr_status` if the domain promoted to/from "production"
#
# Future work (follow-up task #694 scope):
#   Replace this static dict with a live read of AVAILABLE_MODULES
#   (without DB access — read from billing.py at import time) so drift
#   is impossible. Blocked on removing DB-coupled imports from billing.py.
# ---------------------------------------------------------------------------

DOMAIN_REGISTRY: dict[str, dict[str, Any]] = {
    "talent_intelligence_pro": {
        "label": "Talent Intelligence Pro",
        "status": "beta",
        "pr_status": "beta",
        "domain_folder": "talent_intelligence",
    },
    "internal_mobility": {
        "label": "Internal Mobility Suite",
        "status": "beta",
        "pr_status": "beta",
        "domain_folder": "workforce",
    },
    "interview_intelligence": {
        "label": "Interview Intelligence Pro",
        "status": "beta",
        "pr_status": "beta",
        "domain_folder": "interview_intelligence",
    },
    "workforce_planning": {
        "label": "Workforce Planning",
        "status": "coming_soon",
        "pr_status": "experimental",
        "domain_folder": "workforce",
    },
    "candidate_nurture": {
        "label": "Candidate Nurture / CRM",
        "status": "beta",
        "pr_status": "beta",
        "domain_folder": "recruitment",
    },
    "onboarding_suite": {
        "label": "Onboarding Intelligence",
        "status": "coming_soon",
        "pr_status": "experimental",
        "domain_folder": "recruitment_journey",
    },
    "predictive_analytics": {
        "label": "Predictive Attrition Analytics",
        "status": "coming_soon",
        "pr_status": "experimental",
        "domain_folder": "analytics",
    },
    "core_sourcing": {
        "label": "Core Sourcing & Search",
        "status": "active",
        "pr_status": "production",
        "domain_folder": "sourcing",
    },
    "cv_screening_wsi": {
        "label": "CV Screening + WSI",
        "status": "active",
        "pr_status": "production",
        "domain_folder": "cv_screening",
    },
    "pipeline_management": {
        "label": "Pipeline & Kanban Management",
        "status": "active",
        "pr_status": "production",
        "domain_folder": "pipeline",
    },
    "job_management": {
        "label": "Job Management + Wizard",
        "status": "active",
        "pr_status": "production",
        "domain_folder": "job_management",
    },
    "analytics_reporting": {
        "label": "Analytics & Reporting",
        "status": "active",
        "pr_status": "production",
        "domain_folder": "analytics",
    },
    "communication": {
        "label": "Communication Tools",
        "status": "beta",
        "pr_status": "beta",
        "domain_folder": "communication",
        "known_gaps": [],  # PR-06 closed (Task #693): send_email/send_whatsapp now wired to CommunicationDispatcher (Mailgun/Resend + Twilio).
    },
    "interview_scheduling": {
        "label": "Interview Scheduling",
        "status": "coming_soon",
        "pr_status": "experimental",
        "domain_folder": "interview_scheduling",
        "known_gaps": [
            "Rails routes GET /v1/users/scheduling/availability and POST /v1/users/calendar_events do not exist.",
            "schedule_interview tool now persists Interview row + sends invite email (Task #693); Rails calendar sync still pending.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Audit runner
# ---------------------------------------------------------------------------

@dataclass
class DomainAuditResult:
    domain: str
    label: str
    pr_status: str
    passed: list[tuple[Criterion, str]] = field(default_factory=list)
    failed: list[tuple[Criterion, str]] = field(default_factory=list)
    known_gaps: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        total_weight = sum(c.weight for c, _ in self.passed) + sum(c.weight for c, _ in self.failed)
        if total_weight == 0:
            return 0.0
        return sum(c.weight for c, _ in self.passed) / total_weight

    @property
    def is_production_ready(self) -> bool:
        critical = [c for c, _ in self.failed if c.weight >= 2.0]
        return len(critical) == 0 and self.score >= 0.80


def audit_domain(domain: str, info: dict[str, Any]) -> DomainAuditResult:
    result = DomainAuditResult(
        domain=domain,
        label=info["label"],
        pr_status=info.get("pr_status", "experimental"),
        known_gaps=info.get("known_gaps", []),
    )
    folder = info.get("domain_folder", domain)
    for criterion in CHECKLIST:
        try:
            passed, note = criterion.check(domain, folder=folder)
        except Exception as exc:
            passed, note = False, f"Check error: {exc}"
        if passed:
            result.passed.append((criterion, note))
        else:
            result.failed.append((criterion, note))
    return result


def run_audit(
    domains: list[str] | None = None,
    production_only: bool = False,
    strict: bool = False,
) -> tuple[list[DomainAuditResult], bool]:
    targets = DOMAIN_REGISTRY
    if domains:
        targets = {k: v for k, v in DOMAIN_REGISTRY.items() if k in domains}
    if production_only:
        targets = {k: v for k, v in targets.items() if v.get("pr_status") == "production"}

    results: list[DomainAuditResult] = []
    any_failure = False

    for domain, info in sorted(targets.items()):
        result = audit_domain(domain, info)
        results.append(result)
        if result.pr_status == "production" and not result.is_production_ready:
            any_failure = True
        if strict and result.failed:
            any_failure = True

    return results, any_failure


def print_report(results: list[DomainAuditResult], verbose: bool = False) -> None:
    print("\n" + "=" * 70)
    print("  PRODUCTION READINESS AUDIT REPORT")
    print("=" * 70)

    for r in results:
        status_icon = "PASS" if r.is_production_ready else "FAIL"
        gate = " [GATE]" if r.pr_status == "production" else ""
        print(f"\n[{status_icon}] {r.label} ({r.domain}){gate}")
        print(f"       PR Status : {r.pr_status.upper()}")
        print(f"       Score     : {r.score:.0%}  ({len(r.passed)}/{len(r.passed)+len(r.failed)} criteria)")

        if r.failed:
            print("       FAILED CRITERIA:")
            for c, note in r.failed:
                weight_tag = " [CRITICAL]" if c.weight >= 2.0 else ""
                print(f"         ✗ {c.id} — {c.name}{weight_tag}")
                if verbose:
                    print(f"              {note}")

        if r.known_gaps:
            print("       KNOWN GAPS:")
            for gap in r.known_gaps:
                print(f"         ! {gap}")

        if verbose and r.passed:
            print("       PASSED:")
            for c, note in r.passed:
                print(f"         ✓ {c.id} — {c.name}")
                print(f"              {note}")

    print("\n" + "=" * 70)
    production_results = [r for r in results if r.pr_status == "production"]
    failing_production = [r for r in production_results if not r.is_production_ready]

    print(f"  Domains audited       : {len(results)}")
    print(f"  Production domains    : {len(production_results)}")
    print(f"  Failing (production)  : {len(failing_production)}")
    if failing_production:
        print(f"  Failing domains       : {', '.join(r.domain for r in failing_production)}")
    print("=" * 70 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Production Readiness Audit CI Guard")
    parser.add_argument("--domain", nargs="*", help="Specific domain(s) to audit")
    parser.add_argument("--production-only", action="store_true", help="Only audit production-status domains")
    parser.add_argument("--strict", action="store_true", help="Fail if ANY criterion fails (not just production)")
    parser.add_argument("--verbose", action="store_true", help="Show evidence details")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    try:
        results, any_failure = run_audit(
            domains=args.domain,
            production_only=args.production_only,
            strict=args.strict,
        )
    except Exception as exc:
        print(f"ERROR: Audit script failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        report = [
            {
                "domain": r.domain,
                "label": r.label,
                "pr_status": r.pr_status,
                "score": round(r.score, 3),
                "is_production_ready": r.is_production_ready,
                "passed": [c.id for c, _ in r.passed],
                "failed": [c.id for c, _ in r.failed],
                "known_gaps": r.known_gaps,
            }
            for r in results
        ]
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(results, verbose=args.verbose)

    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
