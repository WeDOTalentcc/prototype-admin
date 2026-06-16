"""
WSI Report Generator - Structured reports and candidate feedback.

P0.D fix (audit 2026-05-21): silent fallback eliminado.
Antes: try/except Exception retornava template fake content COM aparencia
de success. Recrutador via "decisao: AGUARDANDO + revisar manualmente"
sem saber que era fallback automatico (LLM tinha falhado).

Agora: LLM call envolvida em safe_llm_with_flag_async (canonical helper
em app.shared.llm.safe_response). Em failure:
  - StructuredReport / CandidateFeedback ainda sao retornados (template
    fallback preserved para back-compat de callers existentes)
  - MAS com flags fallback_used=True + needs_manual_review=True +
    llm_failure_mode populated. Caller pode renderizar UI degraded ou
    fila pra revisao manual.

Pattern canonical alinhado com REGRA 4 CLAUDE.md (fail-loud em LLM paths).
"""
import logging
from typing import Any, Literal

from app.shared.llm.safe_response import safe_llm_with_flag_async, LLMFailureMode

from .models import (
    CandidateFeedback,
    ResponseAnalysis,
    StructuredReport,
    WSIResult,
    safe_json_parse,
)

logger = logging.getLogger(__name__)

class WSIReportGenerator:
    """Gerador de pareceres estruturados e feedbacks com RAG."""
    
    def __init__(self, llm):
        self.llm = llm
        self._load_rag_templates()
    
    def _load_rag_templates(self):
        """Carrega templates do RAG."""
        from pathlib import Path
        
        rag_dir = Path("lia-agent-system/training/rag_knowledge/wsi_methodology")
        self.report_templates = (rag_dir / "report_templates.md").read_text(encoding="utf-8") if (rag_dir / "report_templates.md").exists() else ""
    
    async def generate_report(
        self,
        candidate_id: str,
        wsi_result: WSIResult,
        responses: list[ResponseAnalysis]
    ) -> StructuredReport:
        """Gera parecer estruturado para recrutadores."""
        
        # Preparar contexto das respostas
        responses_summary = "\n".join([
            f"- {r.competency} (Score: {r.final_score}/5): {r.justification}"
            for r in responses
        ])
        
        tech_responses = [r for r in responses if r.competency and any(
            kw in r.competency.lower() for kw in ["python", "react", "java", "sql", "aws", "node", "go", "rust", "docker", "kubernetes", "api", "backend", "frontend", "devops", "data", "machine", "deep", "cloud"]
        )]
        behav_responses = [r for r in responses if r not in tech_responses]
        
        tech_strong = [f"{r.competency} ({r.final_score}/5)" for r in tech_responses if r.final_score >= 4.0]
        tech_gaps = [f"{r.competency} ({r.final_score}/5)" for r in tech_responses if r.final_score < 3.0]
        behav_strong = [f"{r.competency} ({r.final_score}/5)" for r in behav_responses if r.final_score >= 4.0]
        
        prompt = f"""Gere um parecer estruturado completo para recrutadores usando a metodologia WSI.

CANDIDATO ID: {candidate_id}

WSI RESULTADOS:
- WSI Técnico: {wsi_result.technical_wsi}/5.0
- WSI Comportamental: {wsi_result.behavioral_wsi}/5.0
- WSI Geral: {wsi_result.overall_wsi}/5.0
- Classificação: {wsi_result.classification.upper()}

ANÁLISES DAS RESPOSTAS:
{responses_summary}

PONTOS FORTES TÉCNICOS: {tech_strong or "Nenhum score >= 4.0"}
GAPS TÉCNICOS: {tech_gaps or "Nenhum score < 3.0"}
PONTOS FORTES COMPORTAMENTAIS: {behav_strong or "Nenhum score >= 4.0"}

TEMPLATES DE REFERÊNCIA (exemplos do RAG):
{self.report_templates[:3000]}

---

CRITÉRIOS OBJETIVOS PARA DECISÃO (OBRIGATÓRIO seguir — WSI_CUTOFFS canônicos):
- WSI Geral >= 3.75 → decisao = "APROVADO" (= 7.5/10)
- WSI Geral >= 3.0 e < 3.75 → decisao = "AGUARDANDO" / "EM_AVALIACAO" (= 6.0–7.4/10)
- WSI Geral < 3.0 → decisao = "NÃO APROVADO" (= < 6.0/10)
- EXCEÇÃO: Se WSI Geral >= 3.75 MAS há red_flags graves → rebaixa para "AGUARDANDO"

REGRAS DE QUALIDADE DO PARECER:
1. **Sumário Executivo** DEVE ter 2-3 frases completas (mínimo 100 caracteres), incluindo: perfil resumido, principal ponto forte e recomendação clara
2. **Análise Técnica**: Citar ao menos 2 evidências concretas extraídas das respostas (projetos, métricas, tecnologias mencionadas)
3. **Análise Comportamental**: Scores de 1.0 a 5.0 para cada dimensão, baseados nas respostas observadas
4. **Fit Cultural**: Identificar ao menos 1 valor alinhado e 1 ponto de atenção quando WSI < 4.0
5. **Recomendação**: Justificativa DEVE referenciar dados do WSI (scores, classificação). Próximos passos DEVEM ser acionáveis

Gere parecer estruturado incluindo:
1. **Sumário Executivo** (2-3 frases): Resumo do perfil, pontos fortes, recomendação
2. **Análise Técnica**: Pontos fortes (top 3), gaps (se houver), evidências concretas das respostas
3. **Análise Comportamental**: Colaboração, inovação, organização, resiliência (scores 1.0-5.0)
4. **Fit Cultural**: Score geral, valores alinhados, pontos de atenção
5. **Recomendação**: Decisão (seguir critérios acima), justificativa com dados, próximos passos acionáveis

RETORNE APENAS JSON:
{{
  "executive_summary": "...",
  "technical_analysis": {{
    "pontos_fortes": ["...", "...", "..."],
    "gaps": ["..."],
    "evidencias": ["Projeto X", "Métrica Y"]
  }},
  "behavioral_analysis": {{
    "colaboracao": 4.0,
    "inovacao": 4.5,
    "organizacao": 4.0,
    "resiliencia": 3.5
  }},
  "cultural_fit": {{
    "score": 4.0,
    "valores_alinhados": ["Excelência técnica", "..."],
    "atencoes": ["..."]
  }},
  "recommendation": {{
    "decisao": "APROVADO",
    "justificativa": "...",
    "proximos_passos": ["Agendar técnica", "..."]
  }}
}}"""

        # P0.D canonical (audit 2026-05-21): envelope fallback definido upfront.
        # Conteudo continua sendo template stock (back-compat), mas flag
        # fallback_used=True é setada quando LLM falha — surface explícito
        # pro caller que esse parecer NAO foi gerado pelo modelo.
        report_fallback = {
            "executive_summary": (
                f"Candidato com WSI {wsi_result.classification} "
                f"({wsi_result.overall_wsi}/5.0). Análise detalhada não disponível."
            ),
            "technical_analysis": {
                "pontos_fortes": ["Análise em processamento"],
                "gaps": [],
                "evidencias": [],
            },
            "behavioral_analysis": {
                "colaboracao": 3.0,
                "inovacao": 3.0,
                "organizacao": 3.0,
                "resiliencia": 3.0,
            },
            "cultural_fit": {
                "score": 3.0,
                "valores_alinhados": ["Em avaliação"],
                "atencoes": [],
            },
            "recommendation": {
                "decisao": "AGUARDANDO",
                "justificativa": "Análise em processamento - revisar manualmente",
                "proximos_passos": ["Revisar análise manualmente"],
            },
        }

        # P0.D canonical: safe_llm_with_flag_async retorna envelope explícito.
        # Em failure (provider error / parse error / network / unknown), envelope
        # vem com success=False, fallback_used=True, failure_mode classified.
        async def _invoke_llm() -> dict:
            _response = await self.llm.safe_invoke(prompt, provider="claude")
            response = type("R", (), {"content": _response})()
            return safe_json_parse(response.content, fallback=report_fallback)

        envelope = await safe_llm_with_flag_async(
            _invoke_llm,
            fallback_data=report_fallback,
            needs_manual_review_on_fail=True,  # parecer fallback merece revisao manual
        )

        if envelope.success:
            data = envelope.data
        else:
            # Caller continua recebendo StructuredReport (back-compat) mas
            # com flag explícita — UI pode renderizar badge "Análise pendente"
            # ou fila de revisão manual.
            data = envelope.data or report_fallback
            logger.warning(
                "WSI report fallback used for candidate %s "
                "(failure_mode=%s, error=%s)",
                candidate_id,
                envelope.failure_mode.value,
                envelope.error_message,
            )

        return StructuredReport(
            candidate_id=candidate_id,
            wsi_result=wsi_result,
            executive_summary=data.get("executive_summary", "Análise não disponível"),
            technical_analysis=data.get("technical_analysis", {}),
            behavioral_analysis=data.get("behavioral_analysis", {}),
            cultural_fit=data.get("cultural_fit", {}),
            recommendation=data.get("recommendation", {}),
            # P0.D envelope (audit 2026-05-21)
            fallback_used=not envelope.success,
            needs_manual_review=envelope.needs_manual_review,
            llm_failure_mode=(
                envelope.failure_mode.value if not envelope.success else None
            ),
            llm_error_message=envelope.error_message if not envelope.success else None,
        )
    
    async def generate_feedback(
        self,
        wsi_result: WSIResult,
        responses: list[ResponseAnalysis],
        decision: Literal["aprovado", "aguardando", "nao_aprovado"]
    ) -> CandidateFeedback:
        """Gera feedback construtivo para candidato.
        
        IMPORTANTE — NEUTRALIDADE DE TOM:
        O feedback pós-triagem é enviado ANTES da decisão do recrutador.
        O candidato NÃO sabe (e não deve saber) se será aprovado ou não.
        Por isso o tom é SEMPRE construtivo e neutro, independente da
        recomendação interna da LIA. O parâmetro `decision` é mantido
        apenas para rastreabilidade interna (audit trail), NUNCA para
        modular o tom do feedback ao candidato.
        
        Alinhado com wsi_feedback_generator.py:
          - Sem score numérico
          - Sem classificação (aprovado / reprovado / aguardando)
          - Sem comparação com outros candidatos
          - Foco em comportamentos observáveis e desenvolvimento
        """
        
        strong_responses = [r for r in responses if r.final_score >= 4.0]
        development_responses = [r for r in responses if r.final_score < 3.5]
        
        strong_competencies = [f"{r.competency} ({r.final_score}/5)" for r in strong_responses]
        development_competencies = [f"{r.competency} ({r.final_score}/5)" for r in development_responses]
        
        tech_strong = [r for r in responses if r.final_score >= 4.0 and r not in development_responses]
        behav_strong_list = [r.competency for r in tech_strong if r.competency and not any(
            kw in r.competency.lower() for kw in ["python", "react", "java", "sql", "aws", "node", "go", "rust", "docker", "kubernetes", "api", "backend", "frontend", "devops", "data", "machine", "deep", "cloud"]
        )]
        
        prompt = f"""Gere um feedback estruturado e construtivo para o candidato após a etapa de triagem.

PONTOS FORTES TÉCNICOS: {strong_competencies}
PONTOS FORTES COMPORTAMENTAIS: {behav_strong_list or "Nenhum identificado com score >= 4.0"}
OPORTUNIDADES DE DESENVOLVIMENTO: {development_competencies}

TEMPLATES DE REFERÊNCIA (exemplos do RAG):
{self.report_templates[10000:13000]}

---

TOM OBRIGATÓRIO: Construtivo, empático e neutro. Reconheça pontos fortes genuínos, posicione gaps como oportunidades de crescimento. NUNCA antecipar resultado do processo (aprovação ou reprovação). O candidato ainda aguarda a decisão do recrutador.

REGRAS DE QUALIDADE DO FEEDBACK:
1. **main_message**: Mínimo 150 caracteres. Começar agradecendo a participação na etapa de triagem. NUNCA começar com "Infelizmente" ou "Parabéns". NUNCA sugerir aprovação ou reprovação.
2. **technical_strengths**: Citar ao menos 2 competências específicas mencionadas nas respostas. Não usar genéricos como "Participação no processo".
3. **development_opportunities**: Ser específico sobre o que melhorar (ex: "Aprofundar conhecimento em design patterns" vs "Estudar mais").
4. **behavioral_strengths**: Citar comportamentos observados nas respostas (ex: "Demonstrou capacidade analítica ao descrever o diagnóstico do problema").
5. **next_steps**: Informar que a equipe de recrutamento analisará o desempenho e entrará em contato com os próximos passos. NUNCA antecipar qual será a decisão.
6. **personalized_tip**: Uma dica prática e específica baseada nos gaps identificados.
7. **development_plan**: Curto prazo (1-3 meses) e médio prazo (3-6 meses) com ações concretas.
8. **recommended_resources**: Ao menos 2 recursos reais (cursos, livros, certificações, plataformas) relevantes para os gaps.

PROIBIÇÕES ABSOLUTAS:
- NUNCA revelar scores numéricos. Usar termos qualitativos ("excelente domínio", "bom conhecimento", "oportunidade de aprofundamento").
- NUNCA revelar ou sugerir a decisão (aprovado/reprovado/aguardando).
- NUNCA usar tom entusiasta/celebratório que sugira aprovação.
- NUNCA usar tom consolador/lamentoso que sugira reprovação.
- NUNCA comparar com outros candidatos.

RETORNE APENAS JSON:
{{
  "main_message": "...",
  "technical_strengths": ["...", "..."],
  "development_opportunities": ["...", "..."],
  "behavioral_strengths": ["...", "..."],
  "next_steps": "...",
  "personalized_tip": "...",
  "development_plan": {{"curto_prazo": ["..."], "medio_prazo": ["..."]}},
  "recommended_resources": ["Curso X", "Projeto Y"]
}}"""

        _fallback = {
            "main_message": "Obrigado por participar da etapa de triagem. Valorizamos o tempo e a dedicação que você investiu neste processo. A equipe de recrutamento analisará seu desempenho e entrará em contato com os próximos passos.",
            "technical_strengths": strong_competencies[:2] if strong_competencies else ["Participação completa na triagem técnica"],
            "development_opportunities": ["Continue desenvolvendo suas competências técnicas e comportamentais"],
            "behavioral_strengths": ["Engajamento demonstrado durante o processo"],
            "next_steps": "A equipe de recrutamento analisará seu desempenho e entrará em contato em breve com os próximos passos do processo.",
            "personalized_tip": "Continue aprimorando suas competências técnicas e comportamentais.",
            "development_plan": {"curto_prazo": ["Revisar conceitos fundamentais"], "medio_prazo": ["Desenvolver projetos práticos"]},
            "recommended_resources": []
        }

        # P0.D canonical (audit 2026-05-21): safe_llm_with_flag_async em vez
        # de try/except silent. Envelope explícito + flag fallback_used=True
        # quando LLM falha.
        async def _invoke_llm() -> dict:
            _response = await self.llm.safe_invoke(prompt, provider="claude")
            response = type("R", (), {"content": _response})()
            return safe_json_parse(response.content, fallback=_fallback)

        envelope = await safe_llm_with_flag_async(
            _invoke_llm,
            fallback_data=_fallback,
            # CandidateFeedback fallback eh template canonical neutro,
            # nao requer revisao obrigatoria — mas signal pra observabilidade.
            needs_manual_review_on_fail=False,
        )

        data = envelope.data if envelope.success else (envelope.data or _fallback)
        if not envelope.success:
            logger.warning(
                "WSI feedback fallback used for candidate %s "
                "(failure_mode=%s, error=%s)",
                wsi_result.candidate_id,
                envelope.failure_mode.value,
                envelope.error_message,
            )

        return CandidateFeedback(
            candidate_id=wsi_result.candidate_id,
            decision=decision,
            main_message=data.get("main_message", _fallback["main_message"]),
            technical_strengths=data.get("technical_strengths", []),
            development_opportunities=data.get("development_opportunities", []),
            behavioral_strengths=data.get("behavioral_strengths", []),
            next_steps=data.get("next_steps", _fallback["next_steps"]),
            personalized_tip=data.get("personalized_tip"),
            development_plan=data.get("development_plan"),
            recommended_resources=data.get("recommended_resources"),
            # P0.D envelope (audit 2026-05-21)
            fallback_used=not envelope.success,
            needs_manual_review=envelope.needs_manual_review,
            llm_failure_mode=(
                envelope.failure_mode.value if not envelope.success else None
            ),
            llm_error_message=envelope.error_message if not envelope.success else None,
        )


# Global WSI service instance
