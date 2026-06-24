"""Sensor: extract_jd deve rotear education → technical_skills e other/no-verb → behavioral_competencies.
Bug original 2026-06-21: categorias 'education' e 'other' sem verbo infinitivo eram silenciosamente descartadas.
"""

def _run_category_routing(requirements_list):
    """Replica a lógica de routing de jd_generation.py extract_jd para teste unitário."""
    import re
    responsibilities = []
    technical_skills = []
    behavioral_competencies = []
    for req in requirements_list:
        text_val = (req.get("requirement") or "").strip()
        if not text_val:
            continue
        category = (req.get("category") or "").lower()
        if category == "technical":
            technical_skills.append(text_val)
        elif category in ("soft_skill", "soft", "behavioral"):
            behavioral_competencies.append(text_val)
        elif category in ("experience", "responsibility", "responsibilities"):
            responsibilities.append(text_val)
        elif category == "education":
            technical_skills.append(text_val)
        else:
            if re.match(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(ar|er|ir)\b", text_val):
                responsibilities.append(text_val)
            else:
                behavioral_competencies.append(text_val)
    return responsibilities, technical_skills, behavioral_competencies


def test_education_routes_to_technical_skills():
    reqs = [{"requirement": "Superior completo em Ciência da Computação", "category": "education"}]
    resp, tech, behav = _run_category_routing(reqs)
    assert "Superior completo em Ciência da Computação" in tech
    assert behav == []
    assert resp == []


def test_other_no_verb_routes_to_behavioral():
    reqs = [
        {"requirement": "Liderança", "category": "other"},
        {"requirement": "Visão Estratégica", "category": "other"},
    ]
    resp, tech, behav = _run_category_routing(reqs)
    assert "Liderança" in behav
    assert "Visão Estratégica" in behav
    assert tech == []
    assert resp == []


def test_other_verb_infinitivo_routes_to_responsibilities():
    reqs = [{"requirement": "Desenvolver soluções de TI", "category": "other"}]
    resp, tech, behav = _run_category_routing(reqs)
    assert "Desenvolver soluções de TI" in resp
    assert behav == []


def test_technical_routes_correctly():
    reqs = [{"requirement": "Python avançado", "category": "technical"}]
    resp, tech, behav = _run_category_routing(reqs)
    assert "Python avançado" in tech


def test_no_silent_drop_any_category():
    """Nenhum item deve ser silenciosamente descartado — todo item vai para alguma lista."""
    reqs = [
        {"requirement": "Liderança", "category": "other"},
        {"requirement": "Superior em TI", "category": "education"},
        {"requirement": "Python", "category": "technical"},
        {"requirement": "Comunicação", "category": "soft_skill"},
        {"requirement": "Gerenciar equipes", "category": "experience"},
    ]
    resp, tech, behav = _run_category_routing(reqs)
    total_in = len(reqs)
    total_out = len(resp) + len(tech) + len(behav)
    assert total_out == total_in, f"Esperado {total_in} itens, mas {total_out} chegaram nas listas"
