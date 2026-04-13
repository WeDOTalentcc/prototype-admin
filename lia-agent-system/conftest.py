"""Root conftest.py — sets test environment variables before app modules are imported."""
import os

# Disable ResponseEnvelopeMiddleware in tests: it wraps responses in {"ok": true, "data": {...}}
# which breaks all existing tests that check raw JSON response shapes.
# The middleware is tested separately in tests/test_api_contract.py.
os.environ.setdefault("LIA_DISABLE_ENVELOPE_MIDDLEWARE", "1")
