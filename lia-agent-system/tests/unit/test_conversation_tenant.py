"""UC-P1-01: Conversation model must have company_id for tenant isolation."""


def test_conversation_has_company_id():
    """Verify company_id column exists on the conversations table."""
    # Import via the package __init__ to avoid MetaData collision
    import libs.models.lia_models  # noqa: F401 — triggers registration
    from lia_config.database import Base
    table = Base.metadata.tables["conversations"]
    cols = list(table.columns.keys())
    assert "company_id" in cols, f"Conversation must have company_id column, got: {cols}"


def test_conversation_company_id_indexed():
    """Verify company_id has a single-column index on conversations."""
    import libs.models.lia_models  # noqa: F401
    from lia_config.database import Base
    table = Base.metadata.tables["conversations"]
    indexed_cols = [
        list(idx.columns.keys())[0]
        for idx in table.indexes
        if len(list(idx.columns)) == 1
    ]
    assert "company_id" in indexed_cols, "company_id must be indexed"
