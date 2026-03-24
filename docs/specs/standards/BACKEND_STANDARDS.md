# Backend Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
> Stack: Ruby on Rails 7.1 (`ats_api`) + Python FastAPI (`lia-agent-system`)
> Baseado no código real dos repositórios `ats_api` e `lia-agent-system`.

---

## 1. Controller Rails Padrão

### 1.1 Estrutura completa com todas as camadas

```ruby
# frozen_string_literal: true          ← OBRIGATÓRIO — primeira linha de todo .rb

module V1
  module Users
    class JobsController < ApplicationController
      # ── 1. Before actions — ordem importa: auth → resource → guards ──
      before_action :authorize_request
      before_action :set_job, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      # ── 2. Actions públicas — body mínimo, delegar para helpers/services ──

      def index
        perform_search(model: Job, serializer: JobSerializer)
      end

      def show
        render_success(@job, serializer: JobSerializer)
      end

      def create
        @job = @current_user.jobs.build(
          job_params.merge(account_id: @current_user.account_id)
        )

        if @job.save
          return render_success(@job, serializer: JobSerializer, status: :created)
        end
        render_error(@job, status: :unprocessable_entity)
      end

      def update
        @job.update(job_params) ? render_success(@job, serializer: JobSerializer) : render_error(@job)
      end

      def destroy
        @job.destroy
        render_no_content
      end

      private

      # ── 3. set_* — finder com 404 embutido ──
      def set_job
        @job = Job.find_by(id: params[:id])
        render_not_found("Job") unless @job
      end

      # ── 4. ensure_* — guard de autorização ──
      def ensure_owner
        return if @job.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação", status: :forbidden)
      end

      # ── 5. *_params — strong parameters explícitos ──
      def job_params
        params.require(:job).permit(:title, :description, :user_id, :account_id)
      end
    end
  end
end
```

**Regras do controller:**

| Regra | Correto | Errado |
|-------|---------|--------|
| Primeira linha | `# frozen_string_literal: true` | Sem o freeze |
| Namespace | `module V1; module Users` | Nenhum ou flat |
| Before actions | `only:` explícito sempre | `before_action :authorize_request` sem `only:` |
| Finder | `find_by(id: params[:id])` com 404 | `find(params[:id])` que lança exception não tratada |
| Render de sucesso | `render_success(@job, serializer: ...)` | `render json: @job.as_json` |
| Render de erro | `render_error(@job)` com model errors | `render json: { error: "..." }` inconsistente |
| SQL | ActiveRecord `.where(...)` | SQL raw, `.find_by_sql` |
| Lógica de negócio | Em `app/services/` | No controller |

### 1.2 Usar concerns para comportamento reutilizável

```ruby
# app/controllers/concerns/resource_loader.rb — código real do projeto
module ResourceLoader
  extend ActiveSupport::Concern

  included do
    before_action :set_resource, only: %i[show update destroy]
  end

  private

  def set_resource
    klass = controller_name.classify.constantize
    resource = klass.find_by(id: params[:id])
    instance_variable_set("@#{controller_name.singularize}", resource)
    render_not_found(klass.name) unless resource
  end
end

# app/controllers/concerns/search_renderer.rb — código real do projeto
module SearchRenderer
  extend ActiveSupport::Concern

  def perform_search(
    model:,
    serializer:,
    term: params[:term],
    page: params[:page],
    search_with_pin: nil
  )
    results = model.search_default(term, search_with_pin, page, term.blank?, false)
    render json: serializer.new(results[:records], {
      meta: { total: results[:total_count], aggregators: results[:aggs] }
    }).serializable_hash
  end
end
```

Incluir `ResourceLoader` elimina o `set_resource` boilerplate de controllers CRUD padrão.

---

## 2. Endpoint FastAPI Padrão

### 2.1 Módulo completo

```python
"""
Sourcing API - Endpoints for candidate sourcing and matching.

Provides:
- POST /sourcing/search           - Search candidates with boolean queries
- POST /sourcing/match-candidates - Match candidates to job requirements
- GET  /sourcing/suggestions/{job_id} - Suggested candidates for a job
"""
# ── 1. Stdlib ──
import logging
from typing import Any, Dict, List, Optional

# ── 2. Third-party ──
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# ── 3. Internal ──
from app.core.database import get_db
from app.domains.sourcing.services.query_builders import BooleanQueryBuilder

# ── 4. Logger — sempre __name__ ──
logger = logging.getLogger(__name__)

# ── 5. Router — prefix e tags obrigatórios ──
router = APIRouter(prefix="/sourcing", tags=["sourcing"])


# ── 6. Schemas Pydantic — Request e Response nomeados e separados ──

class SourcingSearchRequest(BaseModel):
    """Request for candidate sourcing search."""
    query: Optional[str] = Field(None, description="Free text search query")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    seniority: Optional[str] = Field(
        None,
        description="Seniority: junior, pleno, senior, manager, director"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Max results to return")


class SourcingSearchResponse(BaseModel):
    """Response from candidate sourcing search."""
    success: bool
    candidates_found: int
    candidates: List[Dict[str, Any]]
    search_time_ms: int = 0


# ── 7. Endpoints — verb + noun, response_model declarado ──

@router.post("/search", response_model=SourcingSearchResponse)
async def search_candidates(
    request: SourcingSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SourcingSearchResponse:
    """Search candidates using boolean queries and filters."""
    try:
        results = await BooleanQueryBuilder(db).search(request)
        return SourcingSearchResponse(success=True, **results)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)   # exc_info=True é obrigatório
        raise HTTPException(status_code=500, detail="Internal error")
```

**O que NÃO fazer:**
```python
# ❌ ERRADO — lógica de negócio no endpoint
@router.post("/search")
async def search_candidates(request: SourcingSearchRequest):
    # 100 linhas de lógica aqui — mover para services/domains
    candidates = []
    for skill in request.skills:
        candidates.extend(db.query(Candidate).filter(...).all())
    ...

# ❌ ERRADO — sem tipagem no response
@router.post("/search")
async def search_candidates(request):   # sem tipagem no request
    return {"candidates": [...]}        # sem response_model

# ❌ ERRADO — print em vez de logger
@router.post("/search")
async def search_candidates(request):
    try:
        ...
    except Exception as e:
        print(f"Error: {e}")    # PROIBIDO
        return {"error": str(e)}
```

---

## 3. Autenticação e Autorização

### 3.1 Rails: JWT manual no ApplicationController

```ruby
# app/controllers/application_controller.rb — código real do projeto
class ApplicationController < ActionController::Base

  def authorize_request
    header = request.headers['Authorization']
    token = header.split(' ').last if header
    decoded = jwt_decode(token)

    if decoded
      @current_user = User.find_by(id: decoded[:user_id])
      Current.user = @current_user
      render json: { error: 'Not Authorized' }, status: :unauthorized unless @current_user
    else
      render json: { error: 'Token missing or invalid' }, status: :unauthorized
    end
  end

  private

  def jwt_encode(payload, exp = 24.hours.from_now)
    payload[:exp] = exp.to_i
    JWT.encode(payload, Rails.application.secret_key_base)
  end

  def jwt_decode(token)
    decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
    HashWithIndifferentAccess.new decoded
  rescue StandardError => e
    Rails.logger.error "JWT Decode Error: #{e.message}"
    nil                       # nil = token inválido; authorize_request trata isso
  end
end
```

**Sessão de login (sessions_controller.rb — código real):**

```ruby
# frozen_string_literal: true
module V1
  class SessionsController < ApplicationController
    before_action :authorize_request, except: [:create]
    protect_from_forgery with: :null_session   # CSRF desabilitado para API JSON

    def create
      @user = User.find_by(email: params[:email])

      if @user&.authenticate(params[:password])   # has_secure_password
        token = jwt_encode(user_id: @user.id)
        render json: { user: user_payload(@user), token: }, status: :ok
      else
        render json: { error: "Invalid email or password" }, status: :unauthorized
      end
    end

    def me
      render json: { user: user_payload(@current_user) }
    end

    def logout
      render json: { message: "Logged out" }   # JWT é stateless — cliente descarta o token
    end

    private

    def user_payload(user)
      { id: user.id, email: user.email }
    end
  end
end
```

### 3.2 FastAPI: WorkOS SSO + Rate Limiting

O `lia-agent-system` usa middleware (não `Depends`) para autenticação global:

```python
# app/main.py — middlewares registrados na ordem correta
app.add_middleware(StructuredLoggingMiddleware)   # 1. log de cada request
app.add_middleware(RequestIdMiddleware)            # 2. X-Request-ID header
app.add_middleware(RateLimitMiddleware)            # 3. throttling por user/company
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Rate Limiter — padrão real do projeto:**

```python
# app/middleware/rate_limiter.py
class RateLimiter:
    """Rate limiter usando Redis ZSET sliding window (atomic, multi-instance safe).
    Falls back to in-memory se Redis indisponível (graceful degradation)."""

    LIMITS = {
        "per_minute_per_user":    600,
        "per_hour_per_user":      20000,
        "per_minute_per_company": 3000,
        "per_hour_per_company":   60000,
    }
```

**Request ID — padrão real do projeto:**

```python
# app/middleware/request_id.py — código real
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id   # espelha de volta ao cliente
        return response
```

**Dependency de DB nos endpoints:**

```python
# Padrão real de todos os endpoints do lia-agent-system
@router.post("/search")
async def search(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    ...
```

---

## 4. Erros e Respostas Padronizadas

### 4.1 Rails: helpers de render (nunca `render json:` direto)

O projeto usa helpers definidos no `ApplicationController` ou em concerns:

```ruby
# Respostas de sucesso
render_success(@job, serializer: JobSerializer)              # 200
render_success(@job, serializer: JobSerializer, status: :created)  # 201
render_no_content                                            # 204

# Respostas de erro
render_error(@job, status: :unprocessable_entity)           # 422 com model.errors
render_not_found("Job")                                     # 404
render_simple_error("Não autorizado", status: :forbidden)   # 403
render json: { error: "Invalid email or password" }, status: :unauthorized  # 401
```

**Estrutura de resposta de erro do model (422):**
```json
{
  "errors": {
    "title": ["can't be blank"],
    "description": ["can't be blank"]
  }
}
```

**O que NÃO fazer:**
```ruby
# ❌ ERRADO — formato inconsistente
render json: @job.to_json                   # sem serializer
render json: { success: true, data: @job }  # formato diferente do padrão
render json: @job.errors, status: 422       # sem helpers, sem consistência
raise ActiveRecord::RecordNotFound         # não capturada = 500
```

### 4.2 FastAPI: HTTPException com códigos semânticos

```python
# ✅ CORRETO — erros mapeados corretamente
raise HTTPException(status_code=400, detail="job_id is required")   # bad request
raise HTTPException(status_code=401, detail="Token expired")         # unauthorized
raise HTTPException(status_code=403, detail="Insufficient role")     # forbidden
raise HTTPException(status_code=404, detail="Job not found")         # not found
raise HTTPException(status_code=422, detail="Invalid seniority level")  # validation
raise HTTPException(status_code=429, detail="Rate limit exceeded")   # throttle
raise HTTPException(status_code=500, detail="Internal error")        # server error

# ✅ CORRETO — logger.error com exc_info para stack trace no Sentry
except Exception as e:
    logger.error(f"WSI generation failed for job {job_id}: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")

# ❌ ERRADO
return {"error": "algo deu errado"}       # sem status HTTP, sem HTTPException
raise Exception("erro genérico")          # não tratado = 500 sem log
logger.error(str(e))                      # sem exc_info=True — sem stack trace
```

---

## 5. Serialização de Dados

### 5.1 Rails: JSONAPI::Serializer

```ruby
# app/serializer/job_serializer.rb — código real do projeto
class JobSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :title,
    :description,
    :user_id,
    :account_id,
    :created_at,
    :updated_at,
    :is_remote,
    :city,
    :state,
    :country,
    :workplace_type
  )
end
```

**Como usar no controller:**
```ruby
# Index com meta
render json: JobSerializer.new(results[:records], {
  meta: { total: results[:total_count] }
}).serializable_hash

# Show / Create / Update
render_success(@job, serializer: JobSerializer)
```

**Regras de serializer:**
- Um serializer por model — `JobSerializer`, `ApplySerializer`, `CandidateSerializer`
- Nunca expor campos sensíveis: `password_digest`, tokens internos
- `include JSONAPI::Serializer` em todos
- `# frozen_string_literal: true` obrigatório

### 5.2 FastAPI: Pydantic com Field e description

```python
# Padrão real do lia-agent-system
class GenerateQuestionsRequest(BaseModel):
    job_vacancy_id: Optional[str] = None
    job_title: Optional[str] = None
    skills: Optional[List[str]] = None
    seniority_level: Optional[str] = "pleno"
    num_questions: int = Field(default=5, ge=3, le=12)   # validação embutida

class GenerateQuestionsResponse(BaseModel):
    session_id: str
    questions: List[WSIQuestionOutput]
    job_title: Optional[str]
    methodology: str = "WSI (Bloom + Dreyfus + Big Five)"
```

**Regras de schema:**
- `Field(..., description="...")` em todos os campos — documenta o Swagger automaticamente
- Validações embutidas: `ge=`, `le=`, `min_length=`, `max_length=`
- Schemas separados para Request e Response — nunca reutilizar o mesmo
- Nomes explícitos: `XxxRequest`, `XxxResponse`, `XxxOutput`

---

## 6. Testes de Backend

### 6.1 Rails — RSpec com FactoryBot

**Estrutura:**
```
spec/
  rails_helper.rb             ← configuração base (FactoryBot, Shoulda Matchers)
  factories/
    accounts.rb               ← factory :account
    users.rb                  ← factory :user (associa :account)
    jobs.rb                   ← factory :job (associa :user, :account)
    candidates.rb
    applies.rb
  requests/v1/
    sessions_spec.rb          ← POST /v1/sessions, GET /v1/me
    users/jobs_controller_spec.rb
    users/applies_controller_spec.rb
  models/                     ← validações, associations, callbacks
  support/                    ← helpers compartilhados (auth_headers, etc.)
```

**Factory padrão — código real do projeto:**
```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email { Faker::Internet.email }
    password { "password123" }
    association :account
  end
end

# spec/factories/jobs.rb
FactoryBot.define do
  factory :job do
    title { Faker::Job.title }
    description { Faker::Lorem.paragraph }
    association :user
    account { user.account }                    # conta do mesmo usuário
    sequence(:provider) { |n| "provider_#{n}" } # sequence para unicidade
    sequence(:provider_job_id) { |n| "job_id_#{n}" }
    is_remote { Faker::Boolean.boolean }
    workplace_type { ['on_site', 'hybrid', 'remote'].sample }
  end
end
```

**Request spec padrão — código real do projeto:**
```ruby
# spec/requests/v1/users/jobs_controller_spec.rb
# frozen_string_literal: true
require 'rails_helper'

RSpec.describe 'V1::Users::Jobs API', type: :request do
  let(:user) { create(:user) }
  let(:other_user) { create(:user) }

  # Helpers de auth reutilizados de spec/support/
  let(:headers) { auth_headers(user) }
  let(:no_auth) { { 'Content-Type' => 'application/json' } }
  let(:invalid_auth) { { 'Authorization' => 'Bearer invalid', 'Content-Type' => 'application/json' } }

  describe 'GET /v1/users/jobs' do
    before do
      Current.user = user
      create_list(:job, 3, user: user)
      Job.reindex                             # reindexar Elasticsearch em testes
    end

    context 'quando autenticado' do
      it 'retorna todos os jobs' do
        get '/v1/users/jobs', headers: headers
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)['data'].size).to eq(3)
      end
    end

    context 'quando não autenticado' do
      it 'retorna 401' do
        get '/v1/users/jobs', headers: no_auth
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'com token inválido' do
      it 'retorna 401' do
        get '/v1/users/jobs', headers: invalid_auth
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/jobs' do
    let(:valid_params) { { job: { title: 'Dev Rails', description: 'Descrição', user_id: user.id, account_id: user.account.id } } }
    let(:invalid_params) { { job: { title: '', description: 'Sem título' } } }

    it 'cria job com params válidos' do
      expect {
        post '/v1/users/jobs', params: valid_params.to_json, headers: headers
      }.to change(Job, :count).by(1)
      expect(response).to have_http_status(:created)
    end

    it 'retorna 422 com params inválidos' do
      post '/v1/users/jobs', params: invalid_params.to_json, headers: headers
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
```

**Regras de teste Rails:**
- Um `describe` por endpoint ou comportamento
- `context` em português, descrevendo a condição (`quando autenticado`)
- `it` em português, descrevendo o resultado (`retorna todos os jobs`)
- Sempre testar: autenticado, não autenticado, token inválido
- Sempre testar: params válidos, params inválidos
- `Job.reindex` após criações quando Elasticsearch está envolvido

### 6.2 FastAPI — pytest

```python
# tests/integration/test_easy_cases.py
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_search_candidates_returns_results():
    """Busca retorna lista de candidatos com sucesso."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/sourcing/search", json={
            "skills": ["Python", "FastAPI"],
            "limit": 10,
        })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "candidates" in data


@pytest.mark.asyncio
async def test_search_candidates_without_skills_returns_empty():
    """Busca vazia retorna lista vazia sem erro."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/sourcing/search", json={})

    assert response.status_code == 200
    assert response.json()["candidates_found"] == 0
```

---

## 7. Migrações de Banco de Dados

### 7.1 Rails — padrão de migration

```ruby
# db/migrate/20250714142059_create_applies.rb — código real do projeto
class CreateApplies < ActiveRecord::Migration[7.1]
  def change
    create_table :applies do |t|
      t.references :candidate, null: false, foreign_key: true
      t.references :job, null: false, foreign_key: true
      t.references :selective_process, null: false, foreign_key: true
      t.boolean :is_deleted, default: false
      t.timestamps
    end
  end
end

# db/migrate/20250714150818_add_account_in_others_models.rb — código real
class AddAccountInOthersModels < ActiveRecord::Migration[7.1]
  def change
    # Adicionar referência com FK — padrão obrigatório
    add_reference :applies, :account, null: false, foreign_key: true
    add_reference :candidates, :account, null: false, foreign_key: true
    add_reference :selective_processes, :account, null: false, foreign_key: true
  end
end
```

**Regras de migration:**
- Herdar de `ActiveRecord::Migration[7.1]` — versão atual do projeto
- `null: false` em todas as FKs — evita dados órfãos
- `foreign_key: true` em todas as referências — integridade referencial
- Uma migration por responsabilidade (não misturar create_table com add_column de outra tabela)
- **Nunca alterar tipo da coluna `id`** — quebra dados existentes
- Soft delete via campo `is_deleted: boolean, default: false` — nunca `DROP` de dados de produção
- Migrations são irreversíveis em produção — revisar com cuidado

**Nomenclatura de migrations:**
```
YYYYMMDDHHMMSS_verbo_substantivo.rb

create_jobs.rb              → criar nova tabela
add_account_in_others.rb    → adicionar coluna
remove_deprecated_field.rb  → remover coluna (com reversível)
add_index_to_candidates.rb  → adicionar índice
```

### 7.2 FastAPI — SQLAlchemy (lia-agent-system)

O `lia-agent-system` usa `CREATE TABLE IF NOT EXISTS` diretamente no startup para simplicidade:

```python
# app/core/database.py — padrão real do projeto
async def ensure_workos_columns():
    """Adiciona colunas WorkOS se não existirem (idempotente)."""
    async with get_db_session() as session:
        await session.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS workos_id VARCHAR(255),
            ADD COLUMN IF NOT EXISTS workos_organization_id VARCHAR(255)
        """))
```

---

## 8. Nomenclatura de Rotas e Recursos

### 8.1 Rails — padrão do projeto (routes.rb real)

```ruby
# config/routes.rb — código real do projeto
Rails.application.routes.draw do
  mount ActionCable.server => "/cable"
  get "up" => "rails/health#show"   # health check

  namespace :v1 do
    # ── Auth ──
    post "sessions",  to: "sessions#create"
    get  "me",        to: "sessions#me"
    post "logout",    to: "sessions#logout"

    namespace :users do
      # ── Resources padrão: index + show + create + update + destroy ──
      get    "jobs",     to: "jobs#index"
      get    "jobs/:id", to: "jobs#show"
      post   "jobs",     to: "jobs#create"
      put    "jobs/:id", to: "jobs#update"
      delete "jobs/:id", to: "jobs#destroy"

      # ── Mesma estrutura para: applies, candidates, selective_processes, messages ──
    end
  end
end
```

**Regras de rotas:**

| Regra | Correto | Errado |
|-------|---------|--------|
| Versão | `namespace :v1` | Sem versão |
| Recursos no plural | `/jobs`, `/candidates` | `/job`, `/candidate` |
| Sub-recursos | `namespace :users` para recursos de usuário | Flat sem namespace |
| Verbos HTTP | `get/post/put/delete` corretos | `post` para tudo |
| Path params | `/:id` para recurso individual | `/job_detail/:id` |
| Helpers Rails | `resources :jobs` (quando for CRUD completo) | Rotas manuais redundantes |

**Nota:** o projeto usa rotas manuais (`get "jobs", to: "jobs#index"`) em vez de `resources :jobs`. Ambos são válidos, mas ser consistente. O `resources` é preferível por ser mais conciso:

```ruby
# ✅ PREFERÍVEL para CRUDs completos
namespace :v1 do
  namespace :users do
    resources :jobs, only: %i[index show create update destroy]
    resources :applies, only: %i[index show create update destroy]
    resources :candidates, only: %i[index show create update destroy]
  end
end
```

### 8.2 FastAPI — prefixos e tags por domínio

```python
# Padrão real do projeto — prefix por domínio funcional
router = APIRouter(prefix="/sourcing",  tags=["sourcing"])
router = APIRouter(prefix="/wsi",       tags=["WSI Text Screening"])
router = APIRouter(prefix="/pipeline",  tags=["pipeline"])
router = APIRouter(prefix="/auth",      tags=["auth"])

# Registrado em app/main.py:
app.include_router(sourcing.router,  prefix="/api/v1")
app.include_router(wsi.router,       prefix="/api/v1")
```

**Endpoints resultantes:**
```
POST /api/v1/sourcing/search
POST /api/v1/sourcing/match-candidates
GET  /api/v1/wsi/questions/{job_id}
POST /api/v1/wsi/generate-questions
```

**Regras de nomenclatura FastAPI:**

| Regra | Correto | Errado |
|-------|---------|--------|
| Recursos no plural | `/candidates`, `/jobs` | `/candidate`, `/job` |
| Ações kebab-case | `/match-candidates`, `/generate-questions` | `/matchCandidates`, `/generateQuestions` |
| Versão no prefix | `prefix="/api/v1"` no `include_router` | Sem versão |
| Tags obrigatórias | `tags=["sourcing"]` | Sem tags |
| Verbo HTTP correto | `GET` para leitura, `POST` para criação/ações | `POST` para tudo |

---

## Checklist antes de fazer PR de backend

**Rails:**
- [ ] `# frozen_string_literal: true` na primeira linha de todo `.rb`
- [ ] Controller dentro de namespace `V1::Users::`
- [ ] `before_action` com `only:` explícito
- [ ] Strong parameters com `.permit(...)` correto
- [ ] Serializer criado para o model — sem `.as_json` solto
- [ ] Spec de request cobrindo: autenticado, não autenticado, params válidos, params inválidos
- [ ] Factory FactoryBot cobrindo o model (com Faker para dados realistas)
- [ ] Migration com `null: false` em FKs e `foreign_key: true`

**FastAPI:**
- [ ] Docstring de módulo com lista de endpoints
- [ ] `logger = logging.getLogger(__name__)` no topo
- [ ] Schemas `XxxRequest` e `XxxResponse` com `Field(..., description="...")`
- [ ] `response_model=` no decorator do endpoint
- [ ] `logger.error(..., exc_info=True)` em todos os `except Exception`
- [ ] Lógica de negócio em `services/` ou `domains/`, não no endpoint
- [ ] Rate limit coberto pelo middleware global (não precisa por endpoint)

> Para padrões de agentes IA, ver `docs/specs/standards/AI_ARCHITECTURE.md` (a criar).
> Para padrões de frontend que consome este backend, ver `docs/specs/standards/FRONTEND_STANDARDS.md`.
