# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluations::ScoreCalculatorService do
  describe ".call" do
    before { stub_wsi_response_extraction }

    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account) }
    let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
    let(:candidate) { create(:candidate, account: account) }
    let(:question) do
      create(
        :question,
        evaluation: evaluation,
        response_type: "contextual",
        competence_type: "technical",
        bloom_level: "analyze",
        dreyfus_target: 4,
        ocean_trait: "conscientiousness",
        framework_weights: { bloom: 0.25, dreyfus: 0.35, big_five: 0.1, cbi_star: 0.3 }
      )
    end
    let(:answer) do
      create(
        :answer,
        question: question,
        evaluation: evaluation,
        candidate: candidate,
        user: user,
        account: account,
        job: job,
        description: "Situação: havia atrasos. Tarefa: reduzir o tempo. Ação: implementei automação e liderei o ajuste. Resultado: redução de 30%.",
        comments_response: { score: 0.8, feedback_for_recruiter: "Boa resposta" }
      )
    end

    it "stores analysis_data and final_skill_score in answer" do
      result = described_class.call(answer: answer)

      expect(result.success?).to be true
      expect(answer.reload.analysis_data).to be_a(Hash)
      expect(answer.final_skill_score).to be_between(0.0, 10.0)
      expect(answer.analysis_data["bloom"]).to be_present
      expect(answer.analysis_data["dreyfus"]).to be_present
      expect(answer.analysis_data["big_five"]).to be_present
      expect(answer.analysis_data["cbi_star"]).to be_present
    end

    it "stores rationale as literal evidences when at least two match the answer text" do
      result = described_class.call(answer: answer)

      expect(result.success?).to be true
      expect(answer.reload.analysis_data["rationale"]).to eq(
        [ "implementei automação", "redução de 30%" ]
      )
    end

    it "stores empty rationale when fewer than two verified literal evidences exist" do
      stub_wsi_response_extraction(
        trait_signals_detected: [],
        key_quote: "\"implementei automação\"",
        rationale: [ "implementei automação" ]
      )

      described_class.call(answer: answer)

      expect(answer.reload.analysis_data["rationale"]).to eq([])
    end

    it "computes technical score per WSI layer 3 when self_declaration and specificity align" do
      stub_wsi_response_extraction(
        specificity_score: 8,
        bloom_demonstrated: 4,
        inflation_detected: false
      )
      answer.update!(self_declaration_score: 4, description: answer.description)
      question.update!(bloom_level: "analyze", competence_type: "technical", dreyfus_target: 4)

      described_class.call(answer: answer)
      scoring = answer.reload.analysis_data["scoring"]
      expect(scoring["score_bruto"].to_f).to be_within(0.05).of(8.5)
    end

    it "applies inflation adjustment from extraction" do
      stub_wsi_response_extraction(specificity_score: 8, inflation_detected: true, bloom_demonstrated: 4)
      answer.update!(self_declaration_score: 4)
      question.update!(bloom_level: "analyze", competence_type: "technical", dreyfus_target: 4)

      described_class.call(answer: answer)
      expect(answer.reload.analysis_data.dig("wsi", "layer3", "adjustments_84").to_f).to be < 0
    end

    it "persists WSI extraction and layer3 breakdown" do
      result = described_class.call(answer: answer)
      wsi = answer.reload.analysis_data["wsi"]

      expect(result.success?).to be true
      expect(wsi["extraction"]).to be_present
      expect(wsi["layer3"]).to include("score_bruto", "adjustments_84", "structural")
    end

    it "returns failure when question is missing" do
      answer_without_question = create(:answer, question: nil, user: user, account: account)
      result = described_class.call(answer: answer_without_question)

      expect(result.success?).to be false
      expect(result.error).to include("Question")
    end

    it "prefers self_declaration_score over comments_response score" do
      answer.update!(
        self_declaration_score: 3,
        comments_response: { score: 0.2 }
      )
      result = described_class.call(answer: answer)
      expect(result.success?).to be true
      expect(answer.reload.analysis_data.dig("scoring", "self_declaration_score")).to eq(3.0)
    end

    it "skips scoring for eligibility questions" do
      eligibility_question = create(
        :question,
        evaluation: evaluation,
        response_type: 1,
        competence_type: "eligibility"

      )
      eligibility_answer = create(
        :answer,
        question: eligibility_question,
        evaluation: evaluation,
        candidate: candidate,
        user: user,
        account: account,
        job: job,
        description: "Yes"
      )
      result = described_class.call(answer: eligibility_answer)
      expect(result.success?).to be true
      expect(eligibility_answer.reload.final_skill_score).to be_nil
      expect(eligibility_answer.analysis_data.dig("wsi", "skipped")).to be true
    end
  end
end
