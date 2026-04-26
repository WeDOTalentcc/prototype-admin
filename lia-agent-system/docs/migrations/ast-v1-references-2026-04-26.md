# AST V1 INVENTORY — Sprint I Tarefa A.2
# Date: 2026-04-26
# Files scanned: 2559
# Files with V1 references: 14

## static_import_from_v1_module (5 occurrences)

- `app/orchestrator/registry.py:14` — from app.orchestrator.orchestrator import Orchestrator
- `tests/integration/test_orchestrator_consolidation.py:246` — from app.orchestrator.orchestrator import Orchestrator
- `tests/test_autonomous_react_agent.py:1259` — from app.orchestrator.orchestrator import Orchestrator
- `tests/test_autonomous_react_agent.py:1326` — from app.orchestrator.orchestrator import Orchestrator
- `tests/unit/test_anti_sycophancy_prompts.py:43` — from app.orchestrator.orchestrator import _LIA_SYSTEM_PROMPT

## static_import_v1_name_from_parent (1 occurrences)

- `app/api/orchestrator_routes.py:16` — from app.orchestrator import Orchestrator

## v1_method_access (44 occurrences)

- `app/api/orchestrator_routes.py:136` — .process_request
- `app/api/v1/chat.py:139` — .process_request
- `app/api/v1/lia_assistant/insights.py:400` — .process_request
- `app/domains/communication/services/teams_orchestrator_bridge.py:92` — .process_request
- `app/orchestrator/main_orchestrator.py:1247` — .process_request
- `app/orchestrator/orchestrator.py:270` — ._handle_directly
- `app/orchestrator/orchestrator.py:304` — ._handle_directly
- `app/orchestrator/orchestrator.py:347` — .process_request
- `app/orchestrator/orchestrator.py:434` — ._handle_cv_screening_with_rubric
- `tests/integration/test_orchestrator_consolidation.py:35` — .process_request
- `tests/integration/test_orchestrator_consolidation.py:167` — .process_request
- `tests/test_agent_regression.py:1597` — .process_request
- `tests/test_agent_regression.py:1627` — .process_request
- `tests/test_agent_regression.py:1661` — .process_request
- `tests/test_agent_regression.py:1693` — .process_request
- `tests/test_agent_regression.py:1725` — .process_request
- `tests/test_agent_regression.py:1757` — .process_request
- `tests/test_agent_regression.py:1789` — .process_request
- `tests/test_autonomous_react_agent.py:1327` — .process_request
- `tests/unit/test_main_orchestrator.py:90` — .process_request
- `tests/unit/test_main_orchestrator.py:104` — .process_request
- `tests/unit/test_main_orchestrator.py:105` — .process_request
- `tests/unit/test_main_orchestrator.py:112` — .process_request
- `tests/unit/test_main_orchestrator.py:131` — .process_request
- `tests/unit/test_main_orchestrator.py:199` — .process_request
- `tests/unit/test_main_orchestrator.py:209` — .process_request
- `tests/unit/test_main_orchestrator.py:221` — .process_request
- `tests/unit/test_main_orchestrator.py:234` — .process_request
- `tests/unit/test_main_orchestrator.py:256` — .process_request
- `tests/unit/test_main_orchestrator.py:263` — .process_request
- `tests/unit/test_main_orchestrator.py:274` — .process_request
- `tests/unit/test_main_orchestrator.py:285` — .process_request
- `tests/unit/test_main_orchestrator.py:296` — .process_request
- `tests/unit/test_main_orchestrator.py:297` — .process_request
- `tests/unit/test_main_orchestrator.py:335` — .process_request
- `tests/unit/test_main_orchestrator.py:361` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:173` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:189` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:213` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:226` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:233` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:269` — .process_request
- `tests/unit/test_main_orchestrator_extended.py:288` — .process_request
- `tests/unit/test_sprint_i_foundations.py:180` — .process_request

---
JSON saved to /tmp/ast-v1-2026-04-26.json for diff vs grep
