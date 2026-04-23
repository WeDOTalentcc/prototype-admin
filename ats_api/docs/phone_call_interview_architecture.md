# Entrevista por Ligação Telefônica — Arquitetura de Integração

## Conclusão Principal

O sistema de entrevista por ligação **não precisa de um fluxo separado**. Ele reutiliza 100% da infraestrutura existente de interview sessions. A única diferença é que, no momento da entrevista, o candidato escolhe "telefone" em vez de "navegador", e o **front chama o Interview AI** que por sua vez liga pro candidato via Twilio.

O Rails praticamente não muda. O Interview AI já tem os endpoints prontos. O grosso do trabalho é no front-end.

---

## Fluxo Atual (Voz pelo Navegador)

```
Recrutador                Rails API                    Front (Candidato)           Interview AI
    |                         |                              |                          |
    |-- POST /interview       |                              |                          |
    |   sessions (create) --->|                              |                          |
    |                         |-- email com link ----------->|                          |
    |                         |                              |                          |
    |                         |<-- GET /interview/:token ----|                          |
    |                         |--- config (questions, job) ->|                          |
    |                         |                              |                          |
    |                         |                              |-- WebSocket direto ----->|
    |                         |                              |   (áudio bidirecional)   |
    |                         |                              |                          |
    |                         |<-- POST /answer -------------|   (via Interview AI) --->|
    |                         |<-- POST /complete -----------|                          |
```

## Fluxo Proposto (Ligação Telefônica)

```
Recrutador                Rails API                    Front (Candidato)           Interview AI       Twilio
    |                         |                              |                          |               |
    |-- POST /interview       |                              |                          |               |
    |   sessions (create) --->|                              |                          |               |
    |                         |-- email com MESMO link ----->|                          |               |
    |                         |                              |                          |               |
    |                         |<-- GET /interview/:token ----|                          |               |
    |                         |--- config + candidate.phone->|                          |               |
    |                         |                              |                          |               |
    |                         |             [candidato escolhe "Por Telefone"]          |               |
    |                         |             [confirma número, clica "Iniciar"]          |               |
    |                         |                              |                          |               |
    |                         |<-- POST /start --------------|                          |               |
    |                         |                              |                          |               |
    |                         |                              |-- POST /api/call ------->|               |
    |                         |                              |   {token, account_uid,   |               |
    |                         |                              |    phone}                |               |
    |                         |                              |                          |               |
    |                         |<-- GET /interview/:token ----|------(config)----------->|               |
    |                         |                              |                          |-- liga ------->|
    |                         |                              |<-- {call_sid} -----------|               |
    |                         |                              |   "Ligando..."           |               |
    |                         |                              |                          |    [candidato  |
    |                         |                              |                          |     atende]    |
    |                         |                              |                          |               |
    |                         |                              |          [Lia conduz entrevista por voz via Twilio]
    |                         |                              |                          |               |
    |                         |<-- POST /answer -------------|   (Interview AI envia)   |               |
    |                         |<-- POST /complete -----------|                          |               |
```

---

## O que muda em cada camada

### Rails API — Mudanças mínimas

**1. Incluir `mobile_phone` no response do `InterviewController#show`**

O front precisa do telefone do candidato para pré-preencher o campo. Hoje o `build_candidate_context` não retorna telefone. Adicionar:

```ruby
# app/controllers/v1/interview_controller.rb
def build_candidate_context
  ctx = @session.candidate_context || {}
  {
    name: ctx["name"],
    phone: @session.candidate&.mobile_phone, # ← ADICIONAR
    current_company: ctx["current_company"],
    current_role: ctx["role_name"],
    experience_years: ctx["position_level"]
  }
end
```

**2. Salvar `mobile_phone` no snapshot do `InterviewSession`**

Para que o Interview AI tenha acesso ao telefone sem precisar buscar no banco:

```ruby
# app/models/interview_session.rb → snapshot_contexts
self.candidate_context = {
  name: candidate.name,
  email: candidate.email,
  mobile_phone: candidate.mobile_phone, # ← ADICIONAR
  current_company: candidate.current_company,
  role_name: candidate.role_name,
  position_level: candidate.position_level
}.compact
```

**3. `interview_type: "phone"` já está no INTERVIEW_TYPES**

Já adicionamos `"phone"` ao array de tipos válidos. O recrutador pode criar a session com `interview_type: "phone"` ou deixar como `"voice"` — o candidato escolhe na hora.

**Nenhum endpoint novo é necessário no Rails.** Os endpoints existentes cobrem tudo:

| Endpoint                                       | Quem chama           | Para quê                         |
| ---------------------------------------------- | -------------------- | -------------------------------- |
| `GET /interview/:account_uid/:token`           | Front + Interview AI | Carregar config da entrevista    |
| `POST /interview/:account_uid/:token/start`    | Front                | Marcar entrevista como "active"  |
| `POST /interview/:account_uid/:token/answer`   | Interview AI         | Enviar resposta de cada pergunta |
| `POST /interview/:account_uid/:token/complete` | Interview AI         | Finalizar com relatório + nota   |
| `POST /interview/:account_uid/:token/result`   | Interview AI         | Enviar score final               |

---

### Interview AI (Python) — Nada muda

Todos os endpoints já estão implementados:

| Endpoint                  | Função                                                                       |
| ------------------------- | ---------------------------------------------------------------------------- |
| `POST /api/call`          | Recebe `{token, account_uid, phone}`, busca config no Rails, liga via Twilio |
| `POST /api/twilio/twiml`  | Twilio chama quando a ligação conecta, retorna TwiML com stream              |
| `POST /api/twilio/status` | Webhook de status da chamada                                                 |
| `WS /ws/twilio`           | Stream bidirecional áudio Twilio ↔ Gemini Live                               |

O Interview AI já:

1. Busca as perguntas no Rails via `GET /interview/:account_uid/:token`
2. Liga pro candidato via Twilio
3. Conduz a entrevista com Gemini Live Audio
4. Posta cada resposta via `POST /answer`
5. Finaliza via `POST /complete` com relatório

---

### Front-end — Onde está o trabalho

**Tela de entrevista (`/interviews/:account_uid/:token`):**

1. Ao carregar, o front já faz `GET /interview/:account_uid/:token`
2. Mostrar duas opções:
   - **"Pelo Navegador"** → fluxo atual (WebSocket com Gemini)
   - **"Por Telefone"** → fluxo novo (Twilio)

3. Se candidato escolhe "Por Telefone":
   - Mostrar campo de telefone pré-preenchido com `candidate.phone`
   - Botão "Iniciar por Telefone"
   - Ao clicar:

     ```javascript
     // 1. Notificar Rails que a entrevista começou
     await fetch(`/interview/${accountUid}/${token}/start`, { method: "POST" });

     // 2. Chamar Interview AI para iniciar ligação
     const res = await fetch(`${INTERVIEW_AI_URL}/api/call`, {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({
         token,
         account_uid: accountUid,
         phone: phoneNumber,
       }),
     });
     const { call_sid } = await res.json();
     ```

   - Mostrar feedback: "Ligando para seu celular..." → "Atenda a chamada"
   - Polling no Rails para saber quando completou:
     ```javascript
     const poll = setInterval(async () => {
       const res = await fetch(`/interview/${accountUid}/${token}`);
       const data = await res.json();
       if (data.status === "completed" || data.status === "scored") {
         clearInterval(poll);
         showCompletionScreen(data);
       }
     }, 5000);
     ```

---

## Diagrama de Comunicação Simplificado

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   FRONT-END                                                             │
│   /interviews/:account_uid/:token                                       │
│                                                                         │
│   ┌──────────────────┐     ┌──────────────────┐                         │
│   │  Pelo Navegador  │     │  Por Telefone     │                        │
│   │  (WebSocket)     │     │  (Twilio Call)    │                        │
│   └────────┬─────────┘     └────────┬──────────┘                        │
│            │                        │                                   │
└────────────┼────────────────────────┼───────────────────────────────────┘
             │                        │
             │                        │  POST /api/call {token, account_uid, phone}
             │                        │
             ▼                        ▼
┌────────────────────────┐  ┌─────────────────────────────────────────────┐
│                        │  │                                             │
│   INTERVIEW AI         │  │   INTERVIEW AI                              │
│   (WebSocket mode)     │  │   (Twilio mode)                             │
│                        │  │                                             │
│   Gemini Live ↔ Audio  │  │   1. GET config from Rails                  │
│   via browser WebSocket│  │   2. Twilio calls.create(phone)             │
│                        │  │   3. Twilio → TwiML → Media Stream          │
│                        │  │   4. Stream áudio ↔ Gemini Live             │
│                        │  │   5. POST /answer para cada pergunta        │
│                        │  │   6. POST /complete com relatório            │
│                        │  │                                             │
└───────────┬────────────┘  └────────────────────┬────────────────────────┘
            │                                    │
            │  POST /answer, /complete           │  POST /answer, /complete
            │                                    │
            ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   RAILS API                                                             │
│                                                                         │
│   InterviewController (público, sem auth, token-based)                  │
│                                                                         │
│   GET  /interview/:account_uid/:token          → config                 │
│   POST /interview/:account_uid/:token/start    → marca active           │
│   POST /interview/:account_uid/:token/answer   → salva Answer           │
│   POST /interview/:account_uid/:token/complete → finaliza + relatório   │
│   POST /interview/:account_uid/:token/result   → score final            │
│                                                                         │
│   Mesmos endpoints para AMBAS as modalidades.                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Por que funciona sem mudanças estruturais

1. **Mesma InterviewSession** — O recrutador cria a session normalmente (pode ser `voice` ou `phone`, ou até deixar genérico). O token é o mesmo.

2. **Mesmo link de email** — O candidato recebe `https://app.wedotalent.cc/interviews/{account_uid}/{token}`. A escolha de modalidade é na hora.

3. **Mesmo InterviewController** — O Interview AI (Python) usa os mesmos endpoints de callback (`/answer`, `/complete`) independente de ser via browser WebSocket ou Twilio. Para o Rails, não faz diferença como o áudio chegou.

4. **Interview AI já faz tudo** — O `/api/call` já existe, já busca config no Rails, já liga via Twilio, já posta as respostas de volta.

---

## Mudanças necessárias no Rails (apenas 2)

### 1. Expor telefone no `InterviewController#show`

```ruby
# app/controllers/v1/interview_controller.rb
def build_candidate_context
  ctx = @session.candidate_context || {}
  {
    name: ctx["name"],
    phone: ctx["mobile_phone"] || @session.candidate&.mobile_phone,
    current_company: ctx["current_company"],
    current_role: ctx["role_name"],
    experience_years: ctx["position_level"]
  }
end
```

### 2. Salvar `mobile_phone` no snapshot

```ruby
# app/models/interview_session.rb → snapshot_contexts
self.candidate_context = {
  name: candidate.name,
  email: candidate.email,
  mobile_phone: candidate.mobile_phone,
  current_company: candidate.current_company,
  role_name: candidate.role_name,
  position_level: candidate.position_level
}.compact
```

---

## Variável de ambiente que o Front precisa

O front precisa saber o URL do Interview AI para chamar `/api/call`:

```env
INTERVIEW_AI_URL=https://interview-ai.wedotalent.com   # produção
INTERVIEW_AI_URL=http://localhost:8001                  # desenvolvimento
```

O Rails já tem `INTERVIEW_AI_BASE_URL` configurado, mas quem chama o `/api/call` é o **front**, não o Rails.

---

## E o interview_type?

Duas abordagens possíveis:

**Opção A — Candidato escolhe (recomendada)**

- Recrutador cria a session sem especificar tipo (ou `voice` como padrão)
- Na tela de entrevista, o candidato escolhe "Navegador" ou "Telefone"
- Se escolher telefone, o front atualiza o tipo via `POST /start` (podemos adicionar `interview_type` nesse endpoint)

**Opção B — Recrutador define**

- Recrutador cria com `interview_type: "phone"`
- Front mostra direto a tela de telefone, sem opção de navegador

A **Opção A** é melhor porque dá flexibilidade ao candidato e não exige mudança no fluxo do recrutador.

---

## Resumo de ações por equipe

| Equipe           | Ação                                                                                   | Esforço           |
| ---------------- | -------------------------------------------------------------------------------------- | ----------------- |
| **Rails**        | Adicionar `mobile_phone` ao snapshot e ao response do show                             | Mínimo (2 linhas) |
| **Front**        | Tela de escolha de modalidade + integração com `/api/call` + feedback visual + polling | Médio             |
| **Interview AI** | Nada — endpoints já prontos                                                            | Zero              |
| **Infra**        | Garantir que o front pode chamar o Interview AI (CORS, DNS)                            | Mínimo            |
