# tests/unit/test_chat_identity_masking.py
"""TDD tests for per-turn identity-document masking in chat output (Task B1).

Verifies:
- Default (ContextVar OFF) → passthrough (no regression to existing 16 call-sites)
- ContextVar ON → CPF/RG/CNPJ masked; email and phone preserved (product decision)
- reset_chat_pii_mask_identity restores passthrough
- chat_should_mask_identity resolves correctly via pii_field_resolver
"""
from types import SimpleNamespace

from app.shared.pii_masking import (
    mask_pii_outbound,
    set_chat_pii_mask_identity,
    reset_chat_pii_mask_identity,
    chat_should_mask_identity,
)


def _user(can_sensitive=True, override=None):
    return SimpleNamespace(
        role="recruiter",
        can_view_salary=False,
        can_view_sensitive_pii=can_sensitive,
        pii_field_visibility=override,
    )


def test_passthrough_when_flag_off():
    """Default contextvar False + no global flag -> passthrough."""
    result = mask_pii_outbound("CPF 123.456.789-09 email a@b.com")
    assert result == "CPF 123.456.789-09 email a@b.com"


def test_masks_cpf_but_not_email_when_identity_on():
    """When ContextVar is ON, CPF is masked but email and phone are preserved."""
    tok = set_chat_pii_mask_identity(True)
    try:
        out = mask_pii_outbound("CPF 123.456.789-09 fone (11) 99999-8888 email a@b.com")
        assert "123.456.789-09" not in out, f"CPF should be masked, got: {out}"
        assert "a@b.com" in out, f"email should be preserved, got: {out}"
        assert "99999-8888" in out, f"phone should be preserved, got: {out}"
    finally:
        reset_chat_pii_mask_identity(tok)
    # After reset: passthrough again
    assert "123.456.789-09" in mask_pii_outbound("CPF 123.456.789-09")


def test_masks_rg_when_identity_on():
    """RG is masked when ContextVar is ON."""
    tok = set_chat_pii_mask_identity(True)
    try:
        out = mask_pii_outbound("RG 1.234.567-8")
        assert "1.234.567-8" not in out, f"RG should be masked, got: {out}"
    finally:
        reset_chat_pii_mask_identity(tok)


def test_masks_cnpj_when_identity_on():
    """CNPJ is masked when ContextVar is ON."""
    tok = set_chat_pii_mask_identity(True)
    try:
        out = mask_pii_outbound("CNPJ 12.345.678/0001-99")
        assert "12.345.678/0001-99" not in out, f"CNPJ should be masked, got: {out}"
    finally:
        reset_chat_pii_mask_identity(tok)


def test_resolution_hidden_via_override():
    """User override sets cpf=False → should_mask returns True."""
    assert chat_should_mask_identity(_user(override={"cpf": False}), {}) is True


def test_resolution_visible_default():
    """User can_view_sensitive_pii=True and no override → should_mask returns False."""
    assert chat_should_mask_identity(_user(can_sensitive=True), {}) is False


def test_resolution_hidden_via_role_default():
    """Role default sets recruiter.cpf=False → should_mask returns True."""
    assert chat_should_mask_identity(_user(), {"recruiter": {"cpf": False}}) is True


def test_non_string_passthrough():
    """Non-string input returns unchanged."""
    assert mask_pii_outbound(None) is None
    assert mask_pii_outbound(42) == 42


def test_empty_string_passthrough():
    """Empty string returns unchanged."""
    assert mask_pii_outbound("") == ""


def test_contextvar_isolation():
    """Nested set/reset works correctly (token-based isolation)."""
    tok1 = set_chat_pii_mask_identity(True)
    tok2 = set_chat_pii_mask_identity(False)
    # After setting False: passthrough
    assert "123.456.789-09" in mask_pii_outbound("CPF 123.456.789-09")
    reset_chat_pii_mask_identity(tok2)
    # After resetting tok2: back to True
    out = mask_pii_outbound("CPF 123.456.789-09")
    assert "123.456.789-09" not in out
    reset_chat_pii_mask_identity(tok1)
    # After resetting tok1: back to False (default)
    assert "123.456.789-09" in mask_pii_outbound("CPF 123.456.789-09")
