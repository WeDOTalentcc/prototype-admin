# frozen_string_literal: true

module Candidates
  module Search
    # Helper para testar busca híbrida no Rails console e ver se os candidatos fazem sentido.
    #
    # Uso:
    #   account = Account.find(1)
    #   Apartment::Tenant.switch(account.tenant) do
    #     Candidates::Search::ConsoleDebug.run("frontend react senior nginx postgres", account_id: account.id, limit: 15)
    #   end
    #
    # Ou com tenant já ativo:
    #   Candidates::Search::ConsoleDebug.run("frontend react senior", account_id: 1, limit: 10)
    class ConsoleDebug
      CURRICULUM_SNIPPET = 280

      class << self
        def run(search_text, account_id:, limit: 15)
          account = Account.find(account_id)
          tenant = account.tenant

          Apartment::Tenant.switch(tenant) do
            puts "\n#{'='*80}"
            puts "BUSCA: \"#{search_text}\""
            puts "Account: #{account.id} | Tenant: #{tenant} | Limit: #{limit}"
            puts "="*80

            service = HybridSearchService.new(account_id: account.id, tenant: tenant)
            result = service.search(search_text, user_filters: {}, limit: limit, debug: true)

            if result.explanation
              q = result.explanation["query"] || result.explanation[:query]
              if q
                puts "\n📌 Query usada no ES:  #{q['elasticsearch_query'] || q[:elasticsearch_query]}"
                puts "📌 Query usada no embedding: #{q['embedding_query'] || q[:embedding_query]}"
              end
              sources = result.explanation["sources"] || result.explanation[:sources]
              if sources
                puts "   Resultados ES: #{sources.dig('elasticsearch', 'count') || sources.dig(:elasticsearch, :count)} | Embedding: #{sources.dig('embedding', 'count') || sources.dig(:embedding, :count)}"
              end
              puts "   ES-first ordering: #{result.explanation['es_first_ordering'] || result.explanation[:es_first_ordering]}" if result.explanation.key?("es_first_ordering") || result.explanation.key?(:es_first_ordering)
            end

            puts "\n--- CANDIDATOS (#{result.candidates.size}) ---\n"

            result.candidates.each_with_index do |c, i|
              role = c.role_name.presence || "-"
              company = c.current_company.presence || "-"
              curr = c.curriculum_text.to_s.strip
              snippet = curr.present? ? curr.truncate(CURRICULUM_SNIPPET, omission: "…") : "(sem currículo)"

              puts "#{i + 1}. [id=#{c.id}] #{c.name}"
              puts "   Cargo: #{role} | Empresa: #{company}"
              puts "   Currículo: #{snippet}"
              puts ""
            end

            puts "="*80
            puts "Total: #{result.candidates.size} candidatos. Revise se os perfis batem com a busca."
            puts "="*80 + "\n"

            result
          end
        end

        # Testa apenas a busca por embedding (sem Elasticsearch), para ver o que o pg_vector retorna.
        # Uso: Apartment::Tenant.switch(account.tenant) { ConsoleDebug.run_embedding_only("frontend react senior", account_id: account.id, limit: 15) }
        def run_embedding_only(search_text, account_id:, limit: 15)
          account = Account.find(account_id)
          tenant = account.tenant

          Apartment::Tenant.switch(tenant) do
            puts "\n#{'='*80}"
            puts "BUSCA SÓ EMBEDDING: \"#{search_text}\""
            puts "Account: #{account.id} | Tenant: #{tenant} | Limit: #{limit}"
            puts "="*80

            analyzer = QueryAnalyzer.new
            analysis = analyzer.analyze(search_text)
            hyde_text = HydeQueryExpander.new.expand(search_text)
            text_for_embedding = hyde_text.presence || analysis.embedding_query
            embedding = EmbeddingCache.new.fetch(text_for_embedding, account_id: account.id)
            puts "\n📌 Query embedding (mini currículo ideal): #{text_for_embedding.truncate(200)}"

            strategy = EmbeddingStrategy.new(account_id: account.id)
            results = strategy.search(embedding, user_filters: {}, pool_size: [ limit * 2, 100 ].max)

            # Mesmo keyword gate da busca híbrida: só candidatos com pelo menos 1 termo no currículo/cargo
            if Configuration.embedding_keyword_gate? && results.any?
              terms = (analysis.elasticsearch_query.presence || search_text).to_s.split(/\s+/).map(&:strip).reject { |w| w.size < 2 }.uniq
              if terms.any?
                all_ids = results.map { |r| r[:id] }.uniq
                candidates_for_gate = Candidate.where(id: all_ids).pluck(:id, :curriculum_text, :role_name)
                allowed_ids = candidates_for_gate.select do |_id, curr, role|
                  curr = curr.to_s.downcase
                  role = role.to_s.downcase
                  terms.any? { |t| curr.include?(t.downcase) || role.include?(t.downcase) }
                end.map(&:first).to_set
                results = results.select { |r| allowed_ids.include?(r[:id]) }
                puts "   Keyword gate: #{all_ids.size} → #{results.size} (exigiu 1+ termo: #{terms.join(', ')})"
              end
            end

            ids = results.map { |r| r[:id] }.first(limit)
            candidates = Candidate.where(id: ids).index_by(&:id)
            ordered = ids.filter_map { |id| candidates[id] }

            puts "   Resultados embedding: #{results.size} (mostrando #{ordered.size})"
            puts "\n--- CANDIDATOS (ordem do embedding) ---\n"

            ordered.each_with_index do |c, i|
              r = results.find { |x| x[:id] == c.id }
              dist = r ? r[:distance] : nil
              role = c.role_name.presence || "-"
              company = c.current_company.presence || "-"
              curr = c.curriculum_text.to_s.strip
              snippet = curr.present? ? curr.truncate(CURRICULUM_SNIPPET, omission: "…") : "(sem currículo)"

              puts "#{i + 1}. [id=#{c.id}] #{c.name} #{dist ? "(dist: #{dist.round(4)})" : ""}"
              puts "   Cargo: #{role} | Empresa: #{company}"
              puts "   Currículo: #{snippet}"
              puts ""
            end

            puts "="*80 + "\n"
            ordered
          end
        end
      end
    end
  end
end
