"""
Search Analytics Service - Proactive analysis of candidate search results.

Provides metrics, insights, and suggested actions based on search results.
"""
import logging
import re
import statistics
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class SearchAnalyticsService:
    """Serviço para análise proativa de resultados de busca."""
    
    def __init__(self):
        self.competitor_companies = {
            "nubank", "ifood", "picpay", "mercado livre", "mercadolivre",
            "stone", "pagseguro", "inter", "c6", "btg", "xp", "itaú", "bradesco",
            "santander", "ambev", "vale", "petrobras", "magalu", "magazine luiza",
            "ame", "ame digital", "creditas", "neon", "warren", "loft", "quinto andar",
            "quintoandar", "99", "uber", "rappi", "loggi", "vtex", "totvs"
        }
    
    def analyze_search_results(
        self,
        candidates: list[dict[str, Any]],
        search_criteria: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analisa resultados de busca e retorna métricas e insights.
        
        Args:
            candidates: Lista de candidatos (dicts com dados do perfil)
            search_criteria: Critérios de busca opcionais para contexto
            
        Returns:
            Dict com summary, contact_quality, distributions, top_skills,
            top_companies, experience_range, alerts e suggested_actions
        """
        if not candidates:
            return self._empty_analytics()
        
        summary = self._calculate_summary(candidates)
        contact_quality = self._calculate_contact_quality(candidates)
        distributions = self._calculate_distributions(candidates)
        top_skills = self._extract_top_skills(candidates, limit=10)
        top_companies = self._extract_top_companies(candidates, limit=5)
        experience_range = self._calculate_experience_range(candidates)
        alerts = self._generate_alerts(candidates, distributions, contact_quality)
        suggested_actions = self._get_suggested_actions(candidates)
        
        return {
            "summary": summary,
            "contact_quality": contact_quality,
            "distributions": distributions,
            "top_skills": top_skills,
            "top_companies": top_companies,
            "experience_range": experience_range,
            "alerts": alerts,
            "suggested_actions": suggested_actions
        }
    
    def _empty_analytics(self) -> dict[str, Any]:
        """Returns empty analytics structure when no candidates."""
        return {
            "summary": {
                "total_candidates": 0,
                "local_count": 0,
                "global_count": 0,
                "average_lia_score": 0.0
            },
            "contact_quality": {
                "with_valid_phone": 0,
                "with_valid_email": 0,
                "with_linkedin": 0,
                "phone_percentage": 0.0,
                "email_percentage": 0.0
            },
            "distributions": {
                "seniority": {},
                "location": {},
                "work_model": {}
            },
            "top_skills": [],
            "top_companies": [],
            "experience_range": {
                "min": 0,
                "max": 0,
                "average": 0.0,
                "median": 0.0
            },
            "alerts": [],
            "suggested_actions": self._get_suggested_actions([])
        }
    
    def _calculate_summary(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate summary metrics."""
        total = len(candidates)
        local_count = sum(1 for c in candidates if c.get("source") == "local")
        global_count = total - local_count
        
        scores = [
            c.get("score") or c.get("lia_score") or 0 
            for c in candidates 
            if c.get("score") or c.get("lia_score")
        ]
        average_score = round(statistics.mean(scores), 1) if scores else 0.0
        
        return {
            "total_candidates": total,
            "local_count": local_count,
            "global_count": global_count,
            "average_lia_score": average_score
        }
    
    def _calculate_contact_quality(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate contact quality metrics."""
        total = len(candidates)
        if total == 0:
            return {
                "with_valid_phone": 0,
                "with_valid_email": 0,
                "with_linkedin": 0,
                "phone_percentage": 0.0,
                "email_percentage": 0.0
            }
        
        with_valid_phone = 0
        with_valid_email = 0
        with_linkedin = 0
        
        for c in candidates:
            phone = c.get("phone") or c.get("phone_number")
            if phone and self._is_valid_phone(phone):
                with_valid_phone += 1
            elif c.get("has_phone"):
                with_valid_phone += 1
            
            email = c.get("email")
            if email and self._is_valid_email(email):
                with_valid_email += 1
            elif c.get("has_email"):
                with_valid_email += 1
            
            linkedin = c.get("linkedin_url") or c.get("linkedin")
            if linkedin:
                with_linkedin += 1
        
        return {
            "with_valid_phone": with_valid_phone,
            "with_valid_email": with_valid_email,
            "with_linkedin": with_linkedin,
            "phone_percentage": round((with_valid_phone / total) * 100, 1),
            "email_percentage": round((with_valid_email / total) * 100, 1)
        }
    
    def _calculate_distributions(self, candidates: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
        """Calculate distributions for seniority, location, and work model."""
        seniority_counter: Counter = Counter()
        location_counter: Counter = Counter()
        work_model_counter: Counter = Counter()
        
        for c in candidates:
            seniority = self._normalize_seniority(
                c.get("seniority") or c.get("seniority_level") or 
                self._infer_seniority_from_title(c.get("current_title") or c.get("headline") or "")
            )
            if seniority:
                seniority_counter[seniority] += 1
            
            location = c.get("location") or c.get("location_city") or ""
            if location:
                location_normalized = self._normalize_location(location)
                location_counter[location_normalized] += 1
            
            work_model = self._extract_work_model(c)
            if work_model:
                work_model_counter[work_model] += 1
        
        return {
            "seniority": dict(seniority_counter.most_common(10)),
            "location": dict(location_counter.most_common(10)),
            "work_model": dict(work_model_counter.most_common(5))
        }
    
    def _extract_top_skills(self, candidates: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
        """Extract top skills from candidates."""
        total = len(candidates)
        if total == 0:
            return []
        
        skill_counter: Counter = Counter()
        
        for c in candidates:
            skills = c.get("skills") or c.get("technical_skills") or []
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",")]
            
            for skill in skills:
                if skill and isinstance(skill, str):
                    normalized = skill.strip().title()
                    if len(normalized) > 1:
                        skill_counter[normalized] += 1
        
        top_skills = []
        for skill, count in skill_counter.most_common(limit):
            top_skills.append({
                "skill": skill,
                "count": count,
                "percentage": round((count / total) * 100, 1)
            })
        
        return top_skills
    
    def _extract_top_companies(self, candidates: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
        """Extract top companies from candidates."""
        company_counter: Counter = Counter()
        
        for c in candidates:
            company = c.get("current_company") or c.get("company") or ""
            if company and isinstance(company, str):
                normalized = company.strip()
                if len(normalized) > 1:
                    company_counter[normalized] += 1
        
        top_companies = []
        for company, count in company_counter.most_common(limit):
            top_companies.append({
                "company": company,
                "count": count
            })
        
        return top_companies
    
    def _calculate_experience_range(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate experience years statistics."""
        years_list = []
        
        for c in candidates:
            years = c.get("total_experience_years") or c.get("years_of_experience")
            if years is not None:
                try:
                    years_float = float(years)
                    if 0 <= years_float <= 50:
                        years_list.append(years_float)
                except (ValueError, TypeError):
                    pass
        
        if not years_list:
            return {
                "min": 0,
                "max": 0,
                "average": 0.0,
                "median": 0.0
            }
        
        return {
            "min": int(min(years_list)),
            "max": int(max(years_list)),
            "average": round(statistics.mean(years_list), 1),
            "median": round(statistics.median(years_list), 1)
        }
    
    def _generate_alerts(
        self, 
        candidates: list[dict[str, Any]], 
        distributions: dict[str, dict[str, int]],
        contact_quality: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Generate contextual alerts based on analysis."""
        alerts = []
        total = len(candidates)
        
        if total == 0:
            return []
        
        competitor_count = 0
        for c in candidates:
            company = (c.get("current_company") or "").lower()
            if any(comp in company for comp in self.competitor_companies):
                competitor_count += 1
        
        competitor_percentage = (competitor_count / total) * 100
        if competitor_percentage >= 50:
            alerts.append({
                "type": "warning",
                "message": f"{int(competitor_percentage)}% dos candidatos estão em empresas concorrentes"
            })
        
        location_dist = distributions.get("location", {})
        if location_dist:
            top_location = max(location_dist.items(), key=lambda x: x[1]) if location_dist else None
            if top_location:
                location_percentage = (top_location[1] / total) * 100
                if location_percentage >= 50:
                    alerts.append({
                        "type": "info",
                        "message": f"Pool tem forte concentração em {top_location[0]} ({int(location_percentage)}%)"
                    })
        
        phone_percentage = contact_quality.get("phone_percentage", 0)
        email_percentage = contact_quality.get("email_percentage", 0)
        
        if phone_percentage < 30:
            alerts.append({
                "type": "warning",
                "message": f"Apenas {int(phone_percentage)}% dos candidatos têm telefone disponível"
            })
        
        if email_percentage < 50:
            alerts.append({
                "type": "warning",
                "message": f"Apenas {int(email_percentage)}% dos candidatos têm email disponível"
            })
        
        seniority_dist = distributions.get("seniority", {})
        senior_count = seniority_dist.get("Senior", 0) + seniority_dist.get("senior", 0)
        junior_count = seniority_dist.get("Junior", 0) + seniority_dist.get("junior", 0)
        
        if senior_count > total * 0.7:
            alerts.append({
                "type": "info",
                "message": f"Pool predominantemente sênior ({int((senior_count/total)*100)}%)"
            })
        elif junior_count > total * 0.7:
            alerts.append({
                "type": "info",
                "message": f"Pool predominantemente júnior ({int((junior_count/total)*100)}%)"
            })
        
        return alerts
    
    def _get_suggested_actions(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Get list of suggested actions for the search results."""
        actions = [
            {
                "id": "start_screening",
                "label": "Iniciar Triagem WSI",
                "icon": "ClipboardCheck",
                "description": "Começar avaliação dos candidatos",
                "action_type": "screening"
            },
            {
                "id": "assign_vacancy",
                "label": "Atribuir à Vaga",
                "icon": "Briefcase",
                "description": "Vincular a uma posição aberta",
                "action_type": "assign"
            },
            {
                "id": "save_favorites",
                "label": "Salvar em Favoritos",
                "icon": "Star",
                "description": "Guardar pool para referência",
                "action_type": "favorite"
            },
            {
                "id": "check_availability",
                "label": "Verificar Disponibilidade",
                "icon": "MessageCircle",
                "description": "Enviar WhatsApp em lote",
                "action_type": "whatsapp"
            },
            {
                "id": "schedule_interviews",
                "label": "Agendar Entrevistas",
                "icon": "Calendar",
                "description": "Batch scheduling",
                "action_type": "schedule"
            },
            {
                "id": "refine_search",
                "label": "Refinar Busca",
                "icon": "Filter",
                "description": "Adicionar/remover critérios",
                "action_type": "refine"
            },
            {
                "id": "export_list",
                "label": "Exportar Lista",
                "icon": "Download",
                "description": "Download em Excel/CSV",
                "action_type": "export"
            }
        ]
        
        return actions
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format (Brazilian)."""
        if not phone or not isinstance(phone, str):
            return False
        
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) >= 10 and len(digits_only) <= 13:
            return True
        
        return False
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        if not email or not isinstance(email, str):
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    def _normalize_seniority(self, seniority: str | None) -> str | None:
        """Normalize seniority level strings."""
        if not seniority:
            return None
        
        seniority_lower = seniority.lower().strip()
        
        seniority_map = {
            "júnior": "Junior",
            "junior": "Junior",
            "jr": "Junior",
            "entry": "Junior",
            "entry level": "Junior",
            "pleno": "Pleno",
            "mid": "Pleno",
            "mid-level": "Pleno",
            "midlevel": "Pleno",
            "sênior": "Senior",
            "senior": "Senior",
            "sr": "Senior",
            "staff": "Staff",
            "lead": "Lead",
            "tech lead": "Lead",
            "líder": "Lead",
            "principal": "Principal",
            "manager": "Manager",
            "gerente": "Manager",
            "diretor": "Director",
            "director": "Director"
        }
        
        return seniority_map.get(seniority_lower, seniority.title())
    
    def _infer_seniority_from_title(self, title: str) -> str | None:
        """Infer seniority level from job title."""
        if not title:
            return None
        
        title_lower = title.lower()
        
        if any(term in title_lower for term in ["júnior", "junior", " jr ", " jr.", "entry"]):
            return "Junior"
        elif any(term in title_lower for term in ["pleno", "mid ", "mid-level"]):
            return "Pleno"
        elif any(term in title_lower for term in ["sênior", "senior", " sr ", " sr.", "especialista"]):
            return "Senior"
        elif any(term in title_lower for term in ["staff", "principal"]):
            return "Staff"
        elif any(term in title_lower for term in ["lead", "líder", "tech lead"]):
            return "Lead"
        elif any(term in title_lower for term in ["manager", "gerente", "coordenador"]):
            return "Manager"
        elif any(term in title_lower for term in ["diretor", "director", "head of", "vp ", "c-level", "cto", "cio"]):
            return "Director"
        
        return None
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location strings."""
        if not location:
            return "Não especificado"
        
        location_normalized = location.strip()
        
        location_map = {
            "sp": "São Paulo",
            "são paulo": "São Paulo",
            "sao paulo": "São Paulo",
            "rj": "Rio de Janeiro",
            "rio de janeiro": "Rio de Janeiro",
            "bh": "Belo Horizonte",
            "belo horizonte": "Belo Horizonte",
            "poa": "Porto Alegre",
            "porto alegre": "Porto Alegre",
            "cwb": "Curitiba",
            "curitiba": "Curitiba",
            "bsb": "Brasília",
            "brasília": "Brasília",
            "brasilia": "Brasília",
            "remote": "Remoto",
            "remoto": "Remoto",
        }
        
        location_lower = location.lower().strip()
        if location_lower in location_map:
            return location_map[location_lower]
        
        for key, value in location_map.items():
            if key in location_lower:
                return value
        
        return location_normalized
    
    def _extract_work_model(self, candidate: dict[str, Any]) -> str | None:
        """Extract work model preference from candidate data."""
        work_model = candidate.get("work_model") or candidate.get("modelo_trabalho")
        if work_model:
            model_lower = work_model.lower()
            if "remoto" in model_lower or "remote" in model_lower:
                return "Remoto"
            elif "híbrido" in model_lower or "hybrid" in model_lower:
                return "Híbrido"
            elif "presencial" in model_lower or "onsite" in model_lower or "on-site" in model_lower:
                return "Presencial"
            return work_model.title()
        
        location = candidate.get("location") or ""
        headline = candidate.get("headline") or candidate.get("current_title") or ""
        
        combined = f"{location} {headline}".lower()
        
        if "remoto" in combined or "remote" in combined:
            return "Remoto"
        elif "híbrido" in combined or "hybrid" in combined:
            return "Híbrido"
        
        return None
    
    def generate_proactive_narrative(self, analytics: dict[str, Any]) -> str:
        """
        Generate a proactive narrative description of the search results.
        
        This is a basic implementation. In production, this could be enhanced
        with an LLM for more natural and contextual narratives.
        """
        summary = analytics.get("summary", {})
        total = summary.get("total_candidates", 0)
        
        if total == 0:
            return "Nenhum candidato encontrado com os critérios especificados."
        
        local_count = summary.get("local_count", 0)
        global_count = summary.get("global_count", 0)
        avg_score = summary.get("average_lia_score", 0)
        
        top_skills = analytics.get("top_skills", [])
        top_companies = analytics.get("top_companies", [])
        exp_range = analytics.get("experience_range", {})
        distributions = analytics.get("distributions", {})
        
        narrative_parts = []
        
        source_text = ""
        if local_count > 0 and global_count > 0:
            source_text = f"({local_count} da base local e {global_count} da busca global)"
        elif local_count > 0:
            source_text = "(todos da base local)"
        elif global_count > 0:
            source_text = "(todos da busca global)"
        
        narrative_parts.append(f"Encontrei {total} candidatos {source_text}.")
        
        if avg_score > 0:
            if avg_score >= 80:
                narrative_parts.append(f"O score médio de compatibilidade é excelente: {avg_score}%.")
            elif avg_score >= 60:
                narrative_parts.append(f"O score médio de compatibilidade é bom: {avg_score}%.")
            else:
                narrative_parts.append(f"O score médio de compatibilidade é {avg_score}%.")
        
        if top_skills and len(top_skills) >= 2:
            skills_text = ", ".join([s["skill"] for s in top_skills[:3]])
            narrative_parts.append(f"As skills mais comuns são: {skills_text}.")
        
        if exp_range.get("average", 0) > 0:
            avg_exp = exp_range["average"]
            min_exp = exp_range.get("min", 0)
            max_exp = exp_range.get("max", 0)
            narrative_parts.append(
                f"A experiência média é de {avg_exp} anos (variando de {min_exp} a {max_exp})."
            )
        
        seniority = distributions.get("seniority", {})
        if seniority:
            top_seniority = max(seniority.items(), key=lambda x: x[1]) if seniority else None
            if top_seniority:
                narrative_parts.append(f"A maioria é de nível {top_seniority[0]}.")
        
        if top_companies and len(top_companies) >= 2:
            companies_text = ", ".join([c["company"] for c in top_companies[:3]])
            narrative_parts.append(f"Principais empresas de origem: {companies_text}.")
        
        return " ".join(narrative_parts)


search_analytics_service = SearchAnalyticsService()
