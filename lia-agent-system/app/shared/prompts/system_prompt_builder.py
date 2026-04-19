"""
SystemPromptBuilder — compositor dinâmico de system prompts para a LIA.

Single entry point para compor prompts em runtime, combinando:
  (a) persona base (lia_persona.yaml — cached)
  (b) adições de domínio específico
  (c) contexto do tenant (empresa, setor, vagas)
  (d) contexto do usuário (nome, role)
  (e) resumo do histórico de conversa
  (f) contexto de scope/página
  (g) regras anti-repetição baseadas no estado da conversa
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _load_persona_base() -> str:
    from app.shared.prompts.loader import PromptLoader
    data = PromptLoader.load("shared/lia_persona")
    return data["prompts"]["lia_persona"]


@lru_cache(maxsize=16)
def _load_domain_additions(agent_type: str) -> str | None:
    try:
        from app.shared.prompts.loader import PromptLoader
        data = PromptLoader.load("shared/agent_prompts")
        return data["prompts"].get(agent_type)
    except Exception as exc:
        logger.warning("Failed to load domain additions for agent_type=%s: %s", agent_type, exc)
        return None



REACT_INSTRUCTIONS = (
    "\n## Protocolo de Raciocinio (ReAct)\n\n"
    "Voce opera em um ciclo de Raciocinio-Acao-Observacao:\n\n"
    "1. RACIOCINE sobre a situacao atual:\n"
    "   - O que o recrutador realmente precisa?\n"
    "   - Preciso buscar dados ou posso responder diretamente?\n"
    "   - Ha algum risco de compliance, fairness ou LGPD?\n\n"
    "2. AJA de uma das formas:\n"
    '   - action="call_tool": Chamar uma ferramenta para consultar/executar\n'
    '   - action="respond": Responder ao recrutador com insights\n'
    '   - action="ask_clarification": Pedir esclarecimento quando ambiguo\n\n'
    "3. OBSERVE o resultado e decida se precisa agir novamente ou responder.\n\n"
    'Entenda confirmacoes: "sim", "pode", "confirmo", "ok", "beleza", "bora"\n'
    'Entenda negacoes: "nao", "espera", "cancela", "volta", "quero mudar"\n'
)


# IDENTITY_OVERRIDE injected before persona to override LLM defaults


_PLATFORM_KNOWLEDGE = (
    "## Conhecimento da Plataforma WeDOTalent\n\n"
    "Voce conhece TODAS as funcionalidades, paginas e metodologias da plataforma:\n\n"
    "**Paginas principais** (voce pode navegar o recrutador ate elas):\n"
    "- Dashboard: visao geral, metricas e atividade recente\n"
    "- Vagas: lista e gestao de vagas/posicoes abertas\n"
    "- Pipeline / Kanban: gestao visual de candidatos por etapa do processo\n"
    "- Candidatos: banco de talentos com historico e scores\n"
    "- Sourcing: busca inteligente de candidatos por skills, experiencia, localizacao\n"
    "- Analytics: relatorios, metricas de recrutamento e insights\n"
    "- Configuracoes: perfil da empresa, integracoes (HubSpot, WhatsApp, LLM/IA), politicas\n\n"
    "**Configuracoes da empresa** (caminho: Menu lateral → Configuracoes):\n"
    "  Dados Basicos, Localizacao, Cultura, Beneficios, Processos Seletivos, Integracoes\n"
    "  Se o perfil estiver incompleto, PROATIVAMENTE sugira completar para melhores resultados.\n\n"
    "## Metodologia WSI (Workplace Science Index) — conhecimento canonico\n\n"
    "**WSI = 70% tecnico + 30% comportamental** (scoring de candidatos).\n\n"
    "**Bloom Taxonomy** (dimensao cognitiva, 6 niveis):\n"
    "  1 Lembrar, 2 Compreender, 3 Aplicar, 4 Analisar, 5 Avaliar, 6 Criar.\n\n"
    "**Dreyfus Model** (nivel de expertise, 5 niveis):\n"
    "  1 Novato, 2 Iniciante Avancado, 3 Competente, 4 Proficiente, 5 Expert.\n\n"
    "**Big Five** (personalidade): Abertura, Conscienciosidade, Extroversao, Amabilidade, Neuroticismo.\n\n"
    "**Dynamic Cutoff**: apos 30-50 candidatos, threshold recalculado automaticamente.\n"
    "**Smart Saturation**: se >20 aprovados, pipeline pausa para evitar sobrecarga.\n\n"
    "## Capacidades tecnicas reais (seja precisa)\n"
    "- **CV**: processo texto de CVs. Se vier PDF/DOCX, o sistema extrai o texto antes.\n"
    "- **Entrevistas**: via mensagens WhatsApp (texto e audio). Nao faco ligacao de voz direta.\n"
    "- **Boolean strings**: consigo gerar (ex: \"React\" AND \"Senior\" AND (\"TS\" OR \"Next\") NOT \"Pleno\").\n"
    "- **Fairness**: bloqueio filtros discriminatorios (genero, raca, maternidade, bairro, idade).\n\n"
    "**Regra de Proatividade**: Se detectar pre-condicao faltando (empresa sem perfil, "
    "vaga sem perguntas de triagem, candidato sem score WSI), OFERECA ajuda imediatamente — "
    "nao espere o recrutador perceber.\n"
)

_IDENTITY_OVERRIDE = (
    "# REGRA ZERO -- SUA IDENTIDADE\n\n"
    "SEU NOME E LIA. VOCE E A LIA, assistente de recrutamento da WeDOTalent.\n"
    "Voce NAO e Gemini. Voce NAO e Claude. Voce NAO e GPT. Nao mencione nenhum fabricante de LLM.\n"
    "NUNCA diga 'sou um modelo de linguagem' ou 'como modelo de linguagem'. Voce e a LIA.\n"
    "Se perguntada quem voce e: responda APENAS: Sou a LIA, assistente de recrutamento da WeDOTalent.\n"
    "NUNCA liste suas capacidades em bullets quando se apresentar ou responder quem voce e.\n"
    "NUNCA exiba nomes de funcoes internas (create_job, list_jobs etc). Use linguagem natural.\n"
    "SEMPRE responda em PT-BR, mesmo se o usuario escrever em ingles ou outro idioma.\n\n"
    "---\n\n"
)

class SystemPromptBuilder:
    """Compõe system prompts dinamicamente para qualquer agente/contexto/tenant."""

    @staticmethod
    def build(
        *,
        agent_type: str = "orchestrator",
        tenant_context_snippet: str = "",
        user_name: str = "",
        user_role: str = "",
        recruiter_context: str = "",
        conversation_summary: str = "",
        conversation_history: list[dict[str, Any]] | None = None,
        context_page: str = "general",
        entity_type: str | None = None,
        intent: str = "",
        entities: dict[str, Any] | None = None,
        extra_instructions: str = "",
        conversation_state: Any | None = None,
    ) -> str:
        sections: list[str] = []

        sections.append(_IDENTITY_OVERRIDE)
        persona = _load_persona_base()
        sections.append(persona)
        sections.append(_PLATFORM_KNOWLEDGE)

        domain_additions = _load_domain_additions(agent_type)
        if domain_additions:
            sections.append(f"\n## Especialização do Agente ({agent_type})\n{domain_additions}")

        context_parts: list[str] = []

        if tenant_context_snippet:
            context_parts.append(f"### Contexto do Cliente\n{tenant_context_snippet}")

        if recruiter_context:
            context_parts.append(f"### Preferências do Recrutador\n{recruiter_context}")

        if user_name:
            user_desc = f"Você está conversando com **{user_name}**"
            if user_role:
                user_desc += f", que atua como **{user_role}**"
            user_desc += "."
            context_parts.append(f"### Usuário\n{user_desc}")

        if context_page and context_page != "general":
            page_descriptions = {
                "sourcing": "O usuário está na página de sourcing/busca de candidatos.",
                "talent": "O usuário está visualizando o funil de talentos.",
                "pipeline": "O usuário está gerenciando o pipeline de candidatos.",
                "kanban": "O usuário está no kanban de pipeline.",
                "job": "O usuário está visualizando uma vaga específica.",
                "jobs": "O usuário está na lista de vagas.",
                "vacancies": "O usuário está na página de vagas.",
                "wizard": "O usuário está criando/editando uma vaga pelo wizard.",
                "analytics": "O usuário está na página de relatórios e analytics.",
                "settings": (
                    "O usuário está na página de Configurações da empresa. "
                    "Aqui ele pode configurar: nome/CNPJ/setor/tamanho (Dados Básicos), "
                    "endereço (Localização), cultura/valores (Cultura), benefícios, "
                    "processos seletivos e integrações (HubSpot, WhatsApp, LLM). "
                    "Caminho: Menu lateral → Configurações."
                ),
                "company_settings": (
                    "O usuário está nas Configurações da empresa. "
                    "Pode completar perfil, configurar integrações e políticas de recrutamento."
                ),
                "company_profile": (
                    "O usuário está no Perfil da empresa. "
                    "Se o perfil estiver incompleto, sugerir navegar para Configurações. "
                    "Sem perfil completo, buscas e triagens podem ser menos precisas."
                ),
            }
            page_desc = page_descriptions.get(context_page, f"O usuário está na página: {context_page}.")
            context_parts.append(f"### Localização\n{page_desc}")

        if conversation_summary:
            context_parts.append(f"### Resumo da Conversa Anterior\n{conversation_summary}")

        if conversation_state:
            try:
                mem_lines = []
                if conversation_state.last_entity:
                    e = conversation_state.last_entity
                    mem_lines.append(f"- Última entidade: {e.get('type','?')} **{e.get('name') or e.get('id','?')}** (ID: {e.get('id','?')})")
                if conversation_state.mentioned_candidates:
                    recent = list(conversation_state.mentioned_candidates.items())[-3:]
                    names = ", ".join(f"{n} (ID: {cid})" for n, cid in recent)
                    mem_lines.append(f"- Candidatos mencionados: {names}")
                if conversation_state.last_job_id:
                    mem_lines.append(f"- Última vaga: ID {conversation_state.last_job_id}")
                if mem_lines:
                    context_parts.append("### Memória da Conversa\n" + "\n".join(mem_lines))
            except Exception:
                pass

        if context_parts:
            sections.append("\n## Contexto Atual\n" + "\n\n".join(context_parts))

        is_ongoing = _detect_ongoing_conversation(conversation_history)
        if is_ongoing:
            sections.append(
                "\n## Regras para esta mensagem\n"
                "- NÃO se re-apresente. A conversa já está em andamento.\n"
                "- NÃO repita informações que já foram ditas.\n"
                "- Seja direta e vá ao ponto."
            )

        if intent:
            intent_line = f"Intent detectado: {intent}"
            if entities:
                intent_line += f" | Entidades: {entities}"
            sections.append(f"\n## Roteamento\n{intent_line}")

        # Inject ReAct protocol for agent contexts
        if agent_type and agent_type != "orchestrator":
            sections.append(REACT_INSTRUCTIONS)

        if extra_instructions:
            sections.append(f"\n## Instruções Adicionais\n{extra_instructions}")

        return "\n".join(sections)

    @staticmethod
    def build_error_response(
        *,
        user_name: str = "",
        partial_context: str = "",
        context_page: str = "",
        is_ongoing_conversation: bool = False,
    ) -> str:
        greeting = f"{user_name}, " if user_name else ""
        base = f"{greeting}estou com dificuldade para processar essa solicitação no momento."

        if context_page and context_page not in ("general", ""):
            page_hints = {
                "wizard": " Você pode tentar descrever a vaga novamente ou voltar à etapa anterior.",
                "sourcing": " Pode reformular a busca ou tentar com outros filtros.",
                "pipeline": " Tente novamente em alguns segundos.",
                "kanban": " Tente novamente em alguns segundos.",
                "analytics": " Tente atualizar a página ou solicitar o relatório novamente.",
            }
            hint = page_hints.get(context_page, "")
            return f"{base}{hint} Se persistir, me avise que busco outra forma de ajudar."

        return f"{base} Pode tentar novamente em alguns segundos? Se persistir, me avise que busco outra forma de ajudar."

    @staticmethod
    def build_clarification(
        message: str,
        partial_matches: list[dict[str, Any]] | None = None,
        user_name: str = "",
    ) -> tuple[str, list[str]]:
        snippet = message.strip()[:80]
        greeting = f"{user_name}, " if user_name else ""

        if partial_matches and len(partial_matches) >= 2:
            domains_desc = {
                "job_planner": "criar ou gerenciar vagas",
                "sourcing": "buscar candidatos",
                "cv_screening": "analisar currículos e compatibilidade",
                "interviewer": "conduzir entrevistas",
                "wsi_evaluator": "avaliar com metodologia WSI",
                "scheduling": "agendar entrevistas",
                "analyst_feedback": "relatórios e feedback",
                "ats_integrator": "integração com ATS",
                "recruiter_assistant": "suporte geral de recrutamento",
                "pipeline": "gerenciar pipeline",
            }
            matched_domains = [m.get("domain_id", "") for m in partial_matches[:3]]
            options = [domains_desc.get(d, d) for d in matched_domains if d in domains_desc]

            if options:
                options_text = " ou ".join(options)
                question = (
                    f"{greeting}Sua mensagem pode estar relacionada a {options_text}. "
                    "Pode me dar mais detalhes sobre o que precisa?"
                )
                suggestion_list = [domains_desc.get(d, d).capitalize() for d in matched_domains if d in domains_desc]
                return question, suggestion_list

        default_options = [
            "Criar ou gerenciar vagas",
            "Buscar candidatos",
            "Analisar currículos",
            "Agendar entrevistas",
            "Relatórios e analytics",
        ]

        if snippet:
            question = (
                f"{greeting}Não consegui entender exatamente o que você precisa a partir de \"{snippet}\". "
                "Pode reformular ou me dar mais contexto?"
            )
        else:
            question = f"{greeting}Como posso ajudar você?"

        return question, default_options


def _detect_ongoing_conversation(history: list[dict[str, Any]] | None) -> bool:
    if not history:
        return False
    assistant_msgs = [m for m in history if m.get("role") == "assistant"]
    return len(assistant_msgs) >= 1
