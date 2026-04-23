# frozen_string_literal: true

module Wsi
  class JdAnchoringValidatorService
    TEMPERATURE = 0.0
    MAX_TOKENS = 300

    Result = Struct.new(:success?, :data, :error, :raw_response, keyword_init: true)

    def self.call(job:, question_text:, skill_or_trait_label:, question_category:)
      new(
        job: job,
        question_text: question_text,
        skill_or_trait_label: skill_or_trait_label,
        question_category: question_category
      ).call
    end

    def initialize(job:, question_text:, skill_or_trait_label:, question_category:)
      @job = job
      @question_text = question_text.to_s.strip
      @skill_or_trait_label = skill_or_trait_label.to_s.presence || "não informado"
      @question_category = normalize_category(question_category)
    end

    def call
      return failure("question_text blank") if @question_text.blank?
      return failure("job missing") if @job.blank?

      jd = self.class.jd_text_for_job(@job)
      return failure("jd_text blank") if jd.blank?

      response = Llm::Gateway.fast_chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user", content: user_prompt(jd) }
        ],
        temperature: TEMPERATURE,
        max_tokens: MAX_TOKENS,
        tracking: { operation: "wsi.jd_anchoring_validation" }
      )

      content = response.dig("choices", 0, "message", "content")
      return failure("blank_llm_response") if content.blank?

      parsed = parse_json(content)
      return failure("invalid_json") if parsed.blank?

      Result.new(success?: true, data: normalize_result(parsed), error: nil, raw_response: content)
    rescue StandardError => e
      Rails.logger.error("❌ [Wsi::JdAnchoringValidatorService] #{e.class}: #{e.message}")
      failure(e.message)
    end

    def self.jd_text_for_job(job)
      return "" if job.blank?

      lia = job.lia_job_description
      if lia.is_a?(Hash) && lia["enriched_jd"].present?
        ej = lia["enriched_jd"]
        return ej.to_json if ej.is_a?(Hash)
        return ej.to_s
      end

      parts = []
      parts << job.title.to_s if job.respond_to?(:title)
      parts << job.description.to_s if job.respond_to?(:description)
      if job.respond_to?(:responsibilities)
        r = job.responsibilities
        parts << (r.is_a?(Array) ? r.join("\n") : r.to_s)
      end
      parts.compact.map(&:strip).reject(&:blank?).join("\n\n")
    end

    private

    def failure(message)
      Result.new(success?: false, data: {}, error: message, raw_response: nil)
    end

    def normalize_category(raw)
      s = raw.to_s.downcase
      return "behavioral" if s == "behavioral"
      return "technical" if s == "technical"

      "technical"
    end

    def system_prompt
      <<~PROMPT.strip
        Você é um auditor de qualidade de perguntas de triagem.
        Sua única tarefa é verificar se a pergunta gerada é ANCORADA no Job Description fornecido.

        Uma pergunta é ANCORADA quando:
        - Refere-se a uma responsabilidade, skill, contexto ou desafio EXPLICITAMENTE mencionado no JD
        - Não poderia ser feita com a mesma especificidade para qualquer outra vaga

        Uma pergunta NÃO é ancorada quando:
        - Poderia ser feita para qualquer cargo do mesmo nível ("Descreva um projeto desafiador...")
        - Refere-se a skills ou contextos ausentes do JD
        - É genérica o suficiente para ser reutilizada em vagas completamente diferentes

        REGRAS:
        - Retorne APENAS o JSON. Sem texto fora do JSON.
        - "evidence_in_jd" deve ser uma citação LITERAL do JD entre aspas — nunca paráfrase
        - Se a pergunta não for ancorada, "evidence_in_jd" deve ser "" (string vazia)
        - "anchor_type" classifica o tipo de ancoragem encontrada
      PROMPT
    end

    def user_prompt(jd_enriched_text)
      <<~PROMPT.strip
        Job Description da vaga (texto completo ou trecho relevante):
        ---
        #{jd_enriched_text}
        ---

        Skill ou trait que a pergunta avalia: #{@skill_or_trait_label}
        Tipo de pergunta: #{@question_category} (technical | behavioral)

        Pergunta gerada para validar:
        "#{@question_text}"

        Retorne o seguinte JSON (sem texto fora do JSON):
        {
          "is_anchored": true|false,
          "evidence_in_jd": "\"trecho literal exato do JD que ancora a pergunta\" (vazio se não ancorada)",
          "anchor_type": "responsibility | skill | context | challenge | none",
          "confidence": "high | medium | low",
          "anchor_explanation": "em 1 frase: por que esta pergunta é ou não é específica para este JD",
          "suggestion": "reformulação sugerida apenas se is_anchored = false, senão string vazia"
        }
      PROMPT
    end

    def parse_json(content)
      clean = content.to_s.strip
      clean = clean.sub(/\A```json\s*/i, "").sub(/\A```\s*/i, "").sub(/\s*```\z/, "").strip
      JSON.parse(clean, symbolize_names: true)
    rescue JSON::ParserError
      nil
    end

    def normalize_result(h)
      {
        is_anchored: ActiveModel::Type::Boolean.new.cast(h[:is_anchored]),
        evidence_in_jd: h[:evidence_in_jd].to_s,
        anchor_type: h[:anchor_type].to_s,
        confidence: h[:confidence].to_s,
        anchor_explanation: h[:anchor_explanation].to_s,
        suggestion: h[:suggestion].to_s
      }
    end
  end
end
