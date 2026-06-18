"""TDD: wizard system prompt must mandate seniority confirmation for inferred fields.

Testa que o YAML canônico contém a regra de confirmar inferências antes de
avançar para campos faltantes (Fix P1 seniority inference confirmation).
"""
import pytest
from app.shared.prompts.loader import PromptLoader


def test_job_management_yaml_confirms_inferred_seniority():
    """YAML deve conter instrução para confirmar senioridade inferida do título."""
    data = PromptLoader.load("domains/job_management")
    system_prompt = data.get("system_prompt", "")
    behavioral_rules = data.get("behavioral_rules", [])
    
    # Instrução de confirmar inferência deve estar em system_prompt OU behavioral_rules
    combined = system_prompt + " ".join(str(r) for r in behavioral_rules)
    
    assert "inferid" in combined.lower() or "inferên" in combined.lower() or "infer" in combined.lower(),         "YAML deve mencionar confirmação de campos inferidos automaticamente"
    
    assert "seniori" in combined.lower(),         "YAML deve especificamente mencionar senioridade inferida"
    
    assert "confirm" in combined.lower() or "confirme" in combined.lower(),         "YAML deve incluir instrução de confirmação antes de avançar"


def test_job_management_yaml_confirmation_precedes_missing_fields():
    """Instrução de confirmar inferência deve ser explícita sobre ordem — antes de outros campos."""
    data = PromptLoader.load("domains/job_management")
    system_prompt = data.get("system_prompt", "")
    behavioral_rules = data.get("behavioral_rules", [])
    
    combined = system_prompt + " ".join(str(r) for r in behavioral_rules)
    
    # Deve mencionar confirmar ANTES de perguntar outros campos
    has_order_hint = (
        "antes de perguntar" in combined.lower()
        or "antes de pedir" in combined.lower()
        or "antes de avançar" in combined.lower()
        or "próxima resposta" in combined.lower()
    )
    assert has_order_hint,         "YAML deve indicar que confirmação de inferência vem ANTES de outros campos"
