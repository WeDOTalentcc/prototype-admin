"""T6 (#993) — Sentinela anti-padrão para o agente `company_settings`.

Origem: o chat lateral de Configurações dispara prompts com tags estruturadas
(`[ACTION:prefill_section][target_section:<key>]`). O agente DEVE:

  1. Reconhecer a tag e restringir o escopo à seção indicada.
  2. NUNCA perguntar dados que já estão no `tenant_context_snippet`
     (nome empresa, setor, plano, headcount). Esse foi o bug T-E
     ("LIA pergunta company_id no chat") — esta sentinela impede
     que ele volte especificamente pelo agente de settings.
  3. Após HITL, persistir via tools canônicas (`save_company_field`,
     `save_company_section`, `import_benefits_from_data`,
     `import_workforce_plan`) — todas com FairnessGuard ativo.

Esta suite roda offline (não chama LLM): inspeciona o prompt YAML
renderizado + o template do agente. Espelha a estratégia de
`test_tenant_context_no_regression.py` (Contrato 2 — anti-padrão no
prompt). Se um futuro PR adicionar uma frase como "qual o setor da
empresa?" ao prompt, este teste quebra antes do merge.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from app.domains.company_settings.agents.company_react_agent import (
    CompanySettingsReActAgent,
)
from app.domains.company_settings.agents.company_system_prompt import (
    get_company_system_prompt,
)
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin


# ─── Setup ─────────────────────────────────────────────────────────────────

YAML_PATH = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "prompts"
    / "domains"
    / "company_settings.yaml"
)


# Anti-padrões que NUNCA podem aparecer num system prompt do agente
# `company_settings` quando `tenant_context_snippet` está disponível.
# Cada padrão corresponde a uma pergunta redundante / regressão T-E.
REDUNDANT_QUESTION_REGEX = re.compile(
    r"(?ix)("
    r"  qual\s+(é\s+)?(o\s+)?(nome|setor|porte|tamanho|plano|headcount|industria)\s+da?\s+empresa"
    r"| qual\s+a\s+industria"
    r"| em\s+qual\s+empresa\s+você\s+trabalha"
    r"| preciso\s+saber\s+(qual\s+)?(é\s+)?a?\s*empresa"
    r"| informe\s+(o\s+)?company[_\s]?id"
    r"| me\s+informe\s+(qual\s+)?(a\s+)?empresa"
    r"| quantos\s+funcion[áa]rios\s+(voc[êe]s?|a\s+empresa)\s+t[êe]m"
    r")"
)


# ─── Contrato 1: agente herda mixin e respeita padrão T-D ──────────────────


def test_agent_inherits_tenant_aware_mixin():
    """Sentinela T-D: agente continua no inventário canônico."""
    assert issubclass(CompanySettingsReActAgent, TenantAwareAgentMixin), (
        "CompanySettingsReActAgent perdeu TenantAwareAgentMixin — "
        "tenant_context_snippet não é mais propagado e o bug T-E "
        "('LIA pergunta company_id') reabre neste agente."
    )


def test_agent_has_runtime_prompt_hook():
    """Sentinela T-D: agente sobrescreve `_get_runtime_domain_instructions`,
    única forma canônica de injetar o snippet via PromptComposer.
    """
    assert "_get_runtime_domain_instructions" in vars(CompanySettingsReActAgent), (
        "CompanySettingsReActAgent perdeu override de "
        "_get_runtime_domain_instructions — snippet T-E não flui mais."
    )


# ─── Contrato 2: prompt YAML não contém perguntas redundantes ──────────────


def test_yaml_has_no_redundant_company_questions():
    """Bug-repro core: nas chaves do YAML que descrevem o que a LIA FALA
    (identity, behavioral_rules, structured_action_tags, ethical_validation,
    config_blocks, system_prompt), NUNCA pode aparecer instrução do tipo
    'pergunte qual o setor da empresa', porque setor/nome/plano já estão
    no `tenant_context_snippet` (resolvido do JWT).

    Importante: chaves como `intent_examples` e `few_shot_examples` (input
    do usuário ou diálogo demonstrativo) são exclusas do scan — elas
    descrevem o que o USUÁRIO pode dizer, não o que a LIA deve dizer.

    Se um PR futuro adicionar uma instrução como "Pergunte qual a
    indústria da empresa" em `behavioral_rules` ou similar, este teste
    quebra imediatamente.
    """
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    # Apenas chaves que descrevem a VOZ DA LIA. NÃO incluir intent_examples
    # (input do usuário) nem few_shot_examples (diálogo demonstrativo).
    lia_voice_keys = [
        "identity",
        "behavioral_rules",
        "structured_action_tags",
        "ethical_validation",
        "config_blocks",
        "system_prompt",
    ]
    offenders: list[tuple[str, list]] = []
    for key in lia_voice_keys:
        block = data.get(key, "")
        if not isinstance(block, str):
            continue
        matches = REDUNDANT_QUESTION_REGEX.findall(block)
        if matches:
            offenders.append((key, matches))
    assert not offenders, (
        f"company_settings.yaml contém perguntas redundantes nas chaves "
        f"que descrevem a voz da LIA: {offenders!r}\n"
        "Remover — esses campos vêm do JWT via TenantAwareAgentMixin."
    )


def test_yaml_structured_action_tags_maps_policy_to_save_hiring_policy_pr2():
    """PR2 (Task #1002) — sentinela contra regressão do bug C1 do audit T1-T6.

    O mapeamento `policy → save_hiring_policy` em `structured_action_tags` é
    o ÚNICO contrato que dirige o LLM a persistir hiring policy em
    `company_hiring_policies`. Antes do fix C1, o YAML apontava `policy`
    para `save_company_section`, que rejeita silenciosamente (whitelist
    {profile, culture}) — a IA confirmava o save mas nada chegava ao DB.

    Trava 2 contratos:
      1. O bloco de policy em `structured_action_tags` cita `save_hiring_policy`.
      2. NÃO mapeia mais `policy` para `save_company_section`/`save_company_field`
         (rota antiga, dead code para hiring policy).
    """
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    tags_block = data.get("structured_action_tags", "")
    assert isinstance(tags_block, str) and tags_block.strip(), (
        "structured_action_tags ausente do YAML."
    )
    policy_line_match = re.search(
        r"-\s*policy\s*(?:\u2192|->)[^\n]+", tags_block
    )
    assert policy_line_match, (
        "PR2 regressão: linha de mapeamento `- policy -> ...` removida de "
        "structured_action_tags. Sem ela o agente fica sem caminho canônico "
        "para persistir hiring policy via chat."
    )
    policy_line = policy_line_match.group(0)
    assert "save_hiring_policy" in policy_line, (
        "PR2 regressão: mapeamento `policy -> ...` perdeu referência a "
        f"`save_hiring_policy`. Linha atual: {policy_line!r}. Sem essa tool, "
        "o save de hiring policy via chat volta a ser dead code (bug C1 do "
        "audit T1-T6)."
    )
    for legacy in ("save_company_section", "save_company_field"):
        assert legacy not in policy_line, (
            f"PR2 regressão: mapeamento `policy -> ...` voltou a citar a rota "
            f"antiga `{legacy}`. Essa rota não suporta a tabela "
            "company_hiring_policies — usar save_hiring_policy."
        )


def test_yaml_structured_action_tags_lists_basic_section():
    """PR1 (Task #1001) — sentinela contra regressão do bug C2 do audit
    T1-T6: a seção `basic` (Dados Básicos) precisa permanecer listada
    como valor válido de `<key>` em `structured_action_tags` do YAML.
    Se removida, o agente perde 11 campos cadastrais de
    `company_profiles` (name, cnpj, website, hr_email, hr_phone,
    address, industry, company_size, employee_count, founded_year,
    linkedin_url) — voltaria ao estado pré-PR1, com cobertura efetiva
    via chat caindo de 7 para 6 seções.
    """
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    tags_block = data.get("structured_action_tags", "")
    assert isinstance(tags_block, str), (
        "structured_action_tags ausente ou não é string."
    )
    # 1) precisa estar na lista de "Valores válidos de <key>"
    valid_values_match = re.search(
        r"Valores\s+válidos\s+de\s+<key>\s*:\s*([^\n.]+)",
        tags_block,
        re.IGNORECASE,
    )
    assert valid_values_match, (
        "structured_action_tags perdeu a frase 'Valores válidos de <key>: ...' "
        "— contrato com o frontend (PrefillSection em "
        "use-settings-conversational.ts) deixa de ser validável."
    )
    valid_values_text = valid_values_match.group(1).lower()
    assert "basic" in valid_values_text, (
        f"PR1 regressão: 'basic' sumiu da lista de valores válidos de "
        f"<key> em structured_action_tags. Lista atual: "
        f"{valid_values_match.group(1)!r}. O hub Minha Empresa fica sem "
        "entrada conversacional para 11 campos de company_profiles."
    )
    # 2) precisa ter mapeamento explícito basic → save_company_field/save_company_section
    assert re.search(
        r"-\s*basic\s*(?:→|->)\s*save_company_(field|section)",
        tags_block,
    ), (
        "PR1 regressão: mapeamento `basic → save_company_field/save_company_section` "
        "removido de structured_action_tags. Sem ele o agente não sabe qual "
        "tool chamar quando recebe [target_section:basic]."
    )


def test_frontend_section_labels_includes_basic():
    """PR1 (Task #1001) — sentinela cross-stack: o hook frontend
    `use-settings-conversational.ts` precisa manter `basic` em
    `PrefillSection` E em `SECTION_LABELS`. Se um PR futuro reverter
    qualquer uma das duas, o botão `pending-prefill-basic` some do hub
    Minha Empresa e a tag `[ACTION:prefill_section][target_section:basic]`
    deixa de ser disparada — frontend e backend (YAML) ficam
    silenciosamente fora de sync.

    A lógica é uma checagem textual via regex porque o teste roda em
    Python (lia-agent-system) e o source-of-truth é TS
    (plataforma-lia). Espelha a estratégia de "Contrato 2 — anti-padrão
    no prompt" deste arquivo: failure mode = drift detectável
    pré-merge.
    """
    hook_path = (
        Path(__file__).resolve().parents[4]
        / "plataforma-lia"
        / "src"
        / "hooks"
        / "settings"
        / "use-settings-conversational.ts"
    )
    if not hook_path.exists():  # pragma: no cover — defesa contra reorganização
        pytest.skip(
            f"Hook frontend não encontrado em {hook_path} — repo "
            "reorganizado? Atualizar este teste."
        )
    src = hook_path.read_text(encoding="utf-8")
    # PrefillSection union: linha do tipo `| "basic"` (ou primeira "basic" depois de PrefillSection =).
    assert re.search(
        r"PrefillSection\s*=[^;]*\|\s*\"basic\"",
        src,
        re.DOTALL,
    ), (
        "PR1 regressão: tipo `PrefillSection` em use-settings-conversational.ts "
        "perdeu o membro \"basic\". O hub Minha Empresa fica sem entrada "
        "conversacional para Dados Básicos (bug C2 do audit T1-T6)."
    )
    # SECTION_LABELS: linha `basic: "Dados Básicos"` (label exato — se
    # o PM trocar o copy, este teste lembra de revisar o YAML também).
    assert re.search(
        r"basic\s*:\s*[\"']Dados\s+B[áa]sicos[\"']",
        src,
    ), (
        "PR1 regressão: SECTION_LABELS em use-settings-conversational.ts "
        "perdeu a entrada `basic: \"Dados Básicos\"`. Sem o label, "
        "triggerPrefillSection() falha em runtime quando o usuário clica "
        "no botão `pending-prefill-basic` do MinhaEmpresaHub."
    )


def test_yaml_documents_structured_action_tags():
    """Contrato T6: o prompt YAML deve documentar o reconhecimento das
    tags `[ACTION:*][target_section:*]` enviadas pelo frontend
    (use-settings-conversational.ts). Se a documentação for removida,
    o agente deixa de honrar o hard-scope e o chat lateral vira
    "qualquer coisa pode acontecer".
    """
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    tags_block = data.get("structured_action_tags", "")
    assert isinstance(tags_block, str) and tags_block.strip(), (
        "company_settings.yaml perdeu a chave `structured_action_tags` — "
        "agente deixa de honrar o contrato T6 com o chat lateral."
    )
    required_tokens = [
        "[ACTION:prefill_section]",
        "[target_section:",
        "tenant_context_snippet",
    ]
    for token in required_tokens:
        assert token in tags_block, (
            f"`structured_action_tags` no YAML perdeu o marcador {token!r} — "
            "contrato chat ↔ agente quebrado."
        )


def test_yaml_documents_tenant_context_invariant():
    """A regra #8 de behavioral_rules é a barreira textual contra o bug
    T-E. Se for removida, o agente volta a perguntar dados já
    resolvidos via JWT.
    """
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    rules = data.get("behavioral_rules", "")
    assert "tenant_context_snippet" in rules, (
        "behavioral_rules perdeu a invariante T-E sobre tenant_context_snippet "
        "— agente fica livre pra pedir nome/setor/plano de novo."
    )


# ─── Contrato 3: system prompt renderizado herda as garantias ─────────────


def test_rendered_system_prompt_has_no_redundant_questions():
    """Mesmo após composição via PromptLoader + system_prompt header,
    o resultado renderizado NÃO pode conter perguntas redundantes.
    """
    rendered = get_company_system_prompt()
    matches = REDUNDANT_QUESTION_REGEX.findall(rendered)
    assert not matches, (
        f"System prompt renderizado contém perguntas redundantes: {matches!r}\n"
        "Provável regressão no header de get_company_system_prompt() ou "
        "no YAML carregado via PromptLoader."
    )


def test_rendered_system_prompt_includes_structured_action_tags():
    """T6 (#993) — wiring crítico: o bloco `structured_action_tags` do
    YAML precisa chegar ao prompt renderizado. Se este teste quebrar, o
    agente PERDE a capacidade de reconhecer as tags
    `[ACTION:prefill_section][target_section:X]` enviadas pelo chat
    lateral (use-settings-conversational.ts) e a integração T6 fica
    silenciosamente quebrada — o golden dataset passaria mas em runtime
    a LIA divagaria entre seções.
    """
    rendered = get_company_system_prompt()
    required_markers = [
        "[ACTION:prefill_section]",
        "[target_section:",
        "tenant_context_snippet",
        "import_workforce_plan",  # mapeamento workforce — corrigido em T6
    ]
    for marker in required_markers:
        assert marker in rendered, (
            f"System prompt renderizado perdeu marcador T6 {marker!r} — "
            "wiring de behavioral_rules/structured_action_tags em "
            "company_system_prompt.py foi removido."
        )


# ─── Contrato 4: tools canônicas continuam expostas ───────────────────────


def test_canonical_tools_are_registered():
    """Sentinela T6: as tools citadas pelo `structured_action_tags` no
    YAML devem existir como callables. O agente `company_settings` consome
    tools por dois caminhos:

      (a) Tools "internas" expostas via
          `get_company_settings_tools()` — registry local do agente.
      (b) Tools globais registradas via `register_company_settings_tools()`
          em `tools/import_tools.py` (allowed_agents inclui company_settings).

    Se qualquer uma dessas tools sumir, o mapeamento documentado no YAML
    quebra silenciosamente — a LIA tenta chamar uma tool que não existe.
    """
    from app.domains.company_settings.agents.company_tool_registry import (
        get_company_settings_tools,
    )
    from app.domains.company_settings.tools import import_tools

    local_names = {t.name for t in get_company_settings_tools()}
    required_local = {
        "get_company_profile",
        "save_company_field",
        "save_company_section",
        "analyze_company_website",
        "process_uploaded_document",
        "import_workforce_plan",
        "get_company_completion",
        # PR2 (Task #1002) — bug C1 do audit T1-T6: o agente
        # `CompanySettingsReActAgent` carrega tools por
        # `get_company_settings_tools()`. Sem `save_hiring_policy` aqui,
        # o YAML aponta `policy → save_hiring_policy` mas o LLM colide com
        # `tool_not_found` em runtime — re-criando C1 na camada do agente.
        "save_hiring_policy",
    }
    missing_local = required_local - local_names
    assert not missing_local, (
        f"Tools canônicas removidas do registry local do agente: "
        f"{sorted(missing_local)} — `structured_action_tags` no YAML "
        "deixou de bater com `get_company_settings_tools()`."
    )

    # Tools globais citadas no mapeamento (benefits + policy). Se forem
    # removidas, o YAML aponta para callables inexistentes.
    required_global_callables = (
        "import_benefits_from_data",
        "suggest_recruiting_policy",
        "save_hiring_policy",
    )
    for name in required_global_callables:
        assert hasattr(import_tools, name) and callable(
            getattr(import_tools, name)
        ), (
            f"Tool global '{name}' citada no `structured_action_tags` "
            "do YAML não está mais exportada por "
            "app/domains/company_settings/tools/import_tools.py."
        )


# ─── Contrato 4b (PR0 / Task #1000): wiring runtime no tool_registry global ──


def test_register_company_settings_tools_wired_in_initialize_tools():
    """PR0 (Task #1000) — bug C0 do audit T1-T6: a função
    `register_company_settings_tools()` em
    `app/domains/company_settings/tools/import_tools.py` registra 3 tools
    globais (`check_company_completeness`, `suggest_recruiting_policy`,
    `import_benefits_from_data`) com `allowed_agents` incluindo
    `company_settings`, `recruiter_assistant` e `orchestrator`. Antes do
    fix PR0, ela NUNCA era invocada em runtime — letra morta. O LLM
    "via" o nome no prompt YAML, decidia chamar via function-calling, e
    `tool_executor` retornava `tool_not_found`.

    Esta sentinela valida que `initialize_tools()` (chamada no lifespan
    do FastAPI em `app/main.py:373`) realmente popula o `tool_registry`
    global com as 3 tools e que `company_settings` está em
    `allowed_agents` de cada uma. Se um futuro PR remover o callsite de
    `register_company_settings_tools()` em `app/tools/__init__.py`,
    este teste quebra antes do merge.
    """
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry

    # initialize_tools() é idempotente em re-registro (loga warning + overwrite).
    # Chamar aqui garante o estado pós-boot independente da ordem de testes.
    initialize_tools()

    required_global_tools = {
        "check_company_completeness",
        "suggest_recruiting_policy",
        "import_benefits_from_data",
        "save_hiring_policy",
    }
    registered = set(tool_registry.list_tools())
    missing = required_global_tools - registered
    assert not missing, (
        f"PR0 wiring quebrado: tools globais ausentes do tool_registry "
        f"após initialize_tools(): {sorted(missing)}. "
        "Verificar se `register_company_settings_tools()` continua sendo "
        "invocado em app/tools/__init__.py::initialize_tools()."
    )

    # company_settings precisa estar autorizado em todas as 3 — caso
    # contrário o agente não enxerga via tool_executor mesmo com a tool
    # registrada.
    for name in required_global_tools:
        tool = tool_registry.get_tool(name)
        assert tool is not None, f"Tool '{name}' sumiu de tool_registry."
        assert "company_settings" in (tool.allowed_agents or []), (
            f"Tool '{name}' registrada, mas `company_settings` não está em "
            f"allowed_agents={tool.allowed_agents!r} — agente não consegue chamá-la."
        )


def test_yaml_action_tools_resolvable_at_runtime():
    """PR0 (Task #1000) — defesa data-driven contra registry drift:
    extrai automaticamente todos os nomes de tools mencionados em
    blocos do YAML que descrevem chamadas de função
    (`structured_action_tags`, `behavioral_rules`, `few_shot_examples`)
    e valida que cada um seja resolvível em runtime — seja via toolset
    do próprio `CompanySettingsReActAgent` (caminho LangGraph), seja
    via `tool_registry` global após `initialize_tools()` (caminho
    function-calling do orchestrator/recruiter_assistant).

    Diferente de uma lista hardcoded, este teste falha automaticamente
    se um futuro PR adicionar `foo_bar_tool(...)` no YAML sem registrar
    a tool — fechando o gap de drift que motivou o PR0.
    """
    from app.domains.company_settings.agents.company_react_agent import (
        CompanySettingsReActAgent,
    )
    from app.domains.company_settings.agents.company_tool_registry import (
        get_company_settings_tools,
    )
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry

    initialize_tools()

    # Whitelist conhecida de identificadores que parecem chamada de tool
    # mas NÃO são (kwargs Python, nomes de campos, palavras reservadas).
    # Mantida pequena e documentada — qualquer falso-positivo novo deve
    # ser entendido antes de adicionar aqui.
    NOT_A_TOOL = {
        # kwargs comuns em assinaturas mostradas no YAML
        "section", "field", "value", "data", "benefits", "plan_data",
        "department", "role", "quantity", "deadline", "seniority",
        "sector", "company_size", "website_url", "document_type",
        "default_salary_ranges",
        # campos do schema response
        "success", "category",
        # palavras reservadas / builtins
        "if", "for", "in", "and", "or", "not", "is", "lambda",
        "print", "len", "str", "int", "list", "dict", "set", "tuple",
        "range", "type", "isinstance",
    }
    # Padrão snake_case com pelo menos um underscore — filtro pragmático
    # para reduzir ruído (palavras únicas como "benefits" não passam,
    # mas ficam no NOT_A_TOOL acima como reforço).
    TOOL_CALL_RE = re.compile(r"\b([a-z][a-z0-9_]*_[a-z0-9_]+)\s*\(")

    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    scan_keys = ("structured_action_tags", "behavioral_rules", "few_shot_examples")

    candidates: set[str] = set()
    for key in scan_keys:
        block = data.get(key, "")
        # few_shot_examples é lista de dicts — concatenar valores string.
        if isinstance(block, list):
            text_parts: list[str] = []
            for entry in block:
                if isinstance(entry, dict):
                    text_parts.extend(str(v) for v in entry.values())
                else:
                    text_parts.append(str(entry))
            text = "\n".join(text_parts)
        else:
            text = str(block)
        for match in TOOL_CALL_RE.findall(text):
            if match not in NOT_A_TOOL:
                candidates.add(match)

    assert candidates, (
        "Sentinela data-driven extraiu zero candidatos de tools do YAML. "
        "Provável regressão no parser ou nas chaves `scan_keys`."
    )

    # Toolset real do agente (caminho LangGraph) — é assim que o
    # CompanySettingsReActAgent enxerga tools em runtime via
    # _get_tools(). Usamos a função base get_company_settings_tools()
    # para evitar precisar instanciar o agente (que requer DB).
    agent_tool_names = {t.name for t in get_company_settings_tools()}
    # Defesa: se o nome da função privada do agente mudar, este teste
    # avisa explicitamente.
    assert "_get_tools" in dir(CompanySettingsReActAgent), (
        "CompanySettingsReActAgent perdeu `_get_tools` — reavaliar como "
        "esta sentinela monta agent_tool_names."
    )

    global_tool_names = set(tool_registry.list_tools())
    resolvable = agent_tool_names | global_tool_names

    unresolvable = candidates - resolvable
    assert not unresolvable, (
        f"YAML company_settings.yaml referencia tools que NINGUÉM registra "
        f"em runtime (nem toolset do agente, nem tool_registry global): "
        f"{sorted(unresolvable)}.\n"
        f"Candidatos extraídos do YAML: {sorted(candidates)}\n"
        f"Tools do agente: {sorted(agent_tool_names)}\n"
        f"Tools globais relevantes: "
        f"{sorted(t for t in global_tool_names if 'compan' in t or 'benefit' in t or 'recruit' in t)}\n"
        "LLM tentará chamar essas tools e receberá tool_not_found."
    )


# ─── Contrato 5: golden dataset T6 existe e tem 18 cenários ───────────────


def test_golden_dataset_exists_with_21_scenarios():
    """Golden dataset T6 (#993) + PR1 (#1001): 21 cenários = 7 seções × 3
    contratos (positivo, anti-padrão, fairness). PR1 adicionou a seção
    `basic` (Dados Básicos) cobrindo os 11 campos cadastrais de
    `company_profiles` (name, cnpj, website, hr_email, hr_phone, address,
    industry, company_size, employee_count, founded_year, linkedin_url) —
    inacessíveis via chat antes do fix. Roda via
    `python -m eval.eval_runner --gate eval/golden/company_settings_prefill.jsonl`.
    """
    import json

    golden = (
        Path(__file__).resolve().parents[3]
        / "eval"
        / "golden"
        / "company_settings_prefill.jsonl"
    )
    assert golden.exists(), (
        f"Golden dataset T6 ausente em {golden} — eval gate não roda."
    )
    rows = [json.loads(l) for l in golden.read_text().splitlines() if l.strip()]
    # Matriz mínima: 7 seções × 3 contratos = 21. PRs subsequentes podem
    # adicionar cenários EXTRAS (ex: PR2/Task #1002 adicionou
    # CSP-policy-save-positive e CSP-policy-save-anti-pattern, totalizando 23).
    # Por isso usamos >= 21 e validamos a matriz canônica separadamente.
    assert len(rows) >= 21, (
        f"Golden dataset T6+PR1 deve ter ao menos 21 cenários (matriz 7 seções × 3 contratos), "
        f"encontrado {len(rows)}."
    )

    sections = {"basic", "culture", "tech_stack", "benefits", "workforce", "policy", "compensation"}
    contracts = ("positive", "anti-pattern", "fairness")
    seen: set[tuple[str, str]] = set()
    for r in rows:
        cid = r["id"]  # ex: CSP-culture-positive, CSP-tech_stack-anti-pattern, CSP-policy-save-positive
        assert cid.startswith("CSP-"), f"id fora do padrão CSP-*: {cid}"
        body = cid[len("CSP-"):]
        # contract pode conter hífen ('anti-pattern') — match por sufixo,
        # não por rsplit('-', 1). Cenários extras (ex: CSP-policy-save-*)
        # não precisam bater com a matriz canônica, mas seguem todos os
        # demais contratos (agent, threshold, anti_patterns, success_criteria).
        match = next(
            ((s, c) for c in contracts for s in sections if body == f"{s}-{c}"),
            None,
        )
        if match is not None:
            seen.add(match)
        assert r.get("agent") == "company_settings", (
            f"{cid}: agent deve ser 'company_settings'"
        )
        assert r.get("fail_threshold_avg") == 0.85, (
            f"{cid}: threshold canônico T-E é 0.85"
        )
        assert r.get("anti_patterns"), f"{cid}: anti_patterns vazio"
        assert r.get("success_criteria"), f"{cid}: success_criteria vazio"

    expected = {(s, c) for s in sections for c in contracts}
    missing = expected - seen
    assert not missing, (
        f"Golden dataset T6 incompleto — faltam combinações canônicas: {sorted(missing)}"
    )

    # PR2 (Task #1002) — exigir explicitamente os 2 cenários extras de
    # save_hiring_policy. Se um futuro PR removê-los, o gate cai aqui
    # ANTES de chegar no eval_runner.
    extra_pr2 = {"CSP-policy-save-positive", "CSP-policy-save-anti-pattern"}
    ids_present = {r["id"] for r in rows}
    missing_pr2 = extra_pr2 - ids_present
    assert not missing_pr2, (
        f"PR2 (Task #1002) regressão: cenários de save_hiring_policy ausentes "
        f"do golden: {sorted(missing_pr2)}. Sem eles, a persistência real "
        "da política (bug C1 do audit) deixa de ser coberta pelo eval gate."
    )

    # PR3 (Task #1003) — exigir explicitamente os 3 cenários extras do
    # FairnessGuard recursivo (lista, dict-nested, string curta). Se um
    # futuro PR removê-los, o bypass C3 do audit T1-T6 deixa de ser
    # coberto pelo eval gate.
    extra_pr3 = {
        "CSP-culture-fairness-list-pr3",
        "CSP-compensation-fairness-dict-pr3",
        "CSP-policy-fairness-short-pr3",
    }
    missing_pr3 = extra_pr3 - ids_present
    assert not missing_pr3, (
        f"PR3 (Task #1003) regressão: cenários do FairnessGuard recursivo "
        f"ausentes do golden: {sorted(missing_pr3)}. Sem eles, o bypass C3 "
        "(list/dict/short-string) volta a passar despercebido."
    )


# ─── Contrato 5b: PR7 (Task #1007) — A5 compensation JSONB save path ─────


def test_pr7_a5_profile_additional_data_save_path_exposed():
    """PR7 (Task #1007) — gap A5 do audit T1-T6: o card "Remuneração &
    Onboarding" do hub Minha Empresa expõe `additional_notes`,
    `responsible_name` e `responsible_position` como editáveis, mas eles
    vivem em `company_profiles.additional_data` (JSONB) — antes do PR7
    NÃO havia rota de save via chat (caíam no `else` de
    `_save_company_field_impl` com a mensagem
    "Campo '<x>' nao e valido para perfil"), apesar de o frontend e o
    YAML mapearem `[target_section:compensation]` para o agente.

    Trava 3 contratos:
      1. A whitelist `_PROFILE_ADDITIONAL_DATA_FIELDS` continua exposta
         no módulo (pública para sentinela e para futuras extensões).
      2. As 3 chaves canônicas estão presentes — remover qualquer uma
         re-quebra o save da seção compensation no chat lateral.
      3. O builder gera o trio de queries (select/update/insert) com
         `jsonb_set` para CADA campo whitelisted — defesa contra um PR
         futuro que apague o builder mantendo a whitelist (silent
         regression).
    """
    from app.domains.company_settings.agents.company_tool_registry import (
        _PROFILE_ADDITIONAL_DATA_FIELDS,
        _PROFILE_ADDITIONAL_DATA_QUERIES,
    )

    required = {"additional_notes", "responsible_name", "responsible_position"}
    missing = required - set(_PROFILE_ADDITIONAL_DATA_FIELDS)
    assert not missing, (
        f"PR7/A5 regressão: campos canônicos do bloco compensation "
        f"ausentes de _PROFILE_ADDITIONAL_DATA_FIELDS: {sorted(missing)}. "
        "Sem eles o save via chat para Notas/Responsável volta a falhar "
        "silenciosamente — gap A5 do audit T1-T6 reabre."
    )

    for field in required:
        trio = _PROFILE_ADDITIONAL_DATA_QUERIES.get(field)
        assert trio is not None, (
            f"PR7/A5 regressão: builder _build_profile_additional_data_queries() "
            f"não gerou queries para '{field}' — _save_company_field_impl "
            "vai cair no `else` e o save morre silenciosamente."
        )
        select_q, update_q, insert_q = trio
        assert "additional_data" in update_q and "jsonb_set" in update_q, (
            f"PR7/A5 regressão: query de UPDATE para '{field}' deixou de "
            f"usar `jsonb_set` em `additional_data`. Atual: {update_q!r}."
        )
        assert "additional_data" in insert_q and "jsonb_build_object" in insert_q, (
            f"PR7/A5 regressão: query de INSERT para '{field}' deixou de "
            f"montar `additional_data` via `jsonb_build_object`. Atual: {insert_q!r}."
        )


def test_pr7_a5_yaml_compensation_lists_profile_additional_fields():
    """PR7 (Task #1007) — sentinela cross-stack: o mapeamento da seção
    `compensation` em `structured_action_tags` do YAML precisa citar
    `save_company_field(section="profile", field=<additional_notes|...>)`
    para fechar o loop A5. Se um PR futuro reverter o mapeamento para só
    `save_company_section(section="culture", ...)`, a LIA volta a ter
    apenas o caminho `default_salary_ranges`/`seniority_levels` — Notas
    e Responsável ficam órfãos novamente.
    """
    data = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    tags_block = data.get("structured_action_tags", "")
    comp_line_match = re.search(
        r"-\s*compensation\s*(?:→|->)[^\n]+", tags_block
    )
    assert comp_line_match, (
        "PR7/A5 regressão: linha de mapeamento `- compensation -> ...` "
        "removida de structured_action_tags."
    )
    line = comp_line_match.group(0)
    for token in (
        "save_company_field",
        "additional_notes",
        "responsible_name",
        "responsible_position",
    ):
        assert token in line, (
            f"PR7/A5 regressão: mapeamento `compensation` perdeu referência a "
            f"`{token}`. Linha atual: {line!r}. Sem essa rota o save de "
            "Notas/Responsável via chat volta a ser dead code (gap A5 do "
            "audit T1-T6)."
        )


# ─── Contrato 6: PR3 (Task #1003) — FairnessGuard recursivo aplicado ─────


def test_pr3_fairness_recursive_helper_importable():
    """PR3 (Task #1003) — sentinela contra remoção do helper canônico
    `validate_fairness_recursive`. Se o módulo ou a função sumir, os 5
    wrappers de save voltam ao bypass C3 (filtro `len > 10` + listas/dicts
    ignorados) silenciosamente.
    """
    from app.shared.compliance import fairness_recursive

    assert hasattr(fairness_recursive, "validate_fairness_recursive"), (
        "PR3 regressão: app/shared/compliance/fairness_recursive.py perdeu "
        "`validate_fairness_recursive` — bypass C3 do audit T1-T6 reabre."
    )
    assert hasattr(fairness_recursive, "RecursiveFairnessResult"), (
        "PR3 regressão: dataclass `RecursiveFairnessResult` removida — "
        "o contrato `{offending_field, offending_signal, category}` que a "
        "rule #4 do YAML exige na resposta da tool deixa de existir."
    )


def test_pr3_save_tools_call_fairness_recursive():
    """PR3 (Task #1003) — defesa AST contra regressão do bypass C3.

    Inspeciona via `ast` que CADA UMA das 5 tools de save/import abaixo
    chama `validate_fairness_recursive` no corpo da função. Se um futuro
    PR remover a chamada (ou voltar para o filtro `len > 10` parcial),
    este teste quebra antes do merge.
    """
    import ast

    targets: list[tuple[Path, set[str]]] = [
        (
            Path(__file__).resolve().parents[3]
            / "app"
            / "domains"
            / "company_settings"
            / "agents"
            / "company_tool_registry.py",
            {
                # PR4 (Task #1004) extraiu o corpo dos wrappers `_wrap_*`
                # para helpers `_*_impl` (envolvidos por audit_company_change).
                # A validação de fairness ficou nos helpers — onde o trabalho
                # real acontece. `_wrap_save_company_section` permaneceu
                # monolítico porque já era curto.
                "_save_company_field_impl",
                "_wrap_save_company_section",
                "_import_workforce_plan_impl",
            },
        ),
        (
            Path(__file__).resolve().parents[3]
            / "app"
            / "domains"
            / "company_settings"
            / "tools"
            / "import_tools.py",
            # PR4 (Task #1004) também extraiu corpos para `_*_impl` em
            # import_tools.py (save_hiring_policy / import_benefits_from_data).
            {"_save_hiring_policy_impl", "_import_benefits_from_data_impl"},
        ),
    ]

    for module_path, required_funcs in targets:
        assert module_path.exists(), f"Arquivo esperado não existe: {module_path}"
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        # Mapeia nome de função -> set de nomes de calls (para Name e Attribute)
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if node.name not in required_funcs:
                continue
            calls: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Name):
                        calls.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.add(func.attr)
            if "validate_fairness_recursive" not in calls:
                offenders.append(f"{module_path.name}::{node.name}")
        assert not offenders, (
            "PR3 regressão (bypass C3 reaberto): as funções abaixo NÃO chamam "
            f"`validate_fairness_recursive`: {offenders}. Sem essa chamada, "
            "FairnessGuard volta a deixar passar listas/dicts/strings curtas "
            "(audit T1-T6, finding C3)."
        )

    # Defesa adicional: o filtro antigo `len(...) > 10` não pode mais
    # aparecer em nenhum dos dois arquivos — era exatamente o gating
    # bypass que o PR3 removeu.
    legacy_pattern = re.compile(r"len\s*\(\s*[a-zA-Z_]+\s*\)\s*>\s*10")
    for module_path, _ in targets:
        src = module_path.read_text(encoding="utf-8")
        assert not legacy_pattern.search(src), (
            f"PR3 regressão: filtro legado `len(...) > 10` reapareceu em "
            f"{module_path.name}. Esse era o bypass C3 — quem decide o que "
            "é viés é o FairnessGuard, não o caller."
        )


# ─── Contrato 7: PR4 (Task #1004) — audit log canônico SOX/ISO ────────────


def test_pr4_audit_decorator_helper_importable():
    """PR4 (Task #1004) — sentinela contra remoção do wrapper canônico
    ``audit_company_change``. Se o módulo ou a função sumir, todas as 6
    save/read tools de company_settings voltam a ficar invisíveis ao
    audit trail (bug C4 do audit T1-T6, viola Inegociável #6 SOX/EU AI Act).
    """
    from app.shared.compliance import audit_decorators

    assert hasattr(audit_decorators, "audit_company_change"), (
        "PR4 regressão: app/shared/compliance/audit_decorators.py perdeu "
        "`audit_company_change` — bug C4 do audit T1-T6 reabre."
    )
    assert hasattr(audit_decorators, "is_company_audit_disabled"), (
        "PR4 regressão: helper `is_company_audit_disabled` removido — "
        "wrapper deixa de respeitar `LIA_DISABLE_COMPANY_AUDIT`."
    )


def test_pr4_save_tools_call_audit_company_change():
    """PR4 (Task #1004) — defesa AST contra regressão do bug C4.

    Inspeciona via ``ast`` que CADA UMA das 6 tools (5 save + 1 read)
    de ``company_settings`` chama ``audit_company_change`` no corpo da
    função. Se um futuro PR remover a chamada (ou voltar para o
    fire-and-forget try/except:pass), este teste quebra antes do merge.
    """
    import ast

    targets: list[tuple[Path, set[str]]] = [
        (
            Path(__file__).resolve().parents[3]
            / "app"
            / "domains"
            / "company_settings"
            / "agents"
            / "company_tool_registry.py",
            {
                "_wrap_save_company_field",
                "_wrap_save_company_section",
                "_wrap_import_workforce_plan",
            },
        ),
        (
            Path(__file__).resolve().parents[3]
            / "app"
            / "domains"
            / "company_settings"
            / "tools"
            / "import_tools.py",
            {
                "save_hiring_policy",
                "import_benefits_from_data",
                "check_company_completeness",
            },
        ),
    ]

    for module_path, required_funcs in targets:
        assert module_path.exists(), f"Arquivo esperado não existe: {module_path}"
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if node.name not in required_funcs:
                continue
            calls: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Name):
                        calls.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.add(func.attr)
            if "audit_company_change" not in calls:
                offenders.append(f"{module_path.name}::{node.name}")
        assert not offenders, (
            "PR4 regressão (bug C4 do audit T1-T6 reaberto): as funções "
            f"abaixo NÃO chamam `audit_company_change`: {offenders}. "
            "Sem o wrapper canônico, mutações de company_settings ficam "
            "invisíveis ao audit trail SOX/ISO 27001 / EU AI Act "
            "(viola Inegociável #6)."
        )

    # Defesa adicional: o anti-padrão fire-and-forget
    # `loop.create_task(coro)` (em try/except:pass) NÃO pode mais
    # aparecer em import_tools.py — era exatamente o que o PR4 removeu.
    legacy_pattern = re.compile(r"loop\.create_task\(\s*coro\s*\)")
    import_tools_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "domains" / "company_settings" / "tools" / "import_tools.py"
    )
    src = import_tools_path.read_text(encoding="utf-8")
    assert not legacy_pattern.search(src), (
        "PR4 regressão: padrão fire-and-forget `loop.create_task(coro)` "
        "reapareceu em import_tools.py. O wrapper canônico é fail-CLOSED — "
        "audit deve ser awaited, não disparado e esquecido."
    )


def test_pr4_bypass_flag_registered_in_main_and_health():
    """PR4 (Task #1004) — paridade R-007: a flag
    ``LIA_DISABLE_COMPANY_AUDIT`` precisa estar registrada nos DOIS
    inventários (startup logger em ``app/main.py`` e endpoint
    ``/health/compliance/bypass-status`` em ``app/api/v1/system_health.py``)
    para o canary on-call detectar quando alguém esquecer ela ON em prod.
    """
    base = Path(__file__).resolve().parents[3] / "app"
    main_src = (base / "main.py").read_text(encoding="utf-8")
    health_src = (base / "api" / "v1" / "system_health.py").read_text(encoding="utf-8")
    flag = "LIA_DISABLE_COMPANY_AUDIT"
    assert flag in main_src, (
        f"PR4 regressão: {flag} não está em app/main.py::_BYPASS_FLAGS — "
        "startup logger não vai alertar CRITICAL quando ON."
    )
    assert flag in health_src, (
        f"PR4 regressão: {flag} não está em app/api/v1/system_health.py::"
        "_BYPASS_FLAGS_RUNTIME — endpoint /health/compliance/bypass-status "
        "não vai expor a flag pro canary on-call."
    )


# ─── Contrato 8: PR5 (Task #1005) — endurecimento company_settings ────────


def test_pr5_a1_save_company_field_impl_uses_precompiled_queries():
    """PR5 / A1 (Task #1005) — defesa AST: ``_save_company_field_impl``
    NÃO pode mais formatar SQL via f-string com ``{field}``. As queries
    são pré-compostas em tempo de import e indexadas por whitelist.
    Se um futuro PR voltar a interpolar `field` em runtime, a superfície
    de SQLi reabre — este teste quebra antes do merge.
    """
    import ast

    module_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "domains" / "company_settings"
        / "agents" / "company_tool_registry.py"
    )
    src = module_path.read_text(encoding="utf-8")

    # Nenhuma f-string SQL contendo `{field}` em runtime. Mensagens de
    # log/erro como f"Dado salvo: {section}.{field}" são inofensivas;
    # o que reabre SQLi é interpolar `{field}` em SELECT/UPDATE/INSERT.
    # As queries SQL pré-compostas usam `{f}` em `_build_*_queries`
    # (tempo de import, varrendo a frozenset whitelisted).
    forbidden = re.compile(
        r"f\"[^\"]*(?:SELECT|UPDATE|INSERT|DELETE|FROM|WHERE)[^\"]*\{field\}[^\"]*\"",
        re.IGNORECASE,
    )
    matches = forbidden.findall(src)
    assert not matches, (
        "PR5 / A1 regressão: `_save_company_field_impl` (ou outra função "
        "do registry) voltou a interpolar `{field}` em f-string SQL: "
        f"{matches}. Use `_PROFILE_FIELD_QUERIES[field]` / "
        "`_CULTURE_FIELD_QUERIES[field]` (queries pré-compostas em tempo "
        "de import)."
    )

    # Defesa positiva: as estruturas pré-compostas existem.
    tree = ast.parse(src)
    module_assigns: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    module_assigns.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            module_assigns.add(node.target.id)
    # `_PROFILE_FIELD_QUERIES = _build_profile_queries()` etc.
    for required in ("_PROFILE_FIELD_QUERIES", "_CULTURE_FIELD_QUERIES"):
        assert required in module_assigns, (
            f"PR5 / A1 regressão: variável `{required}` removida do "
            "company_tool_registry — A1 não pode operar sem a tabela "
            "pré-compilada de queries."
        )


def test_pr5_a2_fast_router_routes_prefill_section_tag():
    """PR5 / A2 (Task #1005) — sentinela contra regressão do roteamento
    determinístico. A tag `[ACTION:prefill_section][target_section:<key>]`
    enviada pelo chat lateral de Configurações DEVE rotear para
    `company_settings` no FastRouter (sem cair na cascata LLM).

    Trava 2 contratos:
      1. YAML `domain_routing.yaml` lista o pattern em `company_settings`.
      2. `_HARDCODED_DOMAIN_PATTERNS` (fallback se YAML indisponível) também.
    """
    yaml_path = (
        Path(__file__).resolve().parents[3]
        / "app" / "orchestrator" / "config" / "domain_routing.yaml"
    )
    yaml_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    company_patterns = yaml_data.get("domains", {}).get("company_settings", [])
    expected_pattern_substr = "prefill_section"
    assert any(expected_pattern_substr in p for p in company_patterns), (
        "PR5 / A2 regressão: pattern `prefill_section` removido de "
        "`company_settings` em domain_routing.yaml — chat lateral de "
        "Configurações volta a depender da cascata LLM (latência + "
        "ambiguidade)."
    )

    # Hardcoded fallback (defense in depth).
    from app.orchestrator.routing import fast_router as fr_mod

    hardcoded = fr_mod._HARDCODED_DOMAIN_PATTERNS.get("company_settings", [])
    assert any("prefill_section" in p for p in hardcoded), (
        "PR5 / A2 regressão: fallback hardcoded em "
        "`_HARDCODED_DOMAIN_PATTERNS['company_settings']` perdeu o "
        "pattern `prefill_section`. Se LIA_DISABLE_YAML_ROUTING=1 ou o "
        "YAML sumir, o roteamento determinístico cai."
    )

    # Fim-a-fim: instancia FastRouter e confirma que uma mensagem com a
    # tag estruturada é classificada como `company_settings`.
    fr = fr_mod.FastRouter()
    sample = "[ACTION:prefill_section][target_section:basic] preencher dados básicos"
    matches = []
    for domain_id, patterns in fr_mod._COMPILED_PATTERNS.items():
        for pat in patterns:
            if pat.search(sample.lower()):
                matches.append(domain_id)
                break
    assert "company_settings" in matches, (
        f"PR5 / A2 regressão: FastRouter não casa a tag estruturada com "
        f"`company_settings`. Matches reais: {matches}."
    )


def test_pr5_a6_confidence_gate_wired_in_three_save_tools():
    """PR5 / A6 (Task #1005) — defesa AST contra regressão do gate de
    ConfidencePolicy. As 3 wrappers de save em `company_settings` DEVEM
    consultar `_check_confidence_gate` antes de mutar estado.

    Cobertura:
      - `_wrap_save_company_field` (registry.py)
      - `_wrap_save_company_section` (registry.py)
      - `save_hiring_policy` (canônico em import_tools.py — ambos os
        wrappers convergem aqui)

    Se um futuro PR remover qualquer chamada, este teste quebra antes
    do merge — auto-saves voltam a passar sem checar threshold.
    """
    import ast

    targets: list[tuple[Path, set[str]]] = [
        (
            Path(__file__).resolve().parents[3]
            / "app" / "domains" / "company_settings"
            / "agents" / "company_tool_registry.py",
            {"_wrap_save_company_field", "_wrap_save_company_section"},
        ),
        (
            Path(__file__).resolve().parents[3]
            / "app" / "domains" / "company_settings"
            / "tools" / "import_tools.py",
            {"save_hiring_policy"},
        ),
    ]

    offenders: list[str] = []
    for module_path, required_funcs in targets:
        assert module_path.exists(), f"Arquivo esperado não existe: {module_path}"
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if node.name not in required_funcs:
                continue
            calls: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Name):
                        calls.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        calls.add(func.attr)
            if "_check_confidence_gate" not in calls:
                offenders.append(f"{module_path.name}::{node.name}")

    assert not offenders, (
        "PR5 / A6 regressão: as funções abaixo NÃO consultam "
        f"`_check_confidence_gate`: {offenders}. Sem o gate, callers "
        "auto-save (autonomous_intent=True) podem persistir mesmo com "
        "confidence abaixo de 0.70 (APPLY_NOTIFY)."
    )


def test_pr5_a6_confidence_gate_helper_blocks_low_confidence():
    """PR5 / A6 (Task #1005) — comportamento do helper `_check_confidence_gate`.

    Contrato:
      - Sem `autonomous_intent`: passa (HITL convencional).
      - `autonomous_intent=True` sem `confidence`: bloqueia (fail-CLOSED).
      - `confidence` >= 0.70 (APPLY_NOTIFY): passa.
      - `confidence` < 0.70: bloqueia com `requires_human_approval=True`.

    Cobre as DUAS cópias do helper (registry + import_tools) — devem ter
    comportamento idêntico (defense in depth + simetria de contrato).
    """
    from app.domains.company_settings.agents import (
        company_tool_registry as reg,
    )
    from app.domains.company_settings.tools import import_tools as it

    for helper, label in (
        (reg._check_confidence_gate, "registry"),
        (it._check_confidence_gate, "import_tools"),
    ):
        # 1. HITL convencional → passa (None)
        assert helper({}) is None, f"{label}: HITL sem autonomous_intent deve passar"

        # 2. Autonomous sem confidence → bloqueia
        blocked = helper({"autonomous_intent": True})
        assert blocked is not None and blocked["success"] is False, (
            f"{label}: autonomous_intent sem confidence deve bloquear"
        )
        assert blocked["reason"] == "confidence_missing"
        assert blocked["requires_human_approval"] is True

        # 3. Confidence alto → passa
        assert helper({"autonomous_intent": True, "confidence": 0.92}) is None, (
            f"{label}: confidence >= 0.70 deve passar"
        )
        assert helper({"autonomous_intent": True, "confidence": 0.71}) is None, (
            f"{label}: confidence apenas acima do threshold deve passar"
        )

        # 4. Confidence baixo → bloqueia
        low = helper({"autonomous_intent": True, "confidence": 0.30})
        assert low is not None and low["success"] is False, (
            f"{label}: confidence baixo deve bloquear"
        )
        assert low["reason"] == "low_confidence"
        assert low["requires_human_approval"] is True

        # 5. Confidence inválido → bloqueia
        invalid = helper({"autonomous_intent": True, "confidence": "talvez"})
        assert invalid is not None and invalid["reason"] == "confidence_invalid"


# ─── Contrato 7 (PR8 / Task #1008): backlog técnico M1/M2/M5/B1/B2 ───────
#
# Manifesto canônico de fechamento PR8 — visível no diff para revisores.
# Cada um dos 10 findings (M1-M6 + B1-B4) do audit T1-T6 tem decisão
# explícita: DONE (sentinela neste arquivo), JÁ COBERTO (PR anterior) ou
# DEFERRED (com justificativa: out-of-scope ou follow-up dedicado).
#
# DETALHE FORMAL: `.local/audit-T1-T6-configuracoes.md` §8.
#
PR8_AUDIT_FINDING_DECISIONS: dict[str, str] = {
    "M1": "DONE: hardcoded backend URL removido; sentinela m1.",
    "M2": "DONE: failed_fields[] surfaced; sentinela m2.",
    "M3": "DEFERRED: unit tests dedicados — follow-up task.",
    "M4": "DONE_PRIOR: coberto por PR3 (FairnessGuard) + PR4 (audit wrapper).",
    "M5": "DONE: magic +20 removido em ambos branches; sentinela m5.",
    "M6": "DEFERRED: hooks frontend fora do domínio company_settings.",
    "B1": "DONE: human_review_required propagado nas 2 rotas; sentinela b1.",
    "B2": "DONE: sentinela b2 trava bloco ethical_validation no prompt.",
    "B3": "DEFERRED: FairnessGuard L3 threshold é refator core, fora de escopo.",
    "B4": "DEFERRED: RAGAS baseline é infra de eval, fora de escopo.",
}


def test_pr8_audit_findings_have_explicit_decision_per_id():
    """Trava-PR canônico: o manifesto PR8 deve cobrir TODOS os 10 findings
    (M1-M6 + B1-B4) com decisão explícita. Se um find for adicionado ao
    audit ou um existente perder rastreabilidade, esta sentinela quebra
    antes do merge — força triagem documentada (canonical-fix Fase 0)."""
    expected = {f"M{i}" for i in range(1, 7)} | {f"B{i}" for i in range(1, 5)}
    assert set(PR8_AUDIT_FINDING_DECISIONS.keys()) == expected, (
        "PR8 regressão: manifesto perdeu cobertura de algum finding "
        f"do audit T1-T6. Esperados: {sorted(expected)}; "
        f"presentes: {sorted(PR8_AUDIT_FINDING_DECISIONS.keys())}."
    )
    valid_prefixes = ("DONE", "DONE_PRIOR", "DEFERRED")
    for fid, decision in PR8_AUDIT_FINDING_DECISIONS.items():
        assert decision.startswith(valid_prefixes), (
            f"PR8 regressão: finding {fid} sem decisão canônica "
            f"(deve começar com {valid_prefixes}): {decision!r}"
        )





def test_pr8_m1_analyze_website_no_hardcoded_backend_url():
    """M1 (PR8) — `_wrap_analyze_company_website` não pode mais conter
    o literal `http://127.0.0.1:8001` hardcoded. A URL deve vir de
    `LIA_INTERNAL_BACKEND_URL` / `settings.APP_BASE_URL` / fallback
    parametrizado por `API_PORT`. Sentinela estática contra regressão."""
    src = (
        Path(__file__).resolve().parents[3]
        / "app" / "domains" / "company_settings" / "agents"
        / "company_tool_registry.py"
    ).read_text(encoding="utf-8")
    # localizar bloco da função analyze_company_website
    func_idx = src.find("_wrap_analyze_company_website")
    assert func_idx >= 0, "função _wrap_analyze_company_website removida?"
    func_block = src[func_idx:func_idx + 3000]
    assert "http://127.0.0.1:8001" not in func_block, (
        "M1 regressão: URL hardcoded `http://127.0.0.1:8001` voltou em "
        "`_wrap_analyze_company_website`. Use LIA_INTERNAL_BACKEND_URL ou "
        "settings.APP_BASE_URL/API_PORT (PR8 Task #1008)."
    )
    assert "LIA_INTERNAL_BACKEND_URL" in func_block, (
        "M1 regressão: env var `LIA_INTERNAL_BACKEND_URL` deixou de ser "
        "consultada — backend URL volta a depender de magic literal."
    )


def test_pr8_m2_save_company_section_returns_failed_fields():
    """M2 (PR8) — `_wrap_save_company_section` agora expõe
    `failed_fields` no payload de retorno. Antes, campos que voltavam
    `success=False` eram descartados silenciosamente (anti-pattern
    canonical-fix #3). Sentinela estática contra regressão."""
    src = (
        Path(__file__).resolve().parents[3]
        / "app" / "domains" / "company_settings" / "agents"
        / "company_tool_registry.py"
    ).read_text(encoding="utf-8")
    func_idx = src.find("_wrap_save_company_section")
    assert func_idx >= 0
    func_block = src[func_idx:func_idx + 5000]
    assert "failed_fields" in func_block, (
        "M2 regressão: `failed_fields` removido de "
        "`_wrap_save_company_section`. Falhas parciais voltam a ser "
        "descartadas silenciosamente — agente confirma 'salvo' ao "
        "recrutador sem ter persistido."
    )


def test_pr8_m5_get_company_profile_no_magic_20():
    """M5 (PR8) — completion total não pode mais usar `+ 20` mágico.
    Substituído por `len(_CULTURE_FIELDS)` (cardinal real da whitelist).
    Sentinela estática contra regressão."""
    src = (
        Path(__file__).resolve().parents[3]
        / "app" / "domains" / "company_settings" / "agents"
        / "company_tool_registry.py"
    ).read_text(encoding="utf-8")
    func_idx = src.find("_wrap_get_company_profile")
    assert func_idx >= 0
    func_block = src[func_idx:func_idx + 4000]
    assert "len(profile_data) + 20" not in func_block, (
        "M5 regressão: `len(profile_data) + 20` (magic number) voltou em "
        "`_wrap_get_company_profile`. Usar `len(_CULTURE_FIELDS)` para o "
        "cardinal canônico da whitelist (PR8 Task #1008)."
    )
    assert "_CULTURE_FIELDS" in func_block, (
        "M5 regressão: `_CULTURE_FIELDS` deixou de dirigir o denominador "
        "de completion — total volta a ser chute fixo."
    )


def test_pr8_b1_import_benefits_marks_human_review_required():
    """B1 (PR8) — `import_benefits_from_data` muta config corporativa
    sugerida pela IA → EU AI Act Art. 14 exige `human_review_required=True`
    no audit log. Sentinela estática garante que o flag continua sendo
    passado ao wrapper `audit_company_change`."""
    src = (
        Path(__file__).resolve().parents[3]
        / "app" / "domains" / "company_settings" / "tools"
        / "import_tools.py"
    ).read_text(encoding="utf-8")
    # achar bloco "async def import_benefits_from_data"
    func_idx = src.find("async def import_benefits_from_data")
    assert func_idx >= 0
    # avançar até o `audit_company_change(` mais próximo
    audit_idx = src.find("audit_company_change(", func_idx)
    assert audit_idx >= 0, (
        "B1 regressão: `audit_company_change` removido de "
        "`import_benefits_from_data` — wrapper canônico SOX/EU AI Act perdido."
    )
    # bloco do CM até `) as _audit:`
    end_idx = src.find(") as _audit:", audit_idx)
    audit_block = src[audit_idx:end_idx]
    assert re.search(
        r"human_review_required\s*=\s*True", audit_block
    ), (
        "B1 regressão: `human_review_required=True` removido do callsite "
        "`audit_company_change` em `import_benefits_from_data`. EU AI Act "
        "Art. 14 violado — audit log volta a marcar False (PR8 Task #1008)."
    )

    # B1 deep-fix (code review #1): o flag precisa ser propagado AMBAS as
    # rotas de emissão do _AuditCtx — _emit_independent (intent + exception
    # + read outcome) E _emit_in_session (write outcome atômico). A primeira
    # iteração do PR8 só threadava em _emit_independent; o outcome row do
    # write commit (rota dominante para writes) ainda hardcodava False,
    # furando o flag silenciosamente. Esta sentinela trava AMBAS.
    audit_dec_src = (
        Path(__file__).resolve().parents[3]
        / "app" / "shared" / "compliance" / "audit_decorators.py"
    ).read_text(encoding="utf-8")
    for fn_name in ("_emit_independent", "_emit_in_session"):
        fn_idx = audit_dec_src.find(f"async def {fn_name}")
        assert fn_idx >= 0, f"B1 regressão: função `{fn_name}` removida."
        # bloco até a próxima def ou fim
        next_def = audit_dec_src.find("\n    async def ", fn_idx + 1)
        if next_def < 0:
            next_def = audit_dec_src.find("\n    def ", fn_idx + 1)
        if next_def < 0:
            next_def = len(audit_dec_src)
        fn_block = audit_dec_src[fn_idx:next_def]
        assert "human_review_required=self.human_review_required" in fn_block, (
            f"B1 regressão (deep): `{fn_name}` voltou a hardcodar "
            "`human_review_required=False` em vez de propagar "
            "`self.human_review_required`. Outcome row de "
            "import_benefits_from_data passa a marcar False mesmo com "
            "o callsite passando True — EU AI Act Art. 14 furado."
        )
        assert "human_review_required=False" not in fn_block, (
            f"B1 regressão (deep): literal `human_review_required=False` "
            f"voltou em `{fn_name}` — flag do callsite é ignorado."
        )


def test_pr8_b2_ethical_validation_block_reaches_rendered_prompt():
    """B2 (PR8) — o bloco `ethical_validation` do YAML existe (linha 74)
    e é carregado em `COMPANY_ETHICAL_VALIDATION`, mas precisa chegar ao
    prompt renderizado por `get_company_system_prompt()`. Antes do PR8
    o wiring estava implícito (sem sentinela). Esta sentinela trava o
    contrato: se algum PR futuro remover o bloco `=== VALIDACAO ETICA ===`
    do template, o teste quebra antes do merge."""
    rendered = get_company_system_prompt()
    assert "VALIDACAO ETICA" in rendered or "ethical_validation" in rendered, (
        "B2 regressão: bloco `=== VALIDACAO ETICA ===` removido de "
        "`get_company_system_prompt()` — `ethical_validation` do YAML vira "
        "letra morta (PR8 Task #1008)."
    )
    # marcadores canônicos do bloco YAML (linhas 74-87): se o bloco existir
    # mas estiver vazio, este check pega.
    required_markers = [
        "discriminat",  # "discriminatórios"
        "inclusiv",     # "alternativas inclusivas"
    ]
    for marker in required_markers:
        assert marker in rendered.lower(), (
            f"B2 regressão: marcador `{marker}` ausente do prompt renderizado "
            "— bloco `ethical_validation` do YAML não está mais sendo "
            "injetado em `get_company_system_prompt()`."
        )
