# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::InterviewQuestionGeneratorService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:ec) do
    create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, account: account, user: user, job: job)
  end

  let(:gap) do
    Wsi::GapAnalyzer::GapItem.new(
      kind: :gap,
      label: "python",
      score_obtained: 3.2,
      score_expected: 7.0,
      gap_score_delta: 3.8,
      peso_dimensao: 0.35,
      severidade: :alto,
      bloom_esperado: 4,
      bloom_demonstrado: 2,
      tipo: "tecnico"
    )
  end

  it "returns two interview questions in test env without calling Gemini" do
    allow(Rails.env).to receive(:test?).and_return(true)
    result = described_class.call(evaluation_candidate: ec, top_gaps: [ gap ], triage_question_texts: [ "Q1" ])
    expect(result[:success]).to be true
    expect(result[:interview_questions].size).to eq(2)
    expect(result[:interview_questions].first["question_text"]).to be_present
  end

  it "persists section 7 interview_questions into f11_report_json when persist is true" do
    allow(Rails.env).to receive(:test?).and_return(false)
    client = instance_double(GeminiClient)
    allow(GeminiClient).to receive(:new).and_return(client)
    allow(client).to receive(:chat).and_return(
      "choices" => [
        {
          "message" => {
            "content" => {
              "interview_questions" => [
                { "question_number" => 1, "question_text" => "Question one for the role?" },
                { "question_number" => 2, "question_text" => "Question two for the role?" }
              ]
            }.to_json
          }
        }
      ]
    )

    described_class.call(
      evaluation_candidate: ec,
      top_gaps: [ gap ],
      triage_question_texts: [ "Q1" ],
      persist: true
    )

    ec.reload
    expect(ec.f11_report_json.dig("sections", "7", "interview_questions").size).to eq(2)
    expect(ec.f11_report_json.dig("sections", "7", "interview_questions", 0, "question_text")).to eq("Question one for the role?")
    expect(ec.f11_report_stale).to be false
  end
end
