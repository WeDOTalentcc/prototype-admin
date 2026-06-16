# frozen_string_literal: true

module Wsi
  class GapAnalyzer
    EXPECTED_SCORE = 7.0

    GapItem = Struct.new(
      :kind,
      :label,
      :score_obtained,
      :score_expected,
      :gap_score_delta,
      :peso_dimensao,
      :severidade,
      :bloom_esperado,
      :bloom_demonstrado,
      :tipo,
      keyword_init: true
    )

    def self.call(evaluation_candidate:, answers: nil)
      new(evaluation_candidate: evaluation_candidate, answers: answers).call
    end

    def initialize(evaluation_candidate:, answers: nil)
      @evaluation_candidate = evaluation_candidate
      @answers_override = answers
    end

    def call
      answers = @answers_override || scored_answers
      items = answers.filter_map { |a| build_item(a) }
      strengths = items.select { |i| i.severidade == :ponto_forte }
      gaps = items.reject { |i| i.severidade == :ponto_forte }

      strengths_sorted = strengths.sort_by { |i| -i.score_obtained.to_f }.first(3)
      gaps_sorted = sort_gaps(gaps).first(4)

      {
        strengths: strengths_sorted,
        gaps: gaps_sorted,
        top_gaps_for_llm: sort_gaps(gaps).first(3)
      }
    end

    private

    def scored_answers
      @evaluation_candidate.answers.includes(:question).where.not(final_skill_score: nil)
    end

    def sort_gaps(gaps)
      severidade_rank = { alto: 3, medio: 2, baixo: 1 }
      gaps.sort_by do |g|
        [
          -severidade_rank.fetch(g.severidade, 0),
          -g.peso_dimensao.to_f,
          -g.gap_score_delta.to_f
        ]
      end
    end

    def build_item(answer)
      q = answer.question
      return nil if q.blank?
      return nil if q.competence_type == "eligibility"

      score = answer.final_skill_score.to_f
      tipo = q.competence_type == "behavioral" ? "comportamental" : "tecnico"
      peso = dimension_weight(answer, tipo)
      bloom_e = bloom_expected_numeric(answer)
      bloom_d = bloom_demonstrated_numeric(answer)
      label = behavior_label(answer) || q.title.to_s.presence || "competencia"
      delta = EXPECTED_SCORE - score
      severidade = classify_severity(score: score, peso: peso, bloom_e: bloom_e, bloom_d: bloom_d, answer: answer)

      GapItem.new(
        kind: severidade == :ponto_forte ? :strength : :gap,
        label: label,
        score_obtained: score.round(2),
        score_expected: EXPECTED_SCORE,
        gap_score_delta: delta.round(2),
        peso_dimensao: peso,
        severidade: severidade,
        bloom_esperado: bloom_e,
        bloom_demonstrado: bloom_d,
        tipo: tipo
      )
    end

    def classify_severity(score:, peso:, bloom_e:, bloom_d:, answer:)
      if score >= 7.0 && sufficient_signals?(answer)
        return :ponto_forte
      end

      if score < 4.0 && peso >= 0.20
        return :alto
      end

      if score >= 4.0 && score <= 5.9
        return :medio
      end

      if bloom_e.positive? && bloom_d.positive? && bloom_d == bloom_e - 1
        return :medio
      end

      if bloom_d.positive? && bloom_e.positive? && bloom_d < bloom_e - 1
        return :medio
      end

      if score >= 6.0 && score < 7.0 && !sufficient_signals?(answer)
        return :baixo
      end

      return :medio if score < 6.0

      :baixo
    end

    def sufficient_signals?(answer)
      ext = extraction_hash(answer)
      sig = ext[:signals_detected] || ext["signals_detected"]
      return true if sig.is_a?(Array) && sig.size >= 2
      return true if score_from_analysis(answer) >= 6.5

      false
    end

    def score_from_analysis(answer)
      answer.final_skill_score.to_f
    end

    def dimension_weight(answer, tipo)
      if tipo == "comportamental"
        ep = answer.question&.extra_params
        return 0.33 unless ep.is_a?(Hash)

        w = ep["trait_weight"] || ep[:trait_weight]
        w.present? ? w.to_f.clamp(0.0, 1.0) : 0.33
      else
        0.35
      end
    end

    def behavior_label(answer)
      t = answer.question&.ocean_trait
      return nil if t.blank?

      Wsi::OceanTraitCanonical.to_api(t).to_s
    end

    def bloom_expected_numeric(answer)
      n = Wsi::BloomLevels.from_question(answer.question&.bloom_level)&.to_i
      (n && n.nonzero?) || 3
    end

    def bloom_demonstrated_numeric(answer)
      ext = extraction_hash(answer)
      v = ext[:bloom_demonstrated] || ext["bloom_demonstrated"]
      v.to_i
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
