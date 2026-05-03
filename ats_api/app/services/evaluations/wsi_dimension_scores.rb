# frozen_string_literal: true

module Evaluations
  class WsiDimensionScores
    def self.call(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).call
    end

    def self.distribution_weights(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).send(:final_distribution_weights)
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def macro_distribution_weights
      final_distribution_weights
    end

    def call
      answers = scored_answers
      return empty_result if answers.blank?

      wsi_technical = compute_wsi_technical(answers)
      wsi_behavioral = compute_wsi_behavioral(answers)
      weights = final_distribution_weights
      eligibility_applies = eligibility_block_applies?
      wsi_eligibility = eligibility_applies ? wsi_eligibility_score : 0.0

      peso_tech, peso_comp, peso_elig = if eligibility_applies
        [ weights[:technical] * 0.8, weights[:behavioral] * 0.8, 0.2 ]
      else
        [ weights[:technical], weights[:behavioral], 0.0 ]
      end

      wsi_final = (
        (wsi_technical * peso_tech) +
        (wsi_behavioral * peso_comp) +
        (wsi_eligibility * peso_elig)
      ).clamp(0.0, 10.0).round(2)

      {
        technical: wsi_technical.round(4),
        behavioral: wsi_behavioral.round(4),
        final: wsi_final,
        answers: answers
      }
    end

    private

    def empty_result
      { technical: 0.0, behavioral: 0.0, final: 0.0, answers: [] }
    end

    def scored_answers
      @evaluation_candidate.answers.includes(:question).where.not(final_skill_score: nil).joins(:question)
    end

    def compute_wsi_technical(answers)
      technical = answers.filter_map do |answer|
        next if answer.question&.competence_type == "eligibility"
        next if answer.question&.competence_type == "behavioral"

        answer.final_skill_score.to_f
      end
      average(technical)
    end

    def compute_wsi_behavioral(answers)
      behavioral = answers.select { |a| a.question&.competence_type == "behavioral" }
      return 0.0 if behavioral.blank?

      weights = behavioral.map { |a| trait_weight_for_answer(a) }
      if weights.all? { |w| w.present? && w.to_f.positive? }
        weighted_sum = behavioral.zip(weights).sum { |a, w| a.final_skill_score.to_f * w.to_f }
        weight_total = weights.sum(&:to_f)
        return 0.0 if weight_total <= 0

        (weighted_sum / weight_total).round(4)
      else
        average(behavioral.map { |a| a.final_skill_score.to_f })
      end
    end

    def trait_weight_for_answer(answer)
      ep = answer.question&.extra_params
      return nil unless ep.is_a?(Hash)

      ep["trait_weight"] || ep[:trait_weight]
    end

    def final_distribution_weights
      custom = fetch_config_hash(account_wsi_scoring_config, :macro_distribution)
      has_explicit = custom.key?(:technical) || custom.key?(:behavioral) || custom.key?("technical") || custom.key?("behavioral")

      unless has_explicit
        seniority_key = Wsi::Constants.seniority_key(@evaluation_candidate.job) || "pleno"
        sw = Wsi::Constants::SENIORITY_WEIGHTS.fetch(seniority_key, Wsi::Constants::SENIORITY_WEIGHTS["pleno"])
        return { technical: sw[:technical].to_f, behavioral: sw[:behavioral].to_f }
      end

      technical = custom[:technical] || custom["technical"]
      behavioral = custom[:behavioral] || custom["behavioral"]
      technical = technical.nil? ? 0.70 : technical.to_f
      behavioral = behavioral.nil? ? 0.30 : behavioral.to_f
      total = technical + behavioral
      return { technical: 0.70, behavioral: 0.30 } if total <= 0

      {
        technical: (technical / total).round(4),
        behavioral: (behavioral / total).round(4)
      }
    end

    def eligibility_block_applies?
      eval_record = @evaluation_candidate.evaluation
      return false if eval_record.blank?

      elig_question_ids = eval_record.questions.where(competence_type: "eligibility").pluck(:id)
      return false if elig_question_ids.blank?

      answered = @evaluation_candidate.answers.where(question_id: elig_question_ids)
      answered.count == elig_question_ids.size
    end

    def wsi_eligibility_score
      eval_record = @evaluation_candidate.evaluation
      return 0.0 if eval_record.blank?

      elig_question_ids = eval_record.questions.where(competence_type: "eligibility").pluck(:id)
      return 0.0 if elig_question_ids.blank?

      answered = @evaluation_candidate.answers.where(question_id: elig_question_ids)
      return 0.0 unless answered.count == elig_question_ids.size

      answered.all? { |a| a.eligibility_answer == true } ? 10.0 : 0.0
    end

    def average(values)
      return 0.0 if values.blank?

      (values.sum.to_f / values.size).round(4)
    end

    def account_wsi_scoring_config
      config = @evaluation_candidate.account&.sourcing_config
      return {} unless config.is_a?(Hash)

      (config["wsi_scoring"] || config[:wsi_scoring] || {}).deep_symbolize_keys
    end

    def fetch_config_hash(config, key)
      value = config[key] || config[key.to_s]
      value.is_a?(Hash) ? value.deep_symbolize_keys : {}
    end
  end
end
