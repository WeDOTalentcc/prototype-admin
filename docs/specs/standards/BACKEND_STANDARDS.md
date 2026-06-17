# Backend Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
> **Fonte exclusiva**: código lido via GitHub API — repositórios `ats_api` e `recruiter_agent_v5` (WeDOTalent)
> Stack: Ruby on Rails 7.1 (`ats_api`) + Python/FastAPI/LangGraph (`recruiter_agent_v5`)

---

## Repositórios de origem (GitHub WeDOTalent)

| Repositório | Stack | Papel |
|-------------|-------|-------|
| `ats_api` | Rails 7.1 + PostgreSQL + JWT + Elasticsearch | ATS backend REST API |
| `recruiter_agent_v5` | Python + FastAPI + LangGraph + Gemini + Celery | Agente IA multi-domínio |

---

## 1. Controller Rails Padrão

### 1.1 Controller completo — `jobs_controller.rb` (GitHub `ats_api`)

```ruby
# frozen_string_literal: true           ← PRIMEIRA LINHA de todo arquivo .rb

module V1
  module Users
    class JobsController < ApplicationController
      # ── Ordem obrigatória: auth → resource → guards ──
      before_action :authorize_request
      before_action :set_job, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

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
        @job.update(job_params) ?
          render_success(@job, serializer: JobSerializer) :
          render_error(@job)
      end

      def destroy
        @job.destroy
        render_no_content
      end

      private

      def set_job
        @job = Job.find_by(id: params[:id])
        render_not_found("Job") unless @job
      end

      def ensure_owner
        return if @job.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação neste job", status: :forbidden)
      end

      def job_params
        params.require(:job).permit(:title, :description, :user_id, :account_id)
      end
    end
  end
end
```

### 1.2 Controller com concern — `applies_controller.rb` (GitHub `ats_api`)

```ruby
# frozen_string_literal: true

module V1
  module Users
    class AppliesController < ApplicationController
      include ResourceLoader   # ← concern elimina o set_resource boilerplate

      def index
        perform_search(
          model: Apply,
          serializer: ApplySerializer,
          search_with_pin: { where: { is_deleted: false } },   # filtro padrão
        )
      end

      def show
        render_success(@apply, serializer: ApplySerializer)
      end

      def create
        @apply = Apply.new(apply_params)
        if @apply.save
          return render_success(@apply, serializer: ApplySerializer, status: :created)
        end
        render_error(@apply, status: :unprocessable_entity)
      end

      def update
        @apply.update(apply_params) ?
          render_success(@apply, serializer: ApplySerializer) :
          render_error(@apply)
      end

      def destroy
        @apply.update(is_deleted: true)   # soft delete — nunca .destroy em applies
        render_no_content
      end

      private

      def apply_params
        params.require(:apply).permit(
          :candidate_id, :job_id, :selective_process_id, :is_deleted, :account_id
        )
      end
    end
  end
end
```

### 1.3 Concerns reutilizáveis — código real do `ats_api`

```ruby
# app/controllers/concerns/resource_loader.rb
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
```

```ruby
# app/controllers/concerns/search_renderer.rb
module SearchRenderer
  extend ActiveSupport::Concern

  def perform_search(
    model:,
    serializer:,
    term: params[:term],
    search_params: nil,
    page: params[:page],
    pinned_first: term.blank?,
    current_user_id: @current_user.id,
    search_with_pin: nil
  )
    results = model.search_default(
      term || search_params,
      search_with_pin,
      page,
      pinned_first,
      false
    )

    render json: serializer.new(results[:records], {
      meta: {
        total: results[:total_count],
        aggregators: results[:aggs]
      }
    }).serializable_hash
  end
end
```

**Regras de controller (baseadas nos arquivos reais):**

| Regra | Correto | Errado |
|-------|---------|--------|
| Primeira linha | `# frozen_string_literal: true` | Sem o freeze |
| Namespace | `module V1; module Users` | Sem namespace, flat |
| before_action | `only:` explícito sempre | Sem `only:` (aplica em tudo) |
| Finder | `find_by(id: params[:id])` + 404 | `find()` que lança exception não tratada |
| Render sucesso | `render_success(@job, serializer: JobSerializer)` | `render json: @job.as_json` |
| Render erro | `render_error(@job)` (usa model.errors) | `render json: {error: "..."}` manual |
| Soft delete | `update(is_deleted: true)` | `.destroy` em applies |
| SQL | ActiveRecord sempre | SQL raw, `.find_by_sql` |

---

## 2. Endpoint FastAPI Padrão

### 2.1 `src/api.py` — servidor FastAPI do `recruiter_agent_v5`

```python
# src/api.py — código real do repositório recruiter_agent_v5 (GitHub)
import asyncio
import logging
import uuid
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.services.message_router import MessageRouter

logger = logging.getLogger(__name__)

app = FastAPI(title="Recruiter Agent v5 — Streaming API")

# ── Singleton lazy do router ──
_router: MessageRouter = None

def _get_router() -> MessageRouter:
    global _router
    if _router is None:
        _router = MessageRouter()
    return _router


# ── Schemas Pydantic — Request e Response nomeados ──
class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str | None = None
    hub_mode: bool = True
    context_data: Dict[str, Any] = Field(default_factory=dict)


# ── Endpoint: POST /chat ──
@app.post("/chat")
async def chat(req: ChatRequest):
    router = _get_router()
    loop = asyncio.get_event_loop()

    context_data = {**req.context_data, "session_id": req.session_id}
    payload = {
        "question": req.message,
        "domain": req.domain,
        "context_data": context_data,
        "session_id": req.session_id,
        "hub_mode": req.hub_mode,
    }

    result = await loop.run_in_executor(None, router.route, payload)
    return JSONResponse(content={
        "success": result.get("success", True),
        "message": result.get("message", ""),
        "metadata": result.get("metadata", {}),
    })
```

**Estrutura obrigatória de um módulo FastAPI:**

```python
"""
<Nome do módulo> — <descrição em 1 linha>.

Provides:
- POST /endpoint-a   - descrição
- GET  /endpoint-b   - descrição
"""
# 1. Stdlib imports
import logging
import uuid
from typing import Any, Dict, List, Optional

# 2. Third-party imports
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# 3. Internal imports
from src.config.settings import get_settings

# 4. Logger — sempre __name__
logger = logging.getLogger(__name__)

# 5. Router com prefix e tags
router = APIRouter(prefix="/meu-recurso", tags=["meu-recurso"])

# 6. Schemas Pydantic
class MeuRequest(BaseModel):
    campo: str = Field(..., description="Descrição do campo")
    limite: int = Field(default=20, ge=1, le=100)

class MeuResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]

# 7. Endpoints
@router.post("/buscar", response_model=MeuResponse)
async def buscar(req: MeuRequest) -> MeuResponse:
    try:
        resultado = servico.buscar(req)
        return MeuResponse(success=True, data=resultado)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Busca falhou: {e}", exc_info=True)   # exc_info=True obrigatório
        raise HTTPException(status_code=500, detail="Internal error")
```

---

## 3. Autenticação e Autorização

### 3.1 Rails: JWT manual — `sessions_controller.rb` (GitHub `ats_api`)

```ruby
# frozen_string_literal: true
module V1
  class SessionsController < ApplicationController
    before_action :authorize_request, except: [:create]
    protect_from_forgery with: :null_session   # CSRF off para API JSON

    # POST /v1/sessions — login
    def create
      @user = User.find_by(email: params[:email])

      if @user&.authenticate(params[:password])   # has_secure_password
        token = jwt_encode(user_id: @user.id)
        render json: { user: user_payload(@user), token: }, status: :ok
      else
        render json: { error: "Invalid email or password" }, status: :unauthorized
      end
    end

    # GET /v1/me — usuário atual
    def me
      render json: { user: user_payload(@current_user) }
    end

    # POST /v1/logout — JWT é stateless; cliente descarta o token
    def logout
      render json: { message: "Logged out" }
    end

    private

    def user_payload(user)
      { id: user.id, email: user.email }
    end

    def jwt_encode(payload, exp = 24.hours.from_now)
      payload[:exp] = exp.to_i
      JWT.encode(payload, Rails.application.secret_key_base)
    end

    def jwt_decode(token)
      decoded = JWT.decode(token, Rails.application.secret_key_base)[0]
      HashWithIndifferentAccess.new decoded
    rescue StandardError => e
      Rails.logger.error "JWT Decode Error: #{e.message}"
      nil
    end

    def authorize_request
      header = request.headers["Authorization"]
      token = header.split(" ").last if header
      decoded = jwt_decode(token)

      if decoded
        @current_user = User.find_by(id: decoded[:user_id])
        Current.user = @current_user
        render json: { error: "Invalid token" }, status: :unauthorized unless @current_user
      else
        render json: { error: "Token missing or invalid" }, status: :unauthorized
      end
    end
  end
end
```

### 3.2 Python: Bearer token via `AppliesAPIClient` — `api_client.py` (GitHub `recruiter_agent_v5`)

```python
# src/domains/applies/api_client.py — padrão real do repositório
class AppliesAPIClient:

    def __init__(self, context=None):
        self.settings = get_settings()
        self.base_url = self.settings.ats_api.base_url
        self.timeout = self.settings.rails_api.timeout
        self._ott_service = get_ott_service()
        self._context = context

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._context and self._context.auth_token:
            headers["Authorization"] = f"Bearer {self._context.auth_token}"
        else:
            headers.update(self._ott_service.get_auth_header())   # token de serviço
        return headers

    def _request(self, method: str, path: str, params=None, json_body=None) -> AppliesAPIResponse:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method, url,
                    headers=self._get_headers(),
                    params=params,
                    json=json_body,
                )
                if response.status_code == 401:
                    self._ott_service.invalidate()   # força refresh do token
                    response = client.request(
                        method, url,
                        headers=self._get_headers(),
                        params=params,
                        json=json_body,
                    )
                ...
        except httpx.TimeoutException:
            return AppliesAPIResponse(success=False, error="Timeout ao conectar ao backend")
```

**Anti-patterns de auth:**
```python
# ❌ ERRADO — credenciais hardcoded
headers = {"Authorization": "Bearer mysecrettoken123"}

# ❌ ERRADO — lendo env var diretamente (fora do settings)
token = os.getenv("API_TOKEN")

# ✅ CORRETO — via get_settings()
token = get_settings().ats_api.token
```

---

## 4. Erros e Respostas Padronizadas

### 4.1 Rails — render helpers (nunca `render json:` espalhado)

```ruby
# Sucesso
render_success(@job, serializer: JobSerializer)               # 200
render_success(@job, serializer: JobSerializer, status: :created) # 201
render_no_content                                              # 204

# Erros
render_error(@job, status: :unprocessable_entity)            # 422 + model.errors
render_not_found("Job")                                       # 404
render_simple_error("Não autorizado", status: :forbidden)    # 403
render json: { error: "Invalid email or password" }, status: :unauthorized  # 401 (sessions)
```

**Formato de resposta de erro 422:**
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
# ❌ Formatos inconsistentes entre controllers
render json: @job                                   # sem serializer, sem estrutura
render json: { success: false, msg: "erro" }        # formato fora do padrão
render json: { message: "Not found" }, status: 404  # usar render_not_found
```

### 4.2 FastAPI — HTTPException com status correto

```python
# ✅ Mapeamento correto de erros
raise HTTPException(status_code=400, detail="Parâmetro obrigatório ausente")
raise HTTPException(status_code=401, detail="Token ausente ou inválido")
raise HTTPException(status_code=403, detail="Sem permissão para esta operação")
raise HTTPException(status_code=404, detail="Vaga não encontrada")
raise HTTPException(status_code=422, detail="Nível de senioridade inválido")
raise HTTPException(status_code=429, detail="Rate limit excedido")
raise HTTPException(status_code=500, detail="Internal error")

# ✅ Logger com exc_info obrigatório para erros inesperados
except Exception as e:
    logger.error(f"Chat falhou: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal error")

# ❌ ERRADO
return {"error": "algo deu errado"}     # sem status HTTP
print(f"Erro: {e}")                      # print proibido
logger.error(str(e))                     # sem exc_info=True (sem stack trace)
```

---

## 5. Serialização de Dados

### 5.1 Rails — `JSONAPI::Serializer` — código real do `ats_api`

```ruby
# app/serializer/job_serializer.rb
class JobSerializer
  include JSONAPI::Serializer

  attributes(
    :id, :title, :description, :user_id, :account_id,
    :created_at, :updated_at, :provider, :provider_job_id,
    :company_id, :published_date, :application_deadline,
    :is_remote, :city, :state, :country, :job_url,
    :career_page_id, :career_page_name, :career_page_url,
    :career_page_logo, :friendly_badge, :disabilities, :workplace_type
  )
end
```

```ruby
# app/serializer/apply_serializer.rb
# frozen_string_literal: true
class ApplySerializer
  include JSONAPI::Serializer

  attributes(
    :id, :candidate_id, :job_id, :selective_process_id,
    :is_deleted, :created_at, :updated_at
  )
end
```

**Regras de serializer:**
- `include JSONAPI::Serializer` em todos os serializers
- `# frozen_string_literal: true` obrigatório
- Nunca expor campos sensíveis: `password_digest`, tokens internos
- Um serializer por model

**Resposta JSONAPI de list (padrão `perform_search`):**
```json
{
  "data": [
    { "id": 1, "title": "Dev Rails", "user_id": 5, ... }
  ],
  "meta": {
    "total": 42,
    "aggregators": {}
  }
}
```

### 5.2 Python — Pydantic no `recruiter_agent_v5`

```python
# src/api.py — schemas reais do projeto
class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str | None = None
    hub_mode: bool = True
    context_data: Dict[str, Any] = Field(default_factory=dict)
```

Padrão para novos schemas:
```python
class MinhaRequisicao(BaseModel):
    """Docstring da request."""
    campo_obrigatorio: str = Field(..., description="Descrição clara do campo")
    campo_opcional: Optional[str] = Field(None, description="Opcional — pode ser None")
    limite: int = Field(default=20, ge=1, le=100, description="Entre 1 e 100")

class MinhaResposta(BaseModel):
    """Docstring da response."""
    success: bool
    dados: List[Dict[str, Any]]
    total: int = 0
```

---

## 6. Testes de Backend

### 6.1 Rails — RSpec com FactoryBot — código real do `ats_api`

**Estrutura:**
```
spec/
  rails_helper.rb                              ← FactoryBot, Shoulda, AuthHelper, JWT
  factories/
    accounts.rb                                ← factory :account
    users.rb                                   ← factory :user (associa :account)
    jobs.rb                                    ← factory :job (sequence para unicidade)
    candidates.rb                              ← factory :candidate (campos completos)
    applies.rb
    selective_processes.rb
  requests/v1/
    sessions_spec.rb
    users/jobs_controller_spec.rb
    users/applies_controller_spec.rb
    users/candidates_controller_spec.rb
    users/selective_processes_controller_spec.rb
```

**Factories — código real:**
```ruby
# spec/factories/accounts.rb
FactoryBot.define do
  factory :account do
    name    { Faker::Name.name }
    tenant  { Faker::Name.name }
    staging_tenant { Faker::Name.name }
  end
end

# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email    { Faker::Internet.email }
    password { "password123" }
    association :account
  end
end

# spec/factories/jobs.rb
FactoryBot.define do
  factory :job do
    title       { Faker::Job.title }
    description { Faker::Lorem.paragraph }
    association :user
    account { user.account }                        # conta do mesmo usuário

    # sequence garante unicidade no índice composto
    sequence(:provider)        { |n| "provider_test_#{n}" }
    sequence(:provider_job_id) { |n| "job_id_test_#{n}" }

    is_remote      { Faker::Boolean.boolean }
    city           { Faker::Address.city }
    state          { Faker::Address.state_abbr }
    country        { Faker::Address.country_code }
    workplace_type { ['on_site', 'hybrid', 'remote'].sample }
    published_date { Faker::Date.backward(days: 30) }
  end
end
```

**Request spec — código real de `sessions_spec.rb`:**
```ruby
require 'rails_helper'

RSpec.describe "V1::Sessions API", type: :request do
  let(:user)    { create(:user, password: "password123") }
  let(:headers) { { "Content-Type" => "application/json" } }

  describe "POST /v1/sessions" do
    context "with valid credentials" do
      it "returns token and user" do
        post "/v1/sessions",
          params: { email: user.email, password: "password123" }.to_json,
          headers: headers

        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json["token"]).to be_present
        expect(json["user"]["email"]).to eq(user.email)
      end
    end

    context "with invalid credentials" do
      it "returns unauthorized" do
        post "/v1/sessions",
          params: { email: user.email, password: "wrong" }.to_json,
          headers: headers

        expect(response).to have_http_status(:unauthorized)
        expect(JSON.parse(response.body)["error"]).to eq("Invalid email or password")
      end
    end
  end

  describe "GET /v1/me" do
    context "with valid token" do
      let(:token) { JWT.encode({ user_id: user.id }, Rails.application.secret_key_base) }

      it "returns current user" do
        get "/v1/me", headers: headers.merge("Authorization" => "Bearer #{token}")
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)["user"]["email"]).to eq(user.email)
      end
    end

    context "without token" do
      it "returns unauthorized" do
        get "/v1/me", headers: headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
```

**Request spec de resource — código real de `jobs_controller_spec.rb`:**
```ruby
# frozen_string_literal: true
require 'rails_helper'

RSpec.describe 'V1::Users::Jobs API', type: :request do
  let(:user)       { create(:user) }
  let(:other_user) { create(:user) }

  let(:no_auth_headers)      { { 'Content-Type' => 'application/json' } }
  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token',
                                  'Content-Type' => 'application/json' } }

  describe 'GET /v1/users/jobs' do
    before do
      Current.user = user
      create_list(:job, 3, user: user)
      create_list(:job, 2, user: other_user)
      Job.reindex   # ← Elasticsearch: reindexar após criar dados de teste
    end

    context 'quando autenticado' do
      it 'retorna TODOS os jobs no sistema' do
        get '/v1/users/jobs', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        expect(JSON.parse(response.body)['data'].size).to eq(5)
      end
    end

    context 'quando não autenticado' do
      it 'retorna não autorizado' do
        get '/v1/users/jobs', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'com token inválido' do
      it 'retorna não autorizado' do
        get '/v1/users/jobs', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/jobs' do
    let(:valid_params) do
      { job: { title: 'Dev Rails', description: 'Descrição',
               user_id: user.id, account_id: user.account.id } }
    end
    let(:invalid_params) { { job: { title: '', description: 'Sem título' } } }

    context 'quando autenticado com atributos válidos' do
      it 'cria um novo job' do
        expect {
          post '/v1/users/jobs',
            params: valid_params.to_json,
            headers: auth_headers(user)
        }.to change(Job, :count).by(1)
        expect(response).to have_http_status(:created)
      end
    end

    context 'com atributos inválidos' do
      it 'retorna 422' do
        post '/v1/users/jobs',
          params: invalid_params.to_json,
          headers: auth_headers(user)
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
```

**Regras de teste Rails:**
- `context` descreve a condição em português (`quando autenticado`)
- `it` descreve o resultado em português (`retorna todos os jobs`)
- Sempre testar: autenticado ✓ / não autenticado ✓ / token inválido ✓
- Sempre testar: params válidos ✓ / params inválidos ✓
- `Job.reindex` após create quando Elasticsearch está envolvido

### 6.2 Python — pytest com mocks — código real do `recruiter_agent_v5`

```python
# tests/integration/test_easy_cases.py — código real do repositório
"""
Testes de integração end-to-end - Casos Fáceis (Easy)
Testa comportamento completo do sistema com perguntas simples.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import patch, Mock
from src.workflow.graph import WorkflowOrchestrator
from tests.mocks.mock_api_client import MockAPIClient

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
with open(TEST_CASES_PATH, 'r', encoding='utf-8') as f:
    TEST_CASES_DATA = json.load(f)
EASY_CASES = TEST_CASES_DATA.get("easy", [])

@pytest.fixture
def mock_api_client():
    return MockAPIClient()

@pytest.fixture
def orchestrator_with_mock(mock_api_client):
    with patch('src.agents.api_executor.ATSAPIClient', return_value=mock_api_client):
        orchestrator = WorkflowOrchestrator()
        orchestrator.api_executor.api_client = mock_api_client
        return orchestrator

class TestEasyCases:
    @pytest.mark.parametrize("test_case", EASY_CASES, ids=[tc["id"] for tc in EASY_CASES])
    def test_easy_case(self, test_case, orchestrator_with_mock):
        """Testa um caso fácil end-to-end: intent → plano → execução → resposta."""
        state = orchestrator_with_mock.process_query(test_case["question"])
        validator = ResultValidator(test_case)
        is_valid, errors, warnings = validator.validate(state)
        assert is_valid, f"Falhou: {errors}"
```

```python
# tests/test_fairness.py — padrão unitário real
class TestAnonymizeForLlm:

    def test_returns_tuple(self):
        candidates = [{"id": 1, "name": "João", "score": 85}]
        result = anonymize_for_llm(candidates)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_anonymized_list_has_candidate_code(self):
        candidates = [{"id": 1, "name": "João", "score": 85}]
        anonymized, _ = anonymize_for_llm(candidates)
        assert anonymized[0]["candidate_code"] == "C001"

    def test_removes_pii_fields(self):
        candidates = [{"id": 1, "name": "João Silva", "email": "joao@ex.com", "score": 85}]
        anonymized, _ = anonymize_for_llm(candidates)
        assert "name" not in anonymized[0]
        assert "email" not in anonymized[0]
```

**Instrução TDD do repositório (`.github/instructions/tdd.instructions.md`):**
```
Ciclo obrigatório:
  1. RED   — escreva o teste, execute, confirme que FALHA pela razão certa
  2. GREEN — código mínimo para o teste passar (nada além)
  3. REFACTOR — com testes passando, melhore clareza e simplicidade
  4. COMMIT — só depois do refactor com tudo verde
```

**Pirâmide de testes do `recruiter_agent_v5`:**
```
tests/
  integration/
    test_easy_cases.py        → queries diretas, intenção clara
    test_medium_cases.py      → queries com ambiguidade, filtros compostos
    test_hard_cases.py        → multi-turno, contexto necessário
    test_very_hard_cases.py   → edge cases, falhas de API, timeouts
  test_fairness.py            → anonimização, PII, viés
  test_security.py            → autenticação, autorização
  test_pii_filter.py          → LGPD: campos sensíveis
  mocks/
    mock_api_client.py        → mock do cliente Rails — nunca chamar API real nos testes
```

---

## 7. Migrações de Banco de Dados

### 7.1 Migrações reais do `ats_api`

```ruby
# db/migrate/20250630171206_create_jobs.rb
class CreateJobs < ActiveRecord::Migration[7.1]
  def change
    create_table :jobs do |t|
      t.string :title
      t.text   :description
      t.references :user,    null: false, foreign_key: true  # FK obrigatória
      t.references :account, null: false, foreign_key: true  # FK obrigatória
      t.timestamps
    end
  end
end
```

```ruby
# db/migrate/20250714142059_create_applies.rb
class CreateApplies < ActiveRecord::Migration[7.1]
  def change
    create_table :applies do |t|
      t.references :candidate,        null: false, foreign_key: true
      t.references :job,              null: false, foreign_key: true
      t.references :selective_process, null: false, foreign_key: true
      t.boolean :is_deleted, default: false, null: false   # soft delete
      t.timestamps
    end
  end
end
```

```ruby
# db/migrate/20250714150818_add_account_in_others_models.rb
class AddAccountInOthersModels < ActiveRecord::Migration[7.1]
  def change
    add_reference :applies,             :account, null: false, foreign_key: true
    add_reference :candidates,          :account, null: false, foreign_key: true
    add_reference :selective_processes, :account, null: false, foreign_key: true
  end
end
```

**Regras de migration:**

| Regra | Correto | Errado |
|-------|---------|--------|
| Versão | `ActiveRecord::Migration[7.1]` | Sem versão |
| FKs | `null: false, foreign_key: true` | Sem null constraint |
| Soft delete | `t.boolean :is_deleted, default: false, null: false` | `DROP` de dados |
| Nomenclatura | `create_jobs`, `add_account_to_applies` | Nomes genéricos |
| Atomicidade | Uma responsabilidade por migration | Misturar create_table + add_column de outra |

**Nomenclatura de migrations:**
```
YYYYMMDDHHMMSS_verbo_substantivo.rb

20250630171206_create_jobs.rb                  → nova tabela
20250630164633_add_account_to_users.rb         → adicionar coluna/referência
20250714150818_add_account_in_others_models.rb → múltiplas referências relacionadas
20250708191812_change_message.rb               → alterar coluna existente
```

---

## 8. Nomenclatura de Rotas e Recursos

### 8.1 `config/routes.rb` — código real do `ats_api`

```ruby
# frozen_string_literal: true
Rails.application.routes.draw do
  mount ActionCable.server => "/cable"
  get "up" => "rails/health#show"   # health check para load balancer

  namespace :v1 do
    # ── Auth (fora de namespace users — são rotas de sessão) ──
    post "sessions", to: "sessions#create"
    get  "me",       to: "sessions#me"
    post "logout",   to: "sessions#logout"

    namespace :users do
      # ── Padrão CRUD explícito (projeto não usa resources :x) ──
      get    "jobs",     to: "jobs#index"
      get    "jobs/:id", to: "jobs#show"
      post   "jobs",     to: "jobs#create"
      put    "jobs/:id", to: "jobs#update"
      delete "jobs/:id", to: "jobs#destroy"

      # ── applies, candidates, selective_processes, messages: mesmo padrão ──

      # ── Rotas de users com path semântico diferente ──
      get    "search",     to: "users#index"
      get    "search/:id", to: "users#show"
      post   "create",     to: "users#create"
      put    "edit/:id",   to: "users#update"
      delete "delete/:id", to: "users#destroy"
    end
  end
end
```

**Regras de rota:**

| Regra | Correto | Errado |
|-------|---------|--------|
| Versionamento | `namespace :v1` | Sem versão |
| Recursos plural | `/jobs`, `/candidates` | `/job`, `/candidate` |
| Sub-recursos | `namespace :users` para recursos do usuário | Flat sem namespace |
| Verbos HTTP | `get/post/put/delete` corretos | `post` para tudo |
| Resource IDs | `/:id` | `/job_detail/:id`, `/get_job/:id` |
| Health check | `get "up" => "rails/health#show"` | Ausente |

**Nota:** o projeto usa rotas manuais. `resources :jobs, only: [...]` é equivalente e preferível para CRUDs completos por ser mais conciso:

```ruby
# ✅ Equivalente ao padrão manual do projeto — mais conciso
namespace :v1 do
  namespace :users do
    resources :jobs,               only: %i[index show create update destroy]
    resources :applies,            only: %i[index show create update destroy]
    resources :candidates,         only: %i[index show create update destroy]
    resources :selective_processes, only: %i[index show create update destroy]
    resources :messages,           only: %i[index show create update destroy]
  end
end
```

### 8.2 FastAPI — prefixos por domínio (`recruiter_agent_v5`)

```python
# src/api.py — padrão real
app = FastAPI(title="Recruiter Agent v5 — Streaming API")

# Endpoints no root — sem prefixo de versão no recruiter_agent_v5
@app.post("/chat")
async def chat(req: ChatRequest): ...

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest): ...
```

Para novos módulos com `APIRouter`, seguir o padrão de prefix funcional:
```python
router = APIRouter(prefix="/applies",  tags=["applies"])
router = APIRouter(prefix="/sourcing", tags=["sourcing"])
router = APIRouter(prefix="/jobs",     tags=["jobs"])
```

---

## Checklist de PR — backend

**Rails (`ats_api`):**
- [ ] `# frozen_string_literal: true` na primeira linha de todo `.rb`
- [ ] Controller dentro de namespace `V1::Users::`
- [ ] `before_action` com `only:` explícito
- [ ] Strong parameters com `.permit(...)` completo
- [ ] Serializer JSONAPI criado — sem `.as_json` ou `.to_json` solto
- [ ] Soft delete em applies (`update(is_deleted: true)`), não `.destroy`
- [ ] Spec de request: autenticado ✓ / não autenticado ✓ / token inválido ✓ / params válidos ✓ / params inválidos ✓
- [ ] Factory FactoryBot com Faker para dados realistas + sequence para campos únicos
- [ ] Migration: `null: false` em FKs + `foreign_key: true`

**Python (`recruiter_agent_v5`):**
- [ ] `logger = logging.getLogger(__name__)` no topo do módulo
- [ ] `get_settings()` para config — sem `os.getenv()` avulso
- [ ] `create_tracked_llm()` para instanciar LLM — nunca `ChatGoogleGenerativeAI()` direto
- [ ] `DomainResponse` como único tipo de retorno das actions — sem `dict` raw
- [ ] `@register_domain` na classe de domínio
- [ ] `logger.error(..., exc_info=True)` em todos os `except Exception`
- [ ] Mock da `MockAPIClient` nos testes — sem chamar Rails API real
- [ ] Ciclo TDD: RED → GREEN → REFACTOR antes do commit

> **Fonte**: todo código deste documento foi lido diretamente dos repositórios `ats_api` e `recruiter_agent_v5` no GitHub WeDOTalent.
> Para padrões de frontend, ver `docs/specs/standards/FRONTEND_STANDARDS.md`.
