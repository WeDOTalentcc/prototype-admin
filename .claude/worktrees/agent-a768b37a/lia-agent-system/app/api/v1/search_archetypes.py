"""
Search Archetypes API - Additional endpoints for archetype management.

Note: Core archetype endpoints (list, get, delete, create) are defined in
candidate_search.py which has the /search prefix. This file provides 
additional utility endpoints that don't conflict with existing routes.

The main endpoints are:
- GET /search/archetypes - List all archetypes (in candidate_search.py)
- POST /search/archetypes - Create archetype (in candidate_search.py)
- POST /search/archetypes/from-search - Create from search spec (in candidate_search.py)
- GET /search/archetypes/{id} - Get by ID (in candidate_search.py)
- DELETE /search/archetypes/{id} - Delete archetype (in candidate_search.py)
"""
from fastapi import APIRouter

router = APIRouter()
