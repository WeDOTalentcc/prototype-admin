# frozen_string_literal: true

module Wsi
  # Calls the LLM to extract a Big Five profile from the job text (approved LIA enriched JD or description).
  # Persists to `jobs.wsi_jd_big_five_profile`.
  class JdBigFiveExtractionService
    METHOD_VERSION = "wsi_f25_v1"
    TRAITS = %w[openness conscientiousness extraversion agreeableness stability].freeze
    JD_INSUFFICIENT_NOTE = "[JD insuficiente — análise com baixa confiança]"
    MIN_USEFUL_WORDS = 50
    MAX_TOKENS = 800
    MAX_EVIDENCE_ITEMS_PER_TRAIT = 4
    MAX_EVIDENCE_STRING_CHARS = 180
    TEMPERATURE = 0.1

    def self.call(job:)
      new(job: job).call
    end

    def initialize(job:)
      @job = job
    end

    def call
      return failure("Job inválido", code: "wsi_job_invalid") if @job.blank?

      jd_text, input_source = build_jd_input
      return failure("Texto da vaga insuficiente para análise", code: "wsi_jd_input_missing") if jd_text.blank?

      useful_words = useful_word_count(jd_text)
      jd_insufficient = useful_words < MIN_USEFUL_WORDS

      response = call_llm(jd_text)
      content = response.dig("choices", 0, "message", "content").to_s.strip
      return failure("Resposta vazia do modelo", code: "wsi_llm_empty") if content.blank?

      parsed = parse_response(response)
      return failure("Falha ao interpretar resposta do modelo", code: "wsi_jd_big_five_parse_error") if parsed.blank?

      inner = parsed["big_five_jd"]
      return failure("Resposta do modelo sem perfil Big Five válido", code: "wsi_jd_big_five_parse_error") if inner.blank?

      big_five = normalize_parsed_big_five(inner)
      return failure("Resposta do modelo sem perfil Big Five válido", code: "wsi_jd_big_five_parse_error") if big_five.blank?

      apply_evidence_rules!(big_five, jd_insufficient: jd_insufficient)

      payload = {
        "extracted_at" => Time.current.iso8601,
        "method_version" => METHOD_VERSION,
        "input_source" => input_source,
        "jd_insufficient" => jd_insufficient,
        "useful_word_count" => useful_words,
        "big_five_jd" => stringify_trait_entries(big_five)
      }

      @job.update_column(:wsi_jd_big_five_profile, payload)

      { success: true, profile: payload, error: nil, code: nil }
    rescue StandardError => e
      failure("Erro ao extrair perfil Big Five: #{e.message}", code: "wsi_jd_big_five_extraction_error")
    end

    private

    attr_reader :job

    def failure(message, code:)
      Rails.logger.warn "⚠️  [Wsi::JdBigFiveExtractionService] #{code} para Job ##{@job&.id}: #{message}"
      { success: false, profile: nil, error: message, code: code }
    end

    def call_llm(jd_body)
      Llm::Gateway.chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user", content: user_prompt(jd_body) }
        ],
        temperature: TEMPERATURE,
        max_tokens: MAX_TOKENS,
        tracking: { operation: "wsi.jd_big_five_extraction", job_id: @job.id }
      )
    end

    def parse_response(response)
      content = response.dig("choices", 0, "message", "content").to_s.strip
      json_str = content.gsub(/\A```(?:json)?\s*/, "").gsub(/```\z/, "").strip
      JSON.parse(json_str)
    rescue JSON::ParserError
      nil
    end

    def lia
      raw = @job.lia_job_description
      return {} unless raw.is_a?(Hash)

      raw.with_indifferent_access
    end

    def lia_approved?
      lia["status"].to_s == "approved"
    end

    def build_jd_input
      if lia_approved?
        from_enriched = text_from_enriched_jd(lia[:enriched_jd])
        return [ from_enriched.strip, "lia_enriched" ] if from_enriched.present?
      end

      parts = [ @job.description, @job.responsibilities ].compact
      text = parts.map(&:to_s).join("\n\n").strip
      [ text, "job_description" ]
    end

    def text_from_enriched_jd(enriched)
      return "" unless enriched.is_a?(Hash)

      e = enriched.with_indifferent_access
      segments = []
      segments << e[:about_role].to_s if e[:about_role].present?

      segments << join_lines(e[:responsabilidades])
      segments << e[:responsibilities].to_s if e[:responsibilities].present?
      segments << join_lines(e[:requisitos])
      segments << e[:requirements].to_s if e[:requirements].present?

      comps = e[:competencias_comportamentais]
      if comps.is_a?(Array)
        comps.each do |row|
          next unless row.is_a?(Hash)

          c = row.with_indifferent_access
          name = c[:competencia].presence || c[:name].presence
          trait = c[:trait_big_five].presence
          if name.present? && trait.present?
            segments << %(#{name} (trait_big_five: #{trait}))
          elsif name.present?
            segments << name.to_s
          end
        end
      end

      segments.compact.map(&:strip).reject(&:blank?).join("\n\n")
    end

    def join_lines(value)
      return "" if value.blank?

      if value.is_a?(Array)
        value.map(&:to_s).join("\n")
      else
        value.to_s
      end
    end

    def useful_word_count(text)
      return 0 if text.blank?

      text.scan(/[a-z0-9à-ú]+/i).count { |w| w.length >= 2 }
    end

    def system_prompt
      <<~PROMPT.strip
        Você é um psicólogo organizacional especialista em avaliação de competências e modelo Big Five (NEO-PI-R).
        Analise o Job Description fornecido e extraia o perfil de personalidade requerido pela vaga.

        Para cada um dos 5 traits do Big Five, avalie a INTENSIDADE com que o JD REQUER aquele trait.
        Baseie-se EXCLUSIVAMENTE no texto do JD — não em suposições sobre o tipo de cargo.

        RUBRIC DE AVALIAÇÃO:
        - 0–30: O trait não é mencionado ou relevante para este papel
        - 31–50: O trait aparece implicitamente; é útil mas não diferenciador
        - 51–70: O trait é claramente necessário; mencionado em responsabilidades ou requisitos
        - 71–85: O trait é central para o papel; mencionado múltiplas vezes com evidências fortes
        - 86–100: O trait é absolutamente crítico; a vaga seria inviável sem ele

        REGRAS DE EVIDÊNCIA (OBRIGATÓRIAS):
        - O campo "evidence" deve conter CITAÇÕES LITERAIS do JD — trechos exatos copiados do texto.
        - Por trait: no máximo #{MAX_EVIDENCE_ITEMS_PER_TRAIT} itens em "evidence"; cada string com no máximo #{MAX_EVIDENCE_STRING_CHARS} caracteres (se o trecho for maior, corte no limite sem reticências).
        - Priorize os trechos mais fortes para o trait; não repita a mesma ideia com redação diferente.
          PROIBIDO: paráfrase sem trecho literal
        - Se um trait não tem nenhum trecho literal que o suporte, "evidence" deve ser [] e
          "confidence" deve ser "low" com score ≤ 30
        - NUNCA infira traits a partir do nome da empresa, setor, tecnologias usadas ou cargo —
          somente do texto explícito de responsabilidades, requisitos e contexto do JD

        REGRAS PARA JD INSUFICIENTE:
        - Se o JD tiver menos de 50 palavras úteis disponíveis para análise:
          definir "confidence": "low" para TODOS os traits, independentemente dos scores
          adicionar nota em todos os "evidence": ["[JD insuficiente — análise com baixa confiança]"]

        REGRAS PARA SINAIS CONTRADITÓRIOS:
        - Quando o JD apresentar sinais que se contradizem para o mesmo trait,
          registrar em "evidence" com prefixo "[SINAL CONTRADITÓRIO]" e reduzir score para 40–55,
          definir "confidence": "medium"

        Use sempre a chave "stability" (estabilidade emocional requerida pelo papel), nunca "neuroticism".

        Retorne APENAS um JSON válido, sem texto fora do JSON.
      PROMPT
    end

    def user_prompt(jd_body)
      <<~PROMPT.strip
        JD para análise:
        ---
        #{jd_body}
        ---

        Retorne o seguinte JSON (sem texto fora do JSON):
        {
          "big_five_jd": {
            "openness": { "score": 0, "evidence": [], "confidence": "low" },
            "conscientiousness": { "score": 0, "evidence": [], "confidence": "low" },
            "extraversion": { "score": 0, "evidence": [], "confidence": "low" },
            "agreeableness": { "score": 0, "evidence": [], "confidence": "low" },
            "stability": { "score": 0, "evidence": [], "confidence": "low" }
          }
        }
      PROMPT
    end

    def normalize_parsed_big_five(inner)
      return nil unless inner.is_a?(Hash)

      src = inner.with_indifferent_access
      out = {}

      TRAITS.each do |trait|
        raw_row = src[trait]
        raw_row = src["neuroticism"] if raw_row.blank? && trait == "stability"
        next unless raw_row.is_a?(Hash)

        row = raw_row.with_indifferent_access
        score = row[:score]
        score = score.to_i if score.present?
        score = 0 if score.nil? || score.negative?
        score = 100 if score > 100

        evidence = row[:evidence]
        evidence = [ evidence ] if evidence.is_a?(String)
        evidence = Array(evidence).map(&:to_s)

        conf = row[:confidence].to_s.downcase
        conf = "low" unless %w[high medium low].include?(conf)

        out[trait] = {
          "score" => score,
          "evidence" => evidence,
          "confidence" => conf
        }
      end

      return nil unless out.keys.sort == TRAITS.sort

      out
    end

    def apply_evidence_rules!(big_five, jd_insufficient:)
      TRAITS.each do |trait|
        entry = big_five[trait]
        if jd_insufficient
          entry["evidence"] = [ JD_INSUFFICIENT_NOTE ]
          entry["confidence"] = "low"
          entry.delete("_evidence_missing")
          next
        end

        evidence = Array(entry["evidence"]).map(&:to_s)
        stripped = evidence.map(&:strip).reject(&:blank?)
        if stripped.empty?
          entry["evidence"] = []
          entry["confidence"] = "low"
          entry["_evidence_missing"] = true
          entry["score"] = [ entry["score"].to_i, 30 ].min
        else
          entry["evidence"] = clamp_evidence_list(stripped)
          entry.delete("_evidence_missing")
        end
      end
    end

    def stringify_trait_entries(big_five)
      big_five.transform_values(&:stringify_keys)
    end

    def clamp_evidence_list(strings)
      strings.filter_map do |s|
        chunk = s.to_s.strip[0, MAX_EVIDENCE_STRING_CHARS]&.strip
        chunk.presence
      end.first(MAX_EVIDENCE_ITEMS_PER_TRAIT)
    end
  end
end
