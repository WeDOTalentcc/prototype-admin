"""
Sentinel tests — B6 Desconto ALFA.

Static file-based checks (avoid SQLAlchemy MetaData conflicts).
Validates: migration exists + Subscription model fields + admin endpoint + plan-summary wiring.
"""
import re, os

BASE = "/home/runner/workspace/lia-agent-system"

def test_migration_294_exists():
    mig = os.path.join(BASE, "alembic/versions/294_desconto_alfa.py")
    assert os.path.exists(mig), "Migration 294_desconto_alfa.py must exist"

def test_migration_adds_desconto_pct():
    mig = open(os.path.join(BASE, "alembic/versions/294_desconto_alfa.py")).read()
    assert "desconto_pct" in mig, "Migration must add desconto_pct column"
    assert "desconto_validade" in mig, "Migration must add desconto_validade column"
    assert "server_default='0'" in mig, "desconto_pct must have server_default=0 (non-breaking)"

def test_migration_down_revision_is_293():
    mig = open(os.path.join(BASE, "alembic/versions/294_desconto_alfa.py")).read()
    assert "down_revision = '293'" in mig, "down_revision must be '293'"

def test_subscription_model_has_desconto_pct():
    billing = open(os.path.join(BASE, "libs/models/lia_models/billing.py")).read()
    assert "desconto_pct" in billing, "Subscription model must have desconto_pct column"
    assert "Numeric" in billing, "Subscription model must import Numeric for decimal precision"
    assert "desconto_validade" in billing, "Subscription model must have desconto_validade column"

def test_subscription_to_dict_includes_desconto():
    billing = open(os.path.join(BASE, "libs/models/lia_models/billing.py")).read()
    assert '"desconto_pct"' in billing, "to_dict() must include desconto_pct"

def test_admin_api_has_discount_endpoint():
    api = open(os.path.join(BASE, "app/api/v1/admin_plan_api.py")).read()
    assert "set_subscription_discount" in api, "admin_plan_api must have set_subscription_discount endpoint"
    assert "/discount" in api, "Discount endpoint must be at /discount path"
    assert "DiscountRequest" in api, "Must have DiscountRequest schema"
    assert 'extra="forbid"' in api, "DiscountRequest must use extra=forbid (Pydantic R1)"

def test_discount_schema_no_company_id_in_payload():
    api = open(os.path.join(BASE, "app/api/v1/admin_plan_api.py")).read()
    # Extract DiscountRequest class
    match = re.search(r"class DiscountRequest\(.*?\):(.*?)(?=\n\n|\n@|\nclass |\Z)", api, re.DOTALL)
    if match:
        body = match.group(1)
        assert "company_id" not in body, "DiscountRequest must NOT have company_id in payload (LGPD R2)"

def test_discount_pct_range_validated():
    api = open(os.path.join(BASE, "app/api/v1/admin_plan_api.py")).read()
    assert "ge=0" in api, "desconto_pct must validate ge=0"
    assert "le=100" in api, "desconto_pct must validate le=100"

def test_plan_summary_exposes_desconto():
    billing_api = open(os.path.join(BASE, "app/api/v1/billing.py")).read()
    assert "plan_data[\"desconto\"]" in billing_api or 'plan_data["desconto"]' in billing_api, \
        "my-plan-summary must set plan_data['desconto'] when desconto_pct > 0"

def test_plan_summary_desconto_only_when_active():
    billing_api = open(os.path.join(BASE, "app/api/v1/billing.py")).read()
    assert "if desconto_pct > 0" in billing_api, \
        "desconto section must be conditional (only when pct > 0, zero impact for non-ALFA)"
