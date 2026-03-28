"""
Backwards-compatibility shim.
Real implementation moved to libs/utils (lia_utils.skill_classifier).
"""
from lia_utils.skill_classifier import (  # noqa: F401
    SOFT_SKILLS,
    normalize_skill,
    classify_skills,
)
