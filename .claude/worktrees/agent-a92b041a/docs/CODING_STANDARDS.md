# Coding Standards — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-24
> Baseado no código MAIS BEM ESCRITO de cada repositório — padrão aspiracional.
> Qualquer PR que contradiga este documento deve justificar a exceção explicitamente.

---

## 1. Convenções de Nomenclatura

### 1.1 Arquivos

| Contexto | Convenção | Exemplos |
|---------|-----------|---------|
| Componentes Vue | `PascalCase.vue` prefixado com `Lia` | `LiaField.vue`, `LiaTabBar.vue` |
| Composables Vue | `camelCase.ts` prefixado com `use` | `useCandidate.ts`, `usePipeline.ts` |
| Stores Pinia | `camelCase.ts` sufixado com `Store` | `candidateStore.ts` |
| Controllers Rails | `snake_case_controller.rb` | `jobs_controller.rb` |
| Models Rails | `snake_case.rb` singular | `job.rb`, `apply.rb` |
| Concerns Rails | `PascalCase.rb` | `SearchRenderer.rb`, `AccountScopable.rb` |
| Endpoints FastAPI | `snake_case.py` | `wsi.py`, `sourcing.py`, `candidates.py` |
| Domains Python | `snake_case.py` | `domain.py`, `api_client.py`, `prompts.py` |
| Actions Python | `snake_case.py` por responsabilidade | `search.py`, `scoring.py`, `bulk.py` |
| Configs Python | `snake_case_config.py` | `gemini_config.py`, `celery_config.py` |
| Testes Python | `test_snake_case.py` | `test_easy_cases.py` |

### 1.2 Variáveis e Funções

| Linguagem | Variáveis/Funções | Constantes | Classes |
|-----------|------------------|------------|---------|
| TypeScript/Vue | `camelCase` | `SCREAMING_SNAKE_CASE` | `PascalCase` |
| Ruby | `snake_case` | `SCREAMING_SNAKE_CASE` | `PascalCase` |
| Python | `snake_case` | `SCREAMING_SNAKE_CASE` | `PascalCase` |

### 1.3 Componentes Vue: prefixo obrigatório `Lia`

Todos os componentes do design system (`wedo-nuxt`) e da plataforma usam o prefixo `Lia`:

```
LiaField        → campo de formulário com slot IA
LiaTabBar       → navegação por abas
LiaPageHeader   → header de página
LiaSectionHeader → header de seção
LiaBigFiveChart → gráfico Big Five
```

---

## 2. Estrutura Padrão de Componente Vue

Extraída dos melhores componentes do `wedo-nuxt`. A ordem das seções é obrigatória:

```
1. <template>
2. <script setup lang="ts">
3. <style scoped>
```

### 2.1 Template: HTML semântico com BEM

```vue
<template>
    <div class="lia-field" :class="{ 'lia-field--disabled': disabled }">
        <!-- Label + pill opcional -->
        <div class="lia-field__meta">
            <span class="lia-field__label">{{ label }}</span>
            <div v-if="comment" class="lia-field__pill">{{ comment }}</div>
        </div>

        <!-- Área de conteúdo -->
        <div class="lia-field__content">
            <div class="lia-field__input">
                <slot />
            </div>
            <button
                v-if="showRobotButton"
                :disabled="disabled"
                class="lia-field__robot-btn"
                type="button"
                @click="$emit('liaAddData')"
            >
                <!-- SVG inline — sem src externo para ícones de UI -->
            </button>
        </div>
    </div>
</template>
```

**Regras de template:**
- `v-if` antes de `v-for`. Nunca ambos no mesmo elemento.
- `type="button"` explícito em todo `<button>` dentro de form.
- Comentários HTML apenas para delimitar seções visuais distintas.
- `key` obrigatório em `v-for`: sempre usar ID de negócio, nunca `index`.

### 2.2 Script: `withDefaults` + JSDoc nas props

```vue
<script setup lang="ts">
// 1. Interfaces exportadas (quando outros componentes precisam)
export interface TabItem {
    key: string
    label: string
}

// 2. Props com tipos TypeScript e JSDoc
withDefaults(defineProps<{
    /** Field label text (mandatory) */
    label: string
    /** Optional comment / pill text */
    comment?: string
    /** Disables all interactions */
    disabled?: boolean
    /** Toggle state (v-model) */
    modelValue?: boolean
    /** Whether to show the robot button */
    showRobotButton?: boolean
}>(), {
    comment: undefined,
    disabled: false,
    modelValue: true,
    showRobotButton: true,
})

// 3. Emits com tipagem explícita
defineEmits<{
    /** Fired when the robot button is clicked */
    (e: 'liaAddData'): void
    /** Toggle change event */
    (e: 'update:modelValue', value: boolean): void
}>()

// 4. Composables (se necessário)
// 5. Estado reativo
// 6. Computed
// 7. Métodos
</script>
```

**Regras de script:**
- Sempre `<script setup lang="ts">` — nunca Options API.
- `withDefaults` quando props têm valores padrão.
- JSDoc `/** ... */` em todas as props e emits — é a documentação do componente.
- Interfaces exportadas acima das props (outros componentes podem importar).
- Sem lógica de negócio no componente — extrair para composable.

### 2.3 Style: BEM com tokens Vuetify

```vue
<style scoped>
/* ── Bloco raiz ── */
.lia-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

/* ── Elementos (__) ── */
.lia-field__meta {
    display: flex;
    align-items: center;
    gap: 8px;
}

.lia-field__label {
    font-family: 'Open Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    line-height: 17px;
    letter-spacing: -0.16px;
    color: rgb(var(--v-theme-secondary));
}

/* ── Modificadores (--) ── */
.lia-field--disabled {
    opacity: 0.6;
    pointer-events: none;
}

/* ── Transições ── */
.lia-field__robot-btn {
    transition: color 0.15s ease, background 0.15s ease;
}
</style>
```

**Regras de estilo:**
- Nomenclatura BEM: `.lia-bloco__elemento--modificador`.
- Tokens de cor via CSS vars Vuetify: `rgb(var(--v-theme-primary))`, nunca hex hardcoded.
- `shadow-sm` é o padrão. **`shadow-xl` e `shadow-2xl` são proibidos.**
- Tipografia: Open Sans para texto de UI. 11px/17px para labels e tabs.
- `transition` em todos os elementos interativos (hover, active, disabled).
- Comentários de seção com `/* ── Título ── */`.

---

## 3. Estrutura Padrão de Controller Rails

### 3.1 Controller completo

```ruby
# frozen_string_literal: true   ← OBRIGATÓRIO em todo arquivo .rb

module V1
  module Users
    class JobsController < ApplicationController
      # 1. Before actions — ordem: auth primeiro, depois recursos
      before_action :authorize_request
      before_action :set_job, only: %i[show update destroy]
      before_action :ensure_owner, only: %i[update destroy]

      # 2. Actions públicas — apenas o essencial
      def index
        perform_search(model: Job, serializer: JobSerializer)
      end

      def show
        render_success(@job, serializer: JobSerializer)
      end

      def create
        @job = @current_user.jobs.build(job_params.merge(account_id: @current_user.account_id))

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

      # 3. set_* — finder de recurso com 404 embutido
      def set_job
        @job = Job.find_by(id: params[:id])
        render_not_found("Job") unless @job
      end

      # 4. ensure_* — guarda de autorização
      def ensure_owner
        return if @job.user_id == @current_user.id
        render_simple_error("Não autorizado a realizar esta ação neste job", status: :forbidden)
      end

      # 5. *_params — strong parameters sempre explícitos
      def job_params
        params.require(:job).permit(:title, :description, :user_id, :account_id)
      end
    end
  end
end
```

**Regras de controller:**
- `# frozen_string_literal: true` é a primeira linha de todo arquivo `.rb`.
- Módulos de namespace obrigatórios: `V1::Users::JobsController`.
- `before_action` com `only:` explícito — nunca aplicar a todas as actions por default.
- Ordem na seção `private`: `set_*` → `ensure_*` → `*_params`.
- Nunca SQL raw — sempre ActiveRecord.
- Usar helpers de render (`render_success`, `render_error`, `render_no_content`, `render_not_found`) — não `render json:` diretamente.

### 3.2 Model padrão

```ruby
class Job < ApplicationRecord
  # 1. Includes de concerns
  include Searchable

  # 2. Associations — has_many com dependent, belongs_to
  has_many :selective_processes, dependent: :destroy
  belongs_to :user
  belongs_to :account, optional: true

  # 3. Validations
  validates :title, presence: true
  validates :description, presence: true

  # 4. Callbacks — com parcimônia, apenas lógica de domínio
  after_create :create_default_selective_processes

  private

  def create_default_selective_processes
    # lógica de negócio em método privado nomeado
  end
end
```

**Regras de model:**
- Ordem obrigatória: includes → associations → validations → callbacks → private.
- Soft delete via campo `is_deleted: true` (não `destroy` real para applies).
- Callbacks apenas para lógica que pertence ao ciclo de vida do modelo.
- Lógica complexa em `app/services/`, não em callbacks.

### 3.3 Concerns para comportamento reutilizável

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

Incluir `ResourceLoader` no controller elimina o `set_resource` manual em CRUDs padrão.

---

## 4. Estrutura Padrão de Endpoint FastAPI (Python)

### 4.1 Módulo real — `src/api.py` do `recruiter_agent_v5` (GitHub)

O `recruiter_agent_v5` usa FastAPI com SSE (Server-Sent Events) para streaming. Abaixo o código
real do arquivo `src/api.py`:

```python
# src/api.py — código real do repositório recruiter_agent_v5 (GitHub WeDOTalent)
import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from src.services.message_router import MessageRouter

logger = logging.getLogger(__name__)

app = FastAPI(title="Recruiter Agent v5 — Streaming API")

# ── Singleton lazy — instanciado na primeira requisição ──
_router: MessageRouter = None

def _get_router() -> MessageRouter:
    global _router
    if _router is None:
        _router = MessageRouter()
    return _router


# ── Schema Pydantic: campos com Field e defaults explícitos ──
class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    domain: str | None = None
    hub_mode: bool = True
    context_data: Dict[str, Any] = Field(default_factory=dict)


# ── Endpoint síncrono: POST /chat ──
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


# ── Endpoint SSE streaming: POST /chat/stream ──
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def progress_sender(payload: dict):
        try:
            loop.call_soon_threadsafe(queue.put_nowait, payload)
        except Exception:
            pass

    result_holder: Dict[str, Any] = {}
    error_holder: Dict[str, Any] = {}

    def _run():
        try:
            router = _get_router()
            result_holder["data"] = router.route({
                "question": req.message,
                "domain": req.domain,
                "context_data": {**req.context_data, "session_id": req.session_id,
                                  "progress_sender": progress_sender},
                "session_id": req.session_id,
                "hub_mode": req.hub_mode,
            })
        except Exception as e:
            logger.error(f"[SSE] Route error: {e}", exc_info=True)  # exc_info obrigatório
            error_holder["error"] = str(e)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    async def event_generator():
        loop.run_in_executor(None, _run)
        start = time.time()
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=200)
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": json.dumps({"keepalive": True})}
                continue
            if event is None:
                break
            yield {"event": "progress",
                   "data": json.dumps(event, default=str, ensure_ascii=False)}

        total_ms = (time.time() - start) * 1000
        final = ({"status": "error", "error": error_holder["error"], "total_ms": round(total_ms)}
                 if error_holder else
                 {"status": "completed", "message": result_holder.get("data", {}).get("message", ""),
                  "total_ms": round(total_ms)})
        yield {"event": "stream_end", "data": json.dumps(final, ensure_ascii=False)}

    return EventSourceResponse(event_generator())


# ── Health check ──
@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Estrutura obrigatória de novos módulos FastAPI:**

```python
# 1. Stdlib imports
import logging
from typing import Any, Dict, List, Optional

# 2. Third-party imports (httpx, não requests — ver seção 8)
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# 3. Internal imports (prefixo src., não app.)
from src.config.settings import get_settings
from src.domains.base import DomainResponse

# 4. Logger — __name__ em todo módulo
logger = logging.getLogger(__name__)

# 5. Router com prefix funcional
router = APIRouter(prefix="/meu-recurso", tags=["meu-recurso"])

# 6. Schemas Pydantic nomeados: XxxRequest / XxxResponse
class MeuRequest(BaseModel):
    campo: str = Field(..., description="Descrição do campo")
    limite: int = Field(default=20, ge=1, le=100)

# 7. Endpoint: try/except com HTTPException
@router.post("/buscar")
async def buscar(req: MeuRequest):
    try:
        resultado = servico.buscar(req)
        return {"success": True, "data": resultado}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Busca falhou: {e}", exc_info=True)   # exc_info=True obrigatório
        raise HTTPException(status_code=500, detail="Internal error")
```

**Regras de endpoint FastAPI:**
- Imports em 3 blocos: stdlib → third-party → internal. Linha em branco entre blocos.
- Prefixo interno: sempre `src.` — nunca `app.` (padrão real do projeto).
- `logger = logging.getLogger(__name__)` em todo módulo.
- Schemas Pydantic com nomes explícitos: `XxxRequest` e `XxxResponse`.
- `Field(default_factory=...)` para listas e dicts opcionais (evita mutável como default).
- Erros de validação: `HTTPException(422)`. Erros de sistema: `HTTPException(500)` + `logger.error(..., exc_info=True)`.
- `httpx` para chamadas HTTP internas — **nunca `requests`** (ver seção 8).

---

## 5. Estrutura Padrão de Domain Python (recruiter_agent_v5)

### 5.1 Domain class

```python
import logging
from typing import List, Dict, Any, Optional

from src.domains.base import DomainPrompt, DomainAction, DomainContext, DomainResponse, ActionType
from src.domains.registry import register_domain
from src.utils.llm_factory import create_tracked_llm

logger = logging.getLogger(__name__)


@register_domain                         # auto-registro no DomainRegistry
class AppliesDomain(DomainPrompt):

    def __init__(self) -> None:
        self._actions = AppliesActions()
        self._llm = None                 # lazy init — não instanciar no __init__

    @property
    def llm(self):                       # lazy property — LLM só quando necessário
        if self._llm is None:
            self._llm = create_tracked_llm(  # NUNCA instanciar LLM diretamente
                temperature=0.0,
                service_name="AppliesDomain",
                operation="chat",
            )
        return self._llm

    @property
    def domain_id(self) -> str:
        return "applies"

    @property
    def domain_name(self) -> str:
        return "Gestao de Candidaturas"

    def get_allowed_actions(self) -> List[DomainAction]:
        return [
            DomainAction(
                id="search_applies",
                name="Buscar candidaturas",
                description="Busca candidaturas com filtros: nome, etapa, score, status",
                action_type=ActionType.QUERY,
                examples=("Candidatos dessa vaga", "Buscar Maria", "Score acima de 80"),
            ),
        ]
```

### 5.2 Action class

```python
import logging
from typing import Dict, Any

from src.domains.base import DomainContext, DomainResponse
from src.domains.applies.actions.base import BaseAppliesAction, require_job_id

logger = logging.getLogger(__name__)


class SearchActions(BaseAppliesAction):

    @require_job_id                      # decorator de validação de params
    def search_applies(
        self, params: Dict[str, Any], context: DomainContext, **kwargs
    ) -> DomainResponse:
        api = self.get_api_client(context)

        response = api.search_applies(
            job_id=params["job_id"],
            term=params.get("term"),
            page=params.get("page", 1),
        )

        # Early return em caso de erro
        if not response.success:
            return DomainResponse(
                success=False,
                message=f"Erro ao buscar candidaturas: {response.error}"
            )

        applies = response.data if isinstance(response.data, list) else []

        return DomainResponse(
            success=True,
            message=format_applies_table(applies, response.meta),
            data=applies,
            metadata={"total": len(applies), "job_id": params["job_id"]},
            suggestions=["Ver detalhes", "Filtrar por score", "Pipeline"],
        )
```

**Regras de domain/action Python:**
- `@register_domain` obrigatório na classe de domínio.
- `create_tracked_llm()` sempre — nunca `ChatGoogleGenerativeAI(...)` direto.
- `get_settings()` para configs — nunca `os.getenv()` espalhado pelo código.
- `DomainResponse` como único tipo de retorno de actions. Nunca `dict` raw.
- Early return: verificar erro antes de prosseguir. Evitar `if success: ... else: ...`.
- Type hints em todos os parâmetros e retornos de métodos públicos.
- `logging` — nunca `print()`.
- Prompts escritos em português brasileiro.

### 5.3 Config dataclass

```python
# src/config/gemini_config.py — código real do repositório recruiter_agent_v5 (GitHub)
"""
Gemini API configuration.
Single Responsibility: Manage Gemini API settings only.
"""
from dataclasses import dataclass


@dataclass(frozen=True)           # frozen=True — imutável após criação
class GeminiConfig:
    """Configuration for Google Gemini API."""
    api_key: str
    model: str = "gemini-1.5-flash-latest"   # valor real — não alterar sem alinhamento
    temperature: float = 0.0
```

**Regras de config:**
- Um arquivo por dataclass de config.
- `@dataclass(frozen=True)` — configs são imutáveis.
- Docstring de módulo com responsabilidade única.
- Nunca lógica de negócio em classes de config.

---

## 6. Padrão de Tratamento de Erros

### 6.1 Rails — render helpers, nunca `raise`

```ruby
# BOM — render helper com HTTP status semântico
def set_job
  @job = Job.find_by(id: params[:id])
  render_not_found("Job") unless @job          # 404
end

def ensure_owner
  return if @job.user_id == @current_user.id
  render_simple_error("Não autorizado", status: :forbidden)  # 403
end

def create
  if @job.save
    return render_success(@job, serializer: JobSerializer, status: :created)  # 201
  end
  render_error(@job, status: :unprocessable_entity)  # 422 com erros do model
end
```

### 6.2 FastAPI — HTTPException com códigos semânticos

```python
# BOM
@router.post("/search")
async def search_candidates(request: SourcingSearchRequest, db: AsyncSession = Depends(get_db)):
    try:
        results = await service.search(request, db)
        return SourcingSearchResponse(success=True, **results)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))   # validação
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))   # autorização
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)    # log completo
        raise HTTPException(status_code=500, detail="Internal error")


# RUIM — não fazer
def search_candidates(request):
    try:
        ...
    except:
        print(f"Error: {e}")     # PROIBIDO: print()
        return {"error": str(e)} # PROIBIDO: erro sem status HTTP correto
```

### 6.3 Python (domain actions) — DomainResponse com success=False

```python
# BOM — early return, mensagem em português
if not response.success:
    return DomainResponse(
        success=False,
        message=f"Erro ao buscar candidaturas: {response.error}"
    )

if not term:
    return DomainResponse(
        success=False,
        message="Qual o nome do candidato que você quer buscar?",
        needs_clarification=True,
    )

# RUIM — não fazer
try:
    result = api.search(...)
except Exception as e:
    print(e)         # PROIBIDO
    return None      # PROIBIDO: retornar None em vez de DomainResponse
```

---

## 7. Padrão de Escrita de Testes

### 7.1 Rails — RSpec por camada

```
spec/
  models/        → comportamento de model, validações, associations
  requests/      → endpoints HTTP (status, corpo, autenticação)
  factories/     → FactoryBot — dados de teste realistas
  support/       → helpers compartilhados
```

```ruby
# spec/requests/v1/users/jobs_spec.rb
RSpec.describe "V1::Users::Jobs", type: :request do
  let(:user) { create(:user) }
  let(:headers) { auth_headers(user) }   # helper de suporte

  describe "GET /v1/users/jobs" do
    context "when authenticated" do
      it "returns 200 with jobs list" do
        create_list(:job, 3, user: user)
        get "/v1/users/jobs", headers: headers
        expect(response).to have_http_status(:ok)
        expect(json_body["data"]).to have(3).items
      end
    end

    context "when unauthenticated" do
      it "returns 401" do
        get "/v1/users/jobs"
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
```

### 7.2 Python — por nível de dificuldade do caso de uso

```
tests/
  integration/
    test_easy_cases.py        → queries diretas, intenção clara (parametrize com test_cases.json)
    test_medium_cases.py      → queries com ambiguidade, filtros compostos
    test_hard_cases.py        → multi-turno, contexto necessário
    test_very_hard_cases.py   → edge cases, falhas de API, timeouts
  test_model_router.py        → testes unitários de roteamento LLM
  test_fairness.py            → anonimização, PII, DEI
  test_pii_filter.py          → campos sensíveis, LGPD
  test_security.py            → autenticação, autorização
  mocks/
    mock_api_client.py        → mock do cliente Rails API (via unittest.mock.patch)
```

**Testes unitários — código real de `tests/test_model_router.py` (GitHub `recruiter_agent_v5`):**

```python
# tests/test_model_router.py — código real
import pytest
from src.services.model_router import ModelRouter, get_model_router, ModelChoice


class TestModelRouter:

    def setup_method(self):
        self.router = ModelRouter(
            model_fast="gemini-2.5-flash",
            model_default="gemini-2.5-flash",
            model_heavy="gemini-2.5-pro",
        )

    def test_fast_listar(self):
        choice = self.router.choose("listar vagas ativas")
        assert choice.tier == "fast"
        assert choice.model == "gemini-2.5-flash"

    def test_fast_quantas(self):
        choice = self.router.choose("quantas vagas ativas temos?")
        assert choice.tier == "fast"

    def test_heavy_diagnostico(self):
        choice = self.router.choose("diagnostico completo da vaga 123")
        assert choice.tier == "heavy"
        assert choice.model == "gemini-2.5-pro"

    def test_default_buscar_candidato(self):
        choice = self.router.choose("buscar candidatos com react e node")
        assert choice.tier == "default"
```

**Testes de integração — código real de `tests/integration/test_easy_cases.py` (GitHub):**

```python
# tests/integration/test_easy_cases.py — código real
import pytest
import json
from pathlib import Path
from unittest.mock import patch     # ← mock via patch, nunca classe mock própria
from src.workflow.graph import WorkflowOrchestrator
from tests.mocks.mock_api_client import MockAPIClient

# Casos carregados de arquivo JSON — não hardcoded no teste
TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"
with open(TEST_CASES_PATH, 'r', encoding='utf-8') as f:
    TEST_CASES_DATA = json.load(f)
EASY_CASES = TEST_CASES_DATA.get("easy", [])


@pytest.fixture
def mock_api_client():
    return MockAPIClient()   # MockAPIClient, não MockAppliesAPIClient


@pytest.fixture
def orchestrator_with_mock(mock_api_client):
    # patch via unittest.mock — nunca injeção manual de dependência
    with patch('src.agents.api_executor.ATSAPIClient', return_value=mock_api_client):
        orchestrator = WorkflowOrchestrator()
        orchestrator.api_executor.api_client = mock_api_client
        return orchestrator


class TestEasyCases:
    # parametrize para rodar o mesmo teste com todos os casos do JSON
    @pytest.mark.parametrize("test_case", EASY_CASES, ids=[tc["id"] for tc in EASY_CASES])
    def test_easy_case(self, test_case, orchestrator_with_mock):
        """Testa um caso fácil end-to-end: intent → plano → execução → resposta."""
        state = orchestrator_with_mock.process_query(test_case["question"])
        validator = ResultValidator(test_case)
        is_valid, errors, _ = validator.validate(state)
        assert is_valid, f"Falhou nos casos: {errors}"
```

**Testes de fairness/PII — código real de `tests/test_fairness.py` (GitHub):**

```python
# tests/test_fairness.py — estrutura real
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
        assert "name" not in anonymized[0]     # PII removido
        assert "email" not in anonymized[0]    # PII removido
        assert "score" in anonymized[0]        # dado de negócio mantido
```

**Regras de teste Python:**
- Nome do método: `test_<ação>_<contexto>` descreve comportamento esperado, não implementação.
- Um assert por comportamento sempre que possível.
- `unittest.mock.patch` para APIs externas — **nunca** chamar serviços reais nos testes unitários.
- `MockAPIClient` (de `tests/mocks/`) — **não** criar mocks ad-hoc por classe de domínio.
- Casos de teste parametrizados carregados de JSON — não hardcoded em `@pytest.mark.parametrize`.
- `test_easy_cases` sempre passando antes de trabalhar em `test_hard_cases`.

---

## 8. O que está Explicitamente Proibido

Baseado no que **não existe** no código melhor escrito do projeto:

| Proibição | Motivo | Alternativa |
|-----------|--------|-------------|
| `print()` em qualquer arquivo Python | Não rastreável em produção | `logger.info/warning/error()` |
| `os.getenv()` fora do módulo de settings | Config espalhada é indetectável | `get_settings().atributo` |
| `requests` em Python | Síncrono, sem suporte a async | `httpx` (padrão real do projeto) |
| `datetime.utcnow()` | Deprecated no Python 3.12+ | `datetime.now(timezone.utc)` |
| Instanciar LLM diretamente (`ChatGoogleGenerativeAI(...)`) | Sem rastreamento LangSmith | `create_tracked_llm(...)` |
| Retornar `dict` raw de domain actions | Quebra contrato de tipo | `DomainResponse(...)` |
| `shadow-xl` ou `shadow-2xl` em componentes | Viola Design System LIA v4.x | `shadow-sm` |
| Hex de cor hardcoded em CSS de tema | Inconsistência com dark mode | `rgb(var(--v-theme-primary))` |
| `any` no TypeScript sem justificativa em comentário | Perde type safety | Tipo explícito ou `unknown` |
| SQL raw em controllers Rails | XSS/injection, sem log | ActiveRecord `.where(...)` |
| Lógica de negócio em endpoint FastAPI | Não testável isoladamente | Mover para `services/` ou `domains/` |
| `# frozen_string_literal: true` ausente em `.rb` | Performance e mutabilidade | Adicionar na primeira linha |
| Componente Vue sem `lang="ts"` | TypeScript não aplicado | `<script setup lang="ts">` |
| Props Vue sem tipo TypeScript | Sem autocomplete, sem validação | `defineProps<{ label: string }>()` |
| `before_action` sem `only:` explícito | Aplica auth em rotas não desejadas | `before_action :authorize_request, only: %i[show]` |
| Comentários de código sem propósito real | Ruído no código (instrução base do projeto) | Código autoexplicativo; comentário só para "por quê" |
| `except Exception: raise` (no-op) | Não trata, não loga, re-raise silencioso | Tratar, ou `logger.error(..., exc_info=True)` + raise |
| `\b` antes de `\+` em regex | Word boundary antes de `+` não funciona | Testar regex antes de commitar |
| Acesso direto ao banco do ATS pelos agentes | Viola isolamento de tenant | Chamar `ats_api` via REST |

---

## 9. Padrões de Logging

```python
# PADRÃO Python — um logger por módulo, nível correto
# Fonte: .github/instructions/python-general.instructions.md (GitHub recruiter_agent_v5)
import logging
logger = logging.getLogger(__name__)

# ✅ Padrões corretos — prefixo [NomeDoServiço] para filtrar nos logs
logger.info(f"[MyService] Processing: {query[:80]}")           # evento normal
logger.warning(f"[MyService] Retry attempt {attempt}")         # falha recuperável
logger.error(f"[MyService] Error: {e}", exc_info=True)         # falha grave + stack trace
logger.debug(f"[MyService] Cache hit for session {session_id}") # diagnóstico

# ❌ PROIBIDO
print(f"Processing {query}")                                   # print no lugar de logger
logger.error(str(e))                                           # sem exc_info=True — sem stack trace
```

```ruby
# PADRÃO Rails — código real de sessions_controller.rb (GitHub ats_api)
Rails.logger.error "JWT Decode Error: #{e.message}"   # único logger real encontrado no código
```

**Regras:**
- `exc_info=True` obrigatório no `logger.error()` para incluir stack trace completo.
- Prefixo `[NomeDoServiço]` nas mensagens Python para facilitar filtro em produção.
- Nunca logar dados sensíveis: tokens JWT, senhas, CPF, e-mail completo, `context_data` bruto.

---

> Para decisões arquiteturais que justificam esses padrões, ver `ARCHITECTURE.md`.
> Para padrões específicos de agentes IA e prompts, ver `docs/specs/standards/AI_ARCHITECTURE.md` (a criar).
