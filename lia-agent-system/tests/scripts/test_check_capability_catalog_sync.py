import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from check_capability_catalog_sync import extract_declared_names  # noqa: E402


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
