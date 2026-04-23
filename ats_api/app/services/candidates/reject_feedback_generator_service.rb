# frozen_string_literal: true

module Candidates
  class RejectFeedbackGeneratorService
    def initialize(apply:)
      @apply = apply
    end

    def self.call(apply:, **opts)
      new(apply: apply, **opts).call
    end

    def call
      return fallback_result if Rails.env.test?

      job_title = @apply.job&.title.presence || "Vaga"
      candidate_name = @apply.candidate&.name.presence || "Candidato"
      rejection_reason = @apply.reason_for_reject.presence || "Não informado"
      wsi_score = fetch_wsi_score
      had_incident = fetch_had_incident

      prompt = build_prompt(
        job_title: job_title,
        candidate_name: candidate_name,
        rejection_reason: rejection_reason,
        wsi_score: wsi_score,
        had_incident: had_incident
      )

      response = Llm::Gateway.chat(
        messages: [
          { role: "system", content: system_prompt },
          { role: "user", content: prompt }
        ],
        temperature: 0.5,
        max_tokens: 600,
        response_format: { type: "json_object" },
        tracking: { operation: "candidates.reject_feedback_generator", apply_id: @apply.id }
      )

      content = response.dig("choices", 0, "message", "content")
      return fallback_result if content.blank?

      parsed = parse_response(content)
      parsed
    rescue => e
      fallback_result
    end

    private

    def system_prompt
      <<~PROMPT.strip
        Você é a LIA, assistente de recrutamento da WeDo Talent. Gere feedback profissional e empático para candidato reprovado.

        Regras obrigatórias:
        1. Tom profissional e empático
        2. Não mencionar score numérico
        3. Sugerir áreas de desenvolvimento CONCRETAS (ex: comunicação, organização, liderança) - nunca use placeholders ou variáveis
        4. Se had_incident=true, reconhecer dificuldade técnica com tom mais compreensivo
        5. Máximo 200 palavras
        6. Não prometer recontato futuro
        7. Não mencionar outros candidatos
        8. Incluir agradecimento
        9. Não revelar detalhes internos de avaliação
        10. Personalizar com nome do candidato e vaga

        PROIBIDO: O feedback_text deve ser texto final e completo. NUNCA use placeholders como [mencionar X], [áreas de desenvolvimento], [nome] ou qualquer variável entre colchetes.

        Retorne APENAS um JSON válido no formato:
        {"feedback_text": "...", "tone": "empathetic|neutral|encouraging", "development_areas": ["..."]}
      PROMPT
    end

    def build_prompt(job_title:, candidate_name:, rejection_reason:, wsi_score:, had_incident:)
      <<~PROMPT.strip
        <context>
        Vaga: #{job_title}
        Candidato: #{candidate_name}
        Motivo reprovação: #{rejection_reason}
        Score WSI: #{wsi_score}
        Houve incidente na triagem: #{had_incident}
        </context>

        Gere o feedback no formato JSON especificado.
      PROMPT
    end

    def fetch_wsi_score
      ec = EvaluationCandidate.find_by(
        candidate_id: @apply.candidate_id,
        job_id: @apply.job_id
      )
      return "N/A" unless ec&.score.present? && ec.score.to_f > 0

      (ec.score.to_f / 2.0).round(2).to_s
    end

    def fetch_had_incident
      ec = EvaluationCandidate.find_by(
        candidate_id: @apply.candidate_id,
        job_id: @apply.job_id
      )
      return false unless ec

      Issue.exists?(evaluation_candidate_id: ec.id, type: :screening)
    end

    def parse_response(content)
      json_str = extract_json_from_content(content)
      json = JSON.parse(json_str)
      development_areas = Array(json["development_areas"]).map(&:to_s).reject(&:blank?)
      raw_text = json["feedback_text"].to_s.strip.presence || fallback_feedback_text
      feedback_text = sanitize_feedback_text(raw_text, development_areas)
      {
        feedback_text: feedback_text,
        tone: normalize_tone(json["tone"]),
        development_areas: development_areas
      }
    rescue JSON::ParserError
      {
        feedback_text: fallback_feedback_text,
        tone: "neutral",
        development_areas: []
      }
    end

    def extract_json_from_content(content)
      str = content.to_s.strip
      str = str.sub(/\A```(?:json)?\s*\n?/i, "").sub(/\n?```\s*\z/, "")
      str.strip
    end

    def sanitize_feedback_text(text, development_areas = [])
      return text if text.blank?

      replacement = development_areas.any? ? development_areas.join(" e ") : "diversas competências"
      sanitized = text.gsub(/\s*\[[^\]]+\]\s*/, " #{replacement} ").gsub(/\s{2,}/, " ").strip
      sanitized
    end

    def normalize_tone(tone)
      return "neutral" if tone.blank?

      normalized = tone.to_s.downcase.strip
      %w[empathetic neutral encouraging].include?(normalized) ? normalized : "neutral"
    end

    def fallback_result
      {
        feedback_text: fallback_feedback_text,
        tone: "neutral",
        development_areas: []
      }
    end

    def fallback_feedback_text
      candidate_name = @apply.candidate&.name.presence || "Candidato"
      job_title = @apply.job&.title.presence || "nossa vaga"

      <<~TEXT.strip
        Olá #{candidate_name},

        Agradecemos seu interesse na vaga de #{job_title} e o tempo dedicado ao processo seletivo.

        Infelizmente, neste momento não daremos continuidade à sua candidatura. Desejamos sucesso em sua trajetória profissional e ficamos à disposição para futuras oportunidades.

        Atenciosamente,
        Equipe WeDo Talent
      TEXT
    end
  end
end
