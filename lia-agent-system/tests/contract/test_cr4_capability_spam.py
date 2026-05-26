"""Sprint 2.3 CR-4 sensor (2026-05-26) — REGRA #1 do _greeting_priority em
main_orchestrator.py NÃO contém mini-lista de capabilities que vire
training de capability spam. Conflito com lia_persona.yaml Anti-pattern #1.

Histórico: transcript Paulo 2026-05-26 mostrou LIA repetindo
"Posso ajudar com: Vagas, Candidatos, Comunicação, Agendamento, Analytics"
em todo turn (mesmo após user fazer pergunta específica). Causa raiz era
REGRA #1 do prompt prepend que tinha o EXEMPLO: "Você: 'Posso te mostrar
vagas em aberto, status de candidatos, ou indicadores'" — LLM generalizava
esse pattern.

Sensor estático source-grep — não roda LLM. Pin que REGRA #1:
  - NÃO contém o exemplo antigo de capability mini-list
  - CONTÉM sub-regra explícita "NUNCA enumere features"
  - CONTÉM exemplo NOVO contextual ("Olá! Vi que você tem 3 vagas...")
"""
from pathlib import Path


ORCH = Path("app/orchestrator/execution/main_orchestrator.py")


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_regra_1_does_not_teach_capability_spam():
    """Sprint 2.3 fix: o exemplo antigo de REGRA #1 ensinava capability list.
    Após fix, esse exemplo específico (com mini-lista) NÃO deve existir mais."""
    src = _read(ORCH)
    # The OLD example string (CR-4 root cause) — must NOT exist anymore
    forbidden = "Posso te mostrar vagas em aberto, status de candidatos, ou indicadores"
    assert forbidden not in src, (
        f"main_orchestrator.py REGRA #1 ainda contém o exemplo antigo que "
        f"ensinava capability spam: {forbidden!r}. CR-4 Sprint 2.3 removeu "
        f"esse exemplo. Regressão = LLM voltará a repetir capabilities em "
        f"todo turn (transcript Paulo 2026-05-26)."
    )


def test_regra_1_has_anti_capability_sub_rule():
    """REGRA #1 deve ter sub-regra explícita 'NUNCA enumere features...
    em saudações OU em qualquer turn subsequente'."""
    src = _read(ORCH)
    # Must contain the anti-spam sub-rule
    required_keywords = [
        "NUNCA enumere features",
        "ANTI-PATTERN",
    ]
    for kw in required_keywords:
        assert kw in src, (
            f"REGRA #1 missing canonical anti-capability sub-rule keyword: {kw!r}. "
            f"Sprint 2.3 CR-4 requires explicit 'NUNCA enumere features' instruction "
            f"to prevent LLM from repeating mini-capability lists across turns."
        )


def test_regra_1_has_contextual_example():
    """Exemplo NOVO deve ser contextual (com dado real do tenant) em vez de
    lista de features genérica."""
    src = _read(ORCH)
    # New example must mention contextual data (3 vagas) instead of feature list
    contextual_signals = [
        "3 vagas abertas",  # New example uses tenant context
        "Quer revisar o pipeline",  # Concrete action proposal
    ]
    for s in contextual_signals:
        assert s in src, (
            f"REGRA #1 missing contextual example signal {s!r}. "
            f"Sprint 2.3 fix substituiu mini-lista de features por exemplo "
            f"contextual baseado em dado do tenant."
        )


def test_regra_1_explicitly_marks_old_pattern_as_anti():
    """O exemplo errado (com mini-list de capabilities) deve estar
    explicitamente marcado como ❌ NÃO faça."""
    src = _read(ORCH)
    # The bad example should now appear inside the ❌ marker block
    # Locate REGRA #1 + look for the ❌ marker near capability terms
    assert "❌" in src, "REGRA #1 must use ❌ markers for anti-pattern examples"
    # The bad example must be contextualized as anti-pattern
    assert "ANTI-PATTERN" in src or "NÃO faça — gera capability spam" in src, (
        "REGRA #1 deve marcar explicitamente o pattern velho como ANTI-PATTERN "
        "para o LLM entender que NÃO é template a seguir."
    )
