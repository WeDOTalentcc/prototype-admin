# Auditoria — Falhas de interpretação na conversa de busca da LIA

**Data:** 2026-04-21
**Tarefa:** #738
**Escopo:** Investigação. Nenhuma correção de código entra nesta tarefa.

## Contexto da conversa auditada

Na conversa relatada o usuário tentou abrir o Funil de Talentos e iniciar uma busca. As 4 mensagens problemáticas foram:

1. `busque candidatos desenvolvedor python com inglês avançado em são paulo capital`
   → LIA executou a busca mas afirmou que "não consegue filtrar por localização".
2. `pode3` → LIA respondeu de forma confusa (não entendeu como confirmação).
3. `pode sim` → LIA disparou o fluxo de **perfil cultural** (5 perguntas) em vez de continuar a busca.
4. `estamos falando de buscar candidatos e nao perfil cultura`
   → LIA tratou como nova busca por "e nao perfil cultura" e devolveu "nenhum candidato encontrado".

Além disso, em algum ponto o overlay de dev do Next.js exibiu `HttpError: Failed to fetch` originado em `src/services/lia-api/base.ts:207`.

---

## P1 — "São Paulo capital" não vira filtro de cidade

**Severidade:** Média · **Categoria:** Extração de filtros + Prompt/UX

### Reprodução do caminho
1. Mensagem entra em `chat.send_message` (`app/api/v1/chat.py:228`) → `ChatAdapter.process_message` → `MainOrchestrator.process` (`app/orchestrator/main_orchestrator.py:187`).
2. Pré-checks (security, fairness, tenant, memória) passam.
3. **Phase 1.5 (Agentic Loop, `LIA_AGENTIC_LOOP=true`)** assume — `app/orchestrator/agentic_loop.py:60`. O LLM é chamado com schemas de ferramenta via `generate_with_tools` e decide chamar `search_candidates`.
4. O `CandidateSearchService` (`app/domains/ai/services/candidate_search_service.py:159-169`) tem suporte real para localização:
   ```sql
   AND (:use_loc = 0 OR c.location_city ILIKE :loc OR c.location_state ILIKE :loc)
   ```
   ou seja, o backend **consegue** filtrar por cidade/estado.

### Causa raiz
A frase de LIA "não consigo filtrar por localização" **não vem de nenhum prompt que afirme essa limitação** — uma busca por essa string só aparece em datasets de avaliação (`tests/eval/datasets/sourcing/scenarios.yaml:70`) como _failure mode_ esperado para casos diferentes (benchmark WSI por indústria/localização).

O fluxo real no caso auditado tem dois pontos frágeis convergindo:

1. **Extrator de critérios do front (`plataforma-lia/src/components/expanded-chat/hooks/criteriaExtractorSecondary.ts`)** usa `knownCities` + regex `/(?:localização|localizacao|cidade|local)\s*[:\-]?\s*(...)/`. A frase `em são paulo capital` não casa com nenhum prefixo (`em` não está coberto, e o sufixo `capital` não está em `knownCities` nem é normalizado para `São Paulo`). O parâmetro de localização pode chegar vazio ou como literal `"são paulo capital"`.
2. **Schema da tool `search_candidates`** (Phase 1.5) recebe os parâmetros que o LLM extrair da própria mensagem. Se o LLM não popular `location` (porque o prompt não o instrui claramente a fazê-lo, ou porque `knownCities` não confirma "capital"), a tool é chamada sem o filtro e o LLM, ao gerar a resposta de fallback, **alucina** a desculpa "não consigo filtrar por localização" — provavelmente porque viu o resultado vazio para algo que ele não tem certeza se foi aplicado.

### Evidências
- `candidate_search_service.py:159-169`: predicado `location_city ILIKE` existe.
- `criteriaExtractorSecondary.ts:7-46`: regex de localização não cobre `em <cidade>` nem o sufixo `capital`.
- Sem nenhum registro de `"não consigo filtrar por localização"` em prompts de produção (`app/prompts/**`); só em dados de eval.

### Recomendação (alto nível)
- Garantir que o `description` / `parameters` do tool `search_candidates` exposto ao LLM cite explicitamente que `location_city` e `location_state` são suportados, com exemplos ("São Paulo capital" → `location_city="São Paulo"`).
- Estender o normalizador de cidade do front para reconhecer `"<cidade> capital"` e prefixo `em` antes do nome.
- Adicionar regra no system prompt da LIA proibindo afirmar limitações que não existem nas tools disponíveis.

---

## P2 — "pode sim" dispara o fluxo de perfil cultural (5 perguntas)

**Severidade:** Alta · **Categoria:** Roteamento/intent + Estado de conversa

### Reprodução do caminho
1. Quando o usuário enviou a primeira mensagem ("busque candidatos..."), o `MainOrchestrator` rodou o **PreConditionChecker (D10)** em `main_orchestrator.py:392-428`.
2. `PreConditionChecker.check` (`app/orchestrator/precondition_checker.py:155-172`) detectou `culture_profile_missing` — a empresa não tem `company_culture_profiles` preenchido — e gerou um hint do tipo onboarding.
3. Como `culture_profile_missing` está em `_ONBOARDING_HINT_TYPES` (`main_orchestrator.py:384-391`), o orquestrador **delegou a conversa inteira para o agente `company_settings`** (`_agent_type = "company_settings"`). O system prompt deste agente (`app/domains/company_settings/agents/company_system_prompt.py:72-75`) instrui textualmente: _"SE missing_culture_fields > 0: Faça 5 perguntas curtas sobre missão, visão, valores, modelo de trabalho..."_.
4. No turno em que a LIA executou a busca, ela também terminou perguntando algo como "posso te guiar pelas 5 perguntas culturais?" (proativo, decorrente do hint).
5. `pode3` (provável typo) — `is_confirmation` (`action_executor/utils.py:53-58`, padrões em `intents_config.py:762`) **não casa** com `"pode3"` (não está nos `CONFIRMATION_PATTERNS`), nem dispara nenhum FastRouter pattern. Caiu no LLM cascade que respondeu de forma evasiva.
6. `pode sim` — agora **casa** com `CONFIRMATION_PATTERNS` (`pode sim` está literalmente listado). Phase 0 (`_handle_pending_action` em `main_orchestrator.py:325`) dispara a ação pendente "iniciar onboarding cultural" deixada pelo turno anterior, e o agente `company_settings` toma o controle e começa as 5 perguntas.

### Causa raiz
**Não é o "pode sim" que disparou o fluxo cultural** — quem disparou foi o `PreConditionChecker` no turno anterior, ao detectar `culture_profile_missing` e mudar o `agent_type` da conversa para `company_settings` independentemente do contexto operacional do usuário (que era buscar candidatos). O "pode sim" apenas confirmou a oferta proativa que ficou pendente.

Há dois defeitos combinados:

- **PreConditionChecker é puramente baseado em estado da empresa, sem considerar o contexto da mensagem do usuário.** Mesmo com o usuário em meio a uma busca explícita (intent `sourcing` claríssimo), o checker promove `culture_profile_missing` ao papel de `agent_type` principal do turno seguinte, perdendo o contexto de busca.
- **Pending action / hint proativo não traz "âncora de contexto"**. Quando o usuário responde "pode sim", o sistema não verifica se a oferta confirmada é coerente com o tópico atual (sourcing) — assume que toda confirmação se refere à última oferta proativa.

### Evidências
- `main_orchestrator.py:384-412`: `_ONBOARDING_HINT_TYPES` e troca de `_agent_type` para `company_settings`.
- `company_system_prompt.py:72-75`: instrução literal das 5 perguntas.
- `action_executor/intents_config.py:762`: `"pode sim"` em `CONFIRMATION_PATTERNS`.
- `precondition_checker.py:155-172`: hint disparado por ausência de perfil cultural, sem considerar o intent atual.

### Recomendação (alto nível)
- Quando o usuário tem intent operacional ativo de alta confiança (busca, criação de vaga, ação em pipeline), o PreConditionChecker deve **anexar o hint como "side note"** (mostrar como sugestão proativa) sem trocar o `agent_type` principal do turno.
- Pending actions / proactive offers precisam guardar `context_topic` (sourcing, culture, etc.) e checar coerência com o turno corrente antes de aceitar a confirmação.
- Atalho específico: se o turno anterior do usuário tinha intent `sourcing`/`buscar_candidatos`, ignorar onboarding hints até o usuário concluir/abandonar a busca.

---

## P3 — Frase corretiva interpretada como nova busca

**Severidade:** Alta · **Categoria:** Roteamento/intent + Extração de query

### Reprodução do caminho
Mensagem: `estamos falando de buscar candidatos e nao perfil cultura`

1. `MainOrchestrator.process` → Phase 0 (sem pending action ativa após o ciclo cultural) → Phase 1 (`_try_action_executor`).
2. `ActionExecutorService.try_execute` chama `_detect_intent_from_message` (`action_executor/utils.py`).
3. `_NEGATION_STARTS = ("não, não", "nao, nao", "não era isso", "nao era isso", "cancela isso", "na verdade,")` (`utils.py:123`). A frase **não começa** com nenhum desses padrões — `"estamos falando"` não é reconhecido como correção. Bypass de negação não dispara.
4. Regex de intent casa `r"buscar?\s+\w*\s*candidato"` → intent `buscar_candidatos`.
5. `_extract_entities_from_message` aplica:
   ```python
   r"(?:busca[rn]?|...)\s+(?:candidatos?\s+)?(?:com\s+|para\s+|que\s+|de\s+)?(.{5,})"
   ```
   No texto, a primeira ocorrência de `buscar candidatos` está depois de `estamos falando de`, e o grupo capturado a partir daí é `e nao perfil cultura` (tudo após `buscar candidatos `).
6. Esse texto vira `params["query"] = "e nao perfil cultura"` e é enviado ao tool de busca, que retorna 0 candidatos.
7. **`detect_meta_capability_question` (`meta_question_detector.py`)** também não dispara: a frase não começa com nenhum capability opener (`consegue`, `você sabe`, `tem como`, `é possível`, `como faço para`, etc.).

### Causa raiz
- O **detector de correção/negação é raso** — só reconhece um conjunto pequeno de openers fixos (`utils.py:123`). Frases corretivas naturais como "estamos falando de…", "o que eu pedi foi…", "voltando para…", "esquece o cultural…" passam batidas.
- O **extrator de query do `ActionExecutor` é puramente posicional** — ele pega "tudo depois do verbo" sem analisar se o resto é um critério de busca real ou uma correção/explicação. Com a frase "estamos falando de buscar candidatos e não perfil cultura", a parte capturada é literalmente uma negação.
- Não há nenhuma checagem de "isso parece uma query plausível?" antes de chamar o tool (ex.: contém pelo menos um termo de skill/cidade/título reconhecível).

### Evidências
- `action_executor/utils.py:123-125` — lista limitada de `_NEGATION_STARTS`.
- Função `_extract_entities_from_message` em `action_executor/utils.py` (regex posicional documentada pelo subagente).
- `meta_question_detector.py:35-48` — openers limitados a "consegue/você sabe/tem como/...".

### Recomendação (alto nível)
- Expandir `_NEGATION_STARTS` (e idealmente substituir por um classificador leve) para reconhecer correções/clarificações típicas em PT-BR: "estamos falando de", "o que eu pedi", "esquece", "voltando", "não, é sobre".
- Antes de despachar a query para o tool de busca, validar que ela contém **pelo menos um sinal operacional** (skill conhecida, cidade, senioridade, ID, número). Caso contrário, voltar para o LLM cascade com o histórico para pedir clarificação ou reusar critérios do turno anterior.
- `meta_question_detector` poderia ganhar um irmão `correction_detector` que escala para o LLM com instrução explícita de respeitar a correção do usuário.

---

## P4 — Overlay `HttpError: Failed to fetch` em `base.ts:207`

**Severidade:** Média · **Categoria:** Resiliência de rede no front

### Reprodução do caminho
1. `base.ts:204-208`:
   ```ts
   if (isTransientNetworkError(lastError)) {
     const msg = lastError instanceof Error ? lastError.message : 'Network unavailable'
     throw new HttpError(0, msg, { transientNetworkError: true })
   }
   ```
   Esta é a "saída sancionada" do `fetchWithRetry` quando o backend está em cold-start, ou a rede caiu por instantes — Task #728 tipou esse erro justamente para evitar o overlay do Next reagindo ao texto cru `TypeError: Failed to fetch`.
2. **`chat-api.ts` ainda usa `fetch` cru** (`sendMessage` linhas 17/36/50/69/81): _não_ passa pelo `fetchWithRetry`, então erro de rede no POST do chat propaga como `TypeError`. Isso é tratado pelo `useChatMessages.sendViaRest` com try/catch (substitui por mensagem amigável).
3. O overlay com `HttpError: Failed to fetch` originado em `base.ts:207` portanto **não vem do POST do chat** — vem de outra chamada `fetchWithRetry` que executou no mesmo momento (sidebar de conversas, lista de candidatos, jobs, etc.) cujo consumidor **não tratou** o `HttpError(0, transientNetworkError=true)`.
4. Consumidores que tratam corretamente: `useCandidatesData.handleSecondaryFailure`, `useTriagemMessages` — usam `isTransientNetworkError(err)` para silenciar.
5. Consumidores que provavelmente _não_ tratam (a verificar): vários hooks que chamam `fetchWithRetry` listados em `grep fetchWithRetry plataforma-lia/src` (jobs-api, email-api, candidates-api, misc-api, RecruitmentJourneyConfig, useScreeningConfigManagerCore, candidate-search). Qualquer deles que `await` sem `catch` apropriado causa unhandled rejection → overlay.

### Causa raiz
- O cliente HTTP _faz_ a coisa certa empacotando o erro como `HttpError(0, transientNetworkError=true)`, mas **o tratamento desse erro não é uniforme entre os consumidores**. Há call sites que disparam `fetchWithRetry` em paralelo (sidebar de conversas, lista de candidatos pré-carregada na rota `/funil-talentos`) e propagam o erro como _unhandled rejection_ → o dev overlay do Next captura e mostra o stack `base.ts:207`.
- Não há helper centralizado tipo `runQueryQuiet(fn)` que silencie `HttpError.transientNetworkError` para chamadas de background.
- O overlay aparece apenas em dev (Task #728 já evita o caso bruto); em produção fica como log silencioso.

### Evidências
- `base.ts:199-208` — origem confirmada do erro.
- `chat-api.ts:17-81` — usa `fetch` cru, não passa por `fetchWithRetry`.
- 19 arquivos do front usam `fetchWithRetry`; nem todos checam `isTransientNetworkError`.

### Recomendação (alto nível)
- Criar utilitário compartilhado (ex.: `withTransientNetworkSilence`) e aplicar em todos os hooks que rodam fetches em background no carregamento da página.
- Auditar a lista de 19 consumidores de `fetchWithRetry` e classificá-los: foreground (mostra erro ao usuário) vs. background (silencia se transient).
- Não migrar `chat-api.ts` para `fetchWithRetry` agora — o `useChatMessages` já trata; manter consistência separada.

---

## Distinção por tipo (conforme pedido na task)

| Problema | Categoria |
|---|---|
| P1 — Localização perdida | Extração de filtros (front + tool schema) |
| P2 — "pode sim" → cultura | Roteamento/intent (PreConditionChecker + pending offer sem âncora de contexto) |
| P3 — Correção virou query | Roteamento/intent (negation detector raso + extrator posicional) |
| P4 — Overlay HttpError | Resiliência de rede no front (consumidores não-uniformes) |

---

## Próximas tarefas sugeridas (priorizadas)

> Apenas títulos curtos. Cada item deve virar uma task separada.

**Prioridade ALTA**
1. Não trocar o agente principal quando o usuário tem intent operacional ativo (PreConditionChecker côté contexto).
2. Vincular pending actions / ofertas proativas a um `context_topic` antes de aceitar confirmação.
3. Validar a query extraída pelo ActionExecutor antes de chamar o tool de busca (rejeitar negações/frases sem termo operacional).
4. Expandir o detector de correção/negação para frases naturais em PT-BR ("estamos falando de…", "esquece…", "voltando…").

**Prioridade MÉDIA**
5. Normalizar entrada de cidade no extrator do front: aceitar `em <cidade>` e o sufixo `capital`.
6. Reescrever `description`/`parameters` da tool `search_candidates` exposta ao LLM enfatizando suporte a `location_city`/`location_state`.
7. Adicionar regra no system prompt: proibir afirmar limitações que não existam nas tools disponíveis.
8. Criar utilitário `withTransientNetworkSilence` e aplicar nos hooks de background que usam `fetchWithRetry`.

**Prioridade BAIXA**
9. Cobrir com testes o fluxo "busca → oferta proativa de cultura → correção" (regression de P2/P3 juntos).
10. Telemetria: contar quantas vezes o ActionExecutor envia query vazia / suspeita ao tool de busca.

---

## Out of scope desta auditoria
Nenhuma alteração de código, prompt, schema ou UI foi feita. Nenhum teste novo foi criado.
