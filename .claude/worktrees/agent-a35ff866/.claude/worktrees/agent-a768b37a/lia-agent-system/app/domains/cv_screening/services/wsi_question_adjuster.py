"""
WSI Question Adjuster Service
Regenerates WSI screening questions based on recruiter natural language requests.
Uses Gemini 2.5 Flash for fast iteration.
"""
import logging
import json
import os
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

WSI_BLOCKS = {
    0: {"name": "Abordagem Inicial", "editable": False},
    1: {"name": "Apresentação da Oportunidade", "editable": False},
    2: {"name": "Perguntas Padrão da Empresa", "editable": True, "description": "Perguntas da empresa incluindo elegibilidade"},
    3: {"name": "Avaliação Técnica", "editable": True, "description": "Skills técnicas com pesos e rubricas"},
    4: {"name": "Análise Situacional e Fit", "editable": True, "description": "Perguntas situacionais, comportamentais e culturais"},
    5: {"name": "Resultado e Encerramento", "editable": False},
}

MAX_ITERATIONS_PER_BLOCK = 5

class WSIQuestionAdjusterService:
    def __init__(self):
        self._model = None
        self._iteration_counts: Dict[str, int] = {}

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not configured")
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash")
        return self._model

    def _get_iteration_key(self, job_id: str, block_id: str) -> str:
        return f"{job_id}_{block_id}"

    def _check_iteration_limit(self, job_id: str, block_id: str) -> int:
        key = self._get_iteration_key(job_id, block_id)
        count = self._iteration_counts.get(key, 0)
        if count >= MAX_ITERATIONS_PER_BLOCK:
            raise ValueError(f"Limite de {MAX_ITERATIONS_PER_BLOCK} ajustes atingido para este bloco. Reinicie para fazer novos ajustes.")
        return count

    def _increment_iteration(self, job_id: str, block_id: str) -> int:
        key = self._get_iteration_key(job_id, block_id)
        count = self._iteration_counts.get(key, 0) + 1
        self._iteration_counts[key] = count
        return count

    async def adjust_questions(
        self,
        job_id: str,
        block_id: str,
        adjustment_prompt: str,
        current_questions: List[Dict[str, Any]],
        job_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Adjust WSI questions based on recruiter's natural language request.
        Returns adjusted questions with diff information.
        """
        iteration_count = self._check_iteration_limit(job_id, block_id)

        block_info = WSI_BLOCKS.get(int(block_id), {})
        block_name = block_info.get("name", f"Bloco {block_id}")
        block_description = block_info.get("description", "")

        system_prompt = f"""Você é especialista em metodologia WSI (WeDoTalent Skill Index) para triagem de candidatos.
Sua tarefa é regenerar perguntas de triagem mantendo a integridade metodológica do bloco "{block_name}".

CONTEXTO DO BLOCO:
- Nome: {block_name}
- Descrição: {block_description}
- As perguntas devem manter a estrutura, pesos e critérios de avaliação do WSI.

REGRAS OBRIGATÓRIAS:
1. Manter a mesma quantidade de perguntas (a menos que o recrutador peça explicitamente mais/menos)
2. Cada pergunta deve ter: text, category, type, weight (0.0-1.0)
3. Preservar a conformidade WSI: blocos, pesos, sequência lógica
4. Perguntas devem ser abertas (não sim/não) para avaliação rica
5. Calibrar complexidade conforme senioridade da vaga
6. Manter coerência com as outras perguntas do bloco

FORMATO DE SAÍDA (JSON):
{{
  "adjusted_questions": [
    {{
      "id": "string (manter o id original se possível ou gerar novo)",
      "text": "texto da pergunta",
      "category": "technical|behavioral|cultural|eligibility|situational",
      "type": "open|eliminatory|informative",
      "weight": 0.75,
      "skill_targeted": "competência alvo",
      "justification": "breve justificativa da mudança"
    }}
  ],
  "diff": [
    {{
      "question_id": "id",
      "action": "modified|added|removed",
      "before": "texto anterior (se modified)",
      "after": "texto novo (se modified ou added)",
      "reason": "razão da mudança"
    }}
  ],
  "lia_message": "mensagem conversacional da LIA explicando as mudanças"
}}"""

        job_context_str = ""
        if job_context:
            job_context_str = f"\n\nCONTEXTO DA VAGA:\n- Título: {job_context.get('title', 'N/A')}\n- Senioridade: {job_context.get('seniority', 'N/A')}\n- Departamento: {job_context.get('department', 'N/A')}\n- Skills: {', '.join(job_context.get('skills', []))}"

        user_prompt = f"""O recrutador pediu o seguinte ajuste: "{adjustment_prompt}"

Perguntas atuais do bloco "{block_name}":
{json.dumps(current_questions, ensure_ascii=False, indent=2)}
{job_context_str}

Gere as perguntas ajustadas conforme o pedido, sem comprometer a integridade metodológica WSI.
Responda APENAS com JSON válido, sem markdown."""

        try:
            model = self._get_model()
            response = model.generate_content(
                [{"role": "user", "parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                }
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

            result = json.loads(response_text)

            new_count = self._increment_iteration(job_id, block_id)

            return {
                "success": True,
                "adjusted_questions": result.get("adjusted_questions", []),
                "diff": result.get("diff", []),
                "lia_message": result.get("lia_message", "Perguntas ajustadas com sucesso!"),
                "iteration_count": new_count,
                "max_iterations": MAX_ITERATIONS_PER_BLOCK,
                "block_id": block_id,
                "block_name": block_name
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return {
                "success": False,
                "error": "Erro ao processar resposta da IA. Tente novamente.",
                "iteration_count": iteration_count,
                "max_iterations": MAX_ITERATIONS_PER_BLOCK
            }
        except Exception as e:
            logger.error(f"WSI question adjustment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "iteration_count": iteration_count,
                "max_iterations": MAX_ITERATIONS_PER_BLOCK
            }

    async def evaluate_job_description(
        self,
        job_title: str,
        responsibilities: List[str],
        technical_skills: List[str],
        behavioral_competencies: List[str],
        seniority: Optional[str] = None,
        department: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a Job Description for WSI question generation readiness.
        Returns a score, indicators, and LIA suggestions.
        """
        resp_count = len(responsibilities)
        tech_count = len(technical_skills)
        behav_count = len(behavioral_competencies)

        score = 0
        max_score = 100
        indicators = []

        if resp_count >= 3:
            score += 30
            indicators.append({"label": "Responsabilidades", "count": resp_count, "status": "sufficient", "minimum": 3})
        elif resp_count >= 1:
            score += 15
            indicators.append({"label": "Responsabilidades", "count": resp_count, "status": "partial", "minimum": 3})
        else:
            indicators.append({"label": "Responsabilidades", "count": 0, "status": "insufficient", "minimum": 3})

        if tech_count >= 3:
            score += 30
            indicators.append({"label": "Comp. Técnicas", "count": tech_count, "status": "sufficient", "minimum": 3})
        elif tech_count >= 1:
            score += 15
            indicators.append({"label": "Comp. Técnicas", "count": tech_count, "status": "partial", "minimum": 3})
        else:
            indicators.append({"label": "Comp. Técnicas", "count": 0, "status": "insufficient", "minimum": 3})

        if behav_count >= 3:
            score += 30
            indicators.append({"label": "Comp. Comportamentais", "count": behav_count, "status": "sufficient", "minimum": 3})
        elif behav_count >= 1:
            score += 15
            indicators.append({"label": "Comp. Comportamentais", "count": behav_count, "status": "partial", "minimum": 3})
        else:
            indicators.append({"label": "Comp. Comportamentais", "count": 0, "status": "insufficient", "minimum": 3})

        if seniority:
            score += 10
            indicators.append({"label": "Senioridade", "count": 1, "status": "sufficient", "minimum": 1})
        else:
            indicators.append({"label": "Senioridade", "count": 0, "status": "insufficient", "minimum": 1})

        lia_suggestion = ""
        can_generate = score >= 50

        try:
            model = self._get_model()
            eval_prompt = f"""Avalie este Job Description para geração de perguntas de triagem WSI.

Título: {job_title}
Senioridade: {seniority or 'Não definida'}
Departamento: {department or 'Não definido'}
Responsabilidades ({resp_count}): {', '.join(responsibilities[:5]) if responsibilities else 'Nenhuma'}
Competências Técnicas ({tech_count}): {', '.join(technical_skills[:5]) if technical_skills else 'Nenhuma'}
Competências Comportamentais ({behav_count}): {', '.join(behavioral_competencies[:5]) if behavioral_competencies else 'Nenhuma'}

Score atual: {score}/100
Critérios mínimos: 3 responsabilidades, 3 comp. técnicas, 3 comp. comportamentais

Gere uma avaliação curta (2-3 frases) em português do Brasil:
1. Destaque pontos fortes do JD
2. Aponte o que falta para melhorar o score
3. Dê sugestões específicas se algo estiver abaixo do mínimo

Responda APENAS com o texto da avaliação, sem formatação especial."""

            response = model.generate_content(
                [{"role": "user", "parts": [{"text": eval_prompt}]}],
                generation_config={"temperature": 0.5, "max_output_tokens": 500}
            )
            lia_suggestion = response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate LIA JD evaluation: {e}")
            suggestions = []
            if resp_count < 3:
                suggestions.append(f"adicione mais {3 - resp_count} responsabilidade(s)")
            if tech_count < 3:
                suggestions.append(f"adicione mais {3 - tech_count} competência(s) técnica(s)")
            if behav_count < 3:
                suggestions.append(f"adicione mais {3 - behav_count} competência(s) comportamental(is)")
            if not seniority:
                suggestions.append("defina o nível de senioridade")

            if suggestions:
                lia_suggestion = f"Para melhorar a qualidade das perguntas WSI, {', '.join(suggestions)}."
            else:
                lia_suggestion = "JD bem estruturado! Pronto para gerar perguntas de triagem WSI."

        return {
            "success": True,
            "score": score,
            "max_score": max_score,
            "indicators": indicators,
            "lia_suggestion": lia_suggestion,
            "can_generate": can_generate,
            "details": {
                "responsibilities_count": resp_count,
                "technical_skills_count": tech_count,
                "behavioral_competencies_count": behav_count,
                "seniority_defined": bool(seniority),
                "has_description": bool(description)
            }
        }


wsi_question_adjuster_service = WSIQuestionAdjusterService()
