"""
Job Description Generator Service - Uses Claude to generate professional job descriptions.

This service provides AI-powered generation of complete job descriptions based on
collected criteria, with support for:
- Full description generation
- Section-specific generation
- Description improvement based on feedback
- Translation to other languages
- AI response caching for performance optimization
"""
import json
import logging
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any

from app.domains.ai.services.ai_cache_service import ai_cache_service
from app.domains.ai.services.llm import LLMProvider, llm_service

logger = logging.getLogger(__name__)


class JobDescriptionSection(StrEnum):
    ABOUT_COMPANY = "about_company"
    RESPONSIBILITIES = "responsibilities"
    REQUIREMENTS = "requirements"
    BENEFITS = "benefits"
    HOW_TO_APPLY = "how_to_apply"


@dataclass
class JobDescriptionInput:
    title: str
    department: str | None = None
    seniority: str | None = None
    work_model: str | None = None
    location: str | None = None
    skills: list[str] | None = None
    behavioral_competencies: list[str] | None = None
    salary_range: dict[str, float] | None = None
    benefits: list[str] | None = None
    company_name: str | None = None
    company_culture: str | None = None
    additional_info: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobDescriptionInput":
        return cls(
            title=data.get("title", ""),
            department=data.get("department"),
            seniority=data.get("seniority"),
            work_model=data.get("work_model"),
            location=data.get("location"),
            skills=data.get("skills"),
            behavioral_competencies=data.get("behavioral_competencies"),
            salary_range=data.get("salary_range"),
            benefits=data.get("benefits"),
            company_name=data.get("company_name"),
            company_culture=data.get("company_culture"),
            additional_info=data.get("additional_info"),
        )


@dataclass
class JobDescriptionOutput:
    full_description: str
    sections: dict[str, str]
    summary: str
    seo_title: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_description": self.full_description,
            "sections": self.sections,
            "summary": self.summary,
            "seo_title": self.seo_title,
            "tags": self.tags,
        }


class JobDescriptionGeneratorService:
    """
    Service for generating professional job descriptions using Claude.
    
    Features:
    - Full job description generation
    - Section-specific generation (responsibilities, requirements, benefits)
    - Description improvement based on feedback
    - Translation to other languages
    """
    
    DEFAULT_PROVIDER: LLMProvider = "claude"
    FALLBACK_PROVIDER: LLMProvider = "gemini"
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _build_job_context(self, job_data: dict[str, Any]) -> str:
        """Build a context string from job data for prompts."""
        parts = []
        
        if job_data.get("title"):
            parts.append(f"Cargo: {job_data['title']}")
        if job_data.get("department"):
            parts.append(f"Departamento: {job_data['department']}")
        if job_data.get("seniority"):
            parts.append(f"Senioridade: {job_data['seniority']}")
        if job_data.get("work_model"):
            parts.append(f"Modelo de trabalho: {job_data['work_model']}")
        if job_data.get("location"):
            parts.append(f"Localização: {job_data['location']}")
        if job_data.get("salary_range"):
            salary = job_data["salary_range"]
            if isinstance(salary, dict):
                min_sal = salary.get("min", "")
                max_sal = salary.get("max", "")
                if min_sal or max_sal:
                    parts.append(f"Faixa salarial: R$ {min_sal} - R$ {max_sal}")
            elif isinstance(salary, str) and salary:
                parts.append(f"Faixa salarial: {salary}")
        if job_data.get("description"):
            parts.append(f"Descrição adicional: {job_data['description']}")
        if job_data.get("company_name"):
            parts.append(f"Nome da empresa: {job_data['company_name']}")
        if job_data.get("company_description"):
            parts.append(f"Descrição da empresa: {job_data['company_description']}")
        if job_data.get("company_industry"):
            parts.append(f"Setor/Indústria: {job_data['company_industry']}")
        if job_data.get("company_culture"):
            parts.append(f"Cultura da empresa: {job_data['company_culture']}")
        
        skills = job_data.get("technical_skills") or job_data.get("skills") or []
        if isinstance(skills, list) and skills:
            skills_str = ", ".join(str(s) for s in skills)
            parts.append(f"Habilidades técnicas: {skills_str}")
        
        competencies = job_data.get("behavioral_competencies") or []
        if isinstance(competencies, list) and competencies:
            parts.append(f"Competências comportamentais: {', '.join(str(c) for c in competencies)}")
        
        responsibilities = job_data.get("responsibilities") or []
        if isinstance(responsibilities, list) and responsibilities:
            parts.append("Responsabilidades:")
            for r in responsibilities:
                parts.append(f"  - {r}")
        
        benefits = job_data.get("benefits") or []
        if isinstance(benefits, list) and benefits:
            parts.append(f"Benefícios: {', '.join(str(b) for b in benefits)}")
        
        interview_stages = job_data.get("interview_stages") or []
        if isinstance(interview_stages, list) and interview_stages:
            parts.append(f"Etapas do processo seletivo: {', '.join(str(s) for s in interview_stages)}")
        
        if job_data.get("additional_info"):
            parts.append(f"Informações adicionais: {job_data['additional_info']}")
        
        return "\n".join(parts)
    
    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        cleaned = response.strip()
        
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return {}
    
    async def generate_full_description(
        self,
        job_data: dict[str, Any],
        company_id: str,
        provider: LLMProvider | None = None,
        use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Generate a complete, professional job description.
        
        Args:
            job_data: Dictionary with job information (title, department, skills, etc.)
            provider: LLM provider to use (defaults to Claude)
            company_id: Company identifier for cache isolation
            use_cache: Whether to use cached responses
        
        Returns:
            Dictionary with full_description, sections, summary, seo_title, and tags
        """
        provider = provider or self.DEFAULT_PROVIDER
        context = self._build_job_context(job_data)
        
        if use_cache:
            cached = await ai_cache_service.get_cached(
                cache_type="jd_generation",
                content=context,
                company_id=company_id,
                extra_params={"provider": provider},
                use_similarity=True
            )
            if cached:
                self.logger.info("Using cached JD generation response")
                cached["from_cache"] = True
                return cached
        
        has_benefits = bool(job_data.get("benefits"))
        has_interview_stages = bool(job_data.get("interview_stages"))

        benefits_instruction = ""
        if has_benefits:
            benefits_instruction = '    "benefits": "Lista EXATAMENTE os benefícios fornecidos, sem adicionar outros",'
        
        interview_instruction = ""
        if has_interview_stages:
            interview_instruction = '    "selection_process": "Lista EXATAMENTE as etapas do processo seletivo fornecidas",'

        prompt = f"""Você é um redator especializado em descrições de vagas. Sua função é ESTRUTURAR e MELHORAR A REDAÇÃO das informações fornecidas pelo recrutador, sem jamais inventar conteúdo novo.

REGRA FUNDAMENTAL DE FIDELIDADE:
- Use EXCLUSIVAMENTE as informações fornecidas abaixo.
- Você pode melhorar a qualidade da escrita, estrutura e clareza.
- Você NÃO PODE adicionar requisitos, competências, qualificações, responsabilidades, benefícios ou qualquer conteúdo factual que NÃO tenha sido fornecido.
- NÃO inclua seção de requisitos desejáveis ("Desejáveis"). Apenas requisitos obrigatórios.
- Se uma informação não foi fornecida, NÃO a invente.

INFORMAÇÕES DA VAGA (use SOMENTE estas):
{context}

ESTRUTURA OBRIGATÓRIA DA DESCRIÇÃO (em markdown):

1. **Sobre a Empresa**: Use o nome da empresa, descrição e setor SE fornecidos. Se NÃO fornecidos, use "[Nome da Empresa]" como placeholder. NÃO invente informações sobre a empresa.

2. **Responsabilidades**: Liste SOMENTE as responsabilidades fornecidas. Melhore a redação mas NÃO adicione novas responsabilidades.

3. **Requisitos**: Divida em duas subseções:
   - "Requisitos Técnicos": Use SOMENTE as habilidades técnicas fornecidas.
   - "Requisitos Comportamentais": Use SOMENTE as competências comportamentais fornecidas.
   NÃO inclua seção de "Desejáveis" ou "Diferenciais".

4. **Benefícios**: {"Liste SOMENTE os benefícios fornecidos. NÃO adicione benefícios extras." if has_benefits else "OMITA esta seção completamente pois nenhum benefício foi fornecido."}

5. **Processo Seletivo**: {"Liste SOMENTE as etapas fornecidas." if has_interview_stages else "OMITA esta seção completamente pois nenhuma etapa foi fornecida."}

6. **Diversidade**: Inclua uma frase curta e genérica sobre inclusão e diversidade (ex: "Valorizamos a diversidade e incentivamos candidaturas de todas as pessoas, independentemente de gênero, etnia, orientação sexual, deficiência ou qualquer outra característica.").

Gere uma resposta JSON com a seguinte estrutura:
{{
  "full_description": "Texto completo da descrição da vaga em markdown, seguindo a estrutura acima",
  "sections": {{
    "about_company": "Seção Sobre a Empresa",
    "responsibilities": "Seção de Responsabilidades",
    "requirements": "Seção de Requisitos (Técnicos + Comportamentais, sem Desejáveis)",
{benefits_instruction}
{interview_instruction}
    "diversity": "Frase genérica de diversidade e inclusão"
  }},
  "summary": "",
  "seo_title": "Título otimizado para SEO",
  "tags": ["tags", "extraídas", "somente", "dos", "dados", "fornecidos"]
}}

REGRAS PARA TAGS:
- Extraia tags SOMENTE de: cargo, departamento, habilidades técnicas e competências comportamentais fornecidas.
- NÃO invente tags que não derivem diretamente dos dados fornecidos.
- Tags devem ser em lowercase.

REGRA PARA SUMMARY:
- O campo "summary" DEVE ser uma string vazia "".

Responda APENAS com o JSON, sem explicações adicionais."""

        try:
            response = await llm_service.generate(prompt, provider=provider)
            result = self._parse_json_response(response)
            
            if not result or "full_description" not in result:
                self.logger.warning("Invalid response, trying fallback provider")
                if provider != self.FALLBACK_PROVIDER:
                    return await self.generate_full_description(
                        job_data, provider=self.FALLBACK_PROVIDER,
                        company_id=company_id, use_cache=use_cache
                    )
                return self._create_fallback_response(job_data)
            
            if use_cache:
                await ai_cache_service.set_cached(
                    cache_type="jd_generation",
                    content=context,
                    company_id=company_id,
                    response_data=result,
                    extra_params={"provider": provider}
                )
            
            result["from_cache"] = False
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating full description: {e}")
            if provider != self.FALLBACK_PROVIDER:
                try:
                    return await self.generate_full_description(
                        job_data, provider=self.FALLBACK_PROVIDER,
                        company_id=company_id, use_cache=use_cache
                    )
                except Exception as fallback_error:
                    self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return self._create_fallback_response(job_data)
    
    async def generate_section(
        self,
        job_data: dict[str, Any],
        section: str,
        provider: LLMProvider | None = None
    ) -> dict[str, Any]:
        """
        Generate a specific section of the job description.
        
        Args:
            job_data: Dictionary with job information
            section: Section to generate (responsibilities, requirements, benefits, etc.)
            provider: LLM provider to use
        
        Returns:
            Dictionary with the generated section content
        """
        provider = provider or self.DEFAULT_PROVIDER
        context = self._build_job_context(job_data)
        
        section_prompts = {
            "about_company": """Crie uma seção "Sobre a Empresa" com 2-3 parágrafos que:
- Apresente a empresa de forma atrativa
- Destaque a cultura e valores
- Mencione o setor de atuação e diferenciais""",
            
            "responsibilities": """Crie uma lista de "Responsabilidades" com 5-8 itens que:
- Descreva as principais atividades do cargo
- Use verbos de ação no infinitivo
- Seja específico e mensurável quando possível""",
            
            "requirements": """Crie uma seção de "Requisitos" dividida em:
- Requisitos Obrigatórios (essenciais para a função)
- Requisitos Desejáveis (diferenciais)
Inclua tanto habilidades técnicas quanto comportamentais.""",
            
            "benefits": """Crie uma seção de "Benefícios" que:
- Liste os benefícios de forma atrativa
- Destaque os diferenciais da empresa
- Use emojis moderadamente para visual appeal""",
            
            "how_to_apply": """Crie uma seção "Como se Candidatar" que:
- Explique o processo de candidatura
- Inclua um call-to-action motivador
- Mencione expectativas sobre o processo seletivo"""
        }
        
        section_key = section.lower().replace(" ", "_")
        section_instruction = section_prompts.get(
            section_key,
            f"Crie a seção '{section}' de forma profissional e atrativa."
        )
        
        prompt = f"""Você é um especialista em recrutamento e employer branding.
{section_instruction}

INFORMAÇÕES DA VAGA:
{context}

Responda com um JSON no formato:
{{
  "section": "{section_key}",
  "content": "Conteúdo da seção em markdown",
  "word_count": número_de_palavras
}}

Use formatação markdown (bullet points, negrito, etc.) quando apropriado.
Responda APENAS com o JSON."""

        try:
            response = await llm_service.generate(prompt, provider=provider)
            result = self._parse_json_response(response)
            
            if not result or "content" not in result:
                if provider != self.FALLBACK_PROVIDER:
                    return await self.generate_section(
                        job_data, section, provider=self.FALLBACK_PROVIDER
                    )
                return {
                    "section": section_key,
                    "content": f"[Seção {section} - conteúdo será gerado em breve]",
                    "word_count": 0,
                    "error": "Failed to generate section"
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating section '{section}': {e}")
            return {
                "section": section_key,
                "content": "",
                "word_count": 0,
                "error": str(e)
            }
    
    async def improve_description(
        self,
        current_text: str,
        feedback: str,
        provider: LLMProvider | None = None
    ) -> dict[str, Any]:
        """
        Improve an existing job description based on feedback.
        
        Args:
            current_text: Current job description text
            feedback: Feedback or instructions for improvement
            provider: LLM provider to use
        
        Returns:
            Dictionary with improved text and changes summary
        """
        provider = provider or self.DEFAULT_PROVIDER
        
        prompt = f"""Você é um especialista em recrutamento e employer branding.
Melhore a descrição de vaga abaixo com base no feedback fornecido.

DESCRIÇÃO ATUAL:
{current_text}

FEEDBACK/INSTRUÇÕES DE MELHORIA:
{feedback}

Responda com um JSON no formato:
{{
  "improved_text": "Texto melhorado em markdown",
  "changes_summary": ["Lista de principais mudanças realizadas"],
  "suggestions": ["Sugestões adicionais para melhorar ainda mais"]
}}

DIRETRIZES:
- Mantenha o que está bom no texto original
- Aplique as mudanças solicitadas no feedback
- Melhore a clareza e atratividade do texto
- Use linguagem inclusiva
- Preserve a formatação markdown

Responda APENAS com o JSON."""

        try:
            response = await llm_service.generate(prompt, provider=provider)
            result = self._parse_json_response(response)
            
            if not result or "improved_text" not in result:
                if provider != self.FALLBACK_PROVIDER:
                    return await self.improve_description(
                        current_text, feedback, provider=self.FALLBACK_PROVIDER
                    )
                return {
                    "improved_text": current_text,
                    "changes_summary": [],
                    "suggestions": [],
                    "error": "Failed to improve description"
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error improving description: {e}")
            return {
                "improved_text": current_text,
                "changes_summary": [],
                "suggestions": [],
                "error": str(e)
            }
    
    async def translate_description(
        self,
        text: str,
        target_language: str,
        provider: LLMProvider | None = None
    ) -> dict[str, Any]:
        """
        Translate a job description to another language.
        
        Args:
            text: Job description text to translate
            target_language: Target language (e.g., "English", "Spanish", "French")
            provider: LLM provider to use
        
        Returns:
            Dictionary with translated text and metadata
        """
        provider = provider or self.DEFAULT_PROVIDER
        
        language_names = {
            "en": "English",
            "es": "Spanish (Español)",
            "fr": "French (Français)",
            "de": "German (Deutsch)",
            "it": "Italian (Italiano)",
            "pt": "Portuguese (Português)",
            "zh": "Chinese (中文)",
            "ja": "Japanese (日本語)",
            "ko": "Korean (한국어)",
        }
        
        target = language_names.get(target_language.lower(), target_language)
        
        prompt = f"""You are an expert translator specializing in HR and recruitment content.
Translate the following job description to {target}.

ORIGINAL TEXT (Portuguese):
{text}

Respond with a JSON in this format:
{{
  "translated_text": "Complete translation maintaining markdown formatting",
  "target_language": "{target}",
  "translation_notes": ["Any cultural adaptations or notes about the translation"]
}}

GUIDELINES:
- Maintain the professional tone and format
- Adapt culturally relevant expressions appropriately
- Keep markdown formatting intact
- Preserve technical terms that are commonly used in English
- Ensure the translation sounds natural in the target language

Respond ONLY with the JSON."""

        try:
            response = await llm_service.generate(prompt, provider=provider)
            result = self._parse_json_response(response)
            
            if not result or "translated_text" not in result:
                if provider != self.FALLBACK_PROVIDER:
                    return await self.translate_description(
                        text, target_language, provider=self.FALLBACK_PROVIDER
                    )
                return {
                    "translated_text": "",
                    "target_language": target,
                    "translation_notes": [],
                    "error": "Failed to translate description"
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error translating description: {e}")
            return {
                "translated_text": "",
                "target_language": target,
                "translation_notes": [],
                "error": str(e)
            }
    
    def generate_description(self, job_data: dict[str, Any], company_context: dict[str, Any] | None = None) -> str:
        """
        Generate a professional job description based on job criteria (synchronous, no LLM).
        
        Uses ONLY the data provided — no invented content.
        This is a quick template-based generation for the wizard review stage.
        For LLM-powered generation, use generate_full_description() instead.

        UPSTREAM CONTRACT (audit 2026-05-21, ratchet 2->0):
        ``company_context`` is a dict-shaped argument received from the caller.
        The CALLER is responsible for filtering company fields against
        ``lia_field_toggles`` via
        :class:`app.domains.cv_screening.services.lia_field_config_service.LiaFieldConfigService`
        BEFORE invoking this function. Fields the recruiter disabled MUST
        already be absent / None / empty when arriving here. This function
        is a TEMPLATE builder — it does not consult toggles itself, by
        design, to keep the function pure and reusable. The file is
        ALLOWLISTED in scripts/check_agent_respects_lia_toggles.py.

        Args:
            job_data: Dictionary with job criteria (title, skills, requirements, etc.)
            company_context: Optional company information (about, culture, benefits).
                Caller is responsible for filtering via lia_field_toggles.
        
        Returns:
            Formatted job description string in markdown
        """
        title = job_data.get('job_title') or job_data.get('cargo') or job_data.get('title') or 'Vaga'
        seniority = job_data.get('seniority') or job_data.get('senioridadeIdiomas') or ''
        job_data.get('department') or job_data.get('gestorArea') or ''
        location = job_data.get('location') or job_data.get('localizacao') or ''
        work_model = job_data.get('work_model') or job_data.get('modeloTrabalho') or ''
        company_name = job_data.get('company_name') or (company_context.get('name') if company_context else None) or "[Nome da Empresa]"
        company_description = job_data.get('company_description') or (company_context.get('about') if company_context else None) or ""
        company_industry = job_data.get('company_industry') or (company_context.get('industry') if company_context else None) or ""
        
        tech_skills = job_data.get('technical_skills') or job_data.get('competenciasTecnicas') or job_data.get('detected_skills') or job_data.get('skills') or []
        behavioral_skills = job_data.get('behavioral_competencies') or job_data.get('competenciasComportamentais') or []
        benefits_list = job_data.get('benefits') or job_data.get('beneficios') or []
        responsibilities = job_data.get('responsibilities') or []
        interview_stages = job_data.get('interview_stages') or []
        
        sections = []
        
        full_title = f"{title} {seniority}".strip() if seniority else title
        sections.append(f"# {full_title}\n")
        
        if location or work_model:
            location_line = []
            if location:
                location_line.append(f"📍 {location}")
            if work_model:
                model_str = work_model.title() if isinstance(work_model, str) else str(work_model)
                location_line.append(f"🏢 {model_str}")
            sections.append(" | ".join(location_line) + "\n")
        
        sections.append("\n## Sobre a Empresa\n\n")
        if company_description:
            sections.append(f"**{company_name}** — {company_description}")
        else:
            sections.append(f"**{company_name}**")
        if company_industry:
            sections.append(f"\n\nSetor: {company_industry}")
        sections.append("\n\n")
        
        if responsibilities:
            sections.append("## Responsabilidades\n\n")
            for r in responsibilities:
                sections.append(f"- {r}\n")
            sections.append("\n")
        
        if tech_skills:
            sections.append("## Requisitos Técnicos\n\n")
            for skill in tech_skills:
                skill_name = skill.get('name', skill) if isinstance(skill, dict) else skill
                sections.append(f"- {skill_name}\n")
            sections.append("\n")
        
        if behavioral_skills:
            sections.append("## Requisitos Comportamentais\n\n")
            for skill in behavioral_skills:
                skill_name = skill.get('name', skill) if isinstance(skill, dict) else skill
                sections.append(f"- {skill_name}\n")
            sections.append("\n")
        
        if benefits_list:
            sections.append("## Benefícios\n\n")
            for benefit in benefits_list:
                benefit_name = benefit.get('name', benefit) if isinstance(benefit, dict) else benefit
                sections.append(f"- {benefit_name}\n")
            sections.append("\n")
        
        if interview_stages:
            sections.append("## Processo Seletivo\n\n")
            for i, stage in enumerate(interview_stages, 1):
                sections.append(f"{i}. {stage}\n")
            sections.append("\n")
        
        sections.append("## Diversidade\n\n")
        sections.append("Valorizamos a diversidade e incentivamos candidaturas de todas as pessoas, independentemente de gênero, etnia, orientação sexual, deficiência ou qualquer outra característica.\n")
        
        return "".join(sections)

    def _create_fallback_response(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """Create a basic fallback response when LLM generation fails. Uses ONLY provided data."""
        title = job_data.get("title", "Vaga")
        company_name = job_data.get("company_name") or "[Nome da Empresa]"
        company_description = job_data.get("company_description") or ""
        company_industry = job_data.get("company_industry") or ""
        tech_skills = job_data.get("technical_skills") or job_data.get("skills") or []
        behavioral = job_data.get("behavioral_competencies") or []
        benefits = job_data.get("benefits") or []
        responsibilities = job_data.get("responsibilities") or []
        interview_stages = job_data.get("interview_stages") or []
        department = job_data.get("department") or ""
        
        sections_md = []
        sections_md.append(f"# {title}\n")
        
        about_parts = ["## Sobre a Empresa\n"]
        if company_description:
            about_parts.append(f"{company_name} — {company_description}")
        else:
            about_parts.append(f"{company_name}")
        if company_industry:
            about_parts.append(f"\nSetor: {company_industry}")
        about_text = "\n".join(about_parts)
        sections_md.append(about_text + "\n")
        
        resp_text = ""
        if responsibilities:
            resp_lines = ["## Responsabilidades\n"]
            for r in responsibilities:
                resp_lines.append(f"- {r}")
            resp_text = "\n".join(resp_lines)
            sections_md.append(resp_text + "\n")
        
        req_parts = ["## Requisitos\n"]
        if tech_skills:
            req_parts.append("### Requisitos Técnicos\n")
            for s in tech_skills:
                skill_name = s.get("name", s) if isinstance(s, dict) else s
                req_parts.append(f"- {skill_name}")
            "\n".join(req_parts[1:])
        if behavioral:
            req_parts.append("\n### Requisitos Comportamentais\n")
            for c in behavioral:
                comp_name = c.get("name", c) if isinstance(c, dict) else c
                req_parts.append(f"- {comp_name}")
            "\n".join([l for l in req_parts if "Comportamentais" in l or (req_parts.index(l) > len(req_parts)//2)]) if behavioral else ""
        req_text = "\n".join(req_parts)
        sections_md.append(req_text + "\n")
        
        benefits_text = ""
        if benefits:
            ben_lines = ["## Benefícios\n"]
            for b in benefits:
                b_name = b.get("name", b) if isinstance(b, dict) else b
                ben_lines.append(f"- {b_name}")
            benefits_text = "\n".join(ben_lines)
            sections_md.append(benefits_text + "\n")
        
        process_text = ""
        if interview_stages:
            proc_lines = ["## Processo Seletivo\n"]
            for i, stage in enumerate(interview_stages, 1):
                proc_lines.append(f"{i}. {stage}")
            process_text = "\n".join(proc_lines)
            sections_md.append(process_text + "\n")
        
        diversity_text = "Valorizamos a diversidade e incentivamos candidaturas de todas as pessoas, independentemente de gênero, etnia, orientação sexual, deficiência ou qualquer outra característica."
        sections_md.append(f"## Diversidade\n\n{diversity_text}\n")
        
        tag_sources = [title.lower()] + ([department.lower()] if department else [])
        for s in tech_skills[:5]:
            tag_sources.append((s.get("name", s) if isinstance(s, dict) else s).lower())
        for c in behavioral[:3]:
            tag_sources.append((c.get("name", c) if isinstance(c, dict) else c).lower())
        
        sections_dict = {
            "about_company": about_text,
            "responsibilities": resp_text,
            "requirements": req_text,
            "diversity": diversity_text,
        }
        if benefits:
            sections_dict["benefits"] = benefits_text
        if interview_stages:
            sections_dict["selection_process"] = process_text
        
        return {
            "full_description": "\n".join(sections_md),
            "sections": sections_dict,
            "summary": "",
            "seo_title": title,
            "tags": tag_sources,
            "fallback": True
        }


jd_generator_service = JobDescriptionGeneratorService()
