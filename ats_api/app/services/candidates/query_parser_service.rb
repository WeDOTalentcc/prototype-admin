module Candidates
  class QueryParserService
    def initialize; end

    def self.call(text, **opts)
      new(**opts).call(text)
    end

    def call(text)
      return fallback_response(text) if Rails.env.test? || text.blank?

      Rails.logger.info "🔍 [Candidates::QueryParser] Parsing search query (#{text&.length || 0} chars)"

      response = Llm::Gateway.chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user", content: user_prompt(text) }
        ],
        temperature: 0.2,
        max_tokens: 1500,
        response_format: { type: "json_object" },
        tracking: { operation: "candidates.query_parsing" }
      )

      content = response.dig("choices", 0, "message", "content")
      return fallback_response(text) if content.nil?

      parsed = parse_response(content)
      Rails.logger.info "✅ [Candidates::QueryParser] Query parsed successfully"
      parsed
    rescue => e
      Rails.logger.error "❌ [Candidates::QueryParser] Error: #{e.message}"
      fallback_response(text)
    end

    private

    def fallback_response(text)
      {
        search: text.present? ? text : "*",
        where: {},
        order: {}
      }
    end

    def parse_response(content)
      clean_content = content.strip
                             .gsub(/^```json\s*\n?/, "")
                             .gsub(/^```\s*\n?/, "")
                             .gsub(/\n?```$/, "")
                             .strip

      data = JSON.parse(clean_content, symbolize_names: true)

      {
        search: data[:search] || "*",
        where: normalize_where(data[:where] || {}),
        order: data[:order] || {}
      }
    end

    def normalize_where(where)
      return {} if where.blank?

      where.transform_values do |value|
        case value
        when Hash
          normalize_where_operators(value)
        when String
          value.downcase
        when Array
          value.map { |v| v.is_a?(String) ? v.downcase : v }
        else
          value
        end
      end
    end

    def normalize_where_operators(operators)
      operators.transform_values do |v|
        v.is_a?(String) ? v.downcase : v
      end
    end

    def system_prompt
      <<~PROMPT
        Você é um especialista em converter requisições de recrutadores em filtros Elasticsearch/Searchkick.

        **CAMPOS DISPONÍVEIS:**
        - name: nome do candidato
        - email: email
        - role_name: cargo/função/experiência
        - current_company: empresa ATUAL (não use para experiências passadas)
        - city: cidade
        - state: estado
        - country: país
        - remote_work: boolean (true=aceita remoto)
        - mobility: boolean (true=tem mobilidade)
        - skills: array de habilidades
        - languages: array de idiomas
        - education_levels: nível de escolaridade
        - position_level: júnior, pleno, sênior, etc
        - years_of_experience_range: 0-1, 2-3, 4-5, 6-9, 10-14, 15+
        - clt_expectation: pretensão CLT (número)
        - pj_expectation: pretensão PJ (número)
        - age_range: 18-24, 25-34, 35-44, 45-54, 55-64, 65+

        **OPERADORES:**
        - ilike: busca parcial com % (ex: "%python%")
        - in: array de valores
        - gte: maior ou igual (>=)
        - gt: maior (>)
        - lte: menor ou igual (<=)
        - lt: menor (<)

        **REGRAS:**
        1. Retorne APENAS JSON válido (sem markdown)
        2. SEMPRE minúsculas em textos
        3. "search" = termo geral OU "*"
        4. "where" = filtros estruturados
        5. "order" = ordenação (opcional)

        **ESTRUTURA:**
        {
          "search": "*",
          "where": {
            "campo": { "operador": "valor" }
          },
          "order": {
            "campo": "asc ou desc"
          }
        }

        **EXEMPLOS:**

        Input: "desenvolvedores ruby on rails em são paulo"
        Output: {
          "search": "*",
          "where": {
            "skills": { "in": ["ruby", "rails", "ruby on rails"] },
            "city": { "ilike": "%são paulo%" }
          },
          "order": {},
          "metadata": {
            "original_query": "desenvolvedores ruby on rails em são paulo",

        **EXEMPLOS:**

        1. "desenvolvedores ruby on rails em são paulo"
        {
          "search": "*",
          "where": {
            "skills": { "in": ["ruby", "rails", "ruby on rails"] },
            "city": { "ilike": "%são paulo%" }
          },
          "order": {}
        }

        2. "gerente de projetos sênior que trabalha na google"
        {
          "search": "*",
          "where": {
            "role_name": { "ilike": "%gerente de projetos%" },
            "position_level": { "ilike": "%sênior%" },
            "current_company": { "ilike": "%google%" }
          },
          "order": {}
        }

        3. "candidatos com pretensão pj acima de 15000"
        {
          "search": "*",
          "where": {
            "pj_expectation": { "gte": 15000 }
          },
          "order": {}
        }

        4. "python developer com mais de 5 anos de experiência"
        {
          "search": "*",
          "where": {
            "skills": { "in": ["python"] },
            "years_of_experience_range": { "in": ["6-9", "10-14", "15+"] }
          },
          "order": {}
        }

        5. "liste todos"
        {
          "search": "*",
          "where": {},
          "order": { "updated_at": "desc" }
        }
      PROMPT
    end

    def user_prompt(text)
      "Converta em JSON: \"#{text}\""
    end
  end
end
