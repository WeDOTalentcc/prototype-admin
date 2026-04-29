module Candidates
  module Search
    class QueryAnalyzer
      TIMEOUT_SECONDS = ENV.fetch("QUERY_ANALYZER_TIMEOUT", "3.0").to_f
      CACHE_TTL = 1.hour
      CACHE_PREFIX = "query_analysis".freeze

      def initialize; end

      def analyze(query_text)
        return QueryAnalysis.passthrough(query_text) if query_text.blank?

        cached = fetch_from_cache(query_text)
        return cached if cached

        response = call_llm_with_timeout(query_text)
        return QueryAnalysis.passthrough(query_text) unless response

        analysis = parse_response(response, query_text)
        store_in_cache(query_text, analysis)

        analysis
      rescue => e
        Rails.logger.error("[QueryAnalyzer] Failed: #{e.message}")
        QueryAnalysis.passthrough(query_text)
      end

      private

      def cache_key(query_text)
        normalized = query_text.to_s.downcase.strip.gsub(/\s+/, " ")
        hash = Digest::SHA256.hexdigest(normalized)[0..15]
        "#{CACHE_PREFIX}:#{hash}"
      end

      def fetch_from_cache(query_text)
        cached_data = Rails.cache.read(cache_key(query_text))
        return nil unless cached_data

        data = cached_data.is_a?(Hash) ? cached_data.symbolize_keys : cached_data
        QueryAnalysis.new(
          original_query: data[:original_query],
          entities: data[:entities] || {},
          expanded_terms: data[:expanded_terms] || [],
          keyword_query: data[:keyword_query].to_s.strip.presence,
          embedding_query: data[:embedding_query] || data[:original_query],
          confidence: data[:confidence] || 0.5
        )
      rescue => e
        Rails.logger.warn("[QueryAnalyzer] Cache read failed: #{e.message}")
        nil
      end

      def store_in_cache(query_text, analysis)
        Rails.cache.write(
          cache_key(query_text),
          {
            original_query: analysis.original_query,
            entities: analysis.entities,
            expanded_terms: analysis.expanded_terms,
            keyword_query: analysis.keyword_query,
            embedding_query: analysis.embedding_query,
            confidence: analysis.confidence
          },
          expires_in: CACHE_TTL
        )
      rescue => e
        Rails.logger.warn("[QueryAnalyzer] Cache write failed: #{e.message}")
      end

      def call_llm_with_timeout(query_text)
        Timeout.timeout(TIMEOUT_SECONDS) do
          call_llm(query_text)
        end
      rescue Timeout::Error
        Rails.logger.warn("[QueryAnalyzer] Timeout after #{TIMEOUT_SECONDS}s, using passthrough")
        nil
      end

      def call_llm(query_text)
        Llm::Gateway.fast_chat(
          messages: [
            { role: "system", content: system_prompt },
            { role: "user", content: query_text }
          ],
          temperature: 0.1,
          max_tokens: 500,
          response_format: { type: "json_object" },
          tracking: { operation: "search.query_analysis" }
        )
      end

      def system_prompt
        <<~PROMPT
          Você analisa queries de busca de candidatos para recrutamento.

          Extraia:
          1. entities: entidades identificadas (cargo, skill, empresa, local, senioridade)
          2. expanded_terms: sinônimos e termos relacionados (para referência)
          3. keyword_query: query otimizada para busca full-text (palavras-chave no currículo).
             Regras: manter TODOS os termos importantes da intenção; corrigir erros de digitação;
             normalizar termos técnicos (ex: node -> Node.js, react -> React, mysq -> MySQL);
             NÃO adicionar sinônimos nem termos extras; deve ser concisa.
          4. embedding_query: frase otimizada para busca semântica (similaridade com currículos).
             Objetivo: candidatos com currículo e skills que batem com a vaga rankeiam alto.
             Use: cargo + senioridade + tecnologias/ferramentas principais em linguagem natural.
             Seja específico: tecnologias, ferramentas e nível (ex: sênior, pleno) que aparecem em currículos.
             Ex: "Desenvolvedor frontend React sênior com experiência em Node.js, Nginx e PostgreSQL"

          REGRAS:
          - NÃO invente informações que não estão na query
          - keyword_query: só termos que devem bater no texto (currículo, cargo, skills)
          - embedding_query: descreva o perfil ideal em uma frase densa (cargo + senioridade + stack) para que
            candidatos com currículo e stack alinhados tenham alta similaridade e apareçam no topo.

          Retorne JSON:
          {
            "entities": { "role": "...", "skills": ["..."], "location": "...", "seniority": "...", "company": "..." },
            "expanded_terms": ["termo1", "termo2"],
            "keyword_query": "termos para busca full-text corrigidos e normalizados",
            "embedding_query": "query otimizada para embedding",
            "confidence": 0.0-1.0
          }
        PROMPT
      end

      def parse_response(response, original_query)
        content = response.dig("choices", 0, "message", "content")

        clean_content = content.to_s.strip
                              .gsub(/^```json\s*\n?/i, "")
                              .gsub(/^```\s*\n?/, "")
                              .gsub(/\n?```$/, "")
                              .strip

        data = JSON.parse(clean_content, symbolize_names: true)

        QueryAnalysis.new(
          original_query: original_query,
          entities: data[:entities] || {},
          expanded_terms: data[:expanded_terms] || [],
          keyword_query: data[:keyword_query].to_s.strip.presence,
          embedding_query: data[:embedding_query] || original_query,
          confidence: data[:confidence] || 0.5
        )
      rescue JSON::ParserError => e
        Rails.logger.warn("[QueryAnalyzer] JSON parse failed: #{e.message}")
        QueryAnalysis.passthrough(original_query)
      end
    end

    class QueryAnalysis
      attr_reader :original_query, :entities, :expanded_terms, :keyword_query, :embedding_query, :confidence

      def initialize(original_query:, entities:, expanded_terms:, embedding_query:, confidence:, keyword_query: nil)
        @original_query = original_query
        @entities = entities
        @expanded_terms = expanded_terms
        @keyword_query = keyword_query
        @embedding_query = embedding_query
        @confidence = confidence
      end

      def self.passthrough(query)
        new(
          original_query: query,
          entities: {},
          expanded_terms: [],
          keyword_query: nil,
          embedding_query: query,
          confidence: 1.0
        )
      end

      def use_expanded?
        confidence >= 0.7 && expanded_terms.any?
      end

      # Query para Elasticsearch: preferir a otimizada pela LLM (keyword_query), senão original
      def elasticsearch_query
        keyword_query.presence || original_query
      end
    end
  end
end
