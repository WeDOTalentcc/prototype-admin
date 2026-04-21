"""
FIX 17 — Capability truthfulness guardrail.

Bug observed in chat audit (screenshot 2):
  User: 'busque candidatos desenvolvedor python com ingles avancado em sao paulo capital'
  LIA:  'Não consigo filtrar candidatos por localização no momento, a busca
         por localidade não está disponível.'

The tool search_candidates DOES support location filtering (confirmed in
tool_registry_metadata.yaml description). LIA hallucinated a limitation.
The existing 'hallucination' guardrail covers INVENTING data; this fix
covers the flip side — DENYING capability that exists.

Structural tests (YAML load + content presence).
"""
import pytest


class TestFix17CapabilityTruthfulness:
    def _load_guardrails(self):
        from pathlib import Path
        import yaml
        p = Path("app/prompts/shared/guardrails_block.yaml").resolve()
        if not p.exists():
            # try from any CWD
            import app.prompts as _p
            p = Path(_p.__file__).parent / "shared" / "guardrails_block.yaml"
        return yaml.safe_load(p.read_text())

    def test_guardrails_yaml_loads(self):
        data = self._load_guardrails()
        assert isinstance(data, dict)
        assert "universal" in data

    def test_capability_truthfulness_block_exists(self):
        """Universal block must contain capability_truthfulness key after FIX 17."""
        data = self._load_guardrails()
        universal = data.get("universal", {})
        assert "capability_truthfulness" in universal, (
            "FIX 17: guardrails_block.yaml must have universal.capability_truthfulness"
        )
        content = universal["capability_truthfulness"]
        assert isinstance(content, str) and len(content) > 50

    def test_capability_block_mentions_schema_check(self):
        """Content must instruct LLM to verify tool schema before denying capability."""
        data = self._load_guardrails()
        block = data.get("universal", {}).get("capability_truthfulness", "")
        # Keywords that signal the instruction is there
        low = block.lower()
        has_instruction = any(k in low for k in (
            "consultar",
            "verifique",
            "schema",
            "ferramenta",
            "tool",
            "capability",
            "capacidade",
        ))
        assert has_instruction, (
            f"Block must instruct to verify tool schema. Got: {block[:200]}"
        )

    def test_compliance_base_includes_capability_block(self):
        """compliance_base.py must append capability_truthfulness to prompt assembly."""
        from pathlib import Path
        import app.domains.compliance_base as cb
        src = Path(cb.__file__).read_text()
        assert "capability_truthfulness" in src, (
            "FIX 17: compliance_base.py must reference capability_truthfulness in the "
            "universal guardrails iteration loop"
        )

    def test_existing_hallucination_block_still_there(self):
        """Regression: existing hallucination block must not be removed."""
        data = self._load_guardrails()
        universal = data.get("universal", {})
        assert "hallucination" in universal
        assert "NUNCA invente" in universal["hallucination"]
