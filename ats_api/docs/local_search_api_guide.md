# Local Search - Guia de Implementação e API

> **Guia de Desenvolvimento**  
> **Para:** Desenvolvedores implementando features que usam Local Search  
> **Última atualização:** 2026-02-01

## 📚 Índice

1. [Quick Start](#quick-start)
2. [API de Busca](#api-de-busca)
3. [Configurações](#configurações)
4. [Metadados de Resposta](#metadados-de-resposta)
5. [Casos de Uso Comuns](#casos-de-uso-comuns)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Instalação e Setup

Todas as dependências já estão instaladas. O sistema está pronto para uso.

### Primeiro Uso

```ruby
# 1. Inicializar o serviço
service = Candidates::Search::HybridSearchService.new(
  account_id: current_account.id,
  tenant: current_account.tenant
)

# 2. Fazer uma busca simples
result = service.search(
  "ruby developer senior",
  user_filters: {},
  limit: 10
)

# 3. Acessar resultados
result.candidates.each do |candidate|
  puts "#{candidate.name} - Score: #{result.search_meta_by_id[candidate.id][:score]}"
end

# 4. Ver metadados
puts "Search type: #{result.metadata[:search_type]}"
puts "Total results: #{result.metadata[:count]}"
```

---

## API de Busca

### HybridSearchService#search

**Assinatura:**

```ruby
def search(query_text, user_filters: {}, limit: 50, debug: false)
  # Returns: Result object
end
```

**Parâmetros:**

| Parâmetro | Tipo | Obrigatório | Default | Descrição |
|-----------|------|-------------|---------|-----------|
| `query_text` | String | ✅ | - | Texto da busca (query, CV, ou JD) |
| `user_filters` | Hash | ❌ | `{}` | Filtros adicionais (cidade, estado, etc) |
| `limit` | Integer | ❌ | `50` | Número máximo de resultados |
| `debug` | Boolean | ❌ | `false` | Retorna explicação detalhada |

**Retorno:**

```ruby
Result {
  candidates: Array<Candidate>,
  metadata: Hash,
  search_meta_by_id: Hash<Integer, Hash>,
  explanation: Hash (apenas se debug: true)
}
```

---

### User Filters

Filtros adicionais que podem ser aplicados:

```ruby
user_filters = {
  city: "São Paulo",
  state: "SP",
  min_experience: 3,
  max_experience: 10,
  position_level: ["pleno", "senior"],
  has_curriculum: true,
  has_contact_info: true,
  updated_since: 30.days.ago
}

result = service.search(
  "ruby developer",
  user_filters: user_filters,
  limit: 20
)
```

**Filtros disponíveis:**

| Filtro | Tipo | Exemplo | Descrição |
|--------|------|---------|-----------|
| `city` | String | `"São Paulo"` | Cidade do candidato |
| `state` | String | `"SP"` | Estado (sigla) |
| `min_experience` | Integer | `3` | Anos mínimos de experiência |
| `max_experience` | Integer | `10` | Anos máximos de experiência |
| `position_level` | Array/String | `["pleno", "senior"]` | Nível da posição |
| `has_curriculum` | Boolean | `true` | Tem currículo anexado |
| `has_contact_info` | Boolean | `true` | Tem email ou telefone |
| `updated_since` | DateTime | `30.days.ago` | Atualizado desde |

---

## Configurações

### Configuration Class

Todas as configurações estão em `Candidates::Search::Configuration`:

```ruby
module Candidates
  module Search
    class Configuration
      # Pool sizes
      def self.initial_pool_size
        ENV.fetch('SEARCH_INITIAL_POOL_SIZE', 100).to_i
      end
      
      def self.min_pool_size
        ENV.fetch('SEARCH_MIN_POOL_SIZE', 40).to_i
      end
      
      def self.max_pool_size
        ENV.fetch('SEARCH_MAX_POOL_SIZE', 400).to_i
      end
      
      # Fusion weights (default para simple/complex)
      def self.default_fusion_weights
        {
          simple: { elasticsearch: 0.70, embedding: 0.30 },
          complex: { elasticsearch: 0.50, embedding: 0.50 }
        }
      end
      
      # Embedding relevance filtering
      def self.embedding_keyword_gate?
        ENV.fetch('EMBEDDING_KEYWORD_GATE', 'true') == 'true'
      end
      
      def self.embedding_relevance_threshold
        ENV.fetch('EMBEDDING_RELEVANCE_THRESHOLD', '0.65').to_f
      end
      
      # Reranking signals
      def self.rerank_signals
        {
          profile_completeness: { threshold: 0.80, weight: 0.10 },
          has_contact_info: { weight: 0.05 },
          recent_activity: { days: 30, weight: 0.08 },
          has_experience: { weight: 0.05 },
          has_skills: { weight: 0.03 },
          has_curriculum: { weight: 0.12 }
        }
      end
      
      def self.penalty_signals
        {
          low_completeness: { threshold: 0.40, weight: -0.15 },
          medium_completeness: { threshold: 0.70, weight: -0.08 },
          missing_curriculum: { weight: -0.10 }
        }
      end
      
      # Multi-query settings
      def self.multi_query_boost_per_hit
        ENV.fetch('MULTI_QUERY_BOOST_PER_HIT', '0.15').to_f
      end
      
      # Confidence thresholds
      def self.high_confidence_threshold
        ENV.fetch('HIGH_CONFIDENCE_THRESHOLD', '0.75').to_f
      end
      
      def self.medium_confidence_threshold
        ENV.fetch('MEDIUM_CONFIDENCE_THRESHOLD', '0.50').to_f
      end
    end
  end
end
```

### Variáveis de Ambiente

Configurações via `.env`:

```bash
# Pool sizes
SEARCH_INITIAL_POOL_SIZE=100
SEARCH_MIN_POOL_SIZE=40
SEARCH_MAX_POOL_SIZE=400

# Embedding filtering
EMBEDDING_KEYWORD_GATE=true
EMBEDDING_RELEVANCE_THRESHOLD=0.65

# Multi-query
MULTI_QUERY_BOOST_PER_HIT=0.15

# Confidence thresholds
HIGH_CONFIDENCE_THRESHOLD=0.75
MEDIUM_CONFIDENCE_THRESHOLD=0.50

# LLM
GEMINI_CHAT_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your-api-key

# Embedding
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

---

## Metadados de Resposta

### Result.metadata

Estrutura completa dos metadados retornados:

#### Simple Search

```ruby
{
  request_id: "550e8400-e29b-41d4-a716-446655440000",
  count: 25,
  search_type: :simple
}
```

#### Resume Search

```ruby
{
  request_id: "550e8400-e29b-41d4-a716-446655440000",
  count: 25,
  search_type: :resume,
  
  # Extraction quality
  extraction_confidence: 0.85,           # 0.0-1.0
  extraction_method: :llm,               # :llm | :structured | :keyword_fallback
  missing_fields: [],                    # Array de campos não extraídos
  
  # Multi-query
  queries_generated: 5,                  # Número de queries geradas
  strategy_used: :profile_based,         # Estratégia usada
  
  # Fusion
  fusion_weights: {
    elasticsearch: 0.35,
    embedding: 0.65
  }
}
```

#### Job Description Search

```ruby
{
  request_id: "550e8400-e29b-41d4-a716-446655440000",
  count: 25,
  search_type: :job_description,
  
  # JD processing
  required_skills: ["Ruby on Rails", "PostgreSQL", "Redis"],
  nice_to_have_skills: ["React", "Docker", "AWS"],
  
  # Fusion (ES prioritizado para JD)
  fusion_weights: {
    elasticsearch: 0.60,
    embedding: 0.40
  }
}
```

### Result.search_meta_by_id

Metadados específicos de cada candidato:

```ruby
{
  123 => {
    source: "hybrid",                    # "elasticsearch" | "embedding" | "hybrid"
    score: 0.8542,                       # Score normalizado
    
    # Contribuições das fontes
    contributions: {
      elasticsearch: 0.4,                # 40% do score veio do ES
      embedding: 0.6                     # 60% do score veio do embedding
    },
    
    # Boosts aplicados
    boost: 0.25,                         # Boost total aplicado
    boost_breakdown: {
      profile_completeness: 0.10,
      has_contact_info: 0.05,
      has_curriculum: 0.12,
      required_skill_match: 0.08,        # Apenas em JD search
      multi_query_match: 0.10            # Apenas em Resume search
    },
    
    # Multi-query (apenas Resume search)
    multi_query_hits: 3,                 # Apareceu em 3 queries
    multi_query_boost: 1.30,             # 1.0 + (0.15 * 2)
    
    # Score final
    final_score: 1.0678,                 # rrf_score * (1 + boost)
    
    # Qualidade do perfil
    completeness: 0.85                   # Completude do perfil
  }
}
```

---

## Casos de Uso Comuns

### Caso 1: Busca Simples por Keywords

```ruby
service = Candidates::Search::HybridSearchService.new(
  account_id: current_account.id,
  tenant: current_account.tenant
)

result = service.search(
  "ruby senior",
  user_filters: { city: "São Paulo" },
  limit: 10
)

# Fast path - ~200ms
# Não usa LLM
# ES 70% / Embedding 30%
```

### Caso 2: Upload de Currículo (Match Similar Candidates)

```ruby
resume_text = params[:resume_file].read

result = service.search(
  resume_text,
  limit: 20
)

# Detectado automaticamente como :resume
# Usa ProfileExtractor
# Multi-query retrieval
# Fusion weights ajustados por confidence
# ~2.5s

# Verificar qualidade da extração
if result.metadata[:extraction_confidence] < 0.5
  flash[:warning] = "Algumas informações podem não ter sido extraídas corretamente"
end

# Mostrar queries geradas (debug)
puts "Queries usadas:"
result.metadata[:queries_generated].times do |i|
  puts "  #{i+1}. <query text não retornado, mas usado internamente>"
end
```

### Caso 3: Busca por Descrição de Vaga

```ruby
jd_text = """
  Vaga: Desenvolvedor Ruby Senior

  Requisitos obrigatórios:
  - Ruby on Rails
  - PostgreSQL
  - 5+ anos de experiência
  - Experiência em fintech

  Desejável:
  - React
  - Docker
  - AWS
"""

result = service.search(
  jd_text,
  limit: 15
)

# Detectado automaticamente como :job_description
# Usa JobDescriptionProcessor
# Custom boost para required skills
# ES prioritizado (60/40)
# ~2.0s

# Ver skills detectadas
puts "Required: #{result.metadata[:required_skills].join(', ')}"
puts "Nice-to-have: #{result.metadata[:nice_to_have_skills].join(', ')}"

# Candidatos com mais required skills ranqueiam melhor
result.candidates.each do |candidate|
  meta = result.search_meta_by_id[candidate.id]
  
  if meta[:boost_breakdown][:required_skill_match]
    puts "#{candidate.name} - Matched required skills (boost: #{meta[:boost_breakdown][:required_skill_match]})"
  end
end
```

### Caso 4: Busca Complexa com Filtros

```ruby
result = service.search(
  "desenvolvedor ruby com 5 anos de experiência em rails e experiência em fintech",
  user_filters: {
    city: "São Paulo",
    state: "SP",
    position_level: ["pleno", "senior"],
    has_curriculum: true,
    updated_since: 60.days.ago
  },
  limit: 30
)

# Detectado como :complex
# Usa QueryAnalyzer + HyDE
# ~1.5s

# Verificar se filtros foram muito restritivos
if result.metadata[:count] < 5
  # Tentar busca sem filtros (fallback automático no service)
  result_fallback = service.search(
    "desenvolvedor ruby com 5 anos de experiência",
    limit: 30
  )
  
  if result_fallback.metadata[:fallback]
    flash[:info] = result_fallback.metadata[:message]
  end
end
```

### Caso 5: Debug Mode

```ruby
result = service.search(
  "senior rails developer",
  limit: 10,
  debug: true
)

# Retorna explanation com detalhes:
explanation = result.explanation

puts "ES Query: #{explanation[:es_query_used]}"
puts "Embedding Query: #{explanation[:embedding_query_used]}"
puts "HyDE used: #{explanation[:hyde_used]}"
puts "ES count: #{explanation[:es_count]}"
puts "Embedding count: #{explanation[:emb_count]}"
puts "Fusion weights: #{explanation[:fusion_weights]}"

# Per-candidate explanation
explanation[:results].each do |res|
  puts "Candidate #{res[:id]}: rank=#{res[:rank]}, score=#{res[:final_score]}"
end
```

---

## Integração com Frontend

### Mostrar Confidence no UI

```erb
<%# app/views/candidates/search_results.html.erb %>

<% if @search_result.metadata[:search_type] == :resume %>
  <div class="search-quality-indicator">
    <% confidence = @search_result.metadata[:extraction_confidence] %>
    
    <% if confidence >= 0.75 %>
      <span class="badge badge-success">
        Alta qualidade de extração (#{(confidence * 100).to_i}%)
      </span>
    <% elsif confidence >= 0.50 %>
      <span class="badge badge-warning">
        Extração parcial (#{(confidence * 100).to_i}%)
      </span>
    <% else %>
      <span class="badge badge-danger">
        Extração limitada (#{(confidence * 100).to_i}%)
        <small>Algumas informações podem estar faltando</small>
      </span>
    <% end %>
    
    <% if @search_result.metadata[:missing_fields].any? %>
      <small class="text-muted">
        Campos não extraídos: <%= @search_result.metadata[:missing_fields].join(', ') %>
      </small>
    <% end %>
  </div>
<% end %>
```

### Highlight de Skills (JD Search)

```erb
<%# app/views/candidates/search_results.html.erb %>

<% if @search_result.metadata[:search_type] == :job_description %>
  <div class="jd-skills-detected">
    <h5>Skills Detectadas na Vaga:</h5>
    
    <div class="required-skills">
      <strong>Obrigatórias:</strong>
      <% @search_result.metadata[:required_skills].each do |skill| %>
        <span class="badge badge-danger"><%= skill %></span>
      <% end %>
    </div>
    
    <div class="nice-to-have-skills">
      <strong>Desejáveis:</strong>
      <% @search_result.metadata[:nice_to_have_skills].each do |skill| %>
        <span class="badge badge-info"><%= skill %></span>
      <% end %>
    </div>
  </div>
  
  <%# Highlight candidatos com mais required skills %>
  <% @search_result.candidates.each do |candidate| %>
    <% meta = @search_result.search_meta_by_id[candidate.id] %>
    <% if meta[:boost_breakdown][:required_skill_match] %>
      <div class="candidate-card highlight-required-match">
        <!-- ... -->
        <span class="badge badge-success">
          Atende requisitos obrigatórios
        </span>
      </div>
    <% end %>
  <% end %>
<% end %>
```

### Score Visualization

```erb
<%# app/views/candidates/_candidate_card.html.erb %>

<% meta = search_meta_by_id[candidate.id] %>

<div class="candidate-score-breakdown">
  <div class="score-bar">
    <div class="score-fill" style="width: <%= (meta[:score] * 100).to_i %>%">
      <%= (meta[:score] * 100).to_i %>%
    </div>
  </div>
  
  <div class="score-sources">
    <span class="source-es" style="width: <%= (meta[:contributions][:elasticsearch] * 100).to_i %>%">
      ES: <%= (meta[:contributions][:elasticsearch] * 100).to_i %>%
    </span>
    <span class="source-emb" style="width: <%= (meta[:contributions][:embedding] * 100).to_i %>%">
      Semantic: <%= (meta[:contributions][:embedding] * 100).to_i %>%
    </span>
  </div>
  
  <% if meta[:boost] > 0 %>
    <div class="boosts-applied">
      <small class="text-success">
        +<%= (meta[:boost] * 100).to_i %>% boost
        <% if meta[:boost_breakdown][:multi_query_match] %>
          (incluindo multi-query: <%= (meta[:boost_breakdown][:multi_query_match] * 100).to_i %>%)
        <% end %>
      </small>
    </div>
  <% end %>
  
  <% if meta[:multi_query_hits] && meta[:multi_query_hits] > 1 %>
    <div class="multi-query-indicator">
      <i class="fa fa-star"></i>
      Apareceu em <%= meta[:multi_query_hits] %> queries diferentes
    </div>
  <% end %>
</div>
```

---

## Troubleshooting

### Problema: Poucos resultados retornados

**Sintomas:**
```ruby
result = service.search("ruby developer", limit: 50)
result.candidates.size  # => 3 (esperava 50)
```

**Causas possíveis:**

1. **Filtros muito restritivos**
   ```ruby
   # Solução: Relaxar filtros
   result = service.search(
     "ruby developer",
     user_filters: {},  # Sem filtros primeiro
     limit: 50
   )
   ```

2. **Pool size muito pequeno**
   ```ruby
   # Verificar configuração
   puts Configuration.initial_pool_size  # Deve ser >= 100
   
   # Ajustar via ENV
   ENV['SEARCH_INITIAL_POOL_SIZE'] = '200'
   ```

3. **Embedding relevance filter muito alto**
   ```ruby
   # Verificar threshold
   puts Configuration.embedding_relevance_threshold  # 0.65 default
   
   # Desabilitar temporariamente
   ENV['EMBEDDING_KEYWORD_GATE'] = 'false'
   ```

---

### Problema: Busca muito lenta

**Sintomas:**
```ruby
Benchmark.measure { service.search("query", limit: 10) }.real
# => 5.2 seconds (esperava ~2s)
```

**Diagnóstico:**

```ruby
# Ativar telemetry logs
result = service.search("query", limit: 10)

# Ver breakdown de tempo
Rails.logger.info("Total time: #{result.metadata[:telemetry][:total_time]}")
Rails.logger.info("LLM time: #{result.metadata[:telemetry][:llm_time]}")
Rails.logger.info("ES time: #{result.metadata[:telemetry][:es_time]}")
Rails.logger.info("Embedding time: #{result.metadata[:telemetry][:embedding_time]}")
```

**Soluções:**

1. **LLM timeout**
   ```ruby
   # Aumentar timeout do Gemini
   ENV['GEMINI_TIMEOUT'] = '10'  # segundos
   ```

2. **Embedding API lenta**
   ```ruby
   # Verificar cache hit rate
   cache_stats = EmbeddingCache.stats
   puts "Hit rate: #{cache_stats[:hit_rate]}"  # Deve ser >60%
   
   # Preaquecer cache para queries comuns
   common_queries = ["ruby", "python", "java", "senior developer"]
   common_queries.each do |q|
     EmbeddingCache.fetch(q, account_id: account.id)
   end
   ```

3. **Pool size muito grande**
   ```ruby
   # Reduzir para buscas rápidas
   result = service.search(
     "query",
     limit: 10  # Vai usar pool = 40 (min)
   )
   ```

---

### Problema: Confidence sempre baixa

**Sintomas:**
```ruby
result = service.search(resume_text, limit: 10)
result.metadata[:extraction_confidence]  # => 0.40 (sempre)
result.metadata[:extraction_method]  # => :keyword_fallback
```

**Causas:**

1. **LLM não está respondendo**
   ```ruby
   # Testar LLM diretamente
   client = GeminiClient.new
   response = client.chat(
     model: ENV['GEMINI_CHAT_MODEL'],
     messages: [{ role: 'user', content: 'test' }]
   )
   
   # Verificar API key
   puts ENV['GEMINI_API_KEY'].present?
   ```

2. **Formato de resposta inválido**
   ```ruby
   # ProfileExtractor espera JSON válido
   # Verificar logs para ver resposta crua do LLM
   Rails.logger.debug("LLM response: #{response}")
   ```

3. **Texto muito curto**
   ```ruby
   # Extraction precisa de pelo menos 100 chars
   resume_text.length  # => 50 (muito curto!)
   
   # Solução: Avisar usuário
   if resume_text.length < 100
     flash[:warning] = "CV muito curto, resultados podem ser limitados"
   end
   ```

---

### Problema: JD não detectada corretamente

**Sintomas:**
```ruby
jd_text = "Vaga para desenvolvedor Ruby..."
result = service.search(jd_text, limit: 10)
result.metadata[:search_type]  # => :resume (errado! deveria ser :job_description)
```

**Solução:**

```ruby
# 1. Verificar indicadores
type = SimpleQueryDetector.detect(jd_text)
puts "Detected: #{type}"

# 2. Debug detecção
jd_score = SimpleQueryDetector::JD_INDICATORS.count { |p| jd_text.match?(p) }
resume_score = SimpleQueryDetector::RESUME_INDICATORS.count { |p| jd_text.match?(p) }

puts "JD score: #{jd_score}"        # Deve ser >= 2
puts "Resume score: #{resume_score}"

# 3. Se JD real mas não detectada, adicionar keywords
jd_text_fixed = "Requisitos da vaga: #{jd_text}"
# Ou
jd_text_fixed = "#{jd_text}\n\nResponsabilidades: ..."

result = service.search(jd_text_fixed, limit: 10)
```

---

## Performance Tips

### 1. Cache Agressivo

```ruby
# Controller-level caching
def search
  cache_key = "search/#{current_account.id}/#{Digest::SHA256.hexdigest(params[:q])}/#{params[:limit]}"
  
  @result = Rails.cache.fetch(cache_key, expires_in: 1.hour) do
    service = Candidates::Search::HybridSearchService.new(
      account_id: current_account.id,
      tenant: current_account.tenant
    )
    service.search(params[:q], limit: params[:limit] || 10)
  end
end
```

### 2. Pagination Inteligente

```ruby
# Não buscar tudo de uma vez
# Busca incremental:

# Página 1: limit=10
result = service.search(query, limit: 10)

# Usuário clica "Ver mais"
# Página 2: limit=20 (cache pode ajudar)
result = service.search(query, limit: 20)

# Ou: buscar 50 de uma vez e paginar no frontend
result = service.search(query, limit: 50)
candidates_page_1 = result.candidates[0..9]
candidates_page_2 = result.candidates[10..19]
# ...
```

### 3. Background Jobs para Buscas Pesadas

```ruby
# app/jobs/resume_search_job.rb
class ResumeSearchJob < ApplicationJob
  queue_as :default
  
  def perform(resume_text, account_id, user_id)
    service = Candidates::Search::HybridSearchService.new(
      account_id: account_id,
      tenant: Account.find(account_id).tenant
    )
    
    result = service.search(resume_text, limit: 50)
    
    # Salvar resultado para usuário acessar depois
    SearchResult.create!(
      user_id: user_id,
      query: resume_text[0..100],
      candidate_ids: result.candidates.map(&:id),
      metadata: result.metadata
    )
    
    # Notificar usuário
    SearchCompleteNotification.with(result: result).deliver_later(User.find(user_id))
  end
end

# Controller
def upload_resume
  ResumeSearchJob.perform_later(
    params[:resume_file].read,
    current_account.id,
    current_user.id
  )
  
  flash[:notice] = "Busca em andamento. Você será notificado quando concluir."
  redirect_to searches_path
end
```

---

## Best Practices

### ✅ DO

1. **Use cache quando possível**
   ```ruby
   Rails.cache.fetch("search/#{query_hash}") do
     service.search(query, limit: 10)
   end
   ```

2. **Mostre confidence ao usuário**
   ```ruby
   if result.metadata[:extraction_confidence] < 0.5
     flash[:warning] = "Resultados podem ser limitados"
   end
   ```

3. **Ajuste limit baseado em uso**
   ```ruby
   # Preview: limit baixo
   limit = preview_mode ? 5 : 50
   ```

4. **Monitore performance**
   ```ruby
   ActiveSupport::Notifications.subscribe("search.candidates") do |*args|
     event = ActiveSupport::Notifications::Event.new(*args)
     Rails.logger.info("Search took: #{event.duration}ms")
   end
   ```

### ❌ DON'T

1. **Não busque sem limite**
   ```ruby
   # BAD
   service.search(query, limit: 1000)  # Muito lento!
   
   # GOOD
   service.search(query, limit: 50)
   ```

2. **Não ignore metadados**
   ```ruby
   # BAD
   result.candidates  # Só pegar candidatos
   
   # GOOD
   if result.metadata[:search_type] == :resume
     # Lógica específica para resume
   end
   ```

3. **Não faça busca síncrona para uploads grandes**
   ```ruby
   # BAD
   result = service.search(huge_resume_text, limit: 100)  # 5s+
   
   # GOOD
   ResumeSearchJob.perform_later(huge_resume_text, ...)
   ```

---

**Versão:** 2.0  
**Última atualização:** 2026-02-01  
**Suporte:** dev-team@empresa.com
