"""Smoke test — api-vagas. Placeholder até extração completa do domínio."""
from pathlib import Path

def test_app_directory_structure():
    base = Path(__file__).parent.parent
    assert (base / main.py).exists(), main.py deve existir
    assert (base / Dockerfile).exists(), Dockerfile deve existir
