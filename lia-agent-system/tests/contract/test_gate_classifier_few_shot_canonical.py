"""Sensor canonical Fix E (2026-05-27) -- gate_classifier.yaml DEVE conter
few-shot examples ancorando aprovações curtas + regra de ouro #9 que mensagens
curtas raramente são `provide_new_content`.

Audit context (WIZARD_DEEP_DIVE_2026-05-27_POST_PR18 P0-NOVO-#1 + Fix E):
  Bug histórico: classifier ocasionalmente confundia aprovações curtas
  ("ok", "sim", "pode seguir") com `provide_new_content` em ~5% dos casos,
  disparando cascade indevido (zerar jd_enriched + derivados) e gerando loop
  "me passa a JD". O Fix A (commit e88bf23176) renomeou variavel `msg` evitando
  TypeError; o Fix #3 do `f8043593d` (sanity check <150 chars) mitigou o sintoma;
  o Fix E ataca a CAUSA RAIZ com few-shot examples + regra explícita.

  Sensor protege regressão: se algum dev/agent remover esses exemplos canonical
  ou a regra de ouro #9 no futuro, sensor falha em CI antes do commit landar.

Guards (estruturais -- regex/load sobre YAML canonical):
  1. YAML carrega via yaml.safe_load sem erro.
  2. metadata.version >= "1.0".
  3. system_prompt contém regra de ouro #9 (short-msg rule).
  4. system_prompt contém TODOS os 6 exemplos canonical (ok, sim, pode seguir,
     tá bom, "vamos seguir adiante", "preciso te repassar a JD primeiro").
  5. Exemplos canonical estão mapeados pra intents corretos (approve OR
     ask_question, nunca provide_new_content).

Run standalone:
    python -m pytest lia-agent-system/tests/contract/test_gate_classifier_few_shot_canonical.py -v
"""
from pathlib import Path

import pytest
import yaml


YAML_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "prompts"
    / "job_creation"
    / "gate_classifier.yaml"
)


@pytest.fixture(scope="module")
def yaml_doc():
    return yaml.safe_load(YAML_PATH.read_text())


@pytest.fixture(scope="module")
def system_prompt(yaml_doc):
    sp = yaml_doc.get("system_prompt", "")
    assert isinstance(sp, str) and sp, "system_prompt deve ser string nao-vazia"
    return sp


def test_guard_1_yaml_loads_clean(yaml_doc):
    """Guard 1: YAML carrega sem erro de sintaxe."""
    assert yaml_doc is not None
    assert isinstance(yaml_doc, dict)
    assert "system_prompt" in yaml_doc


def test_guard_2_metadata_version(yaml_doc):
    """Guard 2: metadata.version presente e nao-trivial."""
    metadata = yaml_doc.get("metadata", {})
    assert metadata.get("version"), "metadata.version obrigatorio"
    assert yaml_doc.get("version"), "version top-level obrigatorio"


def test_guard_3_rule_9_short_msg_present(system_prompt):
    """Guard 3: Regra de ouro #9 'Mensagens curtas raramente sao provide_new_content'."""
    assert "9." in system_prompt, "Regra #9 deve estar enumerada"
    assert (
        "curtas" in system_prompt.lower()
        and "provide_new_content" in system_prompt
        and "150 chars" in system_prompt
    ), (
        "Fix E: regra de ouro #9 deve mencionar mensagens curtas, threshold "
        "150 chars, e o intent provide_new_content. Ver gate_classifier.yaml "
        "linha ~85."
    )


# Cada tupla: (snippet canonical do exemplo, intent esperado no mesmo bloco)
CANONICAL_EXAMPLES = [
    ('"ok" → intent=approve', "approve"),
    ('"sim" → intent=approve', "approve"),
    ('"pode seguir" → intent=approve', "approve"),
    ('"tá bom" → intent=approve', "approve"),
    ("vamos seguir adiante com isso aqui", "approve"),
    ("preciso te repassar a JD primeiro", "ask_question"),
    ("Engenheiro Backend Senior remoto", "ask_question"),
]


@pytest.mark.parametrize("example_snippet,expected_intent", CANONICAL_EXAMPLES)
def test_guard_4_canonical_example_present(system_prompt, example_snippet, expected_intent):
    """Guard 4: cada exemplo canonical Fix E presente no system_prompt + mapeado
    pro intent correto (approve ou ask_question, NUNCA provide_new_content)."""
    assert example_snippet in system_prompt, (
        f"Fix E: exemplo canonical {example_snippet!r} ausente do system_prompt. "
        "Esses exemplos ancoram o classifier contra confusão de aprovações curtas "
        "com provide_new_content. Restaurar via gate_classifier.yaml."
    )
    # Confirma que o intent esperado aparece próximo do snippet
    idx = system_prompt.find(example_snippet)
    block = system_prompt[idx : idx + 250]
    assert expected_intent in block, (
        f"Fix E: exemplo {example_snippet!r} deve estar mapeado pro intent "
        f"{expected_intent!r} no bloco de exemplos. Bloco encontrado: {block[:120]!r}"
    )


def test_guard_5_no_short_msg_mapped_to_provide_new_content(system_prompt):
    """Guard 5: nenhum exemplo curto canonical deve estar mapeado pra
    provide_new_content (sinal de regressão direta do bug raiz)."""
    # Para cada exemplo curto, garante que provide_new_content NÃO aparece
    # no bloco de 250 chars após o snippet.
    short_examples = [
        '"ok" →',
        '"sim" →',
        '"pode seguir" →',
        '"tá bom" →',
    ]
    for snippet in short_examples:
        if snippet in system_prompt:
            idx = system_prompt.find(snippet)
            block = system_prompt[idx : idx + 200]
            assert "provide_new_content" not in block, (
                f"Fix E REGRESSAO: exemplo curto {snippet!r} mapeado pra "
                f"provide_new_content no system_prompt. Isso eh exatamente o "
                f"bug que o Fix E veio prevenir. Reverter a mudanca."
            )
