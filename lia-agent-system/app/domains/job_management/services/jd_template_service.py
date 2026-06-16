
"""
Job Description Template Service

Gera duas versões de Job Description:
- Preview (v1): Para validação após coleta inicial, com indicadores de sugestão
- Final (v2): Versão completa para publicação

Todos os textos em Português (Brasil).
"""
import logging
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.domains.job_management.services.interview_stage_defaults import (
    get_default_jd_interview_stages,
    map_pipeline_to_jd_stages,
)
from app.schemas.job_description import (
    CompanyInfo,
    CompensationData,
    Competency,
    ContractType,
    HiringManager,
    InterviewStage,
    JDFinalResponse,
    JDGenerationRequest,
    JDPreviewResponse,
    JobDescriptionFinal,
    JobDescriptionPreview,
    JobMetadata,
    RequirementLevel,
    Responsibility,
    SuggestionSource,
    WorkModel,
)
from app.shared.services.skills_catalog_service import skills_catalog_service

logger = logging.getLogger(__name__)


JD_SECTION_TITLES = {
    "about": "Sobre a Empresa",
    "the_role": "A Vaga",
    "what_you_will_do": "O Que Você Vai Fazer",
    "what_we_are_looking_for": "O Que Buscamos",
    "required": "Requisitos Obrigatórios",
    "nice_to_have": "Diferenciais",
    "technical": "Competências Técnicas",
    "behavioral": "Competências Comportamentais",
    "why_join_us": "Por Que Trabalhar Conosco?",
    "compensation": "Remuneração",
    "benefits": "Benefícios",
    "our_values": "Nossos Valores",
    "interview_process": "Processo Seletivo",
    "diversity": "Diversidade e Inclusão",
    "apply": "Como se Candidatar",
    "questions": "Dúvidas?",
}

WORK_MODEL_LABELS = {
    WorkModel.REMOTE: "100% Remoto",
    WorkModel.HYBRID: "Híbrido",
    WorkModel.ONSITE: "Presencial",
}

CONTRACT_TYPE_LABELS = {
    ContractType.CLT: "CLT",
    ContractType.PJ: "PJ",
    ContractType.ESTAGIO: "Estágio",
    ContractType.TEMPORARIO: "Temporário",
    ContractType.FREELANCER: "Freelancer",
}

SUGGESTION_INDICATOR = "💡"
ALERT_INDICATOR = "⚠️"
NEW_INDICATOR = "✨"


class JDTemplateService:
    """
    Serviço para geração de Job Descriptions em duas versões.
    
    Features:
    - Integração com SkillsCatalogService para sugestões
    - Geração de Markdown e HTML formatados
    - Indicadores visuais de sugestões da LIA
    - Suporte a vaga afirmativa
    - Cálculo de timeline do processo
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def generate_preview(
        self,
        request: JDGenerationRequest,
        include_suggestions: bool = True
    ) -> JDPreviewResponse:
        """
        Gera JD Preview (v1) para validação.
        
        Inclui indicadores de sugestões da LIA (💡) para itens novos.
        Não inclui Interview Process.
        """
        try:
            responsibilities = self._build_responsibilities(
                detected=request.detected_responsibilities,
                role=request.title,
                seniority=request.seniority,
                include_suggestions=include_suggestions
            )
            
            technical, behavioral = self._build_competencies(
                detected_technical=request.detected_technical_skills,
                detected_behavioral=request.detected_behavioral_skills,
                role=request.title,
                seniority=request.seniority,
                include_suggestions=include_suggestions
            )
            
            compensation = self._build_compensation(
                salary_min=request.salary_min,
                salary_max=request.salary_max,
                bonus_percentage=request.bonus_percentage,
                company_id=request.company_id,
                role=request.title,
                seniority=request.seniority
            )
            
            company = await self._get_company_info(request.company_id)
            
            suggestions_count = sum(1 for r in responsibilities if r.is_new)
            suggestions_count += sum(1 for c in technical if c.is_new)
            suggestions_count += sum(1 for c in behavioral if c.is_new)
            
            alerts = []
            alerts_count = 0
            if compensation and compensation.has_alert:
                alerts.append(compensation.alert_message or "Alerta de compensação")
                alerts_count += 1
            
            total_fields = 10
            filled_fields = sum([
                bool(request.title),
                bool(request.department),
                bool(request.seniority),
                bool(request.location),
                len(responsibilities) > 0,
                len(technical) > 0,
                len(behavioral) > 0,
                bool(request.salary_min),
                bool(request.description),
                bool(company),
            ])
            completeness_score = filled_fields / total_fields
            
            preview = JobDescriptionPreview(
                title=request.title,
                department=request.department,
                seniority=request.seniority,
                num_positions=request.num_positions,
                work_model=request.work_model,
                office_days_per_week=request.office_days_per_week,
                contract_type=request.contract_type,
                location=request.location,
                is_affirmative=request.is_affirmative,
                affirmative_type=request.affirmative_type,
                description=request.description,
                responsibilities=responsibilities,
                technical_competencies=technical,
                behavioral_competencies=behavioral,
                compensation=compensation,
                company=company,
                suggestions_count=suggestions_count,
                alerts_count=alerts_count,
                completeness_score=completeness_score,
            )
            
            markdown = self._render_preview_markdown(preview)
            
            return JDPreviewResponse(
                success=True,
                preview=preview,
                markdown=markdown,
                suggestions_applied=suggestions_count,
                alerts=alerts,
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar preview: {e}")
            return JDPreviewResponse(
                success=False,
                error=str(e)
            )
    
    async def generate_final(
        self,
        request: JDGenerationRequest,
        confirmed_responsibilities: list[str] | None = None,
        confirmed_technical: list[str] | None = None,
        confirmed_behavioral: list[str] | None = None,
        confirmed_nice_to_have: list[str] | None = None,
    ) -> JDFinalResponse:
        """
        Gera JD Final (v2) para publicação.
        
        Versão limpa sem indicadores de sugestão.
        Inclui Interview Process, Apply At, etc.
        """
        try:
            responsibilities = confirmed_responsibilities or request.detected_responsibilities
            required_technical = confirmed_technical or request.detected_technical_skills
            required_behavioral = confirmed_behavioral or request.detected_behavioral_skills
            nice_to_have = confirmed_nice_to_have or []
            
            compensation = self._build_compensation(
                salary_min=request.salary_min,
                salary_max=request.salary_max,
                bonus_percentage=request.bonus_percentage,
                company_id=request.company_id,
                role=request.title,
                seniority=request.seniority
            )
            
            company = await self._get_company_info(request.company_id)
            
            interview_process = request.interview_stages or await self._get_company_interview_stages(request.company_id)
            total_timeline = self._calculate_timeline(interview_process)
            
            metadata = None
            if request.hiring_manager_name:
                metadata = JobMetadata(
                    hiring_manager=HiringManager(
                        name=request.hiring_manager_name,
                        email=request.hiring_manager_email or "",
                        department=request.department,
                    ),
                    is_confidential=request.is_confidential,
                    priority=request.priority,
                    open_date=datetime.utcnow(),
                    target_date=request.target_date,
                )
            
            missing_fields = []
            if not responsibilities:
                missing_fields.append("responsabilidades")
            if not required_technical:
                missing_fields.append("competências técnicas")
            if not request.location:
                missing_fields.append("localização")
            
            ready_to_publish = len(missing_fields) == 0
            
            final = JobDescriptionFinal(
                title=request.title,
                department=request.department,
                seniority=request.seniority,
                num_positions=request.num_positions,
                work_model=request.work_model,
                office_days_per_week=request.office_days_per_week,
                contract_type=request.contract_type,
                location=request.location,
                is_affirmative=request.is_affirmative,
                affirmative_type=request.affirmative_type,
                description=request.description,
                responsibilities=responsibilities,
                required_technical=required_technical,
                required_behavioral=required_behavioral,
                nice_to_have=nice_to_have,
                compensation=compensation,
                company=company,
                interview_process=interview_process,
                total_timeline=total_timeline,
                apply_url=company.careers_url if company else None,
                contact_email=company.contact_email if company else None,
                metadata=metadata,
            )
            
            markdown = self._render_final_markdown(final)
            html = self._render_final_html(final)
            
            return JDFinalResponse(
                success=True,
                final=final,
                markdown=markdown,
                html=html,
                ready_to_publish=ready_to_publish,
                missing_fields=missing_fields,
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar JD final: {e}")
            return JDFinalResponse(
                success=False,
                error=str(e)
            )
    
    def _build_responsibilities(
        self,
        detected: list[str],
        role: str,
        seniority: str | None,
        include_suggestions: bool = True
    ) -> list[Responsibility]:
        """Constrói lista de responsabilidades com sugestões."""
        responsibilities = []
        
        for resp in detected:
            responsibilities.append(Responsibility(
                description=resp,
                source=SuggestionSource.DETECTED,
                is_new=False,
            ))
        
        if include_suggestions:
            suggested = self._get_suggested_responsibilities(role, seniority)
            for resp in suggested:
                if not any(r.description.lower() == resp.lower() for r in responsibilities):
                    responsibilities.append(Responsibility(
                        description=resp,
                        source=SuggestionSource.LIA_CATALOG,
                        is_new=True,
                    ))
        
        return responsibilities
    
    def _get_suggested_responsibilities(
        self,
        role: str,
        seniority: str | None
    ) -> list[str]:
        """Retorna responsabilidades sugeridas baseadas no cargo."""
        seniority_lower = (seniority or "").lower()
        role_lower = role.lower()
        
        base_responsibilities = []
        
        if "desenvolv" in role_lower or "dev" in role_lower or "engineer" in role_lower:
            base_responsibilities = [
                "Desenvolver e manter aplicações de alta qualidade",
                "Participar de code reviews e garantir boas práticas",
                "Colaborar com times de produto e design",
                "Documentar soluções técnicas",
            ]
            if "senior" in seniority_lower or "sênior" in seniority_lower:
                base_responsibilities.extend([
                    "Liderar decisões técnicas do squad",
                    "Mentoria de desenvolvedores mais juniores",
                    "Definir arquitetura de novas funcionalidades",
                ])
            if "lead" in seniority_lower or "líder" in seniority_lower:
                base_responsibilities.extend([
                    "Gerenciar prioridades técnicas do time",
                    "Facilitar cerimônias ágeis",
                    "Reportar progresso para stakeholders",
                ])
        
        elif "product" in role_lower or "produto" in role_lower:
            base_responsibilities = [
                "Definir roadmap e priorização de features",
                "Conduzir discovery com usuários",
                "Escrever histórias de usuário e critérios de aceite",
                "Acompanhar métricas de produto",
            ]
        
        elif "design" in role_lower or "ux" in role_lower or "ui" in role_lower:
            base_responsibilities = [
                "Criar wireframes, protótipos e designs de alta fidelidade",
                "Conduzir pesquisas com usuários",
                "Contribuir para o design system",
                "Colaborar com desenvolvedores na implementação",
            ]
        
        elif "dados" in role_lower or "data" in role_lower:
            base_responsibilities = [
                "Desenvolver pipelines de dados",
                "Criar dashboards e relatórios",
                "Garantir qualidade e governança dos dados",
                "Colaborar com times de negócio",
            ]
        
        elif "rh" in role_lower or "recursos humanos" in role_lower or "people" in role_lower:
            base_responsibilities = [
                "Conduzir processos de recrutamento e seleção",
                "Desenvolver programas de treinamento e desenvolvimento",
                "Acompanhar indicadores de RH",
                "Promover cultura organizacional",
            ]
        
        elif "vendas" in role_lower or "sales" in role_lower or "comercial" in role_lower:
            base_responsibilities = [
                "Prospectar e qualificar leads",
                "Conduzir reuniões e apresentações comerciais",
                "Gerenciar pipeline de vendas",
                "Negociar e fechar contratos",
            ]
        
        elif "marketing" in role_lower:
            base_responsibilities = [
                "Planejar e executar campanhas de marketing",
                "Analisar métricas e performance de campanhas",
                "Gerenciar canais de comunicação",
                "Desenvolver estratégias de conteúdo",
            ]
        
        else:
            base_responsibilities = [
                "Executar atividades da área com excelência",
                "Colaborar com times multidisciplinares",
                "Propor melhorias nos processos",
                "Reportar resultados e indicadores",
            ]
        
        return base_responsibilities[:4]
    
    def _build_competencies(
        self,
        detected_technical: list[str],
        detected_behavioral: list[str],
        role: str,
        seniority: str | None,
        include_suggestions: bool = True
    ) -> tuple[list[Competency], list[Competency]]:
        """Constrói listas de competências técnicas e comportamentais."""
        technical = []
        behavioral = []
        
        for skill in detected_technical:
            technical.append(Competency(
                name=skill,
                level=RequirementLevel.REQUIRED,
                source=SuggestionSource.DETECTED,
                is_new=False,
            ))
        
        for skill in detected_behavioral:
            behavioral.append(Competency(
                name=skill,
                level=RequirementLevel.REQUIRED,
                source=SuggestionSource.DETECTED,
                is_new=False,
            ))
        
        if include_suggestions:
            catalog_result = skills_catalog_service.suggest_skills(
                role=role,
                seniority=seniority,
                limit=8
            )
            
            for skill in catalog_result.get("technical_skills", []):
                if not any(t.name.lower() == skill.lower() for t in technical):
                    technical.append(Competency(
                        name=skill,
                        level=RequirementLevel.NICE_TO_HAVE,
                        source=SuggestionSource.LIA_CATALOG,
                        is_new=True,
                    ))
            
            for comp in catalog_result.get("behavioral_competencies", []):
                comp_name = comp.get("name", comp) if isinstance(comp, dict) else comp
                if not any(b.name.lower() == comp_name.lower() for b in behavioral):
                    behavioral.append(Competency(
                        name=comp_name,
                        level=RequirementLevel.REQUIRED,
                        source=SuggestionSource.LIA_CATALOG,
                        is_new=True,
                    ))
        
        return technical, behavioral
    
    def _build_compensation(
        self,
        salary_min: float | None,
        salary_max: float | None,
        bonus_percentage: float | None,
        company_id: str,
        role: str,
        seniority: str | None,
    ) -> CompensationData:
        """Constrói dados de compensação com análise de mercado."""
        has_alert = False
        alert_message = None
        market_comparison = None
        market_percentile = None
        
        if salary_min and salary_max:
            avg_salary = (salary_min + salary_max) / 2
            
            estimated_market = self._estimate_market_salary(role, seniority)
            if estimated_market:
                market_min, market_max = estimated_market
                market_avg = (market_min + market_max) / 2
                
                if avg_salary < market_min:
                    has_alert = True
                    diff_percent = ((market_min - avg_salary) / market_avg) * 100
                    alert_message = f"Salário {diff_percent:.0f}% abaixo do mercado"
                    market_comparison = "abaixo"
                    market_percentile = 25
                elif avg_salary > market_max:
                    market_comparison = "acima"
                    market_percentile = 90
                else:
                    position = (avg_salary - market_min) / (market_max - market_min)
                    market_percentile = int(25 + (position * 50))
                    market_comparison = "alinhado"
        
        return CompensationData(
            salary_min=salary_min,
            salary_max=salary_max,
            bonus_percentage=bonus_percentage,
            has_alert=has_alert,
            alert_message=alert_message,
            market_comparison=market_comparison,
            market_percentile=market_percentile,
        )
    
    def _estimate_market_salary(
        self,
        role: str,
        seniority: str | None
    ) -> tuple[float, float] | None:
        """Estimativa rápida de faixa salarial de mercado."""
        base_ranges = {
            "junior": (4000, 7000),
            "júnior": (4000, 7000),
            "pleno": (7000, 12000),
            "senior": (12000, 20000),
            "sênior": (12000, 20000),
            "lead": (18000, 28000),
            "líder": (18000, 28000),
            "gerente": (20000, 35000),
            "diretor": (30000, 50000),
        }
        
        seniority_key = (seniority or "pleno").lower()
        base = base_ranges.get(seniority_key, (8000, 15000))
        
        tech_keywords = ["desenvolv", "engineer", "data", "devops", "cloud", "arquiteto"]
        role_lower = role.lower()
        
        if any(kw in role_lower for kw in tech_keywords):
            return (int(base[0] * 1.2), int(base[1] * 1.3))
        
        return base
    
    async def _get_company_info(self, company_id: str) -> CompanyInfo | None:
        """Obtém informações da empresa do serviço de configuração."""
        try:
            return CompanyInfo(
                name="[Nome da Empresa]",
                about="[Descrição da empresa - missão, produto, clientes]",
                values=[
                    {"name": "Inovação", "description": "Buscamos sempre novas soluções"},
                    {"name": "Colaboração", "description": "Trabalhamos juntos para alcançar resultados"},
                    {"name": "Excelência", "description": "Compromisso com a qualidade"},
                ],
                evp={
                    "impact": "Seu trabalho impactará milhares de usuários",
                    "growth": "Investimento em desenvolvimento profissional",
                    "team": "Equipe colaborativa e inovadora",
                    "flexibility": "Flexibilidade de horários e local de trabalho",
                    "benefits": "Pacote completo de benefícios",
                },
                diversity_statement="Valorizamos a diversidade e promovemos um ambiente inclusivo para todas as pessoas, independente de gênero, raça, orientação sexual, deficiência ou qualquer outra característica.",
                careers_url="https://careers.empresa.com",
                contact_email="vagas@empresa.com",
            )
        except Exception as e:
            self.logger.warning(f"Erro ao obter info da empresa: {e}")
            return None
    
    async def _get_company_interview_stages(self, company_id: str | None) -> list[InterviewStage]:
        """Load interview stages from the company pipeline via PipelineStageService.

        Falls back to canonical defaults derived from DEFAULT_RECRUITMENT_STAGES
        when the company has no configured pipeline or when the DB is unreachable.
        """
        if company_id:
            try:
                from app.domains.recruiter_assistant.services.pipeline_stage_service import pipeline_stage_service

                db = AsyncSessionLocal()
                try:
                    stages = await pipeline_stage_service._get_company_stages(db, company_id)
                finally:
                    await db.close()

                if stages:
                    interview_stages = map_pipeline_to_jd_stages(stages)
                    if interview_stages:
                        self.logger.info(
                            f"Loaded {len(interview_stages)} pipeline stages for company {company_id}"
                        )
                        return interview_stages
            except Exception as e:
                self.logger.warning(f"Failed to load company pipeline stages: {e}", exc_info=True)

        return get_default_jd_interview_stages()
    
    def _calculate_timeline(self, stages: list[InterviewStage]) -> str:
        """Calcula timeline total do processo."""
        num_stages = len(stages)
        if num_stages <= 3:
            return "1-2 semanas"
        elif num_stages <= 5:
            return "2-3 semanas"
        else:
            return "3-4 semanas"
    
    def _render_preview_markdown(self, preview: JobDescriptionPreview) -> str:
        """Renderiza JD Preview em Markdown com indicadores."""
        lines = []
        
        title_suffix = f" ({preview.num_positions} vaga{'s' if preview.num_positions > 1 else ''})" if preview.num_positions > 1 else ""
        lines.append(f"# {preview.title}{title_suffix}")
        lines.append("")
        
        if preview.company:
            lines.append(f"## {JD_SECTION_TITLES['about']}")
            lines.append(preview.company.about or "[Descrição da empresa]")
            lines.append("")
        
        lines.append(f"## {JD_SECTION_TITLES['the_role']}")
        if preview.description:
            lines.append(preview.description)
            lines.append("")
        
        metadata = []
        if preview.department:
            metadata.append(f"**Departamento**: {preview.department}")
        if preview.seniority:
            metadata.append(f"**Senioridade**: {preview.seniority}")
        if preview.contract_type:
            metadata.append(f"**Contrato**: {CONTRACT_TYPE_LABELS.get(preview.contract_type, preview.contract_type.value)}")
        
        work_model_label = WORK_MODEL_LABELS.get(preview.work_model, preview.work_model.value)
        if preview.work_model == WorkModel.HYBRID and preview.office_days_per_week:
            work_model_label += f" ({preview.office_days_per_week}x/semana no escritório)"
        metadata.append(f"**Modelo**: {work_model_label}")
        
        if preview.location:
            metadata.append(f"**Local**: {preview.location}")
        
        if metadata:
            lines.append(" | ".join(metadata))
            lines.append("")
        
        if preview.is_affirmative:
            affirmative_text = preview.affirmative_type or "Vaga Afirmativa"
            lines.append(f"🏳️‍🌈 **{affirmative_text}**")
            lines.append("")
        
        if preview.responsibilities:
            lines.append(f"## {JD_SECTION_TITLES['what_you_will_do']}")
            for resp in preview.responsibilities:
                indicator = f" {SUGGESTION_INDICATOR}" if resp.is_new else ""
                lines.append(f"- {resp.description}{indicator}")
            lines.append("")
        
        lines.append(f"## {JD_SECTION_TITLES['what_we_are_looking_for']}")
        lines.append("")
        
        required_tech = [c for c in preview.technical_competencies if c.level == RequirementLevel.REQUIRED]
        nice_tech = [c for c in preview.technical_competencies if c.level == RequirementLevel.NICE_TO_HAVE]
        required_beh = [c for c in preview.behavioral_competencies if c.level == RequirementLevel.REQUIRED]
        
        if required_tech or required_beh:
            lines.append(f"### {JD_SECTION_TITLES['required']}")
            lines.append("")
            
            if required_tech:
                lines.append(f"**{JD_SECTION_TITLES['technical']}**")
                for comp in required_tech:
                    indicator = f" {SUGGESTION_INDICATOR}" if comp.is_new else ""
                    years = f" ({comp.years_experience}+ anos)" if comp.years_experience else ""
                    lines.append(f"- {comp.name}{years}{indicator}")
                lines.append("")
            
            if required_beh:
                lines.append(f"**{JD_SECTION_TITLES['behavioral']}**")
                for comp in required_beh:
                    indicator = f" {SUGGESTION_INDICATOR}" if comp.is_new else ""
                    lines.append(f"- {comp.name}{indicator}")
                lines.append("")
        
        if nice_tech:
            lines.append(f"### {JD_SECTION_TITLES['nice_to_have']}")
            for comp in nice_tech:
                indicator = f" {SUGGESTION_INDICATOR}" if comp.is_new else ""
                lines.append(f"- {comp.name}{indicator}")
            lines.append("")
        
        if preview.company and preview.company.evp:
            lines.append(f"## {JD_SECTION_TITLES['why_join_us']}")
            evp = preview.company.evp
            if evp.get("impact"):
                lines.append(f"**Impacto**: {evp['impact']}")
            if evp.get("growth"):
                lines.append(f"**Crescimento**: {evp['growth']}")
            if evp.get("team"):
                lines.append(f"**Time**: {evp['team']}")
            if evp.get("flexibility"):
                lines.append(f"**Flexibilidade**: {evp['flexibility']}")
            if evp.get("benefits"):
                lines.append(f"**Benefícios**: {evp['benefits']}")
            lines.append("")
        
        if preview.compensation:
            lines.append(f"## {JD_SECTION_TITLES['compensation']}")
            comp = preview.compensation
            
            if comp.salary_min and comp.salary_max:
                alert = f" {ALERT_INDICATOR} {comp.alert_message}" if comp.has_alert else ""
                lines.append(f"- **Salário**: R$ {comp.salary_min:,.0f} - R$ {comp.salary_max:,.0f}{alert}")
            
            if comp.bonus_percentage:
                lines.append(f"- **Bônus**: {comp.bonus_percentage}% anual")
            
            if comp.benefits:
                benefits_list = ", ".join([b.name for b in comp.benefits])
                lines.append(f"- **Benefícios**: {benefits_list}")
            lines.append("")
        
        if preview.company and preview.company.values:
            lines.append(f"## {JD_SECTION_TITLES['our_values']}")
            for value in preview.company.values:
                lines.append(f"- **{value['name']}**: {value['description']}")
            lines.append("")
        
        if preview.company and preview.company.diversity_statement:
            lines.append(f"## {JD_SECTION_TITLES['diversity']}")
            lines.append(preview.company.diversity_statement)
            lines.append("")
        
        lines.append("---")
        lines.append(f"{SUGGESTION_INDICATOR} = Sugerido pela LIA | {ALERT_INDICATOR} = Alerta | ✏️ = Editado")
        lines.append("")
        
        return "\n".join(lines)
    
    def _render_final_markdown(self, final: JobDescriptionFinal) -> str:
        """Renderiza JD Final em Markdown (versão limpa)."""
        lines = []
        
        title_suffix = f" ({final.num_positions} vaga{'s' if final.num_positions > 1 else ''})" if final.num_positions > 1 else ""
        lines.append(f"# {final.title}{title_suffix}")
        lines.append("")
        
        if final.company:
            lines.append(f"## {JD_SECTION_TITLES['about']}")
            lines.append(final.company.about or "[Descrição da empresa]")
            lines.append("")
        
        lines.append(f"## {JD_SECTION_TITLES['the_role']}")
        if final.description:
            lines.append(final.description)
            lines.append("")
        
        metadata = []
        if final.department:
            metadata.append(f"**Departamento**: {final.department}")
        if final.seniority:
            metadata.append(f"**Senioridade**: {final.seniority}")
        if final.contract_type:
            metadata.append(f"**Contrato**: {CONTRACT_TYPE_LABELS.get(final.contract_type, final.contract_type.value)}")
        
        work_model_label = WORK_MODEL_LABELS.get(final.work_model, final.work_model.value)
        if final.work_model == WorkModel.HYBRID and final.office_days_per_week:
            work_model_label += f" ({final.office_days_per_week}x/semana no escritório)"
        metadata.append(f"**Modelo**: {work_model_label}")
        
        if final.location:
            metadata.append(f"**Local**: {final.location}")
        
        if metadata:
            lines.append(" | ".join(metadata))
            lines.append("")
        
        if final.is_affirmative:
            affirmative_text = final.affirmative_type or "Vaga Afirmativa"
            lines.append(f"🏳️‍🌈 **{affirmative_text}**")
            lines.append("")
        
        if final.responsibilities:
            lines.append(f"## {JD_SECTION_TITLES['what_you_will_do']}")
            for resp in final.responsibilities:
                lines.append(f"- {resp}")
            lines.append("")
        
        lines.append(f"## {JD_SECTION_TITLES['what_we_are_looking_for']}")
        lines.append("")
        
        if final.required_technical or final.required_behavioral:
            lines.append(f"### {JD_SECTION_TITLES['required']}")
            for skill in final.required_technical:
                lines.append(f"- {skill}")
            for skill in final.required_behavioral:
                lines.append(f"- {skill}")
            lines.append("")
        
        if final.nice_to_have:
            lines.append(f"### {JD_SECTION_TITLES['nice_to_have']}")
            for skill in final.nice_to_have:
                lines.append(f"- {skill}")
            lines.append("")
        
        if final.company and final.company.evp:
            lines.append(f"## {JD_SECTION_TITLES['why_join_us']}")
            evp = final.company.evp
            if evp.get("impact"):
                lines.append(f"**Impacto**: {evp['impact']}")
            if evp.get("growth"):
                lines.append(f"**Crescimento**: {evp['growth']}")
            if evp.get("team"):
                lines.append(f"**Time**: {evp['team']}")
            if evp.get("flexibility"):
                lines.append(f"**Flexibilidade**: {evp['flexibility']}")
            if evp.get("benefits"):
                lines.append(f"**Benefícios**: {evp['benefits']}")
            lines.append("")
        
        if final.compensation:
            lines.append(f"## {JD_SECTION_TITLES['compensation']}")
            comp = final.compensation
            
            if comp.salary_min and comp.salary_max and comp.show_salary:
                lines.append(f"- **Salário**: R$ {comp.salary_min:,.0f} - R$ {comp.salary_max:,.0f}")
            
            if comp.bonus_percentage:
                lines.append(f"- **Bônus**: {comp.bonus_percentage}% anual")
            
            if comp.plr:
                lines.append(f"- **PLR**: {comp.plr}")
            
            if comp.equity:
                lines.append(f"- **Equity**: {comp.equity}")
            
            if comp.benefits:
                benefits_list = ", ".join([b.name for b in comp.benefits])
                lines.append(f"- **Benefícios**: {benefits_list}")
            lines.append("")
        
        if final.company and final.company.values:
            lines.append(f"## {JD_SECTION_TITLES['our_values']}")
            for value in final.company.values:
                lines.append(f"- **{value['name']}**: {value['description']}")
            lines.append("")
        
        if final.interview_process:
            lines.append(f"## {JD_SECTION_TITLES['interview_process']}")
            lines.append("")
            for stage in final.interview_process:
                format_info = f" ({stage.format}, {stage.duration})" if stage.format and stage.duration else ""
                lines.append(f"{stage.order}. **{stage.name}**{format_info}")
                if stage.description:
                    lines.append(f"   {stage.description}")
                lines.append("")
            
            if final.total_timeline:
                lines.append(f"⏱️ **Timeline total**: {final.total_timeline}")
            lines.append("")
        
        if final.company and final.company.diversity_statement:
            lines.append(f"## {JD_SECTION_TITLES['diversity']}")
            lines.append(final.company.diversity_statement)
            lines.append("")
        
        lines.append("---")
        if final.apply_url:
            lines.append(f"📩 **Candidate-se em**: {final.apply_url}")
        if final.contact_email:
            lines.append(f"❓ **Dúvidas?** {final.contact_email}")
        lines.append("")
        
        return "\n".join(lines)
    
    def _render_final_html(self, final: JobDescriptionFinal) -> str:
        """Renderiza JD Final em HTML."""
        import html
        
        def esc(text: str) -> str:
            return html.escape(text) if text else ""
        
        html_parts = ['<div class="job-description">']
        
        title_suffix = f" ({final.num_positions} vaga{'s' if final.num_positions > 1 else ''})" if final.num_positions > 1 else ""
        html_parts.append(f'<h1 class="jd-title">{esc(final.title)}{title_suffix}</h1>')
        
        if final.company:
            html_parts.append('<section class="jd-section jd-about">')
            html_parts.append(f'<h2>{JD_SECTION_TITLES["about"]}</h2>')
            html_parts.append(f'<p>{esc(final.company.about or "")}</p>')
            html_parts.append('</section>')
        
        html_parts.append('<section class="jd-section jd-role">')
        html_parts.append(f'<h2>{JD_SECTION_TITLES["the_role"]}</h2>')
        if final.description:
            html_parts.append(f'<p>{esc(final.description)}</p>')
        
        html_parts.append('<div class="jd-metadata">')
        if final.department:
            html_parts.append(f'<span><strong>Departamento:</strong> {esc(final.department)}</span>')
        if final.seniority:
            html_parts.append(f'<span><strong>Senioridade:</strong> {esc(final.seniority)}</span>')
        work_label = WORK_MODEL_LABELS.get(final.work_model, final.work_model.value)
        if final.work_model == WorkModel.HYBRID and final.office_days_per_week:
            work_label += f" ({final.office_days_per_week}x/semana)"
        html_parts.append(f'<span><strong>Modelo:</strong> {esc(work_label)}</span>')
        if final.location:
            html_parts.append(f'<span><strong>Local:</strong> {esc(final.location)}</span>')
        html_parts.append('</div>')
        
        if final.is_affirmative:
            html_parts.append(f'<div class="jd-affirmative">🏳️‍🌈 {esc(final.affirmative_type or "Vaga Afirmativa")}</div>')
        html_parts.append('</section>')
        
        if final.responsibilities:
            html_parts.append('<section class="jd-section jd-responsibilities">')
            html_parts.append(f'<h2>{JD_SECTION_TITLES["what_you_will_do"]}</h2>')
            html_parts.append('<ul>')
            for resp in final.responsibilities:
                html_parts.append(f'<li>{esc(resp)}</li>')
            html_parts.append('</ul>')
            html_parts.append('</section>')
        
        html_parts.append('<section class="jd-section jd-requirements">')
        html_parts.append(f'<h2>{JD_SECTION_TITLES["what_we_are_looking_for"]}</h2>')
        
        if final.required_technical or final.required_behavioral:
            html_parts.append(f'<h3>{JD_SECTION_TITLES["required"]}</h3>')
            html_parts.append('<ul>')
            for skill in final.required_technical:
                html_parts.append(f'<li>{esc(skill)}</li>')
            for skill in final.required_behavioral:
                html_parts.append(f'<li>{esc(skill)}</li>')
            html_parts.append('</ul>')
        
        if final.nice_to_have:
            html_parts.append(f'<h3>{JD_SECTION_TITLES["nice_to_have"]}</h3>')
            html_parts.append('<ul>')
            for skill in final.nice_to_have:
                html_parts.append(f'<li>{esc(skill)}</li>')
            html_parts.append('</ul>')
        html_parts.append('</section>')
        
        if final.interview_process:
            html_parts.append('<section class="jd-section jd-process">')
            html_parts.append(f'<h2>{JD_SECTION_TITLES["interview_process"]}</h2>')
            html_parts.append('<ol class="interview-stages">')
            for stage in final.interview_process:
                html_parts.append('<li>')
                html_parts.append(f'<strong>{esc(stage.name)}</strong>')
                if stage.format and stage.duration:
                    html_parts.append(f' <span class="stage-meta">({esc(stage.format)}, {esc(stage.duration)})</span>')
                if stage.description:
                    html_parts.append(f'<p>{esc(stage.description)}</p>')
                html_parts.append('</li>')
            html_parts.append('</ol>')
            if final.total_timeline:
                html_parts.append(f'<p class="timeline">⏱️ <strong>Timeline total:</strong> {esc(final.total_timeline)}</p>')
            html_parts.append('</section>')
        
        if final.company and final.company.diversity_statement:
            html_parts.append('<section class="jd-section jd-diversity">')
            html_parts.append(f'<h2>{JD_SECTION_TITLES["diversity"]}</h2>')
            html_parts.append(f'<p>{esc(final.company.diversity_statement)}</p>')
            html_parts.append('</section>')
        
        html_parts.append('<footer class="jd-footer">')
        if final.apply_url:
            html_parts.append(f'<p>📩 <strong>Candidate-se em:</strong> <a href="{esc(final.apply_url)}">{esc(final.apply_url)}</a></p>')
        if final.contact_email:
            html_parts.append(f'<p>❓ <strong>Dúvidas?</strong> <a href="mailto:{esc(final.contact_email)}">{esc(final.contact_email)}</a></p>')
        html_parts.append('</footer>')
        
        html_parts.append('</div>')
        
        return "\n".join(html_parts)


jd_template_service = JDTemplateService()
