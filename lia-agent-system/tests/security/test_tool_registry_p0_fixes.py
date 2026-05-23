import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


def test_update_priority_requires_company_id_in_sql():
    src = (REPO_ROOT / "app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py").read_text()
    update_idx = src.find("UPDATE job_vacancies SET priority")
    assert update_idx != -1, "UPDATE priority query not found"
    snippet = src[update_idx:update_idx+200]
    assert "company_id" in snippet, "UPDATE priority deve ter company_id no WHERE"


def test_kanban_no_cross_tenant_cid_bypass():
    src = (REPO_ROOT / "app/domains/recruiter_assistant/agents/kanban_tool_registry.py").read_text()
    bypass = ":cid = " + chr(39)*2
    assert bypass not in src, "Cross-tenant bypass via :cid=empty deve ser removido"


def test_talent_rank_no_fstring_sql():
    src = (REPO_ROOT / "app/domains/recruiter_assistant/agents/talent_tool_registry.py").read_text()
    # Detect text(f""" pattern - f-string SQL
    fstring_sql = r"text(f" + chr(34)*3
    assert fstring_sql not in src, "f-string em SQL detectada em talent_tool_registry.py"
