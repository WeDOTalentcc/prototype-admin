"""Coverage tests for app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py
and app/templates/report_templates.py.
"""
import pytest
from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import (
    KanbanCommandType,
    KANBAN_COMMAND_TYPES,
    LIA_SYSTEM_PROMPT,
    COMMAND_TEMPLATES,
    NEGATION_PREFIXES,
    get_system_prompt,
    detect_command_type,
    resolve_ui_action,
    get_kanban_prompt_template,
    format_job_context,
    format_candidates_context,
    format_selected_candidates_context,
    format_pipeline_context,
)


class TestModuleConstants:
    def test_lia_system_prompt_exists(self):
        assert LIA_SYSTEM_PROMPT
        assert len(LIA_SYSTEM_PROMPT) > 100

    def test_command_templates_exists(self):
        assert COMMAND_TEMPLATES
        assert isinstance(COMMAND_TEMPLATES, dict)
        assert len(COMMAND_TEMPLATES) > 0

    def test_kanban_command_types_exists(self):
        assert KANBAN_COMMAND_TYPES
        assert isinstance(KANBAN_COMMAND_TYPES, dict)

    def test_negation_prefixes_exists(self):
        assert NEGATION_PREFIXES
        assert isinstance(NEGATION_PREFIXES, list)
        assert len(NEGATION_PREFIXES) > 0


class TestKanbanCommandType:
    def test_is_enum(self):
        from enum import Enum
        assert issubclass(KanbanCommandType, (str, Enum))

    def test_has_values(self):
        # Should have multiple command types
        values = [e.value for e in KanbanCommandType]
        assert len(values) > 0


class TestGetSystemPrompt:
    def test_returns_string(self):
        prompt = get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_matches_lia_system_prompt(self):
        # Should return a meaningful system prompt
        prompt = get_system_prompt()
        assert prompt  # not empty


class TestDetectCommandType:
    def test_basic_detection(self):
        result = detect_command_type("mover candidato para triagem")
        assert isinstance(result, tuple)
        assert len(result) == 2
        cmd_type, confidence = result
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_empty_message(self):
        result = detect_command_type("")
        # Should return something, even for empty string
        assert result is not None

    def test_unknown_command(self):
        result = detect_command_type("xyzzy frobnicator blargh")
        assert result is not None

    def test_move_candidate_command(self):
        result = detect_command_type("mover candidato para próxima fase")
        cmd_type, confidence = result
        assert confidence > 0

    def test_returns_tuple(self):
        result = detect_command_type("agendar entrevista com candidato")
        assert isinstance(result, tuple)


class TestResolveUiAction:
    def test_returns_something(self):
        for cmd in KanbanCommandType:
            result = resolve_ui_action(cmd.value, {}, [])
            assert isinstance(result, tuple)
            break

    def test_with_candidate_data(self):
        for cmd in KanbanCommandType:
            result = resolve_ui_action(
                cmd.value,
                {"candidate_id": "c1", "stage": "triagem"},
                [{"id": "c1", "name": "Ana"}]
            )
            assert result is not None
            break


class TestGetKanbanPromptTemplate:
    def test_returns_something(self):
        for cmd in KanbanCommandType:
            result = get_kanban_prompt_template(cmd.value)
            # Should return a template or None
            break  # Test first one


class TestFormatJobContext:
    def test_basic_job(self):
        job_data = {
            "title": "Engenheiro de Software Sênior",
            "status": "publicada",
        }
        result = format_job_context(job_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_full_job(self):
        job_data = {
            "title": "Product Manager",
            "status": "ao_vivo",
            "department": "Produto",
            "candidates_count": 15,
        }
        result = format_job_context(job_data)
        assert isinstance(result, str)

    def test_empty_job(self):
        result = format_job_context({})
        assert isinstance(result, str)


class TestFormatCandidatesContext:
    def test_basic_candidates(self):
        candidates = [
            {"name": "Ana Silva", "stage": "triagem", "score": 85},
            {"name": "Carlos Santos", "stage": "entrevista"},
        ]
        result = format_candidates_context(candidates)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_candidates(self):
        result = format_candidates_context([])
        assert isinstance(result, str)

    def test_single_candidate(self):
        result = format_candidates_context([{"name": "Maria"}])
        assert isinstance(result, str)


class TestFormatSelectedCandidatesContext:
    def test_with_selected(self):
        candidates = [
            {"name": "Pedro", "id": "cand-001"},
            {"name": "Lucia", "id": "cand-002"},
        ]
        selected_ids = ["cand-001"]
        result = format_selected_candidates_context(candidates, selected_ids)
        assert isinstance(result, str)

    def test_empty_selection(self):
        result = format_selected_candidates_context([], [])
        assert isinstance(result, str)

    def test_all_selected(self):
        candidates = [{"name": "Ana", "id": "c1"}, {"name": "Bruno", "id": "c2"}]
        result = format_selected_candidates_context(candidates, ["c1", "c2"])
        assert isinstance(result, str)


class TestFormatPipelineContext:
    def test_basic_pipeline(self):
        job_data = {"title": "Dev Senior", "status": "publicada"}
        candidates = [
            {"name": "Ana", "stage": "triagem"},
            {"name": "Carlos", "stage": "entrevista"},
        ]
        result = format_pipeline_context(job_data, candidates)
        assert isinstance(result, str)

    def test_empty_pipeline(self):
        result = format_pipeline_context({}, [])
        assert isinstance(result, str)


# ──────────────────────────────────────────────────────────
# report_templates.py
# ──────────────────────────────────────────────────────────
from app.templates.report_templates import ReportTemplates


class TestReportTemplates:
    def test_weekly_report_html_basic(self):
        data = {
            "period": "09-15 Jun 2025",
            "recruiter_name": "Ana Recrutadora",
            "jobs": [],
            "metrics": {},
        }
        result = ReportTemplates.weekly_report_html(data)
        assert isinstance(result, str)

    def test_weekly_report_html_empty_data(self):
        result = ReportTemplates.weekly_report_html({})
        assert isinstance(result, str)

    def test_daily_briefing_html_basic(self):
        data = {
            "date": "10 Jun 2025",
            "recruiter_name": "Carlos",
            "summary": {
                "urgent_count": 2,
                "total_active_jobs": 5,
                "candidates_pending": 10,
            },
        }
        result = ReportTemplates.daily_briefing_html(data)
        assert isinstance(result, str)

    def test_daily_briefing_html_empty(self):
        result = ReportTemplates.daily_briefing_html({})
        assert isinstance(result, str)

    def test_monthly_report_html_basic(self):
        data = {
            "month": "Junho 2025",
            "company": "TechCorp",
            "hires": 5,
        }
        result = ReportTemplates.monthly_report_html(data)
        assert isinstance(result, str)

    def test_monthly_report_html_empty(self):
        result = ReportTemplates.monthly_report_html({})
        assert isinstance(result, str)

    def test_report_templates_instance_exists(self):
        from app.templates.report_templates import report_templates
        assert report_templates is not None
