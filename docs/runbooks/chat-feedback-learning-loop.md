# Runbook — Ciclo de feedback → aprendizagem do chat

Trace ponta-a-ponta do ciclo "recrutador avalia a LIA → a LIA aprende → o
comportamento muda", consertado em Task #1297. Antes desta tarefa o ciclo estava
morto: 14.459 mensagens, mas `interaction_feedback` tinha 1 linha vazia e
`learning_patterns` estava vazia.

## Trace ponta-a-ponta (botão → API → banco → aprendizagem → comportamento)

1. **Botão (captura).** O recrutador clica 👍/👎/nota/correção numa resposta da
   LIA. O componente de ação vive em `MessageActions`
   (`plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx`).
   - **Root cause original:** `UnifiedChat.tsx` não passava `conversationId` ao
     `<UnifiedMessageList>`. Sem ele, o guard `if (conversationId)` nos handlers
     nunca era satisfeito → o POST nunca saía, mas o estado otimista mudava
     (fake success). Por isso a tabela ficava vazia apesar dos cliques.
   - **Fix:** `UnifiedChat.tsx` passa `conversationId={chatConversationId}`; os
     handlers (`handleThumbsUp` / `handleThumbsDownClick` / `submitDownDetails`)
     são **fail-loud**: sem `conversationId` mostram `toast.error` e NÃO mudam o
     estado (canonical-fix, proibido silent fallback). Cada envio inclui
     `messageContext: { lia_response: <texto da resposta> }` para o backend
     aprender com a resposta real, não só com o sinal.

2. **API.** `submitThumbsFeedback(sessionId, messageId, thumbs, opts)`
   (`plataforma-lia/src/services/lia-api/feedback-api.ts`) → `POST` para
   `lia-agent-system/app/api/v1/lia_feedback.py`. O `company_id` vem do JWT do
   usuário autenticado (NUNCA do cliente). `record_feedback` resolve o tenant e
   persiste.

3. **Banco.** Uma linha em `interaction_feedback` (tenant + usuário reais), com
   `lia_response`/`user_message` do `message_context`.

4. **Aprendizagem.** `feedback_service._update_patterns_from_feedback`
   (`lia-agent-system/app/domains/analytics/services/feedback_service.py`).
   - **Root cause original:** early-return `if not feedback.intent: return`. Os
     polegares do chat não carregam intent → nenhum padrão era gerado.
   - **Fix:** sem intent/stage, a chave de padrão é `"general"`
     (`_generate_pattern_key`); o padrão é criado/atualizado com exemplos
     bons/ruins por tenant em `learning_patterns`.

5. **Comportamento.** `get_relevant_patterns` + `get_learned_examples_block`
   alimentam o prompt.
   - **Root cause original:** padrões só eram consumidos pelo wizard; e
     `get_relevant_patterns` casava só por intent, ignorando `"general"`.
   - **Fix:** `get_relevant_patterns` SEMPRE inclui padrões `"general"`; o helper
     canônico `build_system_prompt_with_persona`
     (`app/shared/prompts/persona_aware_prompt.py`) busca o bloco (fail-open) e
     o injeta via novo kwarg `learned_examples=` em `SystemPromptBuilder.build`
     (`app/shared/prompts/system_prompt_builder.py`), atingindo o chat geral e
     os demais agentes, não só o wizard.

## Routing feedback `company_id` (Step 3 — avaliado, sem fix de código)

A auditoria viu `routing_feedback` sob `comp-1`/`empresa-xyz`. Investigação:
`app/shared/services/routing_learning_service.py` é um **shim**; o gravador real
(`main_orchestrator.py`) já persiste `str(ctx.company_id)` do tenant real. Os ids
placeholder vieram de **testes**, não de bug de produção. Logo, nenhuma mudança
de código foi necessária — apenas esta documentação.

## Sentinelas (fail se o ciclo regredir)

- **FE** `plataforma-lia/src/components/unified-chat/__tests__/UnifiedMessageList.feedback.test.tsx`
  - polegar com `conversationId` chama `submitThumbsFeedback` com
    `messageContext.lia_response` (prop precisa fluir);
  - sem `conversationId` → `toast.error` e NENHUMA chamada de rede (fail-loud).
- **BE** `lia-agent-system/tests/unit/test_feedback_learning_loop_t1297.py`
  - padrão `"general"` gerado mesmo sem intent;
  - `get_relevant_patterns` sempre inclui `"general"`;
  - helper de persona injeta `learned_examples` no build;
  - bloco vazio fail-open quando não há padrões.

Comandos:
```
# FE
cd plataforma-lia && npx vitest run src/components/unified-chat/__tests__/UnifiedMessageList.feedback.test.tsx
# BE
cd lia-agent-system && LIA_ENV=test python3 -m pytest tests/unit/test_feedback_learning_loop_t1297.py -q
```
