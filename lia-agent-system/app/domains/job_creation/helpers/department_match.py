"""Department fuzzy matching — extracted from nodes/intake.py (Fase 8 A1).

Pure functions: match a job title against the tenants real department list.
Used by both intake_node (graph) and wizard_service_tools (orchestrator).
"""
import re
import unicodedata
from difflib import SequenceMatcher

_SENIORITY_TOKENS = {
    "diretor", "diretora", "diretoria", "gerente", "coordenador", "coordenadora",
    "analista", "assistente", "estagiario", "estagiaria", "junior", "pleno",
    "senior", "especialista", "head", "lead", "supervisor", "supervisora",
    "chefe", "presidente", "tecnico", "tecnica", "auxiliar", "trainee",
    "vp", "ceo", "cto", "cfo", "coo", "cmo",
}
_DEPT_STOPWORDS = {"de", "da", "do", "e", "das", "dos"}


def _norm_txt(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def _dept_tokens(value: str, *, drop_seniority: bool = False) -> list:
    toks = [
        t for t in re.split(r"[^a-z0-9]+", _norm_txt(value))
        if len(t) >= 3 and t not in _DEPT_STOPWORDS
    ]
    if drop_seniority:
        toks = [t for t in toks if t not in _SENIORITY_TOKENS]
    return toks


def _tok_sim(a: str, b: str) -> float:
    if a == b:
        return 1.0
    n = min(len(a), len(b))
    if n >= 4:
        cp = 0
        for x, y in zip(a, b):
            if x == y:
                cp += 1
            else:
                break
        if cp >= 4:
            return 0.85
    return SequenceMatcher(None, a, b).ratio()


def match_department(title, dept_names, threshold: float = 0.8):
    """Match job title against tenant department names.

    Returns the department name (original) with the best match above threshold,
    or None. Never invents a department the tenant does not have.
    """
    if not title or not dept_names:
        return None
    title_toks = _dept_tokens(title, drop_seniority=True)
    if not title_toks:
        return None
    best, best_score = None, 0.0
    for name in dept_names:
        dtoks = _dept_tokens(name)
        if not dtoks:
            continue
        score = max(
            (_tok_sim(dt, tt) for dt in dtoks for tt in title_toks),
            default=0.0,
        )
        if score > best_score:
            best, best_score = name, score
    return best if best_score >= threshold else None
