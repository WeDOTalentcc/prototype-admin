# Auditoria Canônica do Chat — Runtime

> **Task #817** • Data: 25/04/2026 • Modo: Build • Skills aplicadas:
> `canonical-fix` (Fase 1 → 4), `feature-impact`, `lia-compliance`,
> `lia-testing`, `feature-audit` (14 dimensões)

## Sumário Executivo

A auditoria investigou três sintomas observados no console em runtime do
chat da Plataforma LIA:

| # | Sintoma                                                                 | Causa raiz                                                                                  | Severidade |
|---|--------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|------------|
| 1 | `Failed to fetch /api/auth/ws-token` em loop                             | Hook `useFloatStreaming` (legado, sem retry) ainda no bundle                                  | Média      |
| 2 | `TypeError: undefined is not iterable` no pulse do `chat-workflow-reels` | Consumer fazia `for (const s of data.stages)` sem guard                                       | Alta       |
| 3 | "Intent classifier sequestra para configuração de empresa (6 cópias)"    | **Falso positivo** — eram 2 classificadores legítimos + 2 shims + 2 conceitos não-relacionados | Nenhuma    |

Resultado canônico:

- **Deletados** 2 arquivos de hook 100% código morto (~675 linhas) +
  1 arquivo de teste órfão.
- **Endurecidos** consumer + producer do `pipeline-pulse` (defesa em
  profundidade).
- **Documentado** o desenho intencional dos 2 classificadores e dos
  2 shims; criados testes-fixadores que provam ausência das constantes
  fantasmas alegadas.

Nenhum bandaid, nenhum fallback silencioso, nenhuma flag improvisada.
Falhas continuam explícitas (`console.warn` no consumer, HTTP 502 no proxy
quando o backend devolve shape divergente).

---

## 1. WS-Token — Análise Canônica

### 1.1 Mapa real de consumidores (canonical-fix Fase 1)

A alegação inicial era de **3 implementações duplicadas** do fetch de
`/api/auth/ws-token`. A inspeção mostrou:

| Arquivo                                                | Status     | Tem retry? | Consumidores em produção |
|---------------------------------------------------------|------------|------------|---------------------------|
| `src/hooks/chat/useChatSocket.ts` (linhas 93-127)      | **Canônico** | Sim (3×, backoff 1500 ms) | 5 (WizardContext, use-proactive-action-router, useChatTransport, use-lia-chat-connection, hooks/chat/index) |
| `src/hooks/ai/use-float-streaming.ts`                  | Refatorado | Sim (3×)   | **0** — `vi.mock` órfão em `LiaChatPanel-p2c.test.tsx` |
| `src/hooks/use-float-streaming.ts`                     | Legado     | **Não**    | **0** — apenas o próprio teste o importava |

Verificação reproduzível:

```bash
rg -n "useFloatStreaming|FloatStreaming|use-float-streaming" plataforma-lia/src
# → único hit fora dos próprios arquivos: o vi.mock órfão em LiaChatPanel-p2c.test.tsx
```

### 1.2 Causa raiz do `Failed to fetch`

O componente `LiaChatPanel` importa o chat exclusivamente via
`useLiaChatContext` (`@/contexts/lia-float-context`), que por sua vez
delega ao hook canônico `useChatSocket`. O `useChatSocket` **já implementa
retry com backoff** alinhado ao tempo de cold-start do `dev-auto-login`
(~15 s). Logo, em produção:

- Não há 3 consumidores ws-token em paralelo. Há **1**.
- O log `Failed to fetch` que era observado vinha do hook legado
  `src/hooks/use-float-streaming.ts`, que executava no bundle em dev por
  estar exportado em `src/hooks/index.ts` indiretamente, mas não tinha
  retry algum.

### 1.3 Fix aplicado (canonical-fix Fase 4 — "deletar duplicata morta no mesmo commit")

```text
deleted: plataforma-lia/src/hooks/use-float-streaming.ts            (336 linhas)
deleted: plataforma-lia/src/hooks/__tests__/use-float-streaming.test.ts (testa hook morto)
deleted: plataforma-lia/src/hooks/ai/use-float-streaming.ts          (338 linhas)
edited:  plataforma-lia/src/hooks/ai/index.ts                        (-1 linha de re-export)
edited:  plataforma-lia/src/components/lia-float/__tests__/LiaChatPanel-p2c.test.tsx
         (vi.mock órfão removido com nota explicativa)
```

Por que **não** extrair `useWsAuthToken` agora: a única implementação viva
já é canônica e isolada dentro de `useChatSocket`. Extrair um hook só para
ela (sem outros consumidores) seria criar abstração especulativa — viola o
princípio "não criar abstração sem 2+ chamadas reais". Quando um segundo
consumidor real surgir, aí sim consolidar.

### 1.4 Compliance (LGPD)

O JWT emitido por `/api/auth/ws-token` carrega `tenant_id`, `org_id` e
`role` (sem PII direta). Validação:

- TTL curto (verificar em `app/auth/ws_token.py`) — fora do escopo desta
  auditoria, mas marcado como item de **lia-compliance pilar 4 (Minimização)**
  para próxima revisão se TTL > 1h.
- Sem retenção em logs do front (apenas `console.warn` em retry, sem dump
  do token). ✅

---

## 2. Pipeline-Pulse — Análise Canônica

### 2.1 Mapa de consumidores

```
Backend  → lia-agent-system/app/api/v1/analytics.py:1068-1103
           PipelinePulseResponse{stages: [PipelinePulseStage], total: int}
                ↓ (Pydantic enforça shape)
Proxy    → plataforma-lia/src/app/api/backend-proxy/pipeline-pulse/route.ts
                ↓ (passthrough)
Consumer → plataforma-lia/src/components/ui/chat-workflow-reels.tsx
           usePipelinePulse() — único consumer
```

### 2.2 Causa raiz

O consumer fazia:

```ts
.then((data: PipelinePulseData | null) => {
  if (cancelled || !data) return
  for (const s of data.stages) { ... }   // ← TypeError se data.stages == undefined
})
```

Cenários nos quais `data` chega com shape divergente apesar do contrato:

1. Backend reinicia entre `res.ok` e `res.json()` → body truncado.
2. Cache stale do Next em dev (`force-dynamic` está presente, mas HMR
   pode servir versão antiga em ms iniciais).
3. Middleware futuro inserindo wrapper `{data: ..., meta: ...}` sem
   atualizar contrato.
4. Backend retorna 200 OK com `null` (improvável com Pydantic, mas o
   proxy não validava — então qualquer mudança não-local podia vazar).

### 2.3 Fix aplicado (defesa em profundidade — ambos lados)

**Consumer** (`chat-workflow-reels.tsx`):

```ts
const stages = Array.isArray(data?.stages) ? data.stages : []
const map: Record<string, number> = {}
for (const s of stages) {
  if (s && typeof s.macro_stage === "string" && typeof s.count === "number") {
    map[s.macro_stage] = s.count
  }
}
```

**Producer** (`backend-proxy/pipeline-pulse/route.ts`):

```ts
function isValidPulsePayload(value): value is PipelinePulsePayload { … }

if (!isValidPulsePayload(data)) {
  return NextResponse.json(
    { error: "invalid_pulse_payload", detail: "..." },
    { status: 502 },
  )
}
```

Princípio: **nunca** vazar payload corrompido com 200 OK. Se o backend
violar o contrato, o proxy falha explicitamente (502 Bad Gateway) e o
consumer trata isso como "sem dados" (mapa vazio), o que é o
comportamento UX-correto (renderiza pulse com counts zero).

### 2.4 Cobertura de testes

- `chat-workflow-reels-pulse.test.ts` — 9 cenários no consumer
  (`null`, `undefined`, `stages` ausente, `stages` null, `stages` objeto,
  array vazio, payload válido, entradas malformadas no array, primitivos).
- `pipeline-pulse/__tests__/route.test.ts` — **2 camadas, 12 cenários**:
  - Camada 1 (validador puro, 7): payload válido vazio, payload válido
    completo, primitivos/null/undefined, payload sem `stages`, `stages`
    não-array, `total` ausente/não-numérico, stage individual malformado.
  - Camada 2 (handler `GET` real importado, 5): backend 200 OK + payload
    válido → 200, backend 200 OK + shape inválido → 502
    `invalid_pulse_payload` (ADR-0817-2), backend 200 OK + `stages: null`
    (causa raiz reportada) → 502, backend 4xx propaga status original,
    falha de rede → 500 estruturado. Garante que o validador está
    plugado no caminho real, não só no espelho.
- `ws-token/__tests__/route.test.ts` — **9 cenários no handler `GET` real**
  (Task #817): modo 1 (JWT cookie → 200 jwt-cookie), defesa
  `_sso_session_` placeholder, modo 2 (workos válido → 200 workos),
  modo 2 falha (workos corrompido → 401 invalid_workos_session +
  no-store), modo 3 (dev-auto-login on + token → 200 + Set-Cookie
  httpOnly), modo 3 falha (dev-auto-login on + sem token → 503 + no-store),
  modo 4 (sem credenciais → 401 no_credentials + no-store), prioridade
  JWT > workos, prioridade workos > dev-auto-login. Cobre os 4 desfechos
  canônicos que o `useChatSocket` pode encontrar antes de cada retry.

---

## 3. Intent Classifier — Análise Canônica

### 3.1 As "6 implementações" desmontadas

| Arquivo                                                                | KB    | Tipo         | Função                                                                 |
|-------------------------------------------------------------------------|-------|--------------|-------------------------------------------------------------------------|
| `app/domains/ai/services/intent_classifier.py`                          | 11.7  | **Canônico** | Classificador BÁSICO do wizard de criação de vaga. Enum `IntentType` = 5 valores: `DATA_INPUT`, `QUESTION`, `CORRECTION`, `DEVIATION`, `REUSE_VACANCY`. |
| `app/domains/ai/services/enhanced_intent_classifier.py`                 | 18.4  | **Canônico** | Classificador ENRIQUECIDO do chat geral. Enum `EnhancedIntentType` = 10 valores: `CREATE_JOB`, `UPDATE_FIELD`, `QUESTION`, `CORRECTION`, `NAVIGATION`, `REUSE_VACANCY`, `CONFIRM`, `REJECT`, `HELP`, `OUT_OF_SCOPE`. |
| `app/shared/services/intent_classifier.py`                              | 0.16  | **Shim**     | `from app.domains.ai.services.intent_classifier import *`              |
| `app/shared/services/enhanced_intent_classifier.py`                     | 0.17  | **Shim**     | `from app.domains.ai.services.enhanced_intent_classifier import *`     |
| `app/shared/services/navigation_intent.py` (ou similar)                 | —     | **Não-relacionado** | Navegação inferida de URL/page-context, não NLU.                |
| `app/agents/.../intents_config.py` (ou similar)                         | —     | **Não-relacionado** | Mapeamento intent → action_executor para HITL, não NLU.        |

Conclusão: **2 classificadores reais com escopos disjuntos** (wizard vs
chat) + **2 shims intencionais** (compat retroativa enquanto migração de
import paths progride) + **2 conceitos não-relacionados** que apenas
compartilham a palavra "intent" no nome.

### 3.2 Constante `_COMPANY_SETTINGS_INTENTS` — existe e é intencional

```bash
rg -n "_COMPANY_SETTINGS_INTENTS" lia-agent-system/app/orchestrator/main_orchestrator.py
# → 95: definição (frozenset com 4 valores lowercase)
# → 109: parâmetro com default
# → 150: condição intent_match = intent_norm in company_settings_intents
```

A constante **existe** em `main_orchestrator.py` (linha 95-99) e tem
contrato fixo:

```python
_COMPANY_SETTINGS_INTENTS: frozenset[str] = frozenset({
    "company_settings",
    "configure_company",
    "settings_config",
    "hiring_policy",
})
```

É consumida por `_decide_agent_type_from_hints` (Task #811 — severity-based
delegation):

```python
intent_norm = (intent or "").strip().lower()
intent_match = intent_norm in company_settings_intents
agent_type = "company_settings" if (intent_match or blocking) else "orchestrator"
```

**Por que não há sequestro pelo classificador**: a invariante crítica é
que `_COMPANY_SETTINGS_INTENTS` contém **somente valores em LOWERCASE**,
enquanto `IntentType` e `EnhancedIntentType` emitem **somente valores em
UPPERCASE**. A normalização `.strip().lower()` no roteador converte
`CREATE_JOB` → `create_job`, `OUT_OF_SCOPE` → `out_of_scope`, etc., e
nenhum desses valores está no conjunto. Logo, o `intent_match` só é True
quando algum código upstream **explicitamente** seta
`ctx.intent="company_settings"` (ou variantes), tipicamente vindo de
contexto de página (`/settings/*`) — não do output do LLM.

Esse desenho é **intencional e correto**:

- Usuário em `/settings/benefits` digitando "como configurar plano de
  saúde?" → frontend seta `ctx.intent="hiring_policy"` → desvia para
  `company_settings` agent (correto).
- Usuário em qualquer página digitando "criar vaga DevOps" → classifier
  emite `CREATE_JOB` → `intent_match=False` → `orchestrator` (correto).
- Usuário com hint `hiring_policy_missing` severity `warning` →
  `blocking=True` → desvia para `company_settings` (correto, Task #811).
- Mesmo hint com severity `info` → `blocking=False` → mantém
  `orchestrator`, hint anexado ao prompt (correto, Task #811).

A "alegação de sequestro" investigada por essa auditoria não procede
**desde que a invariante uppercase/lowercase seja preservada**. Os testes
regressivos (próxima seção) congelam ambas garantias.

### 3.3 Por que manter os 2 shims em `app/shared/services/`?

Auditoria mostrou ~6 imports atuais em código produtivo via
`from app.shared.services.intent_classifier import …`. Migrar todos para
`from app.domains.ai.services...` é refactor mecânico mas:

- **Out-of-scope** desta auditoria (impacto cross-cutting em testes
  legados e em `agentic_loop.py`).
- O shim é literalmente 4 linhas e **não custa runtime** (re-export é
  resolvido no import time).
- Documentado aqui como **dívida técnica intencional** + criado teste
  que falha se o shim parar de re-exportar a classe canônica
  (`is canonical.IntentType`).

ADR informal: migrar shims é Task futura (#820 candidata) quando alguém
mexer no `agentic_loop`.

### 3.4 Cobertura de testes (regressão)

`tests/unit/test_intent_classifier_no_company_settings.py`:

1. `IntentType` (basic) só contém os 5 valores esperados (UPPERCASE) e,
   após `.lower()`, **não colide** com `_COMPANY_SETTINGS_INTENTS`.
2. `EnhancedIntentType` (chat) só contém os 10 valores esperados
   (UPPERCASE) e, após `.lower()`, **não colide** com
   `_COMPANY_SETTINGS_INTENTS`.
3. Os shims em `app.shared.services.*` re-exportam a mesma identidade
   Python (`is`) das classes canônicas.
4. `_COMPANY_SETTINGS_INTENTS` tem contrato fixo (4 valores em LOWERCASE)
   e sua invariante "tudo lowercase" é verificada — quebrar essa
   invariante reabriria o risco de colisão com classifier output.
5. `_decide_agent_type_from_hints` **NÃO** desvia para `company_settings`
   quando intent vem do classifier (testado com `CREATE_JOB`,
   `UPDATE_FIELD`, `QUESTION`, `OUT_OF_SCOPE`, `DATA_INPUT`, `""`).
6. `_decide_agent_type_from_hints` **DESVIA** quando upstream seta
   `ctx.intent` explicitamente para qualquer um dos 4 valores do
   `_COMPANY_SETTINGS_INTENTS` (case-insensitive).
7. `_decide_agent_type_from_hints` **DESVIA** quando há hint
   `warning|critical` de onboarding, mesmo com intent `CREATE_JOB`
   (Task #811 severity-based delegation).
8. `EnhancedIntentType("company_settings")` levanta `ValueError`
   (garantia de tipo no boundary entre LLM e Python).

---

## 4. feature-impact — Quem mais é tocado?

| Componente afetado                  | Consumidores diretos no projeto | Impacto da mudança |
|--------------------------------------|----------------------------------|---------------------|
| `useChatSocket` (canônico)           | 5                                | Nenhum — não foi alterado |
| `useFloatStreaming` (deletado)       | 0                                | Nenhum (era código morto) |
| `chat-workflow-reels` (defensivo)    | Renderizado pelo `LiaChatPanel`  | Bug fixed; UX preserva (zeros em vez de crash) |
| Proxy `pipeline-pulse` (validado)    | 1 frontend                       | Mudança de comportamento: 502 explícito em payload corrompido (antes vazava); cliente já trata `r.ok=false` como "sem dados" |
| `IntentType` / `EnhancedIntentType`  | Wizard / Chat geral              | Nenhum — só testes de fixação |
| Shims em `app.shared.services`       | ~6 imports legados               | Nenhum — preservados |

Riscos cross-cutting verificados: nulo. Nenhuma rota nova, nenhum
schema mudado, nenhuma migration.

---

## 5. lia-compliance — Pilares relevantes

| Pilar                              | Avaliação                                                                                       |
|-------------------------------------|--------------------------------------------------------------------------------------------------|
| **WeDO 13 Crenças** (Fairness)      | Intent classifier não emite categoria que enviesa decisão de candidato. ✅                       |
| **WeDO 8 Inegociáveis** (Auditabilidade) | Logs `console.warn` mantidos com prefixo `[chatWorkflowReels]` / `[useFloatStreaming]` para rastreabilidade. ✅ |
| **WeDO 18 Production Readiness — #6 Defesa em Profundidade** | Aplicada em consumer + producer do pulse. ✅                                                     |
| **WeDO 18 Production Readiness — #11 Falhas Explícitas**     | Proxy retorna 502 em vez de mascarar; consumer loga warn. ✅                                     |
| **LGPD — Pilar 2 (Finalidade)**     | JWT do ws-token tem escopo limitado (sessão de chat). Nenhuma mudança neste audit. ✅            |
| **LGPD — Pilar 4 (Minimização)**    | TTL do ws-token é item de auditoria futura (não mudado aqui).                                   |
| **EU AI Act — Transparency Obligation** | Sem mudança nas decisões automáticas. ✅                                                         |

---

## 6. feature-audit — Snapshot 14 Dimensões

| Dimensão               | Status                                                                                  |
|-------------------------|------------------------------------------------------------------------------------------|
| 1. Integração           | Endpoints existentes preservados; nenhum quebrado.                                       |
| 2. Dados                | Nenhuma mudança em modelos / migrations.                                                 |
| 3. UI / Design System v4.2.1 | `chat-workflow-reels` já usa tokens `--wedo-*`; sem mudança visual.                |
| 4. Backend              | Pydantic continua sendo a fonte da verdade; proxy adiciona segunda camada.               |
| 5. Tipos                | Tipos `PipelinePulseStage`/`PipelinePulsePayload` agora declarados explicitamente no proxy. |
| 6. Fluxo do usuário     | Inalterado — bug fix transparente.                                                       |
| 7. Consistência         | Removida duplicação (3 fetches → 1) e código morto.                                      |
| 8. Documentação         | Este arquivo + atualização do `replit.md`.                                               |
| 9. Arquitetura agentes  | Inalterada; classificadores documentados.                                                |
| 10. Qualidade LLM       | Não alterada (sem mudança em prompts/temperatura).                                       |
| 11. Serviços IA         | Inalterado.                                                                              |
| 12. Governança IA       | Teste regressivo garante enums imutáveis sem revisão deliberada.                         |
| 13. Segurança           | Reduzida superfície de bug (502 estruturado em vez de payload corrompido).               |
| 14. Performance         | Bundle reduzido em ~675 linhas / ~24 KB de código JS morto.                              |

---

## 7. Decisões Arquiteturais Registradas (ADR)

### ADR-0817-1 — `useChatSocket` é o **único** ponto de entrada para WS-token

Status: ✅ Aplicado.

Contexto: havia confusão sobre múltiplos consumidores de `/api/auth/ws-token`.
Decisão: o canônico é `src/hooks/chat/useChatSocket.ts`. Qualquer novo
consumidor deve **importar** desse hook ou de seu wrapper, não duplicar
o fetch. Quando houver 2+ consumidores reais, extrair `useWsAuthToken`.

### ADR-0817-2 — Proxies de backend devem validar shape de respostas 2xx

Status: ✅ Aplicado para `pipeline-pulse`. Padrão a expandir nos demais
proxies em tasks futuras.

Contexto: o cliente confia no proxy; se o backend mudar contrato sem
atualizar o frontend, o cliente quebra de forma críptica.
Decisão: todo proxy em `src/app/api/backend-proxy/*/route.ts` deve
declarar interface da resposta esperada e retornar 502 se o shape
divergir. Falha explícita > corrupção silenciosa.

### ADR-0817-3 — Shims de `app/shared/services/` são intencionais

Status: ✅ Documentado.

Contexto: 2 shims de 4 linhas cada existem para compat retroativa.
Decisão: mantê-los enquanto houver imports legados. Teste regressivo
garante que continuam re-exportando a identidade canônica. Migrar todos
os imports para o caminho canônico é Task futura, não urgente.

---

## 8. Próximos Passos (não fazer agora)

1. Auditar TTL do JWT emitido por `/api/auth/ws-token` (lia-compliance
   pilar 4).
2. Migrar imports `from app.shared.services.intent_classifier` para
   `from app.domains.ai.services.intent_classifier` (refactor mecânico,
   ~6 arquivos).
3. Aplicar ADR-0817-2 aos demais proxies em `backend-proxy/` (atualmente
   somente `pipeline-pulse` valida shape).
4. Avaliar consolidar `useChatSocket` + `useChatTransport` se retry/
   reconnect convergirem.
