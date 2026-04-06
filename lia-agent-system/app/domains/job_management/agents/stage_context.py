"""
Stage Context Injector - Provides stage-specific context to the wizard agent.

Each stage has different requirements, expected fields, and conversation goals.
This module injects the right context so the agent knows what to focus on.
"""
from typing import Any

STAGE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "input-evaluation": {
        "name": "Coleta de Informacoes Basicas",
        "description": (
            "Nesta etapa a LIA coleta as informacoes fundamentais da vaga: "
            "titulo do cargo, senioridade, departamento, localizacao, modelo de "
            "trabalho e tipo de contrato. A conversa deve ser natural e a LIA "
            "extrai os dados das respostas do usuario."
        ),
        "required_fields": ["title", "department"],
        "optional_fields": ["seniority", "location", "work_model", "contract_type"],
        "transition_criteria": "Titulo do cargo e departamento estao preenchidos.",
        "next_stage": "jd-enrichment",
        "phase": "collection",
    },
    "jd-enrichment": {
        "name": "Enriquecimento da Descricao",
        "description": (
            "A LIA analisa os dados coletados e enriquece a descricao da vaga "
            "com sugestoes de responsabilidades, beneficios e melhorias usando "
            "dados de mercado, historico da empresa e catalogos de skills. O "
            "usuario revisa e aceita ou ajusta as sugestoes."
        ),
        "required_fields": ["title"],
        "optional_fields": [
            "responsibilities",
            "benefits",
            "description",
            "requirements",
        ],
        "transition_criteria": "Usuario revisou as sugestoes de enriquecimento e confirmou.",
        "next_stage": "salary",
        "phase": "enrichment",
    },
    "salary": {
        "name": "Definicao de Remuneracao",
        "description": (
            "A LIA apresenta benchmarks salariais do Parecer e ajuda o usuario "
            "a definir a faixa salarial adequada para o cargo. Compara a "
            "proposta com dados de mercado e historico da empresa."
        ),
        "required_fields": ["salary_min", "salary_max"],
        "optional_fields": ["salary_currency", "salary_type"],
        "transition_criteria": "Salario minimo e maximo estao definidos.",
        "next_stage": "competencies",
        "phase": "adjustment",
    },
    "competencies": {
        "name": "Competencias e Skills",
        "description": (
            "A LIA sugere competencias tecnicas e comportamentais com base nos "
            "dados do Parecer. O usuario pode aceitar, ajustar ou adicionar "
            "skills conforme necessidade."
        ),
        "required_fields": ["skills"],
        "optional_fields": [
            "behavioral_competencies",
            "certifications",
            "education_level",
        ],
        "transition_criteria": "Pelo menos 3 skills definidas.",
        "next_stage": "wsi-questions",
        "phase": "adjustment",
    },
    "wsi-questions": {
        "name": "Perguntas de Triagem WSI",
        "description": (
            "A LIA gera perguntas de triagem WSI personalizadas para a vaga. "
            "O usuario revisa, customiza e aprova as perguntas que serao "
            "usadas na triagem de candidatos."
        ),
        "required_fields": ["screening_questions"],
        "optional_fields": ["eliminatory_questions"],
        "transition_criteria": "Perguntas de triagem foram aprovadas pelo usuario.",
        "next_stage": "review-publish",
        "phase": "screening",
    },
    "review-publish": {
        "name": "Revisao e Publicacao",
        "description": (
            "Revisao final de todos os dados da vaga antes da publicacao. A "
            "LIA apresenta um resumo completo e solicita confirmacao do "
            "usuario para publicar."
        ),
        "required_fields": [],
        "optional_fields": [],
        "transition_criteria": "Usuario confirmou a publicacao da vaga.",
        "next_stage": "complete",
        "phase": "review",
    },
}


def get_stage_context(stage: str, collected_fields: dict[str, Any]) -> str:
    """Build a formatted context string for the current wizard stage.

    Includes stage information, field completion status, percentage and
    guidance on what the agent should focus on.

    Args:
        stage: Current wizard stage identifier.
        collected_fields: Dictionary of fields already collected and their values.

    Returns:
        Formatted context string for prompt injection.
    """
    stage_def = STAGE_DEFINITIONS.get(stage)
    if not stage_def:
        return f"Estagio desconhecido: {stage}. Trate como coleta inicial."

    required = stage_def["required_fields"]
    optional = stage_def["optional_fields"]
    all_fields = required + optional

    filled: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for field in required:
        value = collected_fields.get(field)
        if value is not None and value != "" and value != []:
            filled.append(field)
        else:
            missing_required.append(field)

    for field in optional:
        value = collected_fields.get(field)
        if value is not None and value != "" and value != []:
            filled.append(field)
        else:
            missing_optional.append(field)

    total = len(all_fields)
    completion = (len(filled) / total * 100) if total > 0 else 100.0

    parts = [
        "=== CONTEXTO DO ESTAGIO ===",
        f"Estagio atual: {stage_def['name']} ({stage})",
        f"Fase: {stage_def['phase']}",
        f"Descricao: {stage_def['description']}",
        f"Proximo estagio: {stage_def['next_stage']}",
        "",
        "--- Progresso ---",
        f"Completude: {completion:.0f}%",
    ]

    if filled:
        parts.append("Campos preenchidos:")
        for field in filled:
            value = collected_fields.get(field, "")
            display = str(value)
            if len(display) > 80:
                display = display[:80] + "..."
            parts.append(f"  - {field}: {display}")

    if missing_required:
        parts.append("Campos obrigatorios FALTANDO:")
        for field in missing_required:
            parts.append(f"  - {field} (OBRIGATORIO)")

    if missing_optional:
        parts.append("Campos opcionais disponiveis:")
        for field in missing_optional:
            parts.append(f"  - {field}")

    parts.append("")
    parts.append(f"Criterio de transicao: {stage_def['transition_criteria']}")

    if missing_required:
        parts.append(
            f"\nFOCO: Colete os campos obrigatorios faltantes: {', '.join(missing_required)}"
        )
    elif stage_def["phase"] == "enrichment":
        parts.append(
            "\nFOCO: Apresente sugestoes de enriquecimento e aguarde revisao do usuario."
        )
    elif stage_def["phase"] == "adjustment":
        parts.append(
            "\nFOCO: Apresente dados do Parecer e ajude o usuario a ajustar valores."
        )
    elif stage_def["phase"] == "review":
        parts.append(
            "\nFOCO: Apresente resumo completo e solicite confirmacao para publicar."
        )
    else:
        parts.append(
            "\nFOCO: Campos obrigatorios preenchidos. Pergunte se deseja completar "
            "campos opcionais ou avancar."
        )

    return "\n".join(parts)


def get_transition_prompt(current_stage: str, collected_fields: dict[str, Any]) -> str:
    """Generate a prompt for checking whether transition criteria are met.

    Args:
        current_stage: Current wizard stage identifier.
        collected_fields: Dictionary of fields already collected.

    Returns:
        Formatted prompt string for transition evaluation.
    """
    stage_def = STAGE_DEFINITIONS.get(current_stage)
    if not stage_def:
        return "Estagio desconhecido. Nao e possivel avaliar transicao."

    required = stage_def["required_fields"]
    filled_required = [
        f
        for f in required
        if collected_fields.get(f) not in (None, "", [])
    ]

    all_required_met = len(filled_required) == len(required)

    parts = [
        f"Avaliacao de transicao para o estagio '{current_stage}':",
        f"Criterio: {stage_def['transition_criteria']}",
        f"Campos obrigatorios preenchidos: {len(filled_required)}/{len(required)}",
    ]

    if all_required_met:
        parts.append(
            f"RESULTADO: Criterios atendidos. Pode sugerir avancar para '{stage_def['next_stage']}'."
        )
    else:
        missing = [f for f in required if f not in filled_required]
        parts.append(
            f"RESULTADO: Criterios NAO atendidos. Faltam: {', '.join(missing)}."
        )

    return "\n".join(parts)
