# frozen_string_literal: true

module Candidates
  class ResumeParserService
    attr_reader :text, :additional_data, :ai_provider

    def initialize(text, additional_data = {}, ai_provider: :gemini)
      @text = text
      @additional_data = additional_data || {}
      @ai_provider = ai_provider
    end

    def call
      return missing_text_error if text.blank?

      begin
        extracted_data = parse_with_ai
        success_response(extracted_data)
      rescue => e
        error_response(e)
      end
    end

    private

    def parse_with_ai
      response = ai_provider == :gemini ? parse_with_gemini : parse_with_openai
      merge_additional_data(response)
    end

    def parse_with_gemini
      response = Llm::Gateway.chat(
        messages: ai_messages,
        temperature: 0.3,
        tracking: { operation: "candidates.resume_parsing" }
      )
      extract_and_parse_gemini_response(response)
    end

    def parse_with_openai
      response = OpenaiService.call(openai_params)
      return parse_openai_success(response) if response[:success]

      raise "Falha ao processar currículo com OpenAI: #{response[:error]}"
    end

    def openai_params
      {
        model: "gpt-4",
        messages: ai_messages,
        temperature: 0.3,
        response_format: { type: "json_object" }
      }
    end

    def ai_messages
      [
        { role: "system", content: system_message },
        { role: "user", content: build_prompt }
      ]
    end

    def extract_and_parse_gemini_response(response)
      text_response = response.dig("choices", 0, "message", "content")
      raise "Resposta vazia do Gemini" if text_response.blank?

      json_text = extract_json_from_text(text_response)
      JSON.parse(json_text, symbolize_names: true)
    rescue JSON::ParserError => e
      log_json_parse_error(e, text_response)
      raise "Falha ao parsear JSON do Gemini"
    end

    def parse_openai_success(response)
      JSON.parse(response[:response], symbolize_names: true)
    end

    def extract_json_from_text(text)
      cleaned = remove_markdown_wrapper(text.strip)
      extract_json_object(cleaned) || cleaned
    end

    def remove_markdown_wrapper(text)
      return text unless text.start_with?("```")

      text.gsub(/^```(?:json)?\s*\n/, "").gsub(/\n```$/, "")
    end

    def extract_json_object(text)
      start_idx = text.index("{")
      end_idx = text.rindex("}")

      return nil unless start_idx && end_idx && end_idx > start_idx

      text[start_idx..end_idx]
    end

    def merge_additional_data(extracted)
      extracted[:email] = additional_data[:email] if additional_data[:email].present?
      extracted[:mobile_phone] = additional_data[:phone] if additional_data[:phone].present?
      extracted[:linkedin] = additional_data[:linkedin] if additional_data[:linkedin].present?

      merge_location_data(extracted) if additional_data[:location].present?

      extracted
    end

    def merge_location_data(extracted)
      parts = additional_data[:location].split(",").map(&:strip)
      extracted[:city] = parts[0] if parts[0].present?
      extracted[:state] = parts[1] if parts[1].present?
      extracted[:country] = parts[2] || "Brasil"
    end

    def missing_text_error
      { success: false, error: "Texto do currículo não fornecido" }
    end

    def success_response(data)
      { success: true, data: data }
    end

    def error_response(error)
      Rails.logger.error "[ResumeParserService] Error: #{error.class}"
      { success: false, error: "Falha ao processar currículo" }
    end

    def log_json_parse_error(error, text_response)
      Rails.logger.error "[ResumeParserService] JSON parse error (#{error.class})"
      Rails.logger.error "[ResumeParserService] Response text length: #{text_response&.length || 0} chars"
    end

    def system_message
      <<~PROMPT
        Você é um especialista em análise de currículos e extração de dados estruturados.
        Sua tarefa é analisar o texto do currículo fornecido e extrair informações relevantes
        em formato JSON estruturado.

        IMPORTANTE:
        - Retorne APENAS JSON válido, sem markdown ou texto adicional
        - Use o mesmo formato do LinkedIn (data_raw) quando possível
        - Seja preciso e não invente informações que não estão no texto
        - Se alguma informação não estiver disponível, use null

        Estrutura esperada do JSON:
        {
          "name": "Nome completo",
          "email": "email@exemplo.com",
          "mobile_phone": "+55 11 99999-9999",
          "phone": "telefone adicional",
          "linkedin": "URL do LinkedIn",
          "github": "URL do GitHub",
          "portfolio": "URL do portfólio",
          "current_company": "Empresa atual",
          "role_name": "Cargo/Posição atual",
          "city": "Cidade",
          "state": "Estado",
          "country": "País",
          "self_introduction": "Resumo profissional ou sobre",
          "skills": ["Skill 1", "Skill 2", "Skill 3"],
          "languages": [
            {
              "language": "English",
              "proficiency": "Fluente"
            }
          ],
          "experiences": [
            {
              "company": "Nome da empresa",
              "position": "Cargo",
              "start_date": "2020-01",
              "end_date": "2023-12",
              "description": "Descrição das atividades",
              "is_current": false
            }
          ],
          "educations": [
            {
              "institution": "Nome da instituição",
              "degree": "Grau/Curso",
              "field_of_study": "Área de estudo",
              "start_date": "2015-01",
              "end_date": "2019-12"
            }
          ],
          "data_raw": {
            "basic_info": {},
            "education": [],
            "experience": [],
            "skills": [],
            "languages": []
          }
        }

        Notas sobre datas:
        - Use formato YYYY-MM quando tiver mês e ano
        - Use formato YYYY quando tiver apenas o ano
        - Para experiência atual, use null em end_date e is_current: true

        Notas sobre idiomas:
        - Normalize os nomes: Português → Portuguese, Inglês → English
        - Mapeie níveis: Básico → Elementary, Intermediário → Intermediate,#{' '}
          Avançado → Advanced, Fluente → Fluent, Nativo → Native
      PROMPT
    end

    def build_prompt
      <<~PROMPT
        Analise o seguinte currículo e extraia todas as informações relevantes em formato JSON:

        ```
        #{text}
        ```

        #{additional_context}

        Retorne APENAS o JSON estruturado conforme o formato especificado, sem texto adicional antes ou depois.
      PROMPT
    end

    def additional_context
      return "" if additional_data.blank?

      context = "\nInformações adicionais fornecidas:\n"

      context += "- Email: #{additional_data[:email]}\n" if additional_data[:email].present?
      context += "- Telefone: #{additional_data[:phone]}\n" if additional_data[:phone].present?
      context += "- LinkedIn: #{additional_data[:linkedin]}\n" if additional_data[:linkedin].present?
      context += "- Localização: #{additional_data[:location]}\n" if additional_data[:location].present?

      context
    end
  end
end
