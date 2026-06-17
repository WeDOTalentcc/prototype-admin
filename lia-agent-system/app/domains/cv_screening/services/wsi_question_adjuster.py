"""
WSI Question Adjuster Service
Regenerates WSI screening questions based on recruiter natural language requests.
Uses Gemini 2.5 Flash for fast iteration.

P0.D fix (audit 2026-05-21, harness REGRA 4): silent fallback eliminado em
``evaluate_job_description``. Antes: try/except em torno do Gemini call
retornava template fake (``lia_suggestion = f"Para melhorar..."``) sem
flag — recrutador via parecer LIA legitimo quando na verdade era template
estatico. Agora: ``safe_llm_with_flag_async`` wrap + flags ``fallback_used``
+ ``llm_failure_mode`` no return dict pra surface explicito.

Mesmo pattern dos C19 (wsi report_generator) + outros siblings P0.D.
Doc canonical: ``app/shared/llm/safe_response.py``.
"""

from app.shared.llm_models import CANONICAL_GEMINI_FLASH_MODEL
import json

from app.domains.ai.services.llm import llm_service
import logging
import os
from typing import Any

from app.shared.llm.safe_response import safe_llm_with_flag_async

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
        self._iteration_counts: dict[str, int] = {}

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
        current_questions: list[dict[str, Any]],
        job_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
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
            from app.shared.providers.llm_factory import get_provider_for_tenant

            container = get_provider_for_tenant()
            response_text = await container.generate_with_fallback(
                system_prompt + "\n\n" + user_prompt,
                agent_type="WSIQuestionAdjusterAgent",
            )
            response_text = response_text.strip()
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
        responsibilities: list[str],
        technical_skills: list[str],
        behavioral_competencies: list[str],
        seniority: str | None = None,
        department: str | None = None,
        description: str | None = None
    ) -> dict[str, Any]:
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

        can_generate = score >= 50

        # P0.D canonical (audit 2026-05-21): template fallback definido upfront.
        # Conteudo eh template stock baseado nos counts (back-compat preservada),
        # mas flag ``fallback_used=True`` eh setada quando Gemini falha — surface
        # explicito pro caller que essa lia_suggestion NAO foi gerada pelo modelo.
        def _build_template_suggestion() -> str:
            template_parts: list[str] = []
            if resp_count < 3:
                template_parts.append(f"adicione mais {3 - resp_count} responsabilidade(s)")
            if tech_count < 3:
                template_parts.append(f"adicione mais {3 - tech_count} competência(s) técnica(s)")
            if behav_count < 3:
                template_parts.append(f"adicione mais {3 - behav_count} competência(s) comportamental(is)")
            if not seniority:
                template_parts.append("defina o nível de senioridade")
            if template_parts:
                return f"Para melhorar a qualidade das perguntas WSI, {', '.join(template_parts)}."
            return "JD bem estruturado! Pronto para gerar perguntas de triagem WSI."

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

        async def _invoke_gemini() -> str:
            # generate_native_gemini_sync eh sync; wrap em coroutine pra honrar
            # o helper canonical safe_llm_with_flag_async signature.
            response = llm_service.generate_native_gemini_sync(
                contents=[{"role": "user", "parts": [{"text": eval_prompt}]}],
                model=CANONICAL_GEMINI_FLASH_MODEL,
                generation_config={"temperature": 0.5, "max_output_tokens": 500},
            )
            return response.text.strip()

        envelope = await safe_llm_with_flag_async(
            _invoke_gemini,
            fallback_data=_build_template_suggestion(),
            # JD evaluation eh advisory (recrutador decide se gera questoes baseado
            # no score quantitativo, nao na suggestion). Template eh canonical
            # fallback funcional; nao precisa review manual obrigatorio.
            needs_manual_review_on_fail=False,
        )

        lia_suggestion = (
            envelope.data if envelope.success else envelope.data
        )  # envelope.data carries the LLM result on success OR fallback on failure

        return {
            "success": True,
            "score": score,
            "max_score": max_score,
            "indicators": indicators,
            "lia_suggestion": lia_suggestion,
            "can_generate": can_generate,
            # P0.D canonical: flags pro caller saber se a lia_suggestion eh LLM-generated
            # ou template fallback. Defaults preservam back-compat (callers que
            # ignoram esses fields continuam funcionando).
            "fallback_used": not envelope.success,
            "llm_failure_mode": (
                envelope.failure_mode.value if not envelope.success else None
            ),
            "llm_error_message": (
                envelope.error_message if not envelope.success else None
            ),
            "details": {
                "responsibilities_count": resp_count,
                "technical_skills_count": tech_count,
                "behavioral_competencies_count": behav_count,
                "seniority_defined": bool(seniority),
                "has_description": bool(description)
            }
        }


wsi_question_adjuster_service = WSIQuestionAdjusterService()
