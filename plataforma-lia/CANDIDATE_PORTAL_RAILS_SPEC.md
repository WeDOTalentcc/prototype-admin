# Candidate Portal — Especificação de Backend Rails

**Versão**: 1.1  
**Data**: 2026-04-19  
**Para**: Time de Backend (ats-api-copia) + Time LIA (Replit) + Time Frontend  
**Autor**: LIA Engineering  

---

## Contexto

Candidatos criados pela LIA precisam de um canal para consultar seu status no processo seletivo sem precisar ligar para o RH. A LIA (FastAPI) expõe um agente conversacional (WhatsApp + web) que consome endpoints deste documento.

**O time Rails entrega**: endpoints de dados + autenticação por token + migrations.  
**O time Replit entrega**: agente IA conversacional + frontend (já implementado — ver seção final).

---

## JWT Token — Formato Exato

```
Header: { "alg": "HS256", "typ": "JWT" }

Payload: {
  "candidate_id": "uuid-string",      # ID do candidato (Apply.candidate_id)
  "vacancy_id":   "uuid-string",      # ID da vaga (Apply.vacancy_id)
  "company_id":   "uuid-string",      # ID da empresa — SEMPRE do token, nunca do body
  "channel":      "web" | "whatsapp", # Canal de acesso
  "iat":          1713456789,         # Emitido em (Unix timestamp)
  "exp":          1716048789          # Expira em (iat + 30 dias)
}

Secret: ENV["CANDIDATE_PORTAL_JWT_SECRET"]  # Novo env var, mín 32 chars
```

**Quando gerar**: no momento em que Apply é criado pela LIA (webhook `apply.created`).  
**Onde salvar**: `applies.candidate_access_token` (string, nullable).  
**Renovação automática**: quando candidato acessa qualquer endpoint, se token expira em < 7 dias, responder com header `X-Token-Renewed: <new_token>`.

---

## Migrations

### Migration 1 — Campos token no Apply

```ruby
# db/migrate/TIMESTAMP_add_candidate_portal_fields_to_applies.rb
class AddCandidatePortalFieldsToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :candidate_access_token, :string
    add_column :applies, :candidate_token_expires_at, :datetime
    add_column :applies, :candidate_portal_enabled, :boolean, default: false, null: false
    add_column :applies, :whatsapp_consent_at, :datetime
    add_column :applies, :candidate_token_last_used_at, :datetime

    add_index :applies, :candidate_access_token, unique: true
  end
end
```

### Migration 2 — Tabela de audit logs

```ruby
# db/migrate/TIMESTAMP_create_candidate_portal_audit_logs.rb
class CreateCandidatePortalAuditLogs < ActiveRecord::Migration[7.1]
  def change
    create_table :candidate_portal_audit_logs, id: :uuid do |t|
      t.string   :candidate_id,       null: false
      t.string   :vacancy_id,         null: false
      t.string   :company_id,         null: false
      t.string   :channel,            null: false  # "web" | "whatsapp"
      t.string   :action,             null: false  # endpoint chamado
      t.boolean  :fairness_triggered, default: false
      t.boolean  :lgpd_disclosure_sent, default: false
      t.jsonb    :metadata,           default: {}
      t.timestamps
    end

    add_index :candidate_portal_audit_logs, :candidate_id
    add_index :candidate_portal_audit_logs, [:candidate_id, :vacancy_id]
    add_index :candidate_portal_audit_logs, :created_at
  end
end
```

### Migration 3 — Campos de config no hiring_policy (se não existirem)

```ruby
# db/migrate/TIMESTAMP_add_candidate_portal_config_to_hiring_policies.rb
class AddCandidatePortalConfigToHiringPolicies < ActiveRecord::Migration[7.1]
  def change
    # Adicionar em hiring_policies.configure_communication (jsonb) ou tabela separada
    # Verificar schema atual antes de aplicar
    add_column :hiring_policies, :candidate_portal_enabled, :boolean, default: false
    add_column :hiring_policies, :show_wsi_feedback_to_candidate, :boolean, default: false
    add_column :hiring_policies, :lgpd_review_contact_email, :string
    add_column :hiring_policies, :candidate_portal_farewell_message, :text
  end
end
```

> **Nota**: Se `hiring_policies` usa JSONB para configurações, adicionar esses campos dentro do JSONB existente em vez de colunas separadas.

---

## Auth Concern

```ruby
# app/controllers/concerns/candidate_authenticatable.rb
module CandidateAuthenticatable
  extend ActiveSupport::Concern

  included do
    before_action :authenticate_candidate!
  end

  private

  def authenticate_candidate!
    token = extract_token
    return render_unauthorized unless token

    begin
      payload = JWT.decode(
        token,
        ENV.fetch("CANDIDATE_PORTAL_JWT_SECRET"),
        true,
        { algorithm: "HS256" }
      ).first

      @candidate_id = payload["candidate_id"]
      @vacancy_id   = payload["vacancy_id"]
      @company_id   = payload["company_id"]  # SEMPRE do token — nunca do params
      @channel      = payload["channel"]

      validate_apply_exists!
      maybe_renew_token(payload)
    rescue JWT::ExpiredSignature
      render_unauthorized("token_expired")
    rescue JWT::DecodeError
      render_unauthorized("token_invalid")
    end
  end

  def validate_apply_exists!
    @apply = Apply
      .where(candidate_id: @candidate_id, vacancy_id: @vacancy_id)
      .where(company_id: @company_id)  # anti-IDOR: company do token
      .first

    render_unauthorized("apply_not_found") unless @apply
  end

  def maybe_renew_token(payload)
    exp = payload["exp"]
    return unless exp && Time.at(exp) < 7.days.from_now

    new_token = CandidatePortalTokenService.generate(
      candidate_id: @candidate_id,
      vacancy_id:   @vacancy_id,
      company_id:   @company_id,
      channel:      @channel
    )
    response.set_header("X-Token-Renewed", new_token)

    @apply.update_columns(
      candidate_access_token: new_token,
      candidate_token_expires_at: 30.days.from_now,
      candidate_token_last_used_at: Time.current
    )
  end

  def extract_token
    request.headers["Authorization"]&.sub(/\ABearer /, "") ||
      params[:token]
  end

  def render_unauthorized(reason = "unauthorized")
    render json: { error: reason }, status: :unauthorized
  end
end
```

---

## Service — Geração de Token

```ruby
# app/services/candidate_portal_token_service.rb
class CandidatePortalTokenService
  JWT_SECRET = ENV.fetch("CANDIDATE_PORTAL_JWT_SECRET")
  EXPIRY_DAYS = 30

  def self.generate(candidate_id:, vacancy_id:, company_id:, channel: "web")
    payload = {
      candidate_id: candidate_id,
      vacancy_id:   vacancy_id,
      company_id:   company_id,
      channel:      channel,
      iat:          Time.current.to_i,
      exp:          EXPIRY_DAYS.days.from_now.to_i
    }
    JWT.encode(payload, JWT_SECRET, "HS256")
  end

  def self.generate_and_save(apply, channel: "web")
    token = generate(
      candidate_id: apply.candidate_id.to_s,
      vacancy_id:   apply.vacancy_id.to_s,
      company_id:   apply.company_id.to_s,
      channel:      channel
    )
    apply.update_columns(
      candidate_access_token:       token,
      candidate_token_expires_at:   EXPIRY_DAYS.days.from_now,
      candidate_portal_enabled:     true,
      candidate_token_last_used_at: nil
    )
    token
  end
end
```

**Quando chamar**: hook em `Apply.after_create` (ou job Sidekiq) quando `apply.created_by == "lia"`.

---

## Endpoints

Base URL: `https://staging2.wedotalent.cc`  
Namespace: `/v1/candidate-portal/`  
Auth: Bearer token JWT no header `Authorization` (obrigatório em todos, exceto `/lookup-by-phone`)

### Roteamento

```ruby
# config/routes.rb
namespace :v1 do
  namespace :candidate_portal do
    get  "applications",      to: "applications#index"
    get  "status",            to: "status#show"
    get  "interview",         to: "interview#show"
    get  "policy",            to: "policy#show"
    get  "wsi-feedback",      to: "wsi_feedback#show"
    post "lookup-by-phone",   to: "lookup#by_phone"  # auth interna, sem JWT candidato
  end
end
```

---

### GET /v1/candidate-portal/applications

**Propósito**: listar todas as vagas ativas do candidato naquela empresa (para o job selector do frontend quando há 2+).  
**Auth**: JWT candidato (candidate_id + company_id do token).

**Response 200**:
```json
{
  "data": [
    {
      "apply_id": "uuid",
      "vacancy_id": "uuid",
      "vacancy_title": "Engenheiro de Software Pleno",
      "stage": "interview_scheduled",
      "stage_label": "Entrevista Agendada",
      "applied_at": "2026-03-15T10:30:00Z"
    }
  ]
}
```

**Campos PROIBIDOS** (nunca retornar):
- `cpf`, `diversity_*`, `salary_*`, `wsi_final_score`, `lia_score`, `match_percentage`, `red_flags`, `interviewer_notes`, `internal_comments`

**Controller**:
```ruby
# app/controllers/v1/candidate_portal/applications_controller.rb
class V1::CandidatePortal::ApplicationsController < ApplicationController
  include CandidateAuthenticatable

  def index
    applies = Apply
      .where(candidate_id: @candidate_id, company_id: @company_id)
      .where.not(status: "archived")
      .includes(:vacancy)
      .order(created_at: :desc)

    render json: { data: applies.map { |a| serialize_apply(a) } }
  end

  private

  def serialize_apply(apply)
    {
      apply_id:     apply.id,
      vacancy_id:   apply.vacancy_id,
      vacancy_title: apply.vacancy&.title,
      stage:        apply.stage,
      stage_label:  apply.stage_label_pt,
      applied_at:   apply.created_at.iso8601
    }
  end
end
```

---

### GET /v1/candidate-portal/status

**Propósito**: status atual do candidato na vaga específica do token.

**Response 200**:
```json
{
  "data": {
    "apply_id": "uuid",
    "vacancy_id": "uuid",
    "vacancy_title": "Engenheiro de Software Pleno",
    "company_name": "Acme Corp",
    "stage": "interview_scheduled",
    "stage_label": "Entrevista Agendada",
    "stage_entered_at": "2026-04-10T09:00:00Z",
    "applied_at": "2026-03-15T10:30:00Z",
    "portal_enabled": true,
    "show_feedback": false
  }
}
```

**Campos PROIBIDOS**: mesmos do endpoint anterior + `wsi_final_score`, `lia_score`, `match_percentage`, `red_flags`.

---

### GET /v1/candidate-portal/interview

**Propósito**: detalhes da entrevista agendada (se houver).

**Response 200 — com entrevista**:
```json
{
  "data": {
    "scheduled": true,
    "interview_at": "2026-04-25T14:00:00Z",
    "type": "video",
    "type_label": "Videoconferência",
    "duration_minutes": 45,
    "location_or_link": "https://meet.google.com/xyz",
    "interviewer_name": "João Silva",
    "preparation_tips": "Prepare exemplos de projetos anteriores."
  }
}
```

**Response 200 — sem entrevista**:
```json
{
  "data": {
    "scheduled": false,
    "message": "Nenhuma entrevista agendada no momento."
  }
}
```

**Campos PROIBIDOS**: `interviewer_notes`, `feedback`, `lia_suggested_questions`, `recording_url`, `is_private`, qualquer campo de avaliação.

---

### GET /v1/candidate-portal/policy

**Propósito**: config do tenant para o portal do candidato (lida pelo agente IA antes de responder sobre feedback).

**Auth**: JWT candidato.

**Response 200**:
```json
{
  "data": {
    "portal_enabled": true,
    "show_feedback": false,
    "lgpd_review_contact": "rh@empresa.com",
    "farewell_message": "Obrigado por participar do nosso processo seletivo!"
  }
}
```

---

### GET /v1/candidate-portal/wsi-feedback

**Propósito**: feedback estruturado das 5 dimensões WSI (SOMENTE se `show_feedback = true` na policy).

**Guards**:
1. `show_feedback` deve ser `true` → caso contrário, 403 com `reason: "feedback_not_enabled"`
2. Apply deve estar em stage `rejected` ou `hired` → caso contrário, 403 com `reason: "process_not_concluded"`

**Response 200**:
```json
{
  "data": {
    "dimensions": {
      "clareza_comunicacao": "O candidato demonstrou capacidade de estruturar ideias de forma clara e objetiva.",
      "conhecimento_tecnico": "Apresentou conhecimento sólido das tecnologias requeridas para a posição.",
      "raciocinio": "Demonstrou raciocínio analítico ao resolver problemas apresentados.",
      "competencias_comportamentais": "Mostrou disposição para trabalho colaborativo e adaptabilidade.",
      "alinhamento_posicao": "Seu perfil tem pontos de alinhamento com as responsabilidades da vaga."
    },
    "sugestoes_desenvolvimento": [
      "Aprofundar conhecimento em arquitetura de sistemas distribuídos.",
      "Praticar comunicação de soluções técnicas para públicos não técnicos."
    ],
    "revisao_humana_disponivel": true,
    "contato_revisao": "rh@empresa.com"
  }
}
```

**Campos PROIBIDOS** (nunca, em nenhuma circunstância):
- `wsi_final_score`, `score`, `bloom_level`, `dreyfus_level`, `red_flags`, `justification`, `classification`, `approved`, qualquer número de pontuação.

**Serializer**:
```ruby
# app/serializers/candidate_wsi_feedback_serializer.rb
class CandidateWsiFeedbackSerializer
  FORBIDDEN = %w[wsi_final_score score bloom_level dreyfus_level red_flags
                 justification classification approved match_percentage lia_score].freeze

  def initialize(wsi_result, policy)
    @wsi    = wsi_result
    @policy = policy
  end

  def serialize
    {
      dimensions: serialize_dimensions,
      sugestoes_desenvolvimento: @wsi[:development_suggestions] || [],
      revisao_humana_disponivel: true,
      contato_revisao: @policy[:lgpd_review_contact]
    }
  end

  private

  def serialize_dimensions
    {
      clareza_comunicacao:          @wsi.dig(:dimensions, :communication_clarity, :text),
      conhecimento_tecnico:         @wsi.dig(:dimensions, :technical_knowledge, :text),
      raciocinio:                   @wsi.dig(:dimensions, :reasoning, :text),
      competencias_comportamentais: @wsi.dig(:dimensions, :behavioral_competencies, :text),
      alinhamento_posicao:          @wsi.dig(:dimensions, :position_alignment, :text)
    }
  end
end
```

---

### POST /v1/candidate-portal/lookup-by-phone

**Propósito**: endpoint interno chamado pelo agente LIA (FastAPI) para identificar um candidato pelo número de telefone no WhatsApp antes de emitir token.  
**Auth**: `Authorization: Bearer <INTERNAL_API_KEY>` (env var `LIA_INTERNAL_API_KEY`) — NÃO é JWT de candidato.

**Request**:
```json
{
  "phone": "+5511999998888",
  "company_id": "uuid"
}
```

**Response 200**:
```json
{
  "data": {
    "candidate_id": "uuid",
    "vacancy_id": "uuid",
    "apply_id": "uuid",
    "candidate_access_token": "eyJhbGci...",
    "has_multiple_applies": false
  }
}
```

**Response 404** — candidato não encontrado:
```json
{ "error": "candidate_not_found" }
```

**Lógica**:
- Buscar `Apply` pelo `candidate.phone == phone AND applies.company_id == company_id`
- Se múltiplas vagas ativas: retornar `has_multiple_applies: true` e a mais recente como principal
- Gerar/renovar token se `candidate_access_token` ausente ou expirado
- Logs: apenas `candidate_id`, `company_id` — NUNCA o número de telefone

---

## Regras LGPD Obrigatórias

| Regra | Como implementar |
|-------|-----------------|
| Art. 46 — Sem PII em logs | Usar apenas `candidate_id`, `vacancy_id`, `company_id` em logs. Nunca `email`, `phone`, `cpf`, `name` |
| Art. 20 — Direito à explicação | Endpoint `/wsi-feedback` sempre retorna `revisao_humana_disponivel: true` e `contato_revisao` |
| Minimização de dados | Serializers devem whitelist campos — nunca expose o objeto AR diretamente |
| Multi-tenancy | `company_id` sempre do token JWT — nunca do body/params. Validar em `validate_apply_exists!` |
| Anti-IDOR | Apply deve satisfazer `candidate_id AND vacancy_id AND company_id` — os 3 do token |

---

## Testes RSpec (Critérios de Aceite)

```ruby
# spec/requests/v1/candidate_portal/status_spec.rb

describe "GET /v1/candidate-portal/status" do
  let(:apply)  { create(:apply, :with_candidate_portal_token) }
  let(:token)  { apply.candidate_access_token }
  let(:headers){ { "Authorization" => "Bearer #{token}" } }

  it "returns status without forbidden fields" do
    get "/v1/candidate-portal/status", headers: headers
    data = JSON.parse(response.body)["data"]

    expect(response).to have_http_status(:ok)
    expect(data).not_to have_key("wsi_final_score")
    expect(data).not_to have_key("lia_score")
    expect(data).not_to have_key("red_flags")
    expect(data).not_to have_key("cpf")
    expect(data).not_to have_key("match_percentage")
  end

  it "blocks cross-company access (IDOR protection)" do
    other_company_apply = create(:apply, company_id: SecureRandom.uuid)
    tampered_token = generate_token_for(other_company_apply)

    get "/v1/candidate-portal/status", headers: { "Authorization" => "Bearer #{tampered_token}" }
    expect(response).to have_http_status(:unauthorized)
  end

  it "rejects expired token" do
    expired_token = generate_expired_token(apply)
    get "/v1/candidate-portal/status", headers: { "Authorization" => "Bearer #{expired_token}" }
    expect(response).to have_http_status(:unauthorized)
    expect(JSON.parse(response.body)["error"]).to eq("token_expired")
  end

  it "renews token when expiring within 7 days" do
    apply.update!(candidate_token_expires_at: 3.days.from_now)
    get "/v1/candidate-portal/status", headers: headers
    expect(response.headers["X-Token-Renewed"]).to be_present
  end
end

describe "GET /v1/candidate-portal/wsi-feedback" do
  it "returns 403 when show_feedback is false" do
    company_policy = create(:hiring_policy, show_wsi_feedback_to_candidate: false)
    # ...
    expect(response).to have_http_status(:forbidden)
    expect(JSON.parse(response.body)["reason"]).to eq("feedback_not_enabled")
  end

  it "never returns wsi_final_score" do
    # even if wsi_result has score, serializer strips it
    expect(JSON.parse(response.body)["data"]).not_to have_key("score")
    expect(JSON.parse(response.body)["data"]["dimensions"].values).to all(be_a(String))
  end
end

describe "POST /v1/candidate-portal/lookup-by-phone" do
  it "returns 403 without internal API key" do
    post "/v1/candidate-portal/lookup-by-phone", params: { phone: "+5511999998888", company_id: "uuid" }
    expect(response).to have_http_status(:forbidden)
  end

  it "never logs the phone number" do
    expect(Rails.logger).not_to receive(:info).with(include("+5511"))
    post "/v1/candidate-portal/lookup-by-phone",
         params: { phone: "+5511999998888", company_id: company.id },
         headers: { "Authorization" => "Bearer #{ENV['LIA_INTERNAL_API_KEY']}" }
  end
end
```

---

## Factory (para testes)

```ruby
# spec/factories/applies.rb (adicionar trait)
trait :with_candidate_portal_token do
  after(:create) do |apply|
    token = CandidatePortalTokenService.generate_and_save(apply)
  end
end
```

---

## Env Vars Novas

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `CANDIDATE_PORTAL_JWT_SECRET` | Secret para assinar tokens JWT dos candidatos | string aleatória 64 chars |
| `LIA_INTERNAL_API_KEY` | Key para autenticar chamadas internas do FastAPI | string aleatória 32 chars |

Adicionar em: `.env.example`, Heroku/Railway config vars, Vault (se em uso).

---

## Checklist de Entrega (Backend Team)

- [ ] Migration 1: `candidate_access_token` + campos em `applies`
- [ ] Migration 2: `candidate_portal_audit_logs`
- [ ] Migration 3: campos de config em `hiring_policies`
- [ ] `db:migrate` em staging2
- [ ] `CandidateAuthenticatable` concern implementado
- [ ] `CandidatePortalTokenService` com geração e renovação de token
- [ ] Todos os 6 endpoints implementados com serializers sem campos proibidos
- [ ] Hook `Apply.after_create` gerando token quando `created_by == "lia"`
- [ ] Env vars configuradas em staging e produção
- [ ] RSpec: todos os testes acima passando
- [ ] Deploy em `staging2.wedotalent.cc`
- [ ] Confirmar para time Replit: URL dos endpoints em staging pronta

---

## Exemplo de Fluxo Completo

```
1. LIA cria candidato via Apply.create(created_by: "lia", ...)
2. after_create hook → CandidatePortalTokenService.generate_and_save(apply)
3. Token gravado em applies.candidate_access_token
4. Rails envia email/WhatsApp com link:
   https://lia.wedotalent.cc/candidate/status?token=<jwt>
5. Candidato clica → Frontend Next.js valida token → chama POST /api/v1/candidate/chat
6. FastAPI valida JWT → rate limit → CandidateSelfServiceAgent
7. Agente chama GET /v1/candidate-portal/status (Rails) → retorna dados sem PII
8. Agente formata resposta em português → candidato vê status
```

---

## Implementação Replit — LIA Agent (FastAPI) — JÁ ENTREGUE

> Esta seção documenta o que o time Replit já implementou na branch `replit-sync` do repositório `wedotalent02202026`. O time Rails consome esses endpoints como cliente — não precisa reimplementar.

### Commits no Replit (branch replit-sync)

**Repositório**: `WeDOTalentcc/wedotalent02202026`  
**Branch**: `replit-sync` (Paulo faz push do Replit IDE)  
**Data de implementação**: 2026-04-19

| Commit | Descrição | O que entregou |
|--------|-----------|----------------|
| `4a762e0ca` | Add candidate portal for job application status and chat | Frontend: `CandidateChatPage.tsx`, `CandidateJobSelector.tsx`, `status/page.tsx` |
| `a21e52d29` | Add candidate portal (merge commit) | Merge do commit acima |
| `ab40cf130` | Update candidate status page and chat features | Proxy routes, `CandidateChatHeader.tsx`, integração com backend APIs |
| `9ebfa3359` | Add functionality to manage candidate requests | `candidate_react_agent.py` inicial, LGPD Art.20 logging |
| `5c1976c09` | Manage candidate requests (merge commit) | Merge — agente ReAct + LGPD |
| `c6220768f` | Improve job creation and candidate sourcing workflows | UX redesign + refinamentos |
| `9bc805b29` | Align chat slash commands across product, code, and docs | Chat slash commands incluindo `/candidate-status` |
| `1b0ca9629` | docs: CANDIDATE_PORTAL_RAILS_SPEC.md | Este documento |

**Commits do domínio `candidate_self_service/` backend**:
- `42c9ce4d2` — Replace stub/fallback handlers with real implementations
- `d312e34dd` — Auto-discovery of AGENT_TYPE_TO_DOMAIN (registra o domínio)
- `b41c542e4` — PII in logs remediation (0 violations)

### Agente ReAct (LangGraph)

```
lia-agent-system/app/domains/candidate_self_service/
├── agents/
│   └── candidate_react_agent.py        ← agente principal LangGraph ReAct
├── candidate_tool_registry.py           ← registry das 3 tools permitidas
├── candidate_system_prompt.py           ← system prompt em português
├── candidate_stage_context.py           ← contexto por estágio de candidatura
├── tools/
│   ├── get_application_status.py        ← consulta GET /v1/candidate-portal/status
│   ├── get_interview_info.py            ← consulta GET /v1/candidate-portal/interview
│   └── get_wsi_feedback.py             ← consulta GET /v1/candidate-portal/wsi-feedback
├── repositories/
│   └── candidate_status_repository.py  ← abstração de acesso aos dados
├── services/
│   └── candidate_status_service.py     ← lógica de negócio do agente
├── config/
│   └── capabilities.yaml              ← config de capabilities do domínio
└── domain.py
```

### Tools Whitelisted — Apenas 3 (por design LGPD)

| Tool | Endpoint Rails consumido | Propósito |
|------|--------------------------|-----------|
| `get_application_status` | `GET /v1/candidate-portal/status` | Status atual na vaga |
| `get_interview_info` | `GET /v1/candidate-portal/interview` | Detalhes da entrevista |
| `get_wsi_feedback` | `GET /v1/candidate-portal/wsi-feedback` | Feedback WSI (se habilitado) |

> **Por que apenas 3?** Princípio de mínimo acesso (LGPD). O agente não pode buscar scores, notas de entrevistador ou dados de outros candidatos — as tools são a barreira de segurança.

### API Pública FastAPI

```
lia-agent-system/app/api/public/candidate_portal.py

POST /api/v1/candidate/chat
Body: {
  "token": "<jwt_candidato>",
  "message": "Qual é o meu status?"
}

Auth: JWT candidato validado internamente pelo FastAPI (não via Rails)
Rate limiting: 30 req/min por candidate_id
LGPD: disclosure automático na primeira mensagem da sessão
```

### Prompt YAML

```
lia-agent-system/app/prompts/domains/candidate_self_service.yaml
```

O prompt instrui o agente a:
- Responder sempre em português
- Nunca revelar scores, classificações ou comparações com outros candidatos
- Sempre mencionar o direito à revisão humana quando falar sobre feedback WSI
- Encerrar a conversa com o `farewell_message` da policy quando o candidato se despede

### Frontend (Next.js — já no Replit)

```
plataforma-lia/src/
├── components/candidate/
│   ├── CandidateChatPage.tsx      ← página principal do chat do candidato
│   ├── CandidateChatHeader.tsx    ← header com nome da vaga e company
│   └── CandidateJobSelector.tsx   ← seletor quando candidato tem 2+ vagas
└── app/candidate/
    └── status/
        └── page.tsx               ← rota pública: /candidate/status?token=<jwt>
```

**Rota pública**: `/candidate/status?token=<jwt_candidato>`  
**Sem auth WorkOS**: rota não passa pelo middleware de autenticação de recrutador  
**Token via query string**: `?token=` (candidato clica no link do email/WhatsApp)

### Fluxo de integração Replit ↔ Rails

```
Candidato clica no link
        ↓
Next.js /candidate/status?token=<jwt>
        ↓
CandidateChatPage.tsx → POST /api/v1/candidate/chat (FastAPI)
        ↓
FastAPI valida JWT → extrai candidate_id, vacancy_id, company_id
        ↓
CandidateSelfServiceAgent (LangGraph ReAct)
        ↓
Tool: get_application_status → GET https://staging2.wedotalent.cc/v1/candidate-portal/status
                                    Bearer: <jwt_candidato>
        ↓
Rails valida JWT (CandidateAuthenticatable) → retorna dados sem PII
        ↓
Agente formata resposta → candidato vê "Sua candidatura está em: Entrevista Agendada"
```

### Dependência crítica para o time Rails

O time Replit está **bloqueado** até que o time Rails entregue:

1. `GET /v1/candidate-portal/status` funcionando em staging2
2. `GET /v1/candidate-portal/interview` funcionando em staging2
3. Env var `CANDIDATE_PORTAL_JWT_SECRET` configurada (mesma em Rails e FastAPI)
4. Env var `LIA_INTERNAL_API_KEY` configurada para o endpoint `/lookup-by-phone`

Confirmar entrega via: enviar exemplo de response real do endpoint `GET /v1/candidate-portal/status` para o time Replit testar a integração end-to-end.
