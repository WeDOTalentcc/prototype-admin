# frozen_string_literal: true

module Wsi
  class RedFlagDetector
    def self.call(evaluation_candidate:)
      new(evaluation_candidate: evaluation_candidate).call
    end

    def initialize(evaluation_candidate:)
      @evaluation_candidate = evaluation_candidate
    end

    def call
      flags = []
      dimensions = Evaluations::WsiDimensionScores.call(evaluation_candidate: @evaluation_candidate)
      answers = dimensions[:answers]
      return [] if answers.blank?

      inflation_n = answers.count { |a| inflation_detected?(a) }
      flags << rf01(inflation_n) if inflation_n.positive? && inflation_n < 3

      bloom_gap_n = answers.count { |a| bloom_gap?(a) }
      flags << rf02(bloom_gap_n) if bloom_gap_n >= 3

      dreyfus_gaps = dreyfus_skill_gap_count(answers)
      flags << rf03(dreyfus_gaps) if dreyfus_gaps >= 2

      tec = dimensions[:technical].to_f
      comp = dimensions[:behavioral].to_f
      flags << rf04(tec, comp) if (tec - comp).abs > 2.0

      flags << rf05(answers) if star_result_missing_ratio(answers) >= 0.5

      flags << rf06(answers) if short_mid_length_count(answers) >= 3

      flags << rf07 if top_trait_soft_gap?

      flags << rf08(answers) if answers.any? { |a| response_inauthentic?(a) }

      flags.compact
    end

    private

    def rf01(inflation_n)
      {
        code: "RF-01",
        level: "medio",
        description: "Inflation signals in #{inflation_n} response(s), below systematic threshold."
      }
    end

    def rf02(bloom_gap_n)
      {
        code: "RF-02",
        level: "alto",
        description: "Bloom demonstrated below expected in #{bloom_gap_n} response(s)."
      }
    end

    def rf03(dreyfus_gaps)
      {
        code: "RF-03",
        level: "alto",
        description: "Dreyfus demonstrated below expected in #{dreyfus_gaps} skill area(s)."
      }
    end

    def rf04(tec, comp)
      {
        code: "RF-04",
        level: "medio",
        description: "Technical vs behavioral asymmetry (#{tec.round(2)} vs #{comp.round(2)})."
      }
    end

    def rf05(answers)
      {
        code: "RF-05",
        level: "medio",
        description: "STAR result component missing in #{star_result_missing_ratio(answers) * 100}% of responses."
      }
    end

    def rf06(answers)
      {
        code: "RF-06",
        level: "medio",
        description: "Consistent mid-length answers (30-60 words) in #{short_mid_length_count(answers)} responses."
      }
    end

    def rf07
      {
        code: "RF-07",
        level: "alto",
        description: "Top-ranked Big Five trait materially below requirement."
      }
    end

    def rf08(answers)
      {
        code: "RF-08",
        level: "alto",
        description: "Authenticity concern flagged in at least one response."
      }
    end

    def inflation_detected?(answer)
      ext = extraction_hash(answer)
      ActiveModel::Type::Boolean.new.cast(ext[:inflation_detected] || ext["inflation_detected"])
    end

    def bloom_gap?(answer)
      ext = extraction_hash(answer)
      bd = ext[:bloom_demonstrated].to_i
      return false if bd <= 0

      be = bloom_expected_numeric(answer)
      bd < be
    end

    def bloom_expected_numeric(answer)
      q = answer.question
      return 3 if q.blank?

      n = Wsi::BloomLevels.from_question(q.bloom_level)&.to_i
      (n && n.nonzero?) || 3
    end

    def dreyfus_skill_gap_count(answers)
      technical_answers = answers.select do |a|
        ct = a.question&.competence_type.to_s
        ct != "behavioral" && ct != "eligibility"
      end

      technical_answers.group_by(&:question_id).count do |_qid, group|
        group.any? { |a| dreyfus_gap?(a) }
      end
    end

    def dreyfus_gap?(answer)
      ad = answer.analysis_data
      return false unless ad.is_a?(Hash)

      d = ad["dreyfus"] || ad[:dreyfus]
      return false unless d.is_a?(Hash)

      exp = d["expected_numeric"] || d[:expected_numeric] || answer.question&.dreyfus_target.to_i
      dem = d["demonstrated"] || d[:demonstrated] || d["score"] || d[:score]
      exp = exp.to_i
      dem = dem.to_i
      return false if exp <= 0 || dem <= 0

      dem < exp
    end

    def star_result_missing_ratio(answers)
      relevant = answers.reject { |a| a.question&.competence_type == "eligibility" }
      return 0.0 if relevant.blank?

      missing = relevant.count { |a| !star_result_present?(a) }
      missing.to_f / relevant.size
    end

    def star_result_present?(answer)
      ext = extraction_hash(answer)
      star = ext[:star_components] || ext["star_components"]
      if star.is_a?(Hash)
        v = star[:result] || star["result"]
        return ActiveModel::Type::Boolean.new.cast(v)
      end

      ad = answer.analysis_data
      return true unless ad.is_a?(Hash)

      cbi = ad["cbi_star"] || ad[:cbi_star]
      return true unless cbi.is_a?(Hash)

      v = cbi[:result] || cbi["result"]
      return true if v.nil?

      ActiveModel::Type::Boolean.new.cast(v)
    end

    def short_mid_length_count(answers)
      answers.count do |a|
        next if a.question&.competence_type == "eligibility"

        n = word_count(a.description)
        n >= 30 && n <= 60
      end
    end

    def word_count(text)
      text.to_s.split(/\s+/).map(&:strip).reject(&:blank?).size
    end

    def top_trait_soft_gap?
      job = @evaluation_candidate.job
      return false if job.blank?

      ranking = job.wsi_jd_trait_ranking
      return false unless ranking.is_a?(Hash)

      rows = Array(ranking["big_five_ranking"]).select { |row| row.is_a?(Hash) }
      first = rows.min_by { |row| row["rank"].to_i }
      return false unless first.is_a?(Hash)

      trait = first["trait"].to_s
      return false if trait.blank?

      observed = @evaluation_candidate.wsi_big_five_observed
      return false unless observed.is_a?(Hash)

      cand = observed.dig("candidate_big_five_observed", trait)
      return false unless cand.is_a?(Hash)

      req = cand["score_required"] || cand[:score_required]
      dem = cand["score_demonstrated"] || cand[:score_demonstrated]
      return false if req.nil? || dem.nil?

      dem.to_i < (req.to_i - 15)
    end

    def response_inauthentic?(answer)
      ext = extraction_hash(answer)
      auth = ext[:response_authentic]
      auth = ext["response_authentic"] if auth.nil?
      return true if ActiveModel::Type::Boolean.new.cast(auth) == false

      false
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
