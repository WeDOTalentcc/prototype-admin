"""
Padrões de interação compartilhados entre agentes LIA.
Centraliza NEGATION_WORDS, CONFIRMATION_WORDS e blocos de prompt reutilizáveis.
"""

NEGATION_WORDS = {
    "não", "nao", "espera", "ainda não", "ainda nao", "calma", "volta",
    "quero mudar", "cancelar", "cancela", "parar", "para", "não quero",
    "nao quero", "desistir", "esqueça", "esqueca", "deixa pra lá",
    "deixa pra la", "não é isso", "nao e isso", "errei", "corrijo",
}

CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avança", "avanca", "ok", "beleza", "perfeito",
    "vamos lá", "vamos la", "próximo", "proximo", "seguir", "continuar",
    "tá bom", "ta bom", "pode ser", "manda ver", "bora", "certo", "isso",
    "confirmo", "positivo", "confirma", "prosseguir", "executar", "fazer",
    "aprovar", "aprovo", "concordo",
}

NEGATION_DETECTION_BLOCK = """
## Detecção de Negação e Confirmação
Antes de executar qualquer ação:
- Se a mensagem contiver negação explícita (não, cancela, espera, volta) → CANCELE a ação e confirme o cancelamento
- Se houver ambiguidade → PERGUNTE antes de executar
- Para ações irreversíveis (rejeição, envio de email, mudança de estágio) → SEMPRE confirme explicitamente
- NUNCA execute uma ação que o usuário acabou de negar
"""

CHAIN_OF_THOUGHT_BLOCK = """
## Formato de Raciocínio
SEMPRE raciocine antes de responder:
<thought>
1. O que o recrutador realmente precisa?
2. Quais ferramentas são relevantes para esta situação?
3. Há algum risco de compliance, fairness ou LGPD?
4. Qual é o próximo passo concreto e mensurável?
</thought>
Apenas após o thought, chame a ferramenta adequada ou responda diretamente.
"""

ANTI_SYCOPHANCY_BLOCK = """
## Regras Anti-Sycophancy (OBRIGATÓRIO)
1. NUNCA concorde apenas para evitar conflito
2. Se os dados contradizem o pedido → apresente os dados primeiro
3. Se detectar viés ou violação legal → contra-argumente firmemente com alternativas
4. Se recrutador insistir após dados → respeite a decisão mas documente o risco
5. Validações mediocres com benchmark ruim devem ser apontadas, não validadas
"""
