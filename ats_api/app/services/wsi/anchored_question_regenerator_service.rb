# frozen_string_literal: true

module Wsi
  class AnchoredQuestionRegeneratorService
    TEMPERATURE = 0.35
    MAX_TOKENS = 400

    def self.call(job:, question_text:, auditor_suggestion:, skill_or_trait_label:, question_category:)
      new(
        job: job,
        question_text: question_text,
        auditor_suggestion: auditor_suggestion,
        skill_or_trait_label: skill_or_trait_label,
        question_category: question_category
      ).call
    end

    def initialize(job:, question_text:, auditor_suggestion:, skill_or_trait_label:, question_category:)
      @job = job
      @question_text = question_text.to_s.strip
      @auditor_suggestion = auditor_suggestion.to_s.strip
      @skill_or_trait_label = skill_or_trait_label.to_s.presence || "não informado"
      @question_category = question_category.to_s.downcase
    end

    def call
      return @question_text if @question_text.blank? || @auditor_suggestion.blank?
      return @question_text if @job.blank?

      jd = JdAnchoringValidatorService.jd_text_for_job(@job)
      return @question_text if jd.blank?

      response = Llm::Gateway.chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user", content: user_prompt(jd) }
        ],
        temperature: TEMPERATURE,
        max_tokens: MAX_TOKENS,
        tracking: { operation: "wsi.jd_anchoring_regeneration" }
      )

      content = response.dig("choices", 0, "message", "content").to_s.strip
      return @question_text if content.blank?

      cleaned = content.sub(/\A["']/, "").sub(/["']\z/, "").strip
      cleaned.presence || @question_text
    rescue StandardError => e
      Rails.logger.warn("⚠️ [Wsi::AnchoredQuestionRegeneratorService] #{e.class}: #{e.message}")
      @question_text
    end

    private

    def system_prompt
      <<~PROMPT.strip
        Você reescreve perguntas de triagem em português do Brasil para ficarem ancoradas no Job Description.
        Retorne APENAS o texto final da pergunta (uma pergunta aberta, 1–3 frases), sem JSON, sem aspas envolvendo o texto todo, sem explicações.
        Não mencione Bloom, Dreyfus, STAR ou frameworks internos.
      PROMPT
    end

    def user_prompt(jd_text)
      <<~PROMPT.strip
        Tipo: #{@question_category} (technical | behavioral)
        Competência avaliada: #{@skill_or_trait_label}

        Job Description (trechos relevantes):
        ---
        #{jd_text[0..12_000]}
        ---

        Pergunta atual:
        #{@question_text}

        Sugestão do auditor de âncora (incorpore para tornar a pergunta específica a ESTA vaga):
        #{@auditor_suggestion}

        Reescreva a pergunta aplicando a sugestão e mantendo tom profissional e neutro em gênero (LGPD).
      PROMPT
    end
  end
end
