# app/services/business_big_five_service.rb
class BusinessBigFiveService
  def self.call(business:, model: nil)
    new(business: business, model: model).call
  end

  def initialize(business:, model: nil)
    @business = business
  end

  def call
    return { success: false, error: "Business não encontrado" } if @business.nil?

    prompt = build_prompt
    Rails.logger.info "🤖 [BusinessBigFiveService] Enviando prompt para Gemini..."

    response = Llm::Gateway.chat(
      messages: [
        { role: "system", content: system_prompt },
        { role: "user", content: prompt }
      ],
      temperature: 0.3,
      max_tokens: 4096,
      tracking: { operation: "business.big_five_generation" }
    )

    content = response.dig("choices", 0, "message", "content")
    if content.nil?
      Rails.logger.error "❌ [BusinessBigFiveService] Resposta vazia do modelo"
      return { success: false, error: "Resposta vazia do modelo" }
    end

    Rails.logger.info "📥 [BusinessBigFiveService] Resposta recebida (#{content.length} chars)"
    Rails.logger.info "=" * 80
    Rails.logger.info content
    Rails.logger.info "=" * 80

    parsed = parse_response(content)
    unless parsed
      Rails.logger.error "❌ [BusinessBigFiveService] Falha ao processar resposta"
      return { success: false, error: "Falha ao processar resposta" }
    end

    Rails.logger.info "✅ [BusinessBigFiveService] JSON parseado com sucesso"
    update_business(parsed)
    { success: true, data: parsed }
  rescue JSON::ParserError => e
    Rails.logger.error "❌ [BusinessBigFiveService] JSON Parse Error: #{e.message}"
    Rails.logger.error "📄 [BusinessBigFiveService] Conteúdo que falhou:"
    Rails.logger.error "=" * 80
    Rails.logger.error content
    Rails.logger.error "=" * 80
    { success: false, error: "Erro ao processar resposta JSON: #{e.message}" }
  rescue => e
    Rails.logger.error "❌ [BusinessBigFiveService] Error: #{e.message}"
    Rails.logger.error e.backtrace.first(10).join("\n")
    { success: false, error: e.message }
  end

  private

  def system_prompt
    <<~PROMPT
      Você é um Especialista em Psicologia Organizacional com profundo conhecimento do modelo Big Five (OCEAN) aplicado a culturas corporativas.
    PROMPT
  end

  def build_prompt
    company_data = build_company_data

    <<~PROMPT
      Analise a empresa e gere perfil Big Five organizacional (escala 0-100 por dimensão).

      Score guide:
      OPENNESS: 70-100=inovadora/startup, 40-70=equilibrio, 0-40=tradicional
      CONSCIENTIOUSNESS: 70-100=processos rigorosos, 40-70=estruturado+flex, 0-40=informal/ágil
      EXTRAVERSION: 70-100=colab intensa/eventos, 40-70=equilibrio, 0-40=individual/deep work
      AGREEABLENESS: 70-100=foco pessoas/DEI, 40-70=equilibrio, 0-40=competitivo/resultados
      STABILITY: 70-100=calmo/estável/WLB, 40-70=estável, 0-40=pressão/caos

      Empresa:
      Website: #{company_data[:website_content]}
      LinkedIn: #{company_data[:linkedin_data]}
      Setor: #{company_data[:industry]} | Tamanho: #{company_data[:company_size]}
      Missão: #{company_data[:mission]}
      Valores: #{company_data[:values]}

      Responda APENAS JSON válido (sem markdown/code blocks). Formato:
      {"big_five":{"openness":75,"conscientiousness":60,"extraversion":70,"agreeableness":65,"stability":55},"reasoning":{"openness":"justificativa","conscientiousness":"justificativa","extraversion":"justificativa","agreeableness":"justificativa","stability":"justificativa"},"culture_summary":"resumo 2-3 frases","confidence":0.85}
    PROMPT
  end

  def build_company_data
    {
      website_content: @business.about.presence || @business.website.presence || "Não disponível",
      linkedin_data: @business.linkedin.presence || "Não disponível",
      industry: @business.industry.presence || "Não especificado",
      company_size: @business.size.presence || "Não especificado",
      mission: @business.mission.presence || "Não disponível",
      values: @business.culture_values.present? ? @business.culture_values.join(", ") : "Não disponível"
    }
  end

  def parse_response(content)
    Rails.logger.info "🔧 [BusinessBigFiveService] Iniciando parsing do JSON..."

    json_content = content.strip
                          .gsub(/^```json\s*\n?/i, "")
                          .gsub(/^```\s*\n?/, "")
                          .gsub(/\n?```\s*$/i, "")
                          .strip

    json_match = json_content.match(/\{[\s\S]*\}/m)
    if json_match
      json_content = json_match[0]
      Rails.logger.info "✅ [BusinessBigFiveService] JSON extraído do conteúdo"
    else
      Rails.logger.warn "⚠️  [BusinessBigFiveService] Nenhum padrão JSON encontrado, tentando usar conteúdo completo"
    end

    Rails.logger.info "📏 [BusinessBigFiveService] Conteúdo JSON final (#{json_content.length} chars)"
    Rails.logger.info "📄 Primeiros 500 chars: #{json_content[0..499]}"

    begin
      parsed = JSON.parse(json_content, symbolize_names: true)
    rescue JSON::ParserError => e
      Rails.logger.warn "⚠️  [BusinessBigFiveService] JSON parse falhou, tentando reparar..."
      json_content = repair_incomplete_json(json_content)
      parsed = JSON.parse(json_content, symbolize_names: true)
    end

    unless parsed.is_a?(Hash) && parsed[:big_five].is_a?(Hash)
      Rails.logger.error "❌ [BusinessBigFiveService] Estrutura JSON inválida. Esperado: { big_five: { ... } }"
      return nil
    end

    parsed
  rescue JSON::ParserError => e
    Rails.logger.error "❌ [BusinessBigFiveService] Erro ao fazer parse do JSON após reparação"
    Rails.logger.error "Erro: #{e.message}"
    Rails.logger.error "Conteúdo original:"
    Rails.logger.error "=" * 80
    Rails.logger.error content
    Rails.logger.error "=" * 80
    raise
  end

  def repair_incomplete_json(json_str)
    Rails.logger.info "🔧 [BusinessBigFiveService] Tentando reparar JSON incompleto..."

    original = json_str.dup

    json_str = json_str.rstrip

    json_str = json_str.chomp(",") if json_str.end_with?(",")

    if json_str.match(/[^\\]["']\s*$/) || json_str.end_with?(': "') || json_str.end_with?(": '")
      json_str = json_str.sub(/:\s*["']?[^"]*$/, ': ""')
    end

    open_braces = json_str.count("{")
    close_braces = json_str.count("}")
    open_brackets = json_str.count("[")
    close_brackets = json_str.count("]")

    (open_brackets - close_brackets).times do
      if json_str.rstrip.end_with?(",")
        json_str = json_str.rstrip.chomp(",")
      end
      json_str += "]"
    end

    missing_braces = open_braces - close_braces

    if json_str.include?('"big_five"') && !json_str.match(/"big_five"\s*:\s*\{[\s\S]*\}/)
      if !json_str.include?('"openness"')
        json_str = json_str.sub(/"big_five"\s*:\s*\{/, '"big_five": {"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "stability": 50')
      end
    end

    missing_braces.times do
      if json_str.rstrip.end_with?(",")
        json_str = json_str.rstrip.chomp(",")
      end
      json_str += "\n}"
    end

    Rails.logger.info "✅ [BusinessBigFiveService] JSON reparado (original: #{original.length} chars, reparado: #{json_str.length} chars)"
    json_str
  end

  def update_business(parsed)
    big_five = parsed[:big_five]
    return unless big_five

    @business.update(
      openness: big_five[:openness],
      conscientiousness: big_five[:conscientiousness],
      extraversion: big_five[:extraversion],
      agreeableness: big_five[:agreeableness],
      stability: big_five[:stability]
    )
  end
end
