# Integracao Teams x Multi-Agente IA

Fluxo completo de conversa bidirecional entre Microsoft Teams e o sistema multi-agente.

---

## Visao Geral

```
┌──────────────┐     webhook      ┌──────────────┐    RabbitMQ     ┌──────────────┐
│  MS Teams    │ ───────────────→ │  Rails API   │ ──────────────→ │  Multi-Agent │
│  (recruiter) │                  │              │                  │  (Python)    │
│              │ ←─────────────── │              │ ←────────────── │              │
└──────────────┘   Graph API      └──────────────┘  messages_      └──────────────┘
                   send_message                     processed
```

---

## Fluxo IDA: Teams → Agente

```
1. Recruiter envia mensagem no Teams (chat 1:1 com LIA)
        │
2. Microsoft Graph envia webhook notification
        │
3. POST /v1/webhooks/teams_chat
        │
4. TeamsWebhookController#create
   ├── Extrai chat_id da notification
   └── Encontra TeamsChatSubscription ativa
        │
5. TeamsMessageIngestionService.call(subscription)
   ├── Busca 5 ultimas mensagens via Graph API
   ├── Filtra apenas mensagens do recruiter (exclui LIA)
   └── Para cada mensagem nova:
        │
6. Message.create!
   ├── entity: ROLE_USER
   ├── status: STATUS_NOT_ANSWERED
   ├── reference: recruiter (User)
   └── metadata:
       ├── source: "teams"
       ├── hub_mode: true
       ├── session_id: "teams_{chat_id}"
       ├── teams_message_id: "{msg_id}"
       ├── teams_chat_id: "{chat_id}"
       ├── teams_lia_user_id: {lia_user_id}
       └── received_at: "{datetime}"
        │
7. after_create_commit → publish_message_event
   ├── no_reply NAO esta setado → continua
   ├── entity != ROLE_SYSTEM → continua
   └── MessagePublishJob.perform_later(message_id, tenant)
        │
8. execute_publish_event → publish_for_user → publish_generic_user_message
   └── Payload para RabbitMQ inclui:
       ├── message_id, content, user_id, account_id
       ├── metadata (com source, teams_chat_id, etc)
       ├── hub_mode: true (extraido do metadata)
       ├── session_id: "teams_{chat_id}" (extraido do metadata)
       └── one_time_token (para callbacks)
        │
9. RabbitMQ: messages_exchange → messages_created
        │
10. Python RecruiterAgentWorker.handle_message()
    ├── Detecta hub_mode: true
    ├── Usa session_id para manter continuidade
    └── Roteia via HubOrchestrator
```

### Pontos-chave da IDA

- **Session continuity**: `session_id = "teams_{chat_id}"` garante que todas as mensagens do mesmo chat Teams mantenham o mesmo session no hub
- **Hub mode**: Todas as mensagens de Teams entram via HubOrchestrator (pode rotear para qualquer dominio)
- **Sem loop**: `from_recruiter?` filtra mensagens do LIA, entao respostas enviadas ao Teams nao re-disparam o fluxo
- **Duplicata**: `already_stored?` verifica `teams_message_id` para nao processar a mesma mensagem duas vezes

---

## Fluxo VOLTA: Agente → Teams

```
1. Python agent processa e envia resposta para RabbitMQ
   └── Queue: messages_processed
        │
2. ProcessWorker.work(raw_payload)
   ├── Encontra mensagem original
   └── handle_standard_response(message, data)
        │
3. Preserva teams_context da mensagem original
   └── teams_context = { source, teams_chat_id, teams_lia_user_id, session_id }
        │
4. Cria Message de resposta (ROLE_SYSTEM)
   ├── content: resposta do agente
   └── metadata: response_metadata + teams_context
        │
5. Broadcast via ActionCable (frontend web recebe em tempo real)
        │
6. from_teams?(teams_context) == true
   └── forward_to_teams(new_message)
        │
7. Microsoft::TeamsResponseJob.perform_async(message_id, tenant)
        │
8. TeamsResponseJob#perform
   ├── Encontra mensagem
   ├── Extrai teams_chat_id e teams_lia_user_id do metadata
   ├── Encontra LIA user com ms_access_token
   ├── Strip HTML do content (Teams recebe texto limpo)
   └── MicrosoftService::Teams.send_message(
         user: lia_user,
         content: texto_limpo,
         content_type: "text",
         chat_id: teams_chat_id
       )
        │
9. Recruiter ve a resposta no Teams chat
```

### Pontos-chave da VOLTA

- **Assincrono**: Envio ao Teams e via Sidekiq job com retry (3 tentativas)
- **Dual delivery**: Resposta vai tanto para ActionCable (frontend) quanto para Teams
- **HTML strip**: Teams recebe texto puro, sem tags HTML do template de mensagem
- **LIA user**: A mensagem no Teams e enviada como o usuario LIA (bot), usando o `ms_access_token` dele
- **Metadata preservado**: A nova mensagem (ROLE_SYSTEM) carrega `teams_chat_id` e `teams_lia_user_id` no metadata para possibilitar o reenvio

---

## Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `app/services/microsoft_service/teams_message_ingestion_service.rb` | Removido `no_reply: true`, adicionado `hub_mode`, `session_id`, `teams_lia_user_id` ao metadata |
| `app/models/message.rb` | `build_generic_message_payload` agora promove `hub_mode` e `session_id` do metadata para campos top-level no payload RabbitMQ |
| `app/workers/message_worker/process_worker.rb` | Preserva `teams_context` da mensagem original, propaga para resposta, enfileira `TeamsResponseJob` |
| `app/jobs/microsoft/teams_response_job.rb` | **Novo** — envia resposta do agente para o Teams via Graph API |

---

## Estrutura da Mensagem no RabbitMQ (IDA)

```json
{
  "message_id": 12345,
  "content": "quantas vagas abertas temos?",
  "user_id": 42,
  "user_name": "Maria Recruiter",
  "account_id": 1,
  "hub_mode": true,
  "session_id": "teams_19:abc123@thread.v2",
  "metadata": {
    "source": "teams",
    "hub_mode": true,
    "session_id": "teams_19:abc123@thread.v2",
    "teams_message_id": "1234567890",
    "teams_chat_id": "19:abc123@thread.v2",
    "teams_lia_user_id": 99,
    "received_at": "2026-03-05T10:30:00Z"
  },
  "one_time_token": "ott_xyz",
  "reference_type": "User",
  "reference_id": 42,
  "entity": 1,
  "status": 0,
  "workspace_id": 0,
  "content_history": [],
  "created_at": "2026-03-05T10:30:05-03:00"
}
```

---

## Estrutura da Resposta no RabbitMQ (VOLTA)

O Python agent envia para `messages_processed`:

```json
{
  "original_message_id": 12345,
  "user_reference_type": "User",
  "user_reference_id": 42,
  "response": {
    "message": "Voce tem 80 vagas abertas no momento...",
    "content_format": "plain_text",
    "api_calls": [],
    "no_reply": false
  },
  "metadata": {}
}
```

O ProcessWorker cria a Message de resposta com metadata:

```json
{
  "message": "Voce tem 80 vagas abertas no momento...",
  "source": "teams",
  "teams_chat_id": "19:abc123@thread.v2",
  "teams_lia_user_id": 99,
  "session_id": "teams_19:abc123@thread.v2"
}
```

---

## Cenarios de Conversa

### Conversa simples

```
Teams:     "quantas vagas abertas?"
→ Agent:   hub_mode, session_id=teams_19:abc
→ Resposta: "Voce tem 80 vagas abertas"
→ Teams:   recruiter ve a resposta no chat
```

### Conversa com continuidade (session)

```
Teams:     "liste as vagas de SP"           session_id=teams_19:abc
→ Agent:   retorna lista de 15 vagas
→ Teams:   "e as urgentes?"                 session_id=teams_19:abc (mesmo!)
→ Agent:   hub entende contexto, filtra urgentes de SP
→ Teams:   recruiter ve resposta filtrada
```

### Clarificacao (pending action)

```
Teams:     "abra a vaga que estou trabalhando"
→ Agent:   detecta ambiguidade, retorna needs_clarification
→ Teams:   "Encontrei 2 vagas: 1) Dev Python 2) QA Senior. Qual?"
→ Teams:   recruiter responde "a primeira"    (mesmo session_id)
→ Agent:   resolve pending_action, abre vaga Dev Python
→ Teams:   "Aqui estao os detalhes da vaga Dev Python..."
```

---

## Protecao contra Loop

1. **Webhook recebe notificacao** de nova mensagem no chat
2. **TeamsMessageIngestionService** busca ultimas mensagens
3. **`from_recruiter?`** filtra: se sender_email == lia_email → descarta
4. Respostas enviadas pelo LIA ao Teams sao automaticamente ignoradas
5. **`already_stored?`** previne duplicatas por `teams_message_id`

Nao ha risco de loop infinito.
