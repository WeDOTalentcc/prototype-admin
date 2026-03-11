"""
T4 — Testes de Carga com Locust para LIA Platform.

Simula 2 tipos de usuários:
1. WizardUser  — cria vagas via chat com a LIA (operações pesadas com LLM)
2. PipelineUser — movimenta candidatos no pipeline (operações de CRUD)

Executar:
    pip install locust
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Targets de performance aceitável:
    p50 < 500ms | p95 < 2s | p99 < 5s | error rate < 1%
"""
import json
import random
import sys
import os

# Garante que load_test_config pode ser importado
sys.path.insert(0, os.path.dirname(__file__))

from locust import HttpUser, task, between, events
from load_test_config import (
    AUTH_HEADERS,
    TEST_COMPANY_ID,
    TEST_USER_ID,
    TEST_JOB_IDS,
    TEST_CANDIDATE_IDS,
    TEST_VACANCY_CANDIDATE_IDS,
    generate_wizard_message,
    generate_pipeline_transition_payload,
)


class WizardUser(HttpUser):
    """
    Simula um recrutador criando vagas via wizard conversacional da LIA.

    Operações:
    - chat_wizard (peso 3): envia mensagem ao wizard e aguarda resposta da LIA
    - get_wizard_state (peso 1): consulta o estado atual da sessão do wizard
    """
    wait_time = between(2, 5)

    def on_start(self):
        """Setup: gera um session_id para este usuário."""
        import uuid
        self.session_id = str(uuid.uuid4())

    @task(3)
    def chat_wizard(self):
        """
        Simula um turno de conversa no wizard de criação de vaga.
        Posta mensagem via chat e aguarda resposta da LIA.
        """
        payload = generate_wizard_message()
        payload["session_id"] = self.session_id  # Mantém sessão consistente

        with self.client.post(
            "/api/v1/wizard/chat",
            json=payload,
            headers=AUTH_HEADERS,
            catch_response=True,
            name="/wizard/chat",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if not data.get("response") and not data.get("message"):
                        response.failure("Wizard retornou resposta vazia")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Resposta não é JSON válido")
            elif response.status_code in (402, 429):
                # 402 = limite de plano, 429 = rate limit — não são erros do sistema
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:200]}")

    @task(1)
    def get_wizard_state(self):
        """
        Consulta o estado atual do wizard (checkpoint da sessão).
        """
        with self.client.get(
            f"/api/v1/wizard/state/{self.session_id}",
            headers=AUTH_HEADERS,
            catch_response=True,
            name="/wizard/state/{session_id}",
        ) as response:
            if response.status_code in (200, 404):
                # 404 é válido se a sessão ainda não foi iniciada
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:200]}")


class PipelineUser(HttpUser):
    """
    Simula um recrutador movimentando candidatos no pipeline.

    Operações:
    - transition_candidate (peso 4): move candidato entre etapas do pipeline
    - list_candidates (peso 2): lista candidatos de uma vaga
    """
    wait_time = between(1, 3)

    @task(4)
    def transition_candidate(self):
        """
        Simula a transição de um candidato entre etapas do pipeline.
        """
        payload = generate_pipeline_transition_payload()

        with self.client.post(
            "/api/v1/pipeline/transition",
            json=payload,
            headers=AUTH_HEADERS,
            catch_response=True,
            name="/pipeline/transition",
        ) as response:
            if response.status_code in (200, 201):
                response.success()
            elif response.status_code in (404, 422):
                # 404 = VacancyCandidate não encontrado (dado de teste)
                # 422 = transição inválida (estado de dados de teste)
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:200]}")

    @task(2)
    def list_candidates(self):
        """
        Lista os candidatos de uma vaga específica.
        """
        job_id = random.choice(TEST_JOB_IDS)

        with self.client.get(
            f"/api/v1/jobs/{job_id}/candidates",
            params={"limit": 20, "offset": 0},
            headers=AUTH_HEADERS,
            catch_response=True,
            name="/jobs/{job_id}/candidates",
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}: {response.text[:200]}")


class HealthCheckUser(HttpUser):
    """
    Usuário de baixo volume para monitorar health do sistema durante o teste.
    """
    wait_time = between(10, 30)
    weight = 1  # Poucos usuários deste tipo

    @task
    def check_health(self):
        with self.client.get(
            "/api/v1/health",
            headers=AUTH_HEADERS,
            catch_response=True,
            name="/health",
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check falhou: HTTP {response.status_code}")


# ==================== HOOKS DE RELATÓRIO ====================

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Exibe resumo de performance ao finalizar o teste."""
    stats = environment.stats

    print("\n" + "=" * 60)
    print("📊 RESUMO DO TESTE DE CARGA — LIA Platform")
    print("=" * 60)

    for name, entry in stats.entries.items():
        p50 = entry.get_response_time_percentile(0.50)
        p95 = entry.get_response_time_percentile(0.95)
        p99 = entry.get_response_time_percentile(0.99)
        error_rate = (entry.num_failures / entry.num_requests * 100) if entry.num_requests > 0 else 0

        p50_ok = "✅" if p50 < 500 else "❌"
        p95_ok = "✅" if p95 < 2000 else "❌"
        p99_ok = "✅" if p99 < 5000 else "❌"
        err_ok = "✅" if error_rate < 1.0 else "❌"

        print(f"\n  {name[1]}")
        print(f"    {p50_ok} p50: {p50:.0f}ms (target: <500ms)")
        print(f"    {p95_ok} p95: {p95:.0f}ms (target: <2s)")
        print(f"    {p99_ok} p99: {p99:.0f}ms (target: <5s)")
        print(f"    {err_ok} error rate: {error_rate:.2f}% (target: <1%)")

    print("\n" + "=" * 60 + "\n")
