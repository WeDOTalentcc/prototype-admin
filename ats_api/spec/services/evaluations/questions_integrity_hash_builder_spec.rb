# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluations::QuestionsIntegrityHashBuilder do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }

  it "returns a 64-char hex digest" do
    create(:question, evaluation: evaluation, position: 1)
    hex = described_class.call(evaluation_id: evaluation.id)
    expect(hex).to match(/\A[0-9a-f]{64}\z/)
  end

  it "is deterministic for the same questions" do
    create(:question, evaluation: evaluation, position: 1, title: "Fixed title")
    a = described_class.call(evaluation_id: evaluation.id)
    b = described_class.call(evaluation_id: evaluation.id)
    expect(a).to eq(b)
  end

  it "changes when a question title changes" do
    q = create(:question, evaluation: evaluation, position: 1, title: "A")
    before = described_class.call(evaluation_id: evaluation.id)
    q.update!(title: "B")
    after = described_class.call(evaluation_id: evaluation.id)
    expect(after).not_to eq(before)
  end

  it "hashes an empty question set" do
    hex = described_class.call(evaluation_id: evaluation.id)
    expect(hex).to match(/\A[0-9a-f]{64}\z/)
    expect(hex).to eq(Digest::SHA256.hexdigest(JSON.generate([])))
  end
end
