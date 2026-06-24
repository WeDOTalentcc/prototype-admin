"""Sensor: useJDEvaluation fetchTechSuggestions/fetchBehavSuggestions NÃO devem enviar company_id.
Bug original: company_id no body causava 422 (WeDoBaseModel extra=forbid).
"""
import re

def test_fetch_tech_suggestions_no_company_id_in_body():
    content = open(
        "/home/runner/workspace/plataforma-lia/src/components/wsi/jd-evaluation/useJDEvaluation.ts"
    ).read()
    # Localiza o body do fetchTechSuggestions
    match = re.search(r"fetchTechSuggestions.*?fetchBehavSuggestions", content, re.DOTALL)
    assert match, "fetchTechSuggestions não encontrado no arquivo"
    body = match.group(0)
    assert "company_id" not in body, (
        "company_id não deve aparecer no body de fetchTechSuggestions — "
        "viola REGRA 2: company_id vem do JWT, não do payload"
    )


def test_fetch_behav_suggestions_no_company_id_in_body():
    content = open(
        "/home/runner/workspace/plataforma-lia/src/components/wsi/jd-evaluation/useJDEvaluation.ts"
    ).read()
    match = re.search(r"fetchBehavSuggestions.*?fetchResponsibilities", content, re.DOTALL)
    assert match, "fetchBehavSuggestions não encontrado"
    body = match.group(0)
    assert "company_id" not in body, (
        "company_id não deve aparecer no body de fetchBehavSuggestions"
    )
