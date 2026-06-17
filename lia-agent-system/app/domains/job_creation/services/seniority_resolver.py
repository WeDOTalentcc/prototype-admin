"""
Seniority Resolver — F4 of WSI methodology.

100% deterministic. Uses 5 signals to resolve seniority:
1. Explicit seniority (user-provided)
2. Title keywords
3. JD analysis (responsibility complexity)
4. Salary range
5. Skills complexity

Based on test specs from lia-hardening/tests_coverage/test_seniority_resolver_unit.py
and seniority_utils.py patterns.
"""

import logging
import re
from typing import List, Optional

from app.domains.job_creation.schemas import SeniorityResult

logger = logging.getLogger(__name__)

# Canonical WSI seniority levels (ordered)
WSI_SENIORITY_LEVELS = ["estagiario", "junior", "pleno", "senior", "lead", "principal", "diretor"]

# Signal weights (sum = 1.0)
SIGNAL_WEIGHTS = {
    "explicit": 0.40,
    "title_keywords": 0.25,
    "jd_analysis": 0.15,
    "salary_range": 0.10,
    "skills_complexity": 0.10,
}

# Title keyword patterns
TITLE_SENIORITY_PATTERNS = {
    "estagiario": re.compile(r'\b(?:estagi[áa]ri[oa]|intern|trainee|aprendiz)\b', re.IGNORECASE),
    "junior": re.compile(r'\b(?:j[úu]nior|jr\.?|entry[- ]level|associad[oa])\b', re.IGNORECASE),
    "pleno": re.compile(r'\b(?:pleno|mid[- ]?level|intermediari[oa])\b', re.IGNORECASE),
    "senior": re.compile(r'\b(?:s[êe]nior|sr\.?|experienced|especialista)\b', re.IGNORECASE),
    "lead": re.compile(r'\b(?:lead|tech\s*lead|team\s*lead|l[íi]der\s*t[ée]cnic)\b', re.IGNORECASE),
    "principal": re.compile(r'\b(?:principal|staff|architect|arquitet[oa])\b', re.IGNORECASE),
    "diretor": re.compile(r'\b(?:diret[oa]r|director|vp|vice[- ]?president|head\s+of|c[- ]?level|cto|cpo)\b', re.IGNORECASE),
}

# Senior skill indicators (from test specs)
SENIOR_SKILL_INDICATORS = {
    "kubernetes", "machine learning", "deep learning", "system design",
    "distributed systems", "microservices architecture", "data engineering",
    "cloud architecture", "devops", "mlops", "platform engineering",
    "technical strategy", "team management", "budget planning",
}

JUNIOR_SKILL_INDICATORS = {
    "excel", "basic sql", "html", "css basics", "git basics",
    "data entry", "manual testing",
}

SENIORITY_DISPLAY_NAMES = {
    "estagiario": "Estagiario",
    "junior": "Junior",
    "pleno": "Pleno",
    "senior": "Senior",
    "lead": "Lead",
    "principal": "Principal / Staff",
    "diretor": "Diretor",
}


def normalize_seniority(raw: str) -> Optional[str]:
    """Normalize seniority string to canonical WSI level."""
    if not raw:
        return None

    lower = raw.lower().strip()

    # Direct matches
    direct_map = {
        "junior": "junior", "júnior": "junior", "jr": "junior", "jr.": "junior",
        "pleno": "pleno", "mid": "pleno", "mid-level": "pleno",
        "senior": "senior", "sênior": "senior", "sr": "senior", "sr.": "senior",
        "lead": "lead", "tech lead": "lead", "team lead": "lead",
        "principal": "principal", "staff": "principal",
        "diretor": "diretor", "director": "diretor", "head": "diretor",
        "estagiario": "estagiario", "estagiário": "estagiario",
        "intern": "estagiario", "trainee": "estagiario",
    }

    if lower in direct_map:
        return direct_map[lower]

    # Pattern matching
    for level, pattern in TITLE_SENIORITY_PATTERNS.items():
        if pattern.search(lower):
            return level

    return None


def _infer_from_title(title: str) -> tuple[Optional[str], float]:
    """Extract seniority from job title."""
    if not title:
        return None, 0.0

    for level, pattern in TITLE_SENIORITY_PATTERNS.items():
        if pattern.search(title):
            return level, 0.9
    return None, 0.0


def _infer_from_skills(skills: List[str]) -> tuple[Optional[str], float]:
    """Infer seniority from skill complexity."""
    if not skills:
        return None, 0.0

    skills_lower = {s.lower() for s in skills}

    senior_count = len(skills_lower & SENIOR_SKILL_INDICATORS)
    junior_count = len(skills_lower & JUNIOR_SKILL_INDICATORS)

    if senior_count >= 3:
        return "senior", 0.7
    if senior_count >= 1 and junior_count == 0:
        return "pleno", 0.5
    if junior_count >= 2:
        return "junior", 0.6

    return None, 0.0


def _level_to_index(level: str) -> int:
    """Convert seniority level to numeric index for averaging."""
    try:
        return WSI_SENIORITY_LEVELS.index(level)
    except ValueError:
        return 2  # default to pleno


def _index_to_level(idx: float) -> str:
    """Convert numeric index back to seniority level."""
    rounded = round(min(max(idx, 0), len(WSI_SENIORITY_LEVELS) - 1))
    return WSI_SENIORITY_LEVELS[rounded]


def resolve_seniority(
    explicit_seniority: Optional[str] = None,
    job_title: Optional[str] = None,
    job_description: Optional[str] = None,
    skills: Optional[List[str]] = None,
    salary_min: Optional[int] = None,
) -> SeniorityResult:
    """Resolve seniority using 5 signals. 100% deterministic.

    Args:
        explicit_seniority: User-provided seniority (highest weight)
        job_title: Job title for keyword extraction
        job_description: JD text for complexity analysis
        skills: List of required skills
        salary_min: Minimum salary for range inference

    Returns:
        SeniorityResult with final_level, confidence, signals_used
    """
    signals = []
    weighted_sum = 0.0
    total_weight = 0.0

    # Signal 1: Explicit seniority (weight: 0.40)
    normalized = normalize_seniority(explicit_seniority or "")
    if normalized:
        idx = _level_to_index(normalized)
        weighted_sum += idx * SIGNAL_WEIGHTS["explicit"]
        total_weight += SIGNAL_WEIGHTS["explicit"]
        signals.append({"signal": "explicit", "value": normalized, "weight": SIGNAL_WEIGHTS["explicit"]})

    # Signal 2: Title keywords (weight: 0.25)
    title_level, title_conf = _infer_from_title(job_title or "")
    if title_level:
        idx = _level_to_index(title_level)
        weighted_sum += idx * SIGNAL_WEIGHTS["title_keywords"]
        total_weight += SIGNAL_WEIGHTS["title_keywords"]
        signals.append({"signal": "title_keywords", "value": title_level, "weight": SIGNAL_WEIGHTS["title_keywords"]})

    # Signal 3: JD analysis (weight: 0.15) — simple heuristic
    if job_description:
        jd_len = len(job_description)
        if jd_len > 2000:
            jd_level = "senior"
        elif jd_len > 800:
            jd_level = "pleno"
        else:
            jd_level = "junior"
        idx = _level_to_index(jd_level)
        weighted_sum += idx * SIGNAL_WEIGHTS["jd_analysis"]
        total_weight += SIGNAL_WEIGHTS["jd_analysis"]
        signals.append({"signal": "jd_analysis", "value": jd_level, "weight": SIGNAL_WEIGHTS["jd_analysis"]})

    # Signal 4: Salary range (weight: 0.10)
    if salary_min and salary_min > 0:
        if salary_min >= 25000:
            sal_level = "lead"
        elif salary_min >= 15000:
            sal_level = "senior"
        elif salary_min >= 8000:
            sal_level = "pleno"
        else:
            sal_level = "junior"
        idx = _level_to_index(sal_level)
        weighted_sum += idx * SIGNAL_WEIGHTS["salary_range"]
        total_weight += SIGNAL_WEIGHTS["salary_range"]
        signals.append({"signal": "salary_range", "value": sal_level, "weight": SIGNAL_WEIGHTS["salary_range"]})

    # Signal 5: Skills complexity (weight: 0.10)
    skills_level, _ = _infer_from_skills(skills or [])
    if skills_level:
        idx = _level_to_index(skills_level)
        weighted_sum += idx * SIGNAL_WEIGHTS["skills_complexity"]
        total_weight += SIGNAL_WEIGHTS["skills_complexity"]
        signals.append({"signal": "skills_complexity", "value": skills_level, "weight": SIGNAL_WEIGHTS["skills_complexity"]})

    # Calculate final level
    if total_weight > 0:
        avg_idx = weighted_sum / total_weight
        final_level = _index_to_level(avg_idx)
        confidence = min(total_weight / 1.0, 1.0)  # max confidence when all signals present
    else:
        final_level = "pleno"  # default
        confidence = 0.0

    display_name = SENIORITY_DISPLAY_NAMES.get(final_level, final_level.title())

    logger.info(
        "[SeniorityResolver] final=%s (confidence=%.2f) | signals=%d",
        final_level, confidence, len(signals),
    )

    return SeniorityResult(
        final_level=final_level,
        confidence=confidence,
        signals_used=signals,
        display_name=display_name,
    )
