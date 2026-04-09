"""
Stage Transition Automation Service

This service provides intelligent automation for candidate stage transitions:
1. Predict sub-status based on candidate context
2. Generate personalized messages using LIA (Claude)
3. Regenerate messages when sub-status changes
4. Execute transitions with communication actions

Part of LIA Automation System v1.0
"""

import json
import logging
import os
from typing import Any

from app.shared.providers.llm_client import get_anthropic_client, is_llm_available

logger = logging.getLogger(__name__)


class SubStatusPredictor:
    """Predicts appropriate sub-status based on candidate context."""
    
    REJECTION_SUBSTATUS_MAP = {
        'insufficient_technical_skills': {
            'triggers': ['low_technical_score', 'technical_gaps'],
            'display_name': 'Competências técnicas insuficientes',
            'message_focus': 'technical_development'
        },
        'another_candidate_selected': {
            'triggers': ['job_has_hire', 'competitive_process'],
            'display_name': 'Outro candidato selecionado',
            'message_focus': 'positive_competitive'
        },
        'profile_not_aligned': {
            'triggers': ['general_mismatch', 'default'],
            'display_name': 'Perfil não alinhado',
            'message_focus': 'general_feedback'
        },
        'cultural_fit': {
            'triggers': ['low_cultural_score', 'behavioral_concerns'],
            'display_name': 'Fit cultural',
            'message_focus': 'culture_fit'
        },
        'overqualified': {
            'triggers': ['high_seniority', 'overqualified_flag'],
            'display_name': 'Superqualificado para a posição',
            'message_focus': 'recognition_future'
        },
        'underqualified': {
            'triggers': ['low_overall_score', 'junior_for_role'],
            'display_name': 'Experiência insuficiente',
            'message_focus': 'development_encouragement'
        },
        'salary_expectation': {
            'triggers': ['salary_mismatch'],
            'display_name': 'Expectativa salarial incompatível',
            'message_focus': 'compensation_mismatch'
        },
        'candidate_withdrew': {
            'triggers': ['candidate_no_response', 'candidate_declined'],
            'display_name': 'Candidato desistiu',
            'message_focus': 'neutral_close'
        },
        'manager_decision': {
            'triggers': ['manager_stage_rejection'],
            'display_name': 'Decisão do gestor',
            'message_focus': 'manager_feedback'
        }
    }
    
    @classmethod
    def predict(
        cls,
        candidate_context: dict[str, Any],
        from_stage: str,
        to_stage: str
    ) -> dict[str, Any]:
        """
        Predict the most appropriate sub-status for a transition.
        
        Returns:
            Dict with predicted_substatus, confidence, reasoning
        """
        if to_stage != 'rejected':
            return cls._predict_non_rejection(candidate_context, from_stage, to_stage)
        
        return cls._predict_rejection(candidate_context, from_stage)
    
    @classmethod
    def _predict_rejection(
        cls,
        context: dict[str, Any],
        from_stage: str
    ) -> dict[str, Any]:
        """Predict rejection sub-status based on context analysis."""
        
        wsi_score = context.get('wsi_score', {})
        interview_notes = context.get('interview_notes', [])
        context.get('lia_parecer', {})
        job = context.get('job', {})
        
        overall_score = wsi_score.get('overall', 0) if wsi_score else 0
        technical_score = wsi_score.get('technical', 0) if wsi_score else 0
        cultural_score = wsi_score.get('cultural', 0) if wsi_score else 0
        
        if job.get('has_hired_candidate'):
            return {
                'predicted_substatus': 'another_candidate_selected',
                'confidence': 0.95,
                'reasoning': 'Vaga já possui candidato contratado'
            }
        
        if technical_score and technical_score < 50:
            return {
                'predicted_substatus': 'insufficient_technical_skills',
                'confidence': 0.85,
                'reasoning': f'Score técnico baixo ({technical_score}/100)'
            }
        
        if cultural_score and cultural_score < 50:
            return {
                'predicted_substatus': 'cultural_fit',
                'confidence': 0.80,
                'reasoning': f'Score cultural baixo ({cultural_score}/100)'
            }
        
        if overall_score and overall_score < 50:
            return {
                'predicted_substatus': 'underqualified',
                'confidence': 0.75,
                'reasoning': f'Score geral baixo ({overall_score}/100)'
            }
        
        if from_stage and 'manager' in from_stage:
            return {
                'predicted_substatus': 'manager_decision',
                'confidence': 0.80,
                'reasoning': 'Reprovação em etapa de entrevista com gestor'
            }
        
        if from_stage == 'interview_technical':
            tech_notes = next(
                (n for n in interview_notes if n.get('stage') == 'interview_technical'),
                None
            )
            if tech_notes and len(tech_notes.get('gaps', [])) >= 2:
                return {
                    'predicted_substatus': 'insufficient_technical_skills',
                    'confidence': 0.85,
                    'reasoning': f"Gaps técnicos identificados: {', '.join(tech_notes.get('gaps', [])[:3])}"
                }
        
        if overall_score and overall_score >= 70:
            return {
                'predicted_substatus': 'another_candidate_selected',
                'confidence': 0.70,
                'reasoning': 'Candidato qualificado, provável competição com outros'
            }
        
        return {
            'predicted_substatus': 'profile_not_aligned',
            'confidence': 0.60,
            'reasoning': 'Perfil geral não alinhado com requisitos da vaga'
        }
    
    @classmethod
    def _predict_non_rejection(
        cls,
        context: dict[str, Any],
        from_stage: str,
        to_stage: str
    ) -> dict[str, Any]:
        """Predict sub-status for non-rejection transitions."""
        
        stage_default_substatus = {
            'screening': 'cv_received',
            'long_list': 'added_to_long_list',
            'short_list': 'added_to_short_list',
            'interview_hr': 'awaiting_hr_schedule',
            'interview_technical': 'awaiting_technical_schedule',
            'interview_manager': 'awaiting_manager1_schedule',
            'interview_manager2': 'awaiting_manager2_schedule',
            'interview_final': 'awaiting_final_schedule',
            'references': 'references_requested',
            'offer': 'preparing_offer',
            'hired': 'onboarding_scheduled',
            'offer_declined': 'accepted_other_offer',
            'standby': 'temporary_hold'
        }
        
        default = stage_default_substatus.get(to_stage, 'in_progress')
        
        return {
            'predicted_substatus': default,
            'confidence': 0.90,
            'reasoning': f'Sub-status padrão para etapa {to_stage}'
        }


class MessageGenerator:
    """Generates personalized messages using Claude."""
    
    CHANNEL_LIMITS = {
        'email': {'max_words': 300, 'emoji_limit': 0, 'formality': 'formal'},
        'whatsapp': {'max_words': 100, 'emoji_limit': 3, 'formality': 'semi_formal'}
    }
    
    MESSAGE_TYPES = {
        'feedback_construtivo': {
            'tone': 'respeitoso, construtivo, encorajador',
            'structure': 'agradecimento → feedback específico → orientação → encerramento positivo',
            'focus': 'pontos fortes + áreas de desenvolvimento'
        },
        'convite_triagem': {
            'tone': 'acolhedor, explicativo, motivacional',
            'structure': 'saudação → explicação da triagem → instruções → incentivo',
            'focus': 'preparar candidato para avaliação WSI'
        },
        'aprovacao': {
            'tone': 'celebratório, encorajador, profissional',
            'structure': 'parabéns → destaque de pontos fortes → próximos passos',
            'focus': 'reconhecimento e expectativa'
        },
        'agendamento': {
            'tone': 'profissional, prático, acolhedor',
            'structure': 'convite → detalhes da entrevista → instruções → disponibilidade',
            'focus': 'informações claras e completas'
        },
        'proposta': {
            'tone': 'celebratório, formal, claro',
            'structure': 'parabéns → detalhes da proposta → próximos passos → prazo',
            'focus': 'formalização da oferta'
        },
        'boas_vindas': {
            'tone': 'muito celebratório, acolhedor',
            'structure': 'boas-vindas → expectativa → onboarding → contatos',
            'focus': 'integração e acolhimento'
        }
    }
    
    SUBSTATUS_MESSAGE_FOCUS = {
        'another_candidate_selected': 'Agradecer participação, reconhecer qualificações, manter positivo sobre competição forte',
        'insufficient_technical_skills': 'Agradecer, mencionar pontos fortes soft skills, sugerir áreas técnicas para desenvolvimento',
        'cultural_fit': 'Ser diplomático, focar em diferença de momento/estilo, não criticar personalidade',
        'profile_not_aligned': 'Feedback geral construtivo, manter porta aberta para futuro',
        'overqualified': 'Reconhecer fortemente as qualificações, expressar que a senioridade excede a posição',
        'underqualified': 'Encorajar desenvolvimento, ser construtivo sobre experiência necessária',
        'manager_decision': 'Agradecer, mencionar que foi decisão do gestor, manter profissional',
        'salary_expectation': 'Ser discreto sobre valores, mencionar incompatibilidade sem detalhes',
        'candidate_withdrew': 'Tom neutro, desejar sucesso, não assumir motivos'
    }
    
    DO_RULES = """
- Usar nome do candidato (primeiro nome para WhatsApp, nome completo para email formal)
- Manter tom respeitoso e profissional
- Ser conciso e direto ao ponto
- Usar linguagem positiva mesmo em rejeições
- Personalizar com dados específicos do candidato quando disponíveis
- Mencionar a vaga/posição específica
- Agradecer a participação do candidato
- Em aprovações: destacar 1-2 pontos fortes observados
- Em rejeições: oferecer feedback construtivo específico
- Incluir próximos passos claros quando aplicável
"""
    
    DONT_RULES = """
- NÃO usar linguagem excessivamente formal ou burocrática
- NÃO ser vago ou genérico demais
- NÃO usar clichês corporativos vazios ("infelizmente", "lamentamos informar")
- NÃO ser condescendente ou paternalista
- NÃO revelar informações confidenciais da empresa
- NÃO comparar candidato com outros diretamente
- NÃO mencionar nomes de outros candidatos
- NÃO prometer futuras oportunidades que não existem
- NÃO inventar dados que não existem no contexto
- NÃO expor scores numéricos diretamente ao candidato
- NÃO citar verbatim notas internas de entrevistadores
- NÃO usar muitos emojis (especialmente em email)
"""

    @classmethod
    async def generate(
        cls,
        candidate_context: dict[str, Any],
        to_stage: str,
        substatus: str,
        job_context: dict[str, Any],
        message_type: str,
        channel: str = 'email'
    ) -> dict[str, Any]:
        """
        Generate a personalized message using Claude.
        
        Returns:
            Dict with subject (if email), body, and metadata
        """
        if not is_llm_available():
            logger.warning("Anthropic API key not configured, using template fallback")
            return cls._generate_fallback(candidate_context, to_stage, substatus, job_context, channel)
        
        try:
            container = get_anthropic_client()

            channel_config = cls.CHANNEL_LIMITS.get(channel, cls.CHANNEL_LIMITS['email'])
            message_config = cls.MESSAGE_TYPES.get(message_type, cls.MESSAGE_TYPES['feedback_construtivo'])
            substatus_focus = cls.SUBSTATUS_MESSAGE_FOCUS.get(substatus, 'Feedback geral construtivo')
            
            candidate_name = candidate_context.get('name', 'Candidato')
            candidate_name.split()[0] if candidate_name else 'Candidato'
            job_title = job_context.get('title', 'a vaga')
            
            personalization_data = cls._build_personalization_data(candidate_context)
            
            prompt = f"""Você é LIA, assistente de recrutamento da WeDoTalent. Gere uma mensagem personalizada.

CANDIDATO:
- Nome: {candidate_name}
- Cargo Atual: {candidate_context.get('current_title', 'Não informado')}

VAGA: {job_title}
TRANSIÇÃO: Para {to_stage}
MOTIVO/SUB-STATUS: {substatus}
FOCO DA MENSAGEM: {substatus_focus}

DADOS PARA PERSONALIZAÇÃO:
{personalization_data}

CONFIGURAÇÃO:
- Canal: {channel}
- Tom: {message_config['tone']}
- Estrutura: {message_config['structure']}
- Foco: {message_config['focus']}
- Máximo de palavras: {channel_config['max_words']}
- Limite de emojis: {channel_config['emoji_limit']}

REGRAS DO QUE FAZER:
{cls.DO_RULES}

REGRAS DO QUE NÃO FAZER:
{cls.DONT_RULES}

{"Gere também um assunto para o email (máximo 60 caracteres)." if channel == 'email' else ""}

Responda em JSON com os campos: {'"subject" (para email), ' if channel == 'email' else ''}"body" (texto da mensagem)."""
            
            response_text = await container.generate_with_fallback(prompt)
            
            import json
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {'body': response_text}
            
            return {
                'subject': result.get('subject', f'Retorno sobre sua candidatura - {job_title}') if channel == 'email' else None,
                'body': result.get('body', response_text),
                'metadata': {
                    'generated_by': 'lia_claude',
                    'model': 'claude-sonnet-4-20250514',
                    'channel': channel,
                    'substatus': substatus,
                    'message_type': message_type
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating message with Claude: {e}")
            return cls._generate_fallback(candidate_context, to_stage, substatus, job_context, channel)
    
    @classmethod
    def _build_personalization_data(cls, context: dict[str, Any]) -> str:
        """Build personalization data string from context."""
        parts = []
        
        if context.get('wsi_score'):
            wsi = context['wsi_score']
            parts.append(f"- Score WSI geral: {wsi.get('overall', 'N/A')}/100")
            if wsi.get('technical'):
                parts.append(f"- Score técnico: {wsi.get('technical')}/100")
            if wsi.get('behavioral'):
                parts.append(f"- Score comportamental: {wsi.get('behavioral')}/100")
        
        if context.get('lia_parecer'):
            parecer = context['lia_parecer']
            if parecer.get('strengths'):
                parts.append(f"- Pontos fortes identificados: {', '.join(parecer['strengths'][:3])}")
            if parecer.get('development_areas'):
                parts.append(f"- Áreas de desenvolvimento: {', '.join(parecer['development_areas'][:2])}")
        
        if context.get('interview_notes'):
            for note in context['interview_notes'][:2]:
                stage_name = note.get('stage', 'Entrevista')
                if note.get('strengths'):
                    parts.append(f"- Pontos fortes ({stage_name}): {', '.join(note['strengths'][:2])}")
                if note.get('gaps'):
                    parts.append(f"- Gaps ({stage_name}): {', '.join(note['gaps'][:2])}")
        
        if not parts:
            parts.append("- Dados detalhados não disponíveis, usar tom geral construtivo")
        
        return '\n'.join(parts)
    
    @classmethod
    def _generate_fallback(
        cls,
        candidate_context: dict[str, Any],
        to_stage: str,
        substatus: str,
        job_context: dict[str, Any],
        channel: str
    ) -> dict[str, Any]:
        """Generate fallback message without LLM."""
        candidate_name = candidate_context.get('name', 'Candidato')
        first_name = candidate_name.split()[0] if candidate_name else 'Candidato'
        job_title = job_context.get('title', 'a vaga')
        
        if to_stage == 'rejected':
            body = f"""Olá {first_name},

Agradecemos muito sua participação em nosso processo seletivo para {job_title}.

Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades atuais da posição.

Mantemos seu currículo em nosso banco de talentos para futuras oportunidades que possam ser compatíveis com seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe WeDoTalent"""
        else:
            body = f"""Olá {first_name},

Gostaríamos de informá-lo(a) sobre uma atualização em sua candidatura para {job_title}.

Em breve entraremos em contato com mais detalhes sobre os próximos passos.

Atenciosamente,
Equipe WeDoTalent"""
        
        return {
            'subject': f'Retorno sobre sua candidatura - {job_title}' if channel == 'email' else None,
            'body': body,
            'metadata': {
                'generated_by': 'fallback_template',
                'channel': channel,
                'substatus': substatus
            }
        }
    
    @classmethod
    async def regenerate_for_substatus(
        cls,
        original_message: str,
        old_substatus: str,
        new_substatus: str,
        candidate_context: dict[str, Any],
        job_context: dict[str, Any],
        channel: str = 'email'
    ) -> dict[str, Any]:
        """
        Regenerate message when sub-status changes.
        Adjusts only the parts related to the reason/feedback.
        """
        if not is_llm_available():
            return await cls.generate(
                candidate_context, 'rejected', new_substatus, 
                job_context, 'feedback_construtivo', channel
            )
        
        try:
            container = get_anthropic_client()

            old_focus = cls.SUBSTATUS_MESSAGE_FOCUS.get(old_substatus, 'Feedback geral')
            new_focus = cls.SUBSTATUS_MESSAGE_FOCUS.get(new_substatus, 'Feedback geral')
            
            prompt = f"""A mensagem abaixo precisa ser ajustada porque o motivo da transição mudou.

MENSAGEM ORIGINAL:
{original_message}

MUDANÇA:
- Motivo anterior: {old_substatus} ({old_focus})
- Novo motivo: {new_substatus} ({new_focus})

CONTEXTO DO CANDIDATO:
- Nome: {candidate_context.get('name', 'Candidato')}
- Vaga: {job_context.get('title', 'a vaga')}

TAREFA:
Ajuste a mensagem para refletir o novo motivo. Mantenha:
- Estrutura geral
- Tom profissional e respeitoso
- Personalizações existentes (nome, vaga)

Altere apenas os trechos que mencionam o motivo específico ou feedback.

REGRAS:
{cls.DONT_RULES}

Responda APENAS com a mensagem ajustada, sem explicações."""

            adjusted_body = await container.generate_with_fallback(prompt)
            adjusted_body = adjusted_body.strip()
            
            return {
                'subject': None,
                'body': adjusted_body,
                'metadata': {
                    'generated_by': 'lia_claude_adjustment',
                    'old_substatus': old_substatus,
                    'new_substatus': new_substatus,
                    'adjustment_type': 'substatus_change'
                }
            }
            
        except Exception as e:
            logger.error(f"Error regenerating message: {e}")
            return await cls.generate(
                candidate_context, 'rejected', new_substatus,
                job_context, 'feedback_construtivo', channel
            )


class StageTransitionAutomationService:
    """
    Main service coordinating stage transition automation.
    """
    
    def __init__(self):
        self.predictor = SubStatusPredictor()
        self.generator = MessageGenerator()
    
    async def predict_substatus(
        self,
        candidate_context: dict[str, Any],
        from_stage: str,
        to_stage: str
    ) -> dict[str, Any]:
        """Predict appropriate sub-status for transition."""
        enable_llm = os.environ.get('ENABLE_LLM_SUBSTATUS_PREDICTION', 'true').lower() == 'true'
        
        if enable_llm and is_llm_available():
            return await self._predict_substatus_with_llm(candidate_context, from_stage, to_stage)
        
        return self.predictor.predict(candidate_context, from_stage, to_stage)
    
    async def _predict_substatus_with_llm(
        self,
        candidate_context: dict[str, Any],
        from_stage: str,
        to_stage: str
    ) -> dict[str, Any]:
        try:
            container = get_anthropic_client()

            from lia_models.recruitment_stages import DEFAULT_SUB_STATUSES
            
            stage_subs = DEFAULT_SUB_STATUSES.get(to_stage, [])
            valid_options = [s['name'] for s in stage_subs]
            
            if not valid_options:
                return SubStatusPredictor.predict(candidate_context, from_stage, to_stage)
            
            wsi = candidate_context.get('wsi_score', {}) or {}
            notes = candidate_context.get('interview_notes', []) or []
            parecer = candidate_context.get('lia_parecer', {}) or {}
            job = candidate_context.get('job', {}) or {}
            
            prompt = f"""Analise o contexto do candidato e determine o sub-status mais apropriado para a transição.

Transição: {from_stage} → {to_stage}
Cargo: {job.get('title', 'N/A')} ({job.get('seniority', 'N/A')})

Scores WSI:
- Overall: {wsi.get('overall', 'N/A')}
- Técnico: {wsi.get('technical', 'N/A')}
- Comportamental: {wsi.get('behavioral', 'N/A')}
- Cultural: {wsi.get('cultural', 'N/A')}

Notas de entrevista: {len(notes)} registros
Parecer LIA: {parecer.get('recommendation', 'N/A')}
Já tem candidato contratado: {job.get('has_hired_candidate', False)}

Sub-statuses válidos: {', '.join(valid_options)}

Responda APENAS com JSON válido:
{{"predicted_substatus": "<um dos válidos>", "confidence": <0.0-1.0>, "reasoning": "<explicação breve>"}}"""

            result_text = await container.generate_with_fallback(prompt)
            result_text = result_text.strip()
            if '{' in result_text:
                json_str = result_text[result_text.index('{'):result_text.rindex('}') + 1]
                result = json.loads(json_str)
                
                if result.get('predicted_substatus') in valid_options:
                    return result
            
            return SubStatusPredictor.predict(candidate_context, from_stage, to_stage)
            
        except Exception as e:
            logger.warning(f"LLM prediction failed, falling back to deterministic: {e}")
            return SubStatusPredictor.predict(candidate_context, from_stage, to_stage)
    
    async def generate_message(
        self,
        candidate_context: dict[str, Any],
        to_stage: str,
        substatus: str,
        job_context: dict[str, Any],
        message_type: str,
        channel: str = 'email'
    ) -> dict[str, Any]:
        """Generate personalized message for transition."""
        return await self.generator.generate(
            candidate_context, to_stage, substatus,
            job_context, message_type, channel
        )
    
    async def regenerate_for_substatus_change(
        self,
        original_message: str,
        old_substatus: str,
        new_substatus: str,
        candidate_context: dict[str, Any],
        job_context: dict[str, Any],
        channel: str = 'email'
    ) -> dict[str, Any]:
        """Regenerate message when sub-status changes."""
        return await self.generator.regenerate_for_substatus(
            original_message, old_substatus, new_substatus,
            candidate_context, job_context, channel
        )
    
    def get_available_actions(
        self,
        from_stage: str,
        to_stage: str
    ) -> list[dict[str, Any]]:
        """Get available actions for a transition."""
        actions = []
        
        if to_stage == 'rejected':
            actions.append({
                'id': 'email',
                'name': 'Enviar feedback por email',
                'description': 'Comunicar resultado com feedback construtivo',
                'recommended': True,
                'template_category': 'feedback_construtivo'
            })
            actions.append({
                'id': 'whatsapp',
                'name': 'Enviar feedback por WhatsApp',
                'description': 'Comunicação rápida via WhatsApp',
                'recommended': False,
                'template_category': 'feedback_construtivo'
            })
        
        elif to_stage == 'screening' or from_stage == 'sourcing':
            actions.append({
                'id': 'triagem_wsi',
                'name': 'Convidar para Triagem WSI',
                'description': 'LIA irá conduzir a triagem automaticamente',
                'recommended': True,
                'template_category': 'convite_triagem'
            })
            actions.append({
                'id': 'email',
                'name': 'Enviar email de contato',
                'description': 'Primeiro contato por email',
                'recommended': False,
                'template_category': 'contato_inicial'
            })
        
        elif 'interview' in to_stage:
            actions.append({
                'id': 'agendar_entrevista',
                'name': 'Agendar entrevista',
                'description': 'Enviar convite para agendamento',
                'recommended': True,
                'template_category': 'agendamento'
            })
            actions.append({
                'id': 'email',
                'name': 'Enviar convite por email',
                'description': 'Email com detalhes da entrevista',
                'recommended': False,
                'template_category': 'agendamento'
            })
        
        elif to_stage == 'offer':
            actions.append({
                'id': 'email',
                'name': 'Enviar proposta por email',
                'description': 'Proposta formal de contratação',
                'recommended': True,
                'template_category': 'proposta'
            })
        
        elif to_stage == 'hired':
            actions.append({
                'id': 'email',
                'name': 'Enviar boas-vindas',
                'description': 'Email de boas-vindas e onboarding',
                'recommended': True,
                'template_category': 'boas_vindas'
            })
        
        elif to_stage in ['long_list', 'short_list']:
            actions.append({
                'id': 'email',
                'name': 'Enviar email de aprovação',
                'description': 'Comunicar avanço no processo',
                'recommended': False,
                'template_category': 'aprovacao'
            })
        
        else:
            actions.append({
                'id': 'email',
                'name': 'Enviar email',
                'description': 'Comunicar atualização',
                'recommended': False,
                'template_category': 'follow_up'
            })
        
        actions.append({
            'id': 'apenas_mover',
            'name': 'Apenas mover',
            'description': 'Mover sem enviar comunicação',
            'recommended': False,
            'template_category': None
        })
        
        return actions
    
    async def predict_substatus_from_db(
        self,
        vacancy_candidate_id: str,
        from_stage: str,
        to_stage: str,
        db: Any = None,
    ) -> dict[str, Any]:
        """Predict substatus using real data from database."""
        if db:
            from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator
            aggregator = CandidateContextAggregator(db)
            context = await aggregator.aggregate(vacancy_candidate_id)
        else:
            context = {"vacancy_candidate_id": vacancy_candidate_id}
        
        return self.predictor.predict(context, from_stage, to_stage)
    
    async def predict_substatus_bulk_from_db(
        self,
        vacancy_candidate_ids: list[str],
        from_stage: str,
        to_stage: str,
        db: Any = None,
    ) -> list[dict[str, Any]]:
        """Predict substatus for multiple candidates using real DB data."""
        results = []
        if db:
            from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator
            aggregator = CandidateContextAggregator(db)
            contexts = await aggregator.aggregate_bulk(vacancy_candidate_ids)
            for vc_id in vacancy_candidate_ids:
                ctx = contexts.get(vc_id, {})
                prediction = self.predictor.predict(ctx, from_stage, to_stage)
                prediction["vacancy_candidate_id"] = vc_id
                results.append(prediction)
        else:
            for vc_id in vacancy_candidate_ids:
                prediction = self.predictor.predict({}, from_stage, to_stage)
                prediction["vacancy_candidate_id"] = vc_id
                results.append(prediction)
        return results


stage_transition_service = StageTransitionAutomationService()
