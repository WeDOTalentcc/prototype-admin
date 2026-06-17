"""Canonical integration adapters (W2-010, 2026-05-22).

Houses unified Rails HTTP client + future external integrations.

Migration roadmap (Phase A — current):
- `app/shared/rails_client.py` → deprecation shim re-exporting from here
- 13 callers usam shim sem mudança de import path
- 2 instanciações diretas de WeDOTalentATSClient permanecem (rails_adapter,
  shim singleton) até Phase B

Phase B (deferida): migrar `WeDOTalentATSClient` (587 LOC) + resolver
incompatibilidade OTT vs Bearer auth com `JobCreationAPIClient`.
"""
