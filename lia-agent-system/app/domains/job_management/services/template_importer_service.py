"""
Template Importer Service.

Imports job templates from external sources:
- ESCO (European Skills, Competences, Qualifications and Occupations)
- O*NET (Occupational Information Network)
- CBO (Classificação Brasileira de Ocupações) mappings

This service enables fast population of the 480+ template library
instead of creating each template manually.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.services.job_template_service import validate_wsi_quality
from lia_models.job_template import JobTemplate

logger = logging.getLogger(__name__)

ESCO_API_BASE = "https://ec.europa.eu/esco/api"
ONET_API_BASE = "https://services.onetcenter.org/ws"


CATEGORY_MAPPING = {
    "tecnologia": {
        "esco_codes": ["25", "133", "351"],
        "onet_prefixes": ["15-", "17-"],
        "display_name": "Tecnologia / TI"
    },
    "financas": {
        "esco_codes": ["24", "331"],
        "onet_prefixes": ["13-"],
        "display_name": "Finanças / Contabilidade"
    },
    "recursos_humanos": {
        "esco_codes": ["242", "121"],
        "onet_prefixes": ["11-3", "13-1"],
        "display_name": "Recursos Humanos"
    },
    "vendas": {
        "esco_codes": ["332", "243"],
        "onet_prefixes": ["41-"],
        "display_name": "Vendas"
    },
    "marketing": {
        "esco_codes": ["243", "264"],
        "onet_prefixes": ["11-2", "27-3"],
        "display_name": "Marketing"
    },
    "operacoes": {
        "esco_codes": ["132", "314"],
        "onet_prefixes": ["11-1", "43-"],
        "display_name": "Operações"
    },
    "engenharia": {
        "esco_codes": ["21", "214"],
        "onet_prefixes": ["17-2"],
        "display_name": "Engenharia"
    },
    "juridico": {
        "esco_codes": ["261"],
        "onet_prefixes": ["23-"],
        "display_name": "Jurídico"
    },
    "administrativo": {
        "esco_codes": ["334", "411"],
        "onet_prefixes": ["43-"],
        "display_name": "Administrativo"
    },
    "customer_success": {
        "esco_codes": ["422"],
        "onet_prefixes": ["43-4"],
        "display_name": "Customer Success"
    },
    "saude": {
        "esco_codes": ["22", "32"],
        "onet_prefixes": ["29-", "31-"],
        "display_name": "Saúde"
    },
    "educacao": {
        "esco_codes": ["23"],
        "onet_prefixes": ["25-"],
        "display_name": "Educação"
    },
    "qualidade": {
        "esco_codes": ["214", "311"],
        "onet_prefixes": ["17-2"],
        "display_name": "Qualidade"
    }
}

SENIORITY_LEVELS = ["junior", "pleno", "senior", "especialista", "coordenador", "gerente", "diretor"]


class TemplateImporterService:
    """Service for importing job templates from external sources."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
    
    async def search_esco_occupations(
        self,
        query: str,
        language: str = "en",
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search ESCO occupations by keyword.
        
        Args:
            query: Search term
            language: Language code (pt, en, es, etc.)
            limit: Max results
            
        Returns:
            List of occupation data with skills
        """
        try:
            url = f"{ESCO_API_BASE}/search"
            params = {
                "text": query,
                "type": "occupation",
                "language": language,
                "limit": limit,
                "full": "true"  # CRITICAL: Get full response with skills
            }
            
            logger.debug(f"Searching ESCO for: {query} (language: {language})")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("_embedded", {}).get("results", [])
            logger.info(f"ESCO search for '{query}' returned {len(results)} results")
            
            occupations = []
            for item in results:
                try:
                    # Extract title - prioritize the given language or English
                    title = item.get("title") or item.get("preferredLabel", {}).get(language) or item.get("preferredLabel", {}).get("en")
                    
                    # Extract description from language-specific dict
                    description_dict = item.get("description", {})
                    if isinstance(description_dict, dict):
                        description = description_dict.get(language) or description_dict.get("en", "")
                    else:
                        description = description_dict or ""
                    
                    # Extract skills from _links
                    essential_skills = []
                    optional_skills = []
                    
                    if "_links" in item:
                        for skill in item.get("_links", {}).get("hasEssentialSkill", []):
                            essential_skills.append({
                                "name": skill.get("title"),
                                "uri": skill.get("uri"),
                                "category": "essential",
                                "level": "intermediate",
                                "weight": 1.0,
                                "required": True
                            })
                        
                        for skill in item.get("_links", {}).get("hasOptionalSkill", []):
                            optional_skills.append({
                                "name": skill.get("title"),
                                "uri": skill.get("uri"),
                                "category": "optional",
                                "level": "basic",
                                "weight": 0.5,
                                "required": False
                            })
                    
                    occupations.append({
                        "uri": item.get("uri"),
                        "title": title,
                        "isco_code": item.get("code"),
                        "alternative_labels": item.get("alternativeLabel", []) if item.get("alternativeLabel") else [],
                        "description": description,
                        "essential_skills": essential_skills[:10],
                        "optional_skills": optional_skills[:5],
                    })
                except Exception as item_error:
                    logger.warning(f"Error parsing occupation item: {item_error}")
                    continue
            
            logger.info(f"Successfully parsed {len(occupations)} occupations from ESCO")
            return occupations
            
        except httpx.HTTPError as e:
            logger.error(f"ESCO HTTP error during search for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"ESCO search failed for '{query}': {e}", exc_info=True)
            return []
    
    async def get_esco_occupation_details(
        self,
        occupation_uri: str,
        language: str = "en"
    ) -> dict[str, Any] | None:
        """
        Get detailed occupation info including skills from ESCO.
        
        Args:
            occupation_uri: ESCO occupation URI
            language: Language code
            
        Returns:
            Detailed occupation data with skills
        """
        try:
            url = f"{ESCO_API_BASE}/resource/occupation"
            params = {
                "uri": occupation_uri,
                "language": language,
                "full": "true"  # CRITICAL: Get full response with skills
            }
            
            logger.debug(f"Fetching ESCO occupation details: {occupation_uri}")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Got occupation response with keys: {list(data.keys())}")
            
            essential_skills = []
            optional_skills = []
            
            # Extract skills from _links
            for skill in data.get("_links", {}).get("hasEssentialSkill", []):
                essential_skills.append({
                    "name": skill.get("title"),
                    "uri": skill.get("uri"),
                    "category": "essential",
                    "level": "intermediate",
                    "weight": 1.0,
                    "required": True
                })
            
            for skill in data.get("_links", {}).get("hasOptionalSkill", []):
                optional_skills.append({
                    "name": skill.get("title"),
                    "uri": skill.get("uri"),
                    "category": "optional",
                    "level": "basic",
                    "weight": 0.5,
                    "required": False
                })
            
            # Extract title from preferredLabel dict - use requested language or fallback to English
            preferred_label = data.get("preferredLabel", {})
            if isinstance(preferred_label, dict):
                title = preferred_label.get(language) or preferred_label.get("en") or data.get("title")
            else:
                title = data.get("title") or preferred_label
            
            # Extract description from language-specific dict
            description_dict = data.get("description", {})
            if isinstance(description_dict, dict):
                description = description_dict.get(language) or description_dict.get("en", "")
            else:
                description = description_dict or ""
            
            # Extract alternative labels
            alternative_labels = data.get("alternativeLabel", {})
            if isinstance(alternative_labels, dict):
                alt_list = alternative_labels.get(language) or alternative_labels.get("en", [])
                if isinstance(alt_list, str):
                    alt_list = [alt_list]
            else:
                alt_list = alternative_labels if isinstance(alternative_labels, list) else []
            
            result = {
                "uri": occupation_uri,
                "title": title,
                "alternative_labels": alt_list[:5],
                "description": description,
                "isco_code": data.get("code"),
                "essential_skills": essential_skills[:10],
                "optional_skills": optional_skills[:5],
            }
            
            logger.info(f"Successfully fetched occupation details: {title} with {len(essential_skills)} essential and {len(optional_skills)} optional skills")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"ESCO HTTP error fetching occupation {occupation_uri}: {e}")
            return None
        except Exception as e:
            logger.error(f"ESCO occupation details failed for {occupation_uri}: {e}", exc_info=True)
            return None
    
    async def import_from_esco(
        self,
        category: str,
        subcategory: str,
        search_terms: list[str],
        seniority_levels: list[str] | None = None
    ) -> list[JobTemplate]:
        """
        Import templates from ESCO for a category.
        
        Args:
            category: Target category
            subcategory: Target subcategory
            search_terms: List of terms to search
            seniority_levels: Seniority levels to create
            
        Returns:
            List of created templates
        """
        seniority_levels = seniority_levels or ["junior", "pleno", "senior"]
        created_templates = []
        
        for term in search_terms:
            logger.info(f"Importing templates for term: {term}")
            occupations = await self.search_esco_occupations(term, language="en")
            
            if not occupations:
                logger.warning(f"No occupations found for term: {term}")
                continue
            
            for occ in occupations[:5]:  # Increased from 3 to 5 to get more templates
                logger.debug(f"Processing occupation: {occ.get('title')}")
                
                # Check if we have skills from search results
                if not occ.get("essential_skills") or len(occ.get("essential_skills", [])) == 0:
                    logger.debug(f"Fetching detailed info for {occ.get('title')} to get skills")
                    # Fetch detailed occupation data if search results don't have skills
                    details = await self.get_esco_occupation_details(occ["uri"], language="en")
                    if not details:
                        logger.warning(f"Could not fetch details for {occ['uri']}")
                        continue
                else:
                    # Use data from search results directly
                    details = occ
                
                for seniority in seniority_levels:
                    try:
                        template = await self._create_template_from_esco(
                            details,
                            category,
                            subcategory,
                            seniority
                        )
                        if template:
                            created_templates.append(template)
                    except Exception as e:
                        logger.warning(f"Failed to create template for {details.get('title')} ({seniority}): {e}")
                        continue
                
                await asyncio.sleep(0.1)  # Reduced sleep for efficiency
        
        logger.info(f"Import from ESCO completed: {len(created_templates)} templates created")
        return created_templates
    
    async def _create_template_from_esco(
        self,
        esco_data: dict[str, Any],
        category: str,
        subcategory: str,
        seniority: str
    ) -> JobTemplate | None:
        """Create a JobTemplate from ESCO occupation data."""
        try:
            # Validate required fields
            if not esco_data.get("title"):
                logger.warning(f"Skipping occupation: missing title. Data keys: {list(esco_data.keys())}")
                return None
            
            title = esco_data["title"]
            title_normalized = JobTemplate.normalize_title(title)
            
            # Check for duplicate
            existing = await self.db.execute(
                text("""
                    SELECT id FROM job_templates 
                    WHERE title_normalized = :title AND seniority = :seniority AND is_system = true
                """),
                {"title": title_normalized, "seniority": seniority}
            )
            if existing.fetchone():
                logger.debug(f"Template already exists: {title} ({seniority})")
                return None
            
            # Combine essential and optional skills
            essential = esco_data.get("essential_skills", [])
            optional = esco_data.get("optional_skills", [])
            skills = essential + optional
            
            logger.debug(f"Creating template '{title}' ({seniority}) with {len(essential)} essential and {len(optional)} optional skills")
            
            # Generate behavioral and responsibilities
            behavioral = self._generate_behavioral_for_seniority(seniority)
            responsibilities = self._generate_responsibilities(title, seniority)
            
            # Get alternative labels and ensure it's a list
            alt_labels = esco_data.get("alternative_labels", [])
            if isinstance(alt_labels, dict):
                # ESCO API returns {lang: [labels]} format
                alt_labels = alt_labels.get("en", []) or list(alt_labels.values())[0] if alt_labels else []
            if not isinstance(alt_labels, list):
                alt_labels = [str(alt_labels)] if alt_labels else []
            
            # Get description and ensure it's a string
            description = esco_data.get("description", "")
            if isinstance(description, dict):
                # ESCO API returns {'literal': '...', 'mimetype': 'plain/text'} or {lang: '...'}
                description = description.get("literal", "") or description.get("en", "") or str(list(description.values())[0]) if description else ""
            if not isinstance(description, str):
                description = str(description) if description else ""
            
            # Create template
            template = JobTemplate(
                id=uuid4(),
                category=category,
                subcategory=subcategory,
                title=title,
                title_normalized=title_normalized,
                title_alternatives=alt_labels[:5],
                seniority=seniority,
                default_description=description,
                default_responsibilities=responsibilities,
                default_skills=skills[:10],
                default_behavioral=behavioral,
                is_system=True,
                is_active=True,
                template_metadata={
                    "source": "esco",
                    "esco_uri": esco_data.get("uri", ""),
                    "isco_code": esco_data.get("isco_code", ""),
                    "imported_at": datetime.utcnow().isoformat(),
                    "skills_count": len(skills),
                    "essential_skills_count": len(essential),
                    "optional_skills_count": len(optional)
                }
            )
            
            # Validate and enrich if needed
            validation = validate_wsi_quality(template.to_dict())
            if not validation["valid"]:
                logger.debug(f"Template validation failed: {validation.get('errors', 'unknown errors')}. Enriching...")
                template = await self._enrich_to_meet_wsi(template)
            
            # Save to database
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(f"✓ Created template: {title} ({seniority}) - ID: {template.id}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to create template from ESCO data: {e}", exc_info=True)
            try:
                await self.db.rollback()
            except Exception:
                pass
            return None
    
    def _generate_behavioral_for_seniority(self, seniority: str) -> list[dict[str, Any]]:
        """Generate behavioral competencies based on seniority."""
        base_behavioral = [
            {"name": "Comunicação", "weight": 1.0, "justification": "Essencial para trabalho em equipe"},
            {"name": "Trabalho em Equipe", "weight": 0.9, "justification": "Colaboração efetiva"},
            {"name": "Resolução de Problemas", "weight": 0.9, "justification": "Capacidade analítica"},
        ]
        
        if seniority in ["senior", "especialista"]:
            base_behavioral.extend([
                {"name": "Mentoria", "weight": 0.8, "justification": "Desenvolver outros profissionais"},
                {"name": "Visão Estratégica", "weight": 0.7, "justification": "Pensamento de longo prazo"},
            ])
        elif seniority in ["coordenador", "gerente", "diretor"]:
            base_behavioral.extend([
                {"name": "Liderança", "weight": 1.0, "justification": "Gestão de equipes"},
                {"name": "Tomada de Decisão", "weight": 0.9, "justification": "Responsabilidade decisória"},
                {"name": "Gestão de Conflitos", "weight": 0.8, "justification": "Mediação de equipe"},
            ])
        else:
            base_behavioral.extend([
                {"name": "Proatividade", "weight": 0.8, "justification": "Iniciativa pessoal"},
                {"name": "Aprendizado Contínuo", "weight": 0.8, "justification": "Desenvolvimento constante"},
            ])
        
        return base_behavioral
    
    def _generate_responsibilities(self, title: str, seniority: str) -> list[str]:
        """Generate responsibilities based on title and seniority."""
        base = [
            f"Executar atividades relacionadas a {title.lower()}",
            "Colaborar com equipes multifuncionais",
            "Documentar processos e entregas",
            "Participar de reuniões e alinhamentos",
            "Seguir padrões e melhores práticas da área",
        ]
        
        if seniority in ["senior", "especialista"]:
            base.extend([
                "Orientar profissionais menos experientes",
                "Propor melhorias em processos existentes",
                "Liderar projetos de média complexidade",
            ])
        elif seniority in ["coordenador", "gerente"]:
            base.extend([
                "Gerir equipe e acompanhar entregas",
                "Definir metas e indicadores de performance",
                "Reportar resultados à liderança",
                "Desenvolver e reter talentos da equipe",
            ])
        elif seniority == "diretor":
            base.extend([
                "Definir estratégia da área",
                "Gerir orçamento e recursos",
                "Representar a empresa em fóruns externos",
                "Alinhar objetivos com a diretoria executiva",
            ])
        
        return base
    
    async def _enrich_to_meet_wsi(self, template: JobTemplate) -> JobTemplate:
        """Enrich template to meet WSI minimum requirements."""
        # Ensure skills list exists and has minimum items
        skills = template.default_skills or []
        if not isinstance(skills, list):
            skills = []
        
        # Fill in missing skills with meaningful fallbacks based on title
        skill_suffixes = [
            "Análise",
            "Implementação", 
            "Otimização",
            "Monitoramento",
            "Documentação"
        ]
        
        idx = 0
        while len(skills) < 5:
            skills.append({
                "name": f"{template.title} - {skill_suffixes[idx % len(skill_suffixes)]}",
                "category": "technical",
                "level": "intermediate",
                "weight": 0.7,
                "required": False
            })
            idx += 1
        
        template.default_skills = skills[:10]  # Cap at 10
        
        # Ensure behavioral competencies exist
        behavioral = template.default_behavioral or []
        if not isinstance(behavioral, list):
            behavioral = []
        
        while len(behavioral) < 3:
            behavioral.append({
                "name": f"Competência Comportamental {len(behavioral) + 1}",
                "weight": 0.7,
                "justification": "Competência importante para a função"
            })
        
        template.default_behavioral = behavioral[:10]  # Cap at 10
        
        # Ensure responsibilities exist
        responsibilities = template.default_responsibilities or []
        if not isinstance(responsibilities, list):
            responsibilities = []
        
        while len(responsibilities) < 5:
            responsibilities.append(f"Responsabilidade relacionada a {template.title.lower()}")
        
        template.default_responsibilities = responsibilities[:15]  # Cap at 15
        
        logger.debug(f"Enriched template '{template.title}': {len(template.default_skills)} skills, {len(template.default_behavioral)} behavioral, {len(template.default_responsibilities)} responsibilities")
        
        return template
    
    async def import_bulk_templates(
        self,
        target_count: int = 480
    ) -> dict[str, Any]:
        """
        Import templates in bulk from ESCO to reach target count.
        
        Args:
            target_count: Target number of templates
            
        Returns:
            Import statistics
        """
        stats = {
            "started_at": datetime.utcnow().isoformat(),
            "target_count": target_count,
            "created": 0,
            "failed": 0,
            "by_category": {}
        }
        
        search_terms_by_category = {
            "tecnologia": [
                "software developer", "data analyst", "system administrator",
                "network engineer", "cybersecurity", "cloud architect",
                "devops engineer", "machine learning", "mobile developer"
            ],
            "financas": [
                "financial analyst", "accountant", "auditor",
                "tax specialist", "controller", "treasury"
            ],
            "recursos_humanos": [
                "hr specialist", "recruiter", "training specialist",
                "compensation analyst", "hr manager"
            ],
            "vendas": [
                "sales representative", "account manager", "sales manager",
                "business development", "key account manager"
            ],
            "marketing": [
                "marketing analyst", "digital marketing", "content manager",
                "brand manager", "social media"
            ],
            "operacoes": [
                "operations manager", "supply chain", "logistics coordinator",
                "project manager", "business analyst"
            ],
            "engenharia": [
                "civil engineer", "mechanical engineer", "electrical engineer",
                "production engineer", "quality engineer"
            ],
            "juridico": [
                "lawyer", "legal analyst", "compliance officer",
                "contract specialist"
            ]
        }
        
        for category, terms in search_terms_by_category.items():
            subcategory = "geral"
            category_stats = {"created": 0, "failed": 0}
            
            for term in terms:
                try:
                    templates = await self.import_from_esco(
                        category=category,
                        subcategory=subcategory,
                        search_terms=[term],
                        seniority_levels=["junior", "pleno", "senior"]
                    )
                    category_stats["created"] += len(templates)
                    stats["created"] += len(templates)
                except Exception as e:
                    logger.error(f"Failed to import {term}: {e}")
                    category_stats["failed"] += 1
                    stats["failed"] += 1
                
                await asyncio.sleep(0.3)
                
                if stats["created"] >= target_count:
                    break
            
            stats["by_category"][category] = category_stats
            
            if stats["created"] >= target_count:
                break
        
        stats["completed_at"] = datetime.utcnow().isoformat()
        return stats
    
    async def get_import_status(self) -> dict[str, Any]:
        """Get current template import status."""
        result = await self.db.execute(
            text("""
                SELECT 
                    category,
                    COUNT(*) as count,
                    COUNT(*) FILTER (WHERE is_system = true) as system_count
                FROM job_templates
                WHERE is_active = true
                GROUP BY category
                ORDER BY count DESC
            """)
        )
        
        categories = {}
        total = 0
        for row in result:
            categories[row[0]] = {
                "total": row[1],
                "system": row[2]
            }
            total += row[1]
        
        return {
            "total_templates": total,
            "by_category": categories,
            "target": 480,
            "progress_percent": min(100, (total / 480) * 100)
        }
