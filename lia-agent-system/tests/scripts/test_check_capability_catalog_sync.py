import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from check_capability_catalog_sync import extract_declared_names  # noqa: E402
from check_capability_catalog_sync import extract_governance_refs  # noqa: E402
from check_capability_catalog_sync import compute_ghosts, format_report  # noqa: E402


def test_extract_declared_names_string_literal():
    src = '''
ToolDefinition(name="search_candidates", description="x")
make_tool(name='move_candidate')
'''
    assert extract_declared_names(src) == {"search_candidates", "move_candidate"}


def test_extract_declared_names_ignores_dynamic():
    src = 'ToolDefinition(name=list_name, description="x")'
    assert extract_declared_names(src) == set()


def test_extract_declared_names_empty_on_garbage():
    assert extract_declared_names("def f(): pass") == set()


def test_extract_governance_refs_scopes_and_restricted():
    yaml_text = '''
version: '1.0'
global:
  scopes:
    talent_funnel:
      query:
        - search_candidates
        - get_candidate_details
      action:
        - move_candidate
restricted_tools:
  - close_job
  - cancel_vacancy
tenants: {}
'''
    refs = extract_governance_refs(yaml_text)
    assert refs["search_candidates"]
    assert "cancel_vacancy" in refs
    assert "close_job" in refs
    assert "restricted_tools" in refs["cancel_vacancy"]
    assert any("scope:talent_funnel" in o for o in refs["search_candidates"])


def test_compute_ghosts():
    refs = {"search_candidates": ["scope:talent.query"], "cancel_vacancy": ["restricted_tools"]}
    declared = {"search_candidates", "move_candidate"}
    exempt = set()
    ghosts = compute_ghosts(refs, declared, exempt)
    assert [g["name"] for g in ghosts] == ["cancel_vacancy"]
    assert ghosts[0]["origins"] == ["restricted_tools"]


def test_compute_ghosts_respects_exempt():
    refs = {"export_candidates": ["restricted_tools"]}
    ghosts = compute_ghosts(refs, set(), exempt={"export_candidates"})
    assert ghosts == []


def test_format_report_mentions_fix():
    report = format_report([{"name": "cancel_vacancy", "origins": ["restricted_tools"]}])
    assert "cancel_vacancy" in report
    assert "restricted_tools" in report
    assert "Fix" in report


from check_capability_catalog_sync import scan_declared_in_tree, EXEMPT_NAMES  # noqa: E402


def test_scan_declared_in_tree(tmp_path):
    d = tmp_path / "app" / "domains" / "x" / "agents"
    d.mkdir(parents=True)
    (d / "x_tool_registry.py").write_text('ToolDefinition(name="rank_candidates")\n')
    (d / "other.py").write_text('make_tool(name="view_job_details")\n')
    found = scan_declared_in_tree(tmp_path / "app")
    assert "rank_candidates" in found
    assert "view_job_details" in found


def test_exempt_names_is_set():
    assert isinstance(EXEMPT_NAMES, set)
