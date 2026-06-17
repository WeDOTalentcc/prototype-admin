require 'rails_helper'

RSpec.describe V1::Evaluations::QuestionsController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:apply) { create(:apply, account: account, job: job, candidate: candidate) }
  let(:evaluation_candidate) { create(:evaluation_candidate, account: account, user: user, evaluation: evaluation, candidate: candidate, apply: apply) }

  before do
    create(:question, evaluation: evaluation, is_deleted: false)
    create(:question, evaluation: evaluation, is_deleted: true)
    Question.reindex(refresh: true) if Question.respond_to?(:reindex)
  end

  describe 'GET /v1/evaluations/:account_uid/:evaluation_candidate_uid/questions' do
    it 'returns only non-deleted questions for the evaluation uid scope' do
      get "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}/questions"

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']).to be_a(Array)
      expect(body['data'].size).to eq(1)
      expect(body['data'].first['attributes']['is_deleted']).to eq(false)
      expect(body['meta']).to be_present
    end

    it 'supports pagination via params' do
      create_list(:question, 3, evaluation: evaluation, is_deleted: false)
      Question.reindex(refresh: true) if Question.respond_to?(:reindex)

      get "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}/questions", params: { page: 1, limit: 2 }
      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data'].length).to be <= 2
    end

    it 'returns 401 when uid is invalid' do
      get "/v1/evaluations/#{account.uid}/invalid/questions"
      expect(response).to have_http_status(:unauthorized)
    end
  end
end
