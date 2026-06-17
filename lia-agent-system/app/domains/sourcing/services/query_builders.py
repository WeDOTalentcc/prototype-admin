"""
Sourcing Query Builders - Utilities for boolean search and candidate matching.

Extracted from the legacy SourcingAgent (Sprint 5 migration).
Used by sourcing endpoints and the SourcingReActAgent tool registry.
"""
from typing import Any


class BooleanQueryBuilder:
    """
    Builder for advanced boolean search queries.
    Generates LinkedIn-style and database-compatible boolean strings.
    """

    @staticmethod
    def build_query(
        title: str | None = None,
        skills: list[str] | None = None,
        companies: list[str] | None = None,
        industries: list[str] | None = None,
        location: str | None = None,
        seniority: str | None = None,
        years_experience: int | None = None,
        exclude_terms: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Build boolean search queries for different platforms.

        Returns:
            Dict with 'linkedin', 'database', 'pearch', and 'raw_parts' query variants.
        """
        parts: list[str] = []
        linkedin_parts: list[str] = []

        if title:
            titles = title.split("/") if "/" in title else [title]
            title_or = " OR ".join([f'"{t.strip()}"' for t in titles])
            parts.append(f"({title_or})")
            linkedin_parts.append(f"({title_or})")

        if skills:
            primary_skills = skills[:5]
            skill_and = " AND ".join([f'"{s}"' for s in primary_skills])
            parts.append(f"({skill_and})")
            secondary_skills = skills[5:10] if len(skills) > 5 else []
            if secondary_skills:
                skill_or = " OR ".join([f'"{s}"' for s in secondary_skills])
                parts.append(f"({skill_or})")
            linkedin_parts.append(" AND ".join([f'"{s}"' for s in primary_skills[:3]]))

        if companies:
            company_or = " OR ".join([f'"{c}"' for c in companies[:10]])
            parts.append(f"({company_or})")

        if industries:
            industry_or = " OR ".join([f'"{i}"' for i in industries[:5]])
            parts.append(f"({industry_or})")

        if location:
            parts.append(f'"{location}"')
            linkedin_parts.append(f'"{location}"')

        if seniority:
            seniority_map = {
                "junior": '("Junior" OR "Júnior" OR "Trainee" OR "Estágio")',
                "pleno": '("Pleno" OR "Mid-level" OR "Intermediário")',
                "senior": '("Senior" OR "Sênior" OR "Sr." OR "Lead")',
                "specialist": '("Especialista" OR "Specialist" OR "Expert")',
                "manager": '("Manager" OR "Gerente" OR "Head" OR "Coordenador")',
                "director": '("Director" OR "Diretor" OR "VP" OR "C-Level")',
            }
            if seniority.lower() in seniority_map:
                parts.append(seniority_map[seniority.lower()])

        if exclude_terms:
            for term in exclude_terms:
                parts.append(f'NOT "{term}"')

        database_query = " AND ".join(parts)
        linkedin_query = " AND ".join(linkedin_parts)
        pearch_query = database_query.replace(" AND ", " ")

        return {
            "linkedin": linkedin_query,
            "database": database_query,
            "pearch": pearch_query,
            "raw_parts": parts,
        }

    @staticmethod
    def expand_synonyms(term: str) -> list[str]:
        """Expand a term with common synonyms."""
        synonyms_map: dict[str, list[str]] = {
            "developer": ["desenvolvedor", "programador", "engineer", "engenheiro"],
            "desenvolvedor": ["developer", "programador", "engineer"],
            "frontend": ["front-end", "front end", "ui developer"],
            "backend": ["back-end", "back end", "server-side"],
            "fullstack": ["full-stack", "full stack", "full-stack developer"],
            "python": ["python3", "py"],
            "javascript": ["js", "ecmascript"],
            "react": ["reactjs", "react.js"],
            "node": ["nodejs", "node.js"],
            "typescript": ["ts"],
            "machine learning": ["ml", "aprendizado de máquina"],
            "data scientist": ["cientista de dados", "ds"],
            "product manager": ["pm", "gerente de produto", "product owner"],
            "ux": ["user experience", "experiência do usuário"],
            "ui": ["user interface", "interface"],
            "devops": ["dev ops", "sre", "platform engineer"],
        }
        result = [term]
        if term.lower() in synonyms_map:
            result.extend(synonyms_map[term.lower()])
        return list(set(result))


class CandidateMatcher:
    """
    Scoring and matching logic for candidates against job requirements.
    """

    @staticmethod
    def calculate_skills_match(
        candidate_skills: list[str],
        required_skills: list[str],
        nice_to_have_skills: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate skills match percentage and details.

        Returns:
            Dict with match_percentage, matched_required, matched_nice_to_have, missing_required.
        """
        if not required_skills:
            return {
                "match_percentage": 100,
                "matched_required": [],
                "matched_nice_to_have": [],
                "missing_required": [],
            }

        candidate_lower = [s.lower().strip() for s in candidate_skills]
        required_lower = [s.lower().strip() for s in required_skills]
        nice_lower = [s.lower().strip() for s in (nice_to_have_skills or [])]

        matched_required = [
            skill for skill in required_lower
            if any(skill in cs or cs in skill for cs in candidate_lower)
        ]
        matched_nice = [
            skill for skill in nice_lower
            if any(skill in cs or cs in skill for cs in candidate_lower)
        ]

        req_pct = (len(matched_required) / len(required_lower) * 100) if required_lower else 100.0
        nice_pct = (len(matched_nice) / len(nice_lower) * 100) if nice_lower else 100.0
        final_pct = req_pct * 0.8 + nice_pct * 0.2

        return {
            "match_percentage": round(final_pct, 1),
            "matched_required": matched_required,
            "matched_nice_to_have": matched_nice,
            "missing_required": [s for s in required_lower if s not in matched_required],
            "required_match_pct": round(req_pct, 1),
            "nice_to_have_match_pct": round(nice_pct, 1),
        }

    @staticmethod
    def calculate_experience_match(
        candidate_years: float | None,
        required_min: int | None,
        required_max: int | None = None,
    ) -> dict[str, Any]:
        """Calculate experience match score."""
        if candidate_years is None:
            return {"match_score": 50, "meets_minimum": None, "status": "unknown"}
        if required_min is None:
            return {"match_score": 100, "meets_minimum": True, "status": "no_requirement"}
        if candidate_years >= required_min:
            if required_max and candidate_years > required_max:
                penalty = min(30, (candidate_years - required_max) * 5)
                return {
                    "match_score": max(70, 100 - penalty),
                    "meets_minimum": True,
                    "exceeds_maximum": True,
                    "status": "overqualified",
                }
            return {"match_score": 100, "meets_minimum": True, "status": "meets_requirement"}
        gap = required_min - candidate_years
        if gap <= 1:
            return {"match_score": 80, "meets_minimum": False, "status": "slightly_under"}
        if gap <= 2:
            return {"match_score": 60, "meets_minimum": False, "status": "under_qualified"}
        return {"match_score": 30, "meets_minimum": False, "status": "significantly_under"}

    @staticmethod
    def calculate_location_match(
        candidate_city: str | None,
        candidate_state: str | None,
        candidate_country: str | None,
        candidate_is_remote: bool | None,
        job_city: str | None,
        job_state: str | None,
        job_country: str | None,
        job_allows_remote: bool | None,
        job_work_model: str | None = None,
    ) -> dict[str, Any]:
        """Calculate location compatibility."""
        if job_allows_remote or job_work_model == "remote":
            return {
                "match_score": 100,
                "is_exact_match": False,
                "is_remote_compatible": True,
                "reason": "Remote position - location flexible",
            }
        if candidate_is_remote and job_work_model == "hybrid":
            return {
                "match_score": 70,
                "is_exact_match": False,
                "is_remote_compatible": True,
                "reason": "Candidate prefers remote but job is hybrid",
            }
        if not job_city and not job_state:
            return {"match_score": 100, "is_exact_match": False, "reason": "No location requirement"}

        score = 0
        if job_city and candidate_city:
            if candidate_city.lower().strip() == job_city.lower().strip():
                score = 100
            elif job_state and candidate_state:
                if candidate_state.lower().strip() == job_state.lower().strip():
                    score = 80
        elif job_state and candidate_state:
            if candidate_state.lower().strip() == job_state.lower().strip():
                score = 80
        elif job_country and candidate_country:
            if candidate_country.lower().strip() == job_country.lower().strip():
                score = 60

        return {
            "match_score": score,
            "is_exact_match": score == 100,
            "is_remote_compatible": False,
            "reason": "Location match" if score >= 80 else "Location mismatch",
        }

    @staticmethod
    def calculate_overall_score(
        skills_match: dict[str, Any],
        experience_match: dict[str, Any],
        location_match: dict[str, Any],
        weights: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate weighted overall match score.
        Default weights: skills=50%, experience=30%, location=20%.
        """
        if weights is None:
            weights = {"skills": 0.50, "experience": 0.30, "location": 0.20}

        overall = (
            skills_match.get("match_percentage", 0) * weights["skills"]
            + experience_match.get("match_score", 50) * weights["experience"]
            + location_match.get("match_score", 50) * weights["location"]
        )
        tier = "A" if overall >= 85 else "B" if overall >= 70 else "C" if overall >= 55 else "D"

        return {
            "overall_score": round(overall, 1),
            "tier": tier,
            "breakdown": {
                "skills": round(skills_match.get("match_percentage", 0), 1),
                "experience": round(experience_match.get("match_score", 50), 1),
                "location": round(location_match.get("match_score", 50), 1),
            },
            "weights": weights,
            "recommendation": (
                "Strong Match" if tier == "A"
                else "Good Match" if tier == "B"
                else "Potential Match" if tier == "C"
                else "Weak Match"
            ),
        }
