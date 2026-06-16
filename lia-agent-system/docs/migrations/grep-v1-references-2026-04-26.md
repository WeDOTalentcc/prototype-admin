# GREP V1 INVENTORY — Sprint I Tarefa A.1
# Date: 2026-04-26

## A.1.1 Importers estaticos de V1

/home/runner/workspace/lia-agent-system/app/orchestrator/__init__.py:4:from .orchestrator import Orchestrator
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:62:class Orchestrator:
/home/runner/workspace/lia-agent-system/app/orchestrator/registry.py:14:    from app.orchestrator.orchestrator import Orchestrator
/home/runner/workspace/lia-agent-system/tests/integration/test_orchestrator_consolidation.py:246:        from app.orchestrator.orchestrator import Orchestrator
/home/runner/workspace/lia-agent-system/tests/test_autonomous_react_agent.py:1259:            from app.orchestrator.orchestrator import Orchestrator
/home/runner/workspace/lia-agent-system/tests/test_autonomous_react_agent.py:1326:            from app.orchestrator.orchestrator import Orchestrator
/home/runner/workspace/lia-agent-system/tests/unit/test_anti_sycophancy_prompts.py:43:        from app.orchestrator.orchestrator import _LIA_SYSTEM_PROMPT

[total: 7 linhas]

## A.1.2 Factory calls get_orchestrator (V1, nao get_main)

/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:123:    orch: Orchestrator = Depends(get_orchestrator)
/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:161:    orch: Orchestrator = Depends(get_orchestrator)
/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:173:async def get_metrics(orch: Orchestrator = Depends(get_orchestrator)):
/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:93:from app.orchestrator.registry import get_orchestrator_instance, set_orchestrator_instance
/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:97:def get_orchestrator() -> Orchestrator:
/home/runner/workspace/lia-agent-system/app/api/v1/lia_assistant/insights.py:382:            from app.api.orchestrator_routes import get_orchestrator
/home/runner/workspace/lia-agent-system/app/api/v1/lia_assistant/insights.py:387:            orchestrator = get_orchestrator()
/home/runner/workspace/lia-agent-system/app/api/v1/onboarding.py:130:    orchestrator = await _get_orchestrator(db)
/home/runner/workspace/lia-agent-system/app/api/v1/onboarding.py:183:    orchestrator = await _get_orchestrator(db)
/home/runner/workspace/lia-agent-system/app/api/v1/onboarding.py:87:async def _get_orchestrator(db=None):
/home/runner/workspace/lia-agent-system/app/api/v1/whatsapp_webhook.py:100:async def _get_orchestrator():
/home/runner/workspace/lia-agent-system/app/api/v1/whatsapp_webhook.py:240:    orchestrator, wa_client = await _get_orchestrator()
/home/runner/workspace/lia-agent-system/app/api/v1/whatsapp_webhook.py:325:            orchestrator, wa_client = await _get_orchestrator()
/home/runner/workspace/lia-agent-system/app/api/v1/whatsapp_webhook.py:340:    orchestrator, wa_client = await _get_orchestrator()
/home/runner/workspace/lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py:71:        from app.orchestrator.registry import get_orchestrator_instance
/home/runner/workspace/lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py:89:            orchestrator = get_orchestrator_instance()
/home/runner/workspace/lia-agent-system/app/domains/job_management/prompts/job_wizard.py:322:def get_orchestrator_prompt(
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:1529:            from app.api.orchestrator_routes import get_orchestrator
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:1530:            orchestrator = get_orchestrator()
/home/runner/workspace/lia-agent-system/app/orchestrator/registry.py:22:def get_orchestrator_instance() -> "Orchestrator | None":
/home/runner/workspace/lia-agent-system/app/orchestrator/registry.py:6:    from app.orchestrator.registry import get_orchestrator_instance, set_orchestrator_instance
/home/runner/workspace/lia-agent-system/app/prompts/__init__.py:35:    get_orchestrator_prompt,
/home/runner/workspace/lia-agent-system/app/prompts/__init__.py:58:    "get_orchestrator_prompt",
/home/runner/workspace/lia-agent-system/app/prompts/job_wizard.py:14:    get_orchestrator_prompt,
/home/runner/workspace/lia-agent-system/app/shared/prompts/__init__.py:25:    get_orchestrator_prompt,
/home/runner/workspace/lia-agent-system/app/shared/prompts/__init__.py:50:    "get_orchestrator_prompt",
/home/runner/workspace/lia-agent-system/app/shared/prompts/job_wizard.py:363:def get_orchestrator_prompt(

[total: 27 linhas]

## A.1.3 Method calls de V1

/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:121:async def process_request(
/home/runner/workspace/lia-agent-system/app/api/orchestrator_routes.py:136:        result = await orch.process_request(
/home/runner/workspace/lia-agent-system/app/api/v1/chat.py:139:    result = await _orch.process_request(
/home/runner/workspace/lia-agent-system/app/api/v1/lia_assistant/insights.py:400:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/app/domains/communication/services/teams_orchestrator_bridge.py:92:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/app/orchestrator/context_adapter.py:84:        """Converte para o formato que Orchestrator.process_request_with_memory() espera."""
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:1051:        Elimina a delegação intermediária para Orchestrator.process_request_with_memory,
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:1053:        somente para process_request (roteamento + execução de domínio).
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:1247:            result = await self._orchestrator.process_request(
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:18:- Orchestrator.process_request_with_memory() (intermediário eliminado)
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:197:        """Converte o dict retornado por Orchestrator.process_request()."""
/home/runner/workspace/lia-agent-system/app/orchestrator/main_orchestrator.py:268:    do pipeline unificado, sem delegar para Orchestrator.process_request_with_memory
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:113:    async def process_request(self, user_id: str, message: str,
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:253:                # If no pre-resolved response (should not happen), fall through to _handle_directly
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:270:                    fb = await self._handle_directly(intent, sanitized, dr.data or {}, context=ctx)
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:304:                fb = await self._handle_directly(intent, sanitized, {}, context=ctx)
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:327:    async def process_request_with_memory(self, db, user_id: str, message: str,
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:347:            result = await self.process_request(user_id=user_id, message=message,
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:426:    async def _handle_directly(
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:434:            rubric_result = await self._handle_cv_screening_with_rubric(message, context or {})
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:475:            # _handle_directly fallback path the same agentic capability.
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:484:                        logger.debug("[LIA-A04] _handle_directly bound %d tools", len(tool_schemas))
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:496:                logger.info("[LIA-A04] _handle_directly LLM requested %d tool(s): %s", len(response_tools_used), response_tools_used)
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:509:    async def _handle_cv_screening_with_rubric(
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:519:        Falls back gracefully so _handle_directly can use the LLM addendum instead.
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:608:    async def execute_plan(self, conversation_id: str, plan: dict[str, Any]) -> dict[str, Any]:
/home/runner/workspace/lia-agent-system/app/orchestrator/orchestrator.py:652:    async def process_analytics_request(self, user_id: str, command: str,
/home/runner/workspace/lia-agent-system/tests/integration/test_orchestrator_consolidation.py:167:        mock_orchestrator.process_request.assert_not_called()
/home/runner/workspace/lia-agent-system/tests/integration/test_orchestrator_consolidation.py:35:    orch.process_request = AsyncMock(return_value={
/home/runner/workspace/lia-agent-system/tests/integration/test_orchestrator_consolidation.py:591:    def test_orchestrator_process_request_message_key_not_lost(self):
/home/runner/workspace/lia-agent-system/tests/integration/test_orchestrator_consolidation.py:593:        Orchestrator.process_request() returns a dict with 'message' key.
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1597:        mock_orch.process_request = mock_process
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1627:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1661:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1693:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1725:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1757:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/tests/test_agent_regression.py:1789:            result = await orchestrator.process_request(
/home/runner/workspace/lia-agent-system/tests/test_autonomous_react_agent.py:1271:                    orchestrator, "process_request", new_callable=AsyncMock
/home/runner/workspace/lia-agent-system/tests/test_autonomous_react_agent.py:1322:        """Verify orchestrator's process_request method intercepts 'autonomous' domain
/home/runner/workspace/lia-agent-system/tests/test_autonomous_react_agent.py:1327:            source = inspect.getsource(Orchestrator.process_request)
/home/runner/workspace/lia-agent-system/tests/test_autonomous_react_agent.py:1330:                "Orchestrator.process_request must check for 'autonomous' domain_id"
/home/runner/workspace/lia-agent-system/tests/test_execution_plan.py:361:    async def test_execute_plan_all_complete(self, executor):
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:104:            mock_orch.process_request.assert_called_once()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:105:            call_kwargs = mock_orch.process_request.call_args.kwargs
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:112:        mock_orch.process_request = AsyncMock(
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:131:        mock_orch.process_request = AsyncMock(side_effect=Exception("DB timeout"))
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:197:        """Sem pending action → vai direto para Phase 2 (process_request)."""
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:199:        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:209:            mock_orch.process_request.assert_called_once()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:221:        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:234:            mock_orch.process_request.assert_called_once()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:256:            mock_orch.process_request.assert_not_called()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:263:        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:274:            mock_orch.process_request.assert_called_once()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:285:        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:296:            mock_orch.process_request.assert_called_once()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:297:            call_kwargs = mock_orch.process_request.call_args.kwargs
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:335:        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:361:        mock_orch.process_request = AsyncMock(return_value=make_orchestrator_result())
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:87:    async def test_calls_process_request(self):
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:88:        """Phase 2 chama orchestrator.process_request (não process_request_with_memory)."""
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator.py:90:        mock_orch.process_request = AsyncMock(
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:173:        mock_orch.process_request = AsyncMock(
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:189:        mock_orch.process_request = AsyncMock(
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:213:        mock_orch.process_request = AsyncMock(
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:226:        call_kwargs = mock_orch.process_request.call_args.kwargs
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:233:        mock_orch.process_request = AsyncMock(
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:269:        mock_orch.process_request.assert_not_called()
/home/runner/workspace/lia-agent-system/tests/unit/test_main_orchestrator_extended.py:288:        mock_orch.process_request.assert_not_called()
/home/runner/workspace/lia-agent-system/tests/unit/test_sprint_i_foundations.py:180:        mock_orchestrator.process_request = AsyncMock(return_value={

[total: 71 linhas]
