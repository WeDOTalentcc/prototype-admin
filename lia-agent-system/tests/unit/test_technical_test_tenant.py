"""UC-P1-02: TechnicalTest must have company_id (nullable for global tests)."""


def test_technical_test_has_company_id():
    """Verify company_id column exists on the TechnicalTest model."""
    # TechnicalTest is NOT in libs/__init__, safe to import directly
    from lia_models.technical_tests import TechnicalTest
    cols = [c.key for c in TechnicalTest.__table__.columns]
    assert "company_id" in cols, f"TechnicalTest must have company_id, got: {cols}"


def test_company_id_nullable_for_global_tests():
    """Global tests (is_global=True) have no company_id — nullable is correct."""
    from lia_models.technical_tests import TechnicalTest
    col = TechnicalTest.__table__.c["company_id"]
    assert col.nullable is True, "company_id must be nullable (global tests have no tenant)"
