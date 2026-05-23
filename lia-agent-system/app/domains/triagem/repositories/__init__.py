"""
P2 D (2026-05-23): TriagemRepository consolidation — canonical single source.

Antes desta consolidação coexistiam duas classes com mesmo papel:
  1. domains/triagem/repositories/triagem_repository.py — STUB vazio
  2. domains/recruitment/repositories/triagem_session_repository.py — CANONICAL

Decisão Paulo: domain `triagem` mantém router/schemas; repository pertence ao
domain `recruitment` (onde vivem services + state). Stub deletado, alias
`TriagemRepository` re-exporta canonical para backward compat de imports
externos durante migração.

Refs: backlog P2 D + P0 fix triagem 497e30429.
"""
from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)

# Backward compat alias — código legacy importa `TriagemRepository`.
# Novos consumers devem importar `TriagemSessionRepository` direto do canonical.
TriagemRepository = TriagemSessionRepository

__all__ = ["TriagemRepository", "TriagemSessionRepository"]
