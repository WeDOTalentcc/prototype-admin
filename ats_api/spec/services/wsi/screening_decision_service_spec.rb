# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::ScreeningDecisionService do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account, seniority: 2) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:long_text) { ("word " * 40).strip }

  let(:evaluation_candidate) do
    create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, account: account, user: user, job: job)
  end

  let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }
  let(:bq) { create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational") }

  def answer_for(question:, score:)
    create(
      :answer,
      question: question,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      description: long_text,
      final_skill_score: score,
      analysis_data: { "dreyfus" => { "score" => 4 } }
    )
  end

  it "returns APROVADO with alta confidence when thresholds met and no gates" do
    answer_for(question: tq, score: 8.0)
    answer_for(question: bq, score: 8.0)

    result = described_class.call(evaluation_candidate: evaluation_candidate)
    expect(result[:result]).to eq("APROVADO")
    expect(result[:confidence]).to eq("alta")
    expect(result[:human_review_required]).to be false
    expect(result[:gate_triggered]).to be_nil
  end

  it "returns REPROVADO with gap_trait_critico when top-1 trait shortfall > 20 and WSI final in review band" do
    job.update_column(
      :wsi_jd_trait_ranking,
      { "big_five_ranking" => [ { "rank" => 1, "trait" => "openness", "score" => 50 } ] }
    )
    evaluation_candidate.update_column(
      :wsi_big_five_observed,
      {
        "candidate_big_five_observed" => {
          "openness" => { "score_required" => 80, "score_demonstrated" => 55 }
        }
      }
    )

    answer_for(question: tq, score: 6.5)
    answer_for(question: bq, score: 6.5)

    result = described_class.call(evaluation_candidate: evaluation_candidate)
    expect(result[:result]).to eq("REPROVADO")
    expect(result[:reason]).to eq("gap_trait_critico")
  end

  it "never returns APROVADO when a gate is active" do
    answer_for(question: tq, score: 9.5)
    answer_for(question: bq, score: 9.5)
    evaluation_candidate.update_columns(g2_gate_triggered: true)

    result = described_class.call(evaluation_candidate: evaluation_candidate)
    expect(result[:result]).to eq("REPROVADO")
    expect(result[:gate_triggered]).to eq("G2")
  end
end
