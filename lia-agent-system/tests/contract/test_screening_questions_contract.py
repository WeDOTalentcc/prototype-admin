"""
Contract Tests: Company Screening Questions — P0-W1-07+08+09+10
================================================================
Verifica contratos de campo, categorias e endpoints da feature
"banco de perguntas padrão da empresa".

P0-W1-09: question_text é o campo canonical (não 'question')
P0-W1-10: categorias frontend (use-eligibility-templates.ts) são aceitas pelo backend
P0-W1-07: POST body inclui category + PUT existe para edições

Estes testes rodam sem rede/LLM — apenas validação estrutural.
"""
import pytest


# ── P0-W1-09: Field name contract ─────────────────────────────────────────

def test_screening_question_model_has_question_text_column():
    """
    P0-W1-09: O model CompanyScreeningQuestion usa question_text (não question).
    Garante que o DB e API são coerentes — o frontend serializa como question_text.
    """
    from lia_models.screening_question import CompanyScreeningQuestion
    col_names = [c.name for c in CompanyScreeningQuestion.__table__.columns]
    assert "question_text" in col_names, (
        "P0-W1-09: CompanyScreeningQuestion.question_text not found in table columns. "
        "Backend expects 'question_text', frontend serializes as 'question_text'. "
        "Fix: ensure column name is question_text, NOT question."
    )
    assert "question" not in col_names, (
        "P0-W1-09: Column 'question' found but should be 'question_text'. "
        "Remove 'question' column or rename to 'question_text'."
    )


def test_screening_question_create_schema_field_is_question_text():
    """
    P0-W1-09: ScreeningQuestionCreate schema deve ter question_text, não question.
    Garante que HTTP 422 não ocorre quando frontend envia question_text.
    """
    from pydantic import ValidationError
    # Importar do endpoint canonical
    import importlib
    mod = importlib.import_module("app.api.v1.screening_questions")
    ScreeningQuestionCreate = mod.ScreeningQuestionCreate

    # Deve aceitar question_text
    payload = ScreeningQuestionCreate(question_text="Qual sua disponibilidade?")
    assert payload.question_text == "Qual sua disponibilidade?"

    # Deve rejeitar campo 'question' (extra='forbid' via WeDoBaseModel)
    with pytest.raises((ValidationError, Exception)):
        ScreeningQuestionCreate(question="Qual sua disponibilidade?")  # type: ignore


# ── P0-W1-10: Categories contract ────────────────────────────────────────

def test_question_categories_includes_all_frontend_categories():
    """
    P0-W1-10: QUESTION_CATEGORIES deve incluir todas as categorias do frontend
    (QuestionCategory em use-eligibility-templates.ts):
      general, eligibility, availability, education, experience,
      languages, compensation, work_model, compliance, system_default
    """
    from lia_models.screening_question import QUESTION_CATEGORIES

    frontend_categories = {
        "general", "eligibility", "availability", "education", "experience",
        "languages", "compensation", "work_model", "compliance", "system_default",
    }

    missing = frontend_categories - set(QUESTION_CATEGORIES.keys())
    assert missing == set(), (
        f"P0-W1-10: Categorias faltando no backend QUESTION_CATEGORIES: {missing}. "
        f"→ Fix: adicionar cada categoria faltante em "
        f"lia-agent-system/libs/models/lia_models/screening_question.py QUESTION_CATEGORIES dict."
    )


def test_question_categories_includes_legacy_backend_categories():
    """
    P0-W1-10: Categorias legadas do backend devem ser mantidas para compatibilidade.
    """
    from lia_models.screening_question import QUESTION_CATEGORIES

    legacy_categories = {
        "availability", "salary", "work_model", "logistics",
        "legal", "experience", "language", "custom",
    }

    missing = legacy_categories - set(QUESTION_CATEGORIES.keys())
    assert missing == set(), (
        f"P0-W1-10: Categorias legadas removidas do backend: {missing}. "
        f"Essas categorias podem existir em dados legados no DB — não remover."
    )


def test_question_categories_has_language_and_languages_aliases():
    """
    P0-W1-10: Backend deve aceitar tanto 'language' (legado) quanto 'languages'
    (frontend use-eligibility-templates.ts usa 'languages' com 's').
    """
    from lia_models.screening_question import QUESTION_CATEGORIES
    assert "language" in QUESTION_CATEGORIES, (
        "P0-W1-10: 'language' (legado) removido — dados antigos no DB usam esse valor."
    )
    assert "languages" in QUESTION_CATEGORIES, (
        "P0-W1-10: 'languages' (frontend) não encontrado em QUESTION_CATEGORIES. "
        "→ Fix: adicionar 'languages' no dict. "
        "Frontend use-eligibility-templates.ts QuestionCategory inclui 'languages'."
    )


# ── P0-W1-07: POST body includes category ────────────────────────────────

def test_screening_question_create_schema_accepts_category():
    """
    P0-W1-07: ScreeningQuestionCreate deve aceitar campo 'category'.
    O frontend envia category no POST body após o fix P0-W1-07.
    """
    import importlib
    mod = importlib.import_module("app.api.v1.screening_questions")
    ScreeningQuestionCreate = mod.ScreeningQuestionCreate

    payload = ScreeningQuestionCreate(
        question_text="Qual sua disponibilidade?",
        category="availability",
    )
    assert payload.category == "availability"


def test_screening_question_create_schema_accepts_frontend_categories():
    """
    P0-W1-07+10: ScreeningQuestionCreate aceita qualquer categoria do frontend
    (campo category é str | None sem enum constraint — permite extensibilidade).
    """
    import importlib
    mod = importlib.import_module("app.api.v1.screening_questions")
    ScreeningQuestionCreate = mod.ScreeningQuestionCreate

    for cat in ["general", "eligibility", "languages", "compensation", "compliance", "education"]:
        payload = ScreeningQuestionCreate(question_text="Test", category=cat)
        assert payload.category == cat, f"category={cat} not accepted"


# ── P0-W1-08: companyQuestions carregado via API (smoke) ──────────────────

def test_categories_endpoint_returns_dict_with_all_frontend_categories():
    """
    P0-W1-08+10: GET /company/screening-questions/categories retorna estrutura
    que o frontend pode consumir para categorias dinâmicas.
    """
    import importlib
    mod = importlib.import_module("app.api.v1.screening_questions")
    CategoriesResponse = mod.CategoriesResponse

    from lia_models.screening_question import QUESTION_CATEGORIES, QUESTION_TYPES

    response = CategoriesResponse(categories=QUESTION_CATEGORIES, types=QUESTION_TYPES)
    assert isinstance(response.categories, dict)
    assert len(response.categories) >= 8, "Deve ter pelo menos 8 categorias"

    # Todas as categorias do frontend devem estar presentes
    frontend_required = ["general", "eligibility", "languages", "compensation", "compliance", "education"]
    for cat in frontend_required:
        assert cat in response.categories, (
            f"P0-W1-10: Categoria '{cat}' não encontrada no endpoint /categories. "
            f"Frontend precisa desta categoria para renderização correta."
        )
