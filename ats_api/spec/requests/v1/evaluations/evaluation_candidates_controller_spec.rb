require 'rails_helper'

RSpec.describe V1::Evaluations::EvaluationCandidatesController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:evaluation) { create(:evaluation, account: account, user: user, job: job) }
  let(:candidate) { create(:candidate, account: account) }
  let(:apply) { create(:apply, account: account, job: job, candidate: candidate) }
  let(:evaluation_candidate) do
    create(:evaluation_candidate, account: account, user: user, evaluation: evaluation,
                                  candidate: candidate, apply: apply)
  end

  describe 'GET /v1/evaluations/:account_uid/:evaluation_candidate_uid' do
    it 'returns evaluation and evaluation_candidate by uid with tenant switch' do
      get "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}"

      expect(response).to have_http_status(:ok)
      parsed = JSON.parse(response.body)
      expect(parsed['evaluation']['id']).to eq(evaluation.id)
      expect(parsed['evaluation_candidate']['id']).to eq(evaluation_candidate.id)
      expect(parsed['evaluation']['account_id']).to be_nil
      expect(parsed['evaluation_candidate']['account_id']).to be_nil
    end

    it 'returns company info with logo_url' do
      get "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}"

      expect(response).to have_http_status(:ok)
      parsed = JSON.parse(response.body)
      expect(parsed['company']).to be_present
      expect(parsed['company']['name']).to eq(account.name)
    end

    it 'returns 401 for invalid uid' do
      get "/v1/evaluations/#{account.uid}/invalid-uid"
      expect(response).to have_http_status(:unauthorized)
    end

    context 'when token is expired' do
      let(:expired_evaluation_candidate) do
        create(:evaluation_candidate, account: account, user: user, evaluation: evaluation,
                                      candidate: candidate, apply: apply, date_expiration: 1.day.ago)
      end

      it 'returns 410 gone for expired evaluation' do
        get "/v1/evaluations/#{account.uid}/#{expired_evaluation_candidate.uid}"

        expect(response).to have_http_status(:gone)
        parsed = JSON.parse(response.body)
        expect(parsed['expired']).to eq(true)
      end
    end

    context 'when evaluation is completed' do
      before do
        Apartment::Tenant.switch!(account.tenant) do
          evaluation_candidate.update!(completed: true)
        end
      end

      it 'returns finished status' do
        get "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}"

        expect(response).to have_http_status(:ok)
        parsed = JSON.parse(response.body)
        expect(parsed['finished']).to eq(true)
      end
    end

    context 'when evaluation is declined' do
      before do
        Apartment::Tenant.switch!(account.tenant) do
          evaluation_candidate.update!(declined_at: Time.current)
        end
      end

      it 'returns declined status' do
        get "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}"

        expect(response).to have_http_status(:ok)
        parsed = JSON.parse(response.body)
        expect(parsed['declined']).to eq(true)
      end
    end
  end

  describe 'POST /v1/evaluations/:account_uid/:evaluation_candidate_uid/decline' do
    it 'allows candidate to decline evaluation' do
      post "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}/decline",
           params: { reason: 'Não tenho interesse' }

      expect(response).to have_http_status(:ok)
      parsed = JSON.parse(response.body)
      expect(parsed['success']).to eq(true)
    end

    it 'rejects declining an already completed evaluation' do
      Apartment::Tenant.switch!(account.tenant) do
        evaluation_candidate.update!(completed: true)
      end

      post "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}/decline"

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
