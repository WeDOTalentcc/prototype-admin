#!/bin/bash
# Sprint 0 — Deploy Phase 6 Hardening to Replit
# Execute este script DENTRO do Replit (lia-agent-system root)
# Pré-requisito: lia-hardening/ deve estar no mesmo diretório ou copiado

set -e

echo "=== Sprint 0: Deploy Phase 6 Hardening ==="
echo ""

# --- 1. Migrations ---
echo ">>> 1/6: Copiando migrations..."
cp lia-hardening/migrations/055_create_talent_pools.py alembic/versions/ 2>/dev/null || echo "  SKIP: 055 já existe ou path diferente"
cp lia-hardening/migrations/056_create_sourcing_agents.py alembic/versions/ 2>/dev/null || echo "  SKIP: 056"
cp lia-hardening/migrations/057_create_recruitment_campaigns.py alembic/versions/ 2>/dev/null || echo "  SKIP: 057"
cp lia-hardening/migrations/058_create_digital_twins.py alembic/versions/ 2>/dev/null || echo "  SKIP: 058"

echo ">>> Executando migrations..."
alembic upgrade head || echo "  WARN: alembic upgrade falhou. Verificar manualmente."

# --- 2. Models ---
echo ""
echo ">>> 2/6: Copiando models..."
cp lia-hardening/agent_studio/sourcing_agent_model.py app/models/sourcing_agent.py
cp lia-hardening/digital_twins/digital_twin_model.py app/models/digital_twin.py

# --- 3. Services ---
echo ""
echo ">>> 3/6: Copiando services..."
cp lia-hardening/agent_studio/sourcing_agent_orchestrator.py app/services/sourcing_agent_orchestrator.py
cp lia-hardening/agent_studio/multi_strategy_search.py app/services/multi_strategy_search.py
cp lia-hardening/digital_twins/twin_knowledge_indexer.py app/services/twin_knowledge_indexer.py
cp lia-hardening/digital_twins/twin_inference_service.py app/services/twin_inference_service.py
cp lia-hardening/voice_screening/voice_interview_state_machine.py app/services/voice_interview_state_machine.py
cp lia-hardening/talent_pool/wsi_compact_pipeline.py app/services/wsi_compact_pipeline.py

# --- 4. API Endpoints ---
echo ""
echo ">>> 4/6: Copiando API endpoints..."
mkdir -p app/shared/agent_templates
cp lia-hardening/agent_studio/sector_templates.py app/shared/agent_templates/sector_templates.py
cp lia-hardening/agent_studio/sector_templates_api.py app/api/v1/sector_templates.py
cp lia-hardening/agent_studio/sourcing_agents_api.py app/api/v1/sourcing_agents.py
cp lia-hardening/agent_studio/multi_strategy_api.py app/api/v1/multi_strategy_search.py
cp lia-hardening/digital_twins/digital_twins_api.py app/api/v1/digital_twins.py
cp lia-hardening/voice_screening/voice_screening_api.py app/api/v1/voice_screening.py

# --- 5. Instruções manuais ---
echo ""
echo ">>> 5/6: AÇÃO MANUAL NECESSÁRIA"
echo "   Adicionar ao app/main.py:"
echo ""
echo "   from app.api.v1.sector_templates import router as sector_templates_router"
echo "   from app.api.v1.sourcing_agents import router as sourcing_agents_router"
echo "   from app.api.v1.multi_strategy_search import router as multi_strategy_router"
echo "   from app.api.v1.digital_twins import router as digital_twins_router"
echo "   from app.api.v1.voice_screening import router as voice_screening_router"
echo ""
echo "   app.include_router(sector_templates_router)"
echo "   app.include_router(sourcing_agents_router)"
echo "   app.include_router(multi_strategy_router)"
echo "   app.include_router(digital_twins_router)"
echo "   app.include_router(voice_screening_router)"

echo ""
echo ">>> 6/6: AÇÃO MANUAL NECESSÁRIA"
echo "   Substituir Depends(lambda: None) pelos deps reais em TODOS os novos endpoints."
echo "   Buscar: Depends(lambda: None)"
echo "   Substituir por: Depends(get_current_user) ou Depends(get_db)"

echo ""
echo "=== Sprint 0 COMPLETO ==="
echo "Verificar: alembic current + curl endpoints"
