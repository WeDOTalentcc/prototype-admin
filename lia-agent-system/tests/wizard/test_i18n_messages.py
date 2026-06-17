"""Tests for i18n helper and messages.yaml — PR-18 F-4.1 (2026-05-26).

Verifies:
1. All keys used in nodes/ exist in messages.yaml
2. msg() returns expected strings for sample keys
3. msg() with kwargs substitutes correctly
4. msg() fails open (returns key) when key missing
"""
import re
import os
import pytest
import yaml
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent.parent  # lia-agent-system/
MESSAGES_FILE = BASE / "app" / "prompts" / "job_creation" / "messages.yaml"
NODES_DIR = BASE / "app" / "domains" / "job_creation" / "nodes"


# ── Fixtures ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def messages():
    assert MESSAGES_FILE.exists(), f"messages.yaml not found at {MESSAGES_FILE}"
    with open(MESSAGES_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── Helper ────────────────────────────────────────────────────────────────
def _resolve_key(data: dict, key: str):
    """Resolve dotted key in nested dict. Returns value or None."""
    parts = key.split(".")
    node = data
    for p in parts:
        if not isinstance(node, dict):
            return None
        node = node.get(p)
        if node is None:
            return None
    return node


def _collect_msg_keys_from_nodes() -> list[str]:
    """Parse all msg("...") calls from nodes/*.py files."""
    pattern = re.compile(r'msg\(\s*["\']([^"\']+)["\']')
    keys = []
    for fname in sorted(NODES_DIR.iterdir()):
        if fname.suffix != ".py" or fname.name.startswith("__"):
            continue
        text = fname.read_text(encoding="utf-8")
        keys.extend(pattern.findall(text))
    return list(dict.fromkeys(keys))  # deduplicated, preserving order


# ── Test 1: All keys used in nodes/ exist in messages.yaml ────────────────
def test_all_msg_keys_exist_in_messages_yaml(messages):
    """Every msg('key.subkey') call in nodes/ must resolve to a string in messages.yaml."""
    used_keys = _collect_msg_keys_from_nodes()
    assert used_keys, "No msg() calls found in nodes/ — check the regex"

    missing = []
    not_string = []
    for key in used_keys:
        value = _resolve_key(messages, key)
        if value is None:
            missing.append(key)
        elif not isinstance(value, str):
            not_string.append((key, type(value).__name__))

    assert not missing, (
        f"Keys used in nodes/ but missing from messages.yaml:\n"
        + "\n".join(f"  - {k}" for k in sorted(missing))
    )
    assert not not_string, (
        f"Keys that resolve to non-string values:\n"
        + "\n".join(f"  - {k}: {t}" for k, t in not_string)
    )


# ── Test 2: msg() returns expected strings for sample keys ────────────────
def test_msg_returns_correct_string():
    """msg() should return the exact string from messages.yaml for static keys."""
    from app.domains.job_creation.helpers.i18n import msg

    assert msg("handoff.job_ready") == "Vaga pronta! Vou levar você para a página da vaga"
    assert msg("eligibility.no_questions").startswith("Nenhuma pergunta eliminatória")
    assert msg("review.ready") == "Tudo pronto para publicar. Quer revisar algo ou publicar a vaga agora?"
    assert msg("intake.ask_for_title") == "Pode me passar o título da vaga ou colar a JD?"
    assert msg("jd_gate.new_jd_received") == "Recebi a descrição nova. Vou re-enriquecer agora."
    assert msg("bigfive.fairness_blocked").startswith("Detectei linguagem")


# ── Test 3: msg() with kwargs substitutes correctly ───────────────────────
def test_msg_with_kwargs():
    """msg() should format placeholders with provided kwargs."""
    from app.domains.job_creation.helpers.i18n import msg

    result = msg("eligibility.questions_configured", count=5)
    assert "5" in result
    assert "pergunta" in result

    result = msg("calibration.complete", approved_count=3, threshold=5)
    assert "3/5" in result
    assert "candidatos aprovados" in result

    result = msg("bigfive.ready", title="Engenheiro de Software")
    assert "Engenheiro de Software" in result

    result = msg("handoff.share_link_suffix", share_link="https://wedo.cc/j/123")
    assert "https://wedo.cc/j/123" in result

    result = msg("publish.policy_deny", rationale="Qualidade insuficiente")
    assert "Qualidade insuficiente" in result


# ── Test 4: msg() fails open when key missing ─────────────────────────────
def test_msg_fails_open_on_missing_key():
    """msg() should return the key itself when not found — never raise."""
    from app.domains.job_creation.helpers.i18n import msg, _load_messages

    # Unknown key returns key unchanged
    assert msg("nonexistent.key") == "nonexistent.key"
    assert msg("handoff.nonexistent_subkey") == "handoff.nonexistent_subkey"

    # Missing kwargs doesn't raise — returns unformatted template
    result = msg("eligibility.questions_configured")  # missing count kwarg
    assert result  # returns something (the template with {count} unformatted)
    assert isinstance(result, str)


# ── Test 5: messages.yaml loads cleanly ───────────────────────────────────
def test_messages_yaml_valid(messages):
    """messages.yaml should load without errors and have expected top-level namespaces."""
    expected_namespaces = {
        "handoff", "eligibility", "calibration", "salary", "competency",
        "publish", "bigfive", "wsi_questions", "pipeline_template",
        "intake", "review", "jd_enrichment", "jd_gate", "review_gate",
        "wsi_questions_gate", "competency_gate",
    }
    actual = set(messages.keys())
    missing = expected_namespaces - actual
    assert not missing, f"Missing top-level namespaces in messages.yaml: {missing}"


# ── Test 6: No hardcoded user-facing PT-BR strings remain in node files ───
def test_no_hardcoded_ptbr_user_strings_in_nodes():
    """Key user-facing PT-BR strings should not appear hardcoded in nodes/."""
    # Strings that should now only appear via msg() calls
    forbidden_literals = [
        "Vaga pronta! Vou levar",
        "Configurei ",
        "Nenhuma pergunta eliminatória",
        "Faixa salarial e benefícios prontos",
        "Calibração concluída",
        "Carreguei ",
        "Não consigo publicar a vaga",
        "Antes de publicar, preciso da sua confirmação",
        "Gerei ",
        "Mapeei o perfil Big Five",
        "Para essa vaga, sugiro o pipeline",
        "Não encontrei um pipeline customizado",
        "Vamos usar o pipeline padrão",
        "Tudo pronto para publicar",
        "Recebi a descrição nova",
        "Não consegui interpretar sua resposta",
    ]

    violations = []
    for fname in sorted(NODES_DIR.iterdir()):
        if fname.suffix != ".py" or fname.name.startswith("__"):
            continue
        text = fname.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            # Skip comments, logger calls, docstrings
            stripped = line.strip()
            if stripped.startswith("#") or "logger." in line or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for lit in forbidden_literals:
                if lit in line and "msg(" not in line:
                    violations.append(f"{fname.name}:{line_no}: {line.strip()[:80]}")

    assert not violations, (
        f"Hardcoded user-facing strings found in nodes/:\n"
        + "\n".join(f"  {v}" for v in violations)
    )
