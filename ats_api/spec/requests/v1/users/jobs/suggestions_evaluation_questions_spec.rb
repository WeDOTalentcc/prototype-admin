# frozen_string_literal: true

require "rails_helper"

RSpec.describe "POST /v1/users/jobs/:id/suggestion/questions", type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  let(:job) do
    create(:job, user: user, account: account, seniority: 2).tap do |j|
      scores = {
        "openness" => 74,
        "conscientiousness" => 76,
        "extraversion" => 40,
        "agreeableness" => 50,
        "stability" => 75
      }
      traits = Wsi::JdBigFiveExtractionService::TRAITS
      big_five = traits.index_with do |trait|
        { "score" => scores.fetch(trait), "evidence" => [], "confidence" => "high" }
      end
      j.update_columns(
        wsi_jd_big_five_profile: { "big_five_jd" => big_five },
        wsi_jd_trait_ranking: {}
      )
      JobSuggestionService.ensure_wsi_jd_trait_ranking!(j.reload, wsi_type: "wsi_compact")
    end
  end

  let(:evaluation) { create(:evaluation, user: user, account: account, job: job) }

  let(:stubbed_questions) do
    [
      {
        title: "Behavioral example",
        description: "Describe a situation",
        response_type: "situational",
        competence_type: "behavioral",
        ocean_trait: "conscientiousness",
        bloom_level: 4,
        dreyfus_target: 3,
        framework_weights: { "bloom" => 0.15, "dreyfus" => 0.25, "big_five" => 0.3, "cbi_star" => 0.3 },
        framework: "big_five",
        time: 5
      }
    ]
  end

  before do
    result = JobSuggestionService::Result.new(true, { questions: stubbed_questions }, nil)
    allow(JobSuggestionService).to receive(:generate_evaluation_questions).and_return(result)
  end

  it "persists extra_params trait_weight from F3 ranking for behavioral questions" do
    post "/v1/users/jobs/#{job.id}/suggestion/questions",
         params: { type: "query", evaluation_id: evaluation.id }.to_json,
         headers: headers

    expect(response).to have_http_status(:ok)
    body = JSON.parse(response.body)
    expect(body["created_questions"]).to be_present

    q = evaluation.reload.questions.order(:id).last
    expect(q.competence_type).to eq("behavioral")
    expect(q.ocean_trait).to eq("conscientiousness")
    stored = job.reload.wsi_jd_trait_ranking["big_five_ranking"].find { |r| r["trait"] == "conscientiousness" }["weight_normalized"]
    expect(q.extra_params["trait_weight"]).to eq(stored)
  end

  it "uses trait_weight 1.0 when ranking is absent" do
    job.update_column(:wsi_jd_trait_ranking, {})

    post "/v1/users/jobs/#{job.id}/suggestion/questions",
         params: { type: "query", evaluation_id: evaluation.id }.to_json,
         headers: headers

    expect(response).to have_http_status(:ok)
    q = evaluation.reload.questions.order(:id).last
    expect(q.extra_params["trait_weight"]).to eq(1.0)
  end
end
