"""
P1 C — `mask_pii` (log scrubber) deve preservar UUID v4.

Origem: logs `[LLM-AUDIT]` em `app/shared/llm/callbacks.py:72` passam
`tenant=<company_id>` como arg de log; `PIIMaskingFilter.filter` aplica
`mask_pii(str(v))` em cada arg, e `PHONE_BR_PATTERN` (`\\d{4}[-\\s]?\\d{4}\\b`)
casa segmentos internos de UUIDs v4 destruindo-os em
`xxxxxxxx-xxxx-***PHONE***-xxxx-xxxxxxxxxxxx` (debug acessibility quebrada,
e tenant id contaminado em logs).

Fix canônico: mesmo guard-token pattern já aplicado em
`strip_pii_for_llm_prompt` (R1/T-F) — UUIDs viram placeholders opacos antes do
strip e voltam depois. Garante invariante "UUID v4 nunca é PII".

Contratos defendidos:
  1. UUIDs v4 sobrevivem intactos a `mask_pii`.
  2. Telefones BR continuam mascarados como `***PHONE***`.
  3. Outros PII (CPF, email) continuam mascarados.
  4. UUIDs v4 v3/v5 (não-v4) podem seguir comportamento legado.
  5. `PIIMaskingFilter` end-to-end preserva UUID em log args.
"""
from __future__ import annotations

import logging
import re
import uuid

import pytest

from app.shared.pii_masking import PIIMaskingFilter, mask_pii

DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"
REAL_UUID_FROM_BUG_REPORT = "3df30e82-0c05-4064-9462-354d1d6a32b7"

_UUID_V4_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


class TestUUIDV4PreservedInMaskPII:
    """Contrato 1: UUID v4 NUNCA pode ser quebrado pelo mask_pii (log scrubber)."""

    def test_demo_company_uuid_alone(self):
        result = mask_pii(DEMO_COMPANY_UUID)
        assert DEMO_COMPANY_UUID in result, result

    def test_real_uuid_from_bug_report(self):
        text = f"Session token: {REAL_UUID_FROM_BUG_REPORT}"
        result = mask_pii(text)
        assert REAL_UUID_FROM_BUG_REPORT in result, result

    def test_uuid_in_log_message(self):
        text = f"[LLM-AUDIT] tenant={REAL_UUID_FROM_BUG_REPORT} caller=foo"
        result = mask_pii(text)
        assert REAL_UUID_FROM_BUG_REPORT in result, result

    @pytest.mark.parametrize("_seed", list(range(50)))
    def test_50_random_uuid_v4_survive(self, _seed):
        u = str(uuid.uuid4())
        text = f"tenant_id={u}; processing..."
        result = mask_pii(text)
        assert u in result, result

    def test_multiple_uuids_same_text(self):
        u1 = str(uuid.uuid4())
        u2 = str(uuid.uuid4())
        text = f"company={u1} job={u2}"
        result = mask_pii(text)
        assert u1 in result, result
        assert u2 in result, result


class TestPhoneBRStillMasked:
    """Contrato 2: regressão — telefones BR continuam mascarados como ***PHONE***."""

    @pytest.mark.parametrize(
        "phone",
        [
            "+55 11 91234-5678",
            "(11) 91234-5678",
            "11 91234-5678",
            "1234-5678",
        ],
    )
    def test_phone_still_masked(self, phone):
        text = f"Contact: {phone}"
        result = mask_pii(text)
        assert "***PHONE***" in result, result

    def test_phone_and_uuid_coexist(self):
        u = DEMO_COMPANY_UUID
        text = f"tenant={u}; phone 11 91234-5678"
        result = mask_pii(text)
        assert u in result, result
        assert "***PHONE***" in result, result


class TestOtherPIIStillMasked:
    """Contrato 3: outros PII continuam mascarados (CPF, email)."""

    def test_email_masked_with_uuid_preserved(self):
        text = f"user={DEMO_COMPANY_UUID} email=john@example.com"
        result = mask_pii(text)
        assert DEMO_COMPANY_UUID in result, result
        assert "***EMAIL***" in result, result

    def test_cpf_masked_with_uuid_preserved(self):
        text = f"tenant={DEMO_COMPANY_UUID} cpf=123.456.789-00"
        result = mask_pii(text)
        assert DEMO_COMPANY_UUID in result, result
        assert "***CPF***" in result, result


class TestPIIMaskingFilterEndToEnd:
    """Contrato 4: PIIMaskingFilter (usado em PIIMaskingFilter.filter) end-to-end."""

    def test_filter_preserves_uuid_in_log_record_args(self):
        pii_filter = PIIMaskingFilter()
        record = logging.LogRecord(
            name="lia.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="[LLM-AUDIT] tenant=%s caller=%s",
            args=(REAL_UUID_FROM_BUG_REPORT, "agent_chat"),
            exc_info=None,
        )
        pii_filter.filter(record)
        # args foram processados via mask_pii
        assert REAL_UUID_FROM_BUG_REPORT in record.args, record.args

    def test_filter_preserves_uuid_in_log_record_msg(self):
        pii_filter = PIIMaskingFilter()
        msg = f"[LLM-AUDIT] tenant={DEMO_COMPANY_UUID} caller=foo"
        record = logging.LogRecord(
            name="lia.test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=msg,
            args=(),
            exc_info=None,
        )
        pii_filter.filter(record)
        assert DEMO_COMPANY_UUID in record.msg, record.msg
