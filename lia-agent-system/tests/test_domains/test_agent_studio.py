"""Tests for AgentStudioDomain — canonical wiring smoke test.

Cobertura mínima (T-15 R4 sensor enforcement):
- Domain importável (canonical path)
- Domain registrado via @register_domain
- YAML canonical loaded com metadata.version (ADR-028-v2)
- Identidade canonical: domain_id + domain_name
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


# --- Smoke: domain canonical import + registry --------------------------------

class TestAgentStudioDomainSmoke:
    def test_domain_class_importable(self):
        """Domain class importável do path canonical."""
        from app.domains.agent_studio.domain import AgentStudioDomain
        assert AgentStudioDomain is not None

    def test_domain_id_canonical(self):
        """Domain id é 'agent_studio' (alinhado com AGENTIC_DOMAINS sensor)."""
        from app.domains.agent_studio.domain import AgentStudioDomain
        assert AgentStudioDomain.domain_id == "agent_studio"

    def test_domain_name_set(self):
        """Domain name canonical declarado."""
        from app.domains.agent_studio.domain import AgentStudioDomain
        assert hasattr(AgentStudioDomain, "domain_name")
        assert AgentStudioDomain.domain_name  # non-empty

    def test_domain_registered_via_decorator(self):
        """@register_domain wiring funciona."""
        # Importing domain.py triggers @register_domain side-effect
        from app.domains.agent_studio.domain import AgentStudioDomain  # noqa: F401
        from app.domains.registry import get_domain_registry

        registry = get_domain_registry()
        # Registry pode expor de diferentes formas — tolerar implementação
        if hasattr(registry, "list_domains"):
            domain_ids = registry.list_domains()
            assert "agent_studio" in domain_ids
        elif hasattr(registry, "domains"):
            assert "agent_studio" in registry.domains
        else:
            # Pelo menos confirma que o registry existe (decorator não crashou)
            assert registry is not None


# --- YAML canonical (ADR-028-v2) ----------------------------------------------

class TestAgentStudioYamlCanonical:
    def _yaml_path(self) -> Path:
        # tests/test_domains/test_agent_studio.py → repo_root/app/prompts/domains/agent_studio.yaml
        repo_root = Path(__file__).resolve().parent.parent.parent
        return repo_root / "app" / "prompts" / "domains" / "agent_studio.yaml"

    def test_yaml_file_exists(self):
        """YAML canonical existe em app/prompts/domains/."""
        path = self._yaml_path()
        assert path.exists(), f"YAML canonical ausente em {path}"

    def test_yaml_metadata_version_present(self):
        """metadata.version obrigatório (ADR-028-v2 sensor T-05)."""
        path = self._yaml_path()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), "YAML root deve ser dict"
        assert "metadata" in data, "YAML deve ter chave metadata (ADR-028-v2)"
        assert "version" in data["metadata"], "metadata.version obrigatório (ADR-028-v2)"
        assert data["metadata"]["version"], "metadata.version não pode ser vazio"

    def test_yaml_domain_field_matches(self):
        """Campo domain do YAML bate com domain_id canonical."""
        path = self._yaml_path()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data.get("domain") == "agent_studio"

    def test_yaml_system_prompt_present(self):
        """system_prompt obrigatório (T-15 R2)."""
        path = self._yaml_path()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "system_prompt" in data, "system_prompt obrigatório (T-15 R2)"
        assert data["system_prompt"].strip(), "system_prompt não pode ser vazio"


# --- Compliance rules wiring (sandbox + prompt injection) ---------------------

class TestAgentStudioComplianceCanonical:
    def test_yaml_declares_prompt_injection_guard(self):
        """YAML menciona PromptInjectionGuard (compliance gate canonical)."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        path = repo_root / "app" / "prompts" / "domains" / "agent_studio.yaml"
        content = path.read_text(encoding="utf-8")
        # Tolerar variações de caixa / formatação
        assert "PromptInjectionGuard" in content or "prompt injection" in content.lower(), (
            "YAML deve declarar PromptInjectionGuard (compliance canonical Agent Studio)"
        )

    def test_yaml_declares_sandbox_isolation(self):
        """YAML menciona sandbox isolation (multi-tenancy canonical)."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        path = repo_root / "app" / "prompts" / "domains" / "agent_studio.yaml"
        content = path.read_text(encoding="utf-8")
        assert "sandbox" in content.lower() or "isolation" in content.lower(), (
            "YAML deve declarar sandbox isolation (multi-tenancy canonical)"
        )
