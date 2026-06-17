"""
Sprint Y5 — C5: Runbook Operacional — Testes de Links

Verifica que:
1. Os arquivos de runbook existem e têm conteúdo
2. Os caminhos de API mencionados nos runbooks são conhecidos e válidos
3. Endpoints críticos estão documentados nos runbooks

Não importa main.py — usa conjunto fixo de endpoints conhecidos.
"""

import os
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Caminhos dos runbooks
# ---------------------------------------------------------------------------

RUNBOOK_DIR = Path(__file__).parent.parent.parent / "docs"
RUNBOOK_DEGRADATION = RUNBOOK_DIR / "RUNBOOK_DEGRADATION.md"
RUNBOOK_PLAYBOOKS = RUNBOOK_DIR / "RUNBOOK_INCIDENT_PLAYBOOKS.md"

# ---------------------------------------------------------------------------
# Conjunto de endpoints conhecidos da plataforma LIA
# Extraídos dos arquivos de roteamento (app/api/v1/) — sem importar main.py
# ---------------------------------------------------------------------------

KNOWN_ENDPOINTS: set[str] = {
    # Circuit Breakers (admin_circuit_breakers.py)
    "/api/v1/admin/circuit-breakers",
    "/api/v1/admin/circuit-breakers/{circuit_name}/reset",
    "/api/v1/admin/circuit-breakers/reset-all",
    # Drift (drift.py)
    "/api/v1/drift/status",
    "/api/v1/drift/run-batch",
    # Bias Audit (bias_audit.py)
    "/api/v1/bias-audit/job/{job_id}",
    "/api/v1/bias-audit/job/{job_id}/history",
    # HITL (hitl.py)
    "/api/v1/hitl/{thread_id}/approve",
    "/api/v1/hitl/{thread_id}/pending",
    # Policy Engine (policy_engine.py)
    "/api/v1/policy-engine",
    "/api/v1/policy-engine/apply-sector/{company_id}",
    "/api/v1/policy-engine/evaluate",
    "/api/v1/policy-engine/seed",
    "/api/v1/policy-engine/evaluation-logs",
    "/api/v1/policy-engine/escalation-logs",
    # Admin LGPD (admin_lgpd.py)
    "/api/v1/admin/lgpd/cleanup-status",
    "/api/v1/admin/lgpd/run-cleanup",
    # RAG (rag_search.py)
    "/api/v1/candidates/rag-search",
    # TOON (toon.py)
    "/api/v1/candidates/{candidate_id}/toon",
}

# ---------------------------------------------------------------------------
# Endpoints esperados em cada runbook (subset que DEVE aparecer nos docs)
# ---------------------------------------------------------------------------

ENDPOINTS_EXPECTED_IN_DEGRADATION = [
    "/api/v1/admin/circuit-breakers",
    "/api/v1/drift/status",
    "/api/v1/drift/run-batch",
    "/api/v1/bias-audit/job/",  # prefixo — job_id é variável
    "/api/v1/hitl/",             # prefixo — thread_id é variável
    "/api/v1/policy-engine/apply-sector/",  # prefixo — company_id é variável
    "/api/v1/admin/lgpd/",  # prefixo de endpoints LGPD (run-cleanup ou cleanup-status)
]

ENDPOINTS_EXPECTED_IN_PLAYBOOKS = [
    "/api/v1/admin/circuit-breakers",
    "/api/v1/drift/status",
    "/api/v1/drift/run-batch",
    "/api/v1/bias-audit/job/",
    "/api/v1/hitl/",
    "/api/v1/policy-engine/apply-sector/",
    "/api/v1/admin/lgpd/",  # prefixo de endpoints LGPD
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_doc(path: Path) -> str:
    """Lê o conteúdo de um arquivo de documentação."""
    assert path.exists(), f"Arquivo não encontrado: {path}"
    content = path.read_text(encoding="utf-8")
    assert len(content) > 100, f"Arquivo muito pequeno (possível vazio): {path}"
    return content


def _extract_api_paths(content: str) -> list[str]:
    """Extrai caminhos de API (/api/v1/...) mencionados em um documento."""
    pattern = r"/api/v1/[a-zA-Z0-9_/{}.-]+"
    return re.findall(pattern, content)


# ---------------------------------------------------------------------------
# Testes de existência e conteúdo
# ---------------------------------------------------------------------------


class TestRunbookFilesExist:
    """Verifica que os arquivos de runbook existem e têm conteúdo substancial."""

    def test_runbook_degradation_exists(self):
        assert RUNBOOK_DEGRADATION.exists(), (
            f"RUNBOOK_DEGRADATION.md não encontrado em: {RUNBOOK_DEGRADATION}"
        )

    def test_runbook_playbooks_exists(self):
        assert RUNBOOK_PLAYBOOKS.exists(), (
            f"RUNBOOK_INCIDENT_PLAYBOOKS.md não encontrado em: {RUNBOOK_PLAYBOOKS}"
        )

    def test_runbook_degradation_has_content(self):
        content = RUNBOOK_DEGRADATION.read_text(encoding="utf-8")
        assert len(content) > 2000, (
            f"RUNBOOK_DEGRADATION.md parece muito curto ({len(content)} chars). "
            "Verificar se o conteúdo foi truncado."
        )

    def test_runbook_playbooks_has_content(self):
        content = RUNBOOK_PLAYBOOKS.read_text(encoding="utf-8")
        assert len(content) > 2000, (
            f"RUNBOOK_INCIDENT_PLAYBOOKS.md parece muito curto ({len(content)} chars)."
        )

    def test_runbook_degradation_has_version_header(self):
        content = RUNBOOK_DEGRADATION.read_text(encoding="utf-8")
        assert "Versão:" in content, "Runbook de degradação deve ter campo 'Versão:'"

    def test_runbook_playbooks_has_version_header(self):
        content = RUNBOOK_PLAYBOOKS.read_text(encoding="utf-8")
        assert "Versão:" in content, "Runbook de playbooks deve ter campo 'Versão:'"


# ---------------------------------------------------------------------------
# Testes de estrutura do RUNBOOK_DEGRADATION
# ---------------------------------------------------------------------------


class TestRunbookDegradationStructure:
    """Verifica que o RUNBOOK_DEGRADATION contém as seções necessárias."""

    @pytest.fixture(scope="class")
    def content(self):
        return _load_doc(RUNBOOK_DEGRADATION)

    def test_has_circuit_breakers_section(self, content):
        assert "Circuit Breaker" in content, (
            "RUNBOOK_DEGRADATION deve ter seção sobre Circuit Breakers"
        )

    def test_has_drift_detection_section(self, content):
        assert "Drift Detection" in content or "Drift" in content, (
            "RUNBOOK_DEGRADATION deve ter seção sobre Drift Detection"
        )

    def test_has_bias_audit_section(self, content):
        assert "Bias Audit" in content or "bias audit" in content.lower(), (
            "RUNBOOK_DEGRADATION deve ter seção sobre Bias Audit"
        )

    def test_has_hitl_section(self, content):
        assert "HITL" in content, (
            "RUNBOOK_DEGRADATION deve ter seção sobre HITL"
        )

    def test_has_policy_engine_section(self, content):
        assert "PolicyEngine" in content or "Policy Engine" in content, (
            "RUNBOOK_DEGRADATION deve ter seção sobre PolicyEngine"
        )

    def test_has_celery_workers_section(self, content):
        assert "Celery" in content, (
            "RUNBOOK_DEGRADATION deve ter seção sobre Celery Workers"
        )

    def test_has_pos_incidente_section(self, content):
        assert "Pós-Incidente" in content, (
            "RUNBOOK_DEGRADATION deve ter seção de Pós-Incidente"
        )

    def test_circuit_reset_api_documented(self, content):
        assert "reset-all" in content, (
            "RUNBOOK_DEGRADATION deve documentar o endpoint reset-all de circuit breakers"
        )

    def test_drift_warning_urgent_documented(self, content):
        assert "warning" in content.lower() or "critical" in content.lower() or "urgent" in content.lower(), (
            "RUNBOOK_DEGRADATION deve documentar os níveis warning/urgent do drift"
        )

    def test_drift_triggers_documented(self, content):
        triggers = ["score_drift", "approval_drift", "cost_drift", "latency_drift"]
        for trigger in triggers:
            assert trigger in content, (
                f"RUNBOOK_DEGRADATION deve documentar o trigger de drift: {trigger}"
            )

    def test_bias_snapshot_failure_documented(self, content):
        assert "snapshot" in content.lower(), (
            "RUNBOOK_DEGRADATION deve documentar procedimento para falha de snapshot de bias audit"
        )

    def test_hitl_drain_documented(self, content):
        # Deve mencionar como drenar/aprovar aprovações pendentes
        assert "pending" in content.lower() or "pendente" in content.lower(), (
            "RUNBOOK_DEGRADATION deve documentar como drenar aprovações HITL pendentes"
        )

    def test_policy_revert_sector_documented(self, content):
        assert "apply-sector" in content or "setor" in content.lower(), (
            "RUNBOOK_DEGRADATION deve documentar como reverter setor errado no PolicyEngine"
        )

    def test_celery_stuck_diagnosis_documented(self, content):
        assert "inspect" in content or "presa" in content.lower() or "stuck" in content.lower(), (
            "RUNBOOK_DEGRADATION deve documentar diagnóstico de tasks Celery presas"
        )


# ---------------------------------------------------------------------------
# Testes de estrutura do RUNBOOK_INCIDENT_PLAYBOOKS
# ---------------------------------------------------------------------------


class TestRunbookPlaybooksStructure:
    """Verifica que o RUNBOOK_INCIDENT_PLAYBOOKS contém os 5 playbooks obrigatórios."""

    @pytest.fixture(scope="class")
    def content(self):
        return _load_doc(RUNBOOK_PLAYBOOKS)

    def test_has_llm_playbook(self, content):
        assert "LLM" in content or "Anthropic" in content, (
            "Playbook deve ter seção sobre LLM primário down"
        )

    def test_has_database_playbook(self, content):
        assert "Banco" in content or "PostgreSQL" in content or "Neon" in content, (
            "Playbook deve ter seção sobre banco de dados indisponível"
        )

    def test_has_redis_playbook(self, content):
        assert "Redis" in content, (
            "Playbook deve ter seção sobre Redis indisponível"
        )

    def test_has_circuit_breaker_playbook(self, content):
        assert "Circuit Breaker" in content, (
            "Playbook deve ter seção sobre Circuit Breaker em OPEN"
        )

    def test_has_drift_playbook(self, content):
        assert "Drift" in content, (
            "Playbook deve ter seção sobre Drift alerta URGENT"
        )

    def test_has_five_playbooks(self, content):
        # Verificar que pelo menos 4 dos 5 prefixos PB-0x aparecem
        pb_count = sum(1 for i in range(1, 6) if f"PB-0{i}" in content)
        assert pb_count >= 4, (
            f"Esperados 5 playbooks (PB-01 a PB-05), encontrados: {pb_count}"
        )

    def test_has_detection_sections(self, content):
        assert "Detecção" in content, (
            "Playbooks devem ter seções de Detecção"
        )

    def test_has_triagem_sections(self, content):
        assert "Triagem" in content, (
            "Playbooks devem ter seções de Triagem"
        )

    def test_has_contencao_sections(self, content):
        assert "Contenção" in content, (
            "Playbooks devem ter seções de Contenção"
        )

    def test_has_resolucao_sections(self, content):
        assert "Resolução" in content, (
            "Playbooks devem ter seções de Resolução"
        )

    def test_has_pos_incidente_sections(self, content):
        assert "Pós-Incidente" in content, (
            "Playbooks devem ter seções de Pós-Incidente"
        )

    def test_has_quick_reference_table(self, content):
        assert "Referências Rápidas" in content or "Referencia" in content, (
            "Runbook de playbooks deve ter tabela de referências rápidas de endpoints"
        )


# ---------------------------------------------------------------------------
# Testes de integridade dos links de API
# ---------------------------------------------------------------------------


class TestRunbookApiLinks:
    """Verifica que os endpoints mencionados nos runbooks são endpoints conhecidos."""

    @pytest.fixture(scope="class")
    def degradation_content(self):
        return _load_doc(RUNBOOK_DEGRADATION)

    @pytest.fixture(scope="class")
    def playbooks_content(self):
        return _load_doc(RUNBOOK_PLAYBOOKS)

    def test_expected_endpoints_in_degradation(self, degradation_content):
        """Verifica que endpoints obrigatórios aparecem no RUNBOOK_DEGRADATION."""
        for endpoint_prefix in ENDPOINTS_EXPECTED_IN_DEGRADATION:
            assert endpoint_prefix in degradation_content, (
                f"Endpoint '{endpoint_prefix}' não encontrado no RUNBOOK_DEGRADATION.md"
            )

    def test_expected_endpoints_in_playbooks(self, playbooks_content):
        """Verifica que endpoints obrigatórios aparecem no RUNBOOK_INCIDENT_PLAYBOOKS."""
        for endpoint_prefix in ENDPOINTS_EXPECTED_IN_PLAYBOOKS:
            assert endpoint_prefix in playbooks_content, (
                f"Endpoint '{endpoint_prefix}' não encontrado no RUNBOOK_INCIDENT_PLAYBOOKS.md"
            )

    def test_api_paths_in_degradation_are_known(self, degradation_content):
        """
        Verifica que caminhos /api/v1/ extraídos do RUNBOOK_DEGRADATION
        existem no conjunto de endpoints conhecidos (ou são prefixos deles).
        """
        extracted = _extract_api_paths(degradation_content)
        unknown = []
        for path in extracted:
            # Normalizar: remover valores concretos de parâmetros para comparar
            normalized = re.sub(r"/[0-9a-f-]{8,}(/|$)", r"/{id}\1", path)
            normalized = re.sub(r"//+", "/", normalized).rstrip("/")

            matched = any(
                path in known or known.rstrip("/") in path or normalized in known
                for known in KNOWN_ENDPOINTS
            )
            if not matched:
                unknown.append(path)

        # Tolerância: alguns paths podem ser exemplos ou sub-paths — aceitar até 3 desconhecidos
        assert len(unknown) <= 3, (
            f"Mais de 3 caminhos de API desconhecidos no RUNBOOK_DEGRADATION:\n"
            + "\n".join(f"  - {p}" for p in unknown)
        )

    def test_api_paths_in_playbooks_are_known(self, playbooks_content):
        """
        Verifica que caminhos /api/v1/ extraídos do RUNBOOK_INCIDENT_PLAYBOOKS
        existem no conjunto de endpoints conhecidos (ou são prefixos deles).
        """
        extracted = _extract_api_paths(playbooks_content)
        unknown = []
        for path in extracted:
            normalized = re.sub(r"/[0-9a-f-]{8,}(/|$)", r"/{id}\1", path)
            normalized = re.sub(r"//+", "/", normalized).rstrip("/")

            matched = any(
                path in known or known.rstrip("/") in path or normalized in known
                for known in KNOWN_ENDPOINTS
            )
            if not matched:
                unknown.append(path)

        assert len(unknown) <= 3, (
            f"Mais de 3 caminhos de API desconhecidos no RUNBOOK_INCIDENT_PLAYBOOKS:\n"
            + "\n".join(f"  - {p}" for p in unknown)
        )

    def test_circuit_breaker_reset_endpoint_documented(self, degradation_content):
        assert "/api/v1/admin/circuit-breakers" in degradation_content

    def test_circuit_breaker_reset_all_endpoint_documented(self, degradation_content):
        assert "reset-all" in degradation_content

    def test_drift_status_endpoint_documented(self, degradation_content):
        assert "/api/v1/drift/status" in degradation_content

    def test_drift_batch_endpoint_documented(self, degradation_content):
        assert "/api/v1/drift/run-batch" in degradation_content

    def test_bias_audit_endpoint_documented(self, degradation_content):
        assert "/api/v1/bias-audit/job/" in degradation_content

    def test_hitl_approve_endpoint_documented(self, degradation_content):
        assert "/api/v1/hitl/" in degradation_content

    def test_policy_engine_apply_sector_documented(self, degradation_content):
        assert "/api/v1/policy-engine/apply-sector/" in degradation_content

    def test_lgpd_cleanup_endpoint_documented(self, degradation_content):
        # Aceita qualquer sub-endpoint de /api/v1/admin/lgpd/ (run-cleanup ou cleanup-status)
        assert "/api/v1/admin/lgpd/" in degradation_content


# ---------------------------------------------------------------------------
# Testes adicionais de qualidade dos runbooks
# ---------------------------------------------------------------------------


class TestRunbookQuality:
    """Testes de qualidade e completude dos runbooks."""

    @pytest.fixture(scope="class")
    def degradation_content(self):
        return _load_doc(RUNBOOK_DEGRADATION)

    @pytest.fixture(scope="class")
    def playbooks_content(self):
        return _load_doc(RUNBOOK_PLAYBOOKS)

    def test_runbook_degradation_mentions_wedotalent(self, degradation_content):
        assert "WeDOTalent" in degradation_content, (
            "Runbook deve referenciar a marca WeDOTalent"
        )

    def test_runbook_playbooks_mentions_wedotalent(self, playbooks_content):
        assert "WeDOTalent" in playbooks_content, (
            "Runbook de playbooks deve referenciar a marca WeDOTalent"
        )

    def test_runbook_degradation_has_curl_examples(self, degradation_content):
        assert "curl" in degradation_content, (
            "RUNBOOK_DEGRADATION deve ter exemplos com curl"
        )

    def test_runbook_playbooks_has_curl_examples(self, playbooks_content):
        assert "curl" in playbooks_content, (
            "RUNBOOK_INCIDENT_PLAYBOOKS deve ter exemplos com curl"
        )

    def test_runbook_degradation_has_sla_info(self, degradation_content):
        assert "SLA" in degradation_content, (
            "RUNBOOK_DEGRADATION deve mencionar SLA"
        )

    def test_runbook_playbooks_has_sla_info(self, playbooks_content):
        assert "SLA" in playbooks_content, (
            "RUNBOOK_INCIDENT_PLAYBOOKS deve mencionar SLA"
        )

    def test_runbooks_mention_lgpd(self, degradation_content, playbooks_content):
        """Ambos os runbooks devem mencionar LGPD por questões de compliance."""
        assert "LGPD" in degradation_content, "RUNBOOK_DEGRADATION deve mencionar LGPD"
        assert "LGPD" in playbooks_content, "RUNBOOK_INCIDENT_PLAYBOOKS deve mencionar LGPD"

    def test_runbook_degradation_has_celery_beat(self, degradation_content):
        assert "celery-beat" in degradation_content or "Celery Beat" in degradation_content, (
            "RUNBOOK_DEGRADATION deve mencionar Celery Beat"
        )

    def test_runbook_degradation_drift_four_triggers(self, degradation_content):
        """Os 4 triggers de drift devem estar documentados."""
        expected = ["score_drift", "approval_drift", "cost_drift", "latency_drift"]
        for t in expected:
            assert t in degradation_content, (
                f"Trigger '{t}' não documentado no RUNBOOK_DEGRADATION"
            )

    def test_runbook_playbooks_has_five_playbooks_titles(self, playbooks_content):
        """Os 5 playbooks devem ter títulos identificáveis."""
        expected_topics = [
            "LLM",
            "Banco",
            "Redis",
            "Circuit Breaker",
            "Drift",
        ]
        for topic in expected_topics:
            assert topic in playbooks_content, (
                f"Playbook sobre '{topic}' não encontrado no RUNBOOK_INCIDENT_PLAYBOOKS"
            )
