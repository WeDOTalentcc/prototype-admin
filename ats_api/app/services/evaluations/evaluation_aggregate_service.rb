# frozen_string_literal: true

module Evaluations
  class EvaluationAggregateService
    DREYFUS_LEVELS = {
      1 => "Novice",
      2 => "Advanced Beginner",
      3 => "Competent",
      4 => "Proficient",
      5 => "Expert"
    }.freeze

    GAP_STATUS_GAP_THRESHOLD = -15

    Result = Struct.new(:success?, :score, :wsi_classification, :wsi_level, :wsi_summary, :error, keyword_init: true)

    def self.call(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).call
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      dimensions = Evaluations::WsiDimensionScores.call(evaluation_candidate: @evaluation_candidate)
      answers = dimensions[:answers]
      return failure("No scored answers found for evaluation candidate") if answers.blank?

      wsi_score = dimensions[:final]

      dreyfus_numeric = average(extract_dreyfus_scores(answers)).round.clamp(1, 5)
      classification = classify_wsi(wsi_score)
      level = DREYFUS_LEVELS[dreyfus_numeric]
      summary = build_summary(
        wsi_score: wsi_score,
        classification: classification,
        level: level,
        answers_count: answers.size
      )

      big_five_payload = build_wsi_big_five_observed(answers)

      @evaluation_candidate.update!(
        score: wsi_score,
        wsi_classification: classification,
        wsi_level: level,
        wsi_summary: summary,
        wsi_big_five_observed: big_five_payload
      )

      Evaluations::WsiScreeningPersistence.call(evaluation_candidate: @evaluation_candidate.reload)

      Result.new(
        success?: true,
        score: wsi_score,
        wsi_classification: classification,
        wsi_level: level,
        wsi_summary: summary,
        error: nil
      )
    rescue StandardError => e
      Rails.logger.error("❌ [EvaluationAggregateService] Error for evaluation_candidate #{@evaluation_candidate&.id}: #{e.class} - #{e.message}")
      failure(e.message)
    end

    private

    def scored_answers
      @evaluation_candidate.answers.includes(:question).where.not(final_skill_score: nil)
    end

    def average(values)
      return 0.0 if values.blank?

      (values.sum.to_f / values.size).round(4)
    end

    def extract_dreyfus_scores(answers)
      answers.filter_map do |answer|
        analysis = answer.analysis_data.is_a?(Hash) ? answer.analysis_data : {}
        analysis.dig("dreyfus", "score") || analysis.dig(:dreyfus, :score)
      end
    end

    def classify_wsi(score)
      s = score.to_f
      return "Excepcional" if s >= 9.0 && s <= 10.0
      return "Excelente" if s >= 8.0 && s < 9.0
      return "Alto" if s >= 7.0 && s < 8.0
      return "Médio" if s >= 6.0 && s < 7.0
      return "Abaixo da média" if s >= 4.5 && s < 6.0
      return "Regular" if s >= 0.0 && s < 4.5

      "Regular"
    end

    def build_summary(wsi_score:, classification:, level:, answers_count:)
      "WSI #{wsi_score}/10.0 (#{classification}) em #{answers_count} respostas avaliadas. Nível global #{level}."
    end

    def build_wsi_big_five_observed(answers)
      job = @evaluation_candidate.job
      return {} if job.blank?

      profile = job.wsi_jd_big_five_profile
      inner = profile.is_a?(Hash) ? profile["big_five_jd"] || profile[:big_five_jd] : nil
      return {} if inner.blank? || !inner.is_a?(Hash)

      by_trait = Hash.new { |h, k| h[k] = [] }
      answers.each do |answer|
        next unless answer.question&.competence_type == "behavioral"

        trait_raw = answer.question.ocean_trait
        next if trait_raw.blank?

        api_trait = Wsi::OceanTraitCanonical.to_api(trait_raw)
        next if api_trait.blank?

        by_trait[api_trait] << answer.final_skill_score.to_f
      end

      observed = {}
      Wsi::JdBigFiveExtractionService::TRAITS.each do |trait|
        row = inner[trait] || inner[trait.to_s]
        score_required = row.is_a?(Hash) ? (row["score"] || row[:score]) : nil
        score_required_i = score_required.nil? ? nil : score_required.to_i

        scores = by_trait[trait]
        if scores.blank?
          observed[trait] = {
            "score_demonstrated" => nil,
            "score_required" => score_required_i,
            "gap" => nil,
            "status" => "Não avaliado",
            "critical_gap" => false
          }
          next
        end

        avg_scale_10 = scores.sum / scores.size
        demonstrated = (avg_scale_10 * 10).round
        if score_required_i.nil?
          observed[trait] = {
            "score_demonstrated" => demonstrated,
            "score_required" => nil,
            "gap" => nil,
            "status" => "OK",
            "critical_gap" => false
          }
          next
        end

        gap = demonstrated - score_required_i
        status = big_five_status_for_gap(gap)
        observed[trait] = {
          "score_demonstrated" => demonstrated,
          "score_required" => score_required_i,
          "gap" => gap,
          "status" => status,
          "critical_gap" => gap <= GAP_STATUS_GAP_THRESHOLD
        }
      end

      critical_gaps = observed.filter_map { |k, v| k if v["critical_gap"] }
      strengths = observed.filter_map { |k, v| k if v["status"] == "SUPERADO" }

      {
        "candidate_big_five_observed" => observed,
        "overall_behavioral_fit" => infer_overall_behavioral_fit(observed),
        "critical_gaps" => critical_gaps,
        "strengths" => strengths
      }
    end

    def big_five_status_for_gap(gap)
      return "SUPERADO" if gap.positive?
      return "GAP" if gap <= GAP_STATUS_GAP_THRESHOLD

      "OK"
    end

    def infer_overall_behavioral_fit(observed)
      gaps = observed.values.filter_map { |v| v["gap"] if v["score_demonstrated"].present? }
      return "unknown" if gaps.blank?

      mean_gap = gaps.sum.to_f / gaps.size
      return "high" if mean_gap >= 5
      return "medium-high" if mean_gap >= 0
      return "medium-low" if mean_gap >= -10

      "low"
    end

    def failure(message)
      Result.new(success?: false, score: nil, wsi_classification: nil, wsi_level: nil, wsi_summary: nil, error: message)
    end
  end
end
