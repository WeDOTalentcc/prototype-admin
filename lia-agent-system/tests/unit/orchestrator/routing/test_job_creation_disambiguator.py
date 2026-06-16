"""
TDD (Task #1211) — canonical job-creation disambiguator.

The disambiguator is the single source of truth for deciding whether a recruiter
message is a JOB-CREATION request (which must ALWAYS route to the canonical
wizard, never to Plan & Execute) and, when the request is composite
("criar a vaga E publicar"), what the optional post-wizard continuation is.

RED first: module does not exist yet.

Run: pytest tests/unit/orchestrator/routing/test_job_creation_disambiguator.py -v
"""
import pytest


# ---------------------------------------------------------------------------
# 1. Creation detection — simple and composite phrasings
# ---------------------------------------------------------------------------

class TestDetectsCreation:
    @pytest.mark.parametrize(
        "msg",
        [
            "criar vaga",
            "criar uma vaga de desenvolvedor",
            "quero criar uma nova vaga",
            "abrir vaga de designer",
            "abrir uma nova posição de QA",
            "vamos criar a vaga de backend",
            "preciso de uma vaga nova",
            # composite phrasings that the substring-only wizard bootstrap MISSES
            "criar a vaga e publicar no ATS",
            "criar a vaga e sincronizar com o Gupy",
            "criar uma vaga de Python e publicar",
        ],
    )
    def test_is_creation_true(self, msg):
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation(msg)
        assert result is not None
        assert result.is_creation is True

    @pytest.mark.parametrize(
        "msg",
        [
            "buscar desenvolvedores e comparar",
            "gerar relatório semanal",
            "olá, tudo bem?",
            "publicar a vaga existente",  # publish-only, not creation
            "mover candidato e notificar",
        ],
    )
    def test_is_creation_false(self, msg):
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation(msg)
        assert result is None or result.is_creation is False


# ---------------------------------------------------------------------------
# 2. Composite continuation extraction
# ---------------------------------------------------------------------------

class TestContinuationExtraction:
    def test_simple_creation_has_no_continuation(self):
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation("criar uma vaga de desenvolvedor")
        assert result is not None
        assert result.is_creation is True
        assert result.continuation_kind is None

    def test_composite_publish_continuation(self):
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation("criar a vaga e publicar no ATS")
        assert result is not None
        assert result.is_creation is True
        assert result.continuation_kind == "publish_job"
        assert result.continuation_text  # human-readable, non-empty

    def test_composite_sync_continuation(self):
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation("criar a vaga e sincronizar com o Gupy")
        assert result is not None
        assert result.continuation_kind in ("publish_job", "sync_job")

    def test_composite_unknown_continuation_signalled_not_faked(self):
        """A composite with a continuation we cannot yet execute must still be
        captured (continuation_text preserved) but flagged as not-connected —
        never silently dropped, never faked as connected."""
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation(
            "criar a vaga e buscar candidatos no LinkedIn"
        )
        assert result is not None
        assert result.is_creation is True
        assert result.continuation_text
        # Sourcing continuation is not yet connected → kind is None (unknown),
        # but the raw text is preserved so the offer can signal it explicitly.
        assert result.continuation_connected is False


# ---------------------------------------------------------------------------
# 3. Continuation kind → connected mapping is explicit
# ---------------------------------------------------------------------------

class TestConnectedContinuations:
    def test_publish_is_connected(self):
        from app.orchestrator.routing.job_creation_disambiguator import (
            detect_job_creation,
        )
        result = detect_job_creation("criar a vaga e publicar")
        assert result is not None
        assert result.continuation_connected is True
