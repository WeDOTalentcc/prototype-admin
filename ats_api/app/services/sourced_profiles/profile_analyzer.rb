module SourcedProfiles
  class ProfileAnalyzer
    MATCH_LEVELS = %w[exceeds meets partial missing].freeze
    MATCH_POINTS = { "exceeds" => 95, "meets" => 75, "partial" => 40, "missing" => 0 }.freeze
    PRIORITIES = %w[essential important nice_to_have].freeze
    PRIORITY_MULTIPLIERS = { "essential" => 3, "important" => 2, "nice_to_have" => 1 }.freeze
    SEVERITIES = %w[low medium high].freeze
    MAX_SCORE = 99

    RED_FLAG_TYPES = %w[
      inconsistent_dates
      misrepresentation
      skill_mismatch
    ].freeze

    NEUTRAL_FLAGS = %w[
      gap_in_employment
      short_tenure
      job_hopping
      career_downgrade
      career_change
      overqualified
      underqualified
    ].freeze

    HIGHLIGHT_TYPES = %w[
      career_progression
      international_exposure
      industry_match
      technical_depth
      leadership
      education
      notable_company
      entrepreneurial
      certifications
    ].freeze

    DEVELOPMENT_AREA_TYPES = %w[
      skill_gap
      experience_gap
      seniority_gap
      industry_gap
      certification_gap
      depth_gap
    ].freeze

    def initialize(logger: Rails.logger)
      @logger = logger
    end

    def call(profile:, query:, sourcing: nil, requirements: nil)
      text = normalized_text(profile)
      if text.blank?
        @logger.warn "[ProfileAnalyzer] skip profile_id=#{profile.id} reason=curriculum_vazio"
        return skipped("curriculum vazio")
      end
      if query.blank?
        @logger.warn "[ProfileAnalyzer] skip profile_id=#{profile.id} reason=query_vazia (sourcing_id=#{sourcing&.id})"
        return skipped("query vazia")
      end

      profile_quality = assess_profile_quality(text)

      cached = fetch_cached_result(query, text)
      return cached if cached

      attempt = 0
      max_json_retries = 2
      max_tokens_for_attempt = [ 8192, 12_288 ]

      rate_retries = 0
      max_rate_retries = 6

      begin
        attempt += 1

        system_msg = system_prompt
        user_msg = user_prompt(query, text, requirements, profile_quality)
        max_out = max_tokens_for_attempt[[attempt - 1, max_tokens_for_attempt.size - 1].min]

        @logger.info "=" * 100
        @logger.info "🤖 [ProfileAnalyzer] PROMPT ENVIADO PARA GEMINI"
        @logger.info "=" * 100
        @logger.info "SYSTEM: #{system_msg[0..500]}..."
        @logger.info "-" * 100
        @logger.info "USER: #{user_msg[0..1000]}#{'...' if user_msg.length > 1000}"
        @logger.info "-" * 100
        @logger.info "Requirements: #{requirements.to_json}"
        @logger.info "Profile Quality: #{profile_quality.to_json}"
        @logger.info "max_output_tokens: #{max_out} (attempt #{attempt})"
        @logger.info "=" * 100

        response = Llm::Gateway.chat(
          messages: [
            { role: "system", content: system_msg },
            { role: "user", content: user_msg }
          ],
          temperature: 0.1,
          max_tokens: max_out,
          response_format: { type: "json_object" },
          tracking: { operation: "sourcing.profile_analysis" }
        )

        raw_content = response.dig("choices", 0, "message", "content")
        finish = response.dig("choices", 0, "finish_reason")

        @logger.info "[ProfileAnalyzer] gemini_response bytes=#{raw_content.to_s.bytesize} finish_reason=#{finish.inspect}"

        parsed = parse_response(response)

        @logger.info "=" * 100
        @logger.info "📊 [ProfileAnalyzer] RESPOSTA PARSEADA"
        @logger.info "=" * 100
        @logger.info JSON.pretty_generate(parsed)
        @logger.info "=" * 100
        return skipped("resposta vazia do modelo") if parsed.nil?

        usage = response.dig("usage") || {}
        cost = calculate_cost(usage)

        final_score = parsed[:calculated_score] || calculate_rubric_score(parsed[:evaluation], requirements)

        result = {
          status: :ok,
          score: final_score,
          insights: build_insights(parsed, query, sourcing, profile, profile_quality, final_score),
          metadata: build_metadata(parsed, sourcing, usage, cost, profile_quality)
        }

        store_cached_result(query, text, result)

        @logger.info "=" * 100
        @logger.info "💾 [ProfileAnalyzer] RESULTADO FINAL (será salvo no SourcedProfileSourcing)"
        @logger.info "=" * 100
        @logger.info "Score Final: #{result[:score]}"
        @logger.info "Profile Quality: #{profile_quality[:completeness].round(2)} (#{profile_quality[:confidence]})"
        @logger.info "Insights: #{JSON.pretty_generate(result[:insights])}"
        @logger.info "Metadata: #{JSON.pretty_generate(result[:metadata])}"
        @logger.info "=" * 100

        result
      rescue Llm::RateLimitExceeded => e
        rate_retries += 1
        if rate_retries <= max_rate_retries
          wait = (2**rate_retries * 0.4) + rand * 2.0
          @logger.warn "[SourcedProfiles::ProfileAnalyzer] rate limit (#{e.limit_type}), retry #{rate_retries}/#{max_rate_retries} in #{wait.round(2)}s"
          sleep(wait)
          attempt = 0
          retry
        end
        @logger.error "❌ [SourcedProfiles::ProfileAnalyzer] Error: #{e.message}"
        { status: :error, error: e.message }
      rescue JSON::ParserError => e
        if attempt < max_json_retries
          @logger.warn "⚠️  [SourcedProfiles::ProfileAnalyzer] JSON parse failed, retrying (#{attempt}/#{max_json_retries})"
          sleep(0.5 * attempt)
          retry
        end
        @logger.error "❌ [SourcedProfiles::ProfileAnalyzer] JSON parse error: #{e.message}"
        { status: :error, error: "Resposta inválida do modelo" }
      rescue => e
        @logger.error "❌ [SourcedProfiles::ProfileAnalyzer] Error: #{e.message}"
        { status: :error, error: e.message }
      end
    end

    private

    attr_reader :logger

    def normalized_text(profile)
      text = profile.curriculum_text.presence

      if text.nil? || text.strip.empty?
        text = profile.candidate&.curriculum_text.presence
      end

      return nil if text.blank?
      text.to_s.strip.first(15_000)
    end

    def system_prompt
      <<~PROMPT
        Você é um recrutador técnico especialista em avaliação objetiva de candidatos.
        Use metodologia de rubrica (exceeds/meets/partial/missing) para cada requisito.
        Cite evidências específicas do currículo para justificar cada avaliação.
        IMPORTANTE: Retorne APENAS JSON válido e completo. Não interrompa o JSON no meio.
        Seja direto, preciso e em português do Brasil.

        ## REGRA CRÍTICA: TEXTOS COMPLETOS
        NUNCA trunce textos com "..." ou "…". Todos os campos de texto devem conter frases COMPLETAS.
        Se um texto for longo, RESUMA ou PARAFRASEIE em vez de truncar.

        ## DIRETRIZES ANTI-VIÉS (OBRIGATÓRIO)
        Avalie APENAS competências técnicas demonstradas. NÃO use como proxy de qualidade:
        - Nome/prestígio de empresas anteriores
        - Nome/ranking de universidades
        - Qualidade de escrita ou gramática do currículo
        - Gaps de emprego (podem ter razões legítimas: saúde, família, estudo, empreendedorismo)
        - Tempo curto em empresas (pode indicar contratos, projetos, layoffs)
        - Localização geográfica ou idioma nativo
        - Idade inferida por datas

        Foque em: skills demonstradas, projetos realizados, resultados mensuráveis, stack técnica.
      PROMPT
    end

    def user_prompt(query, text, requirements, profile_quality)
      requirements_text = if requirements.present?
        requirements.map { |r| "- #{r[:text]} (prioridade: #{r[:priority]}, peso: #{r[:weight]})" }.join("\n")
      else
        "Inferir da query"
      end

      <<~PROMPT
        # CONTEXTO DA BUSCA
        #{query}

        # REQUISITOS ESTRUTURADOS
        #{requirements_text}

        # CURRÍCULO DO CANDIDATO
        #{text}

        # QUALIDADE DO PERFIL
        Completude: #{profile_quality[:completeness].round(2)} (#{profile_quality[:word_count]} palavras)
        Seções faltantes: #{profile_quality[:missing].join(', ').presence || 'nenhuma'}

        # METODOLOGIA DE AVALIAÇÃO
        Para cada requisito, avalie usando esta rubrica:

        **MATCH_LEVELS:**
        - "exceeds" (95 pts): Supera claramente o requisito com múltiplas evidências fortes
        - "meets" (75 pts): Atende completamente o requisito com evidência clara
        - "partial" (40 pts): Atende parcialmente, evidência fraca ou incompleta
        - "missing" (0 pts): Não encontrado ou não atende

        **CONFIDENCE:**
        - "high": Evidência clara e específica no currículo
        - "medium": Evidência inferida ou parcial
        - "low": Sem evidência clara, baseado em suposição

        # CÁLCULO DO SCORE
        Score = Σ(peso_requisito × pontos_match_level) / Σ(peso_requisito × 95) × 100

        **Score máximo: 99 pontos** (perfeição absoluta não existe)

        Onde:
        - Requisitos "essential": peso 30 (ou 3x)
        - Requisitos "important": peso 20 (ou 2x)
        - Requisitos "nice_to_have": peso 10 (ou 1x)

        # FORMATO DE RESPOSTA
        {
          "evaluation": [
            {
              "requirement": "<requisito em português>",
              "priority": "essential|important|nice_to_have",
              "evidence": ["<citação direta do currículo>", "<outra citação>"],
              "match_level": "exceeds|meets|partial|missing",
              "points": 95,
              "confidence": "high|medium|low",
              "rationale": "<justificativa breve em até 80 caracteres>"
            }
          ],
          "calculated_score": 78,
          "score_confidence": "high|medium|low",
          "confidence_factors": {
            "profile_completeness": #{profile_quality[:completeness].round(2)},
            "evidence_density": 0.8,
            "ambiguity_level": 0.2
          },
          "one_liner": "<resumo do fit em até 100 caracteres>",
          "red_flags": [
            {"type": "inconsistent_dates|misrepresentation|skill_mismatch", "description": "<apenas inconsistências factuais>", "severity": "low|medium|high"}
          ],
          "neutral_observations": [
            {"type": "gap_in_employment|career_change|short_tenure", "description": "<observação neutra, sem julgamento>"}
          ],
          "development_areas": [
            {"type": "skill_gap|experience_gap|seniority_gap|industry_gap|certification_gap|depth_gap", "description": "<área onde o candidato pode melhorar em relação à busca>", "requirement": "<requisito relacionado>"}
          ],
          "highlights": [
            {"type": "career_progression|technical_depth|leadership", "description": "<destaque>"}
          ],
          "skills_assessment": {
            "strong": ["skill1", "skill2"],
            "mentioned": ["skill3"],
            "missing_from_search": ["skill4"]
          },
          "suggested_questions": ["pergunta1 curta", "pergunta2 curta", "pergunta3 curta"]
        }

        REGRAS IMPORTANTES:
        - Máximo 8 itens em "evaluation" (principais requisitos)
        - Máximo 2 evidências por requisito (cite trechos específicos, mas CURTOS - máx 150 caracteres cada)
        - Máximo 3 red_flags (APENAS para inconsistências factuais, NÃO para gaps ou job hopping)
        - **OBRIGATÓRIO 1-3 development_areas**: Identifique gaps do candidato em relação à busca. Baseie-se nos requisitos com match_level "partial" ou "missing". Todo candidato tem áreas para desenvolver.
        - Máximo 3 highlights
        - Seja específico nas evidências (nomes de empresas, tecnologias, anos), mas CONCISO

        ## REGRAS DE TEXTO COMPLETO E CONCISÃO (CRÍTICO)
        - NUNCA use "..." para truncar textos. Todos os textos devem ser COMPLETOS.
        - Seja CONCISO e DIRETO. Evite textos longos que podem estourar o limite de tokens.
        - Cada "evidence" deve ser uma citação COMPLETA (máx 150 caracteres). Se for maior, parafraseie.
        - Cada "description" deve ser uma frase COMPLETA (máx 200 caracteres). Se precisar encurtar, reescreva.
        - Cada "rationale" deve ser uma justificativa COMPLETA (máx 200 caracteres).
        - Cada "one_liner" deve ser um resumo COMPLETO (máx 150 caracteres).
        - Cada "suggested_questions" deve ser uma pergunta COMPLETA (máx 200 caracteres).
        - PROIBIDO: textos terminando em "...", "…" ou qualquer forma de truncamento.
        - Se precisar ser conciso, REFORMULE o texto em vez de cortá-lo.
        - Priorize QUALIDADE sobre QUANTIDADE. Menos texto, mais valor.
        - Se o perfil for incompleto, ajuste score_confidence para "medium" ou "low"
        - JSON DEVE ESTAR COMPLETO E VÁLIDO
        - Responda APENAS o JSON, sem markdown ou explicações

        ## REGRAS ANTI-VIÉS (CRÍTICO)
        - Gap de emprego NÃO reduz match_level de nenhum requisito
        - Tempo curto em empresa NÃO é evidência negativa
        - Universidade/empresa de origem NÃO define qualidade técnica
        - Avalie o que a pessoa SABE FAZER, não onde ela estudou/trabalhou
        - Na dúvida sobre uma skill, use "partial" com confidence "low", não "missing"
      PROMPT
    end

    def parse_response(response)
      content = response.dig("choices", 0, "message", "content")
      finish = response.dig("choices", 0, "finish_reason").to_s
      return nil unless content.present?

      cleaned = content.strip
                      .gsub(/^```json\s*\n?/, "")
                      .gsub(/^```\s*\n?/, "")
                      .gsub(/\n?```$/, "")
                      .strip

      return nil if cleaned.blank?

      begin
        data = JSON.parse(cleaned, symbolize_names: true)
        sanitize_payload(data)
      rescue JSON::ParserError => e
        @logger.error "❌ [SourcedProfiles::ProfileAnalyzer] Failed to parse JSON response (finish_reason=#{finish})"
        @logger.error "Raw content (head): #{content[0..400]}"
        @logger.error "Cleaned content (head): #{cleaned[0..400]}"
        raise e
      end
    end

    def sanitize_payload(data)
      # Suporte para formato novo (evaluation) e legado (query_insights)
      evaluation = data[:evaluation] || convert_legacy_insights(data[:query_insights])
      sanitized_evaluation = sanitize_evaluation(evaluation)

      # Calcular score auditável a partir dos insights em vez de confiar no Gemini
      calculated_score = calculate_score_from_evaluation(sanitized_evaluation)

      {
        score: calculated_score,
        calculated_score: calculated_score,
        score_confidence: data[:score_confidence]&.to_s&.presence || "medium",
        confidence_factors: data[:confidence_factors] || {},
        evaluation: sanitized_evaluation,
        one_liner: data[:one_liner].to_s.truncate(150, omission: ""),
        query_insights: convert_evaluation_to_insights(sanitized_evaluation), # Legacy compatibility
        red_flags: sanitize_red_flags(data[:red_flags]),
        neutral_observations: sanitize_neutral_observations(data[:neutral_observations] || extract_neutral_from_red_flags(data[:red_flags])),
        development_areas: sanitize_development_areas(data[:development_areas], sanitized_evaluation),
        highlights: sanitize_highlights(data[:highlights]),
        skills_assessment: sanitize_skills(data[:skills_assessment]),
        suggested_questions: Array(data[:suggested_questions]).compact_blank.first(3).map { |q| q.to_s.truncate(200, omission: "") }
      }
    end

    def calculate_score_from_evaluation(evaluation)
      return 0 if evaluation.blank?

      total_points = 0
      total_max = 0

      evaluation.each do |eval|
        match_points = MATCH_POINTS[eval[:match_level]] || 0
        priority_multiplier = PRIORITY_MULTIPLIERS[eval[:priority]] || 1

        total_points += match_points * priority_multiplier
        total_max += 95 * priority_multiplier
      end

      return 0 if total_max.zero?

      score = ((total_points.to_f / total_max) * 100).round
      [ score, MAX_SCORE ].min
    end

    def convert_legacy_insights(insights)
      return [] unless insights

      Array(insights).map do |insight|
        {
          requirement: insight[:requirement] || insight[:subquery],
          priority: insight[:priority] || "important",
          evidence: insight[:evidence] || insight[:short_quotes] || [],
          match_level: insight[:match_level] || "partial",
          confidence: "medium",
          rationale: insight[:rationale] || insight[:short_rationale] || ""
        }
      end
    end

    def sanitize_evaluation(items)
      Array(items).first(8).map do |eval|
        match_level = MATCH_LEVELS.include?(eval[:match_level]) ? eval[:match_level] : "partial"
        points = MATCH_POINTS[match_level]

        {
          requirement: eval[:requirement].to_s.truncate(200, omission: ""),
          priority: PRIORITIES.include?(eval[:priority]) ? eval[:priority] : "important",
          evidence: Array(eval[:evidence]).compact_blank.first(2).map { |e| e.to_s.truncate(150, omission: "") },
          match_level: match_level,
          points: points,
          confidence: %w[high medium low].include?(eval[:confidence]) ? eval[:confidence] : "medium",
          rationale: eval[:rationale].to_s.truncate(200, omission: "")
        }
      end
    end

    def convert_evaluation_to_insights(evaluation)
      Array(evaluation).map do |eval|
        {
          requirement: eval[:requirement],
          priority: eval[:priority],
          match_level: eval[:match_level],
          short_rationale: eval[:rationale],
          short_quotes: eval[:evidence]
        }
      end
    end

    def sanitize_query_insights(items)
      # Mantido para compatibilidade legado
      Array(items).first(5).map do |insight|
        requirement = insight[:requirement] || insight[:subquery]
        {
          requirement: requirement.to_s.truncate(150, omission: ""),
          priority: PRIORITIES.include?(insight[:priority]) ? insight[:priority] : "important",
          match_level: MATCH_LEVELS.include?(insight[:match_level]) ? insight[:match_level] : "partial",
          rationale: insight[:rationale].to_s.truncate(200, omission: ""),
          evidence: Array(insight[:evidence]).compact_blank.first(2).map { |e| e.to_s.truncate(120, omission: "") }
        }
      end
    end

    def sanitize_red_flags(items)
      Array(items).first(3).filter_map do |flag|
        flag_type = flag[:type].to_s
        next if NEUTRAL_FLAGS.include?(flag_type)
        {
          type: RED_FLAG_TYPES.include?(flag_type) ? flag_type : "skill_mismatch",
          description: flag[:description].to_s.truncate(200, omission: ""),
          severity: SEVERITIES.include?(flag[:severity]) ? flag[:severity] : "low"
        }
      end
    end

    def sanitize_neutral_observations(items)
      Array(items).first(3).map do |obs|
        {
          type: NEUTRAL_FLAGS.include?(obs[:type].to_s) ? obs[:type].to_s : "career_change",
          description: obs[:description].to_s.truncate(200, omission: "")
        }
      end
    end

    def sanitize_highlights(items)
      Array(items).first(3).map do |highlight|
        {
          type: HIGHLIGHT_TYPES.include?(highlight[:type]) ? highlight[:type] : "technical_depth",
          description: highlight[:description].to_s.truncate(200, omission: "")
        }
      end
    end

    def sanitize_development_areas(items, evaluation)
      sanitized = Array(items).first(3).map do |area|
        {
          type: DEVELOPMENT_AREA_TYPES.include?(area[:type].to_s) ? area[:type].to_s : "skill_gap",
          description: area[:description].to_s.truncate(200, omission: ""),
          requirement: area[:requirement].to_s.truncate(150, omission: "")
        }
      end

      # Se a IA não retornou development_areas, inferir dos requisitos partial/missing
      if sanitized.empty? && evaluation.present?
        sanitized = infer_development_areas_from_evaluation(evaluation)
      end

      # Garantir pelo menos 1 item se score < 99
      if sanitized.empty?
        sanitized = [ { type: "depth_gap", description: "Perfil precisa de validação mais profunda em entrevista", requirement: "" } ]
      end

      sanitized
    end

    def infer_development_areas_from_evaluation(evaluation)
      weak_requirements = evaluation.select { |e| %w[partial missing].include?(e[:match_level]) }

      weak_requirements.first(3).map do |eval|
        type = case eval[:match_level]
        when "missing" then "skill_gap"
        when "partial" then "depth_gap"
        else "experience_gap"
        end

        {
          type: type,
          description: "#{eval[:requirement]}: #{eval[:rationale]}".truncate(200, omission: ""),
          requirement: eval[:requirement].to_s.truncate(150, omission: "")
        }
      end
    end

    def sanitize_skills(skills)
      {
        strong: Array(skills&.dig(:strong)).compact_blank.first(10),
        mentioned: Array(skills&.dig(:mentioned)).compact_blank.first(10),
        missing_from_search: Array(skills&.dig(:missing_from_search)).compact_blank.first(5)
      }
    end

    def extract_neutral_from_red_flags(red_flags)
      Array(red_flags).filter_map do |flag|
        flag_type = flag[:type].to_s
        next unless NEUTRAL_FLAGS.include?(flag_type)
        { type: flag_type, description: flag[:description].to_s }
      end
    end

    def build_insights(parsed, query, sourcing, profile, profile_quality, calculated_score)
      {
        "one_liner" => parsed[:one_liner],
        "score_confidence" => parsed[:score_confidence],
        "confidence_factors" => parsed[:confidence_factors].merge(
          "profile_completeness" => profile_quality[:completeness].round(2),
          "profile_word_count" => profile_quality[:word_count]
        ),
        "evaluation" => parsed[:evaluation].map do |eval|
          {
            "requirement" => eval[:requirement],
            "priority" => eval[:priority],
            "match_level" => eval[:match_level],
            "points" => eval[:points],
            "confidence" => eval[:confidence],
            "rationale" => eval[:rationale],
            "evidence" => eval[:evidence]
          }
        end,
        "query_insights" => parsed[:query_insights].map do |insight|
          {
            "subquery" => insight[:requirement],
            "priority" => insight[:priority],
            "match_level" => insight[:match_level],
            "short_rationale" => insight[:short_rationale],
            "short_quotes" => insight[:short_quotes]
          }
        end,
        "red_flags" => parsed[:red_flags],
        "neutral_observations" => parsed[:neutral_observations],
        "development_areas" => parsed[:development_areas],
        "highlights" => parsed[:highlights],
        "skills_assessment" => parsed[:skills_assessment],
        "suggested_questions" => parsed[:suggested_questions],
        "scoring_method" => "rubric_based",
        "calculated_score" => calculated_score,
        "sourcing_id" => sourcing&.id || profile&.sourcing_id,
        "sourcing_query" => query,
        "ai_source" => "gemini",
        "generated_at" => Time.current
      }
    end

    def build_metadata(parsed, sourcing, usage = {}, cost = 0.0, profile_quality = {})
      {
        "ai_source" => "gemini",
        "model" => analysis_model,
        "sourcing_id" => sourcing&.id,
        "ran_at" => Time.current,
        "prompt_tokens" => usage["prompt_tokens"],
        "completion_tokens" => usage["completion_tokens"],
        "total_tokens" => usage["total_tokens"],
        "cost_usd" => cost.round(6),
        "profile_quality" => profile_quality,
        "score_confidence" => parsed[:score_confidence],
        "scoring_method" => "rubric_based"
      }
    end

    def calculate_rubric_score(evaluation, requirements)
      return 0 if evaluation.blank?

      total_weighted_points = 0.0
      total_max_points = 0.0

      evaluation.each do |eval|
        priority = eval[:priority] || "important"
        match_level = eval[:match_level] || "partial"

        multiplier = PRIORITY_MULTIPLIERS[priority] || 2
        points = MATCH_POINTS[match_level] || 40

        total_weighted_points += (points * multiplier)
        total_max_points += (95 * multiplier)
      end

      return 0 if total_max_points.zero?

      score = ((total_weighted_points / total_max_points) * 100).round
      [ score, MAX_SCORE ].min
    end

    def assess_profile_quality(text)
      sections = {
        contact: text.match?(/email|telefone|phone|linkedin|contato/i),
        experience: text.match?(/experiência|experience|trabalhou|worked|empresa|company/i),
        education: text.match?(/formação|education|graduação|universidade|university|curso/i),
        skills: text.match?(/competências|skills|tecnologias|conhecimento|habilidades/i),
        dates: text.scan(/\d{2}\/\d{4}|\d{4}/).count >= 2
      }

      completeness = sections.values.count(true) / sections.size.to_f
      word_count = text.split.size
      is_minimal = word_count < 100

      confidence = if completeness >= 0.8 && !is_minimal
                     "high"
      elsif completeness >= 0.5
                     "medium"
      else
                     "low"
      end

      {
        completeness: completeness,
        missing: sections.select { |_, v| !v }.keys,
        word_count: word_count,
        is_minimal: is_minimal,
        confidence: confidence
      }
    end

    def extract_requirements_from_query(query, sourcing)
      # Tenta usar requisitos já extraídos do sourcing
      return sourcing.parsed_requirements[:requirements] if sourcing&.parsed_requirements.present?

      # Fallback: requisitos básicos inferidos
      []
    end

    def analysis_model
      Llm::ClientFactory.chat_model(account: Current.account)
    end

    def calculate_cost(usage)
      Llm::CostCalculator.calculate(
        model: analysis_model,
        input_tokens: usage["prompt_tokens"] || 0,
        output_tokens: usage["completion_tokens"] || 0
      )
    end

    def fetch_cached_result(query, text)
      cache_key = "profile_analyzer/v1/#{analysis_model}/#{Digest::SHA256.hexdigest("#{query}|#{text}")}"
      cached = Rails.cache.read(cache_key)
      return nil unless cached

      @logger.info "⚡ [ProfileAnalyzer] Cache hit — skipping LLM call"
      cached
    end

    def store_cached_result(query, text, result)
      cache_key = "profile_analyzer/v1/#{analysis_model}/#{Digest::SHA256.hexdigest("#{query}|#{text}")}"
      Rails.cache.write(cache_key, result, expires_in: 7.days)
    rescue => e
      @logger.warn "⚠️ [ProfileAnalyzer] Failed to cache result: #{e.message}"
    end

    def skipped(reason)
      { status: :skipped, error: reason }
    end
  end
end
