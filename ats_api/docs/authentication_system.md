# Sistema de Autenticação — WeDO Talent ATS

> Guia completo dos fluxos de login, SSO, Microsoft, tokens de serviço e integração via extensões.

---

## Visão Geral

O sistema suporta múltiplos métodos de autenticação, configuráveis por conta (`Account`):

| Método | Endpoint Base | Quando Usar |
|--------|--------------|-------------|
| **Email + Senha** | `POST /v1/sessions` | Login tradicional |
| **WorkOS SSO** | `GET /v1/workos/login_url` | Microsoft Entra ID, Google, Okta, SAML |
| **Microsoft Direto** | `GET /v1/users/microsoft_graph_auth/login_url` | Login via Microsoft + Graph API |
| **OAuth (Service)** | `POST /v1/oauth/token` | Serviço-a-serviço (API clients) |
| **OTT (Agent)** | `POST /v1/agent_tokens/exchange` | Agente Python troca OTT por service token |

### Configuração por Conta

Cada `Account` define os métodos permitidos via `auth_config` (jsonb):

```json
{
  "password_login_enabled": true,
  "microsoft_sso_enabled": true,
  "google_sso_enabled": false
}
```

**Antes de exibir a tela de login**, consulte os métodos disponíveis para o email do user:

```
GET /v1/workos/sso_options?email=usuario@empresa.com
```

**Response:**

```json
{
  "sso_enabled": true,
  "providers": [
    {
      "id": "microsoft_entra_id",
      "name": "Microsoft",
      "login_url": "https://api.workos.com/sso/authorize?..."
    }
  ],
  "login_traditional_enabled": true
}
```

| Campo | Descrição |
|-------|-----------|
| `sso_enabled` | `true` se a conta tem SSO ativo (WorkOS habilitado + providers configurados) |
| `providers` | Lista de providers SSO disponíveis com URLs prontas para redirect |
| `login_traditional_enabled` | `true` se login email+senha é permitido. `false` quando SSO é forçado (`sso_enforced`) |

---

## 1. Login Email + Senha

### Fluxo Normal (sem MFA)

```
POST /v1/sessions
Content-Type: application/json

{
  "email": "usuario@empresa.com",
  "password": "senha123"
}
```

**Response (200):**

```json
{
  "user": {
    "id": 1,
    "name": "João Silva",
    "email": "usuario@empresa.com",
    "is_admin": true,
    "microsoft_connected": false,
    "business_name": "Empresa XYZ",
    "business_logo": "http://api.example.com/rails/active_storage/blobs/...",
    "account_id": 1,
    "sourcing_config": {}
  },
  "token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Erros possíveis:**

| Status | Body | Causa |
|--------|------|-------|
| `401` | `{"error": "Invalid email or password"}` | Email ou senha incorretos |
| `403` | `{"error": "Password login is not enabled for this account", "available_methods": ["microsoft_entra_id"]}` | Conta com SSO forçado |
| `429` | `{"error": "Muitas tentativas de login...", "rate_limited": true}` | 5+ tentativas em 60s (rate limit por IP) |

### Fluxo com MFA (Two-Factor)

Se a conta tem MFA habilitado (`mfa_enabled: true`), o login retorna um desafio:

**Passo 1 — Login (retorna `mfa_required: true`):**

```
POST /v1/sessions
Content-Type: application/json

{
  "email": "admin@empresa.com",
  "password": "senha123"
}
```

**Response (200 — MFA challenge):**

```json
{
  "mfa_required": true,
  "mfa_token": "eyJhbGciOiJIUzI1NiJ9...",
  "message": "Código de verificação enviado para ad***n@empresa.com"
}
```

> O backend envia um código de 6 dígitos por email via `MfaMailer`.

**Passo 2 — Verificar código:**

```
POST /v1/sessions/verify_mfa
Content-Type: application/json

{
  "mfa_token": "eyJhbGciOiJIUzI1NiJ9...",
  "code": "482917"
}
```

**Response (200 — sucesso):**

```json
{
  "user": { "id": 1, "name": "Admin", "email": "admin@empresa.com", "..." },
  "token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Erros:**

| Status | Body | Causa |
|--------|------|-------|
| `401` | `{"error": "Código inválido ou expirado", "attempts_remaining": 3}` | Código errado |
| `401` | `{"error": "Token MFA inválido ou expirado"}` | Token MFA expirou (10 min) |
| `429` | `{"error": "Limite de tentativas excedido...", "rate_limited": true}` | 5+ tentativas inválidas |

**Reenviar código MFA:**

```
POST /v1/sessions/resend_mfa
Content-Type: application/json

{
  "mfa_token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**

```json
{
  "message": "Novo código enviado para ad***n@empresa.com",
  "mfa_token": "eyJhbGciOiJIUzI1NiJ9..."
}
```

> Máximo de 3 reenvios por sessão MFA.

---

## 2. Login via WorkOS SSO (Microsoft, Google, Okta, SAML)

O WorkOS é o provider de SSO. Suporta: Microsoft Entra ID, Google OAuth, Okta, Azure AD, ADFS, SAML.

### Fluxo Completo

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │     │  API     │     │  WorkOS  │     │ Provider │
│          │     │          │     │          │     │ (MS/Google)
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. GET /sso_options?email=x     │                │
     │───────────────>│                │                │
     │ { providers }  │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ 2. GET /workos/login_url?provider=microsoft_entra_id
     │───────────────>│                │                │
     │ { url }        │                │                │
     │<───────────────│                │                │
     │                │                │                │
     │ 3. Redirect/popup → url        │                │
     │────────────────────────────────>│                │
     │                │                │ 4. Redirect    │
     │                │                │───────────────>│
     │                │                │                │
     │                │                │ 5. User auth   │
     │                │                │<───────────────│
     │                │                │                │
     │ 6. Callback: /workos/callback?code=XXX&state=YYY │
     │                │<──────────────────────────────────
     │                │                │                │
     │                │ 7. Exchange code for profile     │
     │                │───────────────>│                │
     │                │ { profile }    │                │
     │                │<───────────────│                │
     │                │                │                │
     │ 8. HTML redirect → /auth/callback?token=JWT&user={...}
     │<───────────────│                │                │
     │                │                │                │
     │ 9. Frontend salva token e user  │                │
     └                └                └                └
```

### Passo a Passo

**1. Consultar opções de SSO:**

```
GET /v1/workos/sso_options?email=usuario@empresa.com
```

**2. Obter URL de autorização:**

```
GET /v1/workos/login_url?provider=microsoft_entra_id
```

**Response:**

```json
{
  "url": "https://api.workos.com/sso/authorize?client_id=...&redirect_uri=...&state=...",
  "provider": "microsoft_entra_id"
}
```

**Providers suportados:**

| Provider ID | Nome |
|-------------|------|
| `microsoft_entra_id` | Microsoft (Entra ID) |
| `google_oauth` | Google |
| `okta` | Okta |
| `azure_ad` | Azure AD |
| `adfs` | AD FS |
| `saml` | SAML genérico |

**3. Frontend redireciona o browser para a `url` (ou abre popup).**

**4-5. Usuário autentica no provider (Microsoft/Google/etc).**

**6-7. WorkOS redireciona para `GET /v1/workos/callback?code=XXX&state=YYY`. O backend troca o code por um profile via WorkOS API.**

**8. O callback renderiza HTML que redireciona para o frontend:**

```
{FRONT_URL}/auth/callback?token=JWT_TOKEN&user={"id":1,"name":"...","email":"..."}
```

Se o user usou Microsoft e ainda não tem Graph API conectado, também envia:

```
graph_auth_url=https://login.microsoftonline.com/common/oauth2/v2.0/authorize?...
```

**9. Frontend extrai `token` e `user` dos query params e salva.**

### JIT Provisioning (Just-in-Time)

Se o user não existe mas a conta tem `jit_provisioning_enabled: true`, o WorkOS cria o user automaticamente no primeiro login SSO. O user é criado com uma senha aleatória (não usável para login por senha).

---

## 3. Login via Microsoft Direto (sem WorkOS)

Para login direto pela Microsoft (OAuth2 com Graph API):

### Fluxo

```
┌──────────┐     ┌──────────┐     ┌──────────────────┐
│ Frontend │     │  API     │     │ Microsoft OAuth  │
└────┬─────┘     └────┬─────┘     └────────┬─────────┘
     │                │                     │
     │ 1. GET /v1/users/microsoft_graph_auth/login_url
     │───────────────>│                     │
     │ { url }        │                     │
     │<───────────────│                     │
     │                │                     │
     │ 2. Redirect/popup → url             │
     │─────────────────────────────────────>│
     │                │                     │
     │ 3. User autentica na Microsoft      │
     │                │                     │
     │ 4. Callback: /v1/auth/microsoft_graph_auth/callback?code=X&state=Y
     │                │<────────────────────│
     │                │                     │
     │                │ 5. Token exchange   │
     │                │────────────────────>│
     │                │ { access_token }    │
     │                │<────────────────────│
     │                │                     │
     │                │ 6. GET /me (Graph)  │
     │                │────────────────────>│
     │                │ { mail, name }      │
     │                │<────────────────────│
     │                │                     │
     │ 7. HTML redirect → /auth/callback?token=JWT&user={...}
     │<───────────────│                     │
     └                └                     └
```

**1. Obter URL de login Microsoft:**

```
GET /v1/users/microsoft_graph_auth/login_url
```

**Response:**

```json
{
  "url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=...&redirect_uri=...&response_type=code&scope=openid+profile+email+offline_access+User.Read+Mail.Read+...&state=..."
}
```

**Scopes solicitados:**

```
openid profile email offline_access
User.Read Mail.Read Mail.ReadWrite Mail.Send
MailboxSettings.Read Calendars.ReadWrite
OnlineMeetings.ReadWrite Tasks.ReadWrite
Chat.ReadWrite Chat.Create
```

**2-6. User autentica, callback troca code por tokens, busca `/me` no Graph API.**

**7. Renderiza HTML que redireciona para:**

```
{FRONT_URL}/auth/callback?token=JWT_TOKEN&user={"id":1,"name":"...","email":"...","microsoft_connected":true}
```

**Diferença do WorkOS:** O login Microsoft direto já salva `ms_access_token` e `ms_refresh_token` no user, habilitando Graph API imediatamente (email, calendário, Teams, etc.).

---

## 4. Reset de Senha

### Solicitar Reset

```
POST /v1/password_resets
Content-Type: application/json

{
  "email": "usuario@empresa.com"
}
```

**Response (200):**

```json
{
  "message": "Email de redefinição de senha enviado com sucesso"
}
```

> O user recebe um email com link: `{FRONT_URL}/reset-password/{token}`. Token expira em 1 hora.

### Validar Token

```
GET /v1/password_resets/:token
```

**Response (200):**

```json
{
  "message": "Token válido",
  "expires_at": "2026-03-13T15:00:00Z",
  "user_email": "usuario@empresa.com"
}
```

### Completar Reset

```
POST /v1/password_resets/:token/complete
Content-Type: application/json

{
  "password": "novaSenha123"
}
```

**Response (200):**

```json
{
  "message": "Senha alterada com sucesso"
}
```

---

## 5. Usando o Token JWT

Após login (qualquer método), o frontend recebe um `token` JWT. Usar em todos os requests autenticados:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

### Payload do JWT (user)

```json
{
  "user_id": 1,
  "exp": 1773496265
}
```

- Expira em **24 horas**
- Algoritmo: HS256
- Secret: `Rails.application.secret_key_base`

### Obter Dados do User Atual

```
GET /v1/me
Authorization: Bearer {token}
```

**Response:**

```json
{
  "user": {
    "id": 1,
    "name": "João Silva",
    "email": "usuario@empresa.com",
    "is_admin": true,
    "microsoft_connected": true,
    "business_name": "Empresa XYZ",
    "business_logo": "http://...",
    "account_id": 1,
    "sourcing_config": {}
  }
}
```

---

## 6. OAuth Service-to-Service (API Clients)

Para integrações externas, serviços automatizados ou API clients:

```
POST /v1/oauth/token
Content-Type: application/json

{
  "client_id": "abc123",
  "client_secret": "secret456"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 300
}
```

- Token de serviço (`role: "service"`) expira em **5 minutos**
- Payload inclui: `iss`, `aud`, `jti`, `role: "service"`, `account_id`
- Não tem `user_id` — identifica a conta, não o user

---

## 7. OTT — One-Time Token (Agent Python)

O agente Python obtém acesso via troca de OTT (gerado pelo backend quando cria uma mensagem):

### Fluxo

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│ Frontend │     │  API     │     │ Agent Python │
└────┬─────┘     └────┬─────┘     └──────┬───────┘
     │                │                   │
     │ POST /messages │                   │
     │───────────────>│                   │
     │                │                   │
     │                │ RabbitMQ: { ott } │
     │                │──────────────────>│
     │                │                   │
     │                │ POST /v1/agent_tokens/exchange
     │                │<──────────────────│
     │                │ { ott, client_id }│
     │                │                   │
     │                │ { access_token }  │
     │                │──────────────────>│
     │                │                   │
     │                │ Requests com token│
     │                │<──────────────────│
     └                └                   └
```

**Exchange:**

```
POST /v1/agent_tokens/exchange
Content-Type: application/json

{
  "one_time_token": "eyJhbGciOiJIUzI1NiJ9...",
  "client_id": "python-agent"
}
```

**Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 300,
  "user_id": 1
}
```

- OTT é single-use (via `RequestKey.claim!`)
- Service token resultante expira em **5 minutos**
- Token inclui `account_id` e `user_id` do user original

---

## 8. Integração Microsoft Graph (pós-login)

Diferente do **login**, a integração Microsoft Graph conecta a conta Microsoft do user para funcionalidades como email, calendário e Teams.

### Verificar Status

```
GET /v1/users/microsoft_graph_auth/status
Authorization: Bearer {token}
```

**Response:**

```json
{
  "connected": true,
  "status": "active",
  "expires_at": "2026-03-13T15:00:00Z",
  "auth_url": null
}
```

**Status possíveis:** `active`, `expiring_soon`, `expired`, `not_connected`

Se `connected: false`, o response inclui `auth_url` para iniciar a integração:

```json
{
  "connected": false,
  "status": "not_connected",
  "expires_at": null,
  "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..."
}
```

### Conectar Graph API

```
GET /v1/users/microsoft_graph_auth/url
Authorization: Bearer {token}
```

**Response:**

```json
{
  "url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?..."
}
```

Frontend abre popup/redirect para a `url`. Após consentimento, o callback salva `ms_access_token` e `ms_refresh_token` no user.

---

## 9. Login via Extensão (Browser Extension, VS Code, etc.)

Para uma extensão (browser, VS Code, desktop app) que precisa autenticar no WeDO Talent, existem duas abordagens:

### Opção A — Login Email + Senha (direto)

A extensão coleta email e senha e faz POST diretamente:

```
POST {API_URL}/v1/sessions
Content-Type: application/json

{
  "email": "usuario@empresa.com",
  "password": "senha123"
}
```

Response retorna `token` JWT. A extensão salva o token e usa em requests subsequentes.

**Se MFA for obrigatório**, a extensão deve implementar o fluxo de `verify_mfa` completo.

### Opção B — SSO via Browser (Microsoft, Google, etc.)

A extensão não consegue hospedar o fluxo OAuth internamente. A solução é **abrir o browser do user** e capturar o token no callback:

```
┌───────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Extension │     │ Browser  │     │   API    │     │ Provider │
└─────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
      │                │                │                │
      │ 1. GET /v1/workos/login_url?provider=microsoft_entra_id
      │───────────────────────────────>│                │
      │ { url }                        │                │
      │<───────────────────────────────│                │
      │                │                │                │
      │ 2. Abre browser com url        │                │
      │───────────────>│                │                │
      │                │ 3. Redirect    │                │
      │                │───────────────────────────────>│
      │                │                │                │
      │                │ 4. User autentica              │
      │                │                │                │
      │                │ 5. Callback → API → redirect   │
      │                │<──────────────────────────────── 
      │                │                │                │
      │                │ 6. Redirect → {FRONT_URL}/auth/callback?token=JWT
      │                │─────────────>│                │
      │                │               │                │
      │ 7. Extensão captura o token do redirect         │
      │<──────────────│                │                │
      │                │                │                │
      │ 8. Requests com token                           │
      │───────────────────────────────>│                │
      └                └                └                └
```

**Como capturar o token na extensão:**

1. **Browser Extension:** Registrar um listener para navigação em `{FRONT_URL}/auth/callback*` e extrair `token` dos query params
2. **Desktop App / VS Code Extension:** Iniciar um servidor HTTP local temporário (ex: `http://localhost:PORT/callback`), usar como `redirect_uri` customizado, ou interceptar o deep link
3. **Alternativa com polling:** Após iniciar o fluxo SSO, a extensão pode polling no `GET /v1/me` com um token temporário até o login ser concluído

### Opção C — OAuth Client Credentials (Service)

Para extensões que representam um serviço (não um user):

```
POST {API_URL}/v1/oauth/token
Content-Type: application/json

{
  "client_id": "extension-client-id",
  "client_secret": "extension-secret"
}
```

Token de serviço não tem user associado — útil para automações, não para ações em nome de um user.

---

## Implementação na Extensão — Exemplo Prático

### Browser Extension (Chrome/Firefox)

```typescript
const API_URL = 'https://api.wedotalent.com'
const FRONT_URL = 'https://app.wedotalent.com'

// --- Login email + senha ---
async function loginWithPassword(email: string, password: string) {
  const res = await fetch(`${API_URL}/v1/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })

  const data = await res.json()

  if (data.mfa_required) {
    // Pedir código MFA ao user
    return { mfa_required: true, mfa_token: data.mfa_token }
  }

  if (data.token) {
    await chrome.storage.local.set({ auth_token: data.token, user: data.user })
    return { success: true }
  }

  return { error: data.error }
}

// --- MFA ---
async function verifyMfa(mfaToken: string, code: string) {
  const res = await fetch(`${API_URL}/v1/sessions/verify_mfa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mfa_token: mfaToken, code })
  })

  const data = await res.json()
  if (data.token) {
    await chrome.storage.local.set({ auth_token: data.token, user: data.user })
    return { success: true }
  }
  return { error: data.error, attempts_remaining: data.attempts_remaining }
}

// --- Login SSO (via browser) ---
async function loginWithSSO(provider = 'microsoft_entra_id') {
  // 1. Pedir URL de autorização
  const res = await fetch(`${API_URL}/v1/workos/login_url?provider=${provider}`)
  const { url } = await res.json()

  // 2. Abrir no browser
  chrome.tabs.create({ url })

  // 3. Listener para capturar o callback
  chrome.webNavigation.onBeforeNavigate.addListener(function listener(details) {
    if (details.url.startsWith(`${FRONT_URL}/auth/callback`)) {
      const params = new URLSearchParams(new URL(details.url).search)
      const token = params.get('token')
      const user = JSON.parse(params.get('user') || '{}')

      chrome.storage.local.set({ auth_token: token, user })
      chrome.tabs.remove(details.tabId)
      chrome.webNavigation.onBeforeNavigate.removeListener(listener)
    }
  })
}

// --- Usar token em requests ---
async function authenticatedRequest(path: string, options: RequestInit = {}) {
  const { auth_token } = await chrome.storage.local.get('auth_token')

  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${auth_token}`
    }
  })
}
```

---

## Tabela de Endpoints

| Endpoint | Método | Auth | Descrição |
|----------|--------|------|-----------|
| `/v1/sessions` | POST | Não | Login email + senha |
| `/v1/sessions/verify_mfa` | POST | Não | Verificar código MFA |
| `/v1/sessions/resend_mfa` | POST | Não | Reenviar código MFA |
| `/v1/me` | GET | JWT | Dados do user logado |
| `/v1/logout` | POST | Não | Logout (stateless) |
| `/v1/workos/sso_options` | GET | Não | Opções de SSO por email |
| `/v1/workos/login_url` | GET | Não | URL de autorização WorkOS SSO |
| `/v1/workos/callback` | GET | Não | Callback do WorkOS (retorna HTML) |
| `/v1/users/microsoft_graph_auth/login_url` | GET | Não | URL de login direto Microsoft |
| `/v1/users/microsoft_graph_auth/url` | GET | JWT | URL de integração Graph API |
| `/v1/users/microsoft_graph_auth/status` | GET | JWT | Status da conexão Microsoft |
| `/v1/auth/microsoft_graph_auth/callback` | GET | Não | Callback do Microsoft OAuth (retorna HTML) |
| `/v1/password_resets` | POST | Não | Solicitar reset de senha |
| `/v1/password_resets/:token` | GET | Não | Validar token de reset |
| `/v1/password_resets/:token/complete` | POST | Não | Completar reset de senha |
| `/v1/oauth/token` | POST | Não | Token service-to-service |
| `/v1/agent_tokens/exchange` | POST | Não | Trocar OTT por service token |

---

## Resumo dos Tipos de Token

| Token | Gerado Por | Expira | Payload | Uso |
|-------|-----------|--------|---------|-----|
| **User JWT** | `SessionsController`, callbacks | 24h | `{ user_id, exp }` | Requests autenticados do frontend |
| **Service Token** | `OauthController`, `AgentTokensController` | 5 min | `{ iss, aud, jti, role: "service", account_id, user_id? }` | Agente Python, API clients |
| **OTT** | `JsonWebToken.encode_ott` (via RabbitMQ) | 10 min | `{ iss, aud, jti, role: "one_time_token", account_id, user_id }` | Single-use, trocado por service token |
| **MFA Token** | `MfaService` | 10 min | `{ role: "mfa_pending", user_id }` | Validar código MFA |
| **State Token** | Controllers (WorkOS, Microsoft) | 10-30 min | `{ action, provider, timestamp }` | CSRF prevention em OAuth callbacks |

---

## Fluxo Recomendado para Frontend

```typescript
async function login(email: string, password?: string) {
  // 1. Verificar opções de auth para o email
  const options = await fetch(`/v1/workos/sso_options?email=${email}`)
  const { sso_enabled, providers, login_traditional_enabled } = await options.json()

  // 2. Se só tem SSO (sem senha)
  if (sso_enabled && !login_traditional_enabled) {
    // Redirect para o primeiro provider SSO
    window.location.href = providers[0].login_url
    return
  }

  // 3. Se tem senha e SSO — mostrar ambas opções
  if (login_traditional_enabled && password) {
    const res = await fetch('/v1/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    const data = await res.json()

    if (data.mfa_required) {
      // Mostrar tela de MFA
      return { mfa: true, mfa_token: data.mfa_token }
    }

    if (data.token) {
      saveSession(data.token, data.user)
      return { success: true }
    }

    return { error: data.error }
  }
}

// 4. Callback handler (/auth/callback)
function handleAuthCallback() {
  const params = new URLSearchParams(window.location.search)
  const token = params.get('token')
  const user = JSON.parse(params.get('user') || '{}')
  const graphAuthUrl = params.get('graph_auth_url')

  if (token) {
    saveSession(token, user)

    // Se precisa conectar Microsoft Graph
    if (graphAuthUrl) {
      window.open(graphAuthUrl, '_blank', 'width=600,height=700')
    }

    router.push('/user/dashboard')
  }
}
```
