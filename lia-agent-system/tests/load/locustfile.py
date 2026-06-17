"""
Load tests da plataforma LIA — Sprint K3.

Cenários cobertos:
1. candidate_search  — GET /api/v1/candidates/rag-search (RAG híbrido BM25+semantic)
2. toon_card         — GET /api/v1/candidates/{id}/toon (geração com cache Redis)
3. wsi_screening_batch — POST /api/v1/wsi/sessions (inicializa entrevistas WSI em lote)
4. wizard_interaction — POST /api/v1/chat (fluxo de wizard de criação de vaga)
5. chat_screening    — POST /api/v1/chat (triagem de candidatos via chat)
6. sourcing_search   — POST /api/v1/sourcing/search (busca de candidatos via sourcing)

Targets de SLA:
- candidate_search: P95 < 2s
- toon_card: P95 < 3s
- wsi_screening: P95 < 5s
- wizard_interaction: P95 < 4s
- chat_screening: P95 < 5s
- sourcing_search: P95 < 3s

Uso:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Com perfil de carga:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \\
           --users=50 --spawn-rate=5 --run-time=5m --headless

Variáveis de ambiente:
    LIA_AUTH_TOKEN   — Bearer token de autenticação (obrigatório em produção)
    LIA_COMPANY_ID   — company_id de testes (padrão: c-load-001)
"""
import random
import os
import json
import uuid

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

from load_test_config import (
    SAMPLE_QUERIES,
    SAMPLE_JOB_IDS,
    SAMPLE_CANDIDATE_IDS,
    SAMPLE_COMPANY_IDS,
    SAMPLE_SCREENING_QUERIES,
    SLA,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUTH_TOKEN = os.getenv("LIA_AUTH_TOKEN", "test-token")
DEFAULT_COMPANY_ID = os.getenv("LIA_COMPANY_ID", "c-load-001")


def _headers(company_id: str = DEFAULT_COMPANY_ID) -> dict:
    return {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "X-Company-ID": company_id,
        "Content-Type": "application/json",
    }


def _random_company() -> str:
    return random.choice(SAMPLE_COMPANY_IDS)


def _random_query() -> str:
    return random.choice(SAMPLE_QUERIES)


def _random_job_id() -> str:
    return random.choice(SAMPLE_JOB_IDS)


def _random_candidate_id() -> str:
    return random.choice(SAMPLE_CANDIDATE_IDS)


def _random_screening_query() -> str:
    return random.choice(SAMPLE_SCREENING_QUERIES)


# ---------------------------------------------------------------------------
# User classes
# ---------------------------------------------------------------------------

class RecruiterUser(HttpUser):
    """
    Simula um recrutador usando a plataforma LIA.

    Distribuição de tarefas reflete uso real:
    - 30% buscas de candidatos (ação mais comum)
    - 25% visualização de TOON cards (resultado de busca)
    - 15% interações com Wizard (criação de vagas)
    - 15% triagem via chat (screening LLM)
    - 10% sourcing de candidatos
    - 5%  triagem WSI (menos frequente, mais custosa)
    """

    wait_time = between(1, 3)

    # ---------------------------------------------------------------------------
    # Tarefa 1: candidate_search — RAG híbrido
    # ---------------------------------------------------------------------------

    @task(6)
    def candidate_search(self):
        """
        Busca candidatos via RAG híbrido (BM25 + semântico).

        Endpoint: GET /api/v1/candidates/rag-search
        SLA: P95 < 2s, erro < 1%
        """
        company_id = _random_company()
        query = _random_query()
        alpha = random.choice([0.0, 0.5, 1.0])

        with self.client.get(
            "/api/v1/candidates/rag-search",
            params={
                "q": query,
                "company_id": company_id,
                "limit": 10,
                "alpha": alpha,
            },
            headers=_headers(company_id),
            name="candidate_search",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if "results" not in data and "error" not in data:
                        resp.failure(f"Resposta sem 'results': {resp.text[:200]}")
                    else:
                        resp.success()
                except Exception as exc:
                    resp.failure(f"JSON inválido: {exc}")
            elif resp.status_code == 401:
                resp.failure("Não autorizado — verificar AUTH_TOKEN")
            elif resp.status_code == 404:
                resp.success()
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ---------------------------------------------------------------------------
    # Tarefa 2: toon_card — geração com cache Redis
    # ---------------------------------------------------------------------------

    @task(5)
    def toon_card(self):
        """
        Gera ou retorna do cache o TOON Card de um candidato.

        Endpoint: GET /api/v1/candidates/{candidate_id}/toon
        SLA: P95 < 3s (cache hit < 500ms, cache miss < 3s)
        """
        company_id = _random_company()
        candidate_id = _random_candidate_id()
        job_id = _random_job_id()
        anonymize = random.choice([True, False])

        with self.client.get(
            f"/api/v1/candidates/{candidate_id}/toon",
            params={
                "job_id": job_id,
                "company_id": company_id,
                "anonymize": str(anonymize).lower(),
            },
            headers=_headers(company_id),
            name="toon_card",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            elif resp.status_code == 401:
                resp.failure("Não autorizado")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ---------------------------------------------------------------------------
    # Tarefa 3: wsi_screening_batch — triagem WSI
    # ---------------------------------------------------------------------------

    @task(1)
    def wsi_screening_batch(self):
        """
        Inicia uma sessão de entrevista WSI para um candidato.

        Endpoint: POST /api/v1/wsi/sessions
        SLA: P95 < 5s (operação mais custosa — inclui geração de perguntas via LLM)
        """
        company_id = _random_company()
        candidate_id = _random_candidate_id()
        job_id = _random_job_id()
        session_id = str(uuid.uuid4())

        payload = {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "company_id": company_id,
            "interview_level": random.choice(["quick", "standard"]),
        }

        with self.client.post(
            "/api/v1/wsi/sessions",
            json=payload,
            headers=_headers(company_id),
            name="wsi_screening_batch",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 404, 422):
                resp.success()
            elif resp.status_code == 401:
                resp.failure("Não autorizado")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ---------------------------------------------------------------------------
    # Tarefa 4: wizard_interaction — fluxo de criação de vaga
    # ---------------------------------------------------------------------------

    @task(3)
    def wizard_interaction(self):
        """
        Envia mensagem ao Wizard via chat REST para criar/editar vaga.

        Endpoint: POST /api/v1/chat
        SLA: P95 < 4s
        """
        company_id = _random_company()
        thread_id = str(uuid.uuid4())

        wizard_messages = [
            "quero criar uma nova vaga de desenvolvedor python sênior",
            "salvar rascunho da vaga",
            "publicar a vaga",
            "qual é a faixa salarial para dev backend em São Paulo?",
            "validar os campos da vaga",
        ]

        payload = {
            "message": random.choice(wizard_messages),
            "thread_id": thread_id,
            "session_id": f"load-{thread_id[:8]}",
            "company_id": company_id,
            "user_id": "load-test-user",
            "domain": "wizard",
        }

        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=_headers(company_id),
            name="wizard_interaction",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 404):
                resp.success()
            elif resp.status_code == 401:
                resp.failure("Não autorizado")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ---------------------------------------------------------------------------
    # Tarefa 5: chat_screening — triagem de candidatos via chat (LLM)
    # ---------------------------------------------------------------------------

    @task(3)
    def chat_screening(self):
        """
        Triagem de candidatos via chat com LLM (domínio cv_screening).

        Endpoint: POST /api/v1/chat
        SLA: P95 < 5s (inclui análise de CV e scoring via LLM)
        """
        company_id = _random_company()
        thread_id = str(uuid.uuid4())
        candidate_id = _random_candidate_id()
        job_id = _random_job_id()

        payload = {
            "message": _random_screening_query(),
            "thread_id": thread_id,
            "session_id": f"screening-{thread_id[:8]}",
            "company_id": company_id,
            "user_id": "load-test-user",
            "domain": "cv_screening",
            "context": {
                "candidate_id": candidate_id,
                "job_id": job_id,
            },
        }

        with self.client.post(
            "/api/v1/chat",
            json=payload,
            headers=_headers(company_id),
            name="chat_screening",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 404):
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limit atingido — rever configuração de load test")
            elif resp.status_code == 401:
                resp.failure("Não autorizado")
            else:
                resp.failure(f"HTTP {resp.status_code}")

    # ---------------------------------------------------------------------------
    # Tarefa 6: sourcing_search — busca de sourcing
    # ---------------------------------------------------------------------------

    @task(2)
    def sourcing_search(self):
        """
        Busca de candidatos via sourcing (domínio sourcing).

        Endpoint: POST /api/v1/sourcing/search
        SLA: P95 < 3s
        """
        company_id = _random_company()
        job_id = _random_job_id()

        payload = {
            "query": _random_query(),
            "job_id": job_id,
            "company_id": company_id,
            "limit": 10,
            "filters": {
                "location": random.choice(["São Paulo", "Rio de Janeiro", "Remoto"]),
                "seniority": random.choice(["junior", "pleno", "senior"]),
            },
        }

        with self.client.post(
            "/api/v1/sourcing/search",
            json=payload,
            headers=_headers(company_id),
            name="sourcing_search",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 201, 404, 422):
                resp.success()
            elif resp.status_code == 429:
                resp.failure("Rate limit atingido")
            elif resp.status_code == 401:
                resp.failure("Não autorizado")
            else:
                resp.failure(f"HTTP {resp.status_code}")


# ---------------------------------------------------------------------------
# Eventos — validação de SLA ao final do teste
# ---------------------------------------------------------------------------

@events.quitting.add_listener
def validate_sla(environment, **kwargs):
    """Verifica SLAs ao final do teste e falha se violados."""
    if environment.runner is None:
        return

    stats = environment.runner.stats

    violations = []
    for task_name, sla in SLA.items():
        entry = (
            stats.entries.get((task_name, "GET"))
            or stats.entries.get((task_name, "POST"))
        )
        if entry is None:
            continue

        p95 = entry.get_response_time_percentile(0.95)
        if p95 > sla.p95_ms:
            violations.append(
                f"SLA violado: {task_name} P95={p95:.0f}ms > {sla.p95_ms}ms"
            )

        error_pct = (entry.num_failures / max(entry.num_requests, 1)) * 100
        if error_pct > sla.error_rate_pct:
            violations.append(
                f"Taxa de erro: {task_name} {error_pct:.1f}% > {sla.error_rate_pct}%"
            )

    if violations:
        print("\n[LOAD TEST] SLA VIOLATIONS DETECTED:")
        for v in violations:
            print(f"  - {v}")
        environment.process_exit_code = 1
    else:
        print("\n[LOAD TEST] All SLAs validated successfully.")
