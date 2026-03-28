"""
Pytest configuration for e2e tests.

O event_loop fixture não é definido aqui — o pytest.ini já configura
asyncio_default_fixture_loop_scope = session, fornecendo um único loop
compartilhado por toda a sessão (evita conflitos com asyncpg/ASGITransport).
"""
import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
