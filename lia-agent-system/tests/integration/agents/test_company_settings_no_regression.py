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
    )
    for name in required_global_callables:
        assert hasattr(import_tools, name) and callable(
            getattr(import_tools, name)
        ), (
            f"Tool global '{name}' citada no `structured_action_tags` "
            "do YAML não está mais exportada por "
            "app/domains/company_settings/tools/import_tools.py."
        )


# ─── Contrato 5: golden dataset T6 existe e tem 18 cenários ───────────────


def test_golden_dataset_exists_with_18_scenarios():
    """Golden dataset T6 (#993): 18 cenários = 6 seções × 3 contratos
    (positivo, anti-padrão, fairness). Roda via
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
    assert len(rows) == 18, (
        f"Golden dataset T6 deve ter 18 cenários (6 seções × 3 contratos), "
        f"encontrado {len(rows)}."
    )

    sections = {"culture", "tech_stack", "benefits", "workforce", "policy", "compensation"}
    contracts = ("positive", "anti-pattern", "fairness")
    seen: set[tuple[str, str]] = set()
    for r in rows:
        cid = r["id"]  # ex: CSP-culture-positive, CSP-tech_stack-anti-pattern
        assert cid.startswith("CSP-"), f"id fora do padrão CSP-*: {cid}"
        body = cid[len("CSP-"):]
        # contract pode conter hífen ('anti-pattern') — match por sufixo,
        # não por rsplit('-', 1).
        match = next(
            ((s, c) for c in contracts for s in sections if body == f"{s}-{c}"),
            None,
        )
        assert match is not None, f"id mal formado (esperado CSP-<section>-<contract>): {cid}"
        section, contract = match
        seen.add((section, contract))
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
        f"Golden dataset T6 incompleto — faltam combinações: {sorted(missing)}"
    )
