"""
Communication Templates for LIA Platform.
Contains email and WhatsApp templates for candidate outreach and feedback.
"""
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# LGPD — Aviso de sub-processadores de dados (K1 — Sprint K)
#
# Este aviso deve ser incluído em toda comunicação inicial com candidatos
# que envolva envio via Twilio (WhatsApp/SMS) ou Mailgun (email).
#
# Base legal: LGPD Art. 7º, II (consentimento) + Art. 41 (encarregado)
# Revisão jurídica necessária antes de atualizar DPA com Twilio/Mailgun
# e Política de Privacidade pública.
# ---------------------------------------------------------------------------

DATA_PROCESSING_NOTICE = (
    "Seus dados pessoais fornecidos neste processo seletivo são tratados pela WeDOTalent "
    "em conformidade com a Lei Geral de Proteção de Dados (LGPD — Lei 13.709/2018). "
    "Para viabilizar a comunicação, utilizamos os seguintes sub-processadores de dados: "
    "Twilio Inc. (envio de mensagens WhatsApp/SMS) e Mailgun Inc. (envio de e-mails). "
    "Esses parceiros atuam exclusivamente sob nossas instruções e estão sujeitos a acordos "
    "de proteção de dados compatíveis com a LGPD. "
    "Você pode exercer seus direitos de titular (acesso, correção, exclusão, portabilidade) "
    "a qualquer momento pelo e-mail privacidade@wedotalent.com.br."
)

WSI_INITIAL_CONTACT_LGPD_NOTICE = (
    "\n\n---\n"
    "📋 Tratamento de dados: Este processo utiliza IA para triagem de currículos. "
    + DATA_PROCESSING_NOTICE
    + " Para não participar, basta responder 'não tenho interesse'."
)


class EmailTemplates:
    """Email templates for candidate communication."""
    
    @staticmethod
    def initial_contact(
        candidate_name: str,
        job_title: str,
        company_name: str | None,
        is_confidential: bool,
        job_challenge: str = "",
        recruiter_name: str = "Equipe de Recrutamento",
        privacy_policy_url: str = ""
    ) -> dict[str, str]:
        """Generate initial contact email."""
        
        if is_confidential:
            company_text = "uma empresa líder de mercado"
            intro = f"Estamos conduzindo um processo seletivo confidencial para uma posição de {job_title}."
        else:
            company_text = company_name or "nossa empresa"
            intro = f"A {company_text} está em busca de um(a) {job_title} para integrar nosso time."
        
        subject = f"Oportunidade: {job_title}" + (" - Processo Confidencial" if is_confidential else f" - {company_name or ''}")
        
        privacy_url_line = (
            f"Política de Privacidade: {privacy_policy_url}\n"
            if privacy_policy_url else ""
        )
        privacy_section = (
            f"\n📋 {privacy_url_line}"
            f"{DATA_PROCESSING_NOTICE}\n"
            "Caso não deseje participar do processo, basta responder este email informando.\n"
        )
        
        body = f"""Olá {candidate_name},

{intro}

Seu perfil chamou nossa atenção e acreditamos que você pode ser um excelente fit para esta posição.

{"" if not job_challenge else f'''
O DESAFIO:
{job_challenge}

'''}PRÓXIMOS PASSOS:
Se tiver interesse, convidamos você a participar de uma triagem inicial com a LIA, nossa assistente de recrutamento com inteligência artificial.

A LIA conduz entrevistas de forma:
✅ Profissional e isenta (sem viés)
✅ Humanizada e respeitosa
✅ Com feedback construtivo ao final

A conversa dura aproximadamente 15-20 minutos e pode ser feita por texto ou voz, no horário que preferir.

👉 CLIQUE AQUI PARA INICIAR A TRIAGEM

Caso prefira conversar via WhatsApp, responda este email informando seu número.
{privacy_section}
Qualquer dúvida, estamos à disposição.

Atenciosamente,
{recruiter_name}
{company_text}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def screening_reminder(
        candidate_name: str,
        job_title: str,
        hours_remaining: int = 12
    ) -> dict[str, str]:
        """Generate screening reminder email."""
        
        subject = f"Lembrete: Triagem pendente - {job_title}"
        
        body = f"""Olá {candidate_name},

Notei que você ainda não completou a triagem para a posição de {job_title}.

Você tem mais {hours_remaining} horas para finalizar a conversa.

👉 CLIQUE AQUI PARA CONTINUAR

Se tiver qualquer dificuldade ou dúvida, é só responder este email.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def screening_passed(
        candidate_name: str,
        job_title: str,
        strengths: list,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate screening passed email."""
        
        subject = f"Parabéns! Você avançou no processo - {job_title}"
        
        strengths_text = "\n".join([f"• {s}" for s in strengths[:3]]) if strengths else "• Excelente comunicação"
        
        body = f"""Olá {candidate_name},

Ótimas notícias! 🎉

Você foi aprovado(a) na triagem para a posição de {job_title}!

PONTOS FORTES IDENTIFICADOS:
{strengths_text}

PRÓXIMOS PASSOS:
Em breve entraremos em contato para agendar sua entrevista com a equipe.

Se tiver alguma restrição de agenda, por favor nos avise respondendo este email.

Parabéns e até breve!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def screening_failed(
        candidate_name: str,
        job_title: str,
        strengths: list,
        development_areas: list
    ) -> dict[str, str]:
        """Generate screening failed email."""
        
        subject = f"Resultado da triagem - {job_title}"
        
        strengths_text = "\n".join([f"• {s}" for s in strengths[:3]]) if strengths else "• Boa disposição para o processo"
        development_text = "\n".join([f"• {a}" for a in development_areas[:2]]) if development_areas else "• Aprofundamento em áreas específicas"
        
        body = f"""Olá {candidate_name},

Obrigada por participar da triagem para a posição de {job_title}.

Após uma análise cuidadosa, identificamos que outros candidatos apresentam maior aderência aos requisitos específicos desta posição.

PONTOS FORTES IDENTIFICADOS:
{strengths_text}

ÁREAS COM POTENCIAL DE DESENVOLVIMENTO:
{development_text}

Esta decisão não diminui suas qualificações profissionais. Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades mais alinhadas ao seu perfil.

Desejamos sucesso em sua jornada profissional!

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def interview_scheduled(
        candidate_name: str,
        job_title: str,
        interview_date: datetime,
        interview_link: str,
        interviewer_name: str = "Equipe"
    ) -> dict[str, str]:
        """Generate interview scheduled email."""
        
        date_formatted = interview_date.strftime("%d/%m/%Y às %H:%M")
        subject = f"Entrevista agendada - {job_title}"
        
        body = f"""Olá {candidate_name},

Sua entrevista para a posição de {job_title} está confirmada!

📅 DATA E HORA: {date_formatted}
🔗 LINK: {interview_link}
👤 ENTREVISTADOR: {interviewer_name}

DICAS:
• Teste seu áudio e vídeo antes do horário
• Procure um ambiente tranquilo e bem iluminado
• Tenha em mãos seu currículo e anotações

Caso precise reagendar, responda este email com pelo menos 24h de antecedência.

Boa sorte!

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def rejection_post_interview(
        candidate_name: str,
        job_title: str,
        feedback: str = ""
    ) -> dict[str, str]:
        """Generate rejection email after interview."""
        
        subject = f"Resultado do processo - {job_title}"
        
        feedback_section = f"\n\nFEEDBACK:\n{feedback}\n" if feedback else ""
        
        body = f"""Olá {candidate_name},

Agradecemos sua participação no processo seletivo para a posição de {job_title}.

Após avaliação cuidadosa, decidimos seguir com outros candidatos que apresentaram maior aderência ao perfil buscado neste momento.
{feedback_section}
Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def process_closed(
        candidate_name: str,
        job_title: str
    ) -> dict[str, str]:
        """Generate process closed email for remaining candidates."""
        
        subject = f"Encerramento do processo - {job_title}"
        
        body = f"""Olá {candidate_name},

Gostaríamos de informar que a posição de {job_title} foi preenchida.

Agradecemos sinceramente seu interesse e participação em nosso processo seletivo.

Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def high_match_found(
        recruiter_name: str,
        candidate_name: str,
        job_title: str,
        match_score: float,
        key_matches: list,
        candidate_profile_link: str = ""
    ) -> dict[str, str]:
        """Notify recruiter about high-match candidate."""
        
        subject = f"🎯 Match Alto Encontrado: {candidate_name} para {job_title}"
        
        matches_text = "\n".join([f"• {m}" for m in key_matches[:5]]) if key_matches else "• Perfil altamente compatível"
        
        body = f"""Olá {recruiter_name},

Identificamos um candidato com alta compatibilidade para sua vaga!

CANDIDATO: {candidate_name}
VAGA: {job_title}
SCORE DE MATCH: {match_score:.0f}%

PRINCIPAIS COMPATIBILIDADES:
{matches_text}

{"👉 VER PERFIL COMPLETO: " + candidate_profile_link if candidate_profile_link else ""}

Recomendamos priorizar o contato com este candidato.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def job_paused(
        candidate_name: str,
        job_title: str,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Notify candidates that job was paused."""
        
        subject = f"Atualização do processo - {job_title}"
        
        body = f"""Olá {candidate_name},

Gostaríamos de informar que o processo seletivo para a posição de {job_title} está temporariamente pausado.

Esta pausa não está relacionada ao seu desempenho no processo. Assim que tivermos atualizações, entraremos em contato.

Seu perfil permanece em nossa base e você continua sendo considerado(a) para esta oportunidade.

Agradecemos sua compreensão e paciência.

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def job_reactivated(
        candidate_name: str,
        job_title: str,
        company_name: str | None = None,
        next_steps: str = ""
    ) -> dict[str, str]:
        """Notify candidates that job was reactivated."""
        
        subject = f"Boas notícias! Processo reativado - {job_title}"
        
        next_steps_section = f"\n\nPRÓXIMOS PASSOS:\n{next_steps}\n" if next_steps else ""
        
        body = f"""Olá {candidate_name},

Temos boas notícias! 🎉

O processo seletivo para a posição de {job_title} foi reativado e você continua sendo considerado(a).
{next_steps_section}
Caso tenha alguma alteração em sua disponibilidade ou interesse, por favor nos avise respondendo este email.

Agradecemos sua paciência durante o período de pausa.

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def sla_violated(
        recruiter_name: str,
        job_title: str,
        sla_type: str,
        expected_time: str,
        actual_time: str,
        candidates_affected: int,
        action_required: str = ""
    ) -> dict[str, str]:
        """Alert for SLA violation."""
        
        subject = f"⚠️ Alerta de SLA Violado - {job_title}"
        
        action_section = f"\n\nAÇÃO RECOMENDADA:\n{action_required}\n" if action_required else ""
        
        body = f"""Olá {recruiter_name},

Identificamos uma violação de SLA no processo seletivo.

DETALHES:
• Vaga: {job_title}
• Tipo de SLA: {sla_type}
• Tempo esperado: {expected_time}
• Tempo atual: {actual_time}
• Candidatos afetados: {candidates_affected}
{action_section}
Por favor, tome as medidas necessárias para regularizar a situação.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def goal_at_risk(
        recruiter_name: str,
        goal_name: str,
        current_progress: float,
        target: float,
        deadline: str,
        suggestions: list
    ) -> dict[str, str]:
        """Alert for goal at risk."""
        
        subject = f"⚠️ Meta em Risco: {goal_name}"
        
        suggestions_text = "\n".join([f"• {s}" for s in suggestions[:4]]) if suggestions else "• Revise sua estratégia de sourcing"
        
        body = f"""Olá {recruiter_name},

Uma de suas metas está em risco de não ser atingida.

META: {goal_name}
PROGRESSO ATUAL: {current_progress:.0f}%
OBJETIVO: {target:.0f}%
PRAZO: {deadline}

SUGESTÕES PARA RECUPERAÇÃO:
{suggestions_text}

Posso ajudar a identificar ações para acelerar o progresso.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def goal_missed(
        recruiter_name: str,
        goal_name: str,
        achieved: float,
        target: float,
        analysis: str = "",
        next_steps: list = None
    ) -> dict[str, str]:
        """Alert for missed goal."""
        
        subject = f"📊 Resultado da Meta: {goal_name}"
        
        next_steps = next_steps or []
        next_steps_text = "\n".join([f"• {s}" for s in next_steps[:3]]) if next_steps else "• Agendar reunião para análise de causas"
        analysis_section = f"\nANÁLISE:\n{analysis}\n" if analysis else ""
        
        body = f"""Olá {recruiter_name},

O período da meta abaixo foi encerrado.

META: {goal_name}
RESULTADO: {achieved:.0f}%
OBJETIVO: {target:.0f}%
STATUS: Meta não atingida
{analysis_section}
PRÓXIMOS PASSOS RECOMENDADOS:
{next_steps_text}

Estou disponível para ajudar na análise e planejamento do próximo ciclo.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def weekly_performance(
        recruiter_name: str,
        week_start: str,
        week_end: str,
        candidates_sourced: int,
        candidates_screened: int,
        interviews_conducted: int,
        offers_made: int,
        hires_completed: int,
        highlights: list,
        areas_attention: list
    ) -> dict[str, str]:
        """Weekly performance summary."""
        
        subject = f"📊 Resumo Semanal de Performance ({week_start} - {week_end})"
        
        highlights_text = "\n".join([f"• {h}" for h in highlights[:4]]) if highlights else "• Semana produtiva!"
        attention_text = "\n".join([f"• {a}" for a in areas_attention[:3]]) if areas_attention else "• Nenhuma área crítica identificada"
        
        body = f"""Olá {recruiter_name},

Aqui está seu resumo semanal de performance:

📅 PERÍODO: {week_start} a {week_end}

📈 MÉTRICAS DA SEMANA:
• Candidatos sourced: {candidates_sourced}
• Candidatos triados: {candidates_screened}
• Entrevistas realizadas: {interviews_conducted}
• Ofertas enviadas: {offers_made}
• Contratações concluídas: {hires_completed}

✨ DESTAQUES:
{highlights_text}

⚠️ PONTOS DE ATENÇÃO:
{attention_text}

Continue o ótimo trabalho!

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def ats_sync_failed(
        recruiter_name: str,
        ats_name: str,
        error_type: str,
        error_details: str,
        affected_records: int,
        action_required: str
    ) -> dict[str, str]:
        """Alert for ATS sync failure."""
        
        subject = f"🔴 Falha na Sincronização com {ats_name}"
        
        body = f"""Olá {recruiter_name},

Detectamos uma falha na sincronização com o ATS.

DETALHES DO ERRO:
• ATS: {ats_name}
• Tipo de erro: {error_type}
• Descrição: {error_details}
• Registros afetados: {affected_records}

AÇÃO NECESSÁRIA:
{action_required}

Se o problema persistir, entre em contato com o suporte técnico.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def credits_low(
        user_name: str,
        credits_remaining: int,
        credits_limit: int,
        estimated_days_remaining: int,
        upgrade_link: str = ""
    ) -> dict[str, str]:
        """Alert for low Pearch credits."""
        
        subject = f"⚠️ Créditos Pearch Baixos - {credits_remaining} restantes"
        
        upgrade_section = f"\n\n👉 AUMENTAR CRÉDITOS: {upgrade_link}" if upgrade_link else ""
        
        body = f"""Olá {user_name},

Seus créditos Pearch estão acabando.

SITUAÇÃO ATUAL:
• Créditos restantes: {credits_remaining}
• Limite total: {credits_limit}
• Estimativa de duração: {estimated_days_remaining} dias

Recomendamos renovar seus créditos para não interromper suas buscas.
{upgrade_section}

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def welcome_user(
        user_name: str,
        company_name: str,
        role: str,
        login_link: str,
        quick_start_tips: list
    ) -> dict[str, str]:
        """Welcome email for new user."""
        
        subject = "Bem-vindo(a) à plataforma LIA! 🎉"
        
        tips_text = "\n".join([f"• {t}" for t in quick_start_tips[:5]]) if quick_start_tips else "• Explore o dashboard para conhecer suas métricas"
        
        body = f"""Olá {user_name},

Seja bem-vindo(a) à plataforma LIA! 🎉

Sua conta foi criada com sucesso.

DETALHES DA CONTA:
• Empresa: {company_name}
• Perfil: {role}
• Acesso: {login_link}

DICAS PARA COMEÇAR:
{tips_text}

Estou aqui para ajudar você a otimizar seus processos de recrutamento. Qualquer dúvida, é só perguntar!

Atenciosamente,
LIA - Sua Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def password_changed(
        user_name: str,
        change_date: str,
        ip_address: str = "",
        support_link: str = ""
    ) -> dict[str, str]:
        """Password changed confirmation."""
        
        subject = "🔐 Sua senha foi alterada"
        
        ip_section = f"\n• IP: {ip_address}" if ip_address else ""
        support_section = f"\n\nSe você não realizou esta alteração, entre em contato imediatamente: {support_link}" if support_link else "\n\nSe você não realizou esta alteração, entre em contato com o suporte imediatamente."
        
        body = f"""Olá {user_name},

Sua senha foi alterada com sucesso.

DETALHES:
• Data/Hora: {change_date}{ip_section}
{support_section}

Atenciosamente,
Equipe de Segurança LIA"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def approval_pending(
        approver_name: str,
        request_type: str,
        requester_name: str,
        request_details: str,
        deadline: str,
        approval_link: str
    ) -> dict[str, str]:
        """Approval pending notification."""
        
        subject = f"⏳ Aprovação Pendente: {request_type}"
        
        body = f"""Olá {approver_name},

Você tem uma nova solicitação aguardando sua aprovação.

SOLICITAÇÃO:
• Tipo: {request_type}
• Solicitante: {requester_name}
• Prazo: {deadline}

DETALHES:
{request_details}

👉 APROVAR/REJEITAR: {approval_link}

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def approval_expired(
        approver_name: str,
        request_type: str,
        requester_name: str,
        original_deadline: str,
        consequence: str = ""
    ) -> dict[str, str]:
        """Approval expired notification."""
        
        subject = f"⚠️ Aprovação Expirada: {request_type}"
        
        consequence_section = f"\n\nCONSEQUÊNCIA:\n{consequence}" if consequence else ""
        
        body = f"""Olá {approver_name},

Uma solicitação de aprovação expirou sem resposta.

SOLICITAÇÃO:
• Tipo: {request_type}
• Solicitante: {requester_name}
• Prazo original: {original_deadline}
{consequence_section}

Por favor, entre em contato com {requester_name} para resolver a situação.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def feedback_request(
        candidate_name: str,
        job_title: str,
        company_name: str | None = None,
        feedback_link: str = "",
        incentive: str = ""
    ) -> dict[str, str]:
        """Feedback request email."""
        
        subject = f"Sua opinião é importante - Processo {job_title}"
        
        incentive_section = f"\n\n{incentive}\n" if incentive else ""
        
        body = f"""Olá {candidate_name},

Esperamos que esteja bem!

Gostaríamos de saber sua opinião sobre sua experiência no processo seletivo para {job_title}.

Sua feedback é muito importante para melhorarmos continuamente nosso processo.
{incentive_section}
A pesquisa leva menos de 2 minutos:

👉 RESPONDER PESQUISA: {feedback_link}

Agradecemos antecipadamente sua colaboração!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def offer_sent(
        candidate_name: str,
        job_title: str,
        salary_offered: float | None = None,
        start_date: str | None = None,
        response_deadline: str | None = None,
        offer_details: dict[str, Any] | None = None,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate offer sent email to candidate."""
        
        subject = f"🎉 Proposta de Emprego - {job_title}"
        
        salary_section = f"\n💰 REMUNERAÇÃO: R$ {salary_offered:,.2f}" if salary_offered else ""
        start_section = f"\n📅 DATA DE INÍCIO PROPOSTA: {start_date}" if start_date else ""
        deadline_section = f"\n\n⏰ Por favor, responda até {response_deadline} para garantir sua vaga." if response_deadline else ""
        
        benefits_section = ""
        if offer_details and "benefits" in offer_details:
            benefits = offer_details.get("benefits", [])
            if benefits:
                benefits_text = "\n".join([f"• {b}" for b in benefits])
                benefits_section = f"\n\n🎁 BENEFÍCIOS:\n{benefits_text}"
        
        body = f"""Olá {candidate_name},

Temos o prazer de informar que você foi selecionado(a) para a posição de {job_title}!

Após avaliar cuidadosamente seu perfil e desempenho durante o processo seletivo, estamos convictos de que você será uma excelente adição à nossa equipe.

DETALHES DA PROPOSTA:{salary_section}{start_section}{benefits_section}
{deadline_section}

PRÓXIMOS PASSOS:
1. Revise os termos da proposta
2. Confirme sua aceitação respondendo este email
3. Aguarde as instruções para onboarding

Caso tenha dúvidas ou precise de esclarecimentos, estamos à disposição para conversar.

Ficamos muito felizes com sua chegada!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def candidate_hired_welcome(
        candidate_name: str,
        job_title: str,
        hire_date: str | None = None,
        department: str | None = None,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate welcome email for newly hired candidate."""
        
        subject = f"🎉 Bem-vindo(a) à equipe! - {job_title}"
        
        start_section = f"\n📅 DATA DE INÍCIO: {hire_date}" if hire_date else ""
        department_section = f"\n🏢 DEPARTAMENTO: {department}" if department else ""
        
        body = f"""Olá {candidate_name},

Seja muito bem-vindo(a) à nossa equipe! 🎉

Estamos muito felizes em tê-lo(a) conosco como nosso(a) novo(a) {job_title}.

INFORMAÇÕES IMPORTANTES:{start_section}{department_section}

O QUE ESPERAR NOS PRIMEIROS DIAS:
• Recebimento de credenciais de acesso aos sistemas
• Apresentação à equipe e tour pelo escritório (se aplicável)
• Reunião de onboarding com seu gestor
• Treinamentos iniciais e integração

Estamos preparando tudo para sua chegada e queremos que você se sinta acolhido(a) desde o primeiro dia.

Se tiver qualquer dúvida antes do início, não hesite em entrar em contato.

Até breve!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def candidate_rejected(
        candidate_name: str,
        job_title: str,
        rejection_reason: str | None = None,
        rejection_stage: str | None = None,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate rejection email for candidate."""
        
        subject = f"Resultado do processo seletivo - {job_title}"
        
        stage_info = f" na etapa de {rejection_stage}" if rejection_stage else ""
        
        feedback_section = ""
        if rejection_reason:
            feedback_section = f"""

FEEDBACK:
{rejection_reason}

Esperamos que este feedback seja útil para sua jornada profissional."""
        
        body = f"""Olá {candidate_name},

Agradecemos imensamente seu interesse e participação no processo seletivo para a posição de {job_title}.

Após uma análise cuidadosa{stage_info}, decidimos seguir com outros candidatos que apresentaram maior aderência ao perfil buscado neste momento.

Esta decisão não reflete seu valor como profissional. O mercado de trabalho é competitivo e muitas vezes a decisão depende de fatores específicos da vaga em questão.
{feedback_section}

PRÓXIMOS PASSOS:
• Seu perfil permanece em nosso banco de talentos
• Entraremos em contato caso surjam oportunidades alinhadas ao seu perfil
• Fique à vontade para se candidatar a futuras vagas em nossa empresa

Desejamos muito sucesso em sua carreira!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def workforce_variance(
        manager_name: str,
        department: str,
        planned_headcount: int,
        actual_headcount: int,
        variance: int,
        variance_reasons: list,
        recommendations: list
    ) -> dict[str, str]:
        """Workforce variance notification."""
        
        subject = f"📊 Variância de Workforce - {department}"
        
        variance_type = "acima" if variance > 0 else "abaixo"
        reasons_text = "\n".join([f"• {r}" for r in variance_reasons[:4]]) if variance_reasons else "• Análise em andamento"
        recommendations_text = "\n".join([f"• {r}" for r in recommendations[:3]]) if recommendations else "• Revisar planejamento"
        
        body = f"""Olá {manager_name},

Identificamos uma variância no headcount do departamento {department}.

SITUAÇÃO ATUAL:
• Headcount planejado: {planned_headcount}
• Headcount atual: {actual_headcount}
• Variância: {abs(variance)} ({variance_type} do planejado)

POSSÍVEIS CAUSAS:
{reasons_text}

RECOMENDAÇÕES:
{recommendations_text}

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def upcoming_hires(
        manager_name: str,
        period: str,
        hires: list,
        total_hires: int,
        onboarding_checklist: list
    ) -> dict[str, str]:
        """Upcoming hires notification."""
        
        subject = f"📅 Próximas Contratações - {period}"
        
        hires_text = "\n".join([f"• {h}" for h in hires[:10]]) if hires else "• Nenhuma contratação agendada"
        checklist_text = "\n".join([f"• {c}" for c in onboarding_checklist[:5]]) if onboarding_checklist else "• Preparar estação de trabalho"
        
        body = f"""Olá {manager_name},

Aqui está o resumo das próximas contratações para {period}.

TOTAL DE NOVOS COLABORADORES: {total_hires}

CONTRATAÇÕES AGENDADAS:
{hires_text}

CHECKLIST DE ONBOARDING:
{checklist_text}

Certifique-se de que tudo esteja preparado para receber os novos colaboradores.

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def follow_up(
        candidate_name: str,
        job_title: str,
        days_inactive: int,
        current_stage: str,
        follow_up_type: str = "general",
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate follow-up email for inactive candidates based on their current stage."""
        
        stage_messages = {
            "triagem": {
                "subject": f"Lembrete: Triagem pendente - {job_title}",
                "intro": "Notamos que você ainda não completou a triagem para esta posição.",
                "action": "Clique no link abaixo para continuar sua triagem:\n\n👉 CLIQUE AQUI PARA CONTINUAR A TRIAGEM",
                "urgency": "Gostaríamos muito de conhecer melhor seu perfil!"
            },
            "entrevista": {
                "subject": f"Acompanhamento: Processo seletivo - {job_title}",
                "intro": f"Faz {days_inactive} dias que não temos novidades sobre sua disponibilidade para a entrevista.",
                "action": "Por favor, responda este email informando:\n• Sua disponibilidade de horários\n• Preferência por entrevista presencial ou online",
                "urgency": "Estamos ansiosos para dar continuidade ao seu processo!"
            },
            "proposta": {
                "subject": f"Aguardando retorno: Proposta - {job_title}",
                "intro": f"Faz {days_inactive} dias que enviamos nossa proposta e gostaríamos de saber sua decisão.",
                "action": "Por favor, nos informe:\n• Se você aceita a proposta\n• Se precisa de mais tempo para decidir\n• Se tem alguma dúvida que possamos esclarecer",
                "urgency": "Estamos à disposição para esclarecer qualquer dúvida!"
            },
            "general": {
                "subject": f"Gostaríamos de saber como você está - {job_title}",
                "intro": f"Faz {days_inactive} dias que não temos novidades do seu processo seletivo.",
                "action": "Por favor, responda este email para confirmar seu interesse em continuar no processo.",
                "urgency": "Aguardamos seu retorno!"
            }
        }
        
        stage_key = current_stage.lower() if current_stage and current_stage.lower() in stage_messages else "general"
        message_data = stage_messages[stage_key]
        
        body = f"""Olá {candidate_name},

{message_data['intro']}

Você está participando do processo seletivo para a posição de {job_title}{f' na {company_name}' if company_name else ''}.

{message_data['action']}

{message_data['urgency']}

Caso tenha decidido não continuar no processo, agradecemos se puder nos informar.

Atenciosamente,
LIA - Assistente de Recrutamento
{company_name or ''}"""

        return {"subject": message_data["subject"], "body": body}
    
    @staticmethod
    def inactive_candidate_alert(
        recruiter_name: str,
        candidate_name: str,
        job_title: str,
        days_inactive: int,
        current_stage: str,
        last_activity: str = "",
        candidate_profile_link: str = ""
    ) -> dict[str, str]:
        """Alert recruiter about inactive candidate."""
        
        subject = f"⏰ Candidato Inativo: {candidate_name} - {job_title}"
        
        activity_info = f"\n• Última atividade: {last_activity}" if last_activity else ""
        link_section = f"\n\n👉 VER PERFIL: {candidate_profile_link}" if candidate_profile_link else ""
        
        body = f"""Olá {recruiter_name},

Um candidato está sem atividade há {days_inactive} dias.

DETALHES:
• Candidato: {candidate_name}
• Vaga: {job_title}
• Etapa atual: {current_stage}
• Dias inativo: {days_inactive}{activity_info}

AÇÕES RECOMENDADAS:
• Enviar follow-up para reengajar o candidato
• Verificar se há pendências internas
• Considerar mover para banco de talentos se não houver retorno
{link_section}

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def no_show_first(
        candidate_name: str,
        job_title: str,
        interview_datetime: datetime,
        interviewer_name: str = "Equipe",
        reschedule_link: str = "",
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate email for first no-show - polite reschedule offer."""
        
        date_formatted = interview_datetime.strftime("%d/%m/%Y às %H:%M")
        subject = f"Perdemos você na entrevista - {job_title}"
        
        reschedule_section = f"\n\n👉 REAGENDAR ENTREVISTA: {reschedule_link}" if reschedule_link else "\n\nPor favor, responda este email com sua disponibilidade para reagendarmos."
        
        body = f"""Olá {candidate_name},

Sentimos sua falta na entrevista agendada para o dia {date_formatted} referente à posição de {job_title}.

Sabemos que imprevistos acontecem e gostaríamos de oferecer a oportunidade de reagendar.

SOBRE A ENTREVISTA:
• Posição: {job_title}
• Entrevistador: {interviewer_name}
• Data original: {date_formatted}
{reschedule_section}

Caso não consiga participar do processo, por favor nos informe para que possamos atualizar seu status.

Aguardamos seu retorno!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def no_show_final(
        candidate_name: str,
        job_title: str,
        no_show_count: int,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Generate email for final no-show notice - before rejection."""
        
        subject = f"Aviso importante sobre seu processo - {job_title}"
        
        body = f"""Olá {candidate_name},

Infelizmente, identificamos que você não compareceu às entrevistas agendadas ({no_show_count} ausências registradas) para a posição de {job_title}.

Entendemos que imprevistos podem acontecer, mas precisamos dar continuidade ao processo seletivo.

SITUAÇÃO ATUAL:
• Posição: {job_title}
• Ausências registradas: {no_show_count}

PRÓXIMOS PASSOS:
Caso ainda tenha interesse nesta oportunidade, por favor entre em contato conosco nas próximas 48 horas explicando a situação. Caso contrário, seu processo será encerrado.

Se decidiu seguir por outro caminho, agradecemos seu interesse e desejamos sucesso em sua jornada profissional!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}
    
    @staticmethod
    def no_show_recruiter_alert(
        recruiter_name: str,
        candidate_name: str,
        job_title: str,
        interview_datetime: datetime,
        no_show_count: int,
        recommendation: str,
        candidate_profile_link: str = ""
    ) -> dict[str, str]:
        """Alert recruiter about candidate no-show."""
        
        date_formatted = interview_datetime.strftime("%d/%m/%Y às %H:%M")
        emoji = "⚠️" if no_show_count == 1 else "🚨"
        
        subject = f"{emoji} No-Show: {candidate_name} - {job_title}"
        
        link_section = f"\n\n👉 VER PERFIL: {candidate_profile_link}" if candidate_profile_link else ""
        
        body = f"""Olá {recruiter_name},

O candidato abaixo não compareceu à entrevista agendada.

DETALHES:
• Candidato: {candidate_name}
• Vaga: {job_title}
• Data/Hora: {date_formatted}
• Total de ausências: {no_show_count}

RECOMENDAÇÃO:
{recommendation}
{link_section}

Atenciosamente,
LIA - Assistente de Recrutamento"""

        return {"subject": subject, "body": body}


    @staticmethod
    def job_cancelled(
        candidate_name: str,
        job_title: str,
        company_name: str | None = None
    ) -> dict[str, str]:
        """Notify candidates that job was cancelled."""

        subject = f"Atualização do processo - {job_title}"

        body = f"""Olá {candidate_name},

Gostaríamos de informar que o processo seletivo para a posição de {job_title} foi encerrado.

Esta decisão não está relacionada ao seu desempenho ou participação no processo. Agradecemos sinceramente seu tempo e dedicação.

Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
{company_name or 'Equipe de Recrutamento'}"""

        return {"subject": subject, "body": body}


class WhatsAppTemplates:
    """WhatsApp templates for candidate communication."""
    
    @staticmethod
    def initial_contact(
        candidate_name: str,
        job_title: str,
        company_name: str | None,
        is_confidential: bool,
        privacy_policy_url: str = ""
    ) -> str:
        """Generate initial contact WhatsApp message with AI disclosure and LGPD consent."""
        
        privacy_line = (
            f"Ao continuar, você concorda com nossa Política de Privacidade em {privacy_policy_url}. "
            if privacy_policy_url else ""
        )
        return (
            f"Olá {candidate_name}, tudo bem?\n"
            f"Estamos fazendo uma triagem inicial para a vaga de {job_title}.\n"
            "Gostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas "
            "pela LIA, nossa assistente de recrutamento com inteligência artificial (IA). "
            "Esta conversa é processada via Twilio (sub-processador de dados — LGPD). "
            f"{privacy_line}"
            "Responda 'NÃO' se não deseja participar.\n"
            "Você pode responder agora?"
        )
    
    @staticmethod
    def screening_start(candidate_name: str, job_title: str, duration_minutes: int = 10) -> str:
        """Generate screening start message with preparation tips."""

        return (
            f"Ótimo, {candidate_name}! Vamos começar.\n\n"
            f"Esta triagem é para a posição de *{job_title}*.\n\n"
            f"Dicas rápidas:\n"
            f"✓ Responda de forma natural — não há resposta certa ou errada\n"
            f"✓ Você pode responder por texto ou áudio\n"
            f"✓ Leva cerca de {duration_minutes} minutos\n\n"
            f"Pronto(a) para começar?"
        )

    @staticmethod
    def screening_reminder(candidate_name: str, hours_remaining: int) -> str:
        """Generate screening reminder message."""
        
        return f"""Oi {candidate_name}! 👋

Vi que nossa conversa ficou pausada. Você ainda tem *{hours_remaining}h* para completar a triagem.

Posso continuar de onde paramos quando estiver disponível. É só me chamar!"""
    
    @staticmethod
    def screening_passed(
        candidate_name: str,
        strengths: list
    ) -> str:
        """Generate screening passed message."""
        
        strengths_text = "\n".join([f"• {s}" for s in strengths[:3]]) if strengths else "• Excelente comunicação"
        
        return f"""Parabéns, {candidate_name}! 🎉

Você foi aprovado(a) na triagem!

*Seus pontos fortes:*
{strengths_text}

Vou conversar com o recrutador sobre seu perfil e em breve retorno com informações sobre a próxima etapa.

Qualquer dúvida, é só me chamar!"""
    
    @staticmethod
    def screening_failed(
        candidate_name: str,
        strengths: list,
        development_areas: list
    ) -> str:
        """Generate screening failed message."""
        
        strengths_text = "\n".join([f"• {s}" for s in strengths[:3]]) if strengths else "• Boa disposição"
        development_text = "\n".join([f"• {a}" for a in development_areas[:2]]) if development_areas else "• Aprofundamento técnico"
        
        return f"""Olá {candidate_name},

Obrigada por participar da triagem! Foi muito bom conversar com você.

*Pontos fortes:*
{strengths_text}

*Áreas para desenvolvimento:*
{development_text}

Para esta posição específica, seguiremos com outros candidatos. Mas seu perfil fica em nosso banco e te aviso sobre outras oportunidades!

Sucesso! 🍀"""
    
    @staticmethod
    def interview_scheduled(
        candidate_name: str,
        interview_date: datetime,
        interview_link: str
    ) -> str:
        """Generate interview scheduled message."""
        
        date_formatted = interview_date.strftime("%d/%m às %H:%M")
        
        return f"""Oi {candidate_name}! 📅

Sua entrevista está agendada:

*Data:* {date_formatted}
*Link:* {interview_link}

Vou te lembrar no dia, tá?

Boa sorte! 🍀"""
    
    @staticmethod
    def interview_reminder(
        candidate_name: str,
        interview_date: datetime,
        interview_link: str,
        hours_before: int = 2
    ) -> str:
        """Generate interview reminder message."""
        
        time_formatted = interview_date.strftime("%H:%M")
        
        return f"""Oi {candidate_name}! 👋

Lembrete: sua entrevista é *hoje às {time_formatted}*!

*Link:* {interview_link}

Dicas rápidas:
✅ Teste áudio e vídeo
✅ Ambiente tranquilo
✅ Tenha seu currículo à mão

Boa sorte! 🍀"""
    
    @staticmethod
    def rejection_feedback(
        candidate_name: str,
        custom_feedback: str = ""
    ) -> str:
        """Generate rejection feedback message."""
        
        feedback = custom_feedback or "Decidimos seguir com outros candidatos para esta posição."
        
        return f"""Olá {candidate_name},

{feedback}

Seu perfil fica em nosso banco de talentos. Te aviso sobre novas oportunidades!

Sucesso na sua jornada! 🍀"""
    
    @staticmethod
    def process_closed(candidate_name: str, job_title: str) -> str:
        """Generate process closed message."""
        
        return f"""Olá {candidate_name}! 👋

A posição de *{job_title}* foi preenchida.

Agradeço seu interesse! Seu perfil fica em nosso banco e te aviso sobre novas oportunidades.

Sucesso! 🍀"""
    
    @staticmethod
    def interview_reminder_urgent(
        candidate_name: str,
        interview_date: datetime,
        interview_link: str,
        job_title: str = ""
    ) -> str:
        """Generate urgent interview reminder (1 hour before)."""
        
        time_formatted = interview_date.strftime("%H:%M")
        job_info = f" para *{job_title}*" if job_title else ""
        
        return f"""⏰ {candidate_name}, sua entrevista{job_info} começa em *1 hora*!

*Horário:* {time_formatted}
*Link:* {interview_link}

Últimas dicas:
✅ Verifique conexão de internet
✅ Teste câmera e microfone agora
✅ Tenha água por perto

Te desejo muito sucesso! 🍀"""
    
    @staticmethod
    def offer_deadline_reminder(
        candidate_name: str,
        job_title: str,
        deadline: str,
        hours_remaining: int,
        response_link: str = ""
    ) -> str:
        """Generate offer deadline reminder."""
        
        urgency = "⚠️" if hours_remaining <= 24 else "📋"
        
        link_section = f"\n\n👉 Responder: {response_link}" if response_link else ""
        
        return f"""{urgency} Oi {candidate_name}!

Lembrete: sua proposta para *{job_title}* expira em *{hours_remaining}h* ({deadline}).

Precisa de mais tempo ou tem alguma dúvida? Me avisa que posso ajudar!
{link_section}
Aguardo seu retorno! 😊"""
    
    @staticmethod
    def follow_up(
        candidate_name: str,
        job_title: str,
        days_inactive: int,
        current_stage: str
    ) -> str:
        """Generate follow-up WhatsApp message for inactive candidates."""
        
        stage_messages = {
            "triagem": f"""Oi {candidate_name}! 👋

Vi que sua triagem para *{job_title}* ficou pausada há {days_inactive} dias.

Posso te ajudar a continuar? É só me chamar!

Aguardo seu retorno 😊""",
            "entrevista": f"""Oi {candidate_name}! 👋

Faz {days_inactive} dias que não falamos sobre a entrevista para *{job_title}*.

Você ainda tem interesse? Me conta como posso te ajudar!

Aguardo seu retorno 😊""",
            "proposta": f"""Oi {candidate_name}! 👋

Faz {days_inactive} dias que enviamos a proposta para *{job_title}*.

Tem alguma dúvida que posso esclarecer? Estou aqui para ajudar!

Aguardo seu retorno 😊""",
            "general": f"""Oi {candidate_name}! 👋

Faz {days_inactive} dias que não temos novidades do seu processo para *{job_title}*.

Ainda tem interesse na vaga? É só me chamar!

Aguardo seu retorno 😊"""
        }
        
        stage_key = current_stage.lower() if current_stage and current_stage.lower() in stage_messages else "general"
        return stage_messages[stage_key]
    
    @staticmethod
    def no_show_first(
        candidate_name: str,
        job_title: str,
        interview_datetime: datetime,
        reschedule_link: str = ""
    ) -> str:
        """Generate WhatsApp message for first no-show - polite reschedule offer."""
        
        date_formatted = interview_datetime.strftime("%d/%m às %H:%M")
        
        link_section = f"\n\n👉 Reagendar: {reschedule_link}" if reschedule_link else ""
        
        return f"""Oi {candidate_name}! 👋

Sentimos sua falta na entrevista de hoje ({date_formatted}) para *{job_title}*.

Imprevistos acontecem! Podemos reagendar para outro horário que funcione melhor para você?
{link_section}
Me avisa sua disponibilidade que eu ajudo a remarcar! 😊"""

    @staticmethod
    def no_show_final(
        candidate_name: str,
        job_title: str,
        no_show_count: int
    ) -> str:
        """Generate WhatsApp message for final no-show notice."""
        
        return f"""Oi {candidate_name},

Infelizmente você não compareceu às entrevistas agendadas para *{job_title}* ({no_show_count} ausências).

Caso ainda tenha interesse, por favor entre em contato conosco nas próximas *48 horas*.

Se não conseguir, seu processo será encerrado. Desejamos sucesso na sua jornada! 🍀"""


    @staticmethod
    def job_paused(candidate_name: str, job_title: str) -> str:
        """Generate job paused WhatsApp message."""

        return f"""Olá {candidate_name}! 👋

Informamos que o processo para *{job_title}* está temporariamente pausado. Não se preocupe, isso não tem relação com seu desempenho.

Assim que tivermos novidades, entraremos em contato. Seu perfil continua sendo considerado.

Agradecemos sua paciência! 🙏"""

    @staticmethod
    def job_reactivated(candidate_name: str, job_title: str) -> str:
        """Generate job reactivated WhatsApp message."""

        return f"""Oi {candidate_name}! 🎉

Boas notícias! O processo para *{job_title}* foi reativado e você continua sendo considerado(a)!

Caso tenha mudanças na sua disponibilidade, é só me avisar.

Obrigado pela paciência! 😊"""

    @staticmethod
    def job_cancelled(candidate_name: str, job_title: str) -> str:
        """Generate job cancelled WhatsApp message."""

        return f"""Olá {candidate_name}! 👋

Informamos que o processo para *{job_title}* foi encerrado. Essa decisão não tem relação com seu desempenho.

Seu perfil permanece em nosso banco de talentos e entraremos em contato sobre novas oportunidades.

Desejamos sucesso! 🍀"""
    
    @staticmethod
    def consent_request(
        job_title: str,
        ai_name: str = "Lia",
        is_affirmative: bool = False,
        affirmative_type: str | None = None,
    ) -> str:
        """Generate LGPD consent request for WhatsApp triagem.

        REGRA LGPD: o texto de consentimento DEVE mencionar WeDOTalent (controlador legal,
        LGPD Art. 7/9), prazo de retencao, DPO e canal de revogacao. ai_name NAO substitui
        "WeDOTalent" neste texto — ver ADR voice plugin consent_request canonical rule.
        """
        base = (
            f"Esta triagem e conduzida por inteligencia artificial. Um recrutador "
            f"revisara sua candidatura antes de qualquer decisao sobre o processo.\n\n"
            f"Para participar, a WeDOTalent precisa do seu consentimento conforme a LGPD.\n\n"
            f"Suas respostas serao coletadas e processadas exclusivamente para avaliacao "
            f"da sua candidatura a vaga de {job_title}. Os dados sao armazenados por ate "
            f"12 meses e nao serao usados para reconhecimento biometrico.\n\n"
            f"Voce pode a qualquer momento solicitar acesso, correcao ou exclusao "
            f"pelo e-mail privacidadededados@wedotalent.cc."
        )
        if is_affirmative and affirmative_type:
            type_label = {
                "pcd": "condicao de PCD",
                "racial": "autodeclaracao racial",
                "gender": "identidade de genero",
            }.get(affirmative_type, affirmative_type)
            base += (
                f"\n\nAlem disso, esta e uma vaga de acao afirmativa. Uma das perguntas "
                f"coletara informacao sobre {type_label}. "
                f"Voce tambem consente com esta coleta adicional? (Art. 11 \u00a72o, II \u2014 LGPD)."
            )
        base += (
            "\n\nVoce consente com o uso dos seus dados nesta triagem?"
            "\nResponda *SIM* para continuar ou *NAO* para recusar."
        )
        return base

    @staticmethod
    def expiry_reminder(job_title: str, hours_left: int) -> str:
        """Generate pre-expiry reminder for sessions awaiting consent or response."""
        return (
            f"Ola! Ainda esta disponivel para a triagem da vaga de {job_title}?\n"
            f"Seu prazo para participar expira em {hours_left} hora(s). "
            f"Acesse o link que enviamos anteriormente para continuar."
        )



class RecruiterNotificationTemplates:
    """Templates for recruiter notifications via Teams/Chat."""
    
    @staticmethod
    def daily_briefing(
        recruiter_name: str,
        pending_interviews: int,
        pending_approvals: int,
        active_screenings: int,
        candidates_to_contact: int,
        today_tasks: list
    ) -> str:
        """Generate daily briefing message."""
        
        tasks_text = "\n".join([f"• {t}" for t in today_tasks[:5]]) if today_tasks else "• Nenhuma tarefa pendente"
        
        return f"""☀️ Bom dia, {recruiter_name}!

Aqui está seu resumo do dia:

📊 *VISÃO GERAL:*
• {pending_interviews} entrevistas agendadas para hoje
• {pending_approvals} aprovações pendentes
• {active_screenings} triagens em andamento
• {candidates_to_contact} candidatos aguardando contato

📋 *TAREFAS PRIORITÁRIAS:*
{tasks_text}

Posso ajudar com algo específico?"""
    
    @staticmethod
    def end_of_day_summary(
        recruiter_name: str,
        interviews_completed: int,
        candidates_screened: int,
        approvals_given: int,
        pending_items: list
    ) -> str:
        """Generate end of day summary message."""
        
        pending_text = "\n".join([f"• {p}" for p in pending_items[:5]]) if pending_items else "• Tudo em dia!"
        
        return f"""🌙 Boa noite, {recruiter_name}!

Resumo do dia:

✅ *REALIZADOS:*
• {interviews_completed} entrevistas concluídas
• {candidates_screened} candidatos triados
• {approvals_given} aprovações processadas

⏳ *PENDENTES PARA AMANHÃ:*
{pending_text}

Descanse bem! Até amanhã! 😊"""
    
    @staticmethod
    def interview_reminder(
        recruiter_name: str,
        candidate_name: str,
        interview_time: datetime,
        interview_link: str
    ) -> str:
        """Generate interview reminder for recruiter."""
        
        time_formatted = interview_time.strftime("%H:%M")
        
        return f"""🔔 Lembrete de Entrevista

*Candidato:* {candidate_name}
*Horário:* {time_formatted}
*Link:* {interview_link}

Posso confirmar sua participação?

[ Confirmar ] [ Reagendar ]"""
    
    @staticmethod
    def approval_needed(
        title: str,
        description: str,
        action_items: list
    ) -> str:
        """Generate approval request message."""
        
        items_text = "\n".join([f"• {item}" for item in action_items])
        
        return f"""⚠️ *{title}*

{description}

*Itens para análise:*
{items_text}

[ Aprovar ] [ Rejeitar ] [ Ver detalhes ]"""
    
    @staticmethod
    def _get_tier_from_wsi(wsi_score: float) -> str:
        """Calculate candidate tier (A/B/C/D) based on WSI score."""
        if wsi_score >= 4.0:
            return "A"
        elif wsi_score >= 3.0:
            return "B"
        elif wsi_score >= 2.0:
            return "C"
        else:
            return "D"
    
    @staticmethod
    def _get_tier_emoji(tier: str) -> str:
        """Get emoji for tier."""
        emojis = {"A": "🌟", "B": "✅", "C": "⚠️", "D": "❌"}
        return emojis.get(tier, "📊")
    
    @staticmethod
    def _get_tier_recommendation(tier: str) -> str:
        """Get recommendation text based on tier."""
        recommendations = {
            "A": "Priorizar para entrevista imediata",
            "B": "Recomendado para próxima etapa",
            "C": "Avaliar com outros candidatos",
            "D": "Considerar arquivar"
        }
        return recommendations.get(tier, "Avaliação pendente")
    
    @staticmethod
    def screening_completed(
        candidate_name: str,
        job_title: str,
        wsi_score: float,
        passed: bool,
        strengths: list,
        development_areas: list,
        candidate_id: str = None,
        vacancy_id: str = None,
        hiring_manager_name: str = None,
        department: str = None,
        confidence: float = None,
        wsi_classification: str = None
    ) -> str:
        """Generate screening completed notification with comprehensive information."""
        
        tier = RecruiterNotificationTemplates._get_tier_from_wsi(wsi_score)
        tier_emoji = RecruiterNotificationTemplates._get_tier_emoji(tier)
        tier_recommendation = RecruiterNotificationTemplates._get_tier_recommendation(tier)
        
        status = "✅ APROVADO" if passed else "❌ REPROVADO"
        strengths_text = "\n".join([f"• {s}" for s in strengths[:3]]) if strengths else "• N/A"
        development_text = "\n".join([f"• {a}" for a in development_areas[:3]]) if development_areas else "• N/A"
        
        vacancy_info = f"*Vaga:* {job_title}"
        if vacancy_id:
            vacancy_info += f" (ID: {vacancy_id[:8]}...)"
        
        candidate_info = f"*Candidato:* {candidate_name}"
        if candidate_id:
            candidate_info += f" (ID: {candidate_id[:8]}...)"
        
        manager_line = f"*Gestor:* {hiring_manager_name}\n" if hiring_manager_name else ""
        department_line = f"*Departamento:* {department}\n" if department else ""
        
        classification_text = f" ({wsi_classification})" if wsi_classification else ""
        confidence_text = f"*Confiança:* {confidence:.0%}\n" if confidence is not None else ""
        
        if passed:
            action_prompt = "Deseja agendar entrevista?"
            actions = "[ Aprovar ] [ Agendar Entrevista ] [ Ver Detalhes ]"
        else:
            action_prompt = "Deseja enviar feedback de rejeição?"
            actions = "[ Ver Detalhes ] [ Arquivar ] [ Enviar Feedback ]"
        
        return f"""🎯 *Triagem Concluída*

{vacancy_info}
{candidate_info}
{manager_line}{department_line}
━━━━━━━━━━━━━━━━━━━━━━
{tier_emoji} *Score WSI:* {wsi_score:.1f}/5 | *Tier:* {tier}{classification_text}
{confidence_text}*Status:* {status}
*Recomendação:* {tier_recommendation}
━━━━━━━━━━━━━━━━━━━━━━

*Pontos Fortes:*
{strengths_text}

*Áreas de Desenvolvimento:*
{development_text}

{action_prompt}

{actions}"""    @staticmethod
    def critical_alert(
        alert_type: str,
        message: str,
        action_required: str
    ) -> str:
        """Generate critical alert message."""
        
        return f"""🚨 *ALERTA: {alert_type}*

{message}

*Ação necessária:*
{action_required}

[ Resolver agora ]"""
