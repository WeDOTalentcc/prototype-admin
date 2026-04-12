import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

SENIORITY_KEYWORDS: dict[str, list[str]] = {
    "c_level": ["ceo", "cto", "cfo", "coo", "cmo", "cio", "chief"],
    "vp": ["vice president", "vp"],
    "director": ["director", "diretor", "directeur"],
    "manager": ["manager", "gerente", "head of", "lead"],
    "senior": ["senior", "sênior", "sr.", "principal", "staff"],
    "mid": ["pleno", "mid-level", "mid level"],
    "junior": ["junior", "júnior", "jr.", "trainee", "intern", "estagiário"],
}


class ApifyProfileMapper:

    def map_to_candidate(self, apify_data: dict[str, Any]) -> dict[str, Any]:
        if not apify_data:
            return {}

        candidate: dict[str, Any] = {}

        first_name = apify_data.get("firstName", "")
        last_name = apify_data.get("lastName", "")
        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            candidate["name"] = full_name

        candidate["headline"] = apify_data.get("headline")
        candidate["self_introduction"] = apify_data.get("summary")
        candidate["current_title"] = apify_data.get("headline")
        candidate["linkedin_url"] = apify_data.get("profileUrl") or apify_data.get("url")
        candidate["avatar_url"] = apify_data.get("profilePicture") or apify_data.get("img")

        location_raw = apify_data.get("location", "")
        if location_raw:
            city, state, country = self._parse_location(location_raw)
            if city:
                candidate["location_city"] = city
            if state:
                candidate["location_state"] = state
            if country:
                candidate["location_country"] = country

        connections = apify_data.get("connectionCount") or apify_data.get("connectionsCount")
        if connections:
            try:
                candidate["linkedin_connections"] = int(connections)
            except (ValueError, TypeError):
                pass

        followers = apify_data.get("followersCount")
        if followers:
            try:
                candidate["linkedin_followers"] = int(followers)
            except (ValueError, TypeError):
                pass

        emails = self._extract_emails(apify_data)
        if emails:
            candidate["email"] = emails[0]
            if len(emails) > 1:
                candidate["secondary_email"] = emails[1]
            candidate["personal_emails"] = emails

        phones = self._extract_phones(apify_data)
        if phones:
            candidate["phone"] = phones[0]
            if len(phones) > 1:
                candidate["mobile_phone"] = phones[1] if phones[1] != phones[0] else None

        skills = self.map_to_skills(apify_data)
        if skills:
            candidate["technical_skills"] = skills

        certs = apify_data.get("certifications", [])
        if isinstance(certs, list):
            candidate["certifications"] = [
                c.get("name", c) if isinstance(c, dict) else str(c)
                for c in certs[:20]
            ]

        languages = apify_data.get("languages", [])
        if isinstance(languages, list) and languages:
            candidate["languages"] = [
                lang.get("name", lang) if isinstance(lang, dict) else str(lang)
                for lang in languages
            ]

        current_exp = self._get_current_experience(apify_data)
        if current_exp:
            candidate["current_company"] = current_exp.get("companyName", "")
            title = current_exp.get("title", "")
            if title:
                candidate["current_title"] = title

        years = self._calculate_years_of_experience(apify_data)
        if years is not None:
            candidate["years_of_experience"] = years

        title_for_seniority = candidate.get("current_title") or apify_data.get("headline", "")
        seniority = self._infer_seniority(title_for_seniority)
        if seniority:
            candidate["seniority_level"] = seniority

        candidate["source"] = "apify"
        candidate["enrichment_source"] = "apify"

        return {k: v for k, v in candidate.items() if v is not None}

    def map_to_experiences(self, apify_data: dict[str, Any]) -> list[dict[str, Any]]:
        raw_experiences = apify_data.get("experience", [])
        if not isinstance(raw_experiences, list):
            return []

        experiences: list[dict[str, Any]] = []
        for exp in raw_experiences[:15]:
            if not isinstance(exp, dict):
                continue

            mapped: dict[str, Any] = {
                "company_name": exp.get("companyName", "Unknown"),
                "title": exp.get("title"),
                "description": exp.get("description"),
                "location": exp.get("locationName"),
                "company_linkedin_url": exp.get("companyUrl"),
            }

            time_period = exp.get("timePeriod") or {}
            if isinstance(time_period, dict):
                start = time_period.get("startDate", {})
                end = time_period.get("endDate", {})
                if isinstance(start, dict) and start.get("year"):
                    month = start.get("month", 1)
                    mapped["start_date"] = f"{start['year']}-{month:02d}"
                if isinstance(end, dict) and end.get("year"):
                    month = end.get("month", 1)
                    mapped["end_date"] = f"{end['year']}-{month:02d}"
                else:
                    mapped["is_current"] = True
            elif isinstance(time_period, str):
                mapped["start_date"] = time_period

            if mapped.get("start_date") and mapped.get("end_date"):
                try:
                    s = datetime.strptime(mapped["start_date"], "%Y-%m")
                    e = datetime.strptime(mapped["end_date"], "%Y-%m")
                    mapped["duration_years"] = round((e - s).days / 365.25, 1)
                except (ValueError, TypeError):
                    pass
            elif mapped.get("start_date") and mapped.get("is_current"):
                try:
                    s = datetime.strptime(mapped["start_date"], "%Y-%m")
                    mapped["duration_years"] = round((datetime.utcnow() - s).days / 365.25, 1)
                except (ValueError, TypeError):
                    pass

            experiences.append({k: v for k, v in mapped.items() if v is not None})

        return experiences

    def map_to_educations(self, apify_data: dict[str, Any]) -> list[dict[str, Any]]:
        raw_education = apify_data.get("education", [])
        if not isinstance(raw_education, list):
            return []

        educations: list[dict[str, Any]] = []
        for edu in raw_education[:10]:
            if not isinstance(edu, dict):
                continue

            mapped: dict[str, Any] = {
                "institution": edu.get("schoolName", "Unknown"),
                "degree": edu.get("degreeName"),
                "field_of_study": edu.get("fieldOfStudy"),
            }

            time_period = edu.get("timePeriod") or {}
            if isinstance(time_period, dict):
                start = time_period.get("startDate", {})
                end = time_period.get("endDate", {})
                if isinstance(start, dict) and start.get("year"):
                    mapped["start_date"] = str(start["year"])
                if isinstance(end, dict) and end.get("year"):
                    mapped["end_date"] = str(end["year"])
                    mapped["is_completed"] = True

            educations.append({k: v for k, v in mapped.items() if v is not None})

        return educations

    def map_to_skills(self, apify_data: dict[str, Any]) -> list[str]:
        raw_skills = apify_data.get("skills", [])
        if not isinstance(raw_skills, list):
            return []

        skills: list[str] = []
        for s in raw_skills[:30]:
            if isinstance(s, dict):
                name = s.get("name", "")
            else:
                name = str(s)
            name = name.strip()
            if name and name not in skills:
                skills.append(name)
        return skills

    def _extract_emails(self, data: dict[str, Any]) -> list[str]:
        emails: list[str] = []

        for key in ["email", "emailAddress", "personal_email", "work_email"]:
            val = data.get(key)
            if val and isinstance(val, str) and "@" in val and val not in emails:
                emails.append(val)

        for key in ["emails", "personal_emails", "business_emails"]:
            vals = data.get(key, [])
            if isinstance(vals, list):
                for v in vals:
                    addr = v.get("address", v) if isinstance(v, dict) else str(v)
                    if isinstance(addr, str) and "@" in addr and addr not in emails:
                        emails.append(addr)

        return emails

    def _extract_phones(self, data: dict[str, Any]) -> list[str]:
        phones: list[str] = []

        for key in ["phone", "phoneNumber", "mobile_phone"]:
            val = data.get(key)
            if val and isinstance(val, str) and val not in phones:
                phones.append(val)

        phone_list = data.get("phoneNumbers") or data.get("phones") or []
        if isinstance(phone_list, list):
            for p in phone_list:
                number = p.get("number", p) if isinstance(p, dict) else str(p)
                if isinstance(number, str) and number not in phones:
                    phones.append(number)

        return phones

    def _parse_location(self, location: str) -> tuple[str | None, str | None, str | None]:
        if not location:
            return None, None, None

        parts = [p.strip() for p in location.split(",")]

        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            return parts[0], None, parts[1]
        else:
            return parts[0], None, None

    def _get_current_experience(self, data: dict[str, Any]) -> dict[str, Any] | None:
        experiences = data.get("experience", [])
        if not isinstance(experiences, list) or not experiences:
            return None

        for exp in experiences:
            if not isinstance(exp, dict):
                continue
            time_period = exp.get("timePeriod") or {}
            if isinstance(time_period, dict):
                if not time_period.get("endDate"):
                    return exp
            elif not exp.get("end_date"):
                return exp

        return experiences[0] if experiences else None

    def _calculate_years_of_experience(self, data: dict[str, Any]) -> int | None:
        experiences = data.get("experience", [])
        if not isinstance(experiences, list) or not experiences:
            return None

        earliest_year: int | None = None
        for exp in experiences:
            if not isinstance(exp, dict):
                continue
            time_period = exp.get("timePeriod") or {}
            if isinstance(time_period, dict):
                start = time_period.get("startDate", {})
                if isinstance(start, dict) and start.get("year"):
                    year = int(start["year"])
                    if earliest_year is None or year < earliest_year:
                        earliest_year = year

        if earliest_year:
            return max(0, datetime.utcnow().year - earliest_year)
        return None

    def _infer_seniority(self, title: str) -> str | None:
        if not title:
            return None
        title_lower = title.lower()

        for level, keywords in SENIORITY_KEYWORDS.items():
            for kw in keywords:
                if kw in title_lower:
                    return level
        return None
