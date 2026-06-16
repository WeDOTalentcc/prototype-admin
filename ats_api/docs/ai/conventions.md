# Convenções de Código - ATS Mercado

## 🎯 Filosofia

- **Legibilidade > Brevidade**: Código claro vale mais que código curto
- **DRY**: Don't Repeat Yourself - extrair duplicações
- **Early Return**: Evitar if/else aninhado
- **Clean Code**: SOLID, lambdas > switch, testes rápidos
- **Logging abundante**: Logs detalhados facilitam debugging
- **Fail-fast**: Detectar erros cedo
- **Cache inteligente**: Cache agressivo com invalidação correta
- **Performance consciente**: N+1 queries são inadmissíveis
- **Testes rápidos**: Objetos em memória > banco de dados

## 📁 Estrutura de Arquivos

```
app/
├── services/          # Lógica de negócio
│   ├── candidates/
│   │   └── search/    # Busca híbrida
│   └── sourcings/     # Sourcing de candidatos
├── jobs/              # Background jobs (Sidekiq)
│   ├── candidates/
│   └── pearch/
├── models/            # ActiveRecord models
├── serializers/       # JSON serialization
└── controllers/
    └── v1/            # API v1
```

## 🔤 Nomenclatura

### Services

```ruby
# Padrão: VerbNounService
SearchCandidatesService      # ✅
ProcessProfileService        # ✅
EnqueueJobService           # ✅

CandidatesSearcher          # ❌
ProfileProcessor            # ❌
```

### Jobs

```ruby
# Padrão: Module::VerbNounJob
Candidates::LocalSearchJob   # ✅
Pearch::TalentSearchJob     # ✅

SearchJob                   # ❌ (muito genérico)
LocalJob                    # ❌ (não diz o que faz)
```

### Methods

```ruby
# Ações: verbos
def search_candidates        # ✅
def process_results          # ✅
def calculate_score          # ✅

def candidates              # ❌ (parece getter)
def results                 # ❌ (parece getter)
```

### Predicados (boolean)

```ruby
def simple?                 # ✅
def has_results?            # ✅
def should_retry?           # ✅

def is_simple              # ❌ (redundante)
def check_results          # ❌ (não é clara)
```

## 🏗️ Padrões de Estrutura

### Service Object

```ruby
module Candidates
  module Search
    class HybridSearchService
      # Struct para retorno tipado
      Result = Struct.new(:candidates, :metadata, :explanation, keyword_init: true)

      # Initialize com keyword args
      def initialize(account_id:, tenant:)
        @account_id = account_id
        @tenant = tenant
        setup_dependencies
      end

      # Método público principal
      def search(query, **options)
        with_tenant do
          execute_search(query, options)
        end
      end

      private

      # Métodos privados organizados logicamente
      def execute_search(query, options)
        # implementação
      end

      def setup_dependencies
        @es_strategy = ElasticsearchStrategy.new(account_id: @account_id)
        @emb_strategy = EmbeddingStrategy.new(account_id: @account_id)
      end

      def with_tenant(&block)
        Apartment::Tenant.switch(@tenant, &block)
      end
    end
  end
end
```

### Job (Sidekiq)

```ruby
module Candidates
  class LocalSearchJob
    include Sidekiq::Job

    # Configuração do job
    sidekiq_options queue: :default, retry: 2

    # Perform com argumentos claros
    def perform(account_id, user_id, sourcing_id, query, filters_json)
      setup_context(account_id, user_id)

      with_tenant do
        execute_search(sourcing_id, query, filters_json)
      end
    rescue => e
      handle_error(account_id, sourcing_id, e)
    end

    private

    def setup_context(account_id, user_id)
      @account = Account.find(account_id)
      @user = User.find(user_id)
    end

    def with_tenant(&block)
      Apartment::Tenant.switch(@account.tenant, &block)
    end

    def execute_search(sourcing_id, query, filters_json)
      # implementação
    end

    def handle_error(account_id, sourcing_id, error)
      Rails.logger.error "[#{self.class.name}] Error: #{error.message}"
      Rails.logger.error error.backtrace.first(5).join("\n")

      # Atualiza sourcing como error
      sourcing = Sourcing.find_by(id: sourcing_id)
      sourcing&.update!(status: 'error', error_message: error.message)
    end
  end
end
```

## 📝 Logging

### Padrão de Logs

```ruby
# Logs estruturados com emojis e separadores
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Rails.logger.info "🔄 [HybridSearchService] EXECUTING SEARCH"
Rails.logger.info "   Query: #{query.truncate(100)}"
Rails.logger.info "   Account ID: #{account_id}"
Rails.logger.info "   Filters: #{filters.inspect}"
Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

### Emojis Padrão

```
🔄 - Processamento em andamento
✅ - Sucesso
❌ - Erro
⏳ - Aguardando
💡 - Informação importante
🔍 - Busca/pesquisa
🧠 - LLM/IA
🚀 - Início de processo
🎯 - Meta alcançada
⚡ - Performance/otimização
🔐 - Segurança/autenticação
📊 - Métricas/analytics
🔧 - Configuração
```

### Níveis de Log

```ruby
# DEBUG: Detalhes internos (só em development)
Rails.logger.debug "[ClassName] Internal state: #{state.inspect}"

# INFO: Fluxo principal
Rails.logger.info "[ClassName] Starting process"

# WARN: Situações anormais mas recuperáveis
Rails.logger.warn "[ClassName] Fallback strategy triggered"

# ERROR: Erros que precisam atenção
Rails.logger.error "[ClassName] Failed: #{error.message}"
```

## 🧹 Clean Code Patterns

### Early Return (SEMPRE preferir)

```ruby
# ❌ RUIM - If/else aninhado
def search_candidates(query, filters)
  if query.present?
    if query.length >= 3
      candidates = Candidate.where(account_id: account_id)
      if filters.present?
        candidates = candidates.where(filters)
      end
      if candidates.any?
        return candidates.limit(50)
      else
        return []
      end
    else
      return []
    end
  else
    return []
  end
end

# ✅ BOM - Early return
def search_candidates(query, filters)
  return [] if query.blank?
  return [] if query.length < 3

  candidates = Candidate.where(account_id: account_id)
  candidates = candidates.where(filters) if filters.present?

  return [] if candidates.none?

  candidates.limit(50)
end
```

### Lambda/Hash ao invés de Switch/Case

```ruby
# ❌ RUIM - Switch case
def route_search(query_type, query)
  case query_type
  when :simple
    execute_simple_search(query)
  when :complex
    execute_complex_search(query)
  when :resume
    execute_resume_search(query)
  else
    raise ArgumentError, "Unknown type: #{query_type}"
  end
end

# ✅ BOM - Hash de lambdas
SEARCH_ROUTES = {
  simple: ->(query) { execute_simple_search(query) },
  complex: ->(query) { execute_complex_search(query) },
  resume: ->(query) { execute_resume_search(query) }
}.freeze

def route_search(query_type, query)
  route = SEARCH_ROUTES[query_type]
  raise ArgumentError, "Unknown type: #{query_type}" unless route

  route.call(query)
end

# ✅ MELHOR AINDA - Strategy pattern para casos complexos
class SearchRouter
  STRATEGIES = {
    simple: SimpleSearchStrategy,
    complex: ComplexSearchStrategy,
    resume: ResumeSearchStrategy
  }.freeze

  def route(query_type, query)
    strategy_class = STRATEGIES[query_type]
    raise ArgumentError, "Unknown type: #{query_type}" unless strategy_class

    strategy_class.new.execute(query)
  end
end
```

### DRY - Extrair Duplicações

```ruby
# ❌ RUIM - Código duplicado
class CandidateService
  def format_for_export(candidate)
    {
      name: "#{candidate.first_name} #{candidate.last_name}".strip.titleize,
      email: candidate.email&.downcase,
      phone: candidate.phone&.gsub(/\D/, '')
    }
  end
end

class UserService
  def format_for_export(user)
    {
      name: "#{user.first_name} #{user.last_name}".strip.titleize,
      email: user.email&.downcase,
      phone: user.phone&.gsub(/\D/, '')
    }
  end
end

# ✅ BOM - Extrair para módulo
module Exportable
  def full_name
    "#{first_name} #{last_name}".strip.titleize
  end

  def normalized_email
    email&.downcase
  end

  def normalized_phone
    phone&.gsub(/\D/, '')
  end

  def export_data
    {
      name: full_name,
      email: normalized_email,
      phone: normalized_phone
    }
  end
end

class Candidate
  include Exportable
end

class User
  include Exportable
end
```

## 🎨 Formatação

### Linhas

- Máximo 120 caracteres
- Quebrar argumentos em linhas quando > 3 args

```ruby
# BOM
service.search(
  query,
  user_filters: filters,
  limit: 50,
  debug: true
)

# RUIM
service.search(query, user_filters: filters, limit: 50, debug: true, account_id: 123)
```

### Indentação

- 2 espaços (nunca tabs)
- Alinhar elementos de array/hash

```ruby
# BOM
weights = {
  elasticsearch: 0.70,
  embedding: 0.30
}

# ACEITÁVEL
weights = { elasticsearch: 0.70, embedding: 0.30 }
```

### Strings

- Double quotes `"` por padrão
- Single quotes `'` só quando tem interpolação dentro

```ruby
# BOM
message = "Hello #{name}"
literal = "No interpolation here"

# RUIM
message = 'Hello #{name}'  # não interpola!
literal = 'No interpolation here'  # inconsistente
```

## 🔒 Multi-tenancy

### SEMPRE usar Apartment::Tenant.switch

```ruby
# Em Services
def with_tenant(&block)
  Apartment::Tenant.switch(@tenant, &block)
end

# Em Jobs
Apartment::Tenant.switch(@account.tenant) do
  # código que acessa dados do tenant
end

# Em Controllers (já switcha automaticamente via before_action)
class ApplicationController
  before_action :switch_tenant

  def switch_tenant
    Apartment::Tenant.switch(current_user.account.tenant)
  end
end
```

### Verificar tenant em queries importantes

```ruby
# SEMPRE incluir account_id em queries críticas
candidates = Candidate.where(
  account_id: @account.id,  # ✅ Garante isolamento
  is_deleted: false
)
```

## ⚡ Performance

### N+1 Queries

```ruby
# RUIM ❌
users.each do |user|
  puts user.account.name  # N+1!
end

# BOM ✅
users.includes(:account).each do |user|
  puts user.account.name
end
```

### Pluck vs Map

```ruby
# RUIM ❌
ids = Candidate.all.map(&:id)  # Carrega todos os models!

# BOM ✅
ids = Candidate.pluck(:id)     # SQL direto
```

### Find Each para grandes volumes

```ruby
# RUIM ❌
Candidate.where(account_id: 123).each do |candidate|
  process(candidate)  # Carrega TUDO na memória
end

# BOM ✅
Candidate.where(account_id: 123).find_each(batch_size: 1000) do |candidate|
  process(candidate)  # Processa em lotes
end
```

## 🧪 Testes (RSpec)

### Estrutura

```ruby
RSpec.describe Candidates::Search::HybridSearchService do
  # Setup
  let(:account) { create(:account) }
  let(:tenant) { account.tenant }
  let(:service) { described_class.new(account_id: account.id, tenant: tenant) }

  # Testes organizados por método
  describe '#search' do
    context 'when query is simple' do
      it 'uses simple search path' do
        # Arrange
        query = "ruby developer"

        # Act
        result = service.search(query)

        # Assert
        expect(result.metadata[:search_type]).to eq(:simple)
      end
    end

    context 'when query is complex' do
      it 'uses complex search path' do
        query = "python developer with 5 years experience"
        result = service.search(query)
        expect(result.metadata[:search_type]).to eq(:complex)
      end
    end

    context 'when no results found' do
      it 'returns empty array' do
        result = service.search("nonexistent query")
        expect(result.candidates).to be_empty
      end
    end
  end
end
```

### Mocks e Stubs

```ruby
# Usar allow/expect para mocks
allow(GeminiClient).to receive(:new).and_return(mock_client)
expect(mock_client).to receive(:chat).and_return(response)

# Preferir doubles a mocks reais quando possível
mock_strategy = instance_double(ElasticsearchStrategy)
allow(mock_strategy).to receive(:search).and_return([])
```

## 🔐 Segurança

### Secrets

```ruby
# SEMPRE usar ENV vars
api_key = ENV.fetch("GEMINI_API_KEY")  # ✅

# NUNCA hardcode
api_key = "AIzaSy..."  # ❌ NUNCA!
```

### SQL Injection

```ruby
# RUIM ❌
Candidate.where("name = '#{params[:name]}'")

# BOM ✅
Candidate.where(name: params[:name])
Candidate.where("name = ?", params[:name])
```

### Mass Assignment

```ruby
# RUIM ❌
User.create(params[:user])

# BOM ✅
User.create(user_params)

private

def user_params
  params.require(:user).permit(:name, :email)
end
```

## 📡 APIs e Serialização

### SEMPRE usar serializers

```ruby
# BOM ✅
render json: CandidateSerializer.new(candidates).serializable_hash

# RUIM ❌
render json: candidates.as_json
```

### Padrão de resposta

```ruby
# Success
{
  success: true,
  data: { ... },
  metadata: { count: 10, page: 1 }
}

# Error
{
  success: false,
  error: {
    code: "VALIDATION_ERROR",
    message: "Invalid parameters",
    details: { field: "error message" }
  }
}
```

## 🔄 Background Jobs

### Enqueue

```ruby
# BOM ✅
MyJob.perform_async(arg1, arg2)

# EVITAR (só se precisar delay)
MyJob.perform_in(5.minutes, arg1, arg2)
MyJob.perform_at(1.hour.from_now, arg1, arg2)
```

### Retry

```ruby
# Configure retry strategy
sidekiq_options queue: :default, retry: 3

# Ou customizado
sidekiq_options retry: 5, dead: false
```

## 📊 Métricas e Observabilidade

### Telemetry

```ruby
# Sempre medir operações importantes
telemetry = SearchTelemetry.new

result = telemetry.time(:elasticsearch) do
  @es_strategy.search(query)
end

telemetry.log_summary(result_count: result.size)
```

### Custom Metrics (se usando prometheus/statsd)

```ruby
# Contador
StatsD.increment('search.hybrid.executed')

# Timing
StatsD.measure('search.hybrid.duration') do
  service.search(query)
end

# Gauge
StatsD.gauge('search.results.count', results.size)
```

## 🎓 Recursos

- **Guia de Style**: https://github.com/rubocop/ruby-style-guide
- **Rails Best Practices**: https://rails-bestpractices.com
- **Documentação interna**: `/docs/`
