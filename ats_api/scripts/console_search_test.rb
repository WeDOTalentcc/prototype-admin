# scripts/console_search_test.rb
#
# Testar busca de candidatos no Rails console.
#
# Uso:
#   rails c
#   load "scripts/console_search_test.rb"
#
# Ou copie os blocos abaixo direto no console.

module ConsoleSearchTest
  # --- 1) Pegar account e tenant ---
  # Use uma conta que já exista (ou crie uma). Exemplo:
  def self.setup
    account = Account.first
    if account.blank?
      puts "Nenhuma Account encontrada. Crie uma com Account.create!(name: 'Test', tenant: 'tenant1')"
      return nil
    end
    { account_id: account.id, tenant: account.tenant }
  end

  # --- 2) Busca simples (query curta = rota SIMPLE, sem QueryAnalyzer) ---
  def self.run_simple_search(account_id:, tenant:)
    service = Candidates::Search::HybridSearchService.new(account_id: account_id, tenant: tenant)
    query = "desenvolvedor react senior"
    puts "Query: #{query}"
    start = Time.now
    result = service.search(query, limit: 20)
    elapsed = ((Time.now - start) * 1000).round
    puts "Resultados: #{result.candidates.size} | Tempo: #{elapsed}ms | Tipo: #{result.metadata[:search_type]}"
    result.candidates.first(3).each { |c| puts "  - #{c.name} | #{c.role_name} | id=#{c.id}" }
    result
  end

  # --- 3) Busca com filtros ---
  def self.run_search_with_filters(account_id:, tenant:, city: nil)
    service = Candidates::Search::HybridSearchService.new(account_id: account_id, tenant: tenant)
    filters = city ? { city: city } : {}
    result = service.search("frontend vue", user_filters: filters, limit: 10)
    puts "Resultados: #{result.candidates.size}"
    result
  end

  # --- 4) Criar candidatos de teste (volume) ---
  # CUIDADO: roda no tenant atual. Use Apartment::Tenant.switch!(tenant) antes.
  def self.create_test_candidates(account_id:, count: 10, tenant: nil)
    block = lambda do
      count.times do |i|
        Candidate.create!(
          account_id: account_id,
          is_deleted: false,
          uid: SecureRandom.uuid,
          name: "Candidato Teste #{i + 1}",
          email: "teste#{i + 1}-#{SecureRandom.hex(4)}@example.com",
          role_name: [ "Desenvolvedor Frontend", "Desenvolvedor Backend", "Desenvolvedor Full Stack", "Engenheiro de Software" ].sample,
          curriculum_text: "Experiencia em React, Vue.js, Node.js, Ruby on Rails. #{[ 'Senior', 'Pleno', 'Junior' ].sample}.",
          current_company: [ "Empresa A", "Empresa B", "Startup X" ].sample
        )
      end
      puts "Criados #{count} candidatos."
      Candidate.reindex
      puts "Reindex feito (Searchkick)."
    end
    if tenant.present?
      Apartment::Tenant.switch(tenant, &block)
    else
      block.call
    end
  end

  # --- 5) Executar fluxo completo de teste ---
  def self.run_all(account_id: nil, tenant: nil, create_volume: 0)
    opts = setup
    return if opts.nil?

    account_id ||= opts[:account_id]
    tenant ||= opts[:tenant]

    if create_volume.positive?
      puts "\n--- Criando #{create_volume} candidatos de teste ---"
      create_test_candidates(account_id: account_id, count: create_volume, tenant: tenant)
    end

    puts "\n--- Busca simples ---"
    run_simple_search(account_id: account_id, tenant: tenant)

    puts "\n--- Busca com limite 5 ---"
    service = Candidates::Search::HybridSearchService.new(account_id: account_id, tenant: tenant)
    r = service.search("desenvolvedor", limit: 5)
    puts "Resultados: #{r.candidates.size}"
    r
  end
end

# Descomente e ajuste para rodar direto ao carregar o script:
# ConsoleSearchTest.run_all(create_volume: 5)
