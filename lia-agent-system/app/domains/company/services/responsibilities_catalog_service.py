"""
Responsibilities Catalog Service for Job Wizard Enhancement.

Provides a comprehensive catalog of job responsibilities
for automatic suggestion during job vacancy creation.

Features:
- Responsibilities catalog organized by area and seniority
- Role-to-responsibilities mapping for intelligent suggestions
- Fuzzy search for responsibility discovery
- Seniority-based responsibility count adjustments
- Benchmark against similar roles
- Dynamic company-learned responsibilities from database
"""
import logging
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.company.repositories.company_responsibility_repository import (
    CompanyResponsibilityRepository,
)
from lia_models.company_learning import CompanyResponsibility

logger = logging.getLogger(__name__)


RESPONSIBILITIES_CATALOG: dict[str, dict[str, list[str]]] = {
    "engineering": {
        "development": [
            "Desenvolver e manter aplicações de alta performance",
            "Implementar novas funcionalidades seguindo padrões de qualidade",
            "Escrever código limpo, testável e bem documentado",
            "Realizar code review de colegas de equipe",
            "Participar de cerimônias ágeis (daily, planning, retrospectiva)",
            "Debugar e resolver problemas complexos de produção",
            "Colaborar com designers e product managers na definição de soluções",
            "Manter e atualizar documentação técnica"
        ],
        "leadership": [
            "Liderar tecnicamente projetos e squads",
            "Mentoria de desenvolvedores júnior e pleno",
            "Participar de decisões de arquitetura",
            "Definir padrões técnicos e boas práticas da equipe",
            "Conduzir entrevistas técnicas para novas contratações",
            "Garantir qualidade e performance das entregas do time",
            "Facilitar a comunicação entre áreas técnicas e negócio",
            "Planejar roadmap técnico e evolução da arquitetura"
        ],
        "devops": [
            "Gerenciar infraestrutura cloud (AWS/GCP/Azure)",
            "Implementar e manter pipelines de CI/CD",
            "Monitorar sistemas e garantir alta disponibilidade",
            "Automatizar processos de deploy e provisionamento",
            "Gerenciar containers e orquestração (Docker/Kubernetes)",
            "Implementar práticas de segurança e compliance",
            "Otimizar custos de infraestrutura cloud",
            "Responder a incidentes e realizar post-mortems"
        ],
        "data": [
            "Desenvolver e manter pipelines de dados",
            "Modelar dados para análises e relatórios",
            "Criar dashboards e visualizações de dados",
            "Garantir qualidade e governança dos dados",
            "Otimizar queries e performance de banco de dados",
            "Implementar processos de ETL/ELT",
            "Colaborar com áreas de negócio na análise de dados",
            "Documentar modelos de dados e dicionários"
        ]
    },
    "finance": {
        "accounting": [
            "Realizar fechamento contábil mensal e anual",
            "Preparar demonstrações financeiras (DRE, Balanço)",
            "Executar conciliações bancárias e contábeis",
            "Garantir compliance com normas contábeis (IFRS/GAAP)",
            "Atender auditorias internas e externas",
            "Analisar e classificar lançamentos contábeis",
            "Controlar patrimônio e ativos fixos",
            "Elaborar notas explicativas"
        ],
        "fp_a": [
            "Elaborar orçamento anual e forecasts",
            "Analisar variações e desvios orçamentários",
            "Preparar relatórios gerenciais para diretoria",
            "Desenvolver modelos financeiros e projeções",
            "Calcular e monitorar KPIs financeiros",
            "Apoiar decisões estratégicas com análises financeiras",
            "Consolidar resultados de unidades de negócio",
            "Automatizar processos de reporting"
        ],
        "treasury": [
            "Gerenciar fluxo de caixa e liquidez",
            "Executar operações de câmbio e derivativos",
            "Negociar condições com bancos e instituições financeiras",
            "Controlar endividamento e linhas de crédito",
            "Analisar riscos financeiros e de mercado",
            "Gerenciar investimentos e aplicações financeiras",
            "Processar pagamentos e recebimentos",
            "Garantir compliance em operações financeiras"
        ]
    },
    "hr": {
        "recruitment": [
            "Conduzir processos seletivos end-to-end",
            "Realizar entrevistas por competências",
            "Desenvolver estratégias de atração de talentos",
            "Gerenciar pipeline de candidatos no ATS",
            "Elaborar descrições de vaga e anúncios",
            "Negociar ofertas de trabalho com candidatos",
            "Manter relacionamento com consultorias e headhunters",
            "Analisar métricas de recrutamento (time-to-hire, quality of hire)"
        ],
        "development": [
            "Implementar programas de treinamento e desenvolvimento",
            "Conduzir avaliações de desempenho",
            "Elaborar planos de desenvolvimento individual (PDI)",
            "Gerenciar programas de mentoria e coaching",
            "Desenvolver trilhas de carreira",
            "Facilitar feedbacks 360 graus",
            "Medir e melhorar engajamento dos colaboradores",
            "Coordenar onboarding de novos colaboradores"
        ],
        "compensation": [
            "Administrar política de remuneração e benefícios",
            "Realizar pesquisas salariais de mercado",
            "Elaborar estrutura de cargos e salários",
            "Gerenciar programas de incentivo (PLR, bônus)",
            "Administrar benefícios flexíveis",
            "Garantir compliance trabalhista",
            "Analisar custos de pessoal e orçamento de RH",
            "Implementar programas de reconhecimento"
        ]
    },
    "marketing": {
        "digital": [
            "Planejar e executar campanhas digitais",
            "Gerenciar mídia paga (Google Ads, Meta Ads)",
            "Analisar métricas e performance de campanhas",
            "Implementar estratégias de SEO/SEM",
            "Gerenciar presença em redes sociais",
            "Desenvolver estratégias de growth hacking",
            "Criar landing pages e materiais de conversão",
            "Automatizar jornadas de marketing (nurturing)"
        ],
        "content": [
            "Desenvolver estratégia de conteúdo",
            "Produzir conteúdo para blog, redes sociais e email",
            "Gerenciar calendário editorial",
            "Coordenar produção de materiais ricos (ebooks, webinars)",
            "Garantir tom de voz e branding consistente",
            "Analisar performance de conteúdo",
            "Otimizar conteúdo para SEO",
            "Coordenar produção audiovisual"
        ],
        "product_marketing": [
            "Desenvolver posicionamento e mensagens de produto",
            "Criar materiais de sales enablement",
            "Conduzir análises de mercado e concorrência",
            "Planejar lançamentos de produto (go-to-market)",
            "Desenvolver cases de sucesso e testimonials",
            "Definir pricing e estratégia de monetização",
            "Treinar equipe de vendas sobre produtos",
            "Coletar e analisar feedback de clientes"
        ]
    },
    "sales": {
        "inside_sales": [
            "Prospectar e qualificar leads",
            "Conduzir apresentações e demos de produto",
            "Gerenciar pipeline de vendas no CRM",
            "Negociar e fechar contratos",
            "Elaborar propostas comerciais",
            "Manter relacionamento com clientes da carteira",
            "Atingir metas de vendas mensais/trimestrais",
            "Participar de treinamentos e capacitações"
        ],
        "account_management": [
            "Gerenciar carteira de clientes estratégicos",
            "Identificar oportunidades de upsell e cross-sell",
            "Conduzir QBRs (Quarterly Business Reviews)",
            "Garantir renovação de contratos",
            "Resolver escalações e problemas de clientes",
            "Desenvolver planos de conta estratégicos",
            "Coordenar entregas com equipes internas",
            "Monitorar saúde da conta e NPS"
        ],
        "leadership": [
            "Gerenciar equipe de vendas",
            "Definir e acompanhar metas do time",
            "Desenvolver e capacitar vendedores",
            "Elaborar forecast de vendas",
            "Otimizar processos comerciais",
            "Analisar pipeline e métricas de vendas",
            "Participar de negociações estratégicas",
            "Reportar resultados para diretoria"
        ]
    }
}


SENIORITY_RESPONSIBILITIES: dict[str, dict[str, Any]] = {
    "junior": {
        "focus": ["execução", "aprendizado", "suporte"],
        "keywords": ["apoiar", "auxiliar", "aprender", "executar", "participar"],
        "min_count": 3,
        "max_count": 6,
        "typical_responsibilities": [
            "Apoiar na execução de tarefas sob supervisão",
            "Participar de treinamentos e capacitações",
            "Documentar processos e procedimentos",
            "Colaborar com a equipe em projetos",
            "Aprender ferramentas e tecnologias da área"
        ]
    },
    "pleno": {
        "focus": ["execução autônoma", "colaboração", "qualidade"],
        "keywords": ["desenvolver", "executar", "analisar", "colaborar", "implementar"],
        "min_count": 5,
        "max_count": 8,
        "typical_responsibilities": [
            "Executar tarefas de forma autônoma",
            "Colaborar com diferentes áreas e stakeholders",
            "Propor melhorias em processos existentes",
            "Garantir qualidade das entregas",
            "Compartilhar conhecimento com a equipe"
        ]
    },
    "senior": {
        "focus": ["liderança técnica", "mentoria", "arquitetura"],
        "keywords": ["liderar", "mentoria", "arquitetura", "definir", "garantir", "estratégico"],
        "min_count": 6,
        "max_count": 10,
        "typical_responsibilities": [
            "Liderar tecnicamente projetos e iniciativas",
            "Mentoria de profissionais mais júniors",
            "Participar de decisões estratégicas da área",
            "Definir padrões e boas práticas",
            "Garantir qualidade e performance das entregas",
            "Colaborar com liderança na definição de roadmap"
        ]
    },
    "lead": {
        "focus": ["gestão técnica", "estratégia", "pessoas"],
        "keywords": ["gerenciar", "coordenar", "estratégia", "equipe", "roadmap", "arquitetura"],
        "min_count": 8,
        "max_count": 12,
        "typical_responsibilities": [
            "Gerenciar equipe técnica",
            "Definir arquitetura e roadmap técnico",
            "Conduzir entrevistas e contratações",
            "Garantir entregas e qualidade do time",
            "Representar a área em fóruns estratégicos",
            "Desenvolver e reter talentos",
            "Gerenciar stakeholders e expectativas",
            "Promover cultura de inovação e melhoria contínua"
        ]
    },
    "manager": {
        "focus": ["gestão de pessoas", "resultados", "estratégia"],
        "keywords": ["gerenciar", "liderar", "resultados", "estratégia", "budget", "kpis"],
        "min_count": 8,
        "max_count": 12,
        "typical_responsibilities": [
            "Gerenciar equipe e resultados da área",
            "Definir metas e acompanhar KPIs",
            "Elaborar e gerenciar orçamento da área",
            "Desenvolver e avaliar performance do time",
            "Participar de decisões estratégicas",
            "Reportar resultados para diretoria",
            "Gerenciar projetos e iniciativas da área",
            "Garantir compliance e governança"
        ]
    }
}


ROLE_RESPONSIBILITIES_MAPPING: dict[str, dict[str, Any]] = {
    "desenvolvedor backend": {"area": "engineering", "category": "development"},
    "desenvolvedor frontend": {"area": "engineering", "category": "development"},
    "desenvolvedor fullstack": {"area": "engineering", "category": "development"},
    "desenvolvedor python": {"area": "engineering", "category": "development"},
    "desenvolvedor java": {"area": "engineering", "category": "development"},
    "desenvolvedor node": {"area": "engineering", "category": "development"},
    "engenheiro de dados": {"area": "engineering", "category": "data"},
    "engenheiro devops": {"area": "engineering", "category": "devops"},
    "sre": {"area": "engineering", "category": "devops"},
    "cientista de dados": {"area": "engineering", "category": "data"},
    "tech lead": {"area": "engineering", "category": "leadership"},
    "arquiteto de software": {"area": "engineering", "category": "leadership"},
    "analista contábil": {"area": "finance", "category": "accounting"},
    "contador": {"area": "finance", "category": "accounting"},
    "analista financeiro": {"area": "finance", "category": "fp_a"},
    "controller": {"area": "finance", "category": "fp_a"},
    "tesoureiro": {"area": "finance", "category": "treasury"},
    "analista de rh": {"area": "hr", "category": "recruitment"},
    "recrutador": {"area": "hr", "category": "recruitment"},
    "business partner": {"area": "hr", "category": "development"},
    "analista de t&d": {"area": "hr", "category": "development"},
    "analista de cargos e salários": {"area": "hr", "category": "compensation"},
    "analista de marketing": {"area": "marketing", "category": "digital"},
    "analista de marketing digital": {"area": "marketing", "category": "digital"},
    "redator": {"area": "marketing", "category": "content"},
    "copywriter": {"area": "marketing", "category": "content"},
    "product marketing manager": {"area": "marketing", "category": "product_marketing"},
    "sdr": {"area": "sales", "category": "inside_sales"},
    "vendedor": {"area": "sales", "category": "inside_sales"},
    "account executive": {"area": "sales", "category": "inside_sales"},
    "customer success": {"area": "sales", "category": "account_management"},
    "key account manager": {"area": "sales", "category": "account_management"},
    "gerente comercial": {"area": "sales", "category": "leadership"},
    "gerente de vendas": {"area": "sales", "category": "leadership"}
}


@dataclass
class ResponsibilitySuggestion:
    """Represents a responsibility suggestion with metadata."""
    description: str
    category: str
    area: str
    seniority_fit: str
    relevance_score: float = 1.0


class ResponsibilitiesCatalogService:
    """
    Service for managing and querying the responsibilities catalog.
    
    Provides intelligent responsibility suggestions based on role, seniority,
    and company context for the job wizard enhancement.
    """
    
    FUZZY_MATCH_THRESHOLD = 0.6
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def normalize_role(self, role: str) -> str:
        """Normalize a job role/title for matching against the catalog."""
        if not role:
            return ""
        
        normalized = role.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        replacements = {
            "desenvolvedor(a)": "desenvolvedor",
            "analista de ti": "desenvolvedor",
            "programador": "desenvolvedor",
            "software engineer": "desenvolvedor",
            "dev ": "desenvolvedor ",
            "engenheiro(a)": "engenheiro",
            "gerente de": "gerente",
            "coordenador(a)": "coordenador",
            "analista sr": "analista senior",
            "analista pl": "analista pleno",
            "analista jr": "analista junior",
        }
        
        for pattern, replacement in replacements.items():
            normalized = normalized.replace(pattern, replacement)
        
        return normalized.strip()
    
    def normalize_seniority(self, seniority: str) -> str:
        """Normalize seniority level for matching."""
        if not seniority:
            return "pleno"
        
        seniority = seniority.lower().strip()
        
        mapping = {
            "jr": "junior",
            "júnior": "junior",
            "pl": "pleno",
            "mid": "pleno",
            "sr": "senior",
            "sênior": "senior",
            "líder": "lead",
            "tech lead": "lead",
            "coordenador": "manager",
            "gerente": "manager",
            "manager": "manager",
            "diretor": "manager",
            "director": "manager"
        }
        
        return mapping.get(seniority, seniority)
    
    def _fuzzy_match_role(self, role: str) -> str | None:
        """Find the best matching role in the catalog using fuzzy matching."""
        if not role:
            return None
        
        best_match = None
        best_score = 0.0
        
        for catalog_role in ROLE_RESPONSIBILITIES_MAPPING.keys():
            score = SequenceMatcher(None, role, catalog_role).ratio()
            if score > best_score and score >= self.FUZZY_MATCH_THRESHOLD:
                best_score = score
                best_match = catalog_role
        
        return best_match
    
    def get_expected_responsibilities(
        self,
        role: str,
        seniority: str,
        detected_responsibilities: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Get expected responsibilities for a role and seniority level.
        
        Args:
            role: Job role/title
            seniority: Seniority level (junior, pleno, senior, lead, manager)
            detected_responsibilities: List of responsibilities already detected
            
        Returns:
            Dict with expected, detected, missing responsibilities and completeness score
        """
        normalized_role = self.normalize_role(role)
        normalized_seniority = self.normalize_seniority(seniority)
        detected = detected_responsibilities or []
        
        role_mapping = ROLE_RESPONSIBILITIES_MAPPING.get(normalized_role)
        if not role_mapping:
            role_mapping = self._fuzzy_match_role(normalized_role)
            if role_mapping:
                role_mapping = ROLE_RESPONSIBILITIES_MAPPING.get(role_mapping)
        
        expected_responsibilities = []
        
        if role_mapping:
            area = role_mapping.get("area", "engineering")
            category = role_mapping.get("category", "development")
            
            area_catalog = RESPONSIBILITIES_CATALOG.get(area, {})
            category_responsibilities = area_catalog.get(category, [])
            expected_responsibilities.extend(category_responsibilities)
        
        seniority_config = SENIORITY_RESPONSIBILITIES.get(
            normalized_seniority, 
            SENIORITY_RESPONSIBILITIES.get("pleno", {})
        )
        typical_responsibilities = seniority_config.get("typical_responsibilities", [])
        
        for resp in typical_responsibilities:
            if resp not in expected_responsibilities:
                expected_responsibilities.append(resp)
        
        min_count = seniority_config.get("min_count", 5)
        max_count = seniority_config.get("max_count", 8)
        
        missing_responsibilities = []
        matched_detected = []
        
        for expected in expected_responsibilities:
            is_matched = False
            for det in detected:
                if self._responsibilities_match(det, expected):
                    is_matched = True
                    if det not in matched_detected:
                        matched_detected.append(det)
                    break
            
            if not is_matched:
                missing_responsibilities.append(expected)
        
        total_expected = len(expected_responsibilities)
        total_detected = len(matched_detected)
        completeness_score = int((total_detected / total_expected * 100) if total_expected > 0 else 0)
        
        validation_status = "ok"
        validation_message = ""
        
        if total_detected < min_count:
            validation_status = "warning"
            validation_message = f"⚠️ Detectadas apenas {total_detected}/{min_count} responsabilidades mínimas para {normalized_seniority.title()}"
        elif total_detected > max_count:
            validation_status = "info"
            validation_message = f"ℹ️ Detectadas {total_detected} responsabilidades (máximo recomendado: {max_count})"
        
        return {
            "role": role,
            "seniority": normalized_seniority,
            "expected_responsibilities": expected_responsibilities[:max_count],
            "detected_responsibilities": matched_detected,
            "missing_responsibilities": missing_responsibilities[:5],
            "completeness_score": completeness_score,
            "min_count": min_count,
            "max_count": max_count,
            "validation": {
                "status": validation_status,
                "message": validation_message
            }
        }
    
    def _responsibilities_match(self, detected: str, expected: str) -> bool:
        """Check if a detected responsibility matches an expected one."""
        if not detected or not expected:
            return False
        
        detected_lower = detected.lower().strip()
        expected_lower = expected.lower().strip()
        
        if detected_lower in expected_lower or expected_lower in detected_lower:
            return True
        
        score = SequenceMatcher(None, detected_lower, expected_lower).ratio()
        return score >= 0.5
    
    def suggest_responsibilities(
        self,
        role: str,
        seniority: str,
        limit: int = 5
    ) -> list[ResponsibilitySuggestion]:
        """
        Suggest responsibilities for a role and seniority level.
        
        Args:
            role: Job role/title
            seniority: Seniority level
            limit: Maximum number of suggestions
            
        Returns:
            List of ResponsibilitySuggestion objects
        """
        result = self.get_expected_responsibilities(role, seniority, [])
        suggestions = []
        
        for resp in result.get("missing_responsibilities", [])[:limit]:
            suggestions.append(ResponsibilitySuggestion(
                description=resp,
                category=ROLE_RESPONSIBILITIES_MAPPING.get(
                    self.normalize_role(role), {}
                ).get("category", "general"),
                area=ROLE_RESPONSIBILITIES_MAPPING.get(
                    self.normalize_role(role), {}
                ).get("area", "general"),
                seniority_fit=result.get("seniority", "pleno"),
                relevance_score=1.0
            ))
        
        return suggestions
    
    async def _get_company_responsibilities(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None
    ) -> list[str]:
        """
        Retrieve company-learned responsibilities from the database.
        
        Queries the CompanyResponsibility table for responsibilities that have been
        promoted (times_confirmed >= 3) for the given company, optionally filtered by role.
        
        Args:
            db: AsyncSession database connection
            company_id: Company ID to filter by
            role: Optional role to filter responsibilities by role_associated
            
        Returns:
            List of responsibility descriptions
        """
        try:
            company_responsibilities = await CompanyResponsibilityRepository(
                db
            ).list_promoted_for_company(company_id)
            
            descriptions = []
            for resp in company_responsibilities:
                if role:
                    normalized_role = self.normalize_role(role)
                    roles_list = list(resp.roles_associated) if resp.roles_associated else []  # type: ignore[union-attr]
                    if roles_list:
                        role_matches = any(
                            self.normalize_role(str(r)) == normalized_role
                            for r in roles_list
                        )
                        if not role_matches:
                            continue
                
                descriptions.append(resp.description)
            
            return descriptions
            
        except Exception as e:
            self.logger.error(
                f"Error getting company responsibilities for {company_id}: {e}"
            )
            return []
    
    async def suggest_responsibilities_with_learning(
        self,
        db: AsyncSession,
        company_id: str,
        role: str,
        seniority: str,
        limit: int = 5
    ) -> dict[str, Any]:
        """
        Suggest responsibilities merging company-learned and static catalog responsibilities.
        
        This method combines:
        1. Company-learned responsibilities (promoted with times_confirmed >= 3)
        2. Static catalog responsibilities for the role and seniority
        
        Company-learned responsibilities are prioritized in the suggestions.
        
        Args:
            db: AsyncSession database connection
            company_id: Company ID to query learning data for
            role: Job role/title
            seniority: Seniority level (junior, pleno, senior, lead, manager)
            limit: Maximum number of suggestions to return
            
        Returns:
            Dict with:
                - suggestions: List of ResponsibilitySuggestion objects
                - company_learned_responsibilities: List of company-learned descriptions
                - has_company_learning: Boolean indicating if company has learned data
        """
        try:
            company_responsibilities = await self._get_company_responsibilities(
                db, company_id, role
            )
            
            static_suggestions = self.suggest_responsibilities(role, seniority, limit)
            
            normalized_role = self.normalize_role(role)
            normalized_seniority = self.normalize_seniority(seniority)
            
            role_mapping = ROLE_RESPONSIBILITIES_MAPPING.get(normalized_role, {})
            category = role_mapping.get("category", "general")
            area = role_mapping.get("area", "general")
            
            suggestions = []
            used_descriptions = set()
            
            for company_resp in company_responsibilities[:limit]:
                if company_resp not in used_descriptions:
                    suggestions.append(ResponsibilitySuggestion(
                        description=company_resp,
                        category=category,
                        area=area,
                        seniority_fit=normalized_seniority,
                        relevance_score=1.0
                    ))
                    used_descriptions.add(company_resp)
            
            for static_sugg in static_suggestions:
                if len(suggestions) >= limit:
                    break
                if static_sugg.description not in used_descriptions:
                    suggestions.append(static_sugg)
                    used_descriptions.add(static_sugg.description)
            
            return {
                "suggestions": suggestions,
                "company_learned_responsibilities": company_responsibilities,
                "has_company_learning": len(company_responsibilities) > 0,
                "role": role,
                "seniority": normalized_seniority,
                "company_id": company_id
            }
            
        except Exception as e:
            self.logger.error(
                f"Error in suggest_responsibilities_with_learning "
                f"for {company_id}/{role}/{seniority}: {e}"
            )
            static_suggestions = self.suggest_responsibilities(role, seniority, limit)
            return {
                "suggestions": static_suggestions,
                "company_learned_responsibilities": [],
                "has_company_learning": False,
                "role": role,
                "seniority": self.normalize_seniority(seniority),
                "company_id": company_id,
                "error": str(e)
            }
    
    def validate_responsibilities_count(
        self,
        responsibilities: list[str],
        seniority: str
    ) -> dict[str, Any]:
        """
        Validate if the number of responsibilities is appropriate for the seniority.
        
        Args:
            responsibilities: List of responsibilities
            seniority: Seniority level
            
        Returns:
            Validation result with status and message
        """
        normalized_seniority = self.normalize_seniority(seniority)
        seniority_config = SENIORITY_RESPONSIBILITIES.get(
            normalized_seniority,
            SENIORITY_RESPONSIBILITIES.get("pleno", {})
        )
        
        min_count = seniority_config.get("min_count", 5)
        max_count = seniority_config.get("max_count", 8)
        count = len(responsibilities)
        
        if count < min_count:
            return {
                "status": "warning",
                "message": f"⚠️ Poucas responsabilidades para {normalized_seniority.title()}. Mínimo recomendado: {min_count}",
                "current_count": count,
                "min_count": min_count,
                "max_count": max_count
            }
        elif count > max_count:
            return {
                "status": "info",
                "message": f"ℹ️ Muitas responsabilidades listadas ({count}). Considere focar nas mais importantes.",
                "current_count": count,
                "min_count": min_count,
                "max_count": max_count
            }
        else:
            return {
                "status": "ok",
                "message": f"✅ Número adequado de responsabilidades para {normalized_seniority.title()}",
                "current_count": count,
                "min_count": min_count,
                "max_count": max_count
            }


responsibilities_catalog_service = ResponsibilitiesCatalogService()
