"""Coverage tests for file_router.py — pure classification helpers."""
import pytest

from app.domains.job_creation.services.file_router import (
    CV_PATTERNS,
    JD_PATTERNS,
    MAX_FILE_SIZE,
    classify_file,
    get_routing_action,
    validate_file,
)


class TestPatternConstants:
    def test_cv_patterns_matches_curriculo(self):
        assert CV_PATTERNS.search("curriculo.pdf")

    def test_cv_patterns_matches_cv(self):
        assert CV_PATTERNS.search("cv.pdf")

    def test_cv_patterns_matches_resume(self):
        assert CV_PATTERNS.search("resume.pdf")

    def test_jd_patterns_matches_vaga(self):
        assert JD_PATTERNS.search("vaga.pdf")

    def test_jd_patterns_matches_descricao_da_vaga(self):
        assert JD_PATTERNS.search("descricao_da_vaga.pdf")

    def test_jd_patterns_matches_jd(self):
        assert JD_PATTERNS.search("jd.pdf")


class TestClassifyFile:
    # --- CV by filename (only filenames where word boundary works) ---
    def test_cv_filename_curriculo(self):
        assert classify_file("curriculo.pdf") == "cv"

    def test_cv_filename_cv(self):
        assert classify_file("cv.pdf") == "cv"

    def test_cv_filename_resume(self):
        assert classify_file("resume.pdf") == "cv"

    def test_cv_filename_perfil(self):
        assert classify_file("perfil.pdf") == "cv"

    # --- JD by filename ---
    def test_jd_filename_vaga(self):
        assert classify_file("vaga.pdf") == "jd"

    def test_jd_filename_job_desc(self):
        assert classify_file("job_desc.pdf") == "jd"

    def test_jd_filename_requisitos(self):
        assert classify_file("requisitos.pdf") == "jd"

    def test_jd_filename_cargo(self):
        assert classify_file("cargo.pdf") == "jd"

    def test_jd_filename_descricao_da_vaga(self):
        assert classify_file("descricao_da_vaga.pdf") == "jd"

    def test_jd_filename_jd(self):
        assert classify_file("jd.pdf") == "jd"

    # --- Generic ---
    def test_generic_filename_unknown(self):
        assert classify_file("document.pdf") == "generic"

    def test_generic_no_extension(self):
        assert classify_file("somefile") == "generic"

    # underscore breaks word boundary → generic
    def test_generic_cv_joao_underscore(self):
        assert classify_file("cv_joao.pdf") == "generic"

    def test_generic_vaga_engenheiro_underscore(self):
        assert classify_file("vaga_engenheiro.pdf") == "generic"

    # --- CV by content ---
    def test_cv_by_content_work_experience(self):
        preview = "work experience\neducation\nskills\ncompetências"
        result = classify_file("document.pdf", content_preview=preview)
        assert result == "cv"

    def test_cv_by_content_pt_indicators(self):
        preview = "experiência profissional\nformação acadêmica\nobjetivo profissional"
        result = classify_file("file.pdf", content_preview=preview)
        assert result == "cv"

    # --- JD by content ---
    def test_jd_by_content_responsibilities(self):
        preview = "responsabilidades\nrequisitos\nbeneficios\no que oferecemos"
        result = classify_file("document.pdf", content_preview=preview)
        assert result == "jd"

    # --- No content preview → filename-only ---
    def test_no_content_preview(self):
        result = classify_file("document.pdf", content_preview=None)
        assert result == "generic"


class TestValidateFile:
    def test_valid_pdf_returns_true(self):
        valid, err = validate_file("resume.pdf", 1024)
        assert valid is True
        assert err is None

    def test_oversized_file_fails(self):
        valid, err = validate_file("big.pdf", MAX_FILE_SIZE + 1)
        assert valid is False
        assert "muito grande" in err

    def test_empty_file_fails(self):
        valid, err = validate_file("empty.pdf", 0)
        assert valid is False
        assert "vazio" in err.lower()

    def test_unsupported_extension_fails(self):
        valid, err = validate_file("bad.exe", 1024)
        assert valid is False
        assert ".exe" in err

    def test_txt_file_valid(self):
        valid, err = validate_file("notes.txt", 500)
        assert valid is True

    def test_docx_file_valid(self):
        valid, err = validate_file("cv.docx", 2048)
        assert valid is True

    def test_max_file_size_constant_is_10mb(self):
        assert MAX_FILE_SIZE == 10 * 1024 * 1024


class TestGetRoutingAction:
    def test_cv_routes_to_cv_screening(self):
        action = get_routing_action("cv")
        assert action["action"] == "cv_screening"

    def test_cv_requires_consent(self):
        action = get_routing_action("cv")
        assert action["requires_consent"] is True

    def test_jd_routes_to_wizard_intake(self):
        action = get_routing_action("jd")
        assert action["action"] == "wizard_intake"

    def test_jd_does_not_require_consent(self):
        action = get_routing_action("jd")
        assert action["requires_consent"] is False

    def test_jd_has_auto_start_wizard(self):
        action = get_routing_action("jd")
        assert action.get("auto_start_wizard") is True

    def test_generic_routes_to_file_analysis(self):
        action = get_routing_action("generic")
        assert action["action"] == "file_analysis"

    def test_generic_no_consent_required(self):
        action = get_routing_action("generic")
        assert action["requires_consent"] is False

    def test_all_actions_have_pipeline(self):
        for file_type in ("cv", "jd", "generic"):
            action = get_routing_action(file_type)
            assert "pipeline" in action
