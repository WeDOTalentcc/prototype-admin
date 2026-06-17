# frozen_string_literal: true

require "rails_helper"

LONG_ANSWER_FOR_WSI_G5 = ("word " * 40).strip.freeze

RSpec.describe Evaluations::EvaluationAggregateService do
  describe ".call" do
    let(:account) { create(:account) }
    let(:user) { create(:user, account: account) }
    let(:job) { create(:job, user: user, account: account, seniority: 2) }
    let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }
    let(:candidate) { create(:candidate, account: account) }
    let(:evaluation_candidate) do
      create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        job: job
      )
    end

    let(:technical_question) { create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual") }
    let(:behavioral_question) { create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational") }

    before do
      create(
        :answer,
        question: technical_question,
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        job: job,
        description: LONG_ANSWER_FOR_WSI_G5,
        final_skill_score: 8.6,
        analysis_data: { dreyfus: { score: 4.0 } }
      )
      create(
        :answer,
        question: behavioral_question,
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        job: job,
        description: LONG_ANSWER_FOR_WSI_G5,
        final_skill_score: 8.0,
        analysis_data: { dreyfus: { score: 4.0 } }
      )
    end

    it "updates evaluation_candidate with aggregated fields" do
      result = described_class.call(evaluation_candidate: evaluation_candidate)

      expect(result.success?).to be true
      expect(evaluation_candidate.reload.score).to be > 0
      expect(evaluation_candidate.wsi_classification).to be_present
      expect(evaluation_candidate.wsi_level).to be_present
      expect(evaluation_candidate.wsi_summary).to be_present
      expect(evaluation_candidate.wsi_decision["result"]).to be_present
      expect(evaluation_candidate.wsi_red_flags).to be_a(Array)
    end

    it "supports macro distribution from account sourcing_config" do
      account.update!(
        sourcing_config: {
          "wsi_scoring" => {
            "macro_distribution" => { "technical" => 0.9, "behavioral" => 0.1 }
          }
        }
      )

      result = described_class.call(evaluation_candidate: evaluation_candidate)
      expect(result.success?).to be true
      expect(evaluation_candidate.reload.score).to be > 0
    end

    it "returns failure when there are no scored answers" do
      empty_candidate = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )

      result = described_class.call(evaluation_candidate: empty_candidate)
      expect(result.success?).to be false
    end

    it "applies a different WSI aggregate score when job seniority index maps to different semantic keys" do
      job.update!(seniority: 0)
      evaluation_candidate.reload
      result_junior = described_class.call(evaluation_candidate: evaluation_candidate)
      score_junior = result_junior.score

      job.update!(seniority: 2)
      ec2 = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      create(
        :answer,
        question: technical_question,
        evaluation: evaluation,
        candidate: ec2.candidate,
        account: account,
        user: user,
        job: job,
        description: LONG_ANSWER_FOR_WSI_G5,
        final_skill_score: 8.6,
        analysis_data: { dreyfus: { score: 4.0 } }
      )
      create(
        :answer,
        question: behavioral_question,
        evaluation: evaluation,
        candidate: ec2.candidate,
        account: account,
        user: user,
        job: job,
        description: LONG_ANSWER_FOR_WSI_G5,
        final_skill_score: 8.0,
        analysis_data: { dreyfus: { score: 4.0 } }
      )

      result_senior = described_class.call(evaluation_candidate: ec2)
      expect(Wsi::Constants.seniority_key(job)).to eq("senior")
      expect(result_senior.score).not_to eq(score_junior)
    end

    it "uses canonical senior weights for seniority without extra multiplier (F9-01 / §9.3)" do
      job.update!(seniority: 2)
      evaluation_candidate.reload
      tw = Wsi::Constants::SENIORITY_WEIGHTS["senior"][:technical]
      bw = Wsi::Constants::SENIORITY_WEIGHTS["senior"][:behavioral]
      expect(tw).to eq(0.5625)
      expect(bw).to eq(0.4375)

      wsi_tech = 7.85
      wsi_beh = 7.59
      ec = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      tq = create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual")
      bq = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational")
      create(:answer, question: tq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: wsi_tech, analysis_data: { dreyfus: { score: 4 } })
      create(:answer, question: bq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: wsi_beh, analysis_data: { dreyfus: { score: 4 } })

      result = described_class.call(evaluation_candidate: ec)
      expect(result.success?).to be true
      expect(result.score).to eq(7.74)
    end

    it "computes WSI_comportamental with trait_weight when all behavioral answers have weights (F9-02)" do
      job.update!(seniority: 2)
      evaluation_candidate.reload
      w1, w2, w3 = [ 0.365, 0.356, 0.279 ]
      s1, s2, s3 = [ 8.0, 7.0, 6.0 ]
      expected = ((s1 * w1) + (s2 * w2) + (s3 * w3)) / (w1 + w2 + w3)

      bq1 = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational", extra_params: { "trait_weight" => w1 })
      bq2 = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational", extra_params: { "trait_weight" => w2 })
      bq3 = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational", extra_params: { "trait_weight" => w3 })
      tq = create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual")

      ec = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      create(:answer, question: tq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 7.0, analysis_data: { dreyfus: { score: 3 } })
      create(:answer, question: bq1, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: s1, analysis_data: { dreyfus: { score: 3 } })
      create(:answer, question: bq2, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: s2, analysis_data: { dreyfus: { score: 3 } })
      create(:answer, question: bq3, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: s3, analysis_data: { dreyfus: { score: 3 } })

      result = described_class.call(evaluation_candidate: ec)
      expect(result.success?).to be true
      wsi_tech = 7.0
      wsi_beh = expected.round(4)
      tw = Wsi::Constants::SENIORITY_WEIGHTS["senior"][:technical]
      bw = Wsi::Constants::SENIORITY_WEIGHTS["senior"][:behavioral]
      expect(result.score).to eq((wsi_tech * tw + wsi_beh * bw).round(2))
    end

    it "falls back to simple average for behavioral when trait_weight is missing on any question (F9-02)" do
      job.update!(seniority: 2)
      bq1 = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational", extra_params: { "trait_weight" => 0.5 })
      bq2 = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational", extra_params: {})
      tq = create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual")
      ec = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      create(:answer, question: tq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 7.0, analysis_data: { dreyfus: { score: 3 } })
      create(:answer, question: bq1, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 10.0, analysis_data: { dreyfus: { score: 3 } })
      create(:answer, question: bq2, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 6.0, analysis_data: { dreyfus: { score: 3 } })

      result = described_class.call(evaluation_candidate: ec)
      expect(result.success?).to be true
      wsi_beh_simple = 8.0
      tw = Wsi::Constants::SENIORITY_WEIGHTS["senior"][:technical]
      bw = Wsi::Constants::SENIORITY_WEIGHTS["senior"][:behavioral]
      expect(result.score).to eq((7.0 * tw + wsi_beh_simple * bw).round(2))
    end

    it "classifies WSI >= 9.0 as Excepcional (F9-03 / §9.5)" do
      job.update!(seniority: 2)
      tq = create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual")
      bq = create(:question, evaluation: evaluation, competence_type: "behavioral", response_type: "situational")
      ec = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      create(:answer, question: tq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 9.5, analysis_data: { dreyfus: { score: 5 } })
      create(:answer, question: bq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 9.5, analysis_data: { dreyfus: { score: 5 } })

      described_class.call(evaluation_candidate: ec)
      expect(ec.reload.wsi_classification).to eq("Excepcional")
      expect(ec.score).to be >= 9.0
      expect(ec.score).to be <= 10.0
    end

    it "persists wsi_big_five_observed with GAP and critical_gap for large negative gap (F9-04 / §9.6)" do
      big_five = Wsi::JdBigFiveExtractionService::TRAITS.index_with do |trait|
        { "score" => 50, "evidence" => [], "confidence" => "high" }
      end
      big_five["conscientiousness"] = { "score" => 82, "evidence" => [], "confidence" => "high" }
      job.update!(
        seniority: 2,
        wsi_jd_big_five_profile: { "big_five_jd" => big_five }
      )

      bq = create(
        :question,
        evaluation: evaluation,
        competence_type: "behavioral",
        response_type: "situational",
        ocean_trait: "conscientiousness"
      )
      ec = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      tq = create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual")
      create(:answer, question: tq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 7.0, analysis_data: { dreyfus: { score: 4 } })
      create(:answer, question: bq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 6.2, analysis_data: { dreyfus: { score: 4 } })

      described_class.call(evaluation_candidate: ec)
      obs = ec.reload.wsi_big_five_observed
      row = obs.dig("candidate_big_five_observed", "conscientiousness")
      expect(row["score_demonstrated"]).to eq(62)
      expect(row["score_required"]).to eq(82)
      expect(row["gap"]).to eq(-20)
      expect(row["status"]).to eq("GAP")
      expect(row["critical_gap"]).to be true
      expect(obs["critical_gaps"]).to include("conscientiousness")
    end

    it "marks traits without behavioral questions as score_demonstrated null (F9-04)" do
      big_five = Wsi::JdBigFiveExtractionService::TRAITS.index_with do |trait|
        { "score" => 70, "evidence" => [], "confidence" => "high" }
      end
      job.update!(seniority: 2, wsi_jd_big_five_profile: { "big_five_jd" => big_five })

      bq = create(
        :question,
        evaluation: evaluation,
        competence_type: "behavioral",
        response_type: "situational",
        ocean_trait: "openness"
      )
      ec = create(
        :evaluation_candidate,
        evaluation: evaluation,
        candidate: create(:candidate, account: account),
        account: account,
        user: user,
        job: job
      )
      tq = create(:question, evaluation: evaluation, competence_type: "technical", response_type: "contextual")
      create(:answer, question: tq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 7.0, analysis_data: { dreyfus: { score: 4 } })
      create(:answer, question: bq, evaluation: evaluation, candidate: ec.candidate, account: account, user: user, job: job, description: LONG_ANSWER_FOR_WSI_G5, final_skill_score: 8.0, analysis_data: { dreyfus: { score: 4 } })

      described_class.call(evaluation_candidate: ec)
      row = ec.reload.wsi_big_five_observed.dig("candidate_big_five_observed", "conscientiousness")
      expect(row["score_demonstrated"]).to be_nil
      expect(row["status"]).to eq("Não avaliado")
    end
  end
end
