# Frontend: Página de Entrevista por Voz (Interview Page)

## Rota do Frontend

Criar a página em:

```
/interviews/:account_uid/:token
```

**Exemplo de URL:**
```
http://localhost:3000/interviews/abc123uid/20368a55-93be-4fa0-a9ec-37860bef3e04
```

## API Backend (GET)

```
GET /v1/:account_uid/interview/:token
```

**Resposta 200:**
```json
{
  "token": "20368a55-93be-4fa0-a9ec-37860bef3e04",
  "status": "pending",
  "interview_type": "voice",
  "duration_minutes": 30,
  "language": "pt-BR",
  "company_name": "Talenses Group",
  "job_title": "Senior Software Engineer #4",
  "candidate_name": "Anderson Victhor",
  "questions_count": 3,
  "expires_at": "2026-03-13T23:03:12Z",
  "interviewer_name": "Lia"
}
```

**Resposta 410 (expirado/usado):**
```json
{
  "error": "expired",
  "message": "This interview link has expired or has already been used."
}
```

**Resposta 404:** token ou account_uid inválido.

## Parâmetros da Rota

| Param | Fonte | Descrição |
|---|---|---|
| `account_uid` | URL path | UID da conta (multi-tenant) |
| `token` | URL path | UUID da sessão de entrevista |

## Fluxo da Página

1. Extrair `account_uid` e `token` dos params da rota
2. `GET /v1/:account_uid/interview/:token`
3. Se **200** → renderizar tela de pré-entrevista com dados retornados
4. Se **410** → mostrar tela de "Link Expirado"
5. Se **404** → mostrar tela de "Link Inválido"

## Exemplo Nuxt (pages)

Criar arquivo: `pages/interviews/[account_uid]/[token].vue`

```vue
<script setup>
const route = useRoute()
const { account_uid, token } = route.params

const { data, error } = await useFetch(
  `/api/v1/${account_uid}/interview/${token}`
)
</script>
```

## Mudança no Backend

A URL pública gerada pelo backend agora segue o formato:

```
{FRONT_URL}/interviews/{account_uid}/{token}
```

Antes era `/interview/:token` (sem account_uid) — isso foi corrigido porque o frontend precisa do `account_uid` para chamar a API pública corretamente.
