"""Unit tests for the canonical IntakeExtractor (Task #850).

Covers:
  * Pydantic JobIntakePayload field semantics (`field_is_filled`).
  * `compute_precompleted_stages` routing — including the
    ``NEVER_PRECOMPLETED`` HITL invariant (HITL 1 jd_enrichment + HITL 2
    wsi_questions are never skipped, even when the recruiter provides
    detailed input).
  * Regex fallback parser (no LLM dependency) for title/seniority/work
    model/salary.

These tests are intentionally LLM-free so they can run in CI without any
API keys.
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.services.intake_extractor import (
    IntakeExtractor,
    IntakeField,
    JobIntakePayload,
    LocationField,
    NEVER_PRECOMPLETED,
    SalaryRange,
    _label_for,
    _regex_extract,
    compute_precompleted_stages,
)


# ---------------------------------------------------------------------------
# JobIntakePayload primitives
# ---------------------------------------------------------------------------


class TestJobIntakePayload:
    def test_empty_field_is_not_filled(self):
        p = JobIntakePayload(raw_input="x")
        assert p.field_is_filled("title") is False
        assert p.field_is_filled("salary") is False
        assert p.field_is_filled("technical_skills") is False

    def test_string_field_filled(self):
        p = JobIntakePayload(raw_input="x")
        p.title = IntakeField(value="Engenheiro de Dados", confidence=0.9)
        assert p.field_is_filled("title") is True

    def test_blank_string_is_not_filled(self):
        p = JobIntakePayload(raw_input="x")
        p.title = IntakeField(value="   ", confidence=0.9)
        assert p.field_is_filled("title") is False

    def test_empty_list_is_not_filled(self):
        p = JobIntakePayload(raw_input="x")
        p.technical_skills = IntakeField(value=[], confidence=0.5)
        assert p.field_is_filled("technical_skills") is False

    def test_list_with_items_is_filled(self):
        p = JobIntakePayload(raw_input="x")
        p.technical_skills = IntakeField(value=["python", "sql"], confidence=0.7)
        assert p.field_is_filled("technical_skills") is True

    def test_salary_dict_with_values_is_filled(self):
        p = JobIntakePayload(raw_input="x")
        p.salary = IntakeField(
            value=SalaryRange(min=8000, max=12000).model_dump(),
            confidence=0.8,
        )
        assert p.field_is_filled("salary") is True

    def test_salary_dict_all_none_is_not_filled(self):
        p = JobIntakePayload(raw_input="x")
        p.salary = IntakeField(
            value={"min": None, "max": None, "currency": "BRL"},
            confidence=0.0,
        )
        assert p.field_is_filled("salary") is False


# ---------------------------------------------------------------------------
# compute_precompleted_stages — HITL invariant (Task #850)
# ---------------------------------------------------------------------------


class TestPrecompletedStages:
    def test_never_precompleted_set_contains_both_hitl_stages(self):
        # HITL 1 (jd_enrichment) and HITL 2 (wsi_questions) MUST never
        # appear in the precompleted set, regardless of recruiter input.
        assert "jd_enrichment" in NEVER_PRECOMPLETED
        assert "wsi_questions" in NEVER_PRECOMPLETED

    def test_empty_payload_precompletes_nothing(self):
        p = JobIntakePayload(raw_input="vaga")
        assert compute_precompleted_stages(p) == set()

    def test_salary_alone_precompletes_only_salary_stage(self):
        p = JobIntakePayload(raw_input="x")
        p.salary = IntakeField(
            value=SalaryRange(min=10_000, max=15_000).model_dump(),
            confidence=0.9,
        )
        result = compute_precompleted_stages(p)
        assert result == {"salary"}
        # HITL stages stay out.
        assert "jd_enrichment" not in result
        assert "wsi_questions" not in result

    def test_competency_requires_both_skill_lists(self):
        p = JobIntakePayload(raw_input="x")
        p.technical_skills = IntakeField(value=["python"], confidence=0.7)
        # behavioral_skills missing → competency NOT precompleted.
        assert compute_precompleted_stages(p) == set()

        p.behavioral_skills = IntakeField(value=["comunicacao"], confidence=0.7)
        assert compute_precompleted_stages(p) == {"competency"}

    def test_full_payload_never_skips_hitl(self):
        # Even a fully-specified intake must not bypass HITL 1 / HITL 2.
        p = JobIntakePayload(raw_input="x")
        p.title = IntakeField(value="Eng. de Dados", confidence=0.95)
        p.seniority = IntakeField(value="senior", confidence=0.9)
        p.salary = IntakeField(
            value=SalaryRange(min=15_000, max=22_000).model_dump(),
            confidence=0.9,
        )
        p.technical_skills = IntakeField(
            value=["python", "spark", "sql"], confidence=0.85
        )
        p.behavioral_skills = IntakeField(
            value=["comunicacao", "ownership"], confidence=0.8
        )
        result = compute_precompleted_stages(p)
        assert "salary" in result
        assert "competency" in result
        assert "jd_enrichment" not in result
        assert "wsi_questions" not in result


# ---------------------------------------------------------------------------
# Regex fallback — no LLM required
# ---------------------------------------------------------------------------


class TestRegexFallback:
    def test_extracts_title_seniority_and_model(self):
        # Use accent-free "Senior" so the documented `sen → senior`
        # normalization branch is exercised deterministically.
        raw = "Vaga de Engenheiro de Dados Senior remoto no time de Dados"
        p = _regex_extract(raw)
        assert p.title.value
        assert "engenheiro" in p.title.value.lower()
        assert p.seniority.value == "senior"
        assert p.work_model.value == "remoto"

    def test_extracts_salary_range(self):
        raw = "Salário entre R$ 10.000 a R$ 15.000"
        p = _regex_extract(raw)
        assert p.salary.value["min"] == 10000
        assert p.salary.value["max"] == 15000

    def test_overall_confidence_is_zero_when_nothing_matches(self):
        p = _regex_extract("...")
        assert p.overall_confidence == 0.0

    def test_overall_confidence_averaged_across_fields(self):
        p = _regex_extract("Vaga de Tech Lead pleno híbrido")
        assert p.overall_confidence > 0.0


# ---------------------------------------------------------------------------
# IntakeExtractor.extract — falls back to regex when no LLM client is given
# ---------------------------------------------------------------------------


class TestIntakeExtractorLLMSuccess:
    """Cover the LLM-success path — Task #850 reviewer flagged that this
    branch was previously crashing because confidence aggregation
    referenced removed field names. We exercise the full pipeline with
    a stub LLM that returns valid JSON for the new schema."""

    class _StubLLM:
        def __init__(self, payload: dict):
            self._payload = payload

        def invoke(self, prompt):  # langchain-style ChatModel
            import json

            class _R:
                def __init__(self, content):
                    self.content = content

            return _R(json.dumps(self._payload))

    def test_llm_success_aggregates_confidence_over_split_manager_fields(
        self, monkeypatch
    ):
        # Bypass FairnessGuard + PII mask to keep the test deterministic.
        # The extractor imports `check_input_fairness` and
        # `mask_pii_for_llm` from compliance helpers — patch them on the
        # module namespace where the extractor binds them.
        from app.domains.job_creation.services import intake_extractor as mod

        class _FairnessOK:
            is_blocked = False
            category = None
            blocked_terms: list = []
            educational_message = None

        monkeypatch.setattr(
            mod, "check_input_fairness",
            lambda raw: _FairnessOK(),
            raising=True,
        )
        monkeypatch.setattr(mod, "mask_pii_for_llm", lambda raw: raw, raising=True)

        llm_payload = {
            "title": {"value": "Engenheiro de Dados", "confidence": 0.95},
            "department": {"value": "Dados", "confidence": 0.8},
            "location": {
                "value": {"city": "Sao Paulo", "state": "SP", "country": "Brasil"},
                "confidence": 0.9,
            },
            "work_model": {"value": "remoto", "confidence": 0.95},
            "seniority": {"value": "senior", "confidence": 0.9},
            "manager_name": {"value": "Ana Souza", "confidence": 0.85},
            "manager_email": {"value": "ana@acme.com", "confidence": 0.7},
            "contract_type": {"value": "clt", "confidence": 0.9},
            "responsibilities": {"value": ["liderar squad"], "confidence": 0.7},
            "technical_skills": {"value": ["python"], "confidence": 0.7},
            "behavioral_skills": {"value": ["ownership"], "confidence": 0.8},
            "languages": {"value": ["português"], "confidence": 0.6},
            "salary": {
                "value": {"min": 18000, "max": 25000, "currency": "BRL"},
                "confidence": 0.85,
            },
            "benefits": {"value": ["VR"], "confidence": 0.6},
        }

        extractor = IntakeExtractor(llm_client=self._StubLLM(llm_payload))
        payload = extractor.extract("Vaga de Engenheiro de Dados Senior remoto SP")

        # Both split manager fields land — proves we aren't crashing on
        # the legacy `manager` aggregation key.
        assert payload.manager_name.value == "Ana Souza"
        assert payload.manager_email.value == "ana@acme.com"
        # Confidence aggregation is dynamic over all IntakeField attrs.
        assert 0.7 <= payload.overall_confidence <= 0.95
        # Source is `llm` for an LLM-derived payload.
        assert payload.title.source == "llm"
        # Stage routing now picks up intake + salary + competency.
        skipped = compute_precompleted_stages(payload)
        assert {"intake", "salary", "competency"}.issubset(skipped)
        # HITL invariant still holds.
        assert "jd_enrichment" not in skipped
        assert "wsi_questions" not in skipped


class TestRunJobWizardCompatibilityShim:
    """Lock the legacy `GraphRunnerService.run_job_wizard` API contract
    after Task #850 rerouted it to `JobCreationGraph`. Reviewer flagged
    that an empty `response_text` / stale `job_draft` from the REST
    endpoint `/lia-assistant/job-wizard/graph-orchestrate` would be a
    regression — this guards against it.
    """

    def test_reroute_returns_legacy_shape_with_non_empty_response(
        self, monkeypatch
    ):
        from app.domains.ai.services import graph_runner as gr_mod

        # Stub the canonical graph singleton so we don't need the full
        # backend stack — what we're locking in here is the response
        # *translation*, not the graph nodes themselves.
        class _StubGraph:
            def invoke(self, state, thread_id):
                return {
                    **state,
                    "current_stage": "intake",
                    "intake_payload": {
                        "title": {"value": "Eng. Dados", "confidence": 0.9},
                        "seniority": {"value": "senior", "confidence": 0.9},
                    },
                    "stage_history": ["intake"],
                    "ws_stage_payload": {
                        "type": "wizard_stage",
                        "stage": "intake",
                        "data": {
                            "raw_input": "Vaga de Eng Dados Senior",
                            "intake_payload": {},
                            "precompleted_stages": [],
                            "fairness_blocked": False,
                        },
                    },
                }

        # Patch the module-level singleton (pulled in by the lazy import
        # inside `run_job_wizard`).
        from app.domains.job_creation import graph as jc_graph

        monkeypatch.setattr(jc_graph, "job_creation_graph", _StubGraph(),
                            raising=True)

        # Use the public service constructor — it leaves `self.graph` as
        # `None` (the legacy graph singleton was retired) so the reroute
        # branch fires.
        service = gr_mod.GraphRunnerService()
        assert service.graph is None  # reroute precondition

        import asyncio

        result = asyncio.run(service.run_job_wizard(
            session_id="s1",
            user_message="Vaga de Eng Dados Senior",
            company_id="c1",
            user_id="u1",
        ))

        # Legacy contract — every key is present and non-empty/sane.
        assert isinstance(result["response_text"], str) and result["response_text"]
        assert "Eng. Dados" in result["response_text"]  # built from intake
        assert result["job_draft"]  # the canonical intake_payload dict
        assert result["job_draft"]["title"]["value"] == "Eng. Dados"
        assert result["current_stage"] == "intake"
        assert result["reasoning_steps"] == ["stage:intake"]
        assert result["execution_id"] == "s1"


class TestWizardCanonicalResume:
    """Lock the canonical HITL resume contract used by the WS handler
    (`/api/v1/agent_chat_ws.py::_resume_wizard_canonical`). Reviewer
    flagged the previous `wiz_g._graph.ainvoke(None, ...)` pattern as
    fragile and reading from non-canonical legacy keys
    (`response`/`user_message`). This guards the new path that:
      1. uses `JobCreationGraph.resume(thread_id, prior, updates)`
         (so the audit callback stays wired);
      2. extracts the recruiter-facing message from the canonical
         `ws_stage_payload.data` with stage-aware fallback.
    """

    def test_resume_uses_canonical_api_and_canonical_extraction(
        self, monkeypatch
    ):
        from app.api.v1 import chat_shared as ws_mod
        from app.domains.job_creation import graph as jc_graph

        # Capture how the helper drives the canonical resume API.
        calls: dict = {}

        class _StubSnapshot:
            values = {"current_stage": "jd_enrichment", "intake_payload": {}}

        class _StubGraph:
            def get_state(self, config):
                calls["get_state_thread"] = config["configurable"]["thread_id"]
                return _StubSnapshot()

        class _StubJobGraph:
            _graph = _StubGraph()

            def resume(self, thread_id, prior_state, updates):
                calls["resume_thread"] = thread_id
                calls["resume_prior"] = prior_state
                calls["resume_updates"] = updates
                # Emit canonical state — ws_stage_payload + current_stage,
                # NOT legacy `response`/`user_message`.
                return {
                    "current_stage": "wsi_questions",
                    "intake_payload": {"title": {"value": "Eng"}},
                    "ws_stage_payload": {
                        "type": "wizard_stage",
                        "stage": "wsi_questions",
                        "data": {"message": "Aprovado. Revise as perguntas WSI."},
                    },
                }

        monkeypatch.setattr(jc_graph, "job_creation_graph", _StubJobGraph(),
                            raising=True)

        message, stage_payload = ws_mod._resume_wizard_canonical(
            "thr-42",
            {
                "context": {
                    "draft": {"title": "Eng. Dados"},
                },
                "approval_payload": {"approved_by": "u-7"},
            },
        )

        # Canonical resume API was called with the prior state pulled
        # from the checkpointer plus merged approval updates.
        assert calls["resume_thread"] == "thr-42"
        assert calls["get_state_thread"] == "thr-42"
        assert calls["resume_prior"]["current_stage"] == "jd_enrichment"
        assert calls["resume_updates"]["hitl_approved"] is True
        assert calls["resume_updates"]["approved_by"] == "u-7"
        assert calls["resume_updates"]["draft"] == {"title": "Eng. Dados"}

        # Recruiter-facing message comes from the canonical
        # ws_stage_payload.data.message — never from legacy keys.
        assert message == "Aprovado. Revise as perguntas WSI."
        # Stage payload is forwarded for the right-panel UI.
        assert stage_payload["stage"] == "wsi_questions"
        assert stage_payload["type"] == "wizard_stage"

    def test_resume_falls_back_to_stage_summary_when_no_message(
        self, monkeypatch
    ):
        """If the resumed node didn't emit a `data.message`, the helper
        builds a stage-aware Portuguese fallback so the recruiter never
        sees an empty assistant bubble.
        """
        from app.api.v1 import chat_shared as ws_mod
        from app.domains.job_creation import graph as jc_graph

        class _StubGraph:
            def get_state(self, config):
                class _S:
                    values = {}
                return _S()

        class _StubJobGraph:
            _graph = _StubGraph()

            def resume(self, thread_id, prior_state, updates):
                return {
                    "current_stage": "completed",
                    "ws_stage_payload": {"data": {}},
                }

        monkeypatch.setattr(jc_graph, "job_creation_graph", _StubJobGraph(),
                            raising=True)

        message, _ = ws_mod._resume_wizard_canonical("thr-9", {})
        assert message == "Vaga criada com sucesso."


class TestIntakeNodeMultiSourceWiring:
    """Lock the intake_node → extract_from_sources contract so the
    canonical multi-source merge (form > text > file) actually fires
    in-graph when the recruiter provides structured form data or an
    attached JD.
    """

    def test_intake_node_routes_to_extract_from_sources_when_form_present(
        self, monkeypatch
    ):
        from app.domains.job_creation import graph as jc_graph

        captured: dict = {}

        # Stub the extractor singleton so we can assert which method
        # the node called and with what arguments.
        class _StubExtractor:
            def extract(self, query):
                captured["called"] = "extract"
                raise AssertionError("multi-source path should win")

            def extract_from_sources(
                self, user_text, right_panel_form, attached_file_text
            ):
                captured["called"] = "extract_from_sources"
                captured["user_text"] = user_text
                captured["right_panel_form"] = right_panel_form
                captured["attached_file_text"] = attached_file_text
                # Return a real (minimal) JobIntakePayload via the real
                # extractor to avoid mocking the whole schema.
                from app.domains.job_creation.services.intake_extractor import (
                    get_intake_extractor,
                )
                return get_intake_extractor().extract("")

        monkeypatch.setattr(
            jc_graph, "get_intake_extractor", lambda: _StubExtractor(),
            raising=True,
        )

        out = jc_graph.intake_node({
            "raw_input": "Vaga de Eng",
            "right_panel_form": {"title": "Eng. Dados", "seniority": "senior"},
            "attached_file_text": "JD: Eng. de Dados Sênior, SP, Python.",
        })

        assert captured["called"] == "extract_from_sources"
        assert captured["user_text"] == "Vaga de Eng"
        assert captured["right_panel_form"] == {
            "title": "Eng. Dados", "seniority": "senior",
        }
        assert "Python" in captured["attached_file_text"]
        # Node still emits canonical state shape.
        assert out["current_stage"] == "intake"
        assert "ws_stage_payload" in out

    def test_intake_node_uses_single_source_extract_for_text_only(
        self, monkeypatch
    ):
        from app.domains.job_creation import graph as jc_graph

        captured: dict = {}

        class _StubExtractor:
            def extract(self, query):
                captured["called"] = "extract"
                captured["query"] = query
                from app.domains.job_creation.services.intake_extractor import (
                    get_intake_extractor,
                )
                return get_intake_extractor().extract(query)

            def extract_from_sources(self, **kwargs):
                raise AssertionError("single-source path should win")

        monkeypatch.setattr(
            jc_graph, "get_intake_extractor", lambda: _StubExtractor(),
            raising=True,
        )

        jc_graph.intake_node({"raw_input": "Vaga de Eng Dados"})
        assert captured["called"] == "extract"
        assert captured["query"] == "Vaga de Eng Dados"


class TestStreamJobWizardRetired:
    """`stream_job_wizard()` targeted the retired legacy graph and has
    no callers. Task #857 (N-01): guard against silent failure if a
    future caller is wired up — must raise an HTTP 410 Gone with the
    canonical migration payload instead of leaking the legacy
    NotImplementedError as a 500.
    """

    def test_stream_job_wizard_raises_410_gone(self):
        import asyncio

        from fastapi import HTTPException

        from app.domains.ai.services.graph_runner import GraphRunnerService

        service = GraphRunnerService()
        assert service.graph is None  # legacy singleton retired

        async def _drive():
            agen = service.stream_job_wizard(
                session_id="s",
                user_message="m",
                company_id="c",
                user_id="u",
            )
            await agen.__anext__()

        try:
            asyncio.run(_drive())
        except HTTPException as exc:
            assert exc.status_code == 410
            assert exc.detail == {
                "error": (
                    "Endpoint deprecated. Use WS /ws/agent-chat with "
                    "domain=job_creation."
                ),
            }
        else:
            raise AssertionError("expected HTTPException(410)")


class TestIntakeExtractorFallback:
    def test_extract_uses_regex_when_llm_unavailable(self, monkeypatch):
        # Force the lazy `_get_llm` to return None so the LLM branch is
        # skipped and the regex fallback runs.
        extractor = IntakeExtractor(llm_client=None)
        monkeypatch.setattr(extractor, "_get_llm", lambda: None)
        payload = extractor.extract("Vaga de Engenheiro de Dados Senior remoto")
        assert isinstance(payload, JobIntakePayload)
        assert payload.title.value
        assert payload.seniority.value == "senior"
        # Source should be `regex` (fallback path) — never `llm`.
        assert payload.title.source == "regex"

    def test_extract_blank_input_returns_empty_payload(self):
        extractor = IntakeExtractor(llm_client=None)
        payload = extractor.extract("   ")
        assert isinstance(payload, JobIntakePayload)
        assert payload.overall_confidence == 0.0
        assert compute_precompleted_stages(payload) == set()


# ---------------------------------------------------------------------------
# Confidence label contract (Task #850 spec)
# ---------------------------------------------------------------------------


class TestConfidenceLabel:
    @pytest.mark.parametrize("score,label", [
        (0.0, "low"), (0.49, "low"),
        (0.5, "medium"), (0.79, "medium"),
        (0.8, "high"), (1.0, "high"),
    ])
    def test_label_buckets(self, score, label):
        assert _label_for(score) == label

    def test_field_exposes_label(self):
        f = IntakeField(value="x", confidence=0.92, source="user_text")
        assert f.confidence_label == "high"
        assert f.source == "user_text"

    def test_payload_exposes_overall_label(self):
        p = JobIntakePayload(raw_input="x", overall_confidence=0.6)
        assert p.overall_confidence_label == "medium"


# ---------------------------------------------------------------------------
# LocationField + manager split (Task #850 spec)
# ---------------------------------------------------------------------------


class TestStructuredFields:
    def test_location_is_structured(self):
        loc = LocationField(city="Sao Paulo", state="SP", country="Brasil")
        p = JobIntakePayload(raw_input="x")
        p.location = IntakeField(value=loc.model_dump(), confidence=0.9, source="user_text")
        assert p.field_is_filled("location") is True
        assert p.location.value["city"] == "Sao Paulo"

    def test_manager_split_into_name_and_email(self):
        # manager_name and manager_email are independent fields per spec.
        p = JobIntakePayload(raw_input="x")
        p.manager_name = IntakeField(value="Ana", confidence=0.9, source="right_panel_form")
        # Email arrives only from the attached file's signature.
        p.manager_email = IntakeField(value="ana@acme.com", confidence=0.85, source="attached_file")
        assert p.field_is_filled("manager_name") is True
        assert p.field_is_filled("manager_email") is True
        assert p.manager_name.source == "right_panel_form"
        assert p.manager_email.source == "attached_file"


# ---------------------------------------------------------------------------
# Multi-source merge (extract_from_sources) — Task #850 spec
# ---------------------------------------------------------------------------


class TestMultiSourceMerge:
    def test_form_beats_text_on_overlap(self, monkeypatch):
        extractor = IntakeExtractor(llm_client=None)
        monkeypatch.setattr(extractor, "_get_llm", lambda: None)
        merged = extractor.extract_from_sources(
            user_text="Vaga de Engenheiro de Dados Senior remoto",
            right_panel_form={"title": "Eng. de Dados Pleno", "department": "Dados"},
        )
        # Form has highest confidence (0.95) → wins on title.
        assert merged.title.value == "Eng. de Dados Pleno"
        assert merged.title.source == "right_panel_form"
        # Department came only from form.
        assert merged.department.value == "Dados"
        # Seniority came only from text → preserved.
        assert merged.seniority.value == "senior"
        assert merged.seniority.source == "user_text"

    def test_attached_file_fills_missing_fields_only(self, monkeypatch):
        extractor = IntakeExtractor(llm_client=None)
        monkeypatch.setattr(extractor, "_get_llm", lambda: None)
        merged = extractor.extract_from_sources(
            user_text="Vaga de Tech Lead remoto",
            attached_file_text="Salário entre R$ 18.000 a R$ 25.000",
        )
        # Salary only present in attached file.
        assert merged.salary.value["min"] == 18000
        assert merged.salary.source == "attached_file"
        # Work model comes from user text.
        assert merged.work_model.value == "remoto"
        assert merged.work_model.source == "user_text"

    def test_merge_preserves_hitl_invariant(self, monkeypatch):
        extractor = IntakeExtractor(llm_client=None)
        monkeypatch.setattr(extractor, "_get_llm", lambda: None)
        merged = extractor.extract_from_sources(
            user_text="Vaga de Eng Senior remoto",
            right_panel_form={
                "salary": {"min": 12000, "max": 18000, "currency": "BRL"},
                "technical_skills": ["python"],
                "behavioral_skills": ["ownership"],
            },
            attached_file_text="Responsabilidades: liderar squad",
        )
        skipped = compute_precompleted_stages(merged)
        assert "salary" in skipped
        assert "competency" in skipped
        # HITL invariant — never skipped, regardless of how complete the
        # multi-source payload is.
        assert "jd_enrichment" not in skipped
        assert "wsi_questions" not in skipped
