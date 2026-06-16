# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluations::AnswersIntegrityHashBuilder do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }
  let(:candidate) { create(:candidate, account: account) }

  it "returns a 64-char hex digest" do
    q = create(:question, evaluation: evaluation, position: 1)
    create(
      :answer,
      question: q,
      evaluation: evaluation,
      candidate: candidate,
      user: user,
      account: account,
      job: job,
      description: "A"
    )
    hex = described_class.call(evaluation_id: evaluation.id, candidate_id: candidate.id)
    expect(hex).to match(/\A[0-9a-f]{64}\z/)
  end

  it "is deterministic for the same answers" do
    q = create(:question, evaluation: evaluation, position: 1)
    create(
      :answer,
      question: q,
      evaluation: evaluation,
      candidate: candidate,
      user: user,
      account: account,
      job: job,
      description: "Same",
      self_declaration_score: 4,
      eligibility_answer: nil
    )
    a = described_class.call(evaluation_id: evaluation.id, candidate_id: candidate.id)
    b = described_class.call(evaluation_id: evaluation.id, candidate_id: candidate.id)
    expect(a).to eq(b)
  end
end
