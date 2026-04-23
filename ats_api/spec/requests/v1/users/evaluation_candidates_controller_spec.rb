# spec/requests/v1/users/evaluation_candidates_controller_spec.rb
require 'rails_helper'

RSpec.describe V1::Users::EvaluationCandidatesController, type: :request do
  let(:account)  { create(:account) }
  let(:user)     { create(:user, account: account) }
  let(:headers)  { auth_headers(user) } # supondo que você já tenha helper auth_headers(user)

  let(:evaluation) { create(:evaluation, account: account) }
  let(:candidate)  { create(:candidate, account: account) }
  let(:job)        { create(:job, account: account) }
  let(:apply)      { create(:apply, account: account, candidate: candidate, job: job) }

  let(:valid_params) do
    {
      evaluation_candidate: {
        candidate_id: candidate.id,
        evaluation_id: evaluation.id,
        job_id: job.id,
        apply_id: apply.id,
        completed: false
      }
    }
  end

  describe "GET /v1/users/evaluation_candidates" do
    it "returns list of evaluation_candidates" do
      create(:evaluation_candidate, account: account, user: user, candidate: candidate, evaluation: evaluation)
      EvaluationCandidate.reindex(refresh: true)

      get "/v1/users/evaluation_candidates", headers: headers
      expect(response).to have_http_status(:ok)
      response_data = JSON.parse(response.body)
      expect(response_data['data'].length).to be > 0
    end
  end

  describe "GET /v1/users/evaluation_candidates/:id" do
    it "returns the evaluation_candidate" do
      ec = create(:evaluation_candidate, account: account, user: user, candidate: candidate, evaluation: evaluation)

      get "/v1/users/evaluation_candidates/#{ec.id}", headers: headers
      expect(response).to have_http_status(:ok)
      response_data = JSON.parse(response.body)
      expect(response_data['data']['id']).to eq(ec.id.to_s)
    end

    it "returns 404 if not found" do
      get "/v1/users/evaluation_candidates/999999", headers: headers
      expect(response).to have_http_status(:not_found)
    end
  end

  describe "POST /v1/users/evaluation_candidates" do
    it "creates a new evaluation_candidate" do
      expect {
        post "/v1/users/evaluation_candidates", params: valid_params.to_json, headers: headers
        EvaluationCandidate.reindex(refresh: true)
      }.to change(EvaluationCandidate, :count).by(1)

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']['attributes']['candidate_id']).to eq(candidate.id)
    end

    it "returns error with invalid params" do
      expect {
        post "/v1/users/evaluation_candidates", params: { evaluation_candidate: { candidate_id: nil } }, headers: headers
      }.not_to change(EvaluationCandidate, :count)

      expect(response).to have_http_status(:bad_request)
    end

    it "returns 422 when evaluation has questions pending WSI review" do
      create(:question, evaluation: evaluation, wsi_reviewed: false)

      post "/v1/users/evaluation_candidates", params: valid_params.to_json, headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
      expect(JSON.parse(response.body)["error"]).to eq("questions_pending_review")
    end

    it "creates when all evaluation questions are wsi reviewed" do
      create(:question, evaluation: evaluation, wsi_reviewed: true)

      expect {
        post "/v1/users/evaluation_candidates", params: valid_params.to_json, headers: headers
      }.to change(EvaluationCandidate, :count).by(1)

      expect(response).to have_http_status(:ok)
    end
  end

  describe "PUT /v1/users/evaluation_candidates/:id" do
    let!(:ec) { create(:evaluation_candidate, account: account, user: user, candidate: candidate, evaluation: evaluation) }

    it "updates the evaluation_candidate" do
      put "/v1/users/evaluation_candidates/#{ec.id}",
            params: { evaluation_candidate: { completed: true } }.to_json,
            headers: headers

      expect(response).to have_http_status(:ok)
      expect(ec.reload.completed).to be true
    end
  end

  describe "DELETE /v1/users/evaluation_candidates/:id" do
    let!(:ec) { create(:evaluation_candidate, account: account, user: user, candidate: candidate, evaluation: evaluation) }

    it "marks the evaluation_candidate as deleted" do
      delete "/v1/users/evaluation_candidates/#{ec.id}", headers: headers

      expect(response).to have_http_status(:ok)
      expect(ec.reload.is_deleted).to be true
    end
  end
end
