"""Domain Structure Conformance Test — Sprint 13.

Validates that every directory under app/domains/ follows the canonical
structure documented in DOMAIN_CATALOG.md and the Notion Domain Catalog.

Audit: 2026-06-13. Baseline: 0 violations.
"""
import os
from pathlib import Path

import pytest
import yaml

DOMAINS_ROOT = Path(__file__).resolve().parents[2] / "app" / "domains"

# Support files that are NOT domains
_SUPPORT_FILES = {
    "base.py",
    "compliance_base.py",
    "registry.py",
    "workflow.py",
    "__init__.py",
    "__pycache__",
    "_template",
}

# Domains registered via @register_domain (have domain.py)
_REGISTERED_DOMAINS = {
    "analytics",
    "ats_integration",
    "automation",
    "candidate_self_service",
    "communication",
    "company_settings",
    "cv_screening",
    "hiring_policy",
    "interview_scheduling",
    "job_management",
    "offer",
    "pipeline",
    "recruiter_assistant",
    "sourcing",
    "talent_pool",
    "agent_studio",
    "job_creation",
    "digital_twin",
    "recruitment_campaign",
}

# Domains that legitimately skip capabilities.yaml
_SKIP_CAPABILITIES_YAML = {
    "job_creation",  # LangGraph wizard, no intent routing
}

# Non-registered domains that legitimately have agents/
_NON_REGISTERED_WITH_AGENTS = {
    "policy",      # PolicySetupAgent — intentional, documented
    "workforce",   # workforce_tool_registry — agent tools, documented
}


def _discover_domain_dirs():
    """Discover all domain directories (excluding support files)."""
    dirs = []
    for entry in sorted(DOMAINS_ROOT.iterdir()):
        if entry.is_dir() and entry.name not in _SUPPORT_FILES:
            dirs.append(entry)
    return dirs


def _get_domain_names():
    """Return list of domain directory names for parametrize."""
    return [d.name for d in _discover_domain_dirs()]


# ---------------------------------------------------------------------------
# 1. Every domain directory must have __init__.py
# ---------------------------------------------------------------------------
class TestDomainInit:
    @pytest.mark.parametrize("domain", _get_domain_names())
    def test_has_init(self, domain):
        """Every domain directory must have __init__.py."""
        init = DOMAINS_ROOT / domain / "__init__.py"
        assert init.exists(), (
            f"app/domains/{domain}/ is missing __init__.py. "
            f"Add one to mark the package."
        )


# ---------------------------------------------------------------------------
# 2. Registered domains must have domain.py + ComplianceDomainPrompt
# ---------------------------------------------------------------------------
class TestRegisteredDomains:
    @pytest.mark.parametrize("domain", sorted(_REGISTERED_DOMAINS))
    def test_has_domain_py(self, domain):
        """Registered domains must have domain.py."""
        domain_py = DOMAINS_ROOT / domain / "domain.py"
        assert domain_py.exists(), (
            f"app/domains/{domain}/ is in _REGISTERED_DOMAINS but has no domain.py"
        )

    @pytest.mark.parametrize("domain", sorted(_REGISTERED_DOMAINS))
    def test_inherits_compliance(self, domain):
        """Registered domain classes must inherit ComplianceDomainPrompt."""
        domain_py = DOMAINS_ROOT / domain / "domain.py"
        if not domain_py.exists():
            pytest.skip("no domain.py")
        content = domain_py.read_text()
        assert "ComplianceDomainPrompt" in content, (
            f"app/domains/{domain}/domain.py does not reference ComplianceDomainPrompt. "
            f"LIA-C01 requires all registered domains to inherit from it."
        )

    @pytest.mark.parametrize("domain", sorted(_REGISTERED_DOMAINS))
    def test_has_capabilities_yaml(self, domain):
        """Registered domains must have config/capabilities.yaml (with documented exceptions)."""
        if domain in _SKIP_CAPABILITIES_YAML:
            pytest.skip(f"{domain} is in _SKIP_CAPABILITIES_YAML")
        yaml_path = DOMAINS_ROOT / domain / "config" / "capabilities.yaml"
        assert yaml_path.exists(), (
            f"app/domains/{domain}/config/capabilities.yaml is missing. "
            f"CascadedRouter needs intent keywords to route to this domain."
        )

    @pytest.mark.parametrize("domain", sorted(_REGISTERED_DOMAINS))
    def test_capabilities_yaml_valid(self, domain):
        """capabilities.yaml must be valid YAML with intent_keywords key."""
        if domain in _SKIP_CAPABILITIES_YAML:
            pytest.skip(f"{domain} is in _SKIP_CAPABILITIES_YAML")
        yaml_path = DOMAINS_ROOT / domain / "config" / "capabilities.yaml"
        if not yaml_path.exists():
            pytest.skip("no capabilities.yaml")
        data = yaml.safe_load(yaml_path.read_text())
        assert isinstance(data, dict), (
            f"app/domains/{domain}/config/capabilities.yaml is not a valid YAML dict"
        )
        assert "intent_keywords" in data, (
            f"app/domains/{domain}/config/capabilities.yaml is missing 'intent_keywords' key"
        )


# ---------------------------------------------------------------------------
# 3. Non-registered domains must NOT have domain.py
# ---------------------------------------------------------------------------
class TestNonRegisteredDomains:
    @pytest.mark.parametrize("domain", _get_domain_names())
    def test_no_unexpected_domain_py(self, domain):
        """Domains not in _REGISTERED_DOMAINS should not have domain.py."""
        if domain in _REGISTERED_DOMAINS:
            pytest.skip("registered domain")
        domain_py = DOMAINS_ROOT / domain / "domain.py"
        assert not domain_py.exists(), (
            f"app/domains/{domain}/ has domain.py but is NOT in _REGISTERED_DOMAINS. "
            f"Either add to _REGISTERED_DOMAINS or remove domain.py."
        )

    @pytest.mark.parametrize("domain", _get_domain_names())
    def test_no_agents_unless_documented(self, domain):
        """Non-registered domains should not have agents/ unless documented."""
        if domain in _REGISTERED_DOMAINS:
            pytest.skip("registered domain")
        agents_dir = DOMAINS_ROOT / domain / "agents"
        if not agents_dir.is_dir():
            pytest.skip("no agents/ dir")
        assert domain in _NON_REGISTERED_WITH_AGENTS, (
            f"app/domains/{domain}/ has agents/ but is not registered and not in "
            f"_NON_REGISTERED_WITH_AGENTS. Add to exception set with comment if intentional."
        )


# ---------------------------------------------------------------------------
# 4. No stray .py files at domain top level (should be in services/, tools/, etc.)
# ---------------------------------------------------------------------------
_ALLOWED_TOP_LEVEL_FILES = {
    "__init__.py",
    "domain.py",
    "actions.py",
    "dependencies.py",
    "compliance.py",
    "constants.py",
}

# Domains with documented exceptions for top-level files
_TOP_LEVEL_EXCEPTIONS: dict[str, set[str]] = {
    "agent_studio": {
        "custom_agent_runtime.py",
        "_audit_helper.py",
        "reasoning_trace_builder.py",
        "whatsapp_agent_plugin.py",
        "platform_tools_loader.py",
    },
    "job_creation": {
        "api_client.py",
        "audit_actions.py",
        "dispatch_messages.py",
        "feature_flag.py",
        "graph.py",
        "policy_gate.py",
        "schemas.py",
        "state.py",
    },
}


class TestNoStrayFiles:
    @pytest.mark.parametrize("domain", _get_domain_names())
    def test_no_stray_py_at_top_level(self, domain):
        """Domain top level should only have canonical .py files."""
        domain_dir = DOMAINS_ROOT / domain
        exceptions = _TOP_LEVEL_EXCEPTIONS.get(domain, set())
        stray = []
        for f in domain_dir.iterdir():
            if f.is_file() and f.suffix == ".py" and f.name not in _ALLOWED_TOP_LEVEL_FILES:
                if f.name not in exceptions:
                    stray.append(f.name)
        assert not stray, (
            f"app/domains/{domain}/ has stray .py files at top level: {stray}. "
            f"Move to services/, tools/, or agents/. "
            f"If intentional, add to _TOP_LEVEL_EXCEPTIONS."
        )


# ---------------------------------------------------------------------------
# 5. No empty directories (post-migration artifacts)
# ---------------------------------------------------------------------------
# File extensions that count as "content" (not just .py)
_CONTENT_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".toml", ".txt", ".md"}

# Scaffolding directories that are empty by design (awaiting future content).
# Each entry: domain -> set of subdir names.
_SCAFFOLDING_DIRS: dict[str, set[str]] = {
    "candidate_self_service": {"actions"},   # planned action handlers
    "cv_screening": {"prompts"},             # prompt templates placeholder
    "hiring_policy": {"actions"},            # planned action handlers
    "job_creation": {"actions"},             # planned action handlers
    "offer": {"models"},                     # domain models placeholder
}


class TestNoEmptyDirs:
    @pytest.mark.parametrize("domain", _get_domain_names())
    def test_no_empty_subdirs(self, domain):
        """Domain subdirectories should not be empty (except __pycache__)."""
        domain_dir = DOMAINS_ROOT / domain
        empty = []
        for sub in domain_dir.iterdir():
            if not sub.is_dir() or sub.name == "__pycache__":
                continue
            # Skip documented scaffolding dirs
            scaffolding = _SCAFFOLDING_DIRS.get(domain, set())
            if sub.name in scaffolding:
                continue
            # Check for ANY content file (not just .py)
            content_files = [
                f for f in sub.rglob("*")
                if f.is_file()
                and f.suffix in _CONTENT_EXTENSIONS
                and f.name != "__init__.py"
            ]
            if content_files:
                continue
            # Check if __init__.py has meaningful content (imports, assignments, etc.)
            init = sub / "__init__.py"
            if init.exists():
                content = init.read_text().strip()
                lines = [
                    line for line in content.split("\n")
                    if line.strip()
                    and not line.strip().startswith("#")
                    and not line.strip().startswith('"""')
                    and not line.strip().startswith("'''")
                ]
                if any(
                    kw in line
                    for line in lines
                    for kw in ("import", "=", "def ", "class ")
                ):
                    continue
            empty.append(sub.name)
        assert not empty, (
            f"app/domains/{domain}/ has empty subdirectories: {empty}. "
            f"Remove if repos/services were migrated. "
            f"If intentional, add content files or remove the directory."
        )


# ---------------------------------------------------------------------------
# 6. No macOS artifacts
# ---------------------------------------------------------------------------
class TestNoArtifacts:
    @pytest.mark.parametrize("domain", _get_domain_names())
    def test_no_macos_artifacts(self, domain):
        """No AppleDouble/macOS resource fork files."""
        domain_dir = DOMAINS_ROOT / domain
        artifacts = list(domain_dir.rglob("._*"))
        assert not artifacts, (
            f"app/domains/{domain}/ has macOS artifacts: "
            f"{[str(a.relative_to(DOMAINS_ROOT)) for a in artifacts]}. "
            f"Remove with: rm {' '.join(str(a) for a in artifacts)}"
        )
