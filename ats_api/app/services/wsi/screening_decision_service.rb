# frozen_string_literal: true

module Wsi
  class ScreeningDecisionService
    def self.call(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).call
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      gate = GateEngine.evaluate(evaluation_candidate: @evaluation_candidate)
      if gate[:triggered]
        return {
          result: "REPROVADO",
          confidence: "alta",
          human_review_required: false,
          gate_triggered: gate[:gate],
          reason: gate[:reason].to_s
        }
      end

      dimensions = Evaluations::WsiDimensionScores.call(evaluation_candidate: @evaluation_candidate)
      wsi = dimensions[:final].to_f
      wsi_tec = dimensions[:technical].to_f
      wsi_comp = dimensions[:behavioral].to_f

      if wsi >= 7.5 && wsi_tec >= 6.5 && wsi_comp >= 6.5
        return {
          result: "APROVADO",
          confidence: "alta",
          human_review_required: false,
          gate_triggered: nil,
          reason: "score_thresholds_met"
        }
      end

      if wsi >= 7.0 && wsi_tec >= 5.5
        return {
          result: "APROVADO",
          confidence: "media",
          human_review_required: true,
          gate_triggered: nil,
          reason: "score_thresholds_met_with_review"
        }
      end

      if wsi >= 6.0
        shortfall = top_trait_shortfall_points
        if shortfall > 20
          return {
            result: "REPROVADO",
            confidence: "media",
            human_review_required: true,
            gate_triggered: nil,
            reason: "gap_trait_critico"
          }
        end

        return {
          result: "EM_AVALIACAO",
          confidence: "baixa",
          human_review_required: true,
          gate_triggered: nil,
          reason: "score_in_review_band"
        }
      end

      {
        result: "REPROVADO",
        confidence: "alta",
        human_review_required: false,
        gate_triggered: nil,
        reason: "wsi_final_below_minimum"
      }
    end

    private

    def top_trait_shortfall_points
      job = @evaluation_candidate.job
      return 0 if job.blank?

      ranking = job.wsi_jd_trait_ranking
      return 0 unless ranking.is_a?(Hash)

      rows = Array(ranking["big_five_ranking"]).select { |row| row.is_a?(Hash) }
      first = rows.min_by { |row| row["rank"].to_i }
      return 0 unless first.is_a?(Hash)

      trait = first["trait"].to_s
      return 0 if trait.blank?

      observed = @evaluation_candidate.wsi_big_five_observed
      return 0 unless observed.is_a?(Hash)

      cand = observed.dig("candidate_big_five_observed", trait)
      return 0 unless cand.is_a?(Hash)

      req = cand["score_required"] || cand[:score_required]
      dem = cand["score_demonstrated"] || cand[:score_demonstrated]
      return 0 if req.nil? || dem.nil?

      req.to_i - dem.to_i
    end
  end
end
