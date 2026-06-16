"""TDD Fase 3 — intake_gate confirmação assistida de competências.

O intake_gate, ao aprovar a criação, sugere competências técnicas +
comportamentais (via CompetencyBenchmarkService da Fase 2), dimensionadas
pelo modo, e seed em confirmed_* (accept-all default; recruiter edita via
painel — Fase 5). Não-bloqueante: falha na sugestão não impede aprovação.

Run:
    cd lia-agent-system && python -m pytest tests/wizard/test_intake_gate_competencies_fase3.py -v --no-cov
"""
from __future__ import annotations
import sys
import importlib
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


# ── 1. State fields ───────────────────────────────────────────────────────────

class TestStateFields:
    def test_state_declares_confirmed_competency_fields(self):
        from app.domains.job_creation.state import JobCreationState
        ann = JobCreationState.__annotations__
        assert "confirmed_technical_competencies" in ann
        assert "confirmed_behavioral_competencies" in ann
        assert "intake_competencies_suggested" in ann


# ── helpers ───────────────────────────────────────────────────────────────────

def _approval_state(user_query="compacto, pode criar", **overrides):
    base = {
        "parsed_title": "Engenheiro de Software",
        "parsed_seniority": "senior",
        "parsed_model": "remoto",
        "parsed_department": "Tecnologia",
        "intake_salary_suggested": True,
        "intake_approved": None,
        "screening_mode": None,
        "user_query": user_query,
        "raw_input": "criar vaga engenheiro senior remoto",
        "intake_gate_seen_user_query": "criar vaga engenheiro senior remoto",
        "current_stage": "intake",
        "workspace_id": "cid-1",
        "company_id": "cid-1",
    }
    base.update(overrides)
    return base


def _fake_suggestion(n_tech=5, n_behav=2):
    return {
        "technical": [{"skill": f"Tec{i}", "contexto": f"c{i}"} for i in range(1, n_tech + 1)],
        "behavioral": [
            {"competencia": f"Comp{i}", "contexto": f"c{i}", "trait_big_five": "conscientiousness"}
            for i in range(1, n_behav + 1)
        ],
        "confidence": "medium",
        "screening_mode": "compact",
        "is_estimate": False,
    }


def _run_approval(state, suggestion=None, suggest_side_effect=None):
    """Roda intake_gate_node no path de aprovação, mockando o serviço de competências."""
    node_mod = importlib.import_module("app.domains.job_creation.nodes.intake_gate")

    svc = mock.MagicMock()
    if suggest_side_effect is not None:
        svc.suggest_competencies = mock.AsyncMock(side_effect=suggest_side_effect)
    else:
        svc.suggest_competencies = mock.AsyncMock(
            return_value=suggestion if suggestion is not None else _fake_suggestion()
        )

    with mock.patch(
        "app.domains.job_creation.nodes.intake_gate._in_graph_runtime", return_value=False,
    ), mock.patch(
        "app.domains.job_creation.nodes.intake_gate._safe_fetch_salary",
        return_value={"min": 10000, "max": 15000},
    ), mock.patch(
        "app.domains.analytics.services.competency_benchmark_service.get_competency_benchmark_service",
        return_value=svc,
    ):
        result = node_mod.intake_gate_node(state)
    return result, svc


# ── 2. Aprovação seed confirmed_* a partir das sugestões ─────────────────────

class TestApprovalSeedsCompetencies:
    def test_approval_succeeds(self):
        result, _ = _run_approval(_approval_state())
        assert result.get("intake_approved") is True

    def test_confirmed_technical_seeded(self):
        result, _ = _run_approval(_approval_state(), suggestion=_fake_suggestion(5, 2))
        tech = result.get("confirmed_technical_competencies") or []
        assert len(tech) == 5
        assert tech[0]["skill"] == "Tec1"

    def test_confirmed_behavioral_seeded(self):
        result, _ = _run_approval(_approval_state(), suggestion=_fake_suggestion(5, 2))
        behav = result.get("confirmed_behavioral_competencies") or []
        assert len(behav) == 2
        assert behav[0]["trait_big_five"] == "conscientiousness"

    def test_competencies_suggested_flag_set(self):
        result, _ = _run_approval(_approval_state())
        assert result.get("intake_competencies_suggested") is True

    def test_service_called_with_chosen_mode(self):
        """Recruiter escolheu 'compacto' → serviço chamado com screening_mode='compact'."""
        _, svc = _run_approval(_approval_state(user_query="compacto, pode criar"))
        svc.suggest_competencies.assert_awaited_once()
        kwargs = svc.suggest_competencies.await_args.kwargs
        assert kwargs.get("screening_mode") == "compact"

    def test_service_called_with_full_mode(self):
        _, svc = _run_approval(_approval_state(user_query="completo, pode criar"))
        kwargs = svc.suggest_competencies.await_args.kwargs
        assert kwargs.get("screening_mode") == "full"

    def test_service_called_with_company_id(self):
        """Multi-tenancy: company_id do contexto repassado ao serviço."""
        _, svc = _run_approval(_approval_state())
        kwargs = svc.suggest_competencies.await_args.kwargs
        assert kwargs.get("company_id") == "cid-1"

    def test_suggestions_attached_to_payload(self):
        result, _ = _run_approval(_approval_state(), suggestion=_fake_suggestion(5, 2))
        ws = result.get("ws_stage_payload") or {}
        data = ws.get("data") or {}
        comp = (data.get("suggestions_data") or {}).get("competencies")
        assert comp is not None, "competências sugeridas devem ir ao payload (para o painel)"
        assert len(comp.get("technical") or []) == 5


# ── 3. right_panel_form override ─────────────────────────────────────────────

class TestPanelOverride:
    def test_panel_competencies_override_suggestions(self):
        """Se o recruiter editou competências no painel, elas têm precedência."""
        panel = {
            "confirmed_technical_competencies": [{"skill": "Rust", "contexto": "editado"}],
            "confirmed_behavioral_competencies": [
                {"competencia": "Liderança", "contexto": "x", "trait_big_five": "extraversion"},
            ],
        }
        state = _approval_state(right_panel_form=panel)
        result, _ = _run_approval(state, suggestion=_fake_suggestion(5, 2))
        tech = result.get("confirmed_technical_competencies") or []
        assert len(tech) == 1
        assert tech[0]["skill"] == "Rust"


# ── 4. Fail-open ──────────────────────────────────────────────────────────────

class TestFailOpen:
    def test_service_error_still_approves(self):
        """CompetencyBenchmarkService quebra → aprovação NÃO é bloqueada."""
        result, _ = _run_approval(
            _approval_state(), suggest_side_effect=RuntimeError("svc down"),
        )
        assert result.get("intake_approved") is True
        # confirmed_* deve ser lista (vazia ok), nunca None que quebre downstream
        assert isinstance(result.get("confirmed_technical_competencies"), list)
        assert isinstance(result.get("confirmed_behavioral_competencies"), list)
