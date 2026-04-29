# frozen_string_literal: true

module Evaluations
  class ScoreCalculatorService
    Result = Struct.new(:success?, :analysis_data, :final_skill_score, :error, keyword_init: true)

    def self.call(answer:)
      new(answer: answer).call
    end

    def initialize(answer:)
      @answer = answer
      @question = answer.question
    end

    def call
      return failure("Answer not found") unless @answer
      return failure("Question is required to score answer") unless @question
      return skip_eligibility_scoring if @question.competence_type.to_s == "eligibility"

      response_text = @answer.description.to_s
      masked = Wsi::PiiMasker.call(text: response_text)
      extractor_result = Wsi::ResponseExtractorService.call(answer: @answer, masked_response_text: masked)
      return failure(extractor_result.error) unless extractor_result.success?

      extraction = extractor_result.data.deep_symbolize_keys
      track_injection_attempt!(extraction)

      question_body = [ @question.title, @question.description ].compact.join("\n\n")
      cbi = CbiEvaluator.new(response_text: response_text, question_text: question_body).call

      if injection_override?(extraction, cbi)
        return persist_zero_score(extraction, cbi, masked)
      end

      self_declaration = parse_self_declaration(normalized_comments_response)
      bloom_e = Wsi::BloomLevels.from_question(@question.bloom_level)&.to_i
      bloom_e = 3 if bloom_e.blank?
      bloom_d = extraction[:bloom_demonstrated].to_i
      bloom_d = bloom_e if bloom_d <= 0

      drey_e = @question.dreyfus_target.to_i
      drey_e = 3 if drey_e <= 0
      drey_d = extraction[:dreyfus_demonstrated].to_i
      drey_d = drey_e if drey_d <= 0

      bloom_align = Evaluations::WsiLayerThreeScorer.bloom_alignment(bloom_e, bloom_d)
      expected_signals = expected_trait_signals

      competence_behavioral = @question.competence_type.to_s == "behavioral"

      score_bruto = if competence_behavioral
        behavioral_score_bruto(cbi, extraction, bloom_align, expected_signals)
      else
        technical_score_bruto(self_declaration, extraction, bloom_align)
      end

      adj = Evaluations::WsiLayerThreeScorer.adjustments_84(
        extraction: extraction,
        bloom_e: bloom_e,
        bloom_d: bloom_d,
        drey_e: drey_e,
        drey_d: drey_d,
        expected_signals: expected_signals,
        competence_behavioral: competence_behavioral
      )

      structural = Evaluations::WsiLayerThreeScorer.structural_sum(cbi)
      final_skill_score = (score_bruto + adj + structural).clamp(0.0, 10.0).round(2)

      analysis_data = build_analysis_data(
        extraction: extraction,
        cbi: cbi,
        self_declaration: self_declaration,
        score_bruto: score_bruto,
        adjustments_84: adj,
        structural: structural,
        final_skill_score: final_skill_score,
        bloom_e: bloom_e,
        bloom_d: bloom_d,
        drey_e: drey_e,
        drey_d: drey_d,
        masked_used_for_llm: masked != response_text
      )

      @answer.update!(
        analysis_data: analysis_data,
        final_skill_score: final_skill_score
      )

      Result.new(success?: true, analysis_data: analysis_data, final_skill_score: final_skill_score, error: nil)
    rescue StandardError => e
      Rails.logger.error("❌ [ScoreCalculatorService] Error scoring answer #{@answer&.id}: #{e.class} - #{e.message}")
      failure(e.message)
    end

    private

    def technical_score_bruto(self_declaration, extraction, bloom_align)
      autodecl = self_declaration.to_f.clamp(1.0, 5.0) / 5.0
      specificity = extraction[:specificity_score].to_f.clamp(1.0, 10.0) / 10.0
      (autodecl * 0.35 + specificity * 0.40 + bloom_align * 0.25) * 10.0
    end

    def behavioral_score_bruto(cbi, extraction, bloom_align, expected_signals)
      star_norm = cbi[:star_score].to_f.clamp(0.0, 1.0)
      trait_norm = Evaluations::WsiLayerThreeScorer.trait_signals_norm(
        extraction[:trait_signals_detected],
        expected_signals
      )
      (star_norm * 0.35 + trait_norm * 0.40 + bloom_align * 0.25) * 10.0
    end

    def injection_override?(extraction, cbi)
      return true if cbi[:injection_detected]
      return true if extraction[:authenticity_concern].to_s == "prompt_injection_attempt"

      false
    end

    def persist_zero_score(extraction, cbi, masked)
      rationale = stored_rationale_from(extraction)
      storage_extraction = sanitize_extraction_for_storage(extraction)
      analysis_data = {
        wsi: {
          extraction: storage_extraction.deep_stringify_keys,
          cbi: cbi,
          injection_override: true,
          masked_response: masked != @answer.description.to_s
        },
        rationale: rationale,
        scoring: {
          final_skill_score: 0.0,
          self_declaration_score: parse_self_declaration(normalized_comments_response).round(2)
        }
      }

      @answer.update!(analysis_data: analysis_data, final_skill_score: 0.0)
      Result.new(success?: true, analysis_data: analysis_data, final_skill_score: 0.0, error: nil)
    end

    def track_injection_attempt!(extraction)
      return unless extraction[:authenticity_concern].to_s == "prompt_injection_attempt"

      @answer.increment!(:injection_attempt_count)
      ec = EvaluationCandidate.find_by(evaluation_id: @answer.evaluation_id, candidate_id: @answer.candidate_id)
      return unless ec

      total = Answer.where(evaluation_id: @answer.evaluation_id, candidate_id: @answer.candidate_id).sum(:injection_attempt_count)
      ec.update_column(:g2_gate_triggered, true) if total >= 2
    end

    def expected_trait_signals
      meta = @question.wsi_metadata.is_a?(Hash) ? @question.wsi_metadata : {}
      signals = meta["expected_signals"] || meta[:expected_signals]
      return signals if signals.is_a?(Array) && signals.present?

      trait = @question.ocean_trait.to_s
      return [ "behavioral:#{trait}" ] if trait.present?

      []
    end

    def normalized_comments_response
      raw = @answer.comments_response
      return raw.deep_symbolize_keys if raw.is_a?(Hash)
      return {} if raw.blank?

      JSON.parse(raw.to_s).deep_symbolize_keys
    rescue JSON::ParserError
      {}
    end

    def parse_self_declaration(comments)
      explicit = @answer.self_declaration_score
      if explicit.present?
        return explicit.to_f.clamp(1.0, 5.0).round(2)
      end

      score = comments[:score] || comments.dig(:evaluation, :score)
      return 3.0 if score.blank?

      numeric = score.to_f
      return (numeric * 5.0).clamp(0.0, 5.0).round(2) if numeric <= 1.0

      numeric.clamp(0.0, 5.0).round(2)
    end

    def skip_eligibility_scoring
      @answer.update!(
        analysis_data: { "wsi" => { "skipped" => true, "reason" => "eligibility" }, "rationale" => [] },
        final_skill_score: nil
      )
      Result.new(success?: true, analysis_data: @answer.analysis_data, final_skill_score: nil, error: nil)
    end

    def build_analysis_data(extraction:, cbi:, self_declaration:, score_bruto:, adjustments_84:, structural:, final_skill_score:, bloom_e:, bloom_d:, drey_e:, drey_d:, masked_used_for_llm:)
      legacy_bloom = BloomClassifier.new(response_text: @answer.description.to_s).call
      legacy_dreyfus = DreyfusScorer.new(
        response_text: @answer.description.to_s,
        self_declaration_score: self_declaration
      ).call
      big_five = BigFiveAnalyzer.analyze(@answer.description.to_s)
      rationale = stored_rationale_from(extraction)
      storage_extraction = sanitize_extraction_for_storage(extraction)

      {
        wsi: {
          extraction: storage_extraction.deep_stringify_keys,
          cbi: cbi.deep_stringify_keys,
          layer3: {
            score_bruto: score_bruto.round(4),
            adjustments_84: adjustments_84.round(4),
            structural: structural.round(4)
          },
          masked_used_for_llm: masked_used_for_llm
        },
        bloom: {
          level: legacy_bloom.level,
          score: bloom_d,
          confidence: legacy_bloom.confidence,
          expected_level: @question.bloom_level,
          demonstrated: bloom_d,
          expected_numeric: bloom_e
        },
        dreyfus: {
          level: legacy_dreyfus.level,
          score: drey_d,
          confidence: legacy_dreyfus.confidence,
          target_level: @question.dreyfus_target,
          demonstrated: drey_d,
          expected_numeric: drey_e
        },
        big_five: {
          o: big_five[:o],
          c: big_five[:c],
          e: big_five[:e],
          a: big_five[:a],
          n: big_five[:n],
          confidence: big_five[:confidence],
          target_trait: @question.ocean_trait
        },
        cbi_star: cbi[:star].merge(
          completeness_score: cbi[:completeness_score],
          star_score: cbi[:star_score]
        ),
        scoring: {
          self_declaration_score: self_declaration.round(2),
          score_bruto: score_bruto.round(2),
          adjustments_84: adjustments_84.round(2),
          structural: structural.round(2),
          final_skill_score: final_skill_score
        },
        rationale: rationale
      }
    end

    def stored_rationale_from(extraction)
      Wsi::RationaleEvidenceBuilder.call(
        extraction: extraction,
        source_text: @answer.description.to_s
      )
    end

    def sanitize_extraction_for_storage(extraction)
      extraction.deep_dup.except(:rationale, "rationale")
    end

    def failure(message)
      Result.new(success?: false, analysis_data: {}, final_skill_score: nil, error: message)
    end
  end
end
