# frozen_string_literal: true

module Wsi
  class SeniorityResolverService
    SIGNAL_WEIGHTS = {
      explicit: 0.50,
      title_keywords: 0.25,
      jd_analysis: 0.25,
      salary_range: 0.15,
      skills_complexity: 0.10
    }.freeze

    SIGNAL_WEIGHT_SUM = SIGNAL_WEIGHTS.values.sum

    TITLE_CHAIN = [
      { key: "vp_clevel", pattern: /\b(vp|v\.p\.|c-level|c\s*level|chief|ceo|cto|cpo|cfo|presidente|president)\b/i },
      { key: "diretor", pattern: /\b(diretor|director|head\s+of)\b/i },
      { key: "lead", pattern: /\b(tech\s+lead|team\s+lead|lead\s+engineer|staff\s+engineer|principal\s+engineer)\b/i },
      { key: "lead", pattern: /\b(lead|staff|principal)\b/i },
      { key: "manager", pattern: /\b(gerente|manager|coordenador|coordenadora)\b/i },
      { key: "estagiario", pattern: /\b(estagi[áa]rio|trainee|intern|estágio)\b/i },
      { key: "junior", pattern: /\b(junior|júnior|jr\.?|entry\s*level|entry-level)\b/i },
      { key: "senior", pattern: /\b(senior|sênior|sr\.?|especialista)\b/i },
      { key: "pleno", pattern: /\b(analista)\b/i }
    ].freeze

    SALARY_MIDPOINT_THRESHOLDS_BRL = [
      { max: 3500, key: "junior" },
      { max: 7000, key: "pleno" },
      { max: 12_000, key: "senior" },
      { max: 20_000, key: "lead" },
      { max: Float::INFINITY, key: "diretor" }
    ].freeze

    SKILLS_COUNT_THRESHOLDS = [
      { max: 3, key: "junior" },
      { max: 6, key: "pleno" },
      { max: 10, key: "senior" },
      { max: Float::INFINITY, key: "lead" }
    ].freeze

    Result = Struct.new(
      :success?,
      :suggested_seniority,
      :confidence,
      :seniority_source,
      :error,
      keyword_init: true
    )

    def self.call(job:)
      new(job: job).call
    end

    def initialize(job:)
      @job = job
    end

    def call
      return failure("Job is required") if @job.blank?

      if @job.seniority.present?
        key = Wsi::Constants.seniority_key(@job)
        return Result.new(
          success?: true,
          suggested_seniority: key,
          confidence: "high",
          seniority_source: [ "explicit" ],
          error: nil
        )
      end

      scores = Hash.new(0.0)
      sources = []

      title_key = infer_from_title(@job.title)
      if title_key
        scores[title_key] += SIGNAL_WEIGHTS[:title_keywords]
        sources << "title_keywords"
      end

      jd_key = infer_from_text(jd_text_for_inference)
      if jd_key
        scores[jd_key] += SIGNAL_WEIGHTS[:jd_analysis]
        sources << "jd_analysis" unless sources.include?("jd_analysis")
      end

      salary_key = infer_from_salary
      if salary_key
        scores[salary_key] += SIGNAL_WEIGHTS[:salary_range]
        sources << "salary_range"
      end

      skills_key = infer_from_skills_count
      if skills_key
        scores[skills_key] += SIGNAL_WEIGHTS[:skills_complexity]
        sources << "skills_complexity"
      end

      if scores.empty?
        fallback = title_key || "pleno"
        return Result.new(
          success?: true,
          suggested_seniority: fallback,
          confidence: "low",
          seniority_source: sources.presence || [ "default" ],
          error: nil
        )
      end

      winner = scores.max_by { |_, v| v }
      suggested = winner&.first || "pleno"
      conf = confidence_for(scores, suggested, title_key, sources)

      Result.new(
        success?: true,
        suggested_seniority: suggested,
        confidence: conf,
        seniority_source: sources.uniq,
        error: nil
      )
    rescue StandardError => e
      Rails.logger.error("[Wsi::SeniorityResolverService] #{e.class}: #{e.message}")
      failure(e.message)
    end

    private

    def failure(message)
      Result.new(success?: false, suggested_seniority: nil, confidence: nil, seniority_source: [], error: message)
    end

    def jd_text_for_inference
      lia = @job.lia_job_description
      ej = lia.is_a?(Hash) ? (lia["enriched_jd"] || lia[:enriched_jd]) : nil
      if ej.is_a?(Hash) && ej.present?
        text = text_from_enriched_jd_hash(ej)
        return text if text.present?
      end

      parts = [ @job.description ]
      parts += Array(@job.responsibilities) if @job.respond_to?(:responsibilities)
      parts.compact.map(&:to_s).join("\n\n")
    end

    def text_from_enriched_jd_hash(enriched)
      e = enriched.with_indifferent_access
      segments = []
      segments << e[:about_role].to_s if e[:about_role].present?

      if e[:skills_obrigatorias].is_a?(Array)
        e[:skills_obrigatorias].each do |item|
          segments << item.is_a?(Hash) ? (item["name"] || item[:name] || item.values.first).to_s : item.to_s
        end
      end

      comps = e[:competencias_comportamentais]
      if comps.is_a?(Array)
        comps.each do |row|
          next unless row.is_a?(Hash)

          c = row.with_indifferent_access
          name = c[:competencia].presence || c[:name].presence
          segments << name.to_s if name.present?
        end
      end

      segments << join_enriched_lines(e[:responsabilidades])
      segments << join_enriched_lines(e[:requisitos])

      segments.compact.map(&:strip).reject(&:blank?).join("\n\n")
    end

    def join_enriched_lines(value)
      return "" if value.blank?

      value.is_a?(Array) ? value.map(&:to_s).join("\n") : value.to_s
    end

    def infer_from_title(text)
      return nil if text.blank?

      TITLE_CHAIN.each do |rule|
        return rule[:key] if rule[:pattern].match?(text)
      end

      nil
    end

    def infer_from_text(text)
      return nil if text.blank?

      infer_from_title(text)
    end

    def infer_from_salary
      from = @job.salary_from.to_f
      to = @job.salary_to.to_f
      return nil if from <= 0 && to <= 0

      mid = if from.positive? && to.positive?
        (from + to) / 2.0
      elsif from.positive?
        from
      else
        to
      end

      SALARY_MIDPOINT_THRESHOLDS_BRL.each do |row|
        return row[:key] if mid <= row[:max]
      end

      "diretor"
    end

    def infer_from_skills_count
      return nil unless @job.respond_to?(:skill_relationships)

      n = @job.skill_relationships.where(is_deleted: false).count
      return nil if n.zero?

      SKILLS_COUNT_THRESHOLDS.each do |row|
        return row[:key] if n <= row[:max]
      end

      "lead"
    end

    def confidence_for(scores, winner, title_key, sources)
      return "low" if winner == "pleno" && sources == [ "title_keywords" ]

      sorted = scores.values.sort.reverse
      top = sorted[0].to_f
      second = sorted[1].to_f
      gap_ratio = top.positive? ? (top - second) / top : 0.0

      return "high" if gap_ratio >= 0.45 && top >= 0.2 * SIGNAL_WEIGHT_SUM
      return "low" if gap_ratio < 0.15

      "medium"
    end
  end
end
