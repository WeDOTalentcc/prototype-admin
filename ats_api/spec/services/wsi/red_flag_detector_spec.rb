# frozen_string_literal: true

require "rails_helper"

RSpec.describe Wsi::RedFlagDetector do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account, seniority: 2) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:long_text) { ("word " * 40).strip }

  let(:evaluation_candidate) do
    create(:evaluation_candidate, evaluation: evaluation, candidate: candidate, account: account, user: user, job: job)
  end

  let(:tq) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual", bloom_level: "analisar") }
  let(:bq) { create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational") }

  def extraction_base
    {
      "inflation_detected" => false,
      "bloom_demonstrated" => 4,
      "response_authentic" => true,
      "star_components" => { "situation" => true, "task" => true, "action" => true, "result" => true }
    }
  end

  def build_answer(question:, score:, extraction: {})
    ex = extraction_base.merge(extraction.stringify_keys)
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
      analysis_data: {
        "wsi" => { "extraction" => ex },
        "dreyfus" => { "score" => 3, "expected_numeric" => 4, "demonstrated" => 3 }
      }
    )
  end

  context "RF-01" do
    it "includes RF-01 medio when inflation in exactly 2 answers" do
      build_answer(question: tq, score: 8.0, extraction: { "inflation_detected" => true })
      build_answer(question: tq, score: 8.0, extraction: { "inflation_detected" => true })

      flags = described_class.call(evaluation_candidate: evaluation_candidate)
      rf = flags.find { |f| f[:code] == "RF-01" }
      expect(rf).to be_present
      expect(rf[:level]).to eq("medio")
    end
  end

  context "RF-02" do
    it "includes RF-02 alto when bloom_demonstrated < expected in >= 3 answers" do
      3.times do
        build_answer(question: tq, score: 8.0, extraction: { "bloom_demonstrated" => 1 })
      end

      flags = described_class.call(evaluation_candidate: evaluation_candidate)
      rf = flags.find { |f| f[:code] == "RF-02" }
      expect(rf).to be_present
      expect(rf[:level]).to eq("alto")
    end
  end

  context "RF-08" do
    it "includes RF-08 alto when response_authentic is false in any answer" do
      build_answer(question: tq, score: 8.0, extraction: { "response_authentic" => false })

      flags = described_class.call(evaluation_candidate: evaluation_candidate)
      rf = flags.find { |f| f[:code] == "RF-08" }
      expect(rf).to be_present
      expect(rf[:level]).to eq("alto")
    end
  end
end
