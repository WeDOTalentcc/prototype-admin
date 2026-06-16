# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::GapAnalyzer do
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
      job: job
    )
  end

  def extraction(bloom_demonstrated:, signals: nil)
    ex = { "bloom_demonstrated" => bloom_demonstrated }
    ex["signals_detected"] = signals if signals
    { "wsi" => { "extraction" => ex } }
  end

  it "classifies ALTO when score < 4.0 and peso_dimensao >= 20%" do
    q = create(
      :question,
      evaluation: evaluation,
      competence_type: "behavioral",
      response_type: "situational",
      ocean_trait: "conscientiousness",
      extra_params: { "trait_weight" => 0.25 },
      bloom_level: "4"
    )
    a = create(
      :answer,
      question: q,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      final_skill_score: 3.5,
      analysis_data: extraction(bloom_demonstrated: 3, signals: %w[a b])
    )

    result = described_class.call(evaluation_candidate: ec, answers: [ a ])
    gap = result[:gaps].find { |g| g.severidade == :alto }
    expect(gap).to be_present
    expect(gap.peso_dimensao).to eq(0.25)
  end

  it "classifies MEDIO when bloom_demonstrado == bloom_esperado - 1" do
    q = create(
      :question,
      evaluation: evaluation,
      competence_type: "technical",
      response_type: "contextual",
      bloom_level: "5",
      ocean_trait: nil
    )
    a = create(
      :answer,
      question: q,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      final_skill_score: 6.5,
      analysis_data: extraction(bloom_demonstrated: 4)
    )

    result = described_class.call(evaluation_candidate: ec, answers: [ a ])
    gap = result[:gaps].first
    expect(gap.severidade).to eq(:medio)
  end

  it "limits strengths to 3 and gaps to 4" do
    questions = 8.times.map do |i|
      create(
        :question,
        evaluation: evaluation,
        competence_type: "technical",
        response_type: "contextual",
        position: i,
        bloom_level: "3"
      )
    end
    answers = questions.map do |q|
      create(
        :answer,
        question: q,
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        job: job,
        final_skill_score: 3.0,
        analysis_data: extraction(bloom_demonstrated: 2)
      )
    end

    result = described_class.call(evaluation_candidate: ec, answers: answers)
    expect(result[:strengths].size).to be <= 3
    expect(result[:gaps].size).to be <= 4
  end
end
