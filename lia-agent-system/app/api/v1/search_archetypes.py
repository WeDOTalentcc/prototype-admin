"""
Search Archetypes API - Namespace reservation only.

WT-2022 P1.ARCH: Este arquivo intencionalmente exporta um APIRouter VAZIO.
Os endpoints reais de archetypes vivem em:

    app/api/v1/candidate_search/archetypes.py   (canonical, prefix /search)

Endpoints reais (canonical):
- GET    /search/archetypes              list all archetypes
- POST   /search/archetypes              create archetype
- POST   /search/archetypes/from-search  create from search spec
- GET    /search/archetypes/{id}         get by ID
- DELETE /search/archetypes/{id}         delete archetype

Este arquivo e mantido apenas para evitar import errors em codigo legacy que
pode referenciar app.api.v1.search_archetypes. Para features novas, NAO adicionar
rotas aqui - usar candidate_search/archetypes.py.
"""
from fastapi import APIRouter

# Namespace reservation only - intentionally empty.
# Real router lives in app/api/v1/candidate_search/archetypes.py
router = APIRouter()
