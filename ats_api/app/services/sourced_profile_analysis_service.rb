class SourcedProfileAnalysisService
  CACHE_TTL = 24.hours
  CACHE_KEY = "sp_analysis:%<id>d"
  MODEL_HINT = "claude-sonnet-4-5"

  def initialize(sourced_profile:, force_refresh: false, account: nil)
    @sourced_profile = sourced_profile
    @force_refresh = force_refresh
    @account = account || sourced_profile.account
  end

  def call
    key = format(CACHE_KEY, id: @sourced_profile.id)
    Rails.cache.delete(key) if @force_refresh
    Rails.cache.fetch(key, expires_in: CACHE_TTL) { invoke_llm }
  end

  private

  def invoke_llm
    response = Llm::Gateway.chat(
      messages: build_messages,
      temperature: 0.2,
      max_tokens: 800,
      response_format: { type: "json_object" },
      tracking: { operation: "sourced_profile_analysis" },
      account: @account
    )
    parse_response(response)
  end

  def build_messages
    [
      { role: "system", content: system_prompt },
      { role: "user", content: user_prompt }
    ]
  end

  def system_prompt
    <<~PROMPT
      Você é um recrutador sênior. Analise o perfil enviado e retorne APENAS JSON válido
      no formato:
      {
        "summary": "string curta em pt-BR",
        "skills_analysis": {"strong": [], "moderate": [], "gaps": []},
        "fit_score": 0.0,
        "strengths": [],
        "concerns": []
      }
      Não inclua texto fora do JSON.
    PROMPT
  end

  def user_prompt
    sp = @sourced_profile
    skills = Array(sp.try(:skills_list) || sp.try(:skills) || []).join(", ")
    <<~PROMPT
      Nome: #{sp.try(:name)}
      Headline: #{sp.try(:headline)}
      Skills: #{skills}
      Empresa atual: #{sp.try(:current_company)}
      Experiência: #{sp.try(:experiences_summary) || sp.try(:summary)}
    PROMPT
  end

  def parse_response(response)
    raw = extract_content(response)
    json = raw.is_a?(Hash) ? raw : JSON.parse(raw, symbolize_names: true)
    {
      summary: json[:summary].to_s,
      skills_analysis: json[:skills_analysis] || { strong: [], moderate: [], gaps: [] },
      fit_score: json[:fit_score].to_f,
      strengths: json[:strengths] || [],
      concerns: json[:concerns] || []
    }
  rescue JSON::ParserError
    { summary: "", skills_analysis: { strong: [], moderate: [], gaps: [] }, fit_score: 0.0, strengths: [], concerns: [] }
  end

  def extract_content(response)
    return response if response.is_a?(Hash) || response.is_a?(String)
    response.respond_to?(:content) ? response.content : response.to_s
  end
end
