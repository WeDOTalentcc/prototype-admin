"""G6 sensor: shared_searches endpoint must verify LGPD consent before sharing PII with third parties.

LGPD Art. 7 requires explicit consent before disclosing candidate PII to external
recipients (hiring managers via link+OTP). This is distinct from recruiter viewing
their own data (ADR-LGPD-002, Art. 7 II legítimo interesse).

Sensor type: static source analysis (computacional, não-inferencial).
"""
import pytest


def _read_create_shared_search_body() -> str:
    """Extract the body of create_shared_search from shared_searches.py."""
    with open("app/api/v1/shared_searches.py") as f:
        source = f.read()

    lines = source.split("\n")
    in_create = False
    body_lines = []
    indent_level = None

    for line in lines:
        if "async def create_shared_search" in line:
            in_create = True
            indent_level = len(line) - len(line.lstrip())
            continue
        elif in_create:
            # Next top-level function = end of create_shared_search
            stripped = line.lstrip()
            if stripped.startswith("async def ") or stripped.startswith("def "):
                current_indent = len(line) - len(stripped)
                if current_indent <= indent_level:
                    break
            body_lines.append(line)

    return "\n".join(body_lines)


class TestG6SharedSearchLGPDConsent:
    """G6 sensor: LGPD consent gate in create_shared_search."""

    def test_create_shared_search_has_consent_check(self):
        """create_shared_search must verify communication_consent before sharing PII.

        Fix: add consent gate before build_candidate_snapshot in shared_searches.py.
        """
        body = _read_create_shared_search_body()
        assert "consent" in body.lower(), (
            "G6 LGPD violation: create_shared_search in shared_searches.py does not check "
            "candidate consent before sharing PII with third parties. "
            "Add communication_consent verification before build_candidate_snapshot."
        )

    def test_consent_gate_is_before_snapshot_build(self):
        """Consent gate must appear BEFORE build_candidate_snapshot call.

        Fix: move consent check above the build_candidate_snapshot call.
        """
        body = _read_create_shared_search_body()
        consent_pos = body.lower().find("consent")
        snapshot_pos = body.find("build_candidate_snapshot")

        assert consent_pos != -1, "No consent reference found in create_shared_search"
        assert snapshot_pos != -1, "No build_candidate_snapshot call found"
        assert consent_pos < snapshot_pos, (
            "G6 LGPD violation: consent check appears AFTER build_candidate_snapshot. "
            "Candidate PII is snapshotted before consent is verified. Move gate before snapshot."
        )

    def test_consent_gate_raises_422_on_missing_consent(self):
        """Consent gate must raise HTTP 422 with structured error detail.

        Fix: raise HTTPException(status_code=422, detail={error: lgpd_consent_missing, ...})
        """
        body = _read_create_shared_search_body()
        assert "lgpd_consent_missing" in body, (
            "G6 LGPD violation: consent gate does not raise structured 422 with "
            "lgpd_consent_missing error code. Add HTTPException(422, detail={error: ...})."
        )

    def test_consent_gate_reports_non_consenting_candidate_ids(self):
        """Response must include candidate_ids_without_consent for FE to display.

        Fix: include candidate_ids_without_consent in the 422 detail dict.
        """
        body = _read_create_shared_search_body()
        assert "candidate_ids_without_consent" in body, (
            "G6 LGPD violation: consent gate does not report which candidates lack consent. "
            "Include candidate_ids_without_consent in the 422 error detail."
        )

    def test_consent_check_uses_communication_consent_field(self):
        """Must check the canonical communication_consent field on Candidate model.

        Fix: use getattr(candidate, communication_consent, False) or c.communication_consent.
        """
        body = _read_create_shared_search_body()
        assert "communication_consent" in body, (
            "G6 LGPD violation: consent gate does not check communication_consent field. "
            "This is the canonical consent field on the Candidate model (line 311)."
        )
