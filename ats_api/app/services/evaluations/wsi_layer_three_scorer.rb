# frozen_string_literal: true

module Evaluations
  module WsiLayerThreeScorer
    module_function

    def bloom_alignment(expected, demonstrated)
      return 1.0 if expected.blank? || demonstrated.blank?

      e = expected.to_i
      d = demonstrated.to_i
      diff = e - d
      return 1.00 if diff <= 0
      return 0.70 if diff == 1
      return 0.40 if diff == 2

      0.15
    end

    def trait_signals_norm(detected, expected)
      exp = Array(expected).map(&:to_s).reject(&:blank?)
      det = Array(detected).compact
      denominator = [ exp.size, 1 ].max
      [ det.size.to_f / denominator, 1.0 ].min
    end

    def adjustments_84(extraction:, bloom_e:, bloom_d:, drey_e:, drey_d:, expected_signals:, competence_behavioral:)
      delta = 0.0

      if ActiveModel::Type::Boolean.new.cast(extraction[:inflation_detected])
        delta -= 1.5
      end

      if competence_behavioral && Array(extraction[:trait_signals_detected]).blank?
        delta -= 2.0
      end

      if drey_d < drey_e - 1
        delta -= 0.8
      end

      if bloom_d > bloom_e
        delta += 0.6
      end

      detected = Array(extraction[:trait_signals_detected]).compact
      exp_list = Array(expected_signals).map(&:to_s).reject(&:blank?)
      if competence_behavioral && exp_list.size.positive? && detected.size > exp_list.size
        delta += 0.4
      end

      if drey_d > drey_e
        delta += 0.5
      end

      delta
    end

    def structural_sum(cbi)
      keys = %i[
        star_penalty_words star_penalty_no_first_person star_penalty_missing_result
        star_penalty_paraphrase star_penalty_wrong_language
        star_bonus_quantified star_bonus_long_response star_bonus_multi_episode
      ]
      keys.sum { |k| cbi[k].to_f }
    end
  end
end
