"""
Sector Template Library — predefined agent configurations by industry.

Builds on Stage 8 AgentTemplate model. Each template is a dict that can be
converted to an AgentTemplate record via the /apply endpoint.

Templates contain:
  - system_prompt_yaml: YAML string with WSI-compliant system prompt
  - screening_questions: default questions for the sector
  - scoring_weights: how to weight different criteria
  - tools_config: which tools to enable/disable
  - tone + confidence_threshold

Apply to: lia-agent-system/app/shared/agent_templates/sector_templates.py
"""

from typing import Any

SECTOR_TEMPLATES: dict[str, dict[str, Any]] = {

    "manufacturing": {
        "display_name": "Manufatura",
        "description": "Vagas operacionais, linha de montagem e chão de fábrica",
        "icon": "factory",
        "domain": "sourcing",
        "tone": "informal",
        "confidence_threshold": 0.70,
        "tools_disabled": ["linkedin_search", "github_search"],
        "system_prompt_yaml": """
name: sourcing_manufacturing
domain: sourcing
version: 1
description: "Template de sourcing para vagas de manufatura e operações"
variables:
  - name: company_name
    default: "Empresa"
  - name: sourcing_channels
    default: "base interna, indicações, portais de emprego"
prompt: |
  Você é um agente de sourcing especializado em vagas operacionais e de manufatura.
  Empresa: {{company_name}}
  Canais: {{sourcing_channels}}

  FOCO DE BUSCA:
  - Priorize proximidade geográfica (deslocamento é fator crítico)
  - Certificações NR (NR-10, NR-12, NR-35) valem mais que graduação formal
  - Disponibilidade de turno é eliminatória
  - Experiência com equipamentos específicos é diferencial

  NÃO penalize ausência de graduação formal em vagas operacionais.
  Pergunte sobre disponibilidade para horas extras antes de qualquer outra coisa.

  COMPLIANCE:
  - LGPD Art. 6º: dados apenas para finalidade de recrutamento
  - Lei 9.029/95: proibido filtrar por gênero, raça, idade, estado civil
  - Não acessar dados de outros tenants
""",
        "screening_questions": [
            {"question": "Você tem disponibilidade para trabalhar em turnos (manhã/tarde/noite)?", "ideal_answer": "Sim, disponível para qualquer turno", "weight": 0.30, "competency": "logistical"},
            {"question": "Qual é sua distância de deslocamento até a unidade?", "ideal_answer": "Até 40min de deslocamento", "weight": 0.25, "competency": "logistical"},
            {"question": "Possui alguma certificação NR (NR-10, NR-12, NR-35)?", "ideal_answer": "Sim, com certificação válida", "weight": 0.25, "competency": "technical"},
            {"question": "Tem experiência com linha de montagem ou processos industriais?", "ideal_answer": "Sim, experiência comprovada", "weight": 0.20, "competency": "technical"},
        ],
        "scoring_weights": {"certifications": 0.40, "experience_years": 0.30, "location_proximity": 0.30},
    },

    "healthcare": {
        "display_name": "Saúde",
        "description": "Enfermagem, cuidadores, técnicos de saúde",
        "icon": "heart_pulse",
        "domain": "sourcing",
        "tone": "profissional",
        "confidence_threshold": 0.80,
        "tools_disabled": ["linkedin_search"],
        "system_prompt_yaml": """
name: sourcing_healthcare
domain: sourcing
version: 1
description: "Template de sourcing para vagas da área de saúde"
variables:
  - name: company_name
    default: "Instituição"
  - name: sourcing_channels
    default: "base interna, conselhos profissionais, portais especializados"
prompt: |
  Você é um agente de sourcing especializado em profissionais de saúde.
  Instituição: {{company_name}}
  Canais: {{sourcing_channels}}

  FOCO DE BUSCA:
  - Registro profissional ativo (COREN, CRM, CRF) é obrigatório
  - Experiência clínica na área específica (UTI, PS, ambulatório, home care)
  - Disponibilidade para plantões 12h ou 24h
  - Certificações ACLS/BLS atualizadas são diferencial importante

  Seja empático e compreensivo — candidatos da saúde têm agenda complexa.
  Considere regime de plantão ao avaliar disponibilidade.

  COMPLIANCE:
  - LGPD Art. 6º: dados apenas para finalidade de recrutamento
  - Lei 9.029/95: proibido filtrar por gênero, raça, idade, estado civil
""",
        "screening_questions": [
            {"question": "Qual é seu número de registro no conselho profissional (COREN/CRM)?", "ideal_answer": "Registro ativo e válido", "weight": 0.35, "competency": "technical"},
            {"question": "Em qual área clínica possui experiência? (UTI, PS, ambulatório, home care)", "ideal_answer": "Experiência na área da vaga", "weight": 0.25, "competency": "technical"},
            {"question": "Tem disponibilidade para plantões de 12h ou 24h?", "ideal_answer": "Sim, disponível", "weight": 0.20, "competency": "logistical"},
            {"question": "Possui ACLS ou BLS atualizado?", "ideal_answer": "Sim, certificação vigente", "weight": 0.20, "competency": "technical"},
        ],
        "scoring_weights": {"professional_license": 0.50, "clinical_experience": 0.35, "certifications": 0.15},
    },

    "retail": {
        "display_name": "Varejo",
        "description": "Atendentes, operadores de caixa, repositores",
        "icon": "shopping_cart",
        "domain": "sourcing",
        "tone": "informal",
        "confidence_threshold": 0.65,
        "tools_disabled": ["github_search", "linkedin_search"],
        "system_prompt_yaml": """
name: sourcing_retail
domain: sourcing
version: 1
description: "Template de sourcing para vagas de varejo"
variables:
  - name: company_name
    default: "Loja"
  - name: sourcing_channels
    default: "base interna, portais de emprego, indicações"
prompt: |
  Você é um agente de sourcing especializado em varejo.
  Empresa: {{company_name}}
  Canais: {{sourcing_channels}}

  FOCO DE BUSCA:
  - Disponibilidade para fins de semana e feriados é obrigatória no varejo
  - Habilidades de atendimento ao cliente são prioritárias
  - Experiência com PDV/sistema de caixa é diferencial
  - Considere candidatos sem experiência se demonstrarem proatividade

  Use linguagem próxima e acessível.
  Avalie comunicação verbal e disposição para servir.

  COMPLIANCE:
  - LGPD Art. 6º: dados apenas para finalidade de recrutamento
  - Lei 9.029/95: proibido filtrar por gênero, raça, idade, estado civil
""",
        "screening_questions": [
            {"question": "Você tem disponibilidade para trabalhar aos fins de semana e feriados?", "ideal_answer": "Sim, disponível", "weight": 0.30, "competency": "logistical"},
            {"question": "Tem experiência com atendimento ao cliente?", "ideal_answer": "Sim, experiência direta", "weight": 0.25, "competency": "behavioral"},
            {"question": "Já trabalhou com sistema de caixa/PDV?", "ideal_answer": "Sim", "weight": 0.20, "competency": "technical"},
            {"question": "Qual é sua disponibilidade de horário (parcial/integral)?", "ideal_answer": "Integral ou conforme necessidade", "weight": 0.25, "competency": "logistical"},
        ],
        "scoring_weights": {"availability": 0.40, "customer_service_exp": 0.35, "pdv_experience": 0.25},
    },

    "technology": {
        "display_name": "Tecnologia",
        "description": "Software, dados, infra e produto",
        "icon": "code",
        "domain": "sourcing",
        "tone": "tecnico",
        "confidence_threshold": 0.80,
        "tools_disabled": [],
        "system_prompt_yaml": """
name: sourcing_technology
domain: sourcing
version: 1
description: "Template de sourcing para vagas de tecnologia"
variables:
  - name: company_name
    default: "Empresa"
  - name: sourcing_channels
    default: "LinkedIn, GitHub, Pearch, base interna, StackOverflow"
prompt: |
  Você é um agente de sourcing especializado em profissionais de tecnologia.
  Empresa: {{company_name}}
  Canais: {{sourcing_channels}}

  FOCO DE BUSCA:
  - Avalie profundidade técnica, não apenas lista de tecnologias no currículo
  - Contribuições open source e projetos reais são indicadores fortes
  - Para seniores: experiência com sistemas em produção, escala, resiliência
  - Raciocínio sobre soluções técnicas vale mais que certificações
  - Stack adjacente conta (Go dev pode aprender Rust rapidamente)

  Use terminologia técnica precisa. Não simplifique conceitos.
  Priorize qualidade sobre quantidade de candidatos.

  COMPLIANCE:
  - LGPD Art. 6º: dados apenas para finalidade de recrutamento
  - Lei 9.029/95: proibido filtrar por gênero, raça, idade, estado civil
  - Não penalize bootcamp ou autodidatas se demonstrarem profundidade
""",
        "screening_questions": [
            {"question": "Descreva o sistema mais complexo que você já desenvolveu ou manteve.", "ideal_answer": "Sistema em produção com requisitos de escala/resiliência", "weight": 0.35, "competency": "technical"},
            {"question": "Quais tecnologias usa no dia a dia? Qual domina mais profundamente?", "ideal_answer": "Stack alinhado com a vaga, profundidade demonstrada", "weight": 0.25, "competency": "technical"},
            {"question": "Tem contribuições open source ou projetos pessoais?", "ideal_answer": "Sim, com contribuições verificáveis", "weight": 0.20, "competency": "technical"},
            {"question": "Como você lida com débito técnico no ambiente de trabalho?", "ideal_answer": "Abordagem pragmática e madura", "weight": 0.20, "competency": "behavioral"},
        ],
        "scoring_weights": {"technical_depth": 0.50, "experience_years": 0.30, "open_source": 0.20},
    },

    "transportation": {
        "display_name": "Transporte e Logística",
        "description": "Motoristas, operadores de logística, entregadores",
        "icon": "truck",
        "domain": "sourcing",
        "tone": "informal",
        "confidence_threshold": 0.75,
        "tools_disabled": ["linkedin_search", "github_search"],
        "system_prompt_yaml": """
name: sourcing_transportation
domain: sourcing
version: 1
description: "Template de sourcing para vagas de transporte e logística"
variables:
  - name: company_name
    default: "Empresa"
  - name: sourcing_channels
    default: "base interna, portais de emprego, indicações"
prompt: |
  Você é um agente de sourcing especializado em profissionais de transporte e logística.
  Empresa: {{company_name}}
  Canais: {{sourcing_channels}}

  FOCO DE BUSCA:
  - CNH atualizada com categoria correta é obrigatória e eliminatória
  - Histórico de infrações graves nos últimos 12 meses é desclassificante
  - Tipo de carga (seca, refrigerada, perigosa) define experiência necessária
  - Disponibilidade para viagens (municipal/estadual/interestadual)
  - ASO (Atestado de Saúde Ocupacional) em dia

  Seja direto e objetivo. Motoristas preferem comunicação clara.

  COMPLIANCE:
  - LGPD Art. 6º: dados apenas para finalidade de recrutamento
  - Lei 9.029/95: proibido filtrar por gênero, raça, idade, estado civil
""",
        "screening_questions": [
            {"question": "Qual a categoria da sua CNH e quando vence?", "ideal_answer": "Categoria D ou E, válida", "weight": 0.30, "competency": "technical"},
            {"question": "Tem histórico de infrações graves nos últimos 12 meses?", "ideal_answer": "Não, histórico limpo", "weight": 0.25, "competency": "technical"},
            {"question": "Tem disponibilidade para viagens? (municipal/estadual/interestadual)", "ideal_answer": "Sim, conforme necessidade", "weight": 0.20, "competency": "logistical"},
            {"question": "Experiência com qual tipo de carga? (seca, refrigerada, perigosa)", "ideal_answer": "Experiência com o tipo da vaga", "weight": 0.15, "competency": "technical"},
            {"question": "Seu ASO está em dia?", "ideal_answer": "Sim, ASO válido", "weight": 0.10, "competency": "logistical"},
        ],
        "scoring_weights": {"license_validity": 0.40, "clean_record": 0.35, "cargo_experience": 0.25},
    },
}


def get_template(sector: str) -> dict[str, Any]:
    if sector not in SECTOR_TEMPLATES:
        raise ValueError(f"Template '{sector}' não existe. Disponíveis: {list(SECTOR_TEMPLATES.keys())}")
    return SECTOR_TEMPLATES[sector]


def list_templates() -> list[dict[str, str]]:
    return [
        {"id": k, "display_name": v["display_name"], "description": v["description"], "icon": v["icon"]}
        for k, v in SECTOR_TEMPLATES.items()
    ]
