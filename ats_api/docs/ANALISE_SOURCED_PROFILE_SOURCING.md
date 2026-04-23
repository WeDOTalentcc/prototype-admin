# Análise: melhorias no domínio sourced_profile_sourcing

Baseado nas estatísticas de falhas (ChatAnalyzer) e conversas de usuários (Anderson, Gustavo e outros).

---

## Problemas identificados

### 1. "Essa lista" / "essa pesquisa" → IA pede clarificação
**Causa:** O usuário está dentro de um workspace com sourcing, mas o LLM não entende que "essa lista", "quantos candidatos tem nessa lista?" = sourcing atual. O `count_candidates` não tinha "lista" nos triggers.

**Solução implementada:**
- Triggers de `count_candidates` ampliados: `essa lista`, `nessa lista`, `dessa lista`, `nessa busca`, `essa busca`, `quantos candidatos`, `quantas pessoas`
- `CORE_RULES` reforçadas: "Essa lista, essa pesquisa, nessa busca = sourcing atual. NUNCA peça clarificação para saber de qual lista."

### 2. "Relatório geral" / "estatísticas" / "dados demográficos" → IA nega ou pede clarificação
**Causa:** `summarize_search` não cobria bem essas variações.

**Solução implementada:**
- Triggers de `summarize_search`: `relatorio geral`, `dados e estatist`, `estatistica`, `relatorio de estatist`, `dessa pesquisa`, `dessa lista`
- Novos exemplos: "Me mostra um relatório de estatísticas", "Me mostra os dados e estatísticas"

### 3. "Qual a formação dos top 10?" → Pediu clarificação
**Causa:** `education_distribution` existia mas não estava bem mapeada no prompt.

**Solução implementada:**
- Regra explícita em `CORE_RULES`: "Qual a formação dos top 10? → education_distribution (source=aggregated)"

### 4. "Distribuição por gênero" / "existe separação por gênero?"
**Solução implementada:**
- Triggers de `gender_distribution`: `separação por gênero`, `genero`, `sexo`
- Exemplo: "Existe separação por gênero?" → `gender_distribution`

### 5. "Pontos fortes em comum" / "skills mais comuns"
**Solução implementada:**
- Regras explícitas: `common_strengths` e `analyze_skills` (source=aggregated)

### 6. Memória conversacional não persiste entre mensagens
**Causa:** Cada request recebe `ConversationMemory()` vazia. O Rails armazena mensagens, mas o Python não recebe nem restaura o estado da conversa.

**Solução implementada:**
- Suporte a `conversation_memory` em `context_data`: se o Rails enviar `conversation_memory` (dict serializado) em `context_data`, o orchestrator restaura via `ConversationMemory.from_dict()`.

**O que o Rails precisa fazer:**
1. Persistir o `conversation_memory` retornado no metadata da resposta (quando implementado)
2. Enviar `context_data.conversation_memory` na próxima mensagem do mesmo (user_id, workspace_id, sourcing_id)

### 7. "Exatamente isso!" / confirmações → IA não entende
**Causa:** Sem histórico de mensagens, a IA não sabe a que "isso" se refere.

**Depende de:** Rails enviar as últimas N mensagens em `context_data` (ex.: `recent_messages`) ou o `conversation_memory` com contexto suficiente. O suporte a `conversation_memory` está pronto; falta o Rails popular e devolver.

### 8. sourcing_id inconsistente
**Causa possível:** Em alguns workspaces o Rails não envia `sourcing_id` (ou envia vazio).

**Recomendação:** Garantir que o Rails **sempre** envie `sourcing_id` quando o usuário está em um workspace vinculado a um sourcing. O agent valida e retorna erro se não houver.

---

## Alterações de código

| Arquivo | Alteração |
|---------|-----------|
| `prompt_builder/actions.py` | Triggers e exemplos para `count_candidates`, `summarize_search`, `gender_distribution` |
| `prompt_builder/dynamic_builder.py` | CORE_RULES reforçadas (contexto de sourcing, formação top 10, etc.) |
| `orchestrator.py` | Restore de `conversation_memory` a partir de `context_data` |

---

## Fluxo atual (DomainWorkflow)

O domínio usa **DomainWorkflow** (LangGraph), não o MultiAgentOrchestrator:

1. **DomainIntentAgent** → `domain.process_intent()` → LLM mapeia query → `action_id` + params
2. **DomainExecutorAgent** → `domain.execute_action(action_id, params, context)`
3. **DomainResponseBuilder** → formata a resposta

O `ConversationMemory` é usado pelo **MultiAgentOrchestrator** (RouterAgent), que hoje **não** é o caminho principal para sourced_profile_sourcing. O restore de memory em `_build_context` já prepara o uso futuro.

---

## Backlog sugerido (fora do escopo desta análise)

- Filtrar por situação profissional (sem empresa atual, desempregado) – depende da API
- Filtrar por data de finalização da última oportunidade – depende da API
- Melhorar classificação dos "Indefinidos" (85 msgs sem action_id) – ex.: heurística por conteúdo ("❌", "Desculpe" = falha)
