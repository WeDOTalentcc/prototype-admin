# scripts/test_search_improvements.rb
#
# Valida as melhorias do sistema de busca.
# Executar: rails runner scripts/test_search_improvements.rb
#
# Ou no console: load "scripts/test_search_improvements.rb"

puts "=" * 60
puts "TESTE DE MELHORIAS DO SISTEMA DE BUSCA"
puts "=" * 60

ACCOUNT_ID = ENV.fetch("TEST_ACCOUNT_ID", 1).to_i
TENANT = begin
  ENV.fetch("TEST_TENANT") { Account.find(ACCOUNT_ID).tenant }
rescue ActiveRecord::RecordNotFound
  puts "AVISO: Account #{ACCOUNT_ID} nao encontrada. Use TEST_TENANT=seu_tenant"
  exit 1
end

puts "\nConfiguracao:"
puts "   Account ID: #{ACCOUNT_ID}"
puts "   Tenant: #{TENANT}"

# ---------------------------------------------------------------------------
# TESTE 1: Threshold adaptativo (ElasticsearchStrategy)
# ---------------------------------------------------------------------------
puts "\n" + "=" * 60
puts "TESTE 1: Threshold adaptativo no ElasticsearchStrategy"
puts "=" * 60

test_queries = [
  { query: "react", expected_threshold: "100%", description: "1 palavra" },
  { query: "desenvolvedor react", expected_threshold: "100%", description: "2 palavras" },
  { query: "dev react senior", expected_threshold: "60%", description: "3 palavras" },
  { query: "desenvolvedor frontend senior react", expected_threshold: "60%", description: "4 palavras" },
  { query: "desenvolvedor frontend senior react node.js", expected_threshold: "40%", description: "5 palavras" },
  { query: "desenvolvedor full stack ruby rails vue elasticsearch", expected_threshold: "40%", description: "7 palavras" },
  { query: ("a " * 15).strip, expected_threshold: "25%", description: "15 palavras" },
  { query: ("a " * 50).strip, expected_threshold: "15%", description: "50 palavras" }
]

Apartment::Tenant.switch(TENANT) do
  strategy = Candidates::Search::ElasticsearchStrategy.new(account_id: ACCOUNT_ID)

  test_queries.each do |t|
    threshold = strategy.send(:calculate_threshold, t[:query])
    status = threshold == t[:expected_threshold] ? "OK" : "FALHA"
    puts "  #{status} #{t[:description]}: threshold=#{threshold} (esperado: #{t[:expected_threshold]})"
  end
end

# ---------------------------------------------------------------------------
# TESTE 2: Quantidade de resultados por threshold
# ---------------------------------------------------------------------------
puts "\n" + "=" * 60
puts "TESTE 2: Quantidade de resultados com diferentes thresholds"
puts "=" * 60

query = "desenvolvedor frontend senior react node.js"
thresholds = [ "60%", "40%", "30%", "25%", "15%", "1" ]

Apartment::Tenant.switch(TENANT) do
  puts "Query: '#{query}'"
  thresholds.each do |threshold|
    begin
      results = Candidate.search(
        query,
        operator: "or",
        fields: [ "curriculum_text^5", "role_name^3", "name^2" ],
        per_page: 100,
        load: false,
        body_options: {
          query: { bool: { minimum_should_match: threshold } }
        }
      )
      top_score = results.response.dig("hits", "hits", 0, "_score")&.round(2) || 0
      puts "   #{threshold.ljust(5)} -> #{results.total_count.to_s.rjust(4)} resultados | Top score: #{top_score}"
    rescue => e
      puts "   #{threshold.ljust(5)} -> Erro: #{e.message}"
    end
  end
end

# ---------------------------------------------------------------------------
# TESTE 3: SimpleQueryDetector
# ---------------------------------------------------------------------------
puts "\n" + "=" * 60
puts "TESTE 3: Deteccao de tipo de query (SimpleQueryDetector)"
puts "=" * 60

detector_tests = [
  { query: "react", expected: :simple },
  { query: "desenvolvedor react senior", expected: :simple },
  { query: "dev frontend vue.js", expected: :simple },
  { query: "desenvolvedor com 5 anos de experiencia em react", expected: :complex },
  { query: "preciso de alguem que saiba react e node.js", expected: :complex },
  { query: "fullstack sem experiencia com java", expected: :complex }
]

detector_tests.each do |t|
  result = Candidates::Search::SimpleQueryDetector.detect(t[:query])
  status = result == t[:expected] ? "OK" : "FALHA"
  short = t[:query].length > 50 ? "#{t[:query][0, 47]}..." : t[:query]
  puts "  #{status} '#{short}' -> #{result} (esperado: #{t[:expected]})"
end

# ---------------------------------------------------------------------------
# TESTE 4: Busca completa (HybridSearchService)
# ---------------------------------------------------------------------------
puts "\n" + "=" * 60
puts "TESTE 4: Busca completa (HybridSearchService)"
puts "=" * 60

e2e_queries = [
  "desenvolvedor react",
  "desenvolvedor frontend senior react node.js",
  "fullstack com experiencia em fintech"
]

Apartment::Tenant.switch(TENANT) do
  service = Candidates::Search::HybridSearchService.new(
    account_id: ACCOUNT_ID,
    tenant: TENANT
  )

  e2e_queries.each do |q|
    puts "\nQuery: '#{q}'"
    start_time = Time.now
    begin
      result = service.search(q, limit: 20, debug: false)
      elapsed = ((Time.now - start_time) * 1000).round
      puts "   Resultados: #{result.candidates.size}"
      puts "   Tempo: #{elapsed}ms"
      puts "   Tipo de busca: #{result.metadata[:search_type] || 'N/A'}"
      puts "   QueryAnalyzer pulado: #{result.metadata[:query_analyzer_skipped] ? 'Sim' : 'Nao'}"
      if result.candidates.any?
        puts "   Top 3: #{result.candidates.first(3).map(&:name).join(', ')}"
      end
    rescue => e
      puts "   Erro: #{e.message}"
      puts e.backtrace.first(3).map { |l| "     #{l}" }.join("\n")
    end
  end
end

# ---------------------------------------------------------------------------
# RESUMO
# ---------------------------------------------------------------------------
puts "\n" + "=" * 60
puts "RESUMO"
puts "=" * 60
puts <<~TEXT
  Proximos passos:
  1. Se TESTE 1 passou -> ElasticsearchStrategy com threshold adaptativo OK
  2. Se TESTE 2 mostra mais resultados com threshold menor -> correcao funcionando
  3. Se TESTE 3 passou -> SimpleQueryDetector OK
  4. Se TESTE 4 mostra 'QueryAnalyzer pulado: Sim' para queries simples -> otimizacao OK

  Logs: procure por [ESStrategy] e [HybridSearch] nos logs da aplicacao.
TEXT
