"""Generate GLOSSARIO_ACTIONS_TOOLS.md from the live registry."""
from __future__ import annotations
import importlib, os, sys
from pathlib import Path
os.environ.setdefault("LIA_ALLOW_NON_COMPLIANT_DOMAINS", "1")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://stub:stub@localhost/stub")
os.environ.setdefault("LIA_SKIP_DB", "1")
ROOT = Path("lia-agent-system")
sys.path.insert(0, str(ROOT))

base = ROOT / "app" / "domains"
for d in sorted(base.iterdir()):
    if d.is_dir() and (d / "domain.py").exists():
        try:
            importlib.import_module(f"app.domains.{d.name}.domain")
        except Exception:
            pass

from app.domains.registry import DomainRegistry, _DOMAIN_REGISTRY

def _load_tools(did):
    try:
        m = importlib.import_module(f"app.domains.{did}.tools")
    except Exception:
        return []
    for attr in (f"{did.upper()}_TOOLS", "SOURCING_TOOLS", "TOOLS"):
        v = getattr(m, attr, None)
        if isinstance(v, list) and v:
            return v
    for name in dir(m):
        v = getattr(m, name)
        if isinstance(v, list) and v and isinstance(v[0], dict) and "tool_id" in v[0]:
            return v
    return []

def _intent_routed(did):
    return did == "job_creation"

reg = DomainRegistry()
domains = sorted(d for d in _DOMAIN_REGISTRY if isinstance(d, str))

# Domain blurbs
DOMAIN_BLURB = {
    "agent_studio": "Criação, calibração e marketplace de agentes customizados por tenant.",
    "analytics": "Relatórios de KPIs, funil de conversão, anomalias e previsões de recrutamento.",
    "ats_integration": "Sincronização bidirecional com ATS externos (Gupy, Pandape, Merge).",
    "automation": "Tarefas, regras de automação, alertas proativos e agendamentos recorrentes.",
    "candidate_self_service": "Portal do candidato (status, entrevista, feedback, dados LGPD).",
    "communication": "Email, WhatsApp, Teams, SMS e templates de comunicação multi-canal.",
    "company_settings": "Configuração do perfil da empresa, cultura, stack tecnológica e benefícios.",
    "cv_screening": "Parsing de CV, score WSI, avaliação de rubricas, perguntas dinâmicas e voice screening.",
    "digital_twin": "Gêmeo digital de avaliador (clonagem do julgamento humano).",
    "hiring_policy": "Configuração das políticas de contratação da empresa via wizard de políticas.",
    "interview_scheduling": "Agendamento, lembretes, conflito de agenda, transcrição e análise de voz em entrevistas.",
    "job_creation": "Wizard conversacional de criação de vaga com metodologia WSI (intent-routed).",
    "job_management": "Ciclo de vida de vagas: criação, atualização, pausar, fechar, clonar, templates e enriquecimento de JD.",
    "pipeline_transition": "Movimentação de candidatos no pipeline com explicação de contexto e sub-status.",
    "recruiter_assistant": "Assistente geral do recrutador (briefing, kanban, memória, alertas) — domínio default.",
    "recruitment_campaign": "Campanhas multi-etapa de recrutamento (atração, engajamento, conversão).",
    "sourcing": "Busca ativa de candidatos (local, semantic, global, Pearch), enriquecimento, outreach.",
    "talent_pool": "Talent pools — criação, vínculo com vagas e geração de vagas a partir de pools.",
}

# Architectural pattern by domain
PATTERN = {
    "agent_studio":         ("LangGraphReActBase", "via agent (sem _ACTION_TOOL_MAP)", "—", "evolução"),
    "analytics":            ("LangGraphReActBase", "_ACTION_TOOL_MAP", "AnalyticsReActAgent", "production"),
    "ats_integration":      ("LangGraphReActBase", "_ACTION_TOOL_MAP", "ATSIntegrationReActAgent", "production"),
    "automation":           ("LangGraphReActBase", "_ACTION_TOOL_MAP", "AutomationReActAgent", "production"),
    "candidate_self_service":("LangGraphReActBase", "via agent", "CandidateSelfServiceAgent", "evolução"),
    "communication":        ("LangGraphReActBase", "_ACTION_TOOL_MAP", "CommunicationReActAgent", "production"),
    "company_settings":     ("LangGraphReActBase", "via agent", "CompanySettingsReActAgent", "evolução"),
    "cv_screening":         ("LangGraphReActBase", "_ACTION_TOOL_MAP", "PipelineReActAgent", "production"),
    "digital_twin":         ("DomainPrompt simples", "via agent", "—", "evolução"),
    "hiring_policy":        ("LangGraphReActBase", "via agent", "PolicyReActAgent (+ PolicySetupAgent)", "production"),
    "interview_scheduling": ("LangGraphReActBase", "_ACTION_TOOL_MAP", "—", "production"),
    "job_creation":         ("StateGraph custom (JobCreationGraph)", "process_intent + _route_by_stage (intent-routed)", "—", "production (ADR-019)"),
    "job_management":       ("LangGraphReActBase", "_ACTION_TOOL_MAP", "WizardReActAgent (+ JobWizardGraph)", "production"),
    "pipeline_transition":  ("LangGraphReActBase", "via agent", "PipelineTransitionAgent + 3 sub-agents (Action/Decision/Context)", "production"),
    "recruiter_assistant":  ("LangGraphReActBase", "_ACTION_TOOL_MAP", "KanbanReActAgent (+ Action/Insight/Search) + TalentReActAgent + JobsManagementReActAgent", "production (DEFAULT_DOMAIN)"),
    "recruitment_campaign": ("DomainPrompt simples", "via agent", "—", "evolução"),
    "sourcing":             ("LangGraphReActBase", "_ACTION_TOOL_MAP", "SourcingReActAgent + 9 sub-agents (Planner/Search/Enrich/Engagement/Diversity/Github/StackOverflow/Referral/Nurture/PassivePipeline)", "production"),
    "talent_pool":          ("DomainPrompt simples", "via agent", "—", "evolução"),
}

# Helper sentences inferred from name+description
def how_acts_action(action_id, domain_id, action_tool_map):
    if domain_id == "job_creation":
        return f"Roteado por estágio do wizard via `process_intent` → handler interno do `JobCreationGraph` (LangGraph)."
    tool = action_tool_map.get(action_id)
    if tool:
        return f"Mapeada para a tool `{tool}` em `_ACTION_TOOL_MAP`; executada via `execute_{domain_id}_tool` → handler resolvido por `resolve_handler_path`."
    return f"Executada diretamente pelo agente do domínio (`{PATTERN[domain_id][2]}`) sem tool intermediária — usa LLM + serviços do domínio."

def what_solves(action_id):
    aid = action_id.lower()
    if "search" in aid or "find" in aid: return "Resolve a busca/descoberta requisitada pelo recrutador no fluxo conversacional."
    if "send" in aid or "notify" in aid: return "Entrega comunicação ao candidato/stakeholder no canal apropriado."
    if "create" in aid or "add" in aid: return "Materializa um novo registro/objeto solicitado pelo recrutador."
    if "update" in aid or "set" in aid or "configure" in aid or "edit" in aid: return "Persiste a alteração solicitada sem sair do chat."
    if "list" in aid or "get" in aid or "view" in aid: return "Devolve dados ao chat para o recrutador decidir o próximo passo."
    if "delete" in aid or "cancel" in aid or "reject" in aid or "close" in aid or "pause" in aid: return "Encerra/desliga o item alvo respeitando políticas (HITL quando exigido)."
    if "generate" in aid or "predict" in aid or "forecast" in aid: return "Gera artefato derivado por IA para acelerar a decisão do recrutador."
    if "approve" in aid: return "Materializa o gate HITL: o recrutador aprova/rejeita uma proposta da IA antes de avançar."
    if "calibrate" in aid: return "Refina o agente/perfil com base em feedback recente para reduzir falsos positivos/negativos."
    if "schedule" in aid or "reminder" in aid: return "Agenda interação ou tarefa no momento certo do funil."
    if "sync" in aid or "pull" in aid: return "Sincroniza dados entre LIA e ATS externo evitando trabalho manual de cópia."
    if "wizard" in aid or "stage" in aid: return "Avança o fluxo conversacional por etapas estruturadas."
    return "Atende uma intenção específica do recrutador dentro do domínio."

def how_acts_tool(handler):
    if not handler: return "Handler resolvido em runtime."
    return f"Handler `{handler}` (resolvido por `app.shared.tool_handler.resolve_handler_path`); enforcement de tenant via `@tool_handler` (fail-closed)."

def what_does(desc, fallback):
    return (desc or fallback).strip()

# Build markdown
lines = []
lines.append("# Glossário de Actions e Tools — Plataforma LIA\n")
lines.append("> **Fonte da verdade:** geração programática a partir do `DomainRegistry` ao vivo + descrições declaradas em cada `DomainAction`/`tool_id`.\n")
lines.append("> **Geração:** `python3 scripts/generate_glossario_actions_tools.py` (regenerar quando registries mudarem).  \n")
lines.append("> **Documentos relacionados:** [`MAPA_CAMADA_INTELIGENCIA.md`](./MAPA_CAMADA_INTELIGENCIA.md) (fluxos), [`fase2c_domain_verification_report.md`](./fase2c_domain_verification_report.md) (auditoria viva), [`../ARCHITECTURE.md`](../ARCHITECTURE.md) (ADRs normativos).\n")
lines.append("\n---\n")

# Index
total_actions = sum(len(reg.get_instance(d).get_allowed_actions() or []) for d in domains)
total_tools = sum(len(_load_tools(d)) for d in domains)
lines.append(f"\n## Índice — {len(domains)} domínios, {total_actions} actions, {total_tools} tools\n\n")
lines.append("| # | Domínio | Actions | Tools | Padrão de execução |\n|---|---|---:|---:|---|\n")
for i, did in enumerate(domains, 1):
    a = len(reg.get_instance(did).get_allowed_actions() or [])
    t = len(_load_tools(did))
    p = PATTERN[did][1]
    lines.append(f"| {i} | [`{did}`](#dom-{did}) | {a} | {t} | {p} |\n")
lines.append(f"| **Σ** | | **{total_actions}** | **{total_tools}** | |\n")

lines.append("\n### Convenções\n\n")
lines.append("Cada entrada traz três frases curtas:\n\n")
lines.append("1. **O que faz** — descrição declarada no registry (ou inferida do nome).\n")
lines.append("2. **O que resolve** — qual problema do recrutador resolve no fluxo conversacional.\n")
lines.append("3. **Como atua tecnicamente** — handler/serviço/integração que materializa a operação.\n\n")
lines.append("Tools sem entrada equivalente em actions são executadas diretamente pelo agente; actions sem tool são executadas via LLM/agent (intent-routed em `job_creation`).\n")

# Per-domain sections
lines.append("\n---\n\n## Glossário por Domínio\n")
all_actions_idx = []
all_tools_idx = []
for did in domains:
    inst = reg.get_instance(did)
    actions = inst.get_allowed_actions() or []
    tools = _load_tools(did)
    base_cls, exec_pat, agent, status = PATTERN[did]
    blurb = DOMAIN_BLURB.get(did, "")
    lines.append(f"\n### <a id='dom-{did}'></a>{did}\n\n")
    lines.append(f"**Domínio:** `{did}`  \n**Classe:** `{type(inst).__name__}`  \n**Agente principal:** {agent}  \n**Padrão de execução:** {exec_pat}  \n**Status:** {status}  \n\n")
    if blurb: lines.append(f"_{blurb}_\n\n")

    # Build action_tool_map by introspection
    dir_name = {"pipeline_transition":"pipeline"}.get(did, did); dmod = importlib.import_module(f"app.domains.{dir_name}.domain")
    atm = getattr(dmod, "_ACTION_TOOL_MAP", {}) or {}

    if actions:
        lines.append(f"#### Actions ({len(actions)})\n\n")
        lines.append("| action_id | O que faz | O que resolve | Como atua |\n|---|---|---|---|\n")
        for a in sorted(actions, key=lambda x: x.action_id):
            wd = what_does(a.description or a.name, a.action_id.replace("_"," "))
            ws = what_solves(a.action_id)
            ha = how_acts_action(a.action_id, did, atm)
            wd_e = wd.replace('|','\\|')
            ws_e = ws.replace('|','\\|')
            ha_e = ha.replace('|','\\|')
            lines.append(f"| `{a.action_id}` | {wd_e} | {ws_e} | {ha_e} |\n")
            all_actions_idx.append((a.action_id, did))

    if tools:
        lines.append(f"\n#### Tools ({len(tools)})\n\n")
        lines.append("| tool_id | O que faz | O que resolve | Como atua |\n|---|---|---|---|\n")
        for t in sorted(tools, key=lambda x: x.get("tool_id","")):
            tid = t.get("tool_id")
            desc = t.get("description") or tid.replace("_", " ")
            handler = t.get("handler","")
            ws = what_solves(tid)
            ha = how_acts_tool(handler)
            wd_e = desc.replace('|','\\|')
            ws_e = ws.replace('|','\\|')
            ha_e = ha.replace('|','\\|')
            lines.append(f"| `{tid}` | {wd_e} | {ws_e} | {ha_e} |\n")
            all_tools_idx.append((tid, did))

# Alphabetical indexes
lines.append("\n---\n\n## Índice Alfabético — Actions\n\n")
lines.append("| action_id | domínio |\n|---|---|\n")
for aid, did in sorted(all_actions_idx):
    lines.append(f"| [`{aid}`](#dom-{did}) | `{did}` |\n")

lines.append("\n## Índice Alfabético — Tools\n\n")
lines.append("| tool_id | domínio |\n|---|---|\n")
for tid, did in sorted(all_tools_idx):
    lines.append(f"| [`{tid}`](#dom-{did}) | `{did}` |\n")

lines.append("\n---\n\n_Última geração programática a partir do registry. Para regenerar, rode `python3 scripts/generate_glossario_actions_tools.py` a partir de `lia-agent-system/`._\n")

out = ROOT / "docs" / "GLOSSARIO_ACTIONS_TOOLS.md"
out.write_text("".join(lines))
print(f"Wrote {out} ({sum(len(l) for l in lines)} chars, {len(all_actions_idx)} actions, {len(all_tools_idx)} tools)")
