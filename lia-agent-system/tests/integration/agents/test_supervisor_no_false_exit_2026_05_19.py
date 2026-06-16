"""Sentinela offline — supervisor classifier NUNCA pode classificar respostas
curtas sim/não como ``exit_wizard``.

Harness sensor (2026-05-19) criado para travar a regressão observada em
2026-05-19 quando o usuário Paulo respondeu "agora nao" a uma proposta de
navegação ("Posso te levar para o ambiente de vagas?") e o supervisor
classifier (Haiku) classificou erroneamente como ``exit_wizard``, fazendo
o wizard se despedir prematuramente.

Esta sentinela impõe duas invariantes via AST + AST guard, sem depender
de chamada real ao Haiku (LLM-as-judge seria flaky e cara em CI).

1. **AST guard #1:** o system prompt do supervisor classifier DEVE incluir
   a "REGRA CRÍTICA 2" que instrui o LLM a usar ``last_turns`` para
   disambiguar respostas curtas contra ``exit_wizard``.
2. **AST guard #2:** o system prompt DEVE incluir explicitamente
   "agora não" como ANTI-EXEMPLO de ``exit_wizard``.

Sentinela é fail-CLOSED — qualquer regressão no prompt quebra.
"""
from __future__ import annotations

import ast
from pathlib import Path


def _classifier_source() -> str:
    """Read wizard_supervisor_classifier.py from disk (AST-friendly)."""
    here = Path(__file__).resolve()
    repo_root = here.parents[3]  # tests/integration/agents/ -> repo
    fp = repo_root / "app" / "domains" / "job_creation" / "services" / "wizard_supervisor_classifier.py"
    assert fp.exists(), f"wizard_supervisor_classifier.py not found at {fp}"
    return fp.read_text(encoding="utf-8")


def _extract_module_constant(src: str, const_name: str) -> str:
    """Return the value of a top-level string constant from the module text."""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == const_name:
                    # The value can be a Constant or a BinOp string concat —
                    # use unparse + eval for the string-only happy path.
                    seg = ast.get_source_segment(src, node) or ""
                    return seg
    raise AssertionError(f"Constant {const_name!r} not found")


def test_supervisor_prompt_has_regra_critica_2_against_short_yesno():
    """The system prompt MUST teach the LLM to use last_turns to disambiguate
    short yes/no responses against exit_wizard.

    Regression: 2026-05-19 — "agora nao" was classified as exit_wizard,
    making the wizard exit prematurely.
    """
    src = _classifier_source()
    prompt_src = _extract_module_constant(src, "_INLINE_SYSTEM_PROMPT")
    prompt_low = prompt_src.lower()
    # Must mention "regra crítica 2" or equivalent disambiguation rule
    has_regra_2 = (
        "regra crítica 2" in prompt_low
        or "regra critica 2" in prompt_low
        or "disambiguar" in prompt_low
    )
    assert has_regra_2, (
        "Supervisor classifier prompt must include an explicit rule that "
        "teaches the LLM to use last_turns to disambiguate short yes/no "
        "responses (sim, não, agora-não, depois) against exit_wizard. "
        "See regression 2026-05-19 ('agora nao' → false exit_wizard)."
    )


def test_supervisor_prompt_lists_agora_nao_as_anti_example():
    """The prompt MUST explicitly list 'agora não' as an ANTI-EXAMPLE of
    exit_wizard, otherwise Haiku falls into the same trap as 2026-05-19.
    """
    src = _classifier_source()
    prompt_src = _extract_module_constant(src, "_INLINE_SYSTEM_PROMPT")
    prompt_low = prompt_src.lower()
    # The exact anti-example "agora não" must appear in the prompt
    has_anti_example = (
        "agora não" in prompt_low
        or "agora nao" in prompt_low
    )
    assert has_anti_example, (
        "Supervisor classifier prompt must explicitly list 'agora não' "
        "(or 'agora nao') as an ANTI-EXEMPLO of exit_wizard. Without this, "
        "Haiku treats it as 'depois eu faço' (canonical exit example) and "
        "classifies short negations as wizard-exit. See regression 2026-05-19."
    )


def test_supervisor_prompt_anti_examples_block_exists():
    """The prompt MUST have a block listing concrete anti-examples for
    exit_wizard (defense-in-depth — generic 'don't' isn't enough)."""
    src = _classifier_source()
    prompt_src = _extract_module_constant(src, "_INLINE_SYSTEM_PROMPT")
    has_anti_examples = (
        "anti-exemplo" in prompt_src.lower()
        or "anti-example" in prompt_src.lower()
        or "JAMAIS classifique" in prompt_src
        or "NÃO classifique" in prompt_src
    )
    assert has_anti_examples, (
        "Supervisor classifier prompt must include an ANTI-EXEMPLOS block "
        "with concrete patterns of what NOT to classify as exit_wizard. "
        "See regression 2026-05-19."
    )
