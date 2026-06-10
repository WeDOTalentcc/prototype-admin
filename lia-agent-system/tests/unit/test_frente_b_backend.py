"""
TDD tests para Frente B — B1 + B2 + B3.
SSH-safe: sem imports SQLAlchemy; lê os arquivos como texto e testa lógica pura.
"""
import sys
import re

# ─── Test 1: COMMUNICATION_RULES_DEFAULTS has B1+B2 keys (file content) ─────
def test_defaults_have_b1_b2():
    with open("/home/runner/workspace/lia-agent-system/libs/models/lia_models/company_hiring_policy.py") as f:
        src = f.read()
    assert '"briefing_frequency": "daily"' in src or '"briefing_frequency"' in src, \
        "B1: briefing_frequency missing from COMMUNICATION_RULES_DEFAULTS"
    assert '"digest_enabled": True' in src or '"digest_enabled"' in src, \
        "B2: digest_enabled missing from COMMUNICATION_RULES_DEFAULTS"
    
    # Verify default values from the dict block
    # Find the COMMUNICATION_RULES_DEFAULTS block
    match = re.search(r'COMMUNICATION_RULES_DEFAULTS = \{(.+?)\}', src, re.DOTALL)
    assert match, "COMMUNICATION_RULES_DEFAULTS not found"
    block = match.group(1)
    assert "briefing_frequency" in block, f"B1: not in block: {block}"
    assert "daily" in block, "B1: default value 'daily' not in block"
    assert "digest_enabled" in block, f"B2: not in block: {block}"
    assert "True" in block, "B2: default True not in block"
    print("PASS test_defaults_have_b1_b2")

# ─── Test 2: CommunicationRulesSchema has B1+B2 fields ──────────────────────
def test_schema_has_b1_b2():
    with open("/home/runner/workspace/lia-agent-system/app/schemas/company_hiring_policy.py") as f:
        src = f.read()
    assert "briefing_frequency" in src, "B1: briefing_frequency not in schema"
    assert "digest_enabled" in src, "B2: digest_enabled not in schema"
    # These should be inside CommunicationRulesSchema class
    match = re.search(r'class CommunicationRulesSchema\(BaseModel\):(.*?)(?=\nclass |\Z)', src, re.DOTALL)
    assert match, "CommunicationRulesSchema not found"
    block = match.group(1)
    assert "briefing_frequency" in block, f"B1: field not in CommunicationRulesSchema"
    assert "digest_enabled" in block, f"B2: field not in CommunicationRulesSchema"
    print("PASS test_schema_has_b1_b2")

# ─── Test 3: briefing_frequency + digest_enabled in _blocks_completed ────────
def test_blocks_completed_tracks_b1_b2():
    with open("/home/runner/workspace/lia-agent-system/app/api/v1/hiring_policy.py") as f:
        src = f.read()
    assert '"briefing_frequency"' in src, "B1: briefing_frequency not in hiring_policy.py"
    assert '"digest_enabled"' in src, "B2: digest_enabled not in hiring_policy.py"
    # Should be inside the communication_rules set
    match = re.search(r'"communication_rules": \{(.+?)\}', src)
    assert match, "communication_rules set not found in _blocks_completed"
    block = match.group(1)
    assert "briefing_frequency" in block, f"B1: not in communication_rules tracking: {block}"
    assert "digest_enabled" in block, f"B2: not in communication_rules tracking: {block}"
    print("PASS test_blocks_completed_tracks_b1_b2")

# ─── Test 4: weekly_digest_service has B2 gate logic ────────────────────────
def test_digest_service_has_gate():
    with open("/home/runner/workspace/lia-agent-system/app/domains/analytics/services/weekly_digest_service.py") as f:
        src = f.read()
    assert "digest_enabled" in src, "B2: digest_enabled not in weekly_digest_service.py"
    assert "digest_disabled_by_company" in src, "B2: skip reason not in service"
    assert "fail-open" in src or "fail_open" in src or "failopen" in src or "fail-open" in src, \
        "B2: fail-open comment not in service"
    assert 'company_id: str | None = None' in src, "B2: company_id param not added to generate_and_deliver"
    print("PASS test_digest_service_has_gate")

# ─── Test 5: digest gate logic (pure Python simulation) ──────────────────────
def test_digest_gate_logic():
    # Simulate the gate logic extracted from the service
    def gate(policy, company_id):
        if company_id:
            comm_rules = (policy or {}).get("communication_rules", {})
            if not comm_rules.get("digest_enabled", True):
                return {"skipped": True, "reason": "digest_disabled_by_company"}
        return None  # proceed
    
    # Disabled → skip
    r = gate({"communication_rules": {"digest_enabled": False}}, "co-123")
    assert r is not None and r["skipped"] is True
    
    # Enabled → proceed
    r = gate({"communication_rules": {"digest_enabled": True}}, "co-123")
    assert r is None
    
    # Missing → fail-open (proceed)
    r = gate({"communication_rules": {}}, "co-123")
    assert r is None
    
    # No company_id → skip gate entirely (backward compat)
    r = gate({"communication_rules": {"digest_enabled": False}}, None)
    assert r is None
    
    print("PASS test_digest_gate_logic")

# ─── Test 6: digest.py passes company_id (B2) ────────────────────────────────
def test_digest_py_passes_company_id():
    with open("/home/runner/workspace/lia-agent-system/app/api/v1/digest.py") as f:
        src = f.read()
    assert "company_id=company_id" in src, "B2: digest.py not passing company_id to generate_and_deliver"
    print("PASS test_digest_py_passes_company_id")

# ─── Test 7: notifications.py proactive/history uses DB (B3) ────────────────
def test_proactive_history_uses_db():
    with open("/home/runner/workspace/lia-agent-system/app/api/v1/notifications.py") as f:
        src = f.read()
    assert "ProactiveAction" in src, "B3: ProactiveAction not imported in notifications.py"
    assert "db.execute" in src, "B3: db.execute not used in notifications.py"
    assert '"source": "db"' in src or "'source': 'db'" in src or '\"source\": \"db\"' in src, \
        "B3: source=db marker missing"
    # Should have limit parameter
    assert "limit" in src, "B3: limit param missing from history endpoint"
    print("PASS test_proactive_history_uses_db")

# ─── Test 8: notifications.py no longer uses in-memory dict (B3) ────────────
def test_proactive_history_not_in_memory():
    with open("/home/runner/workspace/lia-agent-system/app/api/v1/notifications.py") as f:
        src = f.read()
    # Should NOT call get_alert_history anymore in the /proactive/history endpoint
    endpoint_section = re.search(r'@router\.get\("/proactive/history".*?(?=@router\.|$)', src, re.DOTALL)
    if endpoint_section:
        endpoint_body = endpoint_section.group(0)
        assert "get_alert_history" not in endpoint_body, \
            "B3: get_alert_history (in-memory) still called in proactive/history endpoint"
    print("PASS test_proactive_history_not_in_memory")

if __name__ == "__main__":
    test_defaults_have_b1_b2()
    test_schema_has_b1_b2()
    test_blocks_completed_tracks_b1_b2()
    test_digest_service_has_gate()
    test_digest_gate_logic()
    test_digest_py_passes_company_id()
    test_proactive_history_uses_db()
    test_proactive_history_not_in_memory()
    print("\n8/8 PASSED")
