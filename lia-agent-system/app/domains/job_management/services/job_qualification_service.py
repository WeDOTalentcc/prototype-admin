"""
Job Qualification Classification Service (WDT-009)
Uses Gemini LLM to classify job vacancies into Alta/Média/Baixa qualification levels.
This classification drives search precision parameters in the Talent Funnel.
"""
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """Você é um especialista em recrutamento e seleção. Analise a vaga abaixo e classifique o NÍVEL DE QUALIFICAÇÃO exigido.

## Critérios de Classificação:

**ALTA** - Vagas executivas, C-Level, diretoria, especialistas sênior raros:
- Cargos: CEO, CTO, VP, Diretor, Head, Principal Engineer, Staff Engineer
- Salário acima de R$ 25.000/mês
- Exige 10+ anos de experiência
- Competências raras ou combinações únicas
- Liderança de grandes equipes (20+)

**MÉDIA** - Vagas de profissionais plenos/sênior com boa experiência:
- Cargos: Sênior, Pleno avançado, Coordenador, Gerente de área
- Salário entre R$ 8.000 e R$ 25.000/mês
- Exige 3-10 anos de experiência
- Competências comuns mas com profundidade
- Gestão de pequenas equipes

**BAIXA** - Vagas operacionais, júnior, estágio, entrada no mercado:
- Cargos: Júnior, Trainee, Estagiário, Assistente, Auxiliar, Analista Jr
- Salário abaixo de R$ 8.000/mês
- Exige 0-3 anos de experiência
- Competências básicas, formação recente
- Sem gestão de equipes

## Vaga para Análise:

Título: {title}
Departamento: {department}
Senioridade: {seniority_level}
Descrição: {description}
Requisitos: {requirements}
Faixa Salarial: {salary_info}
Modelo de Trabalho: {work_model}
Tipo de Contrato: {employment_type}

## Responda APENAS em JSON válido:
{{
  "level": "alta" | "media" | "baixa",
  "confidence": 0.0 a 1.0,
  "reasoning": "explicação breve em português de por que esta classificação foi escolhida"
}}"""


class JobQualificationService:
    def _heuristic_classify(self, title: str, seniority: str | None = None, salary_min: float | None = None) -> dict[str, Any]:
        """Fallback heuristic classification when LLM is unavailable."""
        title_lower = (title or "").lower()
        seniority_lower = (seniority or "").lower()
        
        alta_keywords = ["ceo", "cto", "cfo", "coo", "cpo", "vp", "vice president", "diretor", "director", "head of", "principal", "staff", "c-level", "chief", "sócio", "partner"]
        baixa_keywords = ["júnior", "junior", "trainee", "estagiário", "estágio", "intern", "assistente", "auxiliar", "aprendiz", "young"]
        
        for kw in alta_keywords:
            if kw in title_lower or kw in seniority_lower:
                return {"level": "alta", "confidence": 0.7, "reasoning": f"Classificação heurística: cargo '{title}' contém indicador de alta qualificação ('{kw}')"}
        
        if salary_min and salary_min >= 25000:
            return {"level": "alta", "confidence": 0.65, "reasoning": f"Classificação heurística: faixa salarial R${salary_min:,.0f} indica alta qualificação"}
        
        for kw in baixa_keywords:
            if kw in title_lower or kw in seniority_lower:
                return {"level": "baixa", "confidence": 0.7, "reasoning": f"Classificação heurística: cargo '{title}' contém indicador de baixa qualificação ('{kw}')"}
        
        if salary_min and salary_min < 8000:
            return {"level": "baixa", "confidence": 0.6, "reasoning": f"Classificação heurística: faixa salarial R${salary_min:,.0f} indica baixa qualificação"}
        
        return {"level": "media", "confidence": 0.6, "reasoning": f"Classificação heurística: cargo '{title}' classificado como qualificação média por padrão"}

    async def classify(self, title: str, department: str | None = None, seniority_level: str | None = None,
                       description: str | None = None, requirements: list | None = None,
                       salary_range: dict | None = None, work_model: str | None = None,
                       employment_type: str | None = None) -> dict[str, Any]:
        """Classify a job vacancy qualification level using Gemini LLM with heuristic fallback."""
        salary_info = "Não informado"
        salary_min = None
        if salary_range:
            min_val = salary_range.get("min")
            max_val = salary_range.get("max")
            currency = salary_range.get("currency", "BRL")
            salary_min = min_val
            if min_val and max_val:
                salary_info = f"{currency} {min_val:,.0f} - {max_val:,.0f}"
            elif min_val:
                salary_info = f"{currency} {min_val:,.0f}+"
        
        reqs_text = ", ".join(requirements) if requirements else "Não informado"
        
        from app.shared.providers.llm_factory import get_provider_for_tenant

        prompt = CLASSIFICATION_PROMPT.format(
            title=title or "Não informado",
            department=department or "Não informado",
            seniority_level=seniority_level or "Não informado",
            description=(description or "Não informado")[:1500],
            requirements=reqs_text[:500],
            salary_info=salary_info,
            work_model=work_model or "Não informado",
            employment_type=employment_type or "Não informado",
        )
        
        try:
            container = get_provider_for_tenant()
            text = await container.generate_with_fallback(prompt, agent_type="JobQualificationAgent")
            text = text.strip()
            
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            
            result = json.loads(text)
            level = result.get("level", "media").lower()
            if level not in ("alta", "media", "baixa"):
                level = "media"
            
            confidence = float(result.get("confidence", 0.8))
            confidence = max(0.0, min(1.0, confidence))
            
            return {
                "level": level,
                "confidence": confidence,
                "reasoning": result.get("reasoning", "Classificação via IA sem justificativa detalhada"),
            }
        except Exception as e:
            logger.error(f"Gemini classification failed, using heuristic: {e}")
            return self._heuristic_classify(title, seniority_level, salary_min)


job_qualification_service = JobQualificationService()
