"""
TDD Red test: match_titles_in_message deve tolerar typo leve (1 char) em token.
Root cause P0-B auditado 2026-06-14:
  "diretor juridoc" → "juridoc" ≠ "juridico" (string exata)
  → overlap=1 → abaixo threshold → match falha → sticky_vacancy fallback → vaga errada.

Fix: fuzzy fallback em tokens de vaga (difflib ratio >= 0.82) quando token exato não casa.
"""
from app.shared.entity_resolver import match_titles_in_message


def test_typo_single_token_still_matches():
    """'diretor juridoc' (typo: juridoc vs juridico) deve ainda casar 'Diretor Juridico'."""
    items = [
        ("uuid-juridico", "Diretor(a) Juridico(a) (Chief Legal Officer)"),
        ("uuid-android", "Android Developer Pleno"),
        ("uuid-rh", "Gerente de RH Senior"),
    ]
    result = match_titles_in_message("quer que compare os dois melhores candidatos da vaga de diretor juridoc", items)
    ids = [r[0] for r in result]
    assert "uuid-juridico" in ids, (
        f"Esperado 'uuid-juridico' no resultado mas obteve: {result}\n"
        "Causa: typo 'juridoc' nao casou 'juridico' por exact token match."
    )


def test_no_false_positive_android_for_juridico_query():
    """'diretor juridico' nao deve trazer Android Developer Pleno no topo."""
    items = [
        ("uuid-juridico", "Diretor(a) Juridico(a) (Chief Legal Officer)"),
        ("uuid-android", "Android Developer Pleno"),
    ]
    result = match_titles_in_message("quero detalhes da vaga de diretor juridico", items)
    assert result, "Deve retornar pelo menos 1 resultado"
    assert result[0][0] == "uuid-juridico", (
        f"Primeiro resultado deve ser juridico mas foi: {result[0]}"
    )


def test_exact_match_still_works():
    """Match exato (sem typo) continua funcionando."""
    items = [
        ("uuid-android", "Android Developer Pleno"),
        ("uuid-juridico", "Diretor Juridico Senior"),
    ]
    result = match_titles_in_message("melhores candidatos da vaga de android developer pleno", items)
    ids = [r[0] for r in result]
    assert "uuid-android" in ids, f"Exact match deve funcionar: {result}"
