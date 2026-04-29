# frozen_string_literal: true

module Wsi
  class GateEngine
    def self.evaluate(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).evaluate
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def evaluate
      dimensions = Evaluations::WsiDimensionScores.call(evaluation_candidate: @evaluation_candidate)
      answers = dimensions[:answers]
      return { triggered: false, gate: nil, reason: nil } if answers.blank?

      %i[run_g2 run_g3 run_g4 run_g5 run_g6].each do |step|
        result = send(step, dimensions, answers)
        return result if result[:triggered]
      end

      { triggered: false, gate: nil, reason: nil }
    end

    private

    def run_g2(_dimensions, _answers)
      total_injection = Answer.where(
        evaluation_id: @evaluation_candidate.evaluation_id,
        candidate_id: @evaluation_candidate.candidate_id
      ).sum(:injection_attempt_count)

      if total_injection >= 2 || @evaluation_candidate.g2_gate_triggered
        return { triggered: true, gate: "G2", reason: "prompt_injection_reincident" }
      end

      { triggered: false, gate: nil, reason: nil }
    end

    def run_g3(dimensions, _answers)
      wsi_technical = dimensions[:technical]
      if wsi_technical.to_f < 4.0
        return { triggered: true, gate: "G3", reason: "wsi_tecnico_below_threshold" }
      end

      { triggered: false, gate: nil, reason: nil }
    end

    def run_g4(_dimensions, answers)
      answers.each do |answer|
        next unless critical_question?(answer.question)
        next if answer.final_skill_score.nil?

        if answer.final_skill_score.to_f < 3.0
          return { triggered: true, gate: "G4", reason: "critical_skill_below_threshold" }
        end
      end

      { triggered: false, gate: nil, reason: nil }
    end

    def critical_question?(question)
      return false if question.blank?

      meta = question.wsi_metadata.is_a?(Hash) ? question.wsi_metadata : {}
      ActiveModel::Type::Boolean.new.cast(meta["critical"] || meta[:critical])
    end

    def run_g5(_dimensions, answers)
      gated = answers.reject { |a| a.question&.competence_type == "eligibility" }
      return { triggered: false, gate: nil, reason: nil } if gated.blank?

      short = gated.count { |a| word_count(a.description) < 30 }
      ratio = short.to_f / gated.size
      if ratio >= 0.5
        return { triggered: true, gate: "G5", reason: "low_engagement_short_answers" }
      end

      { triggered: false, gate: nil, reason: nil }
    end

    def run_g6(_dimensions, answers)
      count = answers.count { |a| inflation_detected?(a) }
      if count >= 3
        return { triggered: true, gate: "G6", reason: "systematic_inflation" }
      end

      { triggered: false, gate: nil, reason: nil }
    end

    def word_count(text)
      text.to_s.split(/\s+/).map(&:strip).reject(&:blank?).size
    end

    def inflation_detected?(answer)
      ext = extraction_hash(answer)
      return false if ext.blank?

      ActiveModel::Type::Boolean.new.cast(ext[:inflation_detected] || ext["inflation_detected"])
    end

    def extraction_hash(answer)
      ad = answer.analysis_data
      return {} unless ad.is_a?(Hash)

      raw = ad.dig("wsi", "extraction") || ad.dig(:wsi, :extraction)
      return {} unless raw.is_a?(Hash)

      raw.with_indifferent_access
    end
  end
end
