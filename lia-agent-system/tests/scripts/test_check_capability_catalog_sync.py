import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from check_capability_catalog_sync import extract_declared_names  # noqa: E402
from check_capability_catalog_sync import extract_governance_refs  # noqa: E402


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
