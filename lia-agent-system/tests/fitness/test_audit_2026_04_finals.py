"""
Architectural fitness — AUDIT FINAL 2026-04 closeout.

Cobre os finais F4, F8, F10, F11, F12 do task #352.
Roda no job CI `Architectural fitness functions` junto com test_architectural_fitness.py.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent  # lia-agent-system/
_REPO_ROOT = _ROOT.parent
_APP = _ROOT / "app"
_SCRIPTS = _ROOT / "scripts"


# ────────────────────────────────────────────────────────────────────
# F4 — InterviewGraph deve ter FairnessGuard L2 (paridade com WSI)
# ────────────────────────────────────────────────────────────────────
class TestF4InterviewGraphFairnessGuard:
    """A3: InterviewGraph precisa rodar FairnessGuard sobre a saída ao candidato."""

    def test_interview_graph_calls_check_fairness(self):
        graph = (
            _APP
            / "domains"
            / "interview_scheduling"
            / "agents"
            / "interview_graph.py"
        )
        content = graph.read_text(errors="ignore")
        assert "fairness_guard_middleware" in content, (
            "InterviewGraph não importa fairness_guard_middleware (F4 — AUDIT 2026-04)"
        )
        assert "check_fairness(" in content, (
            "InterviewGraph não invoca check_fairness() (F4 — AUDIT 2026-04)"
        )
        assert "interview_scheduling_response" in content, (
            "InterviewGraph não nomeia o context da chamada FairnessGuard "
            "(esperado: 'interview_scheduling_response')"
        )

    def test_interview_graph_implements_block_and_regenerate(self):
        """F4 exige política BLOCK + REGENERATE, não só fail-open warnings."""
        graph = (
            _APP
            / "domains"
            / "interview_scheduling"
            / "agents"
            / "interview_graph.py"
        )
        content = graph.read_text(errors="ignore")
        assert "_FAIRNESS_BLOCK_FALLBACK_MESSAGE" in content, (
            "InterviewGraph precisa definir mensagem fallback sanitizada "
            "(_FAIRNESS_BLOCK_FALLBACK_MESSAGE) — F4 BLOCK + REGENERATE"
        )
        assert "fairness_blocked" in content, (
            "InterviewGraph precisa marcar response_data['fairness_blocked']=True "
            "ao bloquear — F4 BLOCK + REGENERATE"
        )
        assert 'decision="blocked"' in content or "decision='blocked'" in content, (
            "InterviewGraph precisa chamar audit_service.log_decision com "
            "decision='blocked' quando FG bloqueia — F4 / BCB 498 / SOX"
        )
        assert "fairness_guard_l2" in content, (
            "audit_service.log_decision precisa marcar criteria_used=['fairness_guard_l2'] — F4"
        )


# ────────────────────────────────────────────────────────────────────
# F8 — toda `require_company=False` precisa de comentário `kept:`
# ────────────────────────────────────────────────────────────────────
_FLAG = re.compile(r"require_company\s*=\s*False")
_KEPT = re.compile(r"#\s*require_company=False\s*kept\s*:", re.IGNORECASE)


class TestF8RequireCompanyExemptionsDocumented:
    """W7-residual: cada `require_company=False` precisa de justificativa inline."""

    def test_every_exemption_has_kept_comment(self):
        violations: list[str] = []
        for py in _APP.rglob("*.py"):
            if py.name == "tool_handler.py":
                continue
            try:
                lines = py.read_text(errors="ignore").splitlines()
            except Exception:
                continue
            for idx, line in enumerate(lines):
                if not _FLAG.search(line):
                    continue
                # Skip comment lines (the `kept:` justification itself contains
                # the literal `require_company=False`)
                if line.lstrip().startswith("#"):
                    continue
                kept = False
                for back in range(1, 4):
                    if idx - back < 0:
                        break
                    if _KEPT.search(lines[idx - back]):
                        kept = True
                        break
                if not kept:
                    violations.append(f"{py.relative_to(_REPO_ROOT)}:{idx + 1}")

        assert not violations, (
            "require_company=False sem comentário `kept:` "
            f"({len(violations)} violação(ões)). Atualize "
            "docs/policies/require_company_exemptions.md e adicione comentário inline:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_policy_doc_exists(self):
        doc = _REPO_ROOT / "docs" / "policies" / "require_company_exemptions.md"
        assert doc.exists(), (
            "docs/policies/require_company_exemptions.md ausente (F8 — AUDIT 2026-04)"
        )


# ────────────────────────────────────────────────────────────────────
# F10 — shims `RAILS-DEPRECATED` precisam de cabeçalho `@deprecated since=`
# ────────────────────────────────────────────────────────────────────
_DEPRECATED_HEADER = re.compile(r"@deprecated\s+since\s*=\s*\d{4}-\d{2}-\d{2}")


class TestF10ShimSlaHeaders:
    """Todo arquivo com `RAILS-DEPRECATED` deve declarar `@deprecated since=YYYY-MM-DD`."""

    def test_rails_deprecated_files_have_sla_header(self):
        violations: list[str] = []
        shared = _APP / "shared"
        for py in shared.rglob("*.py"):
            try:
                content = py.read_text(errors="ignore")
            except Exception:
                continue
            if "RAILS-DEPRECATED" not in content:
                continue
            if not _DEPRECATED_HEADER.search(content):
                violations.append(str(py.relative_to(_REPO_ROOT)))

        assert not violations, (
            "Shims sem cabeçalho `@deprecated since=YYYY-MM-DD` "
            f"({len(violations)}). Aplique a política docs/policies/shim_sla.md:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_shim_sla_doc_exists(self):
        doc = _REPO_ROOT / "docs" / "policies" / "shim_sla.md"
        assert doc.exists(), (
            "docs/policies/shim_sla.md ausente (F10 — AUDIT 2026-04)"
        )


# ────────────────────────────────────────────────────────────────────
# F11 — proibir `from langchain_core.tools import tool` em domains/**/tools/
# ────────────────────────────────────────────────────────────────────
_FORBIDDEN_TOOL_IMPORT = re.compile(
    r"^\s*from\s+langchain_core\.tools\s+import\s+(?:[\w\s,]*\b)?tool\b",
    re.MULTILINE,
)


class TestF11NoLangchainToolDecoratorRegression:
    """T2 anti-regressão: tools de domínio não podem voltar a usar `@tool`."""

    def test_no_langchain_tool_import_in_domain_tools(self):
        violations: list[str] = []
        domains = _APP / "domains"
        targets: list[Path] = []
        for tools_dir in domains.glob("*/tools"):
            if tools_dir.is_dir():
                targets.extend(tools_dir.rglob("*.py"))
        for registry in domains.glob("*/agents/*_tool_registry.py"):
            targets.append(registry)
        for path in targets:
            try:
                content = path.read_text(errors="ignore")
            except Exception:
                continue
            if _FORBIDDEN_TOOL_IMPORT.search(content):
                violations.append(str(path.relative_to(_REPO_ROOT)))

        assert not violations, (
            "Regressão de T2 detectada — use `from app.shared.tool_handler import "
            f"tool_handler` ({len(violations)} arquivo(s)):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_lint_script_exists_and_runs(self):
        script = _SCRIPTS / "check_no_langchain_tool_decorator.py"
        assert script.exists(), "scripts/check_no_langchain_tool_decorator.py ausente"
        # Roda como subprocess para validar que o script é executável
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
            timeout=30,
        )
        assert result.returncode == 0, (
            f"check_no_langchain_tool_decorator.py falhou:\n{result.stdout}\n{result.stderr}"
        )


# ────────────────────────────────────────────────────────────────────
# F12 — smoke test: GlobalToolRegistry deve estar deletado OU registrar tools
# ────────────────────────────────────────────────────────────────────
class TestF12GlobalToolRegistryDeadCanary:
    """
    T3 canary: o módulo `app/shared/global_tool_registry.py` foi deletado em
    2026-04 após confirmação de zero callers. Este teste falha se o módulo
    voltar a existir sem callers — força o time a *ativar ou deletar* na
    mesma PR.
    """

    def test_global_tool_registry_module_state(self):
        module = _APP / "shared" / "global_tool_registry.py"
        if not module.exists():
            # Estado canônico atual: deletado. Teste passa.
            return

        # Se voltou a existir, exigimos pelo menos 1 caller em produção que
        # registre tools, caso contrário falha (anti-zumbi).
        callers = 0
        caller_pattern = re.compile(
            r"GlobalToolRegistry\.get_instance\(\)|get_registry\(\)\.register\("
        )
        for py in _APP.rglob("*.py"):
            if py == module:
                continue
            try:
                content = py.read_text(errors="ignore")
            except Exception:
                continue
            if caller_pattern.search(content):
                callers += 1

        assert callers > 0, (
            "global_tool_registry.py voltou a existir mas tem 0 callers em produção. "
            "Decisão arquitetural pendente — ative (com pelo menos 1 caller) ou "
            "delete o módulo (F12 — AUDIT 2026-04, task #351)."
        )


# ────────────────────────────────────────────────────────────────────
# Shim/real service consolidation guard (Task #1283)
# ────────────────────────────────────────────────────────────────────
class TestShimServiceConsolidationGuard:
    """Garante que arquivos em app/shared/services com twin em
    app/domains/*/services permaneçam shims puros (só reexportam), sem
    lógica de negócio duplicada. Fonte-da-verdade = app/domains/*/services.
    """

    def test_shim_guard_script_exists_and_runs(self):
        script = _SCRIPTS / "check_shared_services_shims.py"
        assert script.exists(), "scripts/check_shared_services_shims.py ausente"
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
            timeout=60,
        )
        assert result.returncode == 0, (
            f"check_shared_services_shims.py falhou:\n{result.stdout}\n{result.stderr}"
        )
