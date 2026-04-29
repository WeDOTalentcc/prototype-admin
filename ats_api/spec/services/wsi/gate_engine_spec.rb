# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::GateEngine do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account, seniority: 2) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:evaluation_candidate) do
    create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, account: account, user: user, job: job)
  end

  let(:long_text) { ("word " * 40).strip }

  def build_answer(question:, score:, description: long_text, extraction: {})
    ex = {
      "inflation_detected" => false,
      "star_components" => { "situation" => true, "task" => true, "action" => true, "result" => true }
    }.merge(extraction)
    create(
      :answer,
      question: question,
      evaluation: evaluation,
      candidate: candidate,
      account: account,
      user: user,
      job: job,
      description: description,
      final_skill_score: score,
      analysis_data: { "wsi" => { "extraction" => ex }, "dreyfus" => { "score" => 3, "expected_numeric" => 3, "demonstrated" => 3 } }
    )
  end

  describe "G2" do
    let(:tq1) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }
    let(:tq2) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }

    it "triggers when total injection_attempt_count across answers is >= 2" do
      a1 = build_answer(question: tq1, score: 8.0)
      a2 = build_answer(question: tq2, score: 8.0)
      a1.update_columns(injection_attempt_count: 1)
      a2.update_columns(injection_attempt_count: 1)

      result = described_class.evaluate(evaluation_candidate: evaluation_candidate)
      expect(result[:triggered]).to be true
      expect(result[:gate]).to eq("G2")
    end
  end

  describe "G3" do
    let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }
    let(:bq) { create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational") }

    it "triggers when WSI técnico < 4.0" do
      build_answer(question: tq, score: 3.5)
      build_answer(question: bq, score: 9.0)

      result = described_class.evaluate(evaluation_candidate: evaluation_candidate)
      expect(result[:triggered]).to be true
      expect(result[:gate]).to eq("G3")
      expect(result[:reason]).to eq("wsi_tecnico_below_threshold")
    end
  end

  describe "G4" do
    let(:tq_critical) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual", wsi_metadata: { "critical" => true }) }
    let(:tq_other) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }

    it "triggers when a critical skill answer has score < 3.0 while WSI técnico stays >= 4.0" do
      build_answer(question: tq_critical, score: 2.5)
      build_answer(question: tq_other, score: 8.0)

      result = described_class.evaluate(evaluation_candidate: evaluation_candidate)
      expect(result[:triggered]).to be true
      expect(result[:gate]).to eq("G4")
    end
  end

  describe "G5" do
    let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }
    let(:bq) { create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational") }

    it "triggers when >= 50% of non-eligibility answers have < 30 words" do
      build_answer(question: tq, score: 8.0, description: "short")
      build_answer(question: bq, score: 8.0, description: "also short")

      result = described_class.evaluate(evaluation_candidate: evaluation_candidate)
      expect(result[:triggered]).to be true
      expect(result[:gate]).to eq("G5")
    end
  end

  describe "G6" do
    let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }
    let(:bq) { create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational") }

    it "triggers when inflation_detected is true in >= 3 answers" do
      4.times do
        build_answer(question: tq, score: 8.0, extraction: { "inflation_detected" => true })
      end
      build_answer(question: bq, score: 8.0)

      result = described_class.evaluate(evaluation_candidate: evaluation_candidate)
      expect(result[:triggered]).to be true
      expect(result[:gate]).to eq("G6")
    end
  end

  describe "precedence" do
    let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }

    it "does not use final WSI to override G3" do
      build_answer(question: tq, score: 3.8)

      result = described_class.evaluate(evaluation_candidate: evaluation_candidate)
      expect(result[:triggered]).to be true
      expect(result[:gate]).to eq("G3")
    end
  end
end
