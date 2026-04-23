module SearchArchetypes
  class CreateFromDescriptionService
    def self.call(**args)
      new(**args).call
    end

    def initialize(account:, user:, description:)
      @account = account
      @user = user
      @description = description
    end

    def call
      extracted = extract_with_ai

      SearchArchetype.create!(
        account: @account,
        user: @user,
        uid: SecureRandom.uuid,
        name: extracted[:name] || "Arquétipo #{Time.current.to_i}",
        emoji: extracted[:emoji] || "🎯",
        description: @description,
        query: extracted[:query] || @description,
        seniority: map_seniority(extracted[:seniority]),
        min_experience_years: extracted[:min_experience_years],
        industry: extracted[:industry],
        location: extracted[:location],
        work_model: map_work_model(extracted[:work_model]),
        contract_type: map_contract_type(extracted[:contract_type]),
        skills: extracted[:skills] || [],
        tags: extracted[:tags] || [],
        languages: extracted[:languages] || [],
        local_filters: build_local_filters(extracted),
        global_filters: build_global_filters(extracted)
      )
    end

    private

    def extract_with_ai
      response = call_gemini_api
      parse_response(response)
    end

    def call_gemini_api
      Llm::Gateway.chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user", content: build_extraction_prompt }
        ],
        temperature: 0.2,
        response_format: { type: "json_object" },
        tracking: { operation: "search_archetypes.create_from_description" }
      )
    end

    def system_prompt
      <<~PROMPT
        Você é um especialista em recrutamento. Extraia informações estruturadas#{' '}
        de descrições de perfis de candidatos para criar filtros de busca.

        Sempre retorne JSON válido com os campos especificados.
      PROMPT
    end

    def build_extraction_prompt
      <<~PROMPT
        Extraia informações do seguinte perfil desejado:

        "#{@description}"

        Retorne JSON com:
        {
          "name": "nome sugerido para o arquétipo (curto, ex: 'Tech Lead Python')",
          "emoji": "emoji relevante para o perfil",
          "query": "query otimizada para busca em linguagem natural",
          "seniority": "intern|junior|mid|senior|lead|manager|director|c_level ou null",
          "min_experience_years": número ou null,
          "industry": "setor/indústria ou null",
          "location": "localização (cidade, estado) ou null",
          "work_model": "remote|hybrid|onsite|any",
          "contract_type": "clt|pj|any",
          "skills": ["skill1", "skill2"],
          "tags": ["tag1", "tag2"],
          "languages": ["Português", "Inglês"],
          "local_keywords": ["palavras-chave para busca local/Elasticsearch"],
          "global_keywords": ["palavras-chave para busca global/Pearch"],
          "reasoning": "explicação breve da extração"
        }
      PROMPT
    end

    def parse_response(response)
      content = response.dig("choices", 0, "message", "content")
      return default_extraction if content.blank?

      parse_json_content(content)
    rescue JSON::ParserError => e
      log_parse_error(e)
      default_extraction
    end

    def parse_json_content(content)
      clean_content = clean_json_response(content)
      data = JSON.parse(clean_content, symbolize_names: true)

      Rails.logger.info "[SearchArchetype] AI reasoning: #{data[:reasoning]}"
      data
    end

    def log_parse_error(error)
      Rails.logger.error "[SearchArchetype] Failed to parse AI response: #{error.message}"
    end

    def clean_json_response(content)
      content.strip
             .gsub(/^```json\s*\n?/, "")
             .gsub(/^```\s*\n?/, "")
             .gsub(/\n?```$/, "")
             .strip
    end

    def default_extraction
      {
        name: "Arquétipo #{Time.current.to_i}",
        emoji: "🎯",
        query: @description,
        skills: [],
        tags: [],
        languages: [],
        local_keywords: [],
        global_keywords: []
      }
    end

    def build_local_filters(extracted)
      {
        keywords: extracted[:local_keywords]&.join(" "),
        role_name: extracted[:query]
      }.compact
    end

    def build_global_filters(extracted)
      {
        keywords: extracted[:global_keywords]&.join(" ")
      }.compact
    end

    SENIORITY_MAP = %w[intern junior mid senior lead manager director c_level].freeze
    WORK_MODEL_MAP = { "any" => "any_work_model", "remote" => "remote", "hybrid" => "hybrid", "onsite" => "onsite" }.freeze
    CONTRACT_MAP = { "any" => "any_contract", "clt" => "clt", "pj" => "pj" }.freeze

    def map_seniority(value)
      return nil if value.blank?
      normalized = value.to_s.downcase
      SENIORITY_MAP.include?(normalized) ? normalized : nil
    end

    def map_work_model(value)
      return "any_work_model" if value.blank?
      WORK_MODEL_MAP[value.to_s.downcase] || "any_work_model"
    end

    def map_contract_type(value)
      return "any_contract" if value.blank?
      CONTRACT_MAP[value.to_s.downcase] || "any_contract"
    end
  end
end
