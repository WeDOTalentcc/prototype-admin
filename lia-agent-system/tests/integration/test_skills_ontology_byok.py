"""R-001 — eliminar bypass BYOK em skills_ontology_engine._load_embeddings.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-001 / R-001.

Fonte do bug (origin/main):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    result = genai.embed_content(...)

Fix esperado: usar a camada Choose Your AI (EmbeddingProviderFactory) em vez
de instanciar/configurar diretamente o SDK do Gemini.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "app" / "domains" / "talent_intelligence" / "services" / "skills_ontology_engine.py"


def _read_target_source() -> str:
    assert TARGET.exists(), f"Arquivo alvo nao encontrado: {TARGET}"
    return TARGET.read_text(encoding="utf-8")


def test_skills_ontology_does_not_read_gemini_env_directly() -> None:
    """R-001: skills_ontology_engine NAO pode ler GEMINI_API_KEY/GOOGLE_API_KEY do os.environ.

    BYOK / Choose Your AI: chaves vivem na config do tenant via factory,
    nunca em os.environ.get() ad-hoc no codigo de dominio.
    """
    src = _read_target_source()
    assert 'os.environ.get("GEMINI_API_KEY")' not in src, (
        "R-001: skills_ontology_engine ainda le GEMINI_API_KEY direto do env. "
        "Use EmbeddingProviderFactory.get_default() ou get_provider_for_tenant()."
    )
    assert 'os.environ.get("GOOGLE_API_KEY")' not in src, (
        "R-001: skills_ontology_engine ainda le GOOGLE_API_KEY direto do env. "
        "Use a camada Choose Your AI (factory) em vez de env vars globais."
    )


def test_skills_ontology_does_not_import_google_generativeai() -> None:
    """R-001: skills_ontology_engine NAO pode importar google.generativeai.

    A allowlist de check_llm_imports.py / check_llm_factory_enforcement.py
    nao inclui esse arquivo. Imports diretos do SDK violam Choose Your AI.
    """
    src = _read_target_source()
    assert "import google.generativeai" not in src, (
        "R-001: import direto de google.generativeai detectado. "
        "Mova para app/shared/providers/embedding_gemini.py (allowlisted) "
        "e consuma via EmbeddingProviderFactory."
    )
    assert "from google.generativeai" not in src, (
        "R-001: import 'from google.generativeai ...' detectado. " "Use EmbeddingProviderFactory em vez de SDK direto."
    )


def test_skills_ontology_uses_embedding_factory() -> None:
    """R-001: skills_ontology_engine deve consumir EmbeddingProviderFactory.

    Pattern canonical (app/shared/providers/embedding_factory.py):
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory
        provider = EmbeddingProviderFactory.get_default()
        results = await provider.embed_batch(texts)
    """
    src = _read_target_source()
    uses_factory = "EmbeddingProviderFactory" in src
    uses_provider_for_tenant = "get_provider_for_tenant" in src
    assert uses_factory or uses_provider_for_tenant, (
        "R-001: skills_ontology_engine precisa consumir EmbeddingProviderFactory "
        "(ou get_provider_for_tenant para LLM) em vez do SDK direto. "
        "Veja app/shared/providers/embedding_factory.py para a API canonical."
    )


def test_skills_ontology_does_not_call_genai_configure() -> None:
    """R-001: NAO pode chamar genai.configure() — provider gerencia auth."""
    src = _read_target_source()
    assert (
        "genai.configure" not in src
    ), "R-001: genai.configure(...) detectado. Provider via factory ja gerencia auth tenant-aware."


def test_skills_ontology_does_not_call_genai_embed_content() -> None:
    """R-001: NAO pode chamar genai.embed_content() direto — use provider.embed_batch()."""
    src = _read_target_source()
    assert "genai.embed_content" not in src, (
        "R-001: genai.embed_content(...) detectado. "
        "Use provider.embed_batch(texts) via EmbeddingProviderFactory.get_default()."
    )
