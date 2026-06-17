# Padrões de Design - ATS Mercado

## 🎨 Design Patterns Utilizados

### 1. Service Object Pattern

**Quando usar**: Lógica de negócio complexa que não cabe em models/controllers

```ruby
# ✅ BOM: Service com responsabilidade única
class Candidates::Search::HybridSearchService
  def initialize(account_id:, tenant:)
    @account_id = account_id
    @tenant = tenant
  end

  def search(query, **options)
    # lógica de busca
  end
end

# ❌ RUIM: Tudo no controller
class SearchController
  def search
    # 200 linhas de lógica aqui
  end
end
```

**Estrutura padrão**:

```ruby
module Domain
  class ActionService
    # 1. Initialize com dependencies
    def initialize(dependency:)
      @dependency = dependency
    end

    # 2. Public método principal
    def call(*args)
      prepare
      execute
      finalize
    end

    private

    # 3. Private methods organizados
    def prepare; end
    def execute; end
    def finalize; end
  end
end
```

---

### 2. Strategy Pattern

**Quando usar**: Múltiplos algoritmos intercambiáveis para mesma tarefa

```ruby
# Interface comum
class SearchStrategy
  def search(query, **options)
    raise NotImplementedError
  end
end

# Estratégias concretas
class ElasticsearchStrategy < SearchStrategy
  def search(query, **options)
    # busca full-text
  end
end

class EmbeddingStrategy < SearchStrategy
  def search(query, **options)
    # busca semântica
  end
end

# Uso
strategies = [
  ElasticsearchStrategy.new,
  EmbeddingStrategy.new
]

results = strategies.map { |s| s.search(query) }
```

**Benefícios**:

- Fácil adicionar novas estratégias
- Testável isoladamente
- Segue Open/Closed Principle

---

### 3. Template Method Pattern

**Quando usar**: Algoritmo com passos fixos mas implementações variáveis

```ruby
class SearchService
  def search(query)
    validate_query(query)
    results = execute_search(query)
    post_process(results)
  end

  private

  # Template methods (sobrescrever em subclasses)
  def validate_query(query)
    raise NotImplementedError
  end

  def execute_search(query)
    raise NotImplementedError
  end

  def post_process(results)
    results # implementação padrão
  end
end

class SimpleSearchService < SearchService
  private

  def validate_query(query)
    query.present?
  end

  def execute_search(query)
    Candidate.search(query)
  end
end
```

---

### 4. Facade Pattern

**Quando usar**: Simplificar interface complexa

```ruby
# ✅ BOM: Facade esconde complexidade
class HybridSearchService
  def search(query, **options)
    # Esconde complexidade de:
    # - QueryAnalyzer
    # - Multiple strategies
    # - Fusion
    # - Reranking
    # - Cache

    Result.new(candidates: candidates, metadata: metadata)
  end
end

# Cliente usa interface simples
result = HybridSearchService.new(...).search("ruby")

# ❌ RUIM: Cliente precisa conhecer tudo
query_analysis = QueryAnalyzer.new.analyze(query)
es_results = ElasticsearchStrategy.new.search(query)
emb_results = EmbeddingStrategy.new.search(query)
fused = WeightedRankFusion.combine(...)
reranked = Reranker.apply(...)
```

---

### 5. Builder Pattern

**Quando usar**: Construção complexa de objetos

```ruby
class SearchQueryBuilder
  def initialize
    @filters = {}
    @sort = []
    @limit = 50
  end

  def with_filter(field, value)
    @filters[field] = value
    self
  end

  def sort_by(field, direction = :asc)
    @sort << { field => direction }
    self
  end

  def limit(n)
    @limit = n
    self
  end

  def build
    SearchQuery.new(
      filters: @filters,
      sort: @sort,
      limit: @limit
    )
  end
end

# Uso fluente
query = SearchQueryBuilder.new
  .with_filter(:city, "São Paulo")
  .with_filter(:role, "developer")
  .sort_by(:created_at, :desc)
  .limit(100)
  .build
```

---

### 6. Repository Pattern

**Quando usar**: Abstração de acesso a dados

```ruby
class CandidateRepository
  def initialize(account_id:)
    @account_id = account_id
  end

  def find(id)
    base_scope.find(id)
  end

  def search(query, **filters)
    scope = base_scope
    scope = apply_filters(scope, filters)
    scope.search(query)
  end

  private

  def base_scope
    Candidate.where(account_id: @account_id, is_deleted: false)
  end

  def apply_filters(scope, filters)
    filters.each do |key, value|
      scope = scope.where(key => value)
    end
    scope
  end
end

# Uso
repo = CandidateRepository.new(account_id: 123)
candidates = repo.search("ruby", city: "SP")
```

**Benefícios**:

- Centraliza lógica de queries
- Fácil trocar data source
- Testável com mocks

---

### 7. Observer Pattern (Rails ActiveRecord Callbacks)

**Quando usar**: Ações automáticas após eventos

```ruby
class SourcedProfile < ApplicationRecord
  # Observer via callback
  after_commit :enqueue_ai_analysis, on: :create

  private

  def enqueue_ai_analysis
    SourcedProfiles::AiAnalysisJob.perform_async(id)
  end
end

# Ou via ActiveSupport::Notifications
ActiveSupport::Notifications.subscribe("search.completed") do |event|
  SearchAnalytics.track(event.payload)
end

# Publicar
ActiveSupport::Notifications.instrument("search.completed", {
  query: query,
  results_count: count
})
```

---

### 8. Chain of Responsibility

**Quando usar**: Sequência de handlers até um processar

```ruby
class FallbackSearchChain
  def initialize
    @strategies = [
      TextInSearchStrategy.new,
      WildcardSearchStrategy.new,
      OnlySearchStrategy.new,
      LlmFallbackStrategy.new
    ]
  end

  def execute(query, filters)
    @strategies.each do |strategy|
      result = strategy.try_search(query, filters)
      return result if result.any?
    end

    [] # Nenhuma estratégia funcionou
  end
end

class TextInSearchStrategy
  def try_search(query, filters)
    # tenta busca
    results
  end
end
```

---

### 9. Value Object Pattern

**Quando usar**: Objetos imutáveis que representam valores

```ruby
# ✅ BOM: Value Object imutável
class SearchResult
  attr_reader :candidates, :metadata, :explanation

  def initialize(candidates:, metadata:, explanation: nil)
    @candidates = candidates.freeze
    @metadata = metadata.freeze
    @explanation = explanation&.freeze
    freeze
  end

  def ==(other)
    candidates == other.candidates &&
    metadata == other.metadata
  end
end

# Uso
result = SearchResult.new(
  candidates: [c1, c2],
  metadata: { count: 2 }
)

result.candidates # OK
result.candidates << c3 # RuntimeError: can't modify frozen Array
```

---

### 10. Null Object Pattern

**Quando usar**: Evitar nil checks

```ruby
# ✅ BOM: Null Object
class NullQueryAnalysis
  def elasticsearch_query
    @original_query
  end

  def embedding_query
    @original_query
  end

  def entities
    {}
  end

  def confidence
    0.0
  end
end

class QueryAnalyzer
  def analyze(query)
    return NullQueryAnalysis.new(query) if query.blank?

    # análise real
  end
end

# Uso (sem nil check)
analysis = QueryAnalyzer.new.analyze(nil)
analysis.elasticsearch_query # funciona!

# ❌ RUIM: Nil checks em todo lugar
analysis = QueryAnalyzer.new.analyze(nil)
if analysis
  query = analysis.elasticsearch_query
else
  query = original_query
end
```

---

### 11. Adapter Pattern

**Quando usar**: Adaptar interface incompatível

```ruby
# Interface esperada
class SearchInterface
  def search(query)
    raise NotImplementedError
  end
end

# Adapter para Searchkick
class SearchkickAdapter < SearchInterface
  def initialize(model)
    @model = model
  end

  def search(query)
    results = @model.search(query)

    # Adapta resposta
    results.map { |r| { id: r.id, score: r._score } }
  end
end

# Uso uniforme
adapter = SearchkickAdapter.new(Candidate)
results = adapter.search("ruby")
```

---

## 🔧 Anti-Patterns a Evitar

### 1. God Object

```ruby
# ❌ RUIM: Classe faz tudo
class MegaSearchService
  def search; end
  def analyze_query; end
  def call_llm; end
  def cache_result; end
  def send_notification; end
  def log_metrics; end
  def validate_user; end
  # ... 50+ métodos
end

# ✅ BOM: Separar responsabilidades
class SearchService
  def search
    query_analysis = QueryAnalyzer.new.analyze(query)
    results = SearchExecutor.new.execute(query_analysis)
    CacheService.new.store(results)
    NotificationService.new.notify(results)
  end
end
```

### 2. Anemic Domain Model

```ruby
# ❌ RUIM: Model sem lógica
class Candidate < ApplicationRecord
  # só attributes, sem métodos
end

class CandidateService
  def full_name(candidate)
    "#{candidate.first_name} #{candidate.last_name}"
  end
end

# ✅ BOM: Lógica no model
class Candidate < ApplicationRecord
  def full_name
    "#{first_name} #{last_name}"
  end
end
```

### 3. Magic Numbers/Strings

```ruby
# ❌ RUIM
if score > 0.7
  # ...
end

# ✅ BOM
RELEVANCE_THRESHOLD = 0.7

if score > RELEVANCE_THRESHOLD
  # ...
end

# Ou em Configuration
class Configuration
  def embedding_relevance_threshold
    ENV.fetch("EMBEDDING_RELEVANCE_THRESHOLD", "0.70").to_f
  end
end
```

### 4. Feature Envy

```ruby
# ❌ RUIM: Método acessa muito outro objeto
class SearchService
  def format_result(candidate)
    "#{candidate.name} - #{candidate.email} - #{candidate.phone}"
  end
end

# ✅ BOM: Mover para o objeto
class Candidate
  def formatted_contact
    "#{name} - #{email} - #{phone}"
  end
end
```

---

## 📋 Checklist de Code Review

Ao revisar código, verificar:

- [ ] **Single Responsibility**: Cada classe tem UMA responsabilidade?
- [ ] **DRY**: Código está duplicado?
- [ ] **YAGNI**: Está implementando coisas não necessárias?
- [ ] **Naming**: Nomes descritivos e consistentes?
- [ ] **Error Handling**: Erros tratados adequadamente?
- [ ] **Logging**: Logs suficientes para debugging?
- [ ] **Tests**: Cobertura adequada de testes?
- [ ] **Performance**: N+1 queries? Cache apropriado?
- [ ] **Security**: SQL injection? Mass assignment?
- [ ] **Multi-tenancy**: Tenant isolation garantido?

---

## 🎓 Princípios SOLID

### S - Single Responsibility Principle

Uma classe deve ter apenas uma razão para mudar.

```ruby
# ✅ BOM
class ElasticsearchStrategy
  def search(query)
    # Só faz busca no ES
  end
end

class EmbeddingStrategy
  def search(embedding)
    # Só faz busca vetorial
  end
end
```

### O - Open/Closed Principle

Aberto para extensão, fechado para modificação.

```ruby
# ✅ BOM: Adicionar nova estratégia sem modificar existentes
class NewStrategy < SearchStrategy
  def search(query)
    # nova implementação
  end
end
```

### L - Liskov Substitution Principle

Subclasses devem ser substituíveis por suas superclasses.

```ruby
# ✅ BOM: Qualquer Strategy pode ser usada
def execute_search(strategy)
  strategy.search(query)
end

execute_search(ElasticsearchStrategy.new)
execute_search(EmbeddingStrategy.new)
```

### I - Interface Segregation Principle

Não force classes a implementar métodos que não usam.

```ruby
# ❌ RUIM
class SearchStrategy
  def search; end
  def cache; end
  def log; end
end

# ✅ BOM: Interfaces separadas
class Searchable
  def search; end
end

class Cacheable
  def cache; end
end
```

### D - Dependency Inversion Principle

Dependa de abstrações, não de implementações.

```ruby
# ✅ BOM: Injeta dependency
class SearchService
  def initialize(strategy:)
    @strategy = strategy
  end

  def search(query)
    @strategy.search(query)
  end
end

# Uso com qualquer estratégia
service = SearchService.new(strategy: ElasticsearchStrategy.new)
```
