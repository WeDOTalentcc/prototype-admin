# frozen_string_literal: true

module Wsi
  class ReportBuilderService
    REPORT_SCHEMA_VERSION = "1"
    LLM_AUDIT_PROVIDER_VERSION = "gemini-generative-language-api"

    def self.call(evaluation_candidate:, persist: true)
      new(evaluation_candidate: evaluation_candidate, persist: persist).call
    end

    def initialize(evaluation_candidate:, persist: true)
      @ec = evaluation_candidate
      @persist = persist
    end

    def call
      return failure("evaluation_candidate missing") if @ec.blank?
      return failure("wsi_decision not present") unless @ec.wsi_decision.is_a?(Hash) && @ec.wsi_decision["result"].present?

      dimensions = Evaluations::WsiDimensionScores.call(evaluation_candidate: @ec)
      answers = dimensions[:answers]
      return failure("no scored answers") if answers.blank?

      gap_result = GapAnalyzer.call(evaluation_candidate: @ec, answers: answers)
      triage_questions = answers.map { |a| a.question&.title.to_s }.compact
      interview = InterviewQuestionGeneratorService.call(
        evaluation_candidate: @ec,
        top_gaps: gap_result[:top_gaps_for_llm],
        top_strengths: gap_result[:strengths],
        triage_question_texts: triage_questions,
        persist: false
      )

      report = build_report_hash(dimensions, answers, gap_result, interview)
      Wsi::ReportSchema.validate!(report)

      if @persist
        now = Time.current
        @ec.update_columns(
          f11_report_json: report,
          report_generated_at: now,
          report_version: REPORT_SCHEMA_VERSION,
          f11_report_stale: false,
          updated_at: now
        )
      end

      { success: true, report: report, error: nil }
    rescue ArgumentError => e
      failure(e.message)
    rescue StandardError => e
      Rails.logger.error("❌ [ReportBuilderService] #{e.class} #{e.message}")
      failure(e.message)
    end

    private

    def failure(msg)
      { success: false, report: nil, error: msg }
    end

    def build_report_hash(dimensions, answers, gap_result, interview)
      job = @ec.job
      candidate = @ec.candidate
      decision = @ec.wsi_decision.deep_stringify_keys
      dist = Evaluations::WsiDimensionScores.distribution_weights(evaluation_candidate: @ec)

      answers_hash = Evaluations::AnswersIntegrityHashBuilder.call(
        evaluation_id: @ec.evaluation_id,
        candidate_id: @ec.candidate_id
      )

      generated_at = Time.current.iso8601

      {
        "report_id" => @ec.uid,
        "generated_at" => generated_at,
        "methodology_version" => "2.0",
        "report_version" => REPORT_SCHEMA_VERSION,
        "sections" => {
          "1" => section_1(job, candidate, @ec),
          "2" => section_2(dimensions, decision),
          "3" => section_3(dimensions, dist),
          "4" => section_4(job, answers),
          "5" => section_5(job, @ec),
          "6" => section_6(answers),
          "7" => section_7(gap_result, interview),
          "8" => section_8(dimensions, @ec),
          "9" => section_9(answers_hash, generated_at)
        }
      }
    end

    def section_1(job, candidate, ec)
      mode = ec.evaluation&.questions&.where(is_deleted: false)&.count.to_i <= 7 ? "compact_7q" : "full_12q"
      jd_q = nil

      {
        "job_title" => job&.title,
        "company" => job&.company&.name,
        "seniority" => job&.seniority,
        "screening_mode" => mode,
        "jd_quality_score" => jd_q,
        "candidate_name" => candidate&.name,
        "channel" => ec.chatbot_channel,
        "screening_started_at" => ec.created_at&.iso8601,
        "screening_completed_at" => ec.updated_at&.iso8601,
        "evaluation_uid" => ec.uid
      }
    end

    def section_2(dimensions, decision)
      {
        "wsi_final" => dimensions[:final].to_f.round(2),
        "decision" => decision,
        "red_flags" => @ec.wsi_red_flags,
        "gate_checklist" => GateChecklist.call(evaluation_candidate: @ec)
      }
    end

    def section_3(dimensions, dist)
      {
        "wsi_technical" => dimensions[:technical].to_f.round(4),
        "wsi_behavioral" => dimensions[:behavioral].to_f.round(4),
        "wsi_final" => dimensions[:final].to_f.round(2),
        "weight_technical_pct" => (dist[:technical].to_f * 100).round(1),
        "weight_behavioral_pct" => (dist[:behavioral].to_f * 100).round(1)
      }
    end

    def section_4(job, answers)
      rows = []
      tech = answers.select { |a| a.question&.competence_type.to_s == "technical" }
      tech.each do |a|
        q = a.question
        ext = extraction_hash(a)
        d_dem = a.analysis_data.is_a?(Hash) ? (a.analysis_data.dig("dreyfus", "score") || a.analysis_data.dig(:dreyfus, :score)) : nil
        rows << {
          "skill" => q&.title,
          "critical" => critical_question?(q),
          "score" => a.final_skill_score.to_f.round(2),
          "bloom_expected" => q&.bloom_level,
          "bloom_demonstrated" => ext[:bloom_demonstrated],
          "dreyfus_demonstrated" => d_dem
        }
      end

      { "technical_cross" => rows }
    end

    def section_5(job, ec)
      obs = ec.wsi_big_five_observed.is_a?(Hash) ? ec.wsi_big_five_observed["candidate_big_five_observed"] : {}
      rows = []
      (obs || {}).each do |trait, data|
        next unless data.is_a?(Hash)

        rows << {
          "trait" => trait,
          "score_required" => data["score_required"],
          "score_demonstrated" => data["score_demonstrated"],
          "gap" => data["gap"],
          "status" => data["status"]
        }
      end

      { "big_five_cross" => rows }
    end

    def section_6(answers)
      items = answers.reject { |a| a.question&.competence_type == "eligibility" }.map do |a|
        q = a.question
        ext = extraction_hash(a)
        {
          "question_index" => q&.position,
          "competence_type" => q&.competence_type,
          "label" => q&.title,
          "score" => a.final_skill_score.to_f.round(2),
          "question_text" => q&.title,
          "star" => ext[:star_components] || ext["star_components"],
          "bloom_demonstrated" => ext[:bloom_demonstrated],
          "key_quote" => ext[:key_quote] || ext["key_quote"],
          "signals_detected" => ext[:signals_detected] || ext["signals_detected"]
        }
      end

      { "per_question" => items }
    end

    def section_7(gap_result, interview)
      strengths = gap_result[:strengths].map { |g| gap_item_to_h(g) }
      gaps = gap_result[:gaps].map { |g| gap_item_to_h(g) }

      {
        "strengths" => strengths,
        "gaps" => gaps,
        "interview_questions" => interview[:interview_questions],
        "interview_generation" => {
          "llm_fallback" => interview[:llm_fallback],
          "metadata" => interview[:generation_metadata]
        }
      }
    end

    def section_8(dimensions, ec)
      {
        "wsi_final" => dimensions[:final].to_f.round(2),
        "classification" => ec.wsi_classification
      }
    end

    def section_9(answers_hash, generated_at)
      {
        "screening_uid" => @ec.uid,
        "methodology_version_label" => "WSI v2.0",
        "evaluation_temperature" => 0.0,
        "generated_at" => generated_at,
        "answers_hash" => answers_hash,
        "report_version" => REPORT_SCHEMA_VERSION,
        "llm_jd_enrichment" => llm_model_line(Llm::ClientFactory.chat_model),
        "llm_interview_question_generation" => llm_model_line(Llm::ClientFactory.chat_model),
        "llm_response_evaluation" => llm_model_line(Llm::ClientFactory.fast_model)
      }
    end

    def llm_model_line(model_id)
      "#{model_id} @ #{LLM_AUDIT_PROVIDER_VERSION}"
    end

    def gap_item_to_h(g)
      return g unless g.is_a?(GapAnalyzer::GapItem)

      {
        "label" => g.label,
        "tipo" => g.tipo,
        "score_obtained" => g.score_obtained,
        "score_expected" => g.score_expected,
        "gap_score_delta" => g.gap_score_delta,
        "peso_dimensao" => g.peso_dimensao,
        "severidade" => g.severidade.to_s.upcase,
        "bloom_esperado" => g.bloom_esperado,
        "bloom_demonstrado" => g.bloom_demonstrado
      }
    end

    def critical_question?(question)
      return false if question.blank?

      meta = question.wsi_metadata.is_a?(Hash) ? question.wsi_metadata : {}
      ActiveModel::Type::Boolean.new.cast(meta["critical"] || meta[:critical])
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
