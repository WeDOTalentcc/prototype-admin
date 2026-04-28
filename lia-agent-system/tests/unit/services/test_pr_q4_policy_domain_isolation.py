"""
PR-Q4 — Policy domain isolation tests (harness-engineering sensor computacional).

Guards:
1. app/domains/policy/ MUST NOT have a capabilities.yaml — if it gains one,
   keyword routing could collide with hiring_policy domain (canonical).
2. All capability_map intents that touch policy config must route through
   hiring_policy, not the deprecated policy domain.
3. The deprecated policy domain must NOT use @register_agent decorator —
   it is a questionnaire agent, not a routing target.

These tests enforce the invariant until Sprint VI consolidation removes
the deprecated domain entirely.
See: docs/TODO_POLICY_CONSOLIDATION.md
"""
import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent.parent  # lia-agent-system/


class TestPolicyDomainIsolation:
    """Sensor: ensures deprecated policy/ domain never becomes a routing target."""

    def test_policy_domain_has_no_capabilities_yaml(self):
        """Guard: policy/ MUST NOT gain a capabilities.yaml.

        If it does, keyword routing will collide with hiring_policy (canonical).
        Fix: remove the capabilities.yaml from app/domains/policy/ or move its
        content to app/domains/hiring_policy/config/capabilities.yaml instead.
        """
        policy_caps = ROOT / "app" / "domains" / "policy" / "config" / "capabilities.yaml"
        assert not policy_caps.exists(), (
            "app/domains/policy/config/capabilities.yaml DEVE NOT existir.\n"
            "Este domínio está deprecated (ver __init__.py) e não é um routing target.\n"
            "Mova qualquer keyword que queira adicionar para:\n"
            "  app/domains/hiring_policy/config/capabilities.yaml (domínio canônico).\n"
            "Ref: docs/TODO_POLICY_CONSOLIDATION.md"
        )

    def test_hiring_policy_capabilities_yaml_exists(self):
        """Guard: canonical policy routing domain must have its capabilities.yaml."""
        hp_caps = ROOT / "app" / "domains" / "hiring_policy" / "config" / "capabilities.yaml"
        assert hp_caps.exists(), (
            "app/domains/hiring_policy/config/capabilities.yaml está faltando.\n"
            "Este é o domínio canônico para routing de política de contratação (card 9.2)."
        )

    def test_policy_domain_marked_deprecated_in_init(self):
        """Guard: policy/__init__.py must declare domain as deprecated."""
        init_path = ROOT / "app" / "domains" / "policy" / "__init__.py"
        if not init_path.exists():
            pytest.skip("policy domain not present — already removed")
        content = init_path.read_text(encoding="utf-8")
        assert "deprecated" in content.lower(), (
            "app/domains/policy/__init__.py deve declarar o domínio como deprecated.\n"
            "Adicione: __domain_type__ = 'deprecated'\n"
            "Ref: docs/TODO_POLICY_CONSOLIDATION.md"
        )

    def test_policy_domain_agent_not_registered_as_routing_target(self):
        """Guard: policy/ agents must NOT use @register_agent decorator.

        @register_agent registers the agent in the routing table. The deprecated
        policy domain must stay out of the routing table — hiring_policy is canonical.
        Fix: remove @register_agent from any agent in app/domains/policy/agents/.
        """
        policy_agents_dir = ROOT / "app" / "domains" / "policy" / "agents"
        if not policy_agents_dir.exists():
            pytest.skip("policy domain not present — already removed")

        for py_file in policy_agents_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                src = py_file.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (OSError, SyntaxError):
                continue

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                for dec in node.decorator_list:
                    # @register_agent(...) call
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                        if dec.func.id == "register_agent":
                            rel = py_file.relative_to(ROOT)
                            pytest.fail(
                                f"{rel}: encontrado @register_agent no domínio policy/ DEPRECATED.\n"
                                "O domínio policy/ não deve ser um routing target.\n"
                                "Use app/domains/hiring_policy/ para policy routing.\n"
                                "Ref: docs/TODO_POLICY_CONSOLIDATION.md"
                            )

    def test_hiring_policy_configure_policy_keyword_present(self):
        """Guard: hiring_policy must have 'política' or 'politica' keyword for card 9.2.

        Card 9.2 ('Política de contratação') relies on keyword matching to
        reach hiring_policy. If the keyword is removed, card 9.2 goes to
        general_help (dead end).
        Fix: add 'política: configure_policy' back to hiring_policy capabilities.yaml.
        """
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")

        hp_caps = ROOT / "app" / "domains" / "hiring_policy" / "config" / "capabilities.yaml"
        if not hp_caps.exists():
            pytest.fail("hiring_policy/config/capabilities.yaml not found")

        data = yaml.safe_load(hp_caps.read_text(encoding="utf-8"))
        keywords = data.get("intent_keywords", {})
        has_policy_keyword = any(
            "polít" in k or "politi" in k for k in keywords
        )
        assert has_policy_keyword, (
            "hiring_policy/config/capabilities.yaml não tem keyword 'política'/'politica'.\n"
            "Card 9.2 ('Política de contratação') precisa deste keyword para routing.\n"
            "Adicione: 'política: configure_policy' na seção intent_keywords.\n"
            "Ref: docs/TODO_POLICY_CONSOLIDATION.md"
        )
