"""Interview Scheduling System Prompts.

INTERVIEW_FEW_SHOT_EXAMPLES is a hardcoded string with 8 **Cenário blocks
used both by get_extraction_prompt() and directly by tests.
Content is purposely kept inline (not YAML) so tests can assert structure.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from app.shared.prompts.interaction_patterns import NEGATION_DETECTION_BLOCK
except ImportError:
    NEGATION_DETECTION_BLOCK = (
        "Padrões de negação: não quero, cancela, desisto, não tenho interesse."
    )

# ---------------------------------------------------------------------------
# Base extraction prompt (loaded from YAML when available; fallback inline)
# ---------------------------------------------------------------------------

def _load_base_prompt() -> str:
    try:
        from app.shared.prompts.loader import PromptLoader
        data = PromptLoader.load("domains/interview_scheduling")
        p = data.get("system_prompt", "")
        if isinstance(p, str) and len(p) > 20:
            return p
    except Exception:
        pass
    return (
        "Você é um especialista em agendamento de entrevistas. "
        "Extraia as informações necessárias da mensagem do candidato. "
        "Responda SOMENTE com JSON válido."
    )


INTERVIEW_EXTRACTION_PROMPT: str = _load_base_prompt()

# ---------------------------------------------------------------------------
# Few-shot examples — 8 cenários canônicos
# ---------------------------------------------------------------------------

INTERVIEW_FEW_SHOT_EXAMPLES: str = """**Cenário 1 — Confirmação direta**
Usuário: "Pode ser na quinta-feira às 10h"
<thought>Candidato confirmou data (quinta) e hora (10h). Extrair diretamente.</thought>
{"preferred_date": "quinta-feira", "preferred_time": "10:00"}

**Cenário 2 — Mensagem parcial (só data)**
Usuário: "Prefiro na sexta"
<thought>Mensagem parcial: só informou data, horário ausente. Não inventar hora.</thought>
{"preferred_date": "sexta-feira", "preferred_time": null}

**Cenário 3 — Mensagem parcial (só hora)**
Usuário: "Às 15h tá bom"
<thought>Mensagem parcial: só informou horário, data ausente. Campo preferred_date fica null.</thought>
{"preferred_date": null, "preferred_time": "15:00"}

**Cenário 4 — Data relativa**
Usuário: "Amanhã de manhã"
<thought>Data relativa ("amanhã") e período aproximado ("manhã"). Registrar como recebido.</thought>
{"preferred_date": "amanhã", "preferred_time": "manhã"}

**Cenário 5 — Múltiplas opções**
Usuário: "Posso na terça ou quarta, qualquer horário"
<thought>Candidato ofereceu duas datas alternativas. Usar a primeira como principal.</thought>
{"preferred_date": "terça-feira", "preferred_time": "qualquer horário"}

**Cenário 6 — E-mail do candidato**
Usuário: "Meu e-mail é joao.silva@empresa.com"
<thought>Candidato forneceu e-mail explicitamente. Extrair campo candidate_email.</thought>
{"candidate_email": "joao.silva@empresa.com"}

**Cenário 7 — Reagendamento**
Usuário: "Preciso remarcar, o horário mudou para às 16h"
<thought>Candidato quer alterar horário existente. Atualizar preferred_time.</thought>
{"preferred_time": "16:00", "reschedule": true}

**Cenário 8 — Negação / cancelamento**
Usuário: "Não tenho mais interesse, pode cancelar"
<thought>Negação explícita. Candidato desistiu — sinalizar cancelamento.</thought>
{"intent": "cancel", "candidate_withdrew": true}"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_extraction_prompt(
    last_message: str,
    current_state: str,
    next_pending_field: str,
) -> str:
    """Retorna o prompt de extração formatado com contexto atual.

    Embeds last_message and next_pending_field explicitly so callers
    (and tests) can assert their presence in the returned string.
    """
    pending = next_pending_field if next_pending_field else "nenhum (todos coletados)"
    context_block = (
        f"Mensagem atual do candidato: {last_message}\n"
        f"Estado de coleta atual: {current_state}\n"
        f"Próximo campo a coletar: {pending}"
    )
    return (
        f"{INTERVIEW_EXTRACTION_PROMPT}\n\n"
        f"{context_block}\n\n"
        f"{INTERVIEW_FEW_SHOT_EXAMPLES}\n\n"
        f"{NEGATION_DETECTION_BLOCK}"
    )
