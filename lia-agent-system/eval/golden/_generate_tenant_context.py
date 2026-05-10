"""Generate eval/golden/tenant_context.jsonl programmatically.

T-E canonical: cobre 16 ReActAgents × 30 cenários = 480 turnos.

Cada turno é independente e tem:
  - id, agent, user_query, tenant snippet (Demo Company T-E)
  - expected_snippet_markers: tokens que DEVEM aparecer no system prompt
  - anti_patterns: regex que NUNCA pode aparecer (resposta da LIA não pode
    pedir empresa)
  - success_criteria: 5 critérios 0..1 que o judge usa
  - fail_threshold_avg: 0.85 (espelha gate em eval_runner.gate_check)

Re-run: ``python -m eval.golden._generate_tenant_context``
Saída: ``eval/golden/tenant_context.jsonl`` (sobrescrito).
"""
from __future__ import annotations

import json
from pathlib import Path

# 16 agentes canônicos T-D + wizard
AGENTS = [
    "analytics", "ats_integration", "automation", "autonomous",
    "candidate_self_service", "communication", "company_settings",
    "cv_screening_pipeline", "hiring_policy", "jobs_management", "kanban",
    "talent_funnel", "sourcing", "talent_pool", "pipeline_transition",
    "wizard",
]

# 30 user queries genéricas — todas devem disparar uso do tenant
# context sem perguntar empresa.
QUERIES = [
    "Quais vagas estão abertas hoje?",
    "Mostre o pipeline da vaga de backend.",
    "Liste candidatos no estágio de triagem.",
    "Quantas contratações fechamos esse mês?",
    "Qual o tempo médio de contratação?",
    "Crie um relatório executivo de KPIs.",
    "Mova o João para a próxima etapa.",
    "Sugira candidatos para a vaga de devops.",
    "Cadastre uma nova vaga de UX designer.",
    "Pause a integração com Gupy.",
    "Configure a política de aprovação automática.",
    "Veja as mensagens não lidas de candidatos.",
    "Envie um e-mail de feedback ao candidato.",
    "Atualize o setor da empresa no perfil.",
    "Compare os 3 finalistas da vaga de tech lead.",
    "Mostre a triagem WSI da Maria.",
    "Quem desistiu do processo nesta semana?",
    "Filtre por experiência em React.",
    "Adicione tags de skill ao candidato.",
    "Aprove a transição de Entrevista para Proposta.",
    "Reagende a entrevista do Pedro.",
    "Gere um link público para a vaga.",
    "Quais leads passivos voltaram a engajar?",
    "Adicione filtro de Boolean para Python sênior.",
    "Salve essa busca como favorita.",
    "Veja meu histórico de buscas.",
    "Mostre vagas paradas há mais de 30 dias.",
    "Quem reprovou no fit cultural?",
    "Configure alerta para candidato hot.",
    "Resumo do funil desta semana.",
]

ANTI_PATTERNS = [
    "qual.*empresa",
    "qual.*id.*empresa",
    "preciso.*empresa",
    "informe.*company_id",
    "em\\s+qual\\s+empresa\\s+você\\s+trabalha",
]

SUCCESS_CRITERIA = [
    "tenant_context_present: snippet 'Empresa: Demo Company T-E' aparece no system prompt renderizado",
    "no_ask_company: resposta da LIA NÃO contém anti_patterns regex",
    "uses_sector: resposta usa 'Tecnologia' ou plano 'enterprise' como contexto implícito",
    "no_default_fallback: resposta NÃO contém literais 'sua empresa', 'geral', 'default', 'workspace_id=0'",
    "agent_persona_consistent: tom/role match com agent_type esperado",
]

TENANT_SNIPPET = (
    "Empresa: Demo Company T-E (Tecnologia)\n"
    "Plano: enterprise\n"
    "Timezone: America/Sao_Paulo\n"
    "Headcount: 51-200"
)
EXPECTED_MARKERS = ["Demo Company T-E", "Tecnologia", "enterprise"]


def main() -> None:
    out = Path(__file__).parent / "tenant_context.jsonl"
    rows = []
    for agent in AGENTS:
        for i, q in enumerate(QUERIES, start=1):
            rows.append({
                "id": f"TC-{agent}-{i:03d}",
                "agent": agent,
                "user_query": q,
                "tenant_snippet": TENANT_SNIPPET,
                "expected_snippet_markers": EXPECTED_MARKERS,
                "anti_patterns": ANTI_PATTERNS,
                "success_criteria": SUCCESS_CRITERIA,
                "fail_threshold_avg": 0.85,
            })
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"wrote {len(rows)} rows to {out} ({len(AGENTS)} agents × {len(QUERIES)} queries)")


if __name__ == "__main__":
    main()
