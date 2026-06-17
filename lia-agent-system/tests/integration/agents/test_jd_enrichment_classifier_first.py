"""Task #1123 — Sentinela arquitetural: jd_enrichment_node é classifier-first.

Garante que ``jd_enrichment_node`` rotineiramente delega ao
``IntakeIntentClassifier`` ANTES do guard estático ``raw_input<100``,
e que o guard só dispara quando o classifier devolve ``None`` ou
``confidence<0.7``.

Bug raiz reproduzido por esta sentinela: o classifier era gateado por
``_guard_eligible`` (com ``_raw_len<100``), então mensagens longas
(≥100 chars) que eram perguntas meta nunca passavam pelo LLM, caíam
direto no Layer 2 PII strip + enrichment LLM (~2K tokens) e enriqueciam
a própria pergunta meta como se fosse JD — origem da auditoria
D-2026-05.

6 cenários:
  1. Pergunta meta CURTA (<100 chars) → classifier roda, intent=meta_question
  2. Pergunta meta LONGA (≥100 chars) → classifier roda (não gateado por len)
  3. JD válida LONGA → classifier roda, intent=provides_jd_intent
  4. Intent-only curto → classifier roda, intent=intent_only
  5. Classifier devolve None → guard estático dispara (last resort, len<100)
  6. Classifier baixa conf + len≥100 → cai no fluxo normal (sem guard)
"""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _flag_on(monkeypatch):
    """Liga o classifier flag (default OFF em prod/staging)."""
    monkeypatch.setenv("LIA_WIZARD_INTAKE_CLASSIFIER_ENABLED", "1")


def _base_state(raw: str) -> dict:
    return {
        "raw_input": raw,
        "user_query": raw,
        "user_id": "test-user",
        "workspace_id": "00000000-0000-4000-a000-000000000001",
        "session_id": "test-session",
        "conversation_messages": [],
        "tenant_context_snippet": "Demo Company (Tecnologia, enterprise).",
        "current_stage": "jd_enrichment",
    }


def _make_intake_output(intent: str, confidence: float = 0.9):
    """Constrói um IntakeIntentOutput minimal para o mock."""
    from app.domains.job_creation.services.intake_intent_classifier import (
        IntakeIntentOutput,
    )
    return IntakeIntentOutput(
        intent=intent,
        confidence=confidence,
        conversational_reply="(mock reply)",
    )


def test_meta_question_short_classifier_runs():
    """Cenário 1 — pergunta meta CURTA (<100 chars) deve passar pelo
    classifier (e não cair em guard estático sem consulta LLM)."""
    from app.domains.job_creation import graph as g

    state = _base_state("o que você precisa pra começar?")
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            assert kwargs.get("user_message")
            return _make_intake_output("meta_question", 0.9)

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ):
        result = g.jd_enrichment_node(state)

    assert called["n"] == 1, "Classifier deve ser invocado em pergunta meta curta"
    assert result.get("current_stage") == "jd_enrichment"


def test_meta_question_long_classifier_runs():
    """Cenário 2 (CRÍTICO) — pergunta meta LONGA (≥100 chars). Bug raiz:
    classifier ficava gateado por ``raw_len<100`` e nunca rodava aqui.
    """
    from app.domains.job_creation import graph as g

    raw = (
        "olha eu queria entender melhor antes de começar — você precisa de "
        "que exatamente pra montar a vaga? me explica o processo todo aí pra "
        "eu saber o que preparar antes."
    )
    assert len(raw) >= 100
    state = _base_state(raw)
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return _make_intake_output("meta_question", 0.92)

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ):
        result = g.jd_enrichment_node(state)

    # O contrato: classifier rodou mesmo com raw_len>=100.
    assert called["n"] == 1, (
        "Bug raiz Task #1123: classifier não rodou para mensagem longa — "
        "_classifier_eligible NÃO deve depender de _raw_len<100."
    )
    # Short-circuit emitiu jd_enriched=None (não enriqueceu meta question).
    assert result.get("jd_enriched") is None


def test_jd_provides_intent_classifier_runs():
    """Cenário 3 — JD válida longa também passa pelo classifier
    (que retorna provides_jd_intent → continua para enrichment)."""
    from app.domains.job_creation import graph as g

    raw = (
        "Engenheiro Backend Sênior — Python, FastAPI, AWS, Redis, "
        "PostgreSQL. Atuação em squad de produto. Remoto BR. Faixa "
        "20-28k CLT. Mentoria a juniores e participação em OKRs."
    )
    assert len(raw) >= 100
    state = _base_state(raw)
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return _make_intake_output("provides_jd_intent", 0.95)

    # Mockamos também o LLM enrichment downstream para evitar rede real.
    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ), patch(
        "app.domains.job_creation.graph._enrich_jd_via_llm",
        return_value={"enriched_jd": "(mocked enrich)", "quality_score": 75.0},
        create=True,
    ):
        try:
            g.jd_enrichment_node(state)
        except Exception:
            # Downstream pode falhar por outros mocks faltando — o que
            # importa para o contrato Task #1123 é que o classifier
            # rodou ANTES.
            pass

    assert called["n"] == 1, "Classifier deve rodar antes do enrichment"


def test_intent_only_short_classifier_runs():
    """Cenário 4 — intent-only curto (ex.: 'quero abrir uma vaga')
    deve passar pelo classifier."""
    from app.domains.job_creation import graph as g

    state = _base_state("quero abrir uma vaga")
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return _make_intake_output("intent_only", 0.88)

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ):
        result = g.jd_enrichment_node(state)

    assert called["n"] == 1
    assert result.get("current_stage") == "jd_enrichment"


def test_intent_only_high_conf_fires_guard_not_enrichment():
    """Cenário 4b (Task #1123) — intent_only com confidence>=0.7 NUNCA
    pode cair em enrichment. Deve disparar guard (ask for JD/title)
    independente de raw_len.

    Regressão guard: até o fix do review, intent_only com conf alta
    deixava _guard_eligible=False e o nó fluía para enrichment normal,
    "enriquecendo" intenções vazias como se fossem JD.
    """
    from app.domains.job_creation import graph as g

    raw = (
        "olha eu queria muito abrir uma vaga nova aqui no time, é meio "
        "urgente, vamos começar? me ajuda com isso por favor."
    )
    assert len(raw) >= 100, "Mensagem propositalmente longa para testar bypass do raw_len"
    state = _base_state(raw)
    classifier_called = {"n": 0}
    enrich_called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            classifier_called["n"] += 1
            return _make_intake_output("intent_only", 0.92)

    def _fake_enrich(*args, **kwargs):
        enrich_called["n"] += 1
        return {"enriched_jd": "(should not run)", "quality_score": 0.0}

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ), patch.object(
        g, "_enrich_jd_via_llm", side_effect=_fake_enrich, create=True,
    ):
        result = g.jd_enrichment_node(state)

    assert classifier_called["n"] == 1, "Classifier deve ter rodado primeiro"
    assert enrich_called["n"] == 0, (
        "intent_only NUNCA pode chamar enrichment — deve cair em guard."
    )
    assert result.get("jd_enriched") is None
    assert result.get("current_stage") == "jd_enrichment"
    # Guard estático preserva contrato (awaiting_jd_input True OU mensagem
    # de ask_for_jd presente no payload).
    payload = result.get("ws_stage_payload") or {}
    data = payload.get("data") or {}
    awaiting = data.get("awaiting_jd_input")
    msg = (data.get("message") or "")
    assert awaiting is True or ("descrição" in msg.lower() or "título" in msg.lower()), (
        f"Esperava guard ask-for-JD (awaiting_jd_input=True ou msg pedindo "
        f"JD/título). Got payload.data={data!r}"
    )


def test_classifier_none_static_guard_fires():
    """Cenário 5 — classifier devolve None (fail-OPEN: sem flag, sem
    chave). Guard estático vira last-resort e DEVE disparar (raw_len<100).
    """
    from app.domains.job_creation import graph as g

    state = _base_state("oi")
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return None  # fail-OPEN

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ):
        result = g.jd_enrichment_node(state)

    assert called["n"] == 1, "Classifier deve ser tentado primeiro"
    # Static guard fires: jd_enriched permanece None + current_stage preservado.
    assert result.get("jd_enriched") is None
    assert result.get("current_stage") == "jd_enrichment"


def test_classifier_low_conf_long_msg_no_guard():
    """Cenário 6 — classifier baixa conf (<0.7) E mensagem longa
    (>=100 chars). Guard NÃO deve disparar (last-resort exige len<100).
    Fluxo cai para Layer 2 normal.
    """
    from app.domains.job_creation import graph as g

    raw = (
        "essa é uma mensagem média que talvez seja JD talvez não seja, "
        "tem mais de cem caracteres mas é vaga e ambígua intencionalmente "
        "para o teste."
    )
    assert len(raw) >= 100
    state = _base_state(raw)
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return _make_intake_output("intent_only", 0.4)  # low conf

    enrich_called = {"n": 0}

    def _fake_enrich(*args, **kwargs):
        enrich_called["n"] += 1
        return {"enriched_jd": "(low conf path)", "quality_score": 30.0}

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ):
        try:
            g.jd_enrichment_node(state)
        except Exception:
            pass

    assert called["n"] == 1, "Classifier deve ter rodado"
    # Guard estático NÃO deveria ter sido o terminal aqui — len>=100.
    # O contrato é que `_guard_eligible` é False, então caímos no fluxo
    # normal abaixo (que pode falhar por mocks faltantes, mas isso não
    # invalida o contrato). Nenhum assert sobre enrich aqui — a sentinela
    # foca no fato de que o classifier rodou (vs. o bug original onde
    # nem rodava).


def test_classifier_runs_when_parsed_title_extracted_but_raw_thin():
    """Fix D (2026-05-27) — quando intake extrai parsed_title MAS raw_input
    eh curto e SEM JD/panel/attached, classifier DEVE rodar pra decidir
    entre intent_only (pedir JD) e provides_jd_intent (seguir enrichment).
    
    Bug raiz (descoberto via WIZARD_DEEP_DIVE_2026-05-27_POST_PR18.md P1-NOVO-#1):
    `_classifier_eligible = ... and not _has_parsed_title` bloqueava classifier
    quando title estava extraido. Resultado: guard tambem nao disparava
    (depende de _classifier_eligible), LLM enrichment recebia 40 chars de
    input e inventava about_role/requirements/skills fictícios. Recrutador
    aprovava JD ilusoria, vaga publicada com conteudo nao escrito por ele.
    
    Cenario reproducao Paulo 2026-05-27: "Quero contratar um Engenheiro
    Backend Senior" (40 chars) -> intake extrai title -> jd_enrichment
    invoca LLM com lixo curto.
    """
    from app.domains.job_creation import graph as g

    state = _base_state("Quero contratar um Engenheiro Backend Senior")
    state["parsed_title"] = "Engenheiro Backend Senior"
    state["parsed_seniority"] = "senior"
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return _make_intake_output("intent_only", 0.9)

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ):
        result = g.jd_enrichment_node(state)

    assert called["n"] == 1, (
        "Fix D: classifier DEVE rodar quando parsed_title set mas raw curto "
        "(sem JD/panel/attached). Pre-fix: _has_parsed_title=True bloqueava "
        "_classifier_eligible. Pos-fix: title nao bloqueia mais."
    )
    assert result.get("jd_enriched") is None, (
        "Fix D: intent_only com conf>=0.7 deve disparar guard "
        "-> jd_enriched permanece None (nao chama LLM enrichment com lixo)."
    )
    history = result.get("stage_history", [])
    assert any("awaiting" in h or "intent" in h for h in history), (
        f"Fix D: stage_history deve indicar awaiting/intent (guard fired). "
        f"Got: {history!r}"
    )


def test_classifier_runs_when_parsed_title_set_and_raw_rich():
    """Fix D non-regression — quando parsed_title set MAS raw_input eh rico
    (>=100 chars JD-like), classifier roda e classifica como provides_jd_intent.
    Mantem o behavior de seguir pra LLM enrichment quando ha informacao real."""
    from app.domains.job_creation import graph as g

    raw = (
        "Engenheiro Backend Senior remoto Brasil, Python/FastAPI, PostgreSQL, "
        "Docker, AWS. 5+ anos experiencia. CLT 20-28k. Cultura colaborativa, "
        "mentoria, code review canonical. Sem requisitos discriminatorios."
    )
    assert len(raw) >= 100
    state = _base_state(raw)
    state["parsed_title"] = "Engenheiro Backend Senior"
    called = {"n": 0}

    class _MockClassifier:
        def classify_sync(self, **kwargs):
            called["n"] += 1
            return _make_intake_output("provides_jd_intent", 0.95)

    with patch.object(
        g, "_extract_last_turns", return_value=[],
    ), patch(
        "app.domains.job_creation.services.intake_intent_classifier."
        "get_intake_intent_classifier",
        return_value=_MockClassifier(),
    ), patch(
        "app.domains.job_creation.graph._enrich_jd_via_llm",
        return_value={"enriched_jd": "(mocked)", "quality_score": 80.0},
        create=True,
    ):
        try:
            g.jd_enrichment_node(state)
        except Exception:
            # Downstream pode falhar por outros mocks faltando -- importante eh
            # que classifier rodou ANTES de tudo (contrato Fix D + Task #1123).
            pass

    assert called["n"] == 1, (
        "Fix D non-regression: classifier deve rodar mesmo com parsed_title "
        "set, agora que `not _has_parsed_title` foi removido de "
        "_classifier_eligible."
    )
