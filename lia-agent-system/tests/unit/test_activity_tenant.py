"""UC-P1-03: ActivityFeed and AgentActivity must have company_id."""


def test_activity_feed_has_company_id():
    """Verify company_id column exists on ActivityFeed.

    ActivityFeed IS in libs/__init__, so use Base.metadata.tables to avoid
    the MetaData collision from duplicate class definition.
    """
    import libs.models.lia_models  # noqa: F401 — registers all models
    from lia_config.database import Base
    table = Base.metadata.tables["activity_feed"]
    cols = list(table.columns.keys())
    assert "company_id" in cols, f"ActivityFeed must have company_id, got: {cols}"


def test_agent_activity_has_company_id():
    """Verify company_id column exists on AgentActivity.

    AgentActivity is NOT in libs/__init__, safe to import directly.
    """
    from libs.models.lia_models.agent_activity import AgentActivity
    cols = [c.key for c in AgentActivity.__table__.columns]
    assert "company_id" in cols, f"AgentActivity must have company_id, got: {cols}"
