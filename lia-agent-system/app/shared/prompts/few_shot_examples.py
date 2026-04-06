"""
Few-Shot Examples for LIA Agent Prompts.

Contains domain-specific examples for:
- Job field extraction
- Intent classification
- Salary analysis
- Competency extraction
- Orchestration decisions

Moved from app/prompts/examples.py (I3b cleanup).
"""
from typing import Any


JOB_EXTRACTION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "Preciso de um desenvolvedor Python sênior para São Paulo, remoto, salário entre 15 e 20 mil",
        "output": {
            "title": "Desenvolvedor Python",
            "seniority": "Senior",
            "location": "São Paulo",
            "work_model": "remote",
            "salary_min": 15000,
            "salary_max": 20000
        },
        "reasoning": "Identifiquei o cargo (desenvolvedor Python), senioridade explícita (sênior), localização (São Paulo), modelo de trabalho (remoto) e faixa salarial (15-20 mil)."
    },
    {
        "input": "Vaga de analista de dados pleno, híbrido em Campinas",
        "output": {
            "title": "Analista de Dados",
            "seniority": "Pleno",
            "location": "Campinas",
            "work_model": "hybrid",
            "salary_min": None,
            "salary_max": None
        },
        "reasoning": "Extraí o cargo (analista de dados), senioridade (pleno), localização (Campinas) e modelo (híbrido). Salário não foi mencionado."
    },
    {
        "input": "Gerente de projetos com experiência em metodologias ágeis, presencial no Rio",
        "output": {
            "title": "Gerente de Projetos",
            "seniority": "Senior",
            "location": "Rio de Janeiro",
            "work_model": "onsite",
            "required_skills": ["Metodologias Ágeis", "Gestão de Projetos"],
            "salary_min": None,
            "salary_max": None
        },
        "reasoning": "Cargo de gerência implica senioridade Senior. Localização 'Rio' expandida para 'Rio de Janeiro'. Trabalho presencial (onsite). Competência em metodologias ágeis identificada."
    },
    {
        "input": "Tech lead de frontend, React e TypeScript, remoto, 25k",
        "output": {
            "title": "Tech Lead Frontend",
            "seniority": "Senior",
            "location": None,
            "work_model": "remote",
            "required_skills": ["React", "TypeScript", "Frontend"],
            "salary_min": 25000,
            "salary_max": 25000
        },
        "reasoning": "Tech Lead indica senioridade Senior. Tecnologias React e TypeScript como skills obrigatórias. Salário único de 25k indica min=max. Remoto sem localização específica."
    },
    {
        "input": "Estágio em marketing digital para estudante de publicidade",
        "output": {
            "title": "Estagiário de Marketing Digital",
            "seniority": "Estagio",
            "location": None,
            "work_model": None,
            "required_skills": ["Marketing Digital"],
            "education_level": "Cursando Publicidade"
        },
        "reasoning": "Estágio define senioridade automaticamente. Formação em publicidade como requisito educacional. Marketing digital como área de conhecimento."
    }
]


INTENT_CLASSIFICATION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "Quero criar uma vaga de desenvolvedor",
        "output": {
            "intent": "job_creation",
            "confidence": 0.95,
            "entities": {"role_hint": "desenvolvedor"}
        },
        "reasoning": "Verbo 'criar' + 'vaga' indica intenção clara de criação de vaga. Desenvolvedor é uma dica do cargo."
    },
    {
        "input": "Me mostra os candidatos para a vaga de gerente",
        "output": {
            "intent": "candidate_search",
            "confidence": 0.90,
            "entities": {"job_title": "gerente"}
        },
        "reasoning": "Solicitação de visualização de candidatos indica busca. Gerente é o cargo alvo."
    },
    {
        "input": "Quanto é o salário médio para um analista de dados?",
        "output": {
            "intent": "salary_inquiry",
            "confidence": 0.95,
            "entities": {"job_title": "analista de dados"}
        },
        "reasoning": "Pergunta explícita sobre salário/remuneração. Cargo específico mencionado."
    },
    {
        "input": "Olá, tudo bem?",
        "output": {
            "intent": "greeting",
            "confidence": 0.99,
            "entities": {}
        },
        "reasoning": "Saudação simples sem intenção de negócio. Responder cordialmente."
    },
    {
        "input": "Precisa mudar o título da vaga para Engenheiro de Software",
        "output": {
            "intent": "job_update",
            "confidence": 0.92,
            "entities": {"field": "title", "new_value": "Engenheiro de Software"}
        },
        "reasoning": "Verbo 'mudar' indica atualização. Campo 'título' e novo valor claramente especificados."
    },
    {
        "input": "Como funciona o processo de triagem?",
        "output": {
            "intent": "general_question",
            "confidence": 0.88,
            "entities": {"topic": "triagem"}
        },
        "reasoning": "Pergunta informacional sobre funcionalidade do sistema, não uma ação específica."
    }
]


SALARY_ANALYSIS_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": {
            "job_title": "Desenvolvedor Python",
            "seniority": "Senior",
            "location": "São Paulo",
            "current_range": {"min": 12000, "max": 15000}
        },
        "output": {
            "recommended_min": 18000,
            "recommended_max": 25000,
            "market_position": "below_market",
            "confidence": 0.85,
            "reasoning": "Faixa atual está 20-30% abaixo do mercado para Python Senior em SP. Recomendo ajuste para atrair candidatos qualificados."
        },
        "reasoning": "Analisei dados de mercado para Python Senior em SP. O range proposto está significativamente abaixo da média."
    },
    {
        "input": {
            "job_title": "Analista de Dados",
            "seniority": "Pleno",
            "location": "Remoto",
            "current_range": {"min": 8000, "max": 12000}
        },
        "output": {
            "recommended_min": 8000,
            "recommended_max": 13000,
            "market_position": "at_market",
            "confidence": 0.80,
            "reasoning": "Faixa compatível com mercado para Analista Pleno remoto. Pequeno ajuste no teto pode aumentar competitividade."
        },
        "reasoning": "Vagas remotas têm mercado mais amplo. A faixa está adequada, com margem para otimização."
    },
    {
        "input": {
            "job_title": "Product Manager",
            "seniority": "Senior",
            "location": "São Paulo",
            "current_range": {"min": 30000, "max": 40000}
        },
        "output": {
            "recommended_min": 25000,
            "recommended_max": 35000,
            "market_position": "above_market",
            "confidence": 0.75,
            "reasoning": "Faixa acima da média de mercado. Pode atrair muitos candidatos, mas considere se o orçamento comporta."
        },
        "reasoning": "PM Senior em SP tem mercado aquecido, mas esta faixa está no percentil 90. Empresa deve ter certeza do investimento."
    }
]


COMPETENCY_EXTRACTION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "Preciso de alguém que manje de Python, Django e PostgreSQL",
        "output": {
            "technical_skills": ["Python", "Django", "PostgreSQL"],
            "soft_skills": [],
            "certifications": []
        },
        "reasoning": "Três tecnologias técnicas claramente mencionadas. Linguagem informal 'manje' = conhecimento."
    },
    {
        "input": "Buscamos profissional com boa comunicação, trabalho em equipe e conhecimento em Excel avançado",
        "output": {
            "technical_skills": ["Excel Avançado"],
            "soft_skills": ["Comunicação", "Trabalho em Equipe"],
            "certifications": []
        },
        "reasoning": "Separei habilidades técnicas (Excel) de comportamentais (comunicação, trabalho em equipe)."
    },
    {
        "input": "AWS certified, experiência com Kubernetes e Docker, perfil hands-on",
        "output": {
            "technical_skills": ["Kubernetes", "Docker", "AWS"],
            "soft_skills": ["Perfil Hands-on"],
            "certifications": ["AWS Certified"]
        },
        "reasoning": "Certificação AWS identificada. Kubernetes e Docker como skills técnicas. Hands-on como característica comportamental."
    },
    {
        "input": "Experiência com metodologias ágeis, Scrum Master certificado seria um diferencial",
        "output": {
            "technical_skills": ["Metodologias Ágeis", "Scrum"],
            "soft_skills": [],
            "certifications": ["Scrum Master"],
            "is_differential": True
        },
        "reasoning": "Metodologias ágeis como conhecimento técnico. Certificação SM mencionada como diferencial (não obrigatório)."
    }
]


ORCHESTRATION_DECISION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": {
            "user_message": "O salário está muito baixo, aumenta para 20k",
            "current_stage": 3,
            "job_draft": {"title": "Dev Python", "salary_max": 15000}
        },
        "output": {
            "action": "update_fields",
            "confidence": 0.95,
            "field_updates": [{"field": "salary_max", "value": 20000, "reason": "Ajuste solicitado pelo recrutador"}],
            "response_text": "Atualizei o salário máximo para R$ 20.000. Posso ajudar com mais alguma coisa?"
        },
        "reasoning": "Solicitação clara de atualização de campo específico (salário). Ação direta sem necessidade de esclarecimento."
    },
    {
        "input": {
            "user_message": "Tá bom, pode continuar",
            "current_stage": 2,
            "job_draft": {"title": "Analista", "seniority": "Pleno"}
        },
        "output": {
            "action": "advance_stage",
            "confidence": 0.90,
            "next_stage": 3,
            "response_text": "Ótimo! Vamos definir a faixa salarial e benefícios."
        },
        "reasoning": "Confirmação do usuário para prosseguir. Avançar para próximo estágio do wizard."
    },
    {
        "input": {
            "user_message": "Não sei qual senioridade escolher",
            "current_stage": 1,
            "job_draft": {"title": "Desenvolvedor Backend"}
        },
        "output": {
            "action": "request_clarification",
            "confidence": 0.85,
            "clarification_needed": "seniority",
            "response_text": "Posso ajudar! Qual é o nível de experiência esperado? Junior (0-2 anos), Pleno (2-5 anos) ou Senior (5+ anos)?"
        },
        "reasoning": "Usuário expressou dúvida. Fornecer opções claras para facilitar decisão."
    },
    {
        "input": {
            "user_message": "Como está ficando a vaga?",
            "current_stage": 4,
            "job_draft": {"title": "PM", "seniority": "Senior", "salary_min": 25000}
        },
        "output": {
            "action": "respond",
            "confidence": 0.92,
            "response_text": "Aqui está o resumo da vaga:\n- **Cargo:** PM\n- **Senioridade:** Senior\n- **Salário mínimo:** R$ 25.000\n\nDeseja fazer algum ajuste?"
        },
        "reasoning": "Solicitação de resumo/status. Apresentar informações atuais sem alterar nada."
    }
]


RESPONSIBILITY_GENERATION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": {
            "title": "Desenvolvedor Backend Python",
            "seniority": "Senior"
        },
        "output": [
            "Projetar e implementar APIs RESTful escaláveis usando Python e frameworks como Django/FastAPI",
            "Liderar revisões de código e garantir boas práticas de desenvolvimento",
            "Mentorear desenvolvedores juniores e plenos da equipe",
            "Participar de decisões de arquitetura e design de sistemas",
            "Otimizar performance de aplicações e banco de dados"
        ],
        "reasoning": "Senior backend requer liderança técnica, mentoria e decisões arquiteturais além de codificação."
    },
    {
        "input": {
            "title": "Analista de Dados",
            "seniority": "Pleno"
        },
        "output": [
            "Coletar, processar e analisar grandes volumes de dados",
            "Criar dashboards e relatórios para tomada de decisão",
            "Desenvolver e manter pipelines de ETL",
            "Colaborar com stakeholders para entender necessidades de negócio",
            "Documentar processos e metodologias de análise"
        ],
        "reasoning": "Pleno executa com autonomia mas ainda não lidera. Foco em execução técnica com colaboração."
    }
]


class FewShotExamples:
    """
    Manager for few-shot examples with filtering and selection capabilities.
    """

    @staticmethod
    def get_job_extraction_examples(max_examples: int = 3) -> list[dict[str, Any]]:
        """Get job extraction examples, limited to max_examples."""
        return JOB_EXTRACTION_EXAMPLES[:max_examples]

    @staticmethod
    def get_intent_examples(max_examples: int = 4) -> list[dict[str, Any]]:
        """Get intent classification examples."""
        return INTENT_CLASSIFICATION_EXAMPLES[:max_examples]

    @staticmethod
    def get_salary_examples(max_examples: int = 2) -> list[dict[str, Any]]:
        """Get salary analysis examples."""
        return SALARY_ANALYSIS_EXAMPLES[:max_examples]

    @staticmethod
    def get_competency_examples(max_examples: int = 3) -> list[dict[str, Any]]:
        """Get competency extraction examples."""
        return COMPETENCY_EXTRACTION_EXAMPLES[:max_examples]

    @staticmethod
    def get_orchestration_examples(max_examples: int = 3) -> list[dict[str, Any]]:
        """Get orchestration decision examples."""
        return ORCHESTRATION_DECISION_EXAMPLES[:max_examples]

    @staticmethod
    def get_responsibility_examples(max_examples: int = 2) -> list[dict[str, Any]]:
        """Get responsibility generation examples."""
        return RESPONSIBILITY_GENERATION_EXAMPLES[:max_examples]

    @staticmethod
    def filter_by_seniority(
        examples: list[dict[str, Any]],
        seniority: str
    ) -> list[dict[str, Any]]:
        """Filter examples that match a specific seniority level."""
        filtered = []
        for ex in examples:
            output = ex.get("output", {})
            if isinstance(output, dict):
                ex_seniority = output.get("seniority", "")
                if ex_seniority.lower() == seniority.lower():
                    filtered.append(ex)
            if isinstance(ex.get("input"), dict):
                input_seniority = ex["input"].get("seniority", "")
                if input_seniority.lower() == seniority.lower():
                    filtered.append(ex)
        return filtered if filtered else examples[:2]

    @staticmethod
    def format_for_prompt(examples: list[dict[str, Any]]) -> str:
        """Format examples as a string for inclusion in prompts."""
        formatted_parts = []
        for i, ex in enumerate(examples, 1):
            part = f"Exemplo {i}:\n"
            part += f"  Entrada: {ex.get('input')}\n"
            if ex.get('reasoning'):
                part += f"  Raciocínio: {ex.get('reasoning')}\n"
            part += f"  Saída: {ex.get('output')}\n"
            formatted_parts.append(part)
        return "\n".join(formatted_parts)


# ---------------------------------------------------------------------------
# LIA-P05 — Categorias adicionais de few-shot examples
# ---------------------------------------------------------------------------

CANDIDATE_EVALUATION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "avalia o Joao para a vaga de Dev Senior",
        "domain": "cv_screening",
        "action": "evaluate_candidate",
        "expected_behavior": "Aplica rubric BARS, retorna score com justificativa por competencia",
        "reasoning": "Nome especifico + vaga especifica + verbo avaliar -> evaluate_candidate com rubric estruturado."
    },
    {
        "input": "esse candidato e bom?",
        "domain": "cv_screening",
        "action": "evaluate_candidate",
        "expected_behavior": "Solicita vaga de referencia antes de avaliar",
        "reasoning": "Sem vaga de referencia nao e possivel avaliar contra criterios. Pede contexto primeiro."
    },
    {
        "input": "me da um parecer tecnico do Carlos para a vaga de arquiteto",
        "domain": "cv_screening",
        "action": "generate_report",
        "expected_behavior": "Gera parecer estruturado com pontos fortes, gaps e recomendacao final",
        "reasoning": "Parecer tecnico implica analise profunda, nao apenas score. Usa generate_report."
    },
    {
        "input": "quem dos 5 candidatos triados tem mais fit cultural?",
        "domain": "cv_screening",
        "action": "compare_candidates",
        "expected_behavior": "Compara candidatos em dimensao de fit cultural, usa Big Five se disponivel",
        "reasoning": "Comparacao entre multiplos candidatos com criterio especifico -> compare_candidates."
    },
    {
        "input": "o score do Pedro ta certo? parece alto demais",
        "domain": "cv_screening",
        "action": "calculate_wsi_score",
        "expected_behavior": "Reexecuta calculo WSI e explica criterios que geraram o score atual",
        "reasoning": "Questionamento sobre score -> recalcular e explicar metodologia WSI."
    },
]


SCHEDULING_NEGOTIATION_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "deixa pra amanha",
        "domain": "interview_scheduling",
        "action": "reschedule_interview",
        "expected_behavior": "Identifica como reschedule, propoe horarios disponiveis de amanha",
        "reasoning": "Expressao coloquial de adiamento -> reschedule_interview com data=amanha."
    },
    {
        "input": "nao vai dar pra hoje",
        "domain": "interview_scheduling",
        "action": "reschedule_interview",
        "expected_behavior": "Reconhece cancelamento implicito, pergunta nova data",
        "reasoning": "Negacao + hoje -> cancelamento implicito, precisa nova data antes de reagendar."
    },
    {
        "input": "o candidato pediu pra adiar uma semana",
        "domain": "interview_scheduling",
        "action": "reschedule_interview",
        "expected_behavior": "Calcula data +7 dias, propoe slots disponiveis nesse periodo",
        "reasoning": "Pedido explicito de adiamento com prazo -> reagenda no periodo indicado."
    },
    {
        "input": "confirma a entrevista de amanha com a Ana",
        "domain": "interview_scheduling",
        "action": "confirm_interview",
        "expected_behavior": "Envia confirmacao para candidata Ana via canal preferencial",
        "reasoning": "Verbo confirmar + candidata nomeada + data -> confirm_interview."
    },
    {
        "input": "cancela tudo que tinha agendado com o Paulo",
        "domain": "interview_scheduling",
        "action": "cancel_interview",
        "expected_behavior": "Lista agendamentos com Paulo, solicita confirmacao antes de cancelar",
        "reasoning": "Acao irreversivel -> confirmar antes de executar, mesmo com instrucao clara."
    },
]


COMMUNICATION_TONE_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "manda um zap pro candidato",
        "domain": "communication",
        "action": "send_whatsapp_message",
        "expected_behavior": "Entende 'zap' como WhatsApp, pede confirmacao do template",
        "reasoning": "Girao 'zap' = WhatsApp no contexto brasileiro de RH."
    },
    {
        "input": "fala com ele que nao foi dessa vez",
        "domain": "communication",
        "action": "send_rejection_message",
        "expected_behavior": "Identifica rejeicao, usa template humanizado, verifica FairnessGuard",
        "reasoning": "Expressao coloquial de rejeicao -> template empatetico, passa por FairnessGuard."
    },
    {
        "input": "manda um email de feedback construtivo para os reprovados da etapa tecnica",
        "domain": "communication",
        "action": "send_feedback_email",
        "expected_behavior": "Gera feedback individualizado por candidato com pontos de melhoria",
        "reasoning": "Feedback construtivo = personalizado, nao generico. Processa cada reprovado."
    },
    {
        "input": "avisa os aprovados que passaram pra proxima fase",
        "domain": "communication",
        "action": "send_advancement_message",
        "expected_behavior": "Envia mensagem de avanco com detalhes da proxima etapa",
        "reasoning": "Aprovados + proxima fase -> advancement_message com instrucoes da etapa seguinte."
    },
]


ANALYTICS_QUERY_EXAMPLES: list[dict[str, Any]] = [
    {
        "input": "como ta o funil esse mes?",
        "domain": "analytics",
        "action": "get_funnel_stats",
        "expected_behavior": "Entende 'funil' como pipeline_stats, periodo = mes atual",
        "reasoning": "Funil = pipeline de candidatos. Mes atual sem data explicita."
    },
    {
        "input": "qual minha taxa de conversao?",
        "domain": "analytics",
        "action": "get_conversion_rate",
        "expected_behavior": "Retorna taxa de conversao por etapa com comparativo periodo anterior",
        "reasoning": "Taxa de conversao requer etapas do funil + benchmark para ser util."
    },
    {
        "input": "quantos dias em media leva pra fechar uma vaga?",
        "domain": "analytics",
        "action": "get_time_to_hire",
        "expected_behavior": "Retorna avg_time_to_hire com breakdown por nivel de senioridade",
        "reasoning": "Pergunta sobre tempo de contratacao -> time_to_hire com segmentacao por seniority."
    },
    {
        "input": "qual foi a performance do time de recrutamento no trimestre?",
        "domain": "analytics",
        "action": "get_team_performance",
        "expected_behavior": "Compila metricas de SLA, volume e qualidade de contratacoes do trimestre",
        "reasoning": "Performance do time = multiplas metricas agregadas, periodo = trimestre atual."
    },
]
