module SourcedProfiles
  class QueryRequirementsExtractor
    REQUIREMENT_TYPES = %w[skill experience education location seniority industry background certification].freeze
    PRIORITIES = %w[essential important nice_to_have].freeze

    def initialize(logger: Rails.logger)
      @logger = logger
    end

    def call(query, sourcing: nil)
      return skipped("query vazia") if query.blank?

      begin
        system_msg = system_prompt
        user_msg = user_prompt(query)

        @logger.info "=" * 100
        @logger.info "🔍 [QueryRequirementsExtractor] Extraindo requisitos da busca"
        @logger.info "=" * 100
        @logger.info "Query: #{query}"
        @logger.info "=" * 100

        response = Llm::Gateway.chat(
          messages: [
            { role: "system", content: system_msg },
            { role: "user", content: user_msg }
          ],
          temperature: 0.1,
          max_tokens: 2048,
          response_format: { type: "json_object" },
          tracking: { operation: "sourcing.query_requirements_extraction" }
        )

        raw_content = response.dig("choices", 0, "message", "content")

        @logger.info "=" * 100
        @logger.info "✨ [QueryRequirementsExtractor] Requisitos extraídos"
        @logger.info "=" * 100
        @logger.info raw_content
        @logger.info "=" * 100

        parsed = parse_response(response)
        return skipped("resposta vazia") if parsed.nil?

        usage = response.dig("usage") || {}
        cost = calculate_cost(usage)

        result = {
          status: :ok,
          requirements: parsed[:requirements],
          metadata: {
            inferred_seniority: parsed[:inferred_seniority],
            inferred_industry: parsed[:inferred_industry],
            model: Llm::ClientFactory.chat_model,
            extracted_at: Time.current,
            prompt_tokens: usage["prompt_tokens"],
            completion_tokens: usage["completion_tokens"],
            total_tokens: usage["total_tokens"],
            cost_usd: cost.round(6)
          }
        }

        sourcing&.update(parsed_requirements: result) if sourcing

        @logger.info "✅ [QueryRequirementsExtractor] #{result[:requirements].size} requisitos extraídos"
        result
      rescue => e
        @logger.error "❌ [QueryRequirementsExtractor] Error: #{e.message}"
        { status: :error, error: e.message }
      end
    end

    private

    def system_prompt
      <<~PROMPT
        Você é um especialista em análise de requisitos de recrutamento.
        Sua função é extrair e estruturar os requisitos de uma busca de candidatos.
        Retorne APENAS JSON válido, sem markdown ou explicações.
      PROMPT
    end

    def user_prompt(query)
      <<~PROMPT
        # BUSCA DE RECRUTAMENTO
        #{query}

        # INSTRUÇÕES
        Extraia os requisitos desta busca e classifique cada um por:
        1. Tipo: #{REQUIREMENT_TYPES.join(', ')}
        2. Prioridade: essential (obrigatório), important (desejável forte), nice_to_have (diferencial)
        3. Peso para scoring: essential=30, important=20, nice_to_have=10

        # FORMATO DE RESPOSTA
        {
          "requirements": [
            {
              "text": "<requisito em português, claro e objetivo>",
              "priority": "essential|important|nice_to_have",
              "type": "#{REQUIREMENT_TYPES[0..3].join('|')}",
              "weight": 30
            }
          ],
          "inferred_seniority": "junior|pleno|senior|especialista|null",
          "inferred_industry": "<setor inferido ou null>"
        }

        REGRAS:
        - Máximo 8 requisitos (foque no essencial)
        - Seja específico e mensurável
        - Priorize requisitos técnicos/hard skills como essential
        - Soft skills geralmente são nice_to_have
        - Se não houver indicação clara de senioridade/indústria, use null
      PROMPT
    end

    def parse_response(response)
      content = response.dig("choices", 0, "message", "content")
      return nil unless content.present?

      cleaned = content.strip
                      .gsub(/^```json\s*\n?/, "")
                      .gsub(/^```\s*\n?/, "")
                      .gsub(/\n?```$/, "")
                      .strip

      return nil if cleaned.blank?

      data = JSON.parse(cleaned, symbolize_names: true)
      sanitize_payload(data)
    rescue JSON::ParserError => e
      @logger.error "❌ [QueryRequirementsExtractor] Failed to parse JSON: #{e.message}"
      nil
    end

    def sanitize_payload(data)
      {
        requirements: sanitize_requirements(data[:requirements]),
        inferred_seniority: data[:inferred_seniority].to_s.presence,
        inferred_industry: data[:inferred_industry].to_s.presence
      }
    end

    def sanitize_requirements(items)
      Array(items).first(8).map do |req|
        priority = PRIORITIES.include?(req[:priority]) ? req[:priority] : "important"
        weight = case priority
        when "essential" then 30
        when "important" then 20
        else 10
        end

        {
          text: req[:text].to_s.truncate(150),
          priority: priority,
          type: REQUIREMENT_TYPES.include?(req[:type]) ? req[:type] : "skill",
          weight: weight
        }
      end
    end

    def calculate_cost(usage)
      prompt_tokens = usage["prompt_tokens"] || 0
      completion_tokens = usage["completion_tokens"] || 0

      input_cost = (prompt_tokens / 1_000_000.0) * 0.075
      output_cost = (completion_tokens / 1_000_000.0) * 0.30

      input_cost + output_cost
    end

    def skipped(reason)
      { status: :skipped, error: reason }
    end
  end
end
