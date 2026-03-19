"""
Interview Scheduling System Prompts — centraliza todos os prompts LLM usados
pelos nós do InterviewGraph.

Por que separar?
- Consistência com o padrão 4-arquivos dos demais domínios
- Testabilidade: prompts podem ser verificados sem executar o grafo
- Manutenção: uma única fonte de verdade para ajuste de linguagem/CoT
"""
from app.shared.prompts.interaction_patterns import ANTI_SYCOPHANCY_BLOCK, NEGATION_DETECTION_BLOCK


# ---------------------------------------------------------------------------
# Prompt de extração de campos (usado em interview_details_collector)
# ---------------------------------------------------------------------------

INTERVIEW_EXTRACTION_PROMPT = """\
Extraia informações de agendamento de entrevista da mensagem do usuário.

<thought>
1. O que o usuário mencionou explicitamente sobre a entrevista?
2. Quais campos posso inferir com segurança? Quais estão ausentes?
3. Não inventar dados — retornar apenas o que foi mencionado.
4. Normalizar formatos: datas para YYYY-MM-DD, horários para HH:MM ou token.
</thought>

MENSAGEM DO USUÁRIO:
{last_message}

CAMPOS JÁ COLETADOS:
{current_state}

PRÓXIMO CAMPO PENDENTE:
{next_pending_field}

Retorne um objeto JSON com APENAS os campos mencionados na mensagem:
{{
    "candidate_name": "...",
    "candidate_email": "...",
    "job_title": "...",
    "interview_type": "tecnica|comportamental|cultural|rh|gerencial",
    "interviewer_email": "...",
    "preferred_date": "YYYY-MM-DD",
    "preferred_time": "HH:MM ou manhã|tarde|noite",
    "duration_minutes": 60,
    "interview_mode": "presencial|remoto|hibrido",
    "notes": "..."
}}

RETORNE APENAS OS CAMPOS MENCIONADOS. Se nenhum campo novo foi informado, retorne {{}}.
"""

# ---------------------------------------------------------------------------
# Exemplos few-shot para o coletor de campos
# ---------------------------------------------------------------------------

INTERVIEW_FEW_SHOT_EXAMPLES = """
## Exemplos de Extração

**Cenário 1: Mensagem completa**
Usuário: "Agenda entrevista técnica com João Silva (joao@email.com) para a vaga de Backend Sênior,
terça às 14h com duracao de 1 hora, remoto"
<thought>
1. Candidato: João Silva / joao@email.com
2. Tipo: técnica, vaga: Backend Sênior
3. Data: próxima terça → deixar para o sistema resolver; horário: 14:00
4. Modo: remoto, duração: 60 min
</thought>
Retorno: {"candidate_name": "João Silva", "candidate_email": "joao@email.com",
"job_title": "Backend Sênior", "interview_type": "tecnica", "preferred_time": "14:00",
"duration_minutes": 60, "interview_mode": "remoto"}

**Cenário 2: Mensagem parcial**
Usuário: "Marca para amanhã de manhã"
<thought>
1. Apenas data/horário parciais mencionados
2. "amanhã" → sistema calculará; "manhã" → token válido
3. Nenhum outro campo foi mencionado — não inferir candidato ou tipo
</thought>
Retorno: {"preferred_time": "manhã"}

**Cenário 3: Negação / cancelamento**
Usuário: "Não, cancela isso e marca para sexta à tarde"
<thought>
1. Negação explícita → ignorar agendamento anterior
2. Nova preferência: sexta, tarde
3. Apenas atualizar preferred_time
</thought>
Retorno: {"preferred_time": "tarde"}

**Cenário 4: Tipo de entrevista ambíguo**
Usuário: "Entrevista com o gestor para cargo de gerente"
<thought>
1. "com o gestor" → tipo gerencial
2. cargo: gerente
3. Sem email, data ou horário — não inventar
</thought>
Retorno: {"interview_type": "gerencial", "job_title": "gerente"}

**Cenário 5: Dado insuficiente**
Usuário: "pode agendar"
<thought>
1. Nenhum campo específico fornecido
2. Retornar objeto vazio — aguardar o coletor perguntar o próximo campo
</thought>
Retorno: {}

**Cenário 6: Múltiplos entrevistadores**
Usuário: "Inclui a Ana (ana@empresa.com) como entrevistadora também"
<thought>
1. Adição de entrevistador extra — campo additional_interviewers
2. email: ana@empresa.com
3. Não alterar interviewer_email principal
</thought>
Retorno: {"additional_interviewers": [{"email": "ana@empresa.com"}]}

**Cenário 7: Reagendamento**
Usuário: "Precisa remarcar, o candidato pediu para semana que vem na quarta"
<thought>
1. Reagendamento → sobrescrever preferred_date
2. "semana que vem na quarta" → sistema calculará
3. Registrar nota de reagendamento
</thought>
Retorno: {"notes": "Reagendado a pedido do candidato"}

**Cenário 8: Entrevista presencial com local**
Usuário: "Entrevista presencial na nossa sede em São Paulo, sala de reunião 3"
<thought>
1. Modo: presencial
2. Local: sede SP, sala 3 → campo location
3. Sem data/hora ainda
</thought>
Retorno: {"interview_mode": "presencial", "location": "Sede São Paulo - Sala de Reunião 3"}
"""

# ---------------------------------------------------------------------------
# Função pública — usada pelos nós do interview_graph
# ---------------------------------------------------------------------------


def get_extraction_prompt(
    last_message: str,
    current_state: str,
    next_pending_field: str,
) -> str:
    """Retorna o prompt de extração formatado com contexto atual."""
    return (
        INTERVIEW_EXTRACTION_PROMPT.format(
            last_message=last_message,
            current_state=current_state,
            next_pending_field=next_pending_field or "nenhum (todos coletados)",
        )
        + "\n\n"
        + INTERVIEW_FEW_SHOT_EXAMPLES
        + "\n\n"
        + NEGATION_DETECTION_BLOCK
    )
