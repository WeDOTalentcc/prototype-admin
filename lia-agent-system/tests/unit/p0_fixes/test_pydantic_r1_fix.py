"""
TDD: Pydantic R1 sensor fix + 3 real violations resolved.

Tests verify:
1. Sensor recognises dict-literal model_config = {"extra": "forbid"} as compliant
2. CreateSourcingAgentRequest and FeedbackRequest now have extra='forbid'
3. TestWebhookRequest now has extra='forbid'
4. RegenerateQuestionsRequest is in SKIP_R1 (intentional extra='ignore')
"""
import ast
import subprocess
import sys
from pathlib import Path

REPO = Path('/home/runner/workspace/lia-agent-system')
SENSOR = REPO / 'scripts/check_pydantic_conventions.py'


def _run_sensor(*extra_args):
    result = subprocess.run(
        [sys.executable, str(SENSOR), str(REPO / 'app'), '--warn-only'] + list(extra_args),
        capture_output=True, text=True
    )
    return result.stdout + result.stderr


# --- Inline re-implementation of _has_extra_forbid for unit testing ---
def _has_extra_forbid(class_node: ast.ClassDef) -> bool:
    """Mirror of sensor's _has_extra_forbid — used to unit-test the logic."""
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "model_config" for t in stmt.targets):
            continue
        val = stmt.value
        if isinstance(val, ast.Call):
            for kw in val.keywords:
                if kw.arg == "extra" and isinstance(kw.value, ast.Constant):
                    if kw.value.value == "forbid":
                        return True
        if isinstance(val, ast.Dict):
            for k, v in zip(val.keys, val.values):
                if (
                    isinstance(k, ast.Constant) and k.value == "extra"
                    and isinstance(v, ast.Constant) and v.value == "forbid"
                ):
                    return True
    return False


def test_sensor_recognises_dict_literal_extra_forbid():
    """_has_extra_forbid must accept model_config = {'extra': 'forbid'} (dict literal)."""
    code = '''
class MyRequest:
    model_config = {"extra": "forbid"}
    name: str
'''
    cls = ast.parse(code).body[0]
    assert _has_extra_forbid(cls), "Dict literal extra='forbid' not recognised"


def test_sensor_still_recognises_configdict_call():
    """_has_extra_forbid must still accept ConfigDict(extra='forbid') call form."""
    code = '''
class MyRequest:
    model_config = ConfigDict(extra="forbid")
    name: str
'''
    cls = ast.parse(code).body[0]
    assert _has_extra_forbid(cls), "ConfigDict call form no longer recognised"


def test_sourcing_agents_schemas_have_extra_forbid():
    """CreateSourcingAgentRequest and FeedbackRequest must have extra='forbid'."""
    src = (REPO / 'app/api/v1/sourcing_agents.py').read_text()
    tree = ast.parse(src)
    results = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name in ('CreateSourcingAgentRequest', 'FeedbackRequest'):
            results[node.name] = _has_extra_forbid(node)
    assert 'CreateSourcingAgentRequest' in results, "CreateSourcingAgentRequest not found"
    assert 'FeedbackRequest' in results, "FeedbackRequest not found"
    assert results['CreateSourcingAgentRequest'], "CreateSourcingAgentRequest missing extra='forbid'"
    assert results['FeedbackRequest'], "FeedbackRequest missing extra='forbid'"


def test_teams_webhook_request_has_extra_forbid():
    """TestWebhookRequest must have extra='forbid'."""
    src = (REPO / 'app/api/v1/teams.py').read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'TestWebhookRequest':
            assert _has_extra_forbid(node), "TestWebhookRequest missing extra='forbid'"
            return
    raise AssertionError("TestWebhookRequest class not found in teams.py")


def test_regenerate_questions_in_skip_r1():
    """SKIP_R1 must include RegenerateQuestionsRequest (intentional extra='ignore')."""
    sensor_src = SENSOR.read_text()
    assert '"RegenerateQuestionsRequest"' in sensor_src, (
        "RegenerateQuestionsRequest not found in SKIP_R1"
    )


def test_sensor_reports_zero_r1_violations():
    """End-to-end: sensor must report 0 R1 violations against app/."""
    output = _run_sensor()
    assert 'R1 violation' not in output, f"Unexpected R1 violations:\n{output}"
    assert 'OK' in output or '0 violações' in output or 'conventions OK' in output, (
        f"Unexpected sensor output:\n{output}"
    )


if __name__ == '__main__':
    tests = [
        test_sensor_recognises_dict_literal_extra_forbid,
        test_sensor_still_recognises_configdict_call,
        test_sourcing_agents_schemas_have_extra_forbid,
        test_teams_webhook_request_has_extra_forbid,
        test_regenerate_questions_in_skip_r1,
        test_sensor_reports_zero_r1_violations,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f'  PASS {t.__name__}')
        except Exception as e:
            print(f'  FAIL {t.__name__}: {e}')
            failed += 1
    print(f'\n{len(tests) - failed}/{len(tests)} passed')
    sys.exit(failed)
