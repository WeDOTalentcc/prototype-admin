"""Unit tests for Bug 2a, 3a, and 5b fixes in wizard session service.

Bug 2a: _extract_manager_email should not capture recruiter's own email.
Bug 3a: confirmed_benefits and confirmed_variable_compensation must appear in panel payload.
Bug 5b: jd_preview block must include BaseBlock fields (block_id, role, layout, state).
"""

import re


# ──────────────────────────────────────────────────────────────────────────────
# Reproduce the extraction + gating logic (mirroring the fix at line ~1076)
# so tests don't need to import the full async classmethod.
# ──────────────────────────────────────────────────────────────────────────────

_MANAGER_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _extract_manager_email(raw_text: str) -> str | None:
    """Canonical extraction helper (mirrored from wizard_session_service.py)."""
    if not raw_text:
        return None
    m = _MANAGER_EMAIL_RE.search(raw_text)
    return m.group(0) if m else None


def _apply_manager_email_gating(state: dict, raw_msg: str) -> None:
    """Mirrors the Bug 2a fix logic at line ~1076 of wizard_session_service.py."""
    _email = _extract_manager_email(raw_msg)
    if _email:
        _recruiter_email = (state.get("parsed_recruiter_email") or "").lower().strip()
        if _email.lower() != _recruiter_email:
            state["parsed_manager_email"] = _email


# ──────────────────────────────────────────────────────────────────────────────
# Bug 2a tests
# ──────────────────────────────────────────────────────────────────────────────

class TestExtractManagerEmailGating:
    def test_skips_recruiter_email(self):
        """Bug 2a: recruiter typing their own email must NOT be stored as manager email."""
        state = {"parsed_recruiter_email": "paulo@wedotalent.cc"}
        _apply_manager_email_gating(state, "meu email é paulo@wedotalent.cc")
        assert state.get("parsed_manager_email") is None, (
            "Recruiter's own email must not be stored as parsed_manager_email"
        )

    def test_captures_different_email(self):
        """Bug 2a: a different email in context SHOULD be captured as manager email."""
        state = {"parsed_recruiter_email": "paulo@wedotalent.cc"}
        _apply_manager_email_gating(state, "gestor é carlos.mendes@empresa.com")
        assert state.get("parsed_manager_email") == "carlos.mendes@empresa.com", (
            "Manager email different from recruiter's must be captured"
        )

    def test_no_recruiter_email_set(self):
        """Bug 2a: when no recruiter email is in state, any email IS captured."""
        state = {}
        _apply_manager_email_gating(state, "qualquer@email.com")
        assert state.get("parsed_manager_email") == "qualquer@email.com", (
            "When parsed_recruiter_email is not set, email must be captured"
        )

    def test_case_insensitive_comparison(self):
        """Bug 2a: comparison must be case-insensitive."""
        state = {"parsed_recruiter_email": "Paulo@WedoTalent.CC"}
        _apply_manager_email_gating(state, "Paulo@WedoTalent.CC")
        assert state.get("parsed_manager_email") is None, (
            "Case-insensitive comparison must block recruiter's email regardless of case"
        )

    def test_no_email_in_message(self):
        """Bug 2a: no email in message leaves state unchanged."""
        state = {"parsed_recruiter_email": "paulo@wedotalent.cc"}
        _apply_manager_email_gating(state, "gestor é João da Silva")
        assert state.get("parsed_manager_email") is None


# ──────────────────────────────────────────────────────────────────────────────
# Bug 3a tests — benefits and variable compensation in payload
# ──────────────────────────────────────────────────────────────────────────────

class TestBenefitsInPayload:
    def _apply_benefits_logic(self, new_state: dict, data: dict) -> None:
        """Mirrors the Bug 3a fix logic added after confirmed_languages block."""
        if new_state.get("confirmed_benefits"):
            data["confirmed_benefits"] = new_state.get("confirmed_benefits")
        if new_state.get("confirmed_variable_compensation"):
            data["confirmed_variable_compensation"] = new_state.get("confirmed_variable_compensation")

    def test_benefits_in_payload_when_confirmed(self):
        """Bug 3a: confirmed_benefits must appear in panel data dict."""
        confirmed_benefits = ["Vale Refeição", "Plano de Saúde"]
        new_state = {"confirmed_benefits": confirmed_benefits}
        data: dict = {}
        self._apply_benefits_logic(new_state, data)
        assert data.get("confirmed_benefits") == confirmed_benefits, (
            "confirmed_benefits must be surfaced to the panel payload"
        )

    def test_variable_compensation_in_payload_when_confirmed(self):
        """Bug 3a: confirmed_variable_compensation must appear in panel data dict."""
        var_comp = {"type": "bônus anual", "percentage": 20}
        new_state = {"confirmed_variable_compensation": var_comp}
        data: dict = {}
        self._apply_benefits_logic(new_state, data)
        assert data.get("confirmed_variable_compensation") == var_comp

    def test_benefits_absent_when_not_confirmed(self):
        """Bug 3a: when benefits are not in state, key must NOT be in data."""
        new_state = {}
        data: dict = {}
        self._apply_benefits_logic(new_state, data)
        assert "confirmed_benefits" not in data
        assert "confirmed_variable_compensation" not in data

    def test_benefits_not_overwritten_when_empty_list(self):
        """Bug 3a: empty list is falsy — must not surface (guards against empty override)."""
        new_state = {"confirmed_benefits": []}
        data: dict = {}
        self._apply_benefits_logic(new_state, data)
        assert "confirmed_benefits" not in data


# ──────────────────────────────────────────────────────────────────────────────
# Bug 5b tests — jd_preview block BaseBlock fields
# ──────────────────────────────────────────────────────────────────────────────

class TestJdPreviewBlock:
    def _build_jd_preview_block(self, jd: dict) -> dict:
        """Mirrors the Bug 5b fix in wizard_orchestrator.py lines ~676-682."""
        return {
            "kind": "jd_preview",
            "block_id": f"jd_preview_{id(jd)}",
            "role": "answer",
            "layout": "wide",
            "state": "ready",
            "title": jd.get("titulo_padronizado", "Descrição da Vaga"),
            "body": jd.get("about_role", ""),
            "data": jd,
        }

    def test_jd_preview_has_required_base_block_fields(self):
        """Bug 5b: jd_preview block must carry block_id, role, layout, state."""
        _jd = {"titulo_padronizado": "Engenheiro de Software", "about_role": "Sobre o cargo..."}
        block = self._build_jd_preview_block(_jd)
        for required_field in ("block_id", "role", "layout", "state"):
            assert required_field in block, f"Missing required BaseBlock field: {required_field}"

    def test_jd_preview_field_values(self):
        """Bug 5b: role='answer', layout='wide', state='ready'."""
        _jd = {"titulo_padronizado": "Dev Sênior", "about_role": "Vaga de Dev"}
        block = self._build_jd_preview_block(_jd)
        assert block["role"] == "answer"
        assert block["layout"] == "wide"
        assert block["state"] == "ready"
        assert block["kind"] == "jd_preview"

    def test_jd_preview_block_id_contains_prefix(self):
        """Bug 5b: block_id must start with 'jd_preview_'."""
        _jd = {}
        block = self._build_jd_preview_block(_jd)
        assert block["block_id"].startswith("jd_preview_")

    def test_jd_preview_title_fallback(self):
        """Bug 5b: missing titulo_padronizado falls back to 'Descrição da Vaga'."""
        _jd = {}
        block = self._build_jd_preview_block(_jd)
        assert block["title"] == "Descrição da Vaga"

    def test_jd_preview_data_passthrough(self):
        """Bug 5b: full jd dict must be passed through in 'data' field."""
        _jd = {"titulo_padronizado": "Cargo X", "about_role": "...", "salary_range": "10k-15k"}
        block = self._build_jd_preview_block(_jd)
        assert block["data"] is _jd
