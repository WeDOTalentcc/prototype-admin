"""Initiative VI Fase 0 (2026-04-21) — eval_judge LLM Factory migration.

Tests that:
1. eval/eval_judge_config.yaml exists with model + prompt_template
2. eval_judge.py imports from app.shared.providers.llm_factory
3. No direct anthropic.Anthropic() call remains
4. Config-driven values reach the module (model name, max_tokens)
"""
from __future__ import annotations

from pathlib import Path


def _root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "eval" / "eval_judge.py").exists():
            return parent
    raise RuntimeError("eval/eval_judge.py not found")


def test_eval_judge_config_yaml_exists_with_required_fields() -> None:
    """Fase 0: externalized config file must exist."""
    import yaml

    cfg_path = _root() / "eval" / "eval_judge_config.yaml"
    assert cfg_path.exists(), (
        "Init VI Fase 0: eval/eval_judge_config.yaml must exist "
        "(externalized JUDGE_PROMPT + model config)"
    )
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("provider") == "claude"
    assert "model" in data and data["model"].get("name")
    assert "prompt_template" in data and isinstance(data["prompt_template"], str)
    assert len(data["prompt_template"]) > 500, (
        "Init VI Fase 0: prompt_template must carry the full JUDGE_PROMPT"
    )


def test_eval_judge_uses_llm_factory_not_direct_anthropic() -> None:
    """Fase 0 core: source must import LLMProviderFactory, no direct Anthropic()."""
    source = (_root() / "eval" / "eval_judge.py").read_text(encoding="utf-8")
    assert "LLMProviderFactory" in source, (
        "Init VI Fase 0: eval_judge.py must import LLMProviderFactory "
        "(canonical provider stack)"
    )
    # Legacy direct call must be gone from the judge path
    assert "client = anthropic.Anthropic(" not in source, (
        "Init VI Fase 0: direct anthropic.Anthropic() instantiation must be "
        "replaced with factory. Remains in source: bypass not canonical."
    )
    assert "asyncio.run(" in source, (
        "Init VI Fase 0: sync eval_judge must use asyncio.run() to call "
        "async factory generate()"
    )


def test_eval_judge_fase0_marker_present() -> None:
    """Fase 0 audit marker."""
    source = (_root() / "eval" / "eval_judge.py").read_text(encoding="utf-8")
    assert "Init VI Fase 0" in source or "Initiative VI Fase 0" in source, (
        "Init VI Fase 0: eval_judge.py must contain Fase 0 marker"
    )


def test_judge_config_loads_at_module_import() -> None:
    """Fase 0: module-level _CONFIG must resolve model + prompt from YAML."""
    import importlib.util
    import sys

    root = _root()
    spec = importlib.util.spec_from_file_location(
        "_eval_judge_under_test", root / "eval" / "eval_judge.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_eval_judge_under_test"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("_eval_judge_under_test", None)

    assert hasattr(mod, "_CONFIG"), "Fase 0: _CONFIG module var expected"
    assert hasattr(mod, "_JUDGE_MODEL"), "Fase 0: _JUDGE_MODEL module var expected"
    assert hasattr(mod, "_JUDGE_MAX_TOKENS")
    assert hasattr(mod, "_JUDGE_PROVIDER")
    assert mod._JUDGE_PROVIDER == "claude"
    assert "haiku" in mod._JUDGE_MODEL.lower()
    # Sanity: prompt loaded from config or inline fallback
    assert isinstance(mod.JUDGE_PROMPT, str) and len(mod.JUDGE_PROMPT) > 500
