"""Unit tests — CompanyId value object (T-A canonical infra)."""
from __future__ import annotations

from uuid import UUID

import pytest

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.value_objects.company_id import CompanyId


class TestParseValid:
    def test_uuid_object_normalized_lowercase(self):
        u = UUID("00000000-0000-4000-A000-000000000001")
        cid = CompanyId.parse(u)
        assert cid.value == "00000000-0000-4000-a000-000000000001"
        assert cid.is_uuid is True
        assert cid.is_slug is False

    def test_uuid_string_uppercase_normalized(self):
        cid = CompanyId.parse("00000000-0000-4000-A000-000000000001")
        assert cid.value == "00000000-0000-4000-a000-000000000001"

    def test_uuid_string_with_whitespace_stripped(self):
        cid = CompanyId.parse("  00000000-0000-4000-a000-000000000001  ")
        assert cid.value == "00000000-0000-4000-a000-000000000001"

    def test_slug_demo_company(self):
        cid = CompanyId.parse("demo_company")
        assert cid.value == "demo_company"
        assert cid.is_slug is True
        assert cid.is_uuid is False

    def test_slug_with_dashes(self):
        cid = CompanyId.parse("acme-corp-2026")
        assert cid.value == "acme-corp-2026"

    def test_parse_idempotent(self):
        cid1 = CompanyId.parse("demo_company")
        cid2 = CompanyId.parse(cid1.as_str())
        assert cid1 == cid2


class TestParseInvalid:
    @pytest.mark.parametrize("bad", ["", "   ", "\t\n"])
    def test_empty_or_whitespace_rejected(self, bad):
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(bad)
        assert exc.value.code == "INVALID_COMPANY_ID"
        assert exc.value.details.get("reason") == "empty"

    def test_none_rejected(self):
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(None)
        assert exc.value.details.get("reason") == "none"

    @pytest.mark.parametrize("bad", ["default", "DEFAULT", "None", "null", "system", "anonymous"])
    def test_forbidden_literals_rejected(self, bad):
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(bad)
        assert exc.value.details.get("reason") == "forbidden_literal"

    def test_truncated_uuid_rejected(self):
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse("00000000-0000-4000-a000")
        assert exc.value.details.get("reason") == "format"

    def test_slug_too_short_rejected(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("ab")  # < 3 chars

    def test_slug_starts_with_digit_rejected(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("1company")

    def test_slug_with_uppercase_rejected_after_normalize_back_to_slug(self):
        # "Acme!" → strip+lower → "acme!" → não casa SLUG_RE
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("Acme!")

    def test_non_str_non_uuid_rejected(self):
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(12345)  # type: ignore[arg-type]
        assert exc.value.details.get("reason") == "type"


class TestAccessors:
    def test_as_uuid_on_uuid_value(self):
        cid = CompanyId.parse("00000000-0000-4000-a000-000000000001")
        assert cid.as_uuid() == UUID("00000000-0000-4000-a000-000000000001")

    def test_as_uuid_on_slug_raises(self):
        cid = CompanyId.parse("demo_company")
        with pytest.raises(InvalidCompanyIdError) as exc:
            cid.as_uuid()
        assert exc.value.details.get("reason") == "slug_not_uuid"

    def test_str_returns_value(self):
        cid = CompanyId.parse("demo_company")
        assert str(cid) == "demo_company"

    def test_frozen_equality_and_hash(self):
        a = CompanyId.parse("demo_company")
        b = CompanyId.parse("DEMO_COMPANY")
        assert a == b
        assert hash(a) == hash(b)
        # frozen
        with pytest.raises(Exception):
            a.value = "other"  # type: ignore[misc]


class TestUuidVersionEnforcement:
    """T-A R-1: política do projeto é UUID v4 only (v1/v3/v5 vazam metadata)."""

    def test_uuid_v1_rejected(self):
        from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

        # UUID v1 conhecido (timestamp+MAC); o "1" no terceiro grupo marca a versão
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse("550e8400-e29b-11d4-a716-446655440000")
        assert exc.value.details.get("reason") == "uuid_version"
        assert exc.value.details.get("uuid_version") == 1

    def test_uuid_v3_rejected(self):
        from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse("a3bb189e-8bf9-3888-9912-ace4e6543002")
        assert exc.value.details.get("uuid_version") == 3

    def test_uuid_v5_rejected(self):
        from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse("886313e1-3b8a-5372-9b90-0c9aee199e5d")
        assert exc.value.details.get("uuid_version") == 5

    def test_uuid_v4_accepted(self):
        cid = CompanyId.parse("00000000-0000-4000-a000-000000000001")
        assert cid.is_uuid is True
        assert cid.as_uuid().version == 4

    def test_is_uuid_false_for_non_v4_string_via_parse(self):
        # Garante que is_uuid não regrediu para "qualquer UUID"
        v4 = CompanyId.parse("00000000-0000-4000-a000-000000000001")
        assert v4.is_uuid is True


class TestUuidVersionEnforcementOnUuidObjects:
    """T-A R-1 (round 3): branch UUID-object também exige v4."""

    def test_uuid_v1_object_rejected(self):
        from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

        v1 = UUID("550e8400-e29b-11d4-a716-446655440000")
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(v1)
        assert exc.value.details.get("reason") == "uuid_version"
        assert exc.value.details.get("uuid_version") == 1

    def test_uuid_v3_object_rejected(self):
        from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

        v3 = UUID("a3bb189e-8bf9-3888-9912-ace4e6543002")
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(v3)
        assert exc.value.details.get("uuid_version") == 3

    def test_uuid_v5_object_rejected(self):
        from app.shared.exceptions.tenant_errors import InvalidCompanyIdError

        v5 = UUID("886313e1-3b8a-5372-9b90-0c9aee199e5d")
        with pytest.raises(InvalidCompanyIdError) as exc:
            CompanyId.parse(v5)
        assert exc.value.details.get("uuid_version") == 5

    def test_uuid_v4_object_accepted(self):
        v4 = UUID("00000000-0000-4000-a000-000000000001")
        cid = CompanyId.parse(v4)
        assert cid.is_uuid is True
        assert cid.as_uuid() == v4
