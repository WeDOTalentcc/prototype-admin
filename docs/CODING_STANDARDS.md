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

### 4.1 Módulo completo

```python
"""
Sourcing API - Endpoints for candidate sourcing, matching, and suggestions.

Provides:
- POST /api/v1/sourcing/search - Search candidates with boolean queries
- POST /api/v1/sourcing/match-candidates - Match candidates to job requirements
- GET /api/v1/sourcing/suggestions/{job_id} - Get suggested candidates for a job
"""
# 1. Stdlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Internal
from app.core.database import get_db
from app.domains.sourcing.services.query_builders import BooleanQueryBuilder

# 4. Logger — sempre __name__
logger = logging.getLogger(__name__)

# 5. Router com prefix e tags
router = APIRouter(prefix="/sourcing", tags=["sourcing"])


# 6. Schemas Pydantic — Request e Response separados e nomeados
class SourcingSearchRequest(BaseModel):
    """Request for candidate sourcing search."""
    query: Optional[str] = Field(None, description="Free text search query")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    seniority: Optional[str] = Field(
        None,
        description="Seniority level: junior, pleno, senior, manager, director"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class SourcingSearchResponse(BaseModel):
    """Response from candidate sourcing search."""
    success: bool
    candidates_found: int
    candidates: List[Dict[str, Any]]
    search_time_ms: int = 0


# 7. Endpoints — verbo + substantivo descritivo
@router.post("/search", response_model=SourcingSearchResponse)
async def search_candidates(
    request: SourcingSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SourcingSearchResponse:
    """Search candidates using boolean queries and filters."""
    try:
        # lógica de negócio em serviço, não aqui
        results = await BooleanQueryBuilder(db).search(request)
        return SourcingSearchResponse(success=True, **results)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error")
```

**Regras de endpoint FastAPI:**
- Docstring de módulo obrigatória com lista de endpoints disponíveis.
- Imports em 3 blocos: stdlib → third-party → internal. Linha em branco entre blocos.
- `logger = logging.getLogger(__name__)` em todo módulo que precisa de log.
- Schemas Pydantic com nomes explícitos: `XxxRequest` e `XxxResponse`.
- `Field(..., description="...")` em todos os campos de schema — gera documentação automática.
- `response_model=` declarado no decorator do endpoint.
- Erros de validação: `HTTPException(422)`. Erros de sistema: `HTTPException(500)` + `logger.error`.
- Lógica de negócio em `services/` ou `domains/`, nunca no endpoint.

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
"""
Gemini API configuration.
Single Responsibility: Manage Gemini API settings only.
"""
from dataclasses import dataclass


@dataclass(frozen=True)           # frozen=True — imutável após criação
class GeminiConfig:
    """Configuration for Google Gemini API."""
    api_key: str
    model: str = "gemini-2.5-flash"
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
    test_easy_cases.py        → queries diretas, intenção clara
    test_medium_cases.py      → queries com ambiguidade, filtros compostos
    test_hard_cases.py        → multi-turno, contexto necessário
    test_very_hard_cases.py   → edge cases, falhas de API, timeouts
  evals/
    run_evals.py              → avaliação LLM-as-judge com dataset golden
  mocks/
    mock_api_client.py        → mock do cliente Rails API
```

```python
# tests/integration/test_easy_cases.py
import pytest
from tests.mocks.mock_api_client import MockAppliesAPIClient


def test_search_applies_by_name():
    """Busca por nome retorna candidatos filtrados."""
    mock_api = MockAppliesAPIClient(
        applies=[{"id": 1, "name": "Maria Silva", "total_score": 85}]
    )
    domain = AppliesDomain(api_client=mock_api)
    
    response = domain.execute_action(
        action_id="search_by_name",
        params={"job_id": "123", "term": "Maria"},
        context=mock_context(),
    )
    
    assert response.success is True
    assert "Maria Silva" in response.message
    assert len(response.data) == 1


def test_search_applies_without_term_asks_clarification():
    """Busca sem termo pede clarificação ao invés de falhar."""
    domain = AppliesDomain()
    response = domain.execute_action(
        action_id="search_by_name",
        params={"job_id": "123"},
        context=mock_context(),
    )
    assert response.success is False
    assert response.needs_clarification is True
```

**Regras de teste:**
- Nome do teste descreve comportamento esperado, não implementação.
- Um assert por teste sempre que possível.
- Mocks para APIs externas — nunca chamar serviços reais nos testes unitários.
- `test_easy_cases` sempre passando antes de trabalhar em `test_hard_cases`.
- Testes de integração com serviços reais ficam em `tests/integration/` e rodam separado do CI unitário.

---

## 8. O que está Explicitamente Proibido

Baseado no que **não existe** no código melhor escrito do projeto:

| Proibição | Motivo | Alternativa |
|-----------|--------|-------------|
| `print()` em qualquer arquivo Python | Não rastreável em produção | `logger.info/warning/error()` |
| `os.getenv()` fora do módulo de settings | Config espalhada é indetectável | `get_settings().atributo` |
| Instanciar LLM diretamente (`ChatGoogleGenerativeAI(...)`) | Sem rastreamento LangSmith | `create_tracked_llm(...)` |
| Retornar `dict` raw de domain actions | Quebre contratos de tipo | `DomainResponse(...)` |
| `shadow-xl` ou `shadow-2xl` em componentes | Viola Design System LIA v4.x | `shadow-sm` |
| Hex de cor hardcoded em CSS | Inconsistência com tema | `rgb(var(--v-theme-primary))` |
| `any` no TypeScript sem justificativa em comentário | Perde type safety | Tipo explícito ou `unknown` |
| SQL raw em controllers Rails | XSS/injection, sem log | ActiveRecord `.where(...)` |
| Lógica de negócio em endpoint FastAPI | Não testável isoladamente | Mover para `services/` ou `domains/` |
| `# frozen_string_literal: true` ausente em `.rb` | Performance e mutabilidade | Adicionar na primeira linha |
| Componente Vue sem `lang="ts"` | TypeScript não aplicado | `<script setup lang="ts">` |
| Props Vue sem tipo TypeScript | Sem autocomplete, sem validação | `defineProps<{ label: string }>()` |
| `before_action` sem `only:` explícito | Aplica auth em rotas não desejadas | `before_action :authorize_request, only: %i[show]` |
| Comentários de código sem propósito real | Ruído no código | Código autoexplicativo. Comentário só para "por quê", nunca "o quê" |
| Acesso direto ao banco do ATS pelos agentes | Viola isolamento de tenant | Chamar `ats_api` via REST |

---

## 9. Padrões de Logging

```python
# PADRÃO Python — um logger por módulo, nível correto
import logging
logger = logging.getLogger(__name__)

logger.info(f"Saved question set version for job {job_id}")      # evento normal
logger.warning(f"Failed to save question set version: {err}")    # falha recuperável
logger.error(f"AI generation failed: {e}", exc_info=True)        # falha grave (+ stack trace)
logger.debug(f"Cache hit for session {session_id}")              # diagnóstico
```

```ruby
# PADRÃO Rails
Rails.logger.info "JWT decoded for user #{decoded[:user_id]}"
Rails.logger.error "JWT Decode Error: #{e.message}"
```

**Regras:**
- `exc_info=True` obrigatório no `logger.error()` para incluir stack trace.
- Mensagens em inglês nos logs (facilita busca em Sentry/Datadog por times internacionais).
- Nunca logar dados sensíveis (tokens JWT, senhas, CPF, e-mail completo).

---

> Para decisões arquiteturais que justificam esses padrões, ver `ARCHITECTURE.md`.
> Para padrões específicos de agentes IA e prompts, ver `docs/specs/standards/AI_ARCHITECTURE.md` (a criar).
