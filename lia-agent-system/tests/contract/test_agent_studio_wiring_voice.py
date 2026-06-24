"""Contract tests: Voice domain wiring into Agent Studio.

Voice uses a different pattern than the other 3 domains:
- NOT wired via domain_tool_loaders (it's a CHANNEL, not a tool domain)
- StudioVoicePlugin bridges any custom agent to voice
- agent_studio_voice.py endpoints handle initiation/status
- CustomAgent.voice_enabled is the per-agent toggle

These tests validate the infrastructure exists and the seed migration is valid.
"""
import ast
import pathlib

import pytest


class TestVoiceInfrastructureExists:
    """Verify StudioVoicePlugin and voice endpoints exist."""

    def test_studio_voice_plugin_importable(self):
        from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin
        assert StudioVoicePlugin is not None

    def test_plugin_implements_protocol(self):
        from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin
        from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin
        assert issubclass(StudioVoicePlugin, VoiceCorePlugin)

    def test_plugin_has_required_hooks(self):
        from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin
        assert hasattr(StudioVoicePlugin, "on_session_initiated")
        assert hasattr(StudioVoicePlugin, "get_next_question")
        assert hasattr(StudioVoicePlugin, "on_session_finalized")

    def test_voice_endpoints_exist(self):
        path = pathlib.Path("app/api/v1/agent_studio_voice.py")
        assert path.exists()
        src = path.read_text()
        assert "voice/initiate" in src
        assert "voice/sessions" in src
        assert "voice/enabled" in src

    def test_custom_agent_has_voice_enabled_field(self):
        from lia_models.custom_agent import CustomAgent
        assert hasattr(CustomAgent, "voice_enabled")


class TestVoiceNotInToolLoaders:
    """Voice should NOT be in domain_tool_loaders — it's a channel, not tools."""

    def test_voice_not_in_domain_tool_loaders(self):
        src = pathlib.Path("app/domains/agent_studio/custom_agent_runtime.py").read_text()
        assert '"voice"' not in src or "get_voice_tools" not in src


class TestVoiceMigrationSyntax:

    def test_migration_valid(self):
        path = pathlib.Path("alembic/versions/277_seed_voice_screening_agent_studio.py")
        assert path.exists()
        src = path.read_text()
        tree = ast.parse(src)

        func_names = {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert "upgrade" in func_names
        assert "downgrade" in func_names

    def test_revision_chain(self):
        src = pathlib.Path(
            "alembic/versions/277_seed_voice_screening_agent_studio.py"
        ).read_text()
        tree = ast.parse(src)
        revisions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("revision", "down_revision"):
                        if isinstance(node.value, ast.Constant):
                            revisions[target.id] = node.value.value
        assert revisions["down_revision"] == "276_seed_wf_agent_studio"


class TestAllFourDomainsWired:
    """Final check: all 4 Agent Studio Development domains accounted for."""

    def test_interview_intelligence_wired(self):
        from app.domains.agent_studio.platform_tools_loader import get_domain_tool_loaders
        assert "interview_intelligence" in get_domain_tool_loaders()

    def test_talent_intelligence_wired(self):
        from app.domains.agent_studio.platform_tools_loader import get_domain_tool_loaders
        assert "talent_intelligence" in get_domain_tool_loaders()

    def test_workforce_wired(self):
        from app.domains.agent_studio.platform_tools_loader import get_domain_tool_loaders
        assert "workforce" in get_domain_tool_loaders()

    def test_voice_has_studio_plugin(self):
        from app.domains.voice.plugins.studio_voice_plugin import StudioVoicePlugin
        assert StudioVoicePlugin.plugin_name is not None or hasattr(StudioVoicePlugin, "plugin_name")

    def test_voice_has_marketplace_seed(self):
        path = pathlib.Path("alembic/versions/277_seed_voice_screening_agent_studio.py")
        assert path.exists()
