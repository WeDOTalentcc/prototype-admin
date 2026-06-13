"""Smoke test api-vagas."""
from pathlib import Path

def test_structure():
    base = Path(__file__).parent.parent
    assert (base / "main.py").exists()
    assert (base / "Dockerfile").exists()
