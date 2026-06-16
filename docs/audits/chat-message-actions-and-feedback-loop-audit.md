# Auditoria — Ações de Mensagem do Chat Unificado e Loop de Aprendizado/Personalização

**Data:** 2026-04-19
**Escopo:** Botões/ações por mensagem no chat unificado da LIA (copy, thumbs up/down, chips de clarificação) e o loop de aprendizado/personalização que esses sinais alimentam (`interaction_feedback` → `learning_patterns` → injeção no prompt do `response_generator`).
**Tarefa:** #569 (Plano LIA, Build mode).
**Skills aplicadas:** `feature-impact`, `canonical-fix`, `lia-compliance`, `lia-planning`, `lia-testing`.
**Tipo:** Read-only — nenhuma alteração de código. Apenas relatório + referência no índice. As correções derivadas vão para a Tarefa #570 e follow-ups.

---

## 0. Limitações Probatórias (ler antes do resto)

Para que o leitor saiba o peso de cada afirmação:

- **Verificado em código (alta confiança):** rotas registradas em `app/api/routes.py`, prefixos dos routers, ausência do path `/lia/feedback/{thumbs|rating|correction|metrics}` (busca exaustiva por `@router.post|get` em `lia_assistant*.py`), comportamento do proxy `lia/[...path]/route.ts`, comportamento do cliente `feedback-api.ts`, comportamento do componente `MessageActions` (incluindo o `toast.error` em falha — linhas 81 e 85 de `UnifiedMessageList.tsx`), serviço canônico `feedback_service.py`, ponto de injeção em `nodes.py:982-1087`.
- **Inferência razoável (confiança média) a partir do código verificado:** que **em produção** as chamadas reais retornam 4xx, que `record_feedback` não é invocado via API hoje, que `learning_patterns` está vazio para o caminho do chat, que o bloco "Aprendizados de interações anteriores" injetado no prompt é vazio para esse caminho. Isso decorre logicamente da ausência da rota, mas **não foi confirmado com SELECT em produção** neste workspace.
- **Não verificado nesta auditoria (evidência pendente):**
  1. Snapshot SQL antes/depois de um clique em thumbs no ambiente real (banco não provisionado neste workspace; `checkDatabase` retornou `provisioned: false`; produção não foi acessada por escopo).
  2. Captura de log/trace do prompt final do `response_generator` mostrando ou não a presença dos blocos `Exemplos de boas respostas` / `Evite respostas como` em uma sessão real.
  3. Volume real de `interaction_feedback.created_at >= NOW() - 24h` em produção.

A seção 11 lista o protocolo exato para coletar essas três evidências antes do hardening da Tarefa #570 (recomenda-se executar contra produção em modo read-only via `database` skill com `environment: "production"`).

---

## 1. Sumário Executivo

A camada visual de ações por mensagem está implementada (copy + thumbs up/down + chips de clarificação) e a camada conceitual de aprendizado existe no backend (serviço, modelos, injeção no prompt do gerador de resposta). **Porém o caminho que liga as duas está quebrado em código:** o frontend posta thumbs em endpoints (`/api/v1/lia/feedback/thumbs`, `/rating`, `/correction`, `/metrics`) que **não existem** no FastAPI. O cliente HTTP captura qualquer erro e devolve `{ feedback_id: '', status: 'error' }` sem propagar status nem causa. O componente `MessageActions` reverte o ícone e dispara `toast.error(t('feedbackErrorToast'))` (linhas 81 e 85 de `UnifiedMessageList.tsx`), então o usuário **percebe** que algo falhou — porém recebe sempre uma mensagem genérica ("erro de feedback") e nunca a causa real (404 do endpoint inexistente). Para o usuário final é "às vezes não funciona"; para o time é um bug crônico cuja origem fica oculta no Network tab.

Consequências diretas (inferidas do código — confirmar com SQL na seção 11):
- **Zero registros novos esperados** em `interaction_feedback` vindos do caminho do chat unificado, porque a chamada HTTP nunca chega a `feedback_service.record_feedback`.
- **`learning_patterns` não alimentados pelo chat** → o bloco "Aprendizados de interações anteriores" injetado em `nodes.py:1075-1087` deve cair em `has_patterns: False` para esse caminho. Padrões oriundos do wizard ou outros fluxos podem coexistir e, se houver, mascaram o gap nas métricas agregadas — daí a importância da query 4 da seção 11 (filtrar por origem do feedback, não só por volume total).
- **Loop de personalização do chat → resposta da LIA presumivelmente não está rodando.** A funcionalidade existe no código mas, no caminho do chat, é morta na prática.

Além desse achado P0, a auditoria identifica gaps de UX (sem persistência entre refresh, sem comentário opcional no thumbs down, sem confirmação visual robusta, sem regenerar/editar/continuar/TTS/export/share/branch/lembrar) e gaps de compliance/observabilidade (LGPD, métricas de eficácia do aprendizado, A/B testing não alimentado por thumbs).

**Ranking dos achados (por severidade):**

| # | Achado | Severidade | Onde corrigir |
|---|--------|-----------|---------------|
| F1 | Endpoint `/api/v1/lia/feedback/thumbs` (e família) **não existe** no backend; thumbs falham 404 silenciosamente | **P0 — Bloqueante** | Backend (criar router canônico) + frontend (parar de mascarar erro) |
| F2 | Cliente `feedback-api.ts` colapsa qualquer erro em `{status:'error'}` sem propagar status/causa; o componente exibe só um toast genérico → causa real (404) fica oculta | **P0 — Anti-pattern canonical-fix #3 e #4** | `plataforma-lia/src/services/lia-api/feedback-api.ts` |
| F3 | Thumbs não persistem entre refresh da conversa (estado só em React state local de `MessageActions`) | **P1 — UX** | Hidratar de `interaction_feedback` ao carregar histórico |
| F4 | Thumbs down sem campo de comentário opcional → perde-se o "porquê" da insatisfação | **P1 — UX/Loop** | Modal/popover após thumbs down |
| F5 | Sem confirmação visual após sucesso (só hover state) → usuário duvida se foi salvo | **P1 — UX** | Toast "obrigado pelo feedback" + estado fixo |
| F6 | Loop não retroalimenta A/B testing de prompts; não há dashboard de eficácia de `learning_patterns` | **P2 — Loop/Observabilidade** | Dashboard admin + integração com `prompt_ab_service` |
| F7 | Faltam ações premium presentes nos concorrentes: regenerar, editar+reenviar, continuar, TTS, export, share, branch, "lembrar disso" | **P2 — Paridade competitiva** | Tarefa #570 (parcial) + follow-ups |
| F8 | LGPD: `lia_response` e `user_message` salvos em texto puro em `interaction_feedback` sem marcação de consent nem TTL claro | **P2 — Compliance** | Cross-check com retenção LGPD (PARTE 4 da skill `lia-compliance`) |
| F9 | Backend tem 3 serviços com nome "feedback" (`feedback_service`, `feedback_learning_service`, `ml_feedback_service`) e 6+ rotas com prefixo `feedback` — alto risco de duplicata por confusão | **P2 — Tech debt (canonical-fix)** | Mapa canônico documentado nesta auditoria |

---

## 2. Mapeamento Canônico (skill `canonical-fix` — Fase 1)

### 2.1 Frontend — Ações de mensagem

| Arquivo | Linhas | Papel | Status |
|---------|-------:|-------|--------|
| `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx` | 42-148 | Componente `MessageActions` — copy + thumbs (canônico) | Único — OK |
| `plataforma-lia/src/services/lia-api/feedback-api.ts` | 1-103 | Cliente HTTP de feedback (`submitThumbsFeedback`, `submitRatingFeedback`, `submitCorrectionFeedback`, `getFeedbackMetrics`) | Único — **mas aponta para endpoints fantasmas** |
| `plataforma-lia/src/services/lia-api/base.ts` | 3 | `BACKEND_URL = '/api/backend-proxy'` | Único — OK |
| `plataforma-lia/src/app/api/backend-proxy/lia/[...path]/route.ts` | catch-all | Proxy Next → FastAPI (`${BACKEND_URL}/api/v1/lia/${pathStr}`) | Único — OK; reescreve corretamente |

**Sem duplicatas no frontend.** Não existe `feedback-api.tsx`, não existe outro `MessageActions`. Canônico = tabela acima.

### 2.2 Backend — Serviços e modelos

| Arquivo | Papel | Risco de confusão |
|---------|-------|-------------------|
| `lia-agent-system/app/domains/analytics/services/feedback_service.py` | **Canônico** do feedback do chat (`record_feedback`, `_update_patterns_from_feedback`, `get_relevant_patterns`, `get_pattern_context_for_response`) | — |
| `lia-agent-system/app/shared/services/feedback_service.py` | Re-export (`from app.domains.analytics.services.feedback_service import *`) | OK — é facade legítima |
| `lia-agent-system/app/domains/analytics/services/feedback_learning_service.py` | Wizard corrections + outcomes (`WizardFeedback`, `JobOutcome`, `SuggestionFeedback`) | Nome similar — outro domínio |
| `lia-agent-system/app/domains/analytics/services/ml_feedback_service.py` | Sinais para modelos ML | Nome similar — outro domínio |
| `lia-agent-system/app/domains/candidates/services/candidate_feedback_service.py` | Feedback do candidato (re-submissão de CV) | Nome similar — outro domínio |
| `lia-agent-system/libs/models/lia_models/feedback.py` | **Canônico** dos modelos `InteractionFeedback` e `LearningPattern` | — |
| `lia-agent-system/libs/models/lia_models/feedback_learning.py` | Modelos do wizard (não confundir) | — |
| `lia-agent-system/libs/agents-core/lia_agents_core/nodes.py:982-1087` | **Canônico** da injeção dos padrões no prompt do `response_generator` | — |

### 2.3 Backend — Routers `/feedback/*` registrados

```
search_feedback        prefix=/api/v1/search/feedback        (busca)
ml_feedback            prefix=/api/v1/ml-feedback            (ML)
suggestion_feedback    prefix=/api/v1/suggestion-feedback    (wizard)
calibration            prefix=/api/v1/.../feedback/explicit  (calibração)
public/shared_searches POST /{token}/feedback                (público)
sourcing_agents        POST /{agent_id}/feedback             (sourcing)
job_templates          POST /{template_id}/feedback          (templates)
interviews             POST /interviews/{id}/feedback        (entrevistas)
applications           GET  /feedback/{vacancy_id}/analytics (candidatos)
whatsapp               POST /send-feedback                   (WhatsApp)
teams                  POST /feedback                        (Teams)
lia_assistant_learning POST /lia/learning/stage-feedback     (wizard)
lia_assistant_wizard   POST /lia/wizard/stage8/feedback      (wizard)
lia_assistant_wizard   POST /lia/wizard/stage10/feedback     (wizard)
```

**Nenhum** com `POST /api/v1/lia/feedback/thumbs` ou `/rating` ou `/correction`. O frontend chama um caminho que não tem handler. Resultado: 404 do FastAPI → Next proxy retorna 500/404 → `feedback-api.ts` cai no `if (!response.ok)` e devolve `{status:'error'}` em silêncio (anti-padrão #3 da skill `canonical-fix`).

### 2.4 Conclusão de canonicalidade

**Canônicos identificados:** 4 frontend + 4 backend (lista acima). **Duplicatas a deletar:** nenhuma — todas as variantes de "feedback service" são domínios diferentes legítimos. **Item ausente:** o router que expõe o `feedback_service` canônico via HTTP. Sem ele, o pipeline tem origem (UI), tem destino (LLM prompt) e tem motor (DB + service), **mas falta o tubo entre origem e motor.**

---

## 3. Inventário Detalhado das Ações Existentes

### 3.1 Copy (linhas 56-65 de `UnifiedMessageList.tsx`)

- **Implementação:** `navigator.clipboard.writeText(content)`, toast de sucesso/erro, ícone alterna `Copy → Check` por 1.5 s.
- **Status:** Funciona. 100% client-side. Sem chamada de rede. Sem registro em DB.
- **Gap:** Não há registro de "quais respostas o usuário copia" — sinal forte de utilidade que poderia retroalimentar o `learning_patterns` (resposta copiada = boa). Hoje é desperdiçado.

### 3.2 Thumbs Up / Down (linhas 67-148)

- **UI:** Optimistic update + revert em falha + `aria-pressed`. Bom no plano de acessibilidade (WCAG 2.1 AA — ver lia-compliance crença 13).
- **Backend chamado:** `POST ${BACKEND_URL}/lia/feedback/thumbs` → proxy → `POST /api/v1/lia/feedback/thumbs`.
- **Estado real:** **404.** Endpoint não existe.
- **Tratamento de erro:** colapsado (anti-padrão #3 da `canonical-fix`). O cliente HTTP transforma qualquer status ≠ 2xx em `{ status: 'error' }` sem `console.error`, sem distinguir 404 de 500 de timeout. O componente reverte o ícone e dispara `toast.error(t('feedbackErrorToast'))` (linhas 81 e 85) — então o usuário **vê** uma mensagem genérica, mas a causa real (404 do endpoint inexistente) só é visível abrindo o Network tab. Resultado prático: bug crônico que o usuário reporta como "às vezes o thumbs não funciona", e que o time não consegue rastrear sem investigação manual.
- **Sem comentário no thumbs down:** mesmo se o endpoint existisse, o sinal "down" entraria sem o "porquê" — perda massiva de qualidade de aprendizado.
- **Sem persistência entre refresh:** estado só em `useState` local. Recarregar a conversa zera as marcações (gap UX-1 já mapeado no Task #570).

### 3.3 Chips de clarificação (linhas 244-256)

- **Origem:** evento WS `clarification` do `cascaded_router` (ver `useChatSocket.ts:313-333`). Renderizados quando o roteador cai no Tier 8 e devolve `{question, options}`.
- **Comportamento:** clique chama `onChipClick(value)` → o consumidor (`UnifiedChat`) reenvia como mensagem.
- **Status:** Funciona. **Não emite sinal de feedback** ("o usuário escolheu X dentre N opções" é um sinal valioso para o roteador aprender, mas não é capturado em lugar nenhum).
- **Gap:** Oportunidade de retroalimentar o `cascaded_router` com a escolha do usuário (qual opção, em que contexto) para reduzir Tier 8 ao longo do tempo.

### 3.4 Sem outras ações por mensagem

Comparativo (conhecimento público, abril/2026):

| Ação | LIA hoje | Claude.ai | ChatGPT | Manus | Perplexity |
|------|:--------:|:---------:|:-------:|:-----:|:----------:|
| Copiar | ✅ | ✅ | ✅ | ✅ | ✅ |
| Thumbs up/down | ⚠️ (404) | ✅ | ✅ | ✅ | ✅ |
| Comentário no thumbs down | ❌ | ✅ | ✅ | ✅ | ✅ |
| Regenerar resposta | ❌ | ✅ | ✅ | ✅ | ✅ |
| Editar mensagem do usuário e reenviar | ❌ | ✅ | ✅ | ❌ | ❌ |
| Continuar (resposta truncada) | ❌ | ✅ | ✅ | ❌ | ❌ |
| Text-to-speech | ❌ | ❌ | ✅ | ❌ | ❌ |
| Exportar (PDF/MD) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Compartilhar conversa (link público) | ❌ | ✅ | ✅ | ❌ | ✅ |
| Branch / fork de conversa | ❌ | ✅ | ❌ | ❌ | ❌ |
| Salvar resposta na memória ("lembrar disso") | ❌ | ❌ | ✅ | ❌ | ❌ |
| Citações clicáveis | ❌ | ⚠️ (parcial) | ⚠️ | ✅ | ✅ |

A LIA está atrás dos quatro concorrentes nessa camada. Mais grave: a única ação "premium" implementada (thumbs) está quebrada.

---

## 4. Loop de Aprendizado/Personalização — Como Deveria Funcionar vs. Como Funciona

### 4.1 Fluxo desenhado (intenção)

```
[1] Usuário clica thumbs up/down em mensagem da LIA
        │
        ▼
[2] POST /api/v1/lia/feedback/thumbs  (sessionId, messageId, thumbs, userId)
        │
        ▼
[3] feedback_service.record_feedback(...)
       ├── INSERT INTO interaction_feedback (thumbs, user_message, lia_response,
       │     intent, stage, response_time_ms, tools_used, confidence_score, ...)
       └── _update_patterns_from_feedback()
              └── UPSERT learning_patterns por (company_id, pattern_key=intent_stage)
                   ├── positive_feedback_count++ ou negative_feedback_count++
                   ├── append em example_good_responses ou example_bad_responses (cap 5)
                   ├── recalcula success_rate e confidence
                   └── ativa/desativa via threshold confidence ≥ 0.5
        │
        ▼
[4] Próxima mensagem do MESMO company_id e MESMO intent:
       response_generator.run() em nodes.py:982:
              └── feedback_service.get_pattern_context_for_response(intent, msg, company_id)
                     └── retorna {good_response_examples, bad_response_examples,
                                  response_style_hints, average_success_rate}
        │
        ▼
[5] System prompt recebe (linhas 1075-1087 de nodes.py):
       "## Aprendizados de interações anteriores:
        Exemplos de boas respostas: [...]
        Evite respostas como: [...]
        Dicas de estilo: [...]"
        │
        ▼
[6] LLM gera resposta personalizada por empresa, calibrada nos thumbs prévios.
```

### 4.2 Onde quebra hoje

- **Quebra em [2]:** endpoint não existe → 404. Cadeia inteira para aqui.
- **Quebra silenciosa em [3]:** mesmo se endpoint existisse, o cliente mascara erro e usuário não saberia.
- **Quebra latente em [5]:** mesmo com [2-4] OK, a janela é apenas `pattern[:3]` × `examples[:2]` = no máximo 6 exemplos bons + 6 ruins + 2 hints. Sem priorização por recência, sem decay. Empresa com 1 ano de uso teria padrões antigos misturados com recentes (gap arquitetural).
- **Sem retroalimentação para A/B testing:** existe `prompt_ab_service` na plataforma mas o resultado dos thumbs **não** afeta a escolha de variante de prompt. Os dois sistemas vivem desacoplados.
- **Sem dashboard:** nenhuma tela mostra "qual % de mensagens recebeu thumbs up no último mês", "quais padrões mais ativados", "qual variante de prompt converte melhor". `feedback_service.get_feedback_metrics` existe (linhas 390-510) mas nenhum endpoint expõe e nenhum frontend consome.

### 4.3 Verificação ao vivo (tentativa)

Tentativa de query SELECT em `interaction_feedback` e `learning_patterns` para confirmar se há dados recentes do chat: **banco de dados de desenvolvimento não provisionado neste workspace** (verificado via `checkDatabase`). Recomendação: rodar em produção após o hardening da Tarefa #570 as queries:

```sql
-- Volume de thumbs nas últimas 24h
SELECT thumbs, COUNT(*) FROM interaction_feedback
 WHERE created_at >= NOW() - INTERVAL '24 hours' GROUP BY thumbs;

-- Padrões ativos por empresa
SELECT company_id, COUNT(*) AS active_patterns,
       AVG(confidence) AS avg_conf, AVG(success_rate) AS avg_sr
  FROM learning_patterns WHERE is_active GROUP BY company_id;

-- Padrões com exemplos populados (sinal de loop vivo)
SELECT COUNT(*) FROM learning_patterns
 WHERE jsonb_array_length(example_good_responses::jsonb) > 0
    OR jsonb_array_length(example_bad_responses::jsonb) > 0;
```

Se a primeira query retornar zero novos registros nas últimas 24 h em produção, **F1 está confirmado em campo** e não apenas em código.

---

## 5. Análise de Impacto (skill `feature-impact`)

Aplicada ao escopo conjunto desta auditoria + Tarefa #570. Apenas dimensões com impacto.

| Dimensão | Impacto | O que precisa acontecer |
|----------|---------|-------------------------|
| **Frontend** | Alto | Hidratar thumbs do histórico; toast de sucesso; modal opcional para comentário do thumbs down; parar de mascarar erros do `feedback-api.ts`; no futuro, regenerar/editar/continuar |
| **Backend API** | **Bloqueante** | Criar router canônico `app/api/v1/lia_feedback.py` (prefix `/lia/feedback`) com `POST /thumbs`, `POST /rating`, `POST /correction`, `GET /metrics`. Registrar em `routes.py`. Integrar com `dependencies.get_current_user` e isolamento `company_id`. |
| **Backend Services** | Médio | `feedback_service` já existe e está pronto. Adicionar `delete_feedback` (para LGPD DSR). Considerar decay temporal nos `learning_patterns`. |
| **Banco de dados** | Médio | Modelos OK. Adicionar índice `(company_id, created_at DESC)` em `interaction_feedback` para o dashboard. Confirmar que `company_id` está em todas as queries (multi-tenant — crença 04 e 13 da governança). |
| **Camada IA / Agentes** | Alto | A injeção em `nodes.py:1075-1087` está correta como contrato. Após F1 corrigido, validar que o LLM realmente respeita os padrões (eval com golden dataset — ver lia-testing). |
| **Compliance / LGPD** | Alto | F8 — `interaction_feedback.lia_response` e `.user_message` são PII sob LGPD (podem conter nome de candidato, salário, dados sensíveis). Aplicar PII Masking antes da persistência ou tratar como dado pessoal com retenção de 365 dias (alinhado a "Logs de IA" na PARTE 4 da skill). DSR: usuário deve poder solicitar deleção dos próprios feedbacks. |
| **Segurança / Multi-tenant** | Alto | Endpoint novo deve ler `company_id` do usuário autenticado (não do body) — IDOR clássico se confiar no body. `record_feedback` recebe `company_id` como parâmetro do caller, então a responsabilidade é do router. |
| **Observabilidade** | Médio | Logs estruturados já existem em `feedback_service`. Adicionar métrica Prometheus `lia_feedback_received_total{type, company_id}` e `lia_feedback_pattern_applied_total{intent}`. Trace LangSmith no `get_pattern_context_for_response`. |
| **Testes** | Alto | E2E: usuário clica thumbs → confere registro no DB → segunda mensagem mesmo intent → confere que system prompt contém o exemplo. Eval com golden dataset cobrindo 5 intents principais. |
| **Performance/Código** | Baixo | `feedback-api.ts` é pequeno. `MessageActions` está dentro de `UnifiedMessageList.tsx` (315 linhas) — ainda saudável. Sem risco de monolito. |

---

## 6. Recomendações Prioritizadas

### P0 — Bloqueante (Tarefa #570)

1. **Criar router `app/api/v1/lia_feedback.py`** com endpoints `POST /lia/feedback/thumbs`, `POST /lia/feedback/rating`, `POST /lia/feedback/correction`, `GET /lia/feedback/metrics`. Cada handler:
   - lê `company_id`, `user_id` do contexto autenticado (nunca do body),
   - chama `feedback_service.record_feedback(...)` com `message_context` montado a partir do payload,
   - retorna `{feedback_id, status: 'recorded'}` em 201,
   - retorna 4xx/5xx explícitos em falha (sem `try/except: pass`).
2. **Registrar router** em `app/api/routes.py` (`prefix="/api/v1"`).
3. **Reescrever `feedback-api.ts`** para parar de mascarar erro: lançar `HttpError` em status ≠ 2xx, deixar o componente `MessageActions` reverter o estado E exibir toast (anti-padrão #3 da `canonical-fix`).
4. **Persistir thumbs entre refresh:** ao montar `MessageActions`, ler do `interaction_feedback` o último thumbs daquele `(session_id, message_id)`. Endpoint `GET /lia/feedback/by-message/{message_id}` opcional, ou hidratar via histórico de conversa.
5. **Adicionar PII Masking** antes de persistir `lia_response` e `user_message` (`PIIMaskingFilter` já é canônico — ver lia-compliance PARTE 4).

### P1 — Alto (Tarefa #570 ou follow-up)

6. **Comentário opcional no thumbs down:** popover inline com `<textarea>` + 3 chips ("impreciso", "tom errado", "alucinou"). Persistir em `feedback.feedback_text` + `feedback_category`.
7. **Confirmação visual robusta:** toast "Obrigado pelo feedback" + estado fixo (não opacity 0 ao tirar hover) por X segundos.
8. **Regenerar resposta:** ícone "↻" ao lado dos thumbs. Reenvia a última mensagem do usuário com `regenerate=true` no payload, marca a resposta antiga como "discarded" (campo novo em `interaction_feedback`).

### P2 — Médio/Pós-MVP (follow-ups)

9. **Dashboard de eficácia do aprendizado** (admin only): heatmap por empresa de % thumbs up, padrões mais ativados, decay temporal, win-rate de variantes A/B.
10. **A/B testing alimentado por thumbs:** vincular variante de prompt usada à `interaction_feedback` (campo `prompt_variant`); cron diário ajusta peso da variante por bandit (UCB1).
11. **Retroalimentação dos chips de clarificação:** persistir escolha em `interaction_feedback` com `intent='clarification_chip'` para o `cascaded_router` aprender.
12. **Editar+reenviar / continuar / TTS / export / share / branch / "lembrar disso":** paridade competitiva — escopo separado, pode virar Sprint dedicado ("Chat Premium Actions").
13. **DSR LGPD:** endpoint `DELETE /lia/feedback/me` para o usuário apagar seus próprios feedbacks (Art. 18 V — eliminação).
14. **Decay temporal nos `learning_patterns`:** padrões com `last_applied_at` > 90 dias perdem peso linearmente. Hoje há `expires_at` no modelo mas ninguém escreve nele.

---

## 7. Riscos e Atenções

| Risco | Mitigação |
|-------|-----------|
| Ao corrigir F1, volume de inserts em `interaction_feedback` salta de 0 para milhares/dia → potencial pressão no DB | Adicionar índice `(company_id, created_at DESC)` no mesmo deploy; bulk insert futuramente se necessário. |
| Padrões aprendidos podem injetar viés discriminatório no prompt (ex: empresa que dá thumbs up só em respostas que excluem 50+) | Aplicar `FairnessGuard.check()` nos `example_good_responses`/`example_bad_responses` antes de injetar (lia-compliance PARTE 3 — Camada 1 e 2). Auditoria trimestral dos padrões ativos. |
| `lia_response` salvo em texto puro pode conter PII de candidato | PII Masking no momento do persist (lia-compliance PARTE 4 pilar 3). |
| Thumbs do recrutador A pode influenciar resposta servida ao recrutador B da mesma empresa | É o comportamento desejado (aprendizado por `company_id`), mas precisa estar documentado em política de uso e respeitar o opt-out de "aprender com meus dados". |
| Migrar para o endpoint novo sem coordenar deploy frontend↔backend gera janela de 100% falha | Lançar router primeiro (nada quebra), 1-2 dias de soak, depois lançar frontend que de fato exibe toast de erro. |

---

## 8. Referências de Código

- Frontend ações: `plataforma-lia/src/components/unified-chat/UnifiedMessageList.tsx:42-148`
- Cliente HTTP de feedback: `plataforma-lia/src/services/lia-api/feedback-api.ts:1-103`
- Proxy catch-all LIA: `plataforma-lia/src/app/api/backend-proxy/lia/[...path]/route.ts`
- Service canônico: `lia-agent-system/app/domains/analytics/services/feedback_service.py:42-562`
- Re-export shared: `lia-agent-system/app/shared/services/feedback_service.py`
- Modelos: `lia-agent-system/libs/models/lia_models/feedback.py`
- Injeção no prompt: `lia-agent-system/libs/agents-core/lia_agents_core/nodes.py:980-1087`
- Registro de routers: `lia-agent-system/app/api/routes.py:299, 460-466`

---

## 9. Saída esperada da skill `canonical-fix` (Fase 5)

1. **Qual é o canônico?** Frontend: `UnifiedMessageList.tsx` + `feedback-api.ts`. Backend: `feedback_service.py` (domínio `analytics`) + `feedback.py` (modelos) + `nodes.py:982-1087` (injeção). **Falta canônico:** router HTTP `app/api/v1/lia_feedback.py`.
2. **Duplicatas/dead code deletados nesta auditoria?** Nenhum — auditoria é read-only.
3. **Consumidores tocados?** Nenhum — apenas mapeados.
4. **Teste de regressão?** A criar na Tarefa #570 (e2e thumbs → DB → próximo prompt).
5. **Algum workaround introduzido?** Não.

---

## 11. Protocolo de Coleta das Evidências Pendentes

Para fechar as três lacunas listadas em §0, executar **antes de aplicar a Tarefa #570** (todas read-only contra produção, via `database` skill com `environment: "production"`):

**Q1 — Volume baseline (confirma F1 em campo):**
```sql
SELECT COUNT(*) AS total_24h,
       COUNT(*) FILTER (WHERE thumbs = 'up')   AS up_24h,
       COUNT(*) FILTER (WHERE thumbs = 'down') AS down_24h,
       MAX(created_at)                         AS last_event_at
  FROM interaction_feedback
 WHERE created_at >= NOW() - INTERVAL '24 hours';
```
Esperado se F1 verdadeiro: `total_24h = 0` (ou apenas inserts vindos de outros caminhos não-chat).

**Q2 — Quebra por origem (separa chat de wizard):**
```sql
SELECT (message_context->>'source')::text AS source,
       COUNT(*) AS n
  FROM interaction_feedback
 WHERE created_at >= NOW() - INTERVAL '7 days'
 GROUP BY 1 ORDER BY 2 DESC;
```
Esperado: `chat_unified` ausente ou zero.

**Q3 — Padrões ativos por empresa:**
```sql
SELECT company_id,
       COUNT(*) AS active_patterns,
       AVG(confidence) AS avg_conf,
       AVG(success_rate) AS avg_sr,
       COUNT(*) FILTER (
         WHERE jsonb_array_length(COALESCE(example_good_responses::jsonb, '[]'::jsonb)) > 0
            OR jsonb_array_length(COALESCE(example_bad_responses::jsonb, '[]'::jsonb)) > 0
       ) AS patterns_with_examples
  FROM learning_patterns
 WHERE is_active
 GROUP BY company_id ORDER BY active_patterns DESC LIMIT 20;
```
Esperado: `patterns_with_examples ≈ 0` para a maioria — sinal de loop morto.

**Q4 — Captura do prompt final do `response_generator`:**
1. Em produção, ativar log `LIA_LOG_FINAL_PROMPT=true` (ou usar trace LangSmith do nó `response_generator`) por uma janela de 1 hora.
2. Selecionar 5 traces de empresas distintas com `intent` recorrente (ex.: `screening`, `vacancy_analysis`).
3. Verificar a presença literal do bloco `## Aprendizados de interações anteriores:` e se as listas de exemplos estão preenchidas. Anexar excertos (com PII mascarada) ao apêndice da próxima revisão deste documento.

**Q5 — Comparação após Tarefa #570 mergeada:**
Re-executar Q1, Q2 e Q3 24 h após o deploy. Esperado: `total_24h > 0` em Q1, `chat_unified` aparecendo em Q2, `patterns_with_examples` crescendo em Q3.

Resultados devem ser anexados como subseção `Apêndice A — Evidência ao vivo (data X)` deste mesmo arquivo, mantendo PII mascarada (alinhado a lia-compliance PARTE 4 pilar 3).

---

## Apêndice A — Evidência ao vivo (2026-04-19, réplica read-only de produção)

Coleta executada via `executeSql` com `environment: "production"` (réplica read-only do ATS). Sem nenhuma escrita. Resultados crus abaixo confirmam todas as inferências do relatório.

**Q0 — Schema confirmado** (apenas para registro): `interaction_feedback` tem 20 colunas (id, session_id, company_id, user_id, message_id, user_message, lia_response, intent, stage, rating, thumbs, correction, feedback_text, feedback_category, response_time_ms, tools_used, confidence_score, processed, incorporated_to_rag, created_at). `learning_patterns` tem 16 colunas. **Observação relevante:** o campo originalmente referenciado como `expires_at` (P2 item 14, decay temporal) **não existe** no schema atual — adicionar como migration faz parte do escopo do follow-up #573.

**Q1 — Volume últimas 24 h:**
```
total_24h | up_24h | down_24h | last_event_at
        0 |      0 |        0 | (null)
```

**Q1b — Volume diário últimos 30 dias:**
```
(zero linhas — nenhum evento em 30 dias)
```

**Q1c — Total histórico:**
```
total_ever | first_event              | last_event
         3 | 2026-01-30 00:38:31.726  | 2026-01-30 00:38:38.940
```
Apenas 3 registros em toda a história da tabela, todos no mesmo segundo de 2026-01-30 (compatível com smoke test manual). Zero atividade orgânica.

**Q3 — Padrões aprendidos:**
```
total_patterns | active_patterns | avg_conf | avg_sr
             0 |               0 |   (null) | (null)
```

**Q3b — Padrões com exemplos populados:**
```
patterns_with_good_examples
                          0
```

**Veredicto da evidência:** o loop `chat → interaction_feedback → learning_patterns → prompt` está **comprovadamente morto em produção**. A tabela de padrões nunca foi populada (0 linhas, não apenas inativas). Confirmado o achado F1 do relatório com 100% de certeza factual — não é mais inferência. O bloco "Aprendizados de interações anteriores" injetado em `nodes.py:1075-1087` cai obrigatoriamente em `has_patterns: False` para qualquer empresa em qualquer caminho, porque a tabela de origem é vazia.

**Implicação adicional:** o gap não é só do chat unificado. Como `learning_patterns` está zerado, **nenhum** caminho de feedback (wizard incluso) está conseguindo popular padrões para o `response_generator`. O `_update_patterns_from_feedback` não roda por nenhum canal hoje — vale auditar separadamente os caminhos `/lia/learning/stage-feedback` e `/lia/wizard/stage{8,10}/feedback` para entender se eles também estão quebrados ou se simplesmente não chamam o método de update.

**Q4 (captura do prompt final em runtime) — não executada nesta coleta:** requer ativar log/trace temporário em produção (LangSmith ou flag `LIA_LOG_FINAL_PROMPT`), o que ultrapassa o escopo de "apenas leitura ao banco" autorizado. Recomendado fazer junto com o deploy do hardening da Tarefa #570 — ali a captura passa a valer ouro como prova "antes vs depois".

**PII:** nenhum conteúdo de `user_message` ou `lia_response` foi consultado nesta coleta — apenas agregações (COUNT, MIN, MAX). Sem exposição de dados pessoais.

---

## 12. Próximos Passos

- A Tarefa **#570** absorve os itens P0 e P1 desta auditoria (escopo: criar router canônico, parar de mascarar erro, persistir thumbs, comentário no thumbs down, toast, regenerar).
- Os itens P2 viram follow-ups separados (dashboard, A/B, paridade competitiva, DSR LGPD, decay).
- Recomenda-se rodar as queries da seção 11 em produção antes do hardening para quantificar o gap (volume zero esperado).
- Após F1 corrigido, executar bias audit (lia-compliance PARTE 3) sobre os 100 primeiros `learning_patterns` ativados para garantir que o loop não está aprendendo viés.
