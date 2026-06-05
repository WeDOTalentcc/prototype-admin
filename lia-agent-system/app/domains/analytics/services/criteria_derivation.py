"""
Derivação + avaliação determinística da matriz de qualificação do candidato.

Produtor PURO (sem DB, sem LLM, sem I/O) que compara um candidato contra
critérios vindos de:
- uma VAGA (`derive_from_job`) → agrupados em must_have / preferred, e
- filtros de BUSCA (`derive_from_search`) → lista plana (decisão Paulo v1).

Avaliação determinística cobre critérios estruturados (skills, senioridade,
localização, idiomas, anos de experiência, título). Critérios que exigem
julgamento fuzzy (comportamental; eligibility sem respostas registradas;
texto livre da busca) retornam `status='unknown'` com `provenance='none'` —
NUNCA fabricados (CLAUDE.md REGRA 4 + proveniência honesta). Um passo opcional
de LLM (fora deste módulo) pode resolver os 'unknown' depois.

Entradas são dicts simples para testabilidade sem ORM; o service adapta
JobVacancy/Candidate → dict antes de chamar.
"""
from __future__ import annotations

import unicodedata
from typing import Any

from app.schemas.qualification_matrix import (
    QualificationCriterion,
    QualificationMatrix,
)

_SENIORITY_ORDER = {
    "estagio": 0,
    "estagiario": 0,
    "trainee": 0,
    "junior": 1,
    "pleno": 2,
    "senior": 3,
    "especialista": 4,
    "lead": 4,
    "principal": 5,
    "staff": 5,
    "gerente": 5,
    "diretor": 6,
}


def _norm(text: Any) -> str:
    """lowercase + sem acentos + strip, para comparação resiliente."""
    if text is None:
        return ""
    s = str(text).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _seniority_rank(level: Any) -> int | None:
    n = _norm(level)
    for key, rank in _SENIORITY_ORDER.items():
        if key in n:
            return rank
    return None


def _candidate_skills(candidate: dict) -> list[str]:
    skills = candidate.get("technical_skills") or candidate.get("skills") or []
    if isinstance(skills, str):
        skills = [skills]
    return [s for s in skills if s]


def _candidate_languages(candidate: dict) -> list[str]:
    langs = candidate.get("languages") or []
    out: list[str] = []
    for item in langs if isinstance(langs, list) else []:
        if isinstance(item, dict):
            out.append(str(item.get("language") or item.get("name") or ""))
        elif item:
            out.append(str(item))
    return [x for x in out if x]


def _candidate_location(candidate: dict) -> str:
    parts = [
        candidate.get("location_city"),
        candidate.get("location_state"),
        candidate.get("location_country"),
    ]
    return _norm(", ".join(p for p in parts if p))


# ---- Avaliadores determinísticos (retornam dict de campos do critério) ----

def _eval_skill(skill: str, cand_skills_norm: set[str], cand_skills_raw: list[str]) -> dict:
    sk = _norm(skill)
    found = any(sk == c or sk in c or c in sk for c in cand_skills_norm)
    if found:
        return {
            "status": "met",
            "provenance": "resume",
            "confidence": 1.0,
            "explanation": f"Skill '{skill}' presente no currículo.",
        }
    return {
        "status": "not_met",
        "provenance": "resume",
        "confidence": 1.0,
        "explanation": f"Skill '{skill}' não mencionada no currículo.",
    }


def _eval_seniority(required: str, candidate: dict) -> dict:
    req_rank = _seniority_rank(required)
    cand_rank = _seniority_rank(candidate.get("seniority_level"))
    if req_rank is None or cand_rank is None:
        return {
            "status": "unknown",
            "provenance": "none",
            "confidence": 0.0,
            "explanation": f"Senioridade '{required}' não pôde ser comparada.",
        }
    if cand_rank >= req_rank:
        return {
            "status": "met",
            "provenance": "profile",
            "confidence": 1.0,
            "explanation": f"Senioridade do candidato atende '{required}'.",
        }
    if cand_rank == req_rank - 1:
        return {
            "status": "partial",
            "provenance": "profile",
            "confidence": 0.6,
            "explanation": f"Senioridade do candidato está um nível abaixo de '{required}'.",
        }
    return {
        "status": "not_met",
        "provenance": "profile",
        "confidence": 1.0,
        "explanation": f"Senioridade do candidato abaixo de '{required}'.",
    }


def _eval_location(required_locs: list[str], candidate: dict) -> dict:
    cand_loc = _candidate_location(candidate)
    if not cand_loc:
        return {
            "status": "unknown",
            "provenance": "none",
            "confidence": 0.0,
            "explanation": "Localização do candidato não informada.",
        }
    for loc in required_locs:
        nloc = _norm(loc)
        if nloc and (nloc in cand_loc or cand_loc in nloc):
            return {
                "status": "met",
                "provenance": "profile",
                "confidence": 1.0,
                "explanation": f"Localização compatível com '{loc}'.",
            }
    return {
        "status": "not_met",
        "provenance": "profile",
        "confidence": 1.0,
        "explanation": "Localização do candidato fora do critério.",
    }


def _eval_language(lang: str, candidate: dict) -> dict:
    cand_langs = {_norm(x) for x in _candidate_languages(candidate)}
    nl = _norm(lang)
    if any(nl == c or nl in c or c in nl for c in cand_langs):
        return {
            "status": "met",
            "provenance": "resume",
            "confidence": 1.0,
            "explanation": f"Idioma '{lang}' presente no perfil.",
        }
    return {
        "status": "not_met",
        "provenance": "resume",
        "confidence": 1.0,
        "explanation": f"Idioma '{lang}' não informado no perfil.",
    }


def _eval_min_years(min_years: int, candidate: dict) -> dict:
    years = candidate.get("years_of_experience")
    if years is None:
        return {
            "status": "unknown",
            "provenance": "none",
            "confidence": 0.0,
            "explanation": "Anos de experiência não informados.",
        }
    if years >= min_years:
        return {
            "status": "met",
            "provenance": "resume",
            "confidence": 1.0,
            "explanation": f"{years} anos de experiência (mínimo {min_years}).",
        }
    return {
        "status": "not_met",
        "provenance": "resume",
        "confidence": 1.0,
        "explanation": f"{years} anos de experiência, abaixo do mínimo {min_years}.",
    }


def _eval_title(title: str, candidate: dict) -> dict:
    cand_title = _norm(candidate.get("current_title"))
    nt = _norm(title)
    if not cand_title:
        return {
            "status": "unknown",
            "provenance": "none",
            "confidence": 0.0,
            "explanation": "Cargo atual do candidato não informado.",
        }
    # match por tokens significativos do título buscado
    tokens = [t for t in nt.split() if len(t) > 2]
    if tokens and all(t in cand_title for t in tokens):
        return {
            "status": "met",
            "provenance": "profile",
            "confidence": 0.9,
            "explanation": f"Cargo atual compatível com '{title}'.",
        }
    if tokens and any(t in cand_title for t in tokens):
        return {
            "status": "partial",
            "provenance": "profile",
            "confidence": 0.5,
            "explanation": f"Cargo atual parcialmente relacionado a '{title}'.",
        }
    return {
        "status": "not_met",
        "provenance": "profile",
        "confidence": 0.8,
        "explanation": f"Cargo atual não corresponde a '{title}'.",
    }


def _crit(id_: str, label: str, group: str, ev: dict, source_ref: str | None = None) -> QualificationCriterion:
    return QualificationCriterion(
        id=id_,
        label=label,
        group=group,  # type: ignore[arg-type]
        status=ev["status"],
        explanation=ev.get("explanation", ""),
        provenance=ev.get("provenance", "none"),
        confidence=ev.get("confidence", 0.0),
        source_ref=source_ref,
    )


# ---------------------------- BUSCA (flat) ----------------------------

def derive_from_search(filters: dict, candidate: dict) -> QualificationMatrix:
    """
    Lista plana de critérios a partir dos filtros de busca (decisão Paulo v1:
    sem split must-have/preferred — filtros de busca são todos opcionais hoje).
    """
    candidate = candidate or {}
    cand_skills_raw = _candidate_skills(candidate)
    cand_skills_norm = {_norm(s) for s in cand_skills_raw}
    criteria: list[QualificationCriterion] = []

    skills = list(filters.get("required_skills") or []) + list(filters.get("preferred_skills") or [])
    # FE SearchFilters: skills.skillItems
    sk_block = filters.get("skills")
    if isinstance(sk_block, dict):
        skills += [s.get("name") if isinstance(s, dict) else s for s in (sk_block.get("skillItems") or [])]
    for s in [x for x in skills if x]:
        criteria.append(_crit(f"skill:{_norm(s)}", str(s), "criteria",
                              _eval_skill(str(s), cand_skills_norm, cand_skills_raw)))

    for lvl in (filters.get("seniority_levels") or filters.get("levels") or []):
        if lvl:
            criteria.append(_crit(f"seniority:{_norm(lvl)}", f"Senioridade: {lvl}", "criteria",
                                  _eval_seniority(str(lvl), candidate)))

    locs = list(filters.get("locations") or [])
    if locs:
        criteria.append(_crit("location", f"Localização: {', '.join(map(str, locs))}", "criteria",
                              _eval_location([str(x) for x in locs], candidate)))

    min_years = filters.get("min_years_experience")
    if isinstance(min_years, int) and min_years > 0:
        criteria.append(_crit("min_years", f"Mínimo {min_years} anos de experiência", "criteria",
                              _eval_min_years(min_years, candidate)))

    for title in (filters.get("titles") or []):
        if title:
            criteria.append(_crit(f"title:{_norm(title)}", f"Cargo: {title}", "criteria",
                                  _eval_title(str(title), candidate)))

    lang_block = filters.get("languages")
    lang_list = lang_block.get("languages") if isinstance(lang_block, dict) else lang_block
    for lang in (lang_list or []):
        name = lang.get("name") if isinstance(lang, dict) else lang
        if name:
            criteria.append(_crit(f"lang:{_norm(name)}", f"Idioma: {name}", "criteria",
                                  _eval_language(str(name), candidate)))

    return QualificationMatrix.build(mode="flat", criteria=criteria, generated_with_llm=False)


# ---------------------------- VAGA (grouped) ----------------------------

def derive_from_job(
    job: dict,
    candidate: dict,
    eligibility: list[dict] | None = None,
) -> QualificationMatrix:
    """
    Critérios agrupados em must_have / preferred a partir da vaga.

    must_have: eligibility eliminatória + technical_requirements[required] +
               languages[required] + behavioral 'Essencial' + requirements (legacy).
    preferred: demais skills/requirements + behavioral não-essencial.
    Avaliação determinística onde há sinal estruturado; senão 'unknown'.
    """
    job = job or {}
    candidate = candidate or {}
    cand_skills_raw = _candidate_skills(candidate)
    cand_skills_norm = {_norm(s) for s in cand_skills_raw}
    criteria: list[QualificationCriterion] = []

    # Eligibility eliminatória → must_have. Avalia se houver resposta registrada.
    for item in (eligibility or []):
        if not item.get("is_eliminatory"):
            continue
        label = item.get("question") or item.get("label") or "Critério eliminatório"
        ans = item.get("candidate_answer")
        expected = item.get("expected_answer")
        if ans is None:
            ev = {"status": "unknown", "provenance": "none", "confidence": 0.0,
                  "explanation": "Resposta de elegibilidade ainda não coletada."}
        elif expected is not None and _norm(ans) == _norm(expected):
            ev = {"status": "met", "provenance": "eligibility", "confidence": 1.0,
                  "explanation": "Resposta atende ao critério eliminatório."}
        else:
            ev = {"status": "not_met", "provenance": "eligibility", "confidence": 1.0,
                  "explanation": "Resposta não atende ao critério eliminatório."}
        criteria.append(_crit(f"elig:{item.get('id', _norm(label))}", str(label), "must_have", ev))

    # technical_requirements: required → must_have, else preferred
    for tr in (job.get("technical_requirements") or []):
        if not isinstance(tr, dict):
            continue
        tech = tr.get("technology") or tr.get("name")
        if not tech:
            continue
        group = "must_have" if tr.get("required") else "preferred"
        criteria.append(_crit(f"tech:{_norm(tech)}", str(tech), group,
                              _eval_skill(str(tech), cand_skills_norm, cand_skills_raw)))

    # languages: required → must_have, else preferred
    for lg in (job.get("languages") or []):
        if not isinstance(lg, dict):
            continue
        name = lg.get("language") or lg.get("name")
        if not name:
            continue
        group = "must_have" if lg.get("required") else "preferred"
        criteria.append(_crit(f"lang:{_norm(name)}", f"Idioma: {name}", group,
                              _eval_language(str(name), candidate)))

    # behavioral_competencies → must_have se 'Essencial', senão preferred (fuzzy → unknown)
    for bc in (job.get("behavioral_competencies") or []):
        if not isinstance(bc, dict):
            continue
        comp = bc.get("competency") or bc.get("name")
        if not comp:
            continue
        essential = _norm(bc.get("weight")) == "essencial"
        group = "must_have" if essential else "preferred"
        ev = {"status": "unknown", "provenance": "none", "confidence": 0.0,
              "explanation": "Competência comportamental requer avaliação (triagem/WSI)."}
        criteria.append(_crit(f"behav:{_norm(comp)}", str(comp), group, ev))

    # requirements (legacy ARRAY de strings) → must_have, texto livre → unknown
    for req in (job.get("requirements") or []):
        if not req:
            continue
        ev = {"status": "unknown", "provenance": "none", "confidence": 0.0,
              "explanation": "Requisito textual — avaliação fuzzy pendente."}
        criteria.append(_crit(f"req:{_norm(req)[:40]}", str(req), "must_have", ev))

    return QualificationMatrix.build(mode="grouped", criteria=criteria, generated_with_llm=False)
