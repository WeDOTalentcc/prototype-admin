# frozen_string_literal: true

module EmailTemplates
  class SuggestionService
    def initialize(email_template, text, extra_params: nil)
      @email_template = email_template
      @text = text
      @extra_params = extra_params
    end

    def self.call(email_template, text, extra_params, **opts)
      new(email_template, text, extra_params: extra_params, **opts).call
    end

    def call
      return nil if Rails.env.test?
      return nil if @text.blank?

      if reject_feedback_request?
        return generate_reject_feedback
      end

      log_message = @email_template ? "for template #{@email_template.id}" : "from scratch"
      Rails.logger.info "EmailTemplates::SuggestionService: Generating suggestion #{log_message}"

      begin
        response = Llm::Gateway.chat(
          messages: [
            {
              role: "system",
              content: system_prompt
            },
            {
              role: "user",
              content: user_prompt
            }
          ],
          temperature: 0.7,
          max_tokens: 4096,
          response_format: { type: "json_object" },
          tracking: { operation: "email_templates.suggestion" }
        )

        content = response.dig("choices", 0, "message", "content")
        if content.blank?
          Rails.logger.error "EmailTemplates::SuggestionService: Empty content from API"
          return nil
        end

        Rails.logger.info "EmailTemplates::SuggestionService: Raw response content (#{content.length} chars)"
        Rails.logger.debug "EmailTemplates::SuggestionService: Content preview: #{content[0, 200]}"

        parsed = parse_response(content)
        Rails.logger.info "EmailTemplates::SuggestionService: Successfully generated suggestion: #{parsed.inspect}"
        parsed
      rescue JSON::ParserError => e
        Rails.logger.error "EmailTemplates::SuggestionService: JSON Parse Error - #{e.message}"
        Rails.logger.error "EmailTemplates::SuggestionService: Content was: #{content[0, 500] if defined?(content)}"
        fallback_response
      rescue => e
        Rails.logger.error "EmailTemplates::SuggestionService: Error - #{e.message}"
        Rails.logger.error "EmailTemplates::SuggestionService: #{e.backtrace.first(5).join('\n')}"
        fallback_response
      end
    end

    private

    def reject_feedback_request?
      @extra_params.is_a?(Hash) && ActiveModel::Type::Boolean.new.cast(@extra_params[:is_reject_feedback])
    end

    def generate_reject_feedback
      apply_id = @extra_params[:apply_id].to_i
      return nil if apply_id.zero?

      account_id = @extra_params[:account_id] || Current.account&.id
      apply = Apply.find_by(id: apply_id, account_id: account_id)
      return nil unless apply

      result = Candidates::RejectFeedbackGeneratorService.call(apply: apply)
      job_title = apply.job&.title.presence || "Vaga"
      candidate_name = apply.candidate&.name.presence || "Candidato"

      {
        name: "Feedback de rejeição - #{candidate_name}",
        subject: "Atualização sobre sua candidatura - #{job_title}",
        content: result[:feedback_text].to_s,
        category_id: 2
      }
    rescue => e
      Rails.logger.error "EmailTemplates::SuggestionService: RejectFeedback error - #{e.message}"
      nil
    end

    def available_variables(reference_types = nil)
      tag_array = EmailTemplate.tag_array

      if reference_types && reference_types.is_a?(Array) && reference_types.any?
        normalized_types = reference_types.map(&:to_s)
        filtered_tags = tag_array.select do |entity_type, _|
          normalized_types.include?(entity_type.to_s) || normalized_types.include?(entity_type.to_sym.to_s)
        end
      else
        filtered_tags = tag_array
      end

      variables_list = []
      filtered_tags.each do |entity_type, tags|
        tags.each do |tag_info|
          variables_list << "- #{tag_info[:tag]} - #{tag_info[:text]}"
        end
      end

      variables_list.join("\n          ")
    end

    def system_prompt
      if @email_template
        <<~PROMPT
          Você é um assistente especializado em criar e modificar templates de email para recrutamento.
          Sua função é gerar templates de email profissionais baseados em um template existente e nas modificações solicitadas pelo usuário.

          REGRA CRÍTICA: Você DEVE usar APENAS as variáveis fornecidas na lista de VARIÁVEIS DISPONÍVEIS, no formato exato {{nome_variavel}}.
          NUNCA use placeholders como [Nome da Posição], [Seu Cargo], [Nome da Empresa] ou qualquer outro formato que não seja {{variável}}.
          NUNCA invente variáveis que não estão na lista fornecida.

          Você deve retornar APENAS um JSON válido com os campos: name, subject, content e category.
          O campo category deve ser o ID numérico da categoria (1-5).
        PROMPT
      else
        <<~PROMPT
          Você é um assistente especializado em criar templates de email para recrutamento.
          Sua função é gerar templates de email profissionais do zero baseado nas especificações solicitadas pelo usuário.

          REGRA CRÍTICA: Você DEVE usar APENAS as variáveis fornecidas na lista de VARIÁVEIS DISPONÍVEIS, no formato exato {{nome_variavel}}.
          NUNCA use placeholders como [Nome da Posição], [Seu Cargo], [Nome da Empresa] ou qualquer outro formato que não seja {{variável}}.
          NUNCA invente variáveis que não estão na lista fornecida.

          Você deve retornar APENAS um JSON válido com os campos: name, subject, content e category.
          O campo category deve ser o ID numérico da categoria (1-5).
        PROMPT
      end
    end

    def user_prompt
      categories_list = EmailTemplate::CATEGORIES.map { |c| "#{c[:id]}: #{c[:name]}" }.join(", ")
      reference_types = nil
      subject = nil
      content = nil

      if @email_template
        current_category = EmailTemplate::CATEGORIES.find { |c| c[:id] == @email_template.category_id }
        category_name = current_category&.dig(:name) || "Não especificada"

        <<~PROMPT
          TEMPLATE ATUAL:
          Nome: #{@email_template.name}
          Assunto: #{@email_template.subject}
          Conteúdo: #{@email_template.content}
          Categoria: #{category_name} (ID: #{@email_template.category_id})

          MODIFICAÇÕES SOLICITADAS:
          #{@text}

          CATEGORIAS DISPONÍVEIS:
          #{categories_list}

          Sua tarefa:
          1. Analise o template atual e as modificações solicitadas
          2. Gere um novo template que incorpore as modificações solicitadas
          3. Mantenha a essência e o propósito do template original, aplicando as alterações pedidas
          4. Selecione a categoria apropriada (use o ID numérico) baseado no conteúdo e propósito do template
          5. Garanta que o template seja profissional, claro e adequado para recrutamento

          VARIÁVEIS DISPONÍVEIS:
          Você PODE usar APENAS as seguintes variáveis no conteúdo do email usando EXATAMENTE a sintaxe {{nome_variavel}}:
          #{available_variables}

          REGRAS OBRIGATÓRIAS PARA VARIÁVEIS:
          - Use APENAS as variáveis listadas acima, no formato exato {{nome_variavel}}
          - NUNCA use placeholders como [Nome da Posição], [Seu Cargo], [Nome da Empresa], etc.
          - NUNCA invente variáveis que não estão na lista acima
          - Se precisar mencionar algo que não tem variável disponível, use texto genérico sem placeholders
          - Exemplo CORRETO: "Prezado(a) {{candidate_name}}, informamos sobre sua aprovação para {{job_title}}"
          - Exemplo INCORRETO: "Prezado(a) {{candidate_name}}, informamos sobre sua aprovação para [Nome da Posição]"

          IMPORTANTE:
          - Retorne APENAS um JSON válido com os campos: name, subject, content, category
          - O campo category deve ser um número inteiro entre 1 e 5 (ID da categoria)
          - O campo name deve ser um nome descritivo para o template
          - O campo subject deve ser um assunto apropriado para o email (pode usar variáveis APENAS da lista acima)
          - O campo content deve ser o corpo completo do email em HTML ou texto formatado (pode usar variáveis APENAS da lista acima)
          - Use as variáveis disponíveis quando apropriado para personalizar o template
          - Se as modificações não especificarem uma categoria, mantenha a categoria original ou escolha a mais apropriada
          - Se as modificações não especificarem um nome, mantenha ou melhore o nome original
        PROMPT
      else
        reference_types = nil
        subject = nil
        content = nil

        if @extra_params
          reference_types = @extra_params[:reference_types]
          subject = @extra_params[:subject]
          content = @extra_params[:content]
        end

        extra_info = ""
        if subject.present? || content.present?
          extra_info = "\n\n          INFORMAÇÕES ADICIONAIS:\n"
          extra_info += "          Assunto sugerido: #{subject}\n" if subject.present?
          extra_info += "          Conteúdo sugerido: #{content}\n" if content.present?
        end

        <<~PROMPT
          ESPECIFICAÇÕES PARA O TEMPLATE:
          #{@text}#{extra_info}

          CATEGORIAS DISPONÍVEIS:
          #{categories_list}

          Sua tarefa:
          1. Analise as especificações fornecidas pelo usuário
          2. Crie um template de email profissional do zero baseado nas especificações
          3. Selecione a categoria apropriada (use o ID numérico) baseado no propósito do email
          4. Garanta que o template seja profissional, claro e adequado para recrutamento
          5. Se as especificações não mencionarem categoria, escolha a mais apropriada baseado no contexto

          VARIÁVEIS DISPONÍVEIS:
          Você PODE usar APENAS as seguintes variáveis no conteúdo do email usando EXATAMENTE a sintaxe {{nome_variavel}}:
          #{available_variables(reference_types)}

          REGRAS OBRIGATÓRIAS PARA VARIÁVEIS:
          - Use APENAS as variáveis listadas acima, no formato exato {{nome_variavel}}
          - NUNCA use placeholders como [Nome da Posição], [Seu Cargo], [Nome da Empresa], etc.
          - NUNCA invente variáveis que não estão na lista acima
          - Se precisar mencionar algo que não tem variável disponível, use texto genérico sem placeholders
          - Exemplo CORRETO: "Prezado(a) {{candidate_name}}, informamos sobre sua aprovação para {{job_title}}"
          - Exemplo INCORRETO: "Prezado(a) {{candidate_name}}, informamos sobre sua aprovação para [Nome da Posição]"

          IMPORTANTE:
          - Retorne APENAS um JSON válido com os campos: name, subject, content, category
          - O campo category deve ser um número inteiro entre 1 e 5 (ID da categoria)
          - O campo name deve ser um nome descritivo e claro para o template
          - O campo subject deve ser um assunto profissional e apropriado para o email (pode usar variáveis APENAS da lista acima)
          - O campo content deve ser o corpo completo do email em HTML ou texto formatado (pode usar variáveis APENAS da lista acima)
          - Use as variáveis disponíveis quando apropriado para personalizar o template
          - Seja criativo mas profissional na criação do template
          - O template deve ser útil para recrutadores enviarem para candidatos
        PROMPT
      end
    end

    def parse_response(content)
      json_content = extract_json_string(content)

      parsed = JSON.parse(json_content, symbolize_names: true)

      category_id = parsed[:category] || parsed["category"]
      category_id = category_id.to_i if category_id

      valid_category_ids = EmailTemplate::CATEGORIES.map { |c| c[:id] }
      unless valid_category_ids.include?(category_id)
        category_id = @email_template&.category_id || 1
      end

      {
        name: parsed[:name] || parsed["name"] || @email_template&.name || "Novo Template",
        subject: parsed[:subject] || parsed["subject"] || @email_template&.subject || "",
        content: parsed[:content] || parsed["content"] || @email_template&.content || "",
        category_id: category_id || @email_template&.category_id || 1
      }
    rescue JSON::ParserError => e
      Rails.logger.warn "EmailTemplates::SuggestionService: JSON parse failed, trying regex fallback - #{e.message}"
      parse_response_fallback(content) || fallback_response
    end

    def extract_json_string(content)
      str = content.to_s.strip
      str = str.sub(/\A```(?:json)?\s*\n?/i, "").sub(/\n?```\s*\z/, "")
      json_match = str.match(/\{[\s\S]*\}/m)
      json_match ? json_match[0] : str
    end

    def parse_response_fallback(content)
      str = extract_json_string(content)
      name = str[/"name"\s*:\s*"((?:[^"\\]|\\.)*)"/m, 1]&.gsub(/\\"/, '"')
      subject = str[/"subject"\s*:\s*"((?:[^"\\]|\\.)*)"/m, 1]&.gsub(/\\"/, '"')
      content_match = str.match(/"content"\s*:\s*"((?:[^"\\]|\\.)*)/m)
      content_val = content_match ? content_match[1].to_s.gsub(/\\n/, "\n").gsub(/\\"/, '"') : nil

      return nil if name.blank? && subject.blank? && content_val.blank?

      category_id = @email_template&.category_id || 1
      {
        name: name.presence || @email_template&.name || "Novo Template",
        subject: subject.presence || @email_template&.subject || "",
        content: content_val.presence || @email_template&.content || "",
        category_id: category_id
      }
    end

    def fallback_response
      if @email_template
        {
          name: @email_template.name,
          subject: @email_template.subject,
          content: @email_template.content,
          category_id: @email_template.category_id
        }
      else
        nil
      end
    end
  end
end
