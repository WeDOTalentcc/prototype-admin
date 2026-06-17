# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::ReportBuilderService do
  include ActiveSupport::Testing::TimeHelpers

  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account, seniority: 2) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:ec) do
    create(
      :evaluation_candidate,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      completed: true,
      score: 7.8,
      wsi_decision: {
        "result" => "APROVADO",
        "confidence" => "alta",
        "decided_at" => Time.current.iso8601
      },
      wsi_red_flags: [],
      wsi_classification: "Excelente",
      wsi_big_five_observed: {}
    )
  end

  let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual", bloom_level: "4") }
  let(:bq) do
    create(
      :question,
      evaluation: evaluation,
      competence_type: "behavioral",
      response_type: "situational",
      ocean_trait: "conscientiousness",
      extra_params: { "trait_weight" => 0.33 },
      bloom_level: "4"
    )
  end

  before do
    create(
      :answer,
      question: tq,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      final_skill_score: 8.0,
      description: ("word " * 40).strip,
      analysis_data: { "wsi" => { "extraction" => { "bloom_demonstrated" => 4 } }, "dreyfus" => { "score" => 4 } }
    )
    create(
      :answer,
      question: bq,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      final_skill_score: 7.5,
      description: ("word " * 40).strip,
      analysis_data: { "wsi" => { "extraction" => { "bloom_demonstrated" => 4, "signals_detected" => %w[a b] } }, "dreyfus" => { "score" => 3 } }
    )
  end

  it "builds a report passing schema validation with 9 sections and gate_checklist" do
    result = described_class.call(evaluation_candidate: ec.reload, persist: false)
    expect(result[:success]).to be true
    report = result[:report]
    expect(Wsi::ReportSchema.validate(report)).to be_empty

    expect(report["sections"]["2"]["gate_checklist"].keys).to include("G1", "G2", "G3", "G4", "G5", "G6")
    s9 = report["sections"]["9"]
    expect(s9["answers_hash"]).to be_present
    expect(s9["report_version"]).to eq(Wsi::ReportBuilderService::REPORT_SCHEMA_VERSION)
    suffix = Wsi::ReportBuilderService::LLM_AUDIT_PROVIDER_VERSION
    expect(s9["llm_jd_enrichment"]).to eq("#{Wsi::JdEnrichmentService::DEFAULT_MODEL} @ #{suffix}")
    expect(s9["llm_interview_question_generation"]).to eq(
      "#{Wsi::InterviewQuestionGeneratorService::DEFAULT_MODEL} @ #{suffix}"
    )
    expect(s9["llm_response_evaluation"]).to eq("#{Wsi::ResponseExtractorService::DEFAULT_MODEL} @ #{suffix}")
  end
end
