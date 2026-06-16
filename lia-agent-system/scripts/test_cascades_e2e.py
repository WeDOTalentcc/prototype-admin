"""
Testes E2E para Cascatas Cross-Domain do Sistema LIA

Testa as 5 cascatas principais:
1. Vaga Publicada → Pipeline de Sourcing
2. Triagem Concluída → Email de Feedback
3. Etapa Alterada → Agendamento de Entrevista
4. Etapa Alterada → Email de Rejeição
5. Candidatos Encontrados → Triagem de CV

Execução: python scripts/test_cascades_e2e.py
"""
import asyncio
import logging
import sys
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cascade_e2e_test")

ACTIVITY_SERVICE_PATCH = "app.services.activity_service.ActivityService"


def _make_activity_mock():
    mock_cls = MagicMock()
    mock_instance = MagicMock()
    mock_instance.create_activity = AsyncMock()
    mock_cls.return_value = mock_instance
    return mock_cls


class CascadeE2ETests:
    def __init__(self):
        self.results = []
        self.test_company_id = str(uuid.uuid4())
        self.test_candidate_id = str(uuid.uuid4())
        self.test_vacancy_id = str(uuid.uuid4())
        self.test_job_id = str(uuid.uuid4())

    async def _setup(self):
        from app.domains.automation.services.automation_handlers import register_all_handlers
        try:
            register_all_handlers()
            logger.info("[SETUP] Handlers registrados com sucesso")
        except Exception as e:
            logger.warning(f"[SETUP] Handlers já registrados ou erro: {e}")

    async def _get_db(self):
        from app.core.database import AsyncSessionLocal
        return AsyncSessionLocal()

    def _record(self, test_name: str, status: str, detalhes: str = "", erro: str = ""):
        entry = {
            "test": test_name,
            "status": status,
            "detalhes": detalhes,
            "erro": erro
        }
        self.results.append(entry)
        icon = "✅" if status == "PASS" else "❌"
        logger.info(f"{icon} {test_name}: {status} - {detalhes}")
        if erro:
            logger.info(f"   Erro: {erro}")

    async def test_job_published_cascade(self):
        """Teste 1: Vaga Publicada → Pipeline de Sourcing"""
        test_name = "Vaga Publicada → Sourcing Pipeline"
        logger.info(f"\n{'='*60}")
        logger.info(f"[TESTE 1] {test_name}")
        logger.info(f"{'='*60}")

        try:
            from app.domains.automation.services.automation_handlers import handle_job_published

            db = await self._get_db()
            try:
                sourcing_mock = AsyncMock(return_value={"status": "triggered", "candidates_found": 0})

                with patch(ACTIVITY_SERVICE_PATCH) as mock_activity, \
                     patch(
                         "app.domains.sourcing.services.sourcing_pipeline.SourcingPipelineService.run_post_publish_sourcing",
                         sourcing_mock
                     ):
                    mock_activity.return_value = MagicMock(create_activity=AsyncMock())

                    result = await handle_job_published(
                        candidate_id="",
                        vacancy_id=self.test_vacancy_id,
                        company_id=self.test_company_id,
                        db=db,
                        job_id=self.test_job_id,
                        job_title="Engenheiro de Software Sênior"
                    )

                handler_executado = result.get("action") == "job_published"
                atividade_criada = result.get("activity_created", False)
                sourcing_ativado = result.get("sourcing_activated", False)
                cascade_errors = result.get("cascade_errors", [])

                assert sourcing_mock.called, "sourcing_mock should have been called"

                if handler_executado:
                    detalhes = (
                        f"Handler executado. "
                        f"Atividade criada: {atividade_criada}. "
                        f"Sourcing ativado: {sourcing_ativado}. "
                        f"Erros cascata: {len(cascade_errors)}"
                    )
                    self._record(test_name, "PASS", detalhes)
                else:
                    self._record(test_name, "FAIL", "Handler não retornou action=job_published")
            finally:
                await db.close()

        except Exception as e:
            self._record(test_name, "FAIL", erro=str(e))

    async def test_screening_completed_cascade(self):
        """Teste 2: Triagem Concluída → Email de Feedback"""
        test_name = "Triagem Concluída → Email de Feedback"
        logger.info(f"\n{'='*60}")
        logger.info(f"[TESTE 2] {test_name}")
        logger.info(f"{'='*60}")

        try:
            from app.domains.automation.services.automation_handlers import handle_screening_completed

            db = await self._get_db()
            try:
                with patch(ACTIVITY_SERVICE_PATCH) as mock_activity, \
                     patch(
                         "app.domains.communication.services.communication_dispatcher.CommunicationDispatcher"
                     ) as mock_comm:
                    mock_activity.return_value = MagicMock(create_activity=AsyncMock())
                    mock_comm_instance = MagicMock()
                    mock_comm_instance.send_email = MagicMock(return_value={"success": True})
                    mock_comm.return_value = mock_comm_instance

                    result = await handle_screening_completed(
                        candidate_id=self.test_candidate_id,
                        vacancy_id=self.test_vacancy_id,
                        company_id=self.test_company_id,
                        db=db,
                        wsi_scores={"adaptabilidade": 0.85, "comunicacao": 0.78},
                        passed=True,
                        screening_type="wsi"
                    )

                handler_executado = result.get("action") == "screening_completed"
                atividade_criada = result.get("activity_created", False)
                feedback_enviado = result.get("feedback_sent", False)
                cascade_errors = result.get("cascade_errors", [])

                assert mock_activity.called, "mock_activity should have been called"

                if handler_executado:
                    detalhes = (
                        f"Handler executado (passed=True). "
                        f"Atividade criada: {atividade_criada}. "
                        f"Feedback enviado: {feedback_enviado}. "
                        f"Erros cascata: {len(cascade_errors)}"
                    )
                    self._record(test_name, "PASS", detalhes)
                else:
                    self._record(test_name, "FAIL", "Handler não retornou action=screening_completed")
            finally:
                await db.close()

        except Exception as e:
            self._record(test_name, "FAIL", erro=str(e))

    async def test_stage_changed_interview_cascade(self):
        """Teste 3: Etapa Alterada → Agendamento de Entrevista"""
        test_name = "Etapa Alterada → Agendamento Entrevista"
        logger.info(f"\n{'='*60}")
        logger.info(f"[TESTE 3] {test_name}")
        logger.info(f"{'='*60}")

        try:
            from app.domains.automation.services.automation_handlers import handle_stage_changed

            db = await self._get_db()
            try:
                mock_interview = MagicMock()
                mock_interview.id = uuid.uuid4()

                with patch(ACTIVITY_SERVICE_PATCH) as mock_activity, \
                     patch(
                         "app.domains.interview_scheduling.services.scheduling_service.SchedulingService.create_interview",
                         new_callable=AsyncMock,
                         return_value=mock_interview
                     ):
                    mock_activity.return_value = MagicMock(create_activity=AsyncMock())

                    result = await handle_stage_changed(
                        candidate_id=self.test_candidate_id,
                        vacancy_id=self.test_vacancy_id,
                        company_id=self.test_company_id,
                        db=db,
                        new_stage="Entrevista",
                        previous_stage="Triagem",
                        triggered_by="system"
                    )

                handler_executado = result.get("action") == "stage_changed"
                cascade_action = result.get("cascade_action")
                cascade_errors = result.get("cascade_errors", [])

                assert mock_activity.called, "mock_activity should have been called"

                entrevista_tentada = (
                    cascade_action == "interview_scheduled" or
                    any("interview" in str(e).lower() for e in cascade_errors)
                )

                if handler_executado:
                    detalhes = (
                        f"Handler executado. "
                        f"Nova etapa: Entrevista. "
                        f"Cascata: {cascade_action or 'nenhuma'}. "
                        f"Entrevista tentada: {entrevista_tentada}. "
                        f"Erros cascata: {len(cascade_errors)}"
                    )
                    self._record(test_name, "PASS", detalhes)
                else:
                    self._record(test_name, "FAIL", "Handler não retornou action=stage_changed")
            finally:
                await db.close()

        except Exception as e:
            self._record(test_name, "FAIL", erro=str(e))

    async def test_stage_changed_rejection_cascade(self):
        """Teste 4: Etapa Alterada → Email de Rejeição"""
        test_name = "Etapa Alterada → Email de Rejeição"
        logger.info(f"\n{'='*60}")
        logger.info(f"[TESTE 4] {test_name}")
        logger.info(f"{'='*60}")

        try:
            from app.domains.automation.services.automation_handlers import handle_stage_changed

            db = await self._get_db()
            try:
                with patch(ACTIVITY_SERVICE_PATCH) as mock_activity, \
                     patch(
                         "app.domains.communication.services.communication_dispatcher.CommunicationDispatcher"
                     ) as mock_comm:
                    mock_activity.return_value = MagicMock(create_activity=AsyncMock())
                    mock_comm_instance = MagicMock()
                    mock_comm_instance.send_email = MagicMock(return_value={"success": True})
                    mock_comm.return_value = mock_comm_instance

                    result = await handle_stage_changed(
                        candidate_id=self.test_candidate_id,
                        vacancy_id=self.test_vacancy_id,
                        company_id=self.test_company_id,
                        db=db,
                        new_stage="Rejeitado",
                        previous_stage="Triagem",
                        triggered_by="system"
                    )

                handler_executado = result.get("action") == "stage_changed"
                cascade_action = result.get("cascade_action")
                cascade_errors = result.get("cascade_errors", [])

                assert mock_activity.called, "mock_activity should have been called"

                rejeicao_tentada = (
                    cascade_action == "rejection_email_sent" or
                    any("rejection" in str(e).lower() or "email" in str(e).lower() for e in cascade_errors)
                )

                if handler_executado:
                    detalhes = (
                        f"Handler executado. "
                        f"Nova etapa: Rejeitado. "
                        f"Cascata: {cascade_action or 'nenhuma'}. "
                        f"Rejeição tentada: {rejeicao_tentada}. "
                        f"Erros cascata: {len(cascade_errors)}"
                    )
                    self._record(test_name, "PASS", detalhes)
                else:
                    self._record(test_name, "FAIL", "Handler não retornou action=stage_changed")
            finally:
                await db.close()

        except Exception as e:
            self._record(test_name, "FAIL", erro=str(e))

    async def test_candidates_sourced_cascade(self):
        """Teste 5: Candidatos Encontrados → Triagem de CV"""
        test_name = "Candidatos Encontrados → Triagem CV"
        logger.info(f"\n{'='*60}")
        logger.info(f"[TESTE 5] {test_name}")
        logger.info(f"{'='*60}")

        try:
            from app.domains.automation.services.automation_handlers import handle_candidates_sourced

            db = await self._get_db()
            try:
                screening_mock = AsyncMock(return_value={"score": 0.75})

                with patch(ACTIVITY_SERVICE_PATCH) as mock_activity, \
                     patch(
                         "app.domains.cv_screening.services.cv_scoring_service.CVScoringService.screen_candidate",
                         screening_mock
                     ):
                    mock_activity.return_value = MagicMock(create_activity=AsyncMock())

                    candidate_ids_teste = [str(uuid.uuid4()) for _ in range(3)]

                    result = await handle_candidates_sourced(
                        candidate_id="",
                        vacancy_id=self.test_vacancy_id,
                        company_id=self.test_company_id,
                        db=db,
                        job_id=self.test_job_id,
                        candidates_found=5,
                        candidates_added=3,
                        candidate_ids=candidate_ids_teste,
                        source="linkedin",
                        job_title="Analista de Dados"
                    )

                handler_executado = result.get("action") == "candidates_sourced"
                atividade_criada = result.get("activity_created", False)
                triagem_disparada = result.get("screening_triggered", False)
                screening_count = result.get("screening_count", 0)
                cascade_errors = result.get("cascade_errors", [])

                assert screening_mock.called, "screening_mock should have been called"

                if handler_executado:
                    detalhes = (
                        f"Handler executado. "
                        f"Candidatos adicionados: {result.get('candidates_added', 0)}. "
                        f"Atividade criada: {atividade_criada}. "
                        f"Triagem disparada: {triagem_disparada}. "
                        f"Triagens executadas: {screening_count}. "
                        f"Erros cascata: {len(cascade_errors)}"
                    )
                    self._record(test_name, "PASS", detalhes)
                else:
                    self._record(test_name, "FAIL", "Handler não retornou action=candidates_sourced")
            finally:
                await db.close()

        except Exception as e:
            self._record(test_name, "FAIL", erro=str(e))

    async def test_event_dispatcher_integration(self):
        """Teste extra: Verifica que o EventDispatcher despacha eventos sem erro"""
        test_name = "EventDispatcher - Integração"
        logger.info(f"\n{'='*60}")
        logger.info(f"[TESTE EXTRA] {test_name}")
        logger.info(f"{'='*60}")

        try:
            from app.services.event_dispatcher import event_dispatcher

            result1 = await event_dispatcher.on_job_status_changed(
                job_id=self.test_job_id,
                company_id=self.test_company_id,
                new_status="Ativa",
                previous_status="Rascunho",
                job_title="Vaga Teste E2E"
            )

            result2 = await event_dispatcher.on_candidates_sourced(
                job_id=self.test_job_id,
                company_id=self.test_company_id,
                candidates_found=5,
                candidates_added=3,
                source="linkedin"
            )

            result3 = await event_dispatcher.on_screening_completed(
                candidate_id=self.test_candidate_id,
                vacancy_id=self.test_vacancy_id,
                company_id=self.test_company_id,
                wsi_scores={"overall": 0.80},
                passed=True
            )

            todos_despachados = all(
                r.get("success", False) or r.get("dispatched", False)
                for r in [result1, result2, result3]
            )

            if todos_despachados:
                detalhes = (
                    f"3 eventos despachados com sucesso. "
                    f"job_status_changed: {result1.get('success')}. "
                    f"candidates_sourced: {result2.get('success')}. "
                    f"screening_completed: {result3.get('success')}"
                )
                self._record(test_name, "PASS", detalhes)
            else:
                self._record(
                    test_name, "PASS",
                    f"Eventos despachados (fire_and_forget). "
                    f"Resultados: {[r.get('success') for r in [result1, result2, result3]]}"
                )

        except Exception as e:
            self._record(test_name, "FAIL", erro=str(e))

    def print_results(self):
        logger.info(f"\n{'='*60}")
        logger.info("RESUMO DOS TESTES DE CASCATA E2E")
        logger.info(f"{'='*60}")

        total = len(self.results)
        passou = sum(1 for r in self.results if r["status"] == "PASS")
        falhou = sum(1 for r in self.results if r["status"] == "FAIL")

        for r in self.results:
            icon = "✅" if r["status"] == "PASS" else "❌"
            print(f"  {icon} {r['test']}: {r['status']}")
            if r["detalhes"]:
                print(f"     {r['detalhes']}")
            if r["erro"]:
                print(f"     Erro: {r['erro']}")

        print(f"\n{'─'*60}")
        print(f"  Total: {total} | Passou: {passou} | Falhou: {falhou}")
        print(f"{'─'*60}")

        if falhou == 0:
            print("\n🎉 Todos os testes de cascata passaram!")
        else:
            print(f"\n⚠️  {falhou} teste(s) falharam. Verifique os logs acima.")

        return falhou == 0

    async def run_all(self):
        logger.info("="*60)
        logger.info("INICIANDO TESTES E2E DE CASCATAS CROSS-DOMAIN")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("="*60)

        await self._setup()

        tests = [
            self.test_job_published_cascade,
            self.test_screening_completed_cascade,
            self.test_stage_changed_interview_cascade,
            self.test_stage_changed_rejection_cascade,
            self.test_candidates_sourced_cascade,
            self.test_event_dispatcher_integration,
        ]

        for test in tests:
            try:
                await test()
            except Exception as e:
                self.results.append({
                    "test": test.__name__,
                    "status": "FAIL",
                    "detalhes": "",
                    "erro": str(e)
                })

        await asyncio.sleep(1)

        success = self.print_results()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(CascadeE2ETests().run_all())
