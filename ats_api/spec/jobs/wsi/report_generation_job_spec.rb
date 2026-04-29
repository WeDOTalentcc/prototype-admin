# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::ReportGenerationJob do
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
      score: 7.0,
      wsi_decision: { "result" => "APROVADO", "confidence" => "alta" },
      wsi_red_flags: []
    )
  end

  let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }

  before do
    create(
      :answer,
      question: tq,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      final_skill_score: 7.0,
      description: ("word " * 40).strip,
      analysis_data: { "dreyfus" => { "score" => 3 } }
    )
    ec.reload
  end

  it "persists f11_report_json for the evaluation candidate" do
    described_class.new.perform(ec.id, account.id)
    ec.reload
    expect(ec.f11_report_json).to be_present
    expect(ec.f11_report_stale).to be false
  end
end
