# frozen_string_literal: true

class Candidates::SuggestionService
  def initialize(business_city: nil, business_state: nil)
    @business_city = business_city
    @business_state = business_state
  end

  def self.call(text, **opts)
    new(**opts).call(text)
  end

  def call(text)
    # Do not hit external APIs during tests
    return nil if Rails.env.test?

    input_text = text.to_s.strip
    if input_text.blank?
      Rails.logger.error "Candidates::SuggestionService: Empty text provided"
      return nil
    end

    suggestion_prompt = build_prompt(input_text)
    attributes_prompt = build_attributes_prompt(input_text)

    Rails.logger.debug "Candidates::SuggestionService: Making request text_length=#{input_text.length}"

    begin
      suggestion_response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um assistente copilot que ajuda recrutadores a completar textos de pesquisa de candidatos de forma natural e fluida. Sua função é sugerir uma continuação de texto que completa o que o usuário está digitando."
          },
          {
            role: "user",
            content: suggestion_prompt
          }
        ],
        temperature: 0.7,
        max_tokens: 512,
        tracking: { operation: "candidates.suggestion_autocomplete" }
      )

      suggestion_content = suggestion_response.dig("choices", 0, "message", "content")
      suggestion = suggestion_content ? parse_suggestion(suggestion_content, input_text) : nil

      attributes_response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um assistente especializado em extrair informações estruturadas de textos de busca de candidatos. Você deve retornar APENAS um JSON válido, sem texto adicional."
          },
          {
            role: "user",
            content: attributes_prompt
          }
        ],
        temperature: 0.3,
        # Gemini 2.x may reserve budget for internal reasoning; use a high ceiling to avoid truncated JSON.
        max_tokens: 8192,
        response_format: { type: "json_object" },
        tracking: { operation: "candidates.suggestion_attributes" }
      )

      attributes_content = attributes_response.dig("choices", 0, "message", "content")
      attributes = attributes_content ? parse_attributes(attributes_content) : {}

      {
        suggestion: suggestion,
        attributes: attributes
      }
    rescue => e
      Rails.logger.error "Candidates::SuggestionService: Error - #{e.message}"
      Rails.logger.error "Candidates::SuggestionService: #{e.backtrace.first(3).join('\n')}"
      nil
    end
  end

  def self.generate_query_from_files(extracted_text, **opts)
    new(**opts).generate_query_from_files(extracted_text)
  end

  def self.generate_query_from_boolean_search(boolean_query, **opts)
    new(**opts).generate_query_from_boolean_search(boolean_query)
  end

  def generate_query_from_files(extracted_text)
    return extracted_text if Rails.env.test?

    input_text = extracted_text.to_s.strip
    if input_text.blank?
      Rails.logger.error "Candidates::SuggestionService: Empty extracted text provided"
      return nil
    end

    prompt = build_query_generation_prompt(input_text)

    Rails.logger.info "Candidates::SuggestionService: Generating search query from extracted text (length: #{input_text.length})"

    begin
      response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um especialista em recrutamento e seleção. Sua função é analisar documentos (currículos, descrições de vagas, perfis) e gerar uma query de busca otimizada para encontrar candidatos similares."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 500,
        tracking: { operation: "candidates.query_from_files" }
      )

      content = response.dig("choices", 0, "message", "content")

      if content.nil?
        Rails.logger.error "Candidates::SuggestionService: LLM returned nil content"
        return parse_query_fallback(input_text)
      end

      query = parse_generated_query(content)
      Rails.logger.info "Candidates::SuggestionService: Generated query: #{query[0, 100]}..."

      query
    rescue => e
      Rails.logger.error "Candidates::SuggestionService: Error generating query - #{e.message}"
      Rails.logger.error "Candidates::SuggestionService: #{e.backtrace.first(3).join('\n')}"
      parse_query_fallback(input_text)
    end
  end

  def generate_query_from_boolean_search(boolean_query)
    return default_boolean_attributes if Rails.env.test?

    input_text = boolean_query.to_s.strip
    if input_text.blank?
      Rails.logger.error "Candidates::SuggestionService: Empty boolean query provided"
      return default_boolean_attributes
    end

    prompt = build_boolean_search_attributes_prompt(input_text)

    begin
      response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um especialista em análise de queries de busca booleana para recrutamento. Sua função é extrair informações estruturadas de queries que usam operadores AND/OR. Você deve retornar APENAS um JSON válido, sem texto adicional."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 500,
        response_format: { type: "json_object" },
        tracking: { operation: "candidates.boolean_search_extraction" }
      )

      content = response.dig("choices", 0, "message", "content")

      if content.nil?
        Rails.logger.error "Candidates::SuggestionService: LLM returned nil content for boolean search"
        return default_boolean_attributes
      end

      attributes = parse_boolean_attributes(content)

      attributes
    rescue => e
      Rails.logger.error "Candidates::SuggestionService: Error extracting attributes from boolean search - #{e.message}"
      Rails.logger.error "Candidates::SuggestionService: #{e.backtrace.first(3).join('\n')}"
      default_boolean_attributes
    end
  end

  def self.suggest_role_names(role_names_text, **opts)
    new(**opts).suggest_role_names(role_names_text)
  end

  def self.generate_query_from_filters(filters, **opts)
    new(**opts).generate_query_from_filters(filters)
  end

  def self.generate_concise_query_from_job(job, **opts)
    new(**opts).generate_concise_query_from_job(job)
  end

  def generate_query_from_filters(filters)
    return "" if Rails.env.test? || filters.blank?

    filters_hash = filters.is_a?(Hash) ? filters : filters.to_h
    if filters_hash.blank?
      Rails.logger.error "Candidates::SuggestionService: Empty filters provided"
      return ""
    end

    prompt = build_filters_to_query_prompt(filters_hash)

    Rails.logger.debug "Candidates::SuggestionService: Generating query from filters"

    begin
      response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um assistente especializado em recrutamento. Sua função é transformar filtros de busca estruturados em uma query de texto natural e fluida em português brasileiro para busca de candidatos."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 500,
        tracking: { operation: "candidates.query_from_filters" }
      )

      content = response.dig("choices", 0, "message", "content")
      query = content ? parse_generated_query(content) : ""

      Rails.logger.info "Candidates::SuggestionService: Generated query: #{query[0, 100]}..."
      query
    rescue => e
      Rails.logger.error "Candidates::SuggestionService: Error generating query from filters - #{e.message}"
      ""
    end
  end

  def suggest_role_names(role_names_text)
    return [] if Rails.env.test? || role_names_text.blank?

    input_text = role_names_text.to_s.strip
    if input_text.blank?
      return []
    end

    prompt = build_role_names_suggestion_prompt(input_text)

    begin
      response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um assistente especializado em recrutamento e cargos profissionais. Sua função é sugerir cargos/funções relevantes baseado em uma lista de role_names fornecida."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.5,
        max_tokens: 500,
        tracking: { operation: "candidates.role_name_suggestions" }
      )

      content = response.dig("choices", 0, "message", "content")
      suggestions = content ? parse_role_names_suggestions(content) : []

      Rails.logger.info "Candidates::SuggestionService: Generated #{suggestions.length} role_name suggestions"
      suggestions
    rescue => e
      Rails.logger.error "Candidates::SuggestionService: Error suggesting role_names - #{e.message}"
      []
    end
  end

  def generate_concise_query_from_job(job)
    return "Busque por candidatos com base nas informações da vaga" if Rails.env.test?

    context = build_job_context(job)
    result = generate_concise_query_for_chip(context)
    result || "Busque por candidatos com base nas informações da vaga"
  end

  def build_job_context(job)
    text_parts = []

    if job.title.present?
      text_parts << "Cargo: #{job.title}"
    end

    if job.description.present?
      text_parts << job.description
    end

    additional_info = []

    if job.skills.any?
      skills_names = job.skills.pluck(:name).compact.join(", ")
      additional_info << "Requer conhecimento em #{skills_names}"
    end

    location_parts = [ job.city, job.state, job.country ].compact
    if location_parts.any?
      additional_info << "Localização: #{location_parts.join(", ")}"
    elsif job.is_remote
      additional_info << "Trabalho remoto"
    end

    if job.seniority.present? && job.seniority.is_a?(Integer) && job.seniority >= 0 && job.seniority < Job::SENIORITY.length
      seniority_text = Job::SENIORITY[job.seniority]
      additional_info << "Nível #{seniority_text}" if seniority_text
    end

    if job.company&.name.present?
      additional_info << "Empresa do setor de #{job.company.name}"
    end

    full_text = text_parts.join(". ")
    full_text += ". #{additional_info.join(". ")}" if additional_info.any?

    full_text.strip
  end

  def generate_concise_query_for_chip(context)
    prompt = build_concise_chip_prompt(context)

    begin
      response = Llm::Gateway.chat(
        messages: [
          {
            role: "system",
            content: "Você é um especialista em recrutamento. Sua função é gerar queries de busca muito concisas e diretas, perfeitas para exibição em chips/badges de interface."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 100,
        tracking: { operation: "candidates.concise_query_for_chip" }
      )

      content = response.dig("choices", 0, "message", "content")
      return nil if content.nil?

      query = parse_concise_query(content)
      query
    rescue => e
      Rails.logger.error "Candidates::SuggestionService: Error generating concise query - #{e.message}"
      nil
    end
  end

  def build_concise_chip_prompt(context)
    <<~PROMPT
      Analise a seguinte descrição de vaga e gere uma query de busca MUITO CONCISA (máximo 15 palavras) para exibição em um chip/badge de interface.

      DESCRIÇÃO DA VAGA:
      #{context}

      REGRAS OBRIGATÓRIAS - LEIA COM ATENÇÃO:
      1. PRESERVE O CARGO COMPLETO EXATAMENTE COMO ESTÁ:#{' '}
         - Se o cargo é "Desenvolvedor React Pleno", a query DEVE começar com "Desenvolvedor React Pleno"
         - Se o cargo é "Analista de Dados", a query DEVE começar com "Analista de Dados"
         - Se o cargo é "Product Manager", a query DEVE começar com "Product Manager"
         - NUNCA remova palavras do cargo como "Desenvolvedor", "Analista", "Engenheiro", "Product Manager", etc.
         - O cargo completo é a parte MAIS IMPORTANTE e DEVE aparecer no início da query

      2. Mantenha o nível de senioridade quando presente (Júnior, Pleno, Sênior) - geralmente já está no cargo

      3. Inclua localização se mencionada

      4. Inclua principais skills (máximo 2-3 tecnologias) se relevantes

      5. Inclua experiência se relevante (ex: "5+ anos", "mínimo 3 anos")

      A query deve ser:
      - Extremamente concisa (10-15 palavras no máximo)
      - Direta ao ponto, sem palavras desnecessárias
      - Formato natural e fluido, como os exemplos abaixo
      - Sem prefixos como "Busque por" ou "Procure"
      - SEMPRE comece com o cargo completo

      Exemplos do formato esperado:
      - "Desenvolvedor Backend Sênior em São Paulo, 5+ anos, Node.js e Python"
      - "Product Manager Pleno remoto, experiência em B2B SaaS, metodologias ágeis"
      - "Desenvolvedor Full Stack, React e Node.js, mínimo 3 anos"
      - "Analista de Dados em São Paulo, Python e SQL, experiência em startups"
      - "Desenvolvedor React Pleno, experiência em aplicações web modernas"

      IMPORTANTE:
      - Retorne APENAS a query, sem explicações, sem formatação markdown, sem aspas
      - SEMPRE preserve o cargo completo - nunca remova palavras como "Desenvolvedor", "Analista", "Engenheiro"
      - O cargo completo DEVE ser a primeira parte da query
      - Seja extremamente conciso - cada palavra deve ser essencial, mas o cargo deve estar completo
      - Priorize: cargo completo + nível + localização + skills principais + experiência
      - Máximo de 15 palavras
    PROMPT
  end

  def parse_concise_query(content)
    query = content.strip
                  .gsub(/^```[\w]*\s*/, "")
                  .gsub(/```\s*$/, "")
                  .gsub(/^["']|["']$/, "")
                  .gsub(/^(query|busca|search):\s*/i, "")
                  .gsub(/^[-*•]\s*/, "")
                  .strip

    query = query.split("\n").first&.strip || query.split(".").first&.strip || query

    query = query[0, 120] if query.length > 120

    query
  end

  private

  def build_prompt(text)
    context_info = []
    context_info << "Localização da empresa: #{@business_city}" if @business_city.present?
    context_info << "Estado da empresa: #{@business_state}" if @business_state.present?

    context_text = context_info.any? ? "\n\nContexto adicional: #{context_info.join(', ')}" : ""

    <<~PROMPT
      Você é um copilot de texto para pesquisa de candidatos. O usuário está digitando uma busca; sua resposta deve ser a FRASE DE BUSCA COMPLETA (não apenas o trecho novo).

      Texto que o usuário já digitou: "#{text}"

      OBJETIVO PRINCIPAL:
      O objetivo é ajudar a preencher os seguintes chips/campos (NÃO sugira setor/área de atuação):
      1. role_name: cargo/função (ex: "Desenvolvedor", "Analista", "Product Manager")
      2. experience_time: tempo de experiência ou senioridade (ex: "5+ anos", "Sênior", "Pleno", "mínimo 3 anos")
      3. location: localização (ex: "São Paulo", "SP", "Brasil", "remoto")
      4. skills: habilidades/tecnologias (ex: "React", "Python", "Java", "Node.js")

      Sua tarefa:
      1. Analise o texto e identifique quais dos 4 campos (role_name, experience_time, location, skills) JÁ ESTÃO PRESENTES e quais FALTAM
      2. Gere UMA ÚNICA linha com a BUSCA COMPLETA: comece com o mesmo texto que o usuário já digitou (preservando palavras e ordem), em seguida acrescente o que faltar para uma busca natural e específica
      3. PRIORIZE preencher os campos que faltam; a frase final deve soar como escrita pelo próprio recrutador
      4. Se todos os campos já estão presentes, acrescente uma melhoria ou especificação adicional ao final da frase completa
      5. NUNCA sugira setor, área de atuação, fintechs, e-commerce, tecnologia como setor, ou similares#{context_text}

      ESTRATÉGIA (aplique no TEXTO COMPLETO, não só no sufixo):
      - Se falta role_name: inclua cargo na frase inteira
      - Se falta experience_time: inclua senioridade ou tempo na frase inteira
      - Se falta location: inclua localização na frase inteira
      - Se falta skills: inclua habilidades/tecnologias na frase inteira
      - NÃO sugira setor/área (fintechs, e-commerce, saúde, etc.)

      Exemplos (resposta = busca COMPLETA, começando pelo que o usuário já escreveu):
      - Usuário: "Desenvolvedor" → "Desenvolvedor Backend com 5+ anos em São Paulo"
      - Usuário: "Desenvolvedor React" → "Desenvolvedor React Sênior em São Paulo, mínimo 3 anos"
      - Usuário: "Desenvolvedor em São Paulo" → "Desenvolvedor em São Paulo Backend com React, 5+ anos de experiência"
      - Usuário: "Quero encontrar candidatos com experiência em" → "Quero encontrar candidatos com experiência em Marketing Digital em São Paulo, mínimo 3 anos"
      - Usuário: "Analista financeiro com" → "Analista financeiro com experiência em Excel"
      - Se o texto já cobre os quatro campos: acrescente algo útil ao final da frase completa (ex.: "com certificações em contas a pagar")

      IMPORTANTE:
      - Retorne APENAS UMA linha de texto, sem formatação, marcadores, aspas ou numeração
      - A linha deve ser a busca inteira, começando pelo prefixo do usuário (ajuste apenas capitalização mínima se necessário para legibilidade)
      - Seja conciso: no máximo cerca de 25 palavras no total
      - NUNCA inclua sugestão de setor (fintechs, tecnologia, e-commerce, saúde, etc.)
    PROMPT
  end

  def build_attributes_prompt(text)
    <<~PROMPT
      Analise o seguinte texto de busca de candidatos e extraia as informações estruturadas.

      Texto: "#{text}"

      Extraia e retorne APENAS um JSON válido com os seguintes campos:

      CAMPOS ESTRUTURAIS (arrays de strings; use [] quando nada for mencionado):
      - role_name: palavras-chave de cargo/função (ex: ["desenvolvedor", "backend"])
      - experience_time: experiência/senioridade (ex: ["+5 anos"], ["sênior"])
      - location: cidades, estados, remoto, presencial, etc.
      - sector: setores/áreas (ex: ["fintech"], ["tecnologia"])
      - skills: tecnologias, linguagens, frameworks (ex: ["python"], ["react"])

      synonym_hint (objeto ou null) — sinônimos e termos relacionados ao contexto da busca (qualquer cargo, skill ou expressão do texto):
      - Se fizer sentido sugerir termos alternativos para ampliar a busca (ex.: tecnologias da stack, títulos de cargo equivalentes, ferramentas do mesmo ecossistema), preencha:
        { "focus_term": "<termo principal do texto a que os sinônimos se referem>", "related_terms": ["<termo1>", "<termo2>", ...] }
      - related_terms: até 6 strings curtas, relevantes ao mercado e ao focus_term (não use listas fixas genéricas; adapte ao que o usuário escreveu).
      - Se não houver sugestão útil ou o texto for só localização/senioridade sem termo para expandir, use null.

      quality_score (inteiro 0 a 100) — use EXATAMENTE a mesma regra da plataforma Python (search-assistant):
      - Existem 5 dimensões, nesta ordem: (1) Cargo = role_name preenchido, (2) Localização = location preenchido,
        (3) Experiência = experience_time preenchido, (4) Habilidades = skills preenchido, (5) Setor = sector preenchido.
      - Uma dimensão "preenchida" se o array correspondente tiver pelo menos um elemento após a extração.
      - quality_score = parte inteira de (número_de_dimensões_preenchidas / 5) * 100.
        Ex.: 3 dimensões preenchidas → 60; 5 dimensões → 100; 0 dimensões → 0.

      next_recommended_action (string) — alinhado ao assistente Python:
      - Se faltar pelo menos uma dimensão, use o PRIMEIRO critério faltante nesta ordem: Cargo, Localização, Experiência, Habilidades, Setor.
        Texto: "Adicione <rótulo em minúsculas> para melhorar os resultados"
        (ex.: falta Experiência → "Adicione experiência para melhorar os resultados"; falta Cargo → "Adicione cargo para melhorar os resultados").
      - Se as 5 dimensões estiverem preenchidas: "Busca bem definida! Pronta para executar".
      - Caso contrário (caso limite): "Continue descrevendo o perfil ideal".

      alerts (array de objetos) — mesmo espírito do analisador Python (search_assistant.analyze_search_quality):
      Cada objeto deve ter: "type" (string), "severity" ("info" | "warning" | "error"), "message" (string),
      e opcionalmente "suggestion" (string), "action_value" (string para acrescentar à busca).
      Regras a aplicar quando fizer sentido:
      1) Se quality_score < 40: inclua um alerta severity "warning", type "broad_search", avisando que a busca pode ser ampla e sugerindo adicionar até 2 dos critérios ainda faltantes.
      2) Se quality_score == 100 e o texto tiver mais de 100 caracteres: um alerta "info", type "restrictive_search", sobre muitos critérios poderem limitar resultados.
      3) Termos ambíguos no texto (ex.: só "dev" sem frontend/backend/mobile; "analista" sem qual tipo; "gerente" sem área): alerta "info", type "ambiguous_term", com pergunta para especificar.
      Não duplique sinônimos em alerts: use o campo synonym_hint para termos relacionados; não inclua alert type "synonym_suggestion" (o sistema deriva isso de synonym_hint).

      IMPORTANTE:
      - Retorne APENAS o JSON, sem markdown, sem texto fora do JSON.
      - quality_score deve ser coerente com a contagem das 5 dimensões (não use faixas subjetivas 80–100; use a fórmula acima).
      - alerts pode ser [] se nenhuma regra se aplicar.

      Exemplo de resposta esperada:
      {
        "role_name": ["desenvolvedor"],
        "experience_time": [],
        "location": [],
        "sector": [],
        "skills": ["python"],
        "synonym_hint": {
          "focus_term": "python",
          "related_terms": ["django", "fastapi", "flask", "pandas"]
        },
        "quality_score": 40,
        "next_recommended_action": "Adicione experiência para melhorar os resultados",
        "alerts": []
      }
    PROMPT
  end

  def parse_suggestion(content, prefix_text = nil)
    # Remove markdown formatting, quotes, and other formatting
    suggestion = content.gsub(/^[-*•]\s*/, "")
                        .gsub(/^\d+[\.\)]\s*/, "")
                        .gsub(/^["']|["']$/, "")
                        .strip

    # Take only the first line if there are multiple lines
    suggestion = suggestion.split("\n").first&.strip || suggestion

    # Remove lines that look like headers/examples
    return nil if suggestion.blank? || suggestion.match?(/^(sugest|exemplo|nota|importante|tarefa)/i)

    # If the model returned only a suffix, prepend the user's prefix (case-insensitive check)
    if prefix_text.present?
      pfx = prefix_text.to_s.strip
      if pfx.length.positive? && !suggestion.downcase.start_with?(pfx.downcase)
        suggestion = "#{pfx} #{suggestion}".gsub(/\s+/, " ").strip
      end
    end

    # Limit length (full-query suggestions need more room than suffix-only)
    suggestion = suggestion[0, 400] if suggestion.length > 400

    suggestion
  end

  def parse_attributes(content)
    json_content = normalize_attributes_json_string(content)
    parsed = try_parse_json_object(json_content)
    parsed ||= try_parse_json_object(repair_truncated_attributes_json(json_content))
    parsed ||= extract_attributes_fallback_from_partial_json(json_content)

    unless parsed.is_a?(Hash)
      Rails.logger.error "Candidates::SuggestionService: Could not parse attributes JSON (content length=#{content.to_s.length})"
      return default_attributes
    end

    build_attributes_result(parsed)
  end

  def normalize_attributes_json_string(content)
    s = content.to_s.strip
    s = s.gsub(/^```json\s*/i, "").gsub(/^```\s*/, "").gsub(/```\s*$/, "").strip
    i = s.index("{")
    s = i ? s[i..] : s
    s
  end

  def try_parse_json_object(json_content)
    JSON.parse(json_content)
  rescue JSON::ParserError
    nil
  end

  # When Gemini hits MAX_TOKENS, JSON often stops mid-object. Close it with required keys.
  def repair_truncated_attributes_json(raw)
    s = raw.to_s.strip
    return s if s.end_with?("}")

    s = s.sub(/,\s*\z/, "")
    s = s.sub(%r{\s+\z}, "")

    return s if s.end_with?("}")

    # Drop an incomplete last property (e.g. `"skills":` with no value)
    s = s.sub(/,\s*"[^"]*"\s*:\s*[^,}\]]*\z/, "")
    s = s.sub(/,\s*\z/, "")

    unless s.end_with?("}")
      s += "," unless s.end_with?("[", "}")
      s << '"skills": [], "synonym_hint": null, "quality_score": 0, "next_recommended_action": null, "alerts": [] }'
    end
    s
  end

  # Last resort: pull array fields with regex (single-line arrays).
  def extract_attributes_fallback_from_partial_json(raw)
    return nil if raw.blank?

    {
      "role_name" => parse_json_array_fragment(raw, "role_name"),
      "experience_time" => parse_json_array_fragment(raw, "experience_time"),
      "location" => parse_json_array_fragment(raw, "location"),
      "sector" => parse_json_array_fragment(raw, "sector"),
      "skills" => parse_json_array_fragment(raw, "skills"),
      "synonym_hint" => nil,
      "quality_score" => 0,
      "next_recommended_action" => nil,
      "alerts" => []
    }
  end

  def parse_json_array_fragment(json, key)
    m = json.match(/"#{Regexp.escape(key)}"\s*:\s*(\[[^\]]*\])/m)
    return [] unless m

    JSON.parse(m[1])
  rescue JSON::ParserError
    []
  end

  # Same rule as lia-agent-system search_assistant.calculate_completeness: 5 dims, score = (filled/5)*100
  def quality_score_from_extracted_arrays(role_name:, experience_time:, location:, sector:, skills:)
    dims = [
      Array(role_name).map(&:to_s).reject(&:blank?).any?,
      Array(location).map(&:to_s).reject(&:blank?).any?,
      Array(experience_time).map(&:to_s).reject(&:blank?).any?,
      Array(skills).map(&:to_s).reject(&:blank?).any?,
      Array(sector).map(&:to_s).reject(&:blank?).any?
    ]
    ((dims.count(true) / 5.0) * 100).to_i
  end

  def next_recommended_action_from_missing(role_name:, experience_time:, location:, sector:, skills:)
    # Order matches Python search_assistant: Cargo, Localização, Experiência, Habilidades, Setor
    checks = [
      [Array(role_name).reject(&:blank?).any?, "cargo"],
      [Array(location).reject(&:blank?).any?, "localização"],
      [Array(experience_time).reject(&:blank?).any?, "experiência"],
      [Array(skills).reject(&:blank?).any?, "habilidades"],
      [Array(sector).reject(&:blank?).any?, "setor"]
    ]
    missing = checks.reject(&:first).map(&:last)
    return "Busca bem definida! Pronta para executar" if missing.empty?

    "Adicione #{missing.first} para melhorar os resultados"
  end

  def build_attributes_result(parsed)
    role_name = Array(parsed["role_name"] || parsed[:role_name]).map(&:to_s)
    experience_time = Array(parsed["experience_time"] || parsed[:experience_time]).map(&:to_s)
    location = Array(parsed["location"] || parsed[:location]).map(&:to_s)
    sector = Array(parsed["sector"] || parsed[:sector]).map(&:to_s)
    skills = Array(parsed["skills"] || parsed[:skills]).map(&:to_s)

    score = quality_score_from_extracted_arrays(
      role_name: role_name,
      experience_time: experience_time,
      location: location,
      sector: sector,
      skills: skills
    )

    next_recommended_action = parsed["next_recommended_action"] || parsed[:next_recommended_action]
    next_recommended_action = next_recommended_action.to_s.strip.presence
    next_recommended_action ||= next_recommended_action_from_missing(
      role_name: role_name,
      experience_time: experience_time,
      location: location,
      sector: sector,
      skills: skills
    )

    synonym_hint = normalize_synonym_hint_hash(parsed["synonym_hint"] || parsed[:synonym_hint])

    alerts = parse_attributes_alerts(parsed["alerts"] || parsed[:alerts])
    alerts = append_synonym_alert_from_hint(alerts, synonym_hint)

    {
      role_name: role_name,
      experience_time: experience_time,
      location: location,
      sector: sector,
      skills: skills,
      synonym_hint: synonym_hint,
      quality_score: score,
      next_recommended_action: next_recommended_action,
      alerts: alerts
    }
  end

  def normalize_synonym_hint_hash(raw)
    return nil if raw.blank?
    return nil unless raw.is_a?(Hash)

    focus = (raw["focus_term"] || raw[:focus_term]).to_s.strip.presence
    related = Array(raw["related_terms"] || raw[:related_terms]).map(&:to_s).map(&:strip).reject(&:blank?)
    return nil if focus.blank? || related.empty?

    { focus_term: focus, related_terms: related.first(6) }
  end

  def append_synonym_alert_from_hint(alerts, synonym_hint)
    return alerts if synonym_hint.blank?
    return alerts if alerts.any? { |a| (a[:type] || a["type"]).to_s == "synonym_suggestion" }

    related = synonym_hint[:related_terms]
    focus = synonym_hint[:focus_term]
    alerts + [
      {
        type: "synonym_suggestion",
        severity: "info",
        message: "Considere também: #{related.first(3).join(", ")}",
        suggestion: "Adicionar sinônimos de '#{focus}'",
        action_value: related.first(2).join(", ")
      }
    ]
  end

  def default_attributes
    {
      role_name: [],
      experience_time: [],
      location: [],
      sector: [],
      skills: [],
      synonym_hint: nil,
      quality_score: 0,
      next_recommended_action: nil,
      alerts: []
    }
  end

  def parse_attributes_alerts(raw)
    return [] unless raw.is_a?(Array)

    raw.filter_map do |a|
      next unless a.is_a?(Hash)

      message = (a["message"] || a[:message]).to_s.strip
      next if message.blank?

      sev = (a["severity"] || a[:severity]).to_s.downcase
      sev = "info" unless %w[info warning error].include?(sev)

      {
        type: (a["type"] || a[:type] || "info").to_s,
        severity: sev,
        message: message,
        suggestion: (a["suggestion"] || a[:suggestion]).presence&.to_s,
        action_label: (a["action_label"] || a[:action_label]).presence&.to_s,
        action_value: (a["action_value"] || a[:action_value]).presence&.to_s
      }.compact
    end
  end

  def build_query_generation_prompt(extracted_text)
    <<~PROMPT
      Analise o seguinte texto extraído de documentos (pode ser um currículo, descrição de vaga, perfil profissional, etc.) e gere uma query de busca otimizada para encontrar candidatos similares.

      TEXTO EXTRAÍDO:
      #{extracted_text}

      Sua tarefa:
      1. Identifique as informações mais relevantes do texto:
         - Cargo/função mencionada
         - Skills e tecnologias
         - Experiência profissional
         - Localização (se mencionada)
         - Setor/área de atuação
         - Nível de senioridade

      2. Gere uma query de busca natural e otimizada que capture o perfil ideal de candidato similar.

      3. A query deve ser:
         - Clara e específica
         - Focada nos aspectos mais relevantes (cargo, skills principais, experiência)
         - Natural, como se um recrutador estivesse descrevendo o perfil
         - Conciso mas completo (máximo 200 palavras)

      4. Se o texto for um currículo, gere uma query que encontre candidatos com perfil similar.
      5. Se o texto for uma descrição de vaga, gere uma query que encontre candidatos que se encaixem no perfil.

      IMPORTANTE:
      - Retorne APENAS a query de busca, sem explicações, sem formatação markdown, sem prefixos como "Query:" ou "Busca:"
      - A query deve ser um texto natural e fluido
      - Foque nos aspectos mais importantes para matching de candidatos
      - Se não conseguir identificar informações relevantes, retorne uma versão resumida e otimizada do texto original

      Exemplo de formato esperado:
      "Desenvolvedor Full Stack com experiência em Ruby on Rails, React e PostgreSQL. Mínimo 3 anos de experiência. Conhecimento em APIs REST, Git e metodologias ágeis."
    PROMPT
  end

  def parse_generated_query(content)
    # Remove markdown formatting, quotes, and prefixes
    query = content.strip
                  .gsub(/^```[\w]*\s*/, "")
                  .gsub(/```\s*$/, "")
                  .gsub(/^["']|["']$/, "")
                  .gsub(/^(query|busca|search):\s*/i, "")
                  .gsub(/^[-*•]\s*/, "")
                  .strip

    # Take only the first paragraph if there are multiple
    query = query.split("\n\n").first&.strip || query.split("\n").first&.strip || query

    # Limit length to reasonable size
    query = query[0, 500] if query.length > 500

    query
  end

  def parse_query_fallback(extracted_text)
    # Fallback: retorna uma versão resumida do texto original
    # Remove quebras de linha excessivas e limpa o texto
    fallback = extracted_text.gsub(/\n{3,}/, "\n\n")
                             .gsub(/[^\S\n]+/, " ")
                             .strip

    # Limita o tamanho
    fallback = fallback[0, 500] if fallback.length > 500

    fallback
  end

  def build_boolean_search_attributes_prompt(boolean_query)
    <<~PROMPT
      Analise a seguinte query de busca booleana para recrutamento e extraia as informações estruturadas.

      QUERY BOOLEANA:
      #{boolean_query}

      A query usa operadores AND/OR para combinar termos. Sua tarefa é identificar e categorizar os termos em:
      - role_name: cargos/funções mencionados (ex: "desenvolvedor backend", "software engineer", "engenheiro de software")
      - skills: tecnologias, linguagens, frameworks, ferramentas (ex: "React", "backend", "API", "REST")
      - experience_time: informações de experiência/tempo (ex: "sênior", "pleno", "+5 anos", "3-5 anos")
      - location: localizações mencionadas (ex: "São Paulo", "SP", "remoto", "Brasil")

      REGRAS DE EXTRAÇÃO:
      1. role_name: Capture todos os termos relacionados a cargos/funções, mesmo que em diferentes idiomas
         - Exemplo: ("desenvolvedor backend" OR "backend developer" OR "software engineer") → ["desenvolvedor backend", "backend developer", "software engineer", "engenheiro de software"]

      2. skills: Capture tecnologias, frameworks, linguagens, ferramentas mencionadas
         - Exemplo: (React OR "React.js") → ["React", "React.js"]
         - Exemplo: (backend OR "back-end") → ["backend", "back-end"]
         - Exemplo: (API OR APIs OR "REST" OR "RESTful") → ["API", "APIs", "REST", "RESTful"]

      3. experience_time: Capture apenas se houver menção explícita a tempo de experiência ou nível
         - Exemplo: "sênior", "pleno", "júnior", "+5 anos", "3-5 anos", "mínimo 3 anos"
         - Se não houver menção, deixe vazio []

      4. location: Capture apenas se houver menção explícita a localização
         - Exemplo: "São Paulo", "SP", "Brasil", "remoto", "presencial"
         - Se não houver menção, deixe vazio []

      IMPORTANTE:
      - Retorne APENAS o JSON, sem texto adicional, sem markdown, sem explicações
      - Todos os campos de array devem ser arrays de strings, mesmo que vazios
      - Mantenha os termos exatamente como aparecem na query (preserve aspas, maiúsculas/minúsculas quando relevante)
      - Se um termo aparece em múltiplos grupos OR, inclua todas as variações
      - Não invente termos que não estão na query
      - Para skills, inclua variações como "React" e "React.js" se ambas aparecem

      Exemplo de resposta esperada para a query:
      ("desenvolvedor backend" OR "backend developer" OR "software engineer" OR "engenheiro de software")
      AND (backend OR "back-end")
      AND (React OR "React.js")
      AND (API OR APIs OR "REST" OR "RESTful")

      {
        "role_name": ["desenvolvedor backend", "backend developer", "software engineer", "engenheiro de software"],
        "skills": ["backend", "back-end", "React", "React.js", "API", "APIs", "REST", "RESTful"],
        "experience_time": [],
        "location": []
      }
    PROMPT
  end

  def parse_boolean_attributes(content)
    json_content = content.strip

    json_content = json_content.gsub(/^```json\s*/, "").gsub(/^```\s*/, "").gsub(/```\s*$/, "").strip

    json_match = json_content.match(/\{[\s\S]*\}/)
    json_content = json_match[0] if json_match

    parsed = JSON.parse(json_content)

    {
      role_name: Array(parsed["role_name"] || parsed[:role_name]).map(&:to_s).compact,
      skills: Array(parsed["skills"] || parsed[:skills]).map(&:to_s).compact,
      experience_time: Array(parsed["experience_time"] || parsed[:experience_time]).map(&:to_s).compact,
      location: Array(parsed["location"] || parsed[:location]).map(&:to_s).compact
    }
  rescue JSON::ParserError => e
    Rails.logger.error "Candidates::SuggestionService: Failed to parse boolean attributes JSON - #{e.message}"
    Rails.logger.error "Candidates::SuggestionService: Content was: #{content[0, 200]}"
    default_boolean_attributes
  end

  def default_boolean_attributes
    {
      role_name: [],
      skills: [],
      experience_time: [],
      location: []
    }
  end

  def build_role_names_suggestion_prompt(role_names_text)
    <<~PROMPT
      Analise a seguinte lista de role_names (cargos/funções) e sugira outros role_names relevantes e relacionados que possam ser úteis para recrutamento.

      LISTA DE ROLE_NAMES FORNECIDA:
      #{role_names_text}

      Sua tarefa:
      1. Identifique o padrão, área ou categoria dos role_names fornecidos
      2. Sugira 5-10 role_names adicionais que sejam:
         - Relacionados à mesma área/categoria
         - Relevantes para recrutamento
         - Variados em níveis de senioridade (quando aplicável)
         - Específicos e profissionais
      3. Considere:
         - Sinônimos e variações comuns
         - Níveis hierárquicos (júnior, pleno, sênior, lead, etc.)
         - Especializações dentro da mesma área
         - Títulos alternativos usados no mercado

      IMPORTANTE:
      - Retorne APENAS uma lista simples de role_names, um por linha
      - Não inclua numeração, marcadores, ou formatação
      - Cada role_name deve estar em uma linha separada
      - Seja específico e profissional
      - Não repita os role_names já fornecidos
      - Máximo de 10 sugestões

      Exemplo de formato esperado:
      Desenvolvedor Backend
      Engenheiro de Software
      Arquiteto de Sistemas
      Tech Lead
      Desenvolvedor Full Stack
    PROMPT
  end

  def parse_role_names_suggestions(content)
    suggestions = content.strip
                         .split("\n")
                         .map(&:strip)
                         .reject(&:blank?)
                         .reject { |s| s.match?(/^(exemplo|importante|tarefa|sua|lista|role|name)/i) }
                         .reject { |s| s.match?(/^[-*•\d\.\)]/) }
                         .map { |s| s.gsub(/^["']|["']$/, "").strip }
                         .compact
                         .uniq
                         .first(10)

    suggestions
  end

  def build_filters_to_query_prompt(filters)
    filters_json = JSON.pretty_generate(filters)

    <<~PROMPT
      Transforme os seguintes filtros de busca de candidatos em uma query de texto natural e fluida em português brasileiro.

      FILTROS:
      #{filters_json}

      Sua tarefa:
      1. Analise todos os filtros fornecidos
      2. Transforme-os em uma query de texto natural que descreva o perfil do candidato procurado
      3. A query deve ser:
         - Natural e fluida, como se um recrutador estivesse descrevendo o perfil
         - Em português brasileiro
         - Específica e clara
         - Incluindo todos os critérios relevantes dos filtros
         - Conciso mas completo (máximo 200 palavras)

      4. Considere os seguintes mapeamentos:
         - experience_years: "com X a Y anos de experiência"
         - current_job_titles: "atualmente como [títulos]"
         - previous_job_titles: "com experiência anterior como [títulos]"
         - job_levels: "nível [níveis]"
         - function_areas: "na área de [áreas]"
         - companies: "que trabalhou/trabalha em [empresas]"
         - company_sectors: "em empresas do setor [setores]"
         - selectedSkills: "com conhecimento em [skills]" (marcar obrigatórias)
         - universities: "formado em [universidades]"
         - study_areas: "em [áreas de estudo]"
         - open_to_opportunities: "aberto a oportunidades"
         - top_universities: "de universidades de destaque"
         - startup_experience: "com experiência em startups"
         - time_in_role: "com X a Y anos no cargo atual"
         - languages_attributes: "com domínio de [idiomas]"

      IMPORTANTE:
      - Retorne APENAS a query de texto, sem explicações, sem formatação markdown, sem prefixos
      - A query deve ser um texto natural e fluido
      - Use conectores naturais como "com", "que", "em", "de", etc.
      - Seja específico e profissional
      - Não inclua filtros que não foram fornecidos

      Exemplo de formato esperado:
      "Busque por desenvolvedor backend com experiência em Ruby on Rails, mínimo 3 anos de experiência, que trabalhou em empresas de tecnologia como Google ou Microsoft, formado em universidades de destaque, com conhecimento em JavaScript e Python, aberto a oportunidades."
    PROMPT
  end
end
