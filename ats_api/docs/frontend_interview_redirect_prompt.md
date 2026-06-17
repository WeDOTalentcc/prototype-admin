# Frontend: Redirecionar Voz/Telefone para /interviews/

## Contexto

A pagina `/evaluations/[id]/[uid].vue` exibe 3 botoes: "Chat por Texto", "Conversa por Voz" e "Ligacao Telefonica". Atualmente, voz e telefone abrem o `VoiceRoom` dentro da mesma pagina de evaluation. O correto e redirecionar para `/interviews/{account_uid}/{token}`, que e o sistema real-time de entrevista por voz (WebSocket + Gemini Live Audio).

## O que mudou na API

O endpoint `GET /v1/evaluations/{account_uid}/{evaluation_candidate_uid}` agora retorna um campo novo: `interview_sessions`.

### Exemplo de resposta:

```json
{
  "evaluation": { "notification_channels": ["internal", "voice", "phone"], ... },
  "evaluation_candidate": { ... },
  "candidate": { "name": "Joao" },
  "company": { "name": "WeDO Talent" },
  "job": { "title": "Senior Software Engineer" },
  "questions": [...],
  "interview_sessions": [
    {
      "interview_type": "voice",
      "token": "725f4e1c-8aec-4e3a-81f7-b4f197b3d0cc",
      "url": "/interviews/6b61fa80-b239-489a-b102-4a54b660ebb1/725f4e1c-8aec-4e3a-81f7-b4f197b3d0cc",
      "status": "pending",
      "expires_at": "2026-03-26T19:53:00.000Z"
    },
    {
      "interview_type": "phone",
      "token": "c70f90e5-2ea6-4302-a09c-c02511ee7c70",
      "url": "/interviews/6b61fa80-b239-489a-b102-4a54b660ebb1/c70f90e5-2ea6-4302-a09c-c02511ee7c70",
      "status": "pending",
      "expires_at": "2026-03-26T19:53:00.000Z"
    }
  ]
}
```

## Logica de renderizacao dos botoes

| Canal | Condicao para exibir | Acao ao clicar |
|-------|---------------------|----------------|
| Chat por Texto | `notification_channels` inclui `"internal"` OU esta vazio | `begin('text')` — abre `EvaluationWrapper` na mesma pagina (comportamento atual) |
| Conversa por Voz | `interview_sessions` contem item com `interview_type === "voice"` | `navigateTo(session.url)` — redireciona para `/interviews/{account_uid}/{token}` |
| Ligacao Telefonica | `interview_sessions` contem item com `interview_type === "phone"` | `navigateTo(session.url)` — redireciona para `/interviews/{account_uid}/{token}` |

**Regra importante**: A presenca do botao de voz/telefone agora depende de existir uma `InterviewSession` ativa (status `pending` ou `active`, nao expirada), nao mais do `notification_channels`.

## Alteracoes necessarias no `[uid].vue`

### 1. Injetar `interview_sessions` do layout

O layout de evaluations ja faz o fetch da API e injeta os dados. Adicionar:

```ts
const interviewSessions = inject('interview_sessions', ref([]))
```

### 2. Atualizar computed properties dos botoes

```ts
const channels = computed(() => evaluation_candidate.value?.notification_channels || [])

const hasInternal = computed(() =>
  channels.value.length === 0 || channels.value.includes('internal')
)

const voiceSession = computed(() =>
  interviewSessions.value?.find(s => s.interview_type === 'voice' && s.status !== 'expired')
)

const phoneSession = computed(() =>
  interviewSessions.value?.find(s => s.interview_type === 'phone' && s.status !== 'expired')
)

const hasVoice = computed(() => !!voiceSession.value)
const hasPhone = computed(() => !!phoneSession.value)
```

### 3. Atualizar funcao `begin()`

```ts
function begin(selectedMode: 'text' | 'voice' | 'phone') {
  if (selectedMode === 'voice' && voiceSession.value) {
    navigateTo(voiceSession.value.url)
    return
  }

  if (selectedMode === 'phone' && phoneSession.value) {
    navigateTo(phoneSession.value.url)
    return
  }

  if (selectedMode === 'text') {
    mode.value = selectedMode
    start.value = true
  }
}
```

### 4. Remover o phoneStep e o VoiceRoom para voz/telefone

- Remover o bloco `<div v-if="phoneStep">` (input de telefone) — o telefone sera coletado na pagina de `/interviews/`
- Remover `<div v-if="start && mode === 'voice'">` com `VoiceRoom` — voz agora vai para `/interviews/`
- Remover `<div v-if="start && mode === 'phone'">` com `VoiceRoom channel="phone"` — telefone agora vai para `/interviews/`
- Manter apenas `<div v-if="start && mode === 'text'">` com `EvaluationWrapper`

### 5. Atualizar o layout de evaluations

No layout que faz o fetch da API (`layouts/evaluations.vue` ou similar), adicionar o provide:

```ts
const interviewSessions = ref(data.interview_sessions || [])
provide('interview_sessions', interviewSessions)
```

## URLs finais

- **Chat**: permanece em `/evaluations/{account_uid}/{ec_uid}` (mesma pagina)
- **Voz**: redireciona para `/interviews/{account_uid}/{voice_token}`
- **Telefone**: redireciona para `/interviews/{account_uid}/{phone_token}`

## Pagina de interviews

A pagina `/interviews/[account_uid]/[token].vue` ja suporta:
- **Lobby** com informacoes do candidato e da vaga
- **Voice room** com WebSocket + Gemini Live Audio
- **Phone** com chamada via Twilio
- O `interview_type` da session determina qual modo a pagina renderiza
- O telefone do candidato ja esta no `candidate_context.mobile_phone` da session
