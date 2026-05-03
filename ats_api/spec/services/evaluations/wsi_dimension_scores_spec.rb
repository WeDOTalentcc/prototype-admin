# frozen_string_literal: true

require "rails_helper"

RSpec.describe Evaluations::WsiDimensionScores do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, user: user, account: account) }
  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:apply) { create(:apply, account: account, job: job, candidate: candidate) }
  let(:evaluation_candidate) do
    create(:evaluation_candidate, account: account, user: user,
           evaluation: evaluation, candidate: candidate, apply: apply)
  end

  def create_scored_answer(question:, score:)
    create(:answer,
           question: question,
           evaluation: evaluation,
           candidate: candidate,
           account: account,
           user: user,
           job: job,
           apply: apply,
           final_skill_score: score)
  end

  describe ".call" do
    context "when there are no scored answers" do
      it "returns empty result" do
        result = described_class.call(evaluation_candidate: evaluation_candidate)
        expect(result).to eq({ technical: 0.0, behavioral: 0.0, final: 0.0, answers: [] })
      end
    end

    context "with valid scored technical answers" do
      it "computes technical WSI from answers linked to real questions" do
        question = create(:question, evaluation: evaluation, competence_type: "technical")
        create_scored_answer(question: question, score: 8.0)

        result = described_class.call(evaluation_candidate: evaluation_candidate)
        expect(result[:technical]).to be > 0
        expect(result[:final]).to be > 0
      end
    end

    context "scoring integrity — orphan answers excluded" do
      it "excludes answers with no associated question from WSI computation" do
        question = create(:question, evaluation: evaluation, competence_type: "technical")
        legitimate = create_scored_answer(question: question, score: 6.0)

        orphan = create(:answer,
                        evaluation: evaluation,
                        candidate: candidate,
                        account: account,
                        user: user,
                        job: job,
                        apply: apply,
                        question: nil,
                        final_skill_score: 10.0)

        result = described_class.call(evaluation_candidate: evaluation_candidate)

        scored = result[:answers]
        expect(scored.map(&:id)).to include(legitimate.id)
        expect(scored.map(&:id)).not_to include(orphan.id)
        expect(result[:technical].round(4)).to eq(6.0)
      end

      it "returns empty result when only orphan answers with scores exist" do
        create(:answer,
               evaluation: evaluation,
               candidate: candidate,
               account: account,
               user: user,
               job: job,
               apply: apply,
               question: nil,
               final_skill_score: 10.0)

        result = described_class.call(evaluation_candidate: evaluation_candidate)
        expect(result).to eq({ technical: 0.0, behavioral: 0.0, final: 0.0, answers: [] })
      end
    end
  end
end
