# frozen_string_literal: true

module Wsi
  class GateChecklist
    def self.call(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).call
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      dimensions = Evaluations::WsiDimensionScores.call(evaluation_candidate: @evaluation_candidate)
      answers = dimensions[:answers]
      {
        "G1" => gate_g1(answers),
        "G2" => gate_g2,
        "G3" => gate_g3(dimensions),
        "G4" => gate_g4(answers),
        "G5" => gate_g5(answers),
        "G6" => gate_g6(answers)
      }
    end

    private

    def gate_g1(answers)
      eval_record = @evaluation_candidate.evaluation
      return { "pass" => true, "detail" => "no_eligibility_questions" } if eval_record.blank?

      elig_ids = eval_record.questions.where(competence_type: "eligibility").pluck(:id)
      return { "pass" => true, "detail" => "no_eligibility_questions" } if elig_ids.blank?

      answered = @evaluation_candidate.answers.where(question_id: elig_ids)
      if answered.count != elig_ids.size
        return { "pass" => false, "detail" => "incomplete_eligibility" }
      end

      all_yes = answered.all? { |a| a.eligibility_answer == true }
      return { "pass" => true, "detail" => "all_eligible" } if all_yes

      { "pass" => false, "detail" => "eligibility_failed" }
    end

    def gate_g2
      total_injection = Answer.where(
        evaluation_id: @evaluation_candidate.evaluation_id,
        candidate_id: @evaluation_candidate.candidate_id
      ).sum(:injection_attempt_count)

      if total_injection >= 2 || @evaluation_candidate.g2_gate_triggered
        return { "pass" => false, "detail" => "prompt_injection", "count" => total_injection }
      end

      { "pass" => true, "detail" => "ok" }
    end

    def gate_g3(dimensions)
      wsi_technical = dimensions[:technical].to_f
      if wsi_technical < 4.0
        return { "pass" => false, "detail" => "wsi_tecnico_below_4", "wsi_tecnico" => wsi_technical.round(2) }
      end

      { "pass" => true, "detail" => "ok", "wsi_tecnico" => wsi_technical.round(2) }
    end

    def gate_g4(answers)
      answers.each do |answer|
        next unless critical_question?(answer.question)
        next if answer.final_skill_score.nil?

        if answer.final_skill_score.to_f < 3.0
          return { "pass" => false, "detail" => "critical_skill_below_3", "question_id" => answer.question_id }
        end
      end

      { "pass" => true, "detail" => "ok" }
    end

    def critical_question?(question)
      return false if question.blank?

      meta = question.wsi_metadata.is_a?(Hash) ? question.wsi_metadata : {}
      ActiveModel::Type::Boolean.new.cast(meta["critical"] || meta[:critical])
    end

    def gate_g5(answers)
      gated = answers.reject { |a| a.question&.competence_type == "eligibility" }
      return { "pass" => true, "detail" => "no_gated_answers" } if gated.blank?

      short = gated.count { |a| word_count(a.description) < 30 }
      ratio = short.to_f / gated.size
      if ratio >= 0.5
        return { "pass" => false, "detail" => "low_engagement_short_answers", "short_ratio" => ratio.round(2) }
      end

      { "pass" => true, "detail" => "ok", "short_ratio" => ratio.round(2) }
    end

    def gate_g6(answers)
      count = answers.count { |a| inflation_detected?(a) }
      if count >= 3
        return { "pass" => false, "detail" => "systematic_inflation", "inflation_count" => count }
      end

      { "pass" => true, "detail" => "ok", "inflation_count" => count }
    end

    def word_count(text)
      text.to_s.split(/\s+/).map(&:strip).reject(&:blank?).size
    end

    def inflation_detected?(answer)
      ext = extraction_hash(answer)
      ActiveModel::Type::Boolean.new.cast(ext[:inflation_detected] || ext["inflation_detected"])
    end

    def extraction_hash(answer)
      ad = answer.analysis_data
      return {}.with_indifferent_access unless ad.is_a?(Hash)

      raw = ad.dig("wsi", "extraction") || ad.dig(:wsi, :extraction)
      return {}.with_indifferent_access unless raw.is_a?(Hash)

      raw.with_indifferent_access
    end
  end
end
