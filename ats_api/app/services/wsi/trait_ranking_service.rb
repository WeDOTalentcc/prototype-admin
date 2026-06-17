# frozen_string_literal: true

module Wsi
  class TraitRankingService
    METHOD_VERSION = "wsi_f3_v1"
    TRAITS = JdBigFiveExtractionService::TRAITS

    def self.call(job:, mode: :compact)
      new(job: job, mode: mode).call
    end

    def self.trait_weight_for(job:, ocean_trait:)
      return 1.0 if job.blank?

      trait = ocean_trait.to_s.strip
      return 1.0 if trait.blank?

      data = job.wsi_jd_trait_ranking
      return 1.0 unless data.is_a?(Hash) && data.present?

      rows = data["big_five_ranking"]
      return 1.0 if rows.blank?

      api_trait = Wsi::OceanTraitCanonical.to_api(trait)
      row = Array(rows).find do |r|
        next unless r.is_a?(Hash)

        r = r.with_indifferent_access
        r[:trait].to_s == api_trait
      end
      return 1.0 if row.blank?

      w = row.with_indifferent_access[:weight_normalized]
      return 1.0 if w.nil?

      w.to_f
    end

    def initialize(job:, mode:)
      @job = job
      @mode = mode
    end

    def call
      return failure("Invalid job", code: "wsi_trait_ranking_job_invalid") if @job.blank?
      return failure("mode must be :compact or :full", code: "wsi_trait_ranking_mode_invalid") unless valid_mode?

      profile = @job.wsi_jd_big_five_profile
      inner = profile.is_a?(Hash) ? profile["big_five_jd"] || profile[:big_five_jd] : nil
      return failure("Missing big_five_jd in wsi_jd_big_five_profile", code: "wsi_trait_ranking_profile_missing") if inner.blank?

      seniority_key = Wsi::Constants.seniority_key(@job)
      mode_sym = @mode.to_sym
      top_n = Wsi::Constants.big_five_top_n(seniority_key, mode_sym)

      scored = TRAITS.map { |trait| [ trait, score_for(inner, trait) ] }
      scored.sort_by! { |trait, score| [ -score, TRAITS.index(trait) ] }

      top_slice = scored.first(top_n)
      sum_top = top_slice.sum { |_, s| s.to_f }
      sum_top = 1.0 if sum_top <= 0

      big_five_ranking = scored.each_with_index.map do |(trait, score), index|
        rank = index + 1
        in_top = rank <= top_n
        weight = if in_top
          (score.to_f / sum_top).round(6)
        else
          0.0
        end

        {
          "rank" => rank,
          "trait" => trait,
          "score" => score,
          "weight_normalized" => weight,
          "in_top_n" => in_top
        }
      end

      payload = {
        "computed_at" => Time.current.iso8601,
        "method_version" => METHOD_VERSION,
        "mode" => mode_sym.to_s,
        "seniority_key" => seniority_key,
        "top_n" => top_n,
        "big_five_ranking" => big_five_ranking
      }

      @job.update_column(:wsi_jd_trait_ranking, payload)

      { success: true, ranking: payload, error: nil, code: nil }
    rescue StandardError => e
      failure("Trait ranking failed: #{e.message}", code: "wsi_trait_ranking_error")
    end

    private

    def valid_mode?
      %i[compact full].include?(@mode.to_sym)
    end

    def score_for(inner, trait)
      row = inner.is_a?(Hash) ? inner[trait] || inner[trait.to_sym] : nil
      return 0 unless row.is_a?(Hash)

      s = row["score"] || row[:score]
      s = s.to_i
      return 0 if s.negative?

      [ s, 100 ].min
    end

    def failure(message, code:)
      { success: false, ranking: nil, error: message, code: code }
    end
  end
end
