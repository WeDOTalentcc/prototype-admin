# frozen_string_literal: true

require 'rails_helper'

RSpec.describe V1::Evaluations::MessagesController, type: :request do
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

  let(:base_path) { "/v1/evaluations/#{account.uid}/#{evaluation_candidate.uid}" }

  describe 'GET /v1/evaluations/:account_uid/:evaluation_candidate_uid/messages' do
    it 'returns empty array when no messages exist' do
      get "#{base_path}/messages"

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data']).to eq([])
      expect(body['meta']['total']).to eq(0)
    end

    it 'returns message history ordered by created_at asc' do
      Apartment::Tenant.switch!(account.tenant) do
        create(:message, account: account, reference: evaluation_candidate, content: 'Primeira mensagem',
                         entity: 0, status: 0, created_at: 2.minutes.ago)
        create(:message, account: account, reference: evaluation_candidate, content: 'Resposta do candidato',
                         entity: 1, status: 0, created_at: 1.minute.ago)
      end

      get "#{base_path}/messages"

      expect(response).to have_http_status(:ok)
      body = JSON.parse(response.body)
      expect(body['data'].size).to eq(2)
      expect(body['data'].first['content']).to eq('Primeira mensagem')
      expect(body['data'].first['entity']).to eq(0)
      expect(body['data'].last['content']).to eq('Resposta do candidato')
      expect(body['data'].last['entity']).to eq(1)
    end

    it 'returns 401 for invalid uid' do
      get "/v1/evaluations/#{account.uid}/invalid-uid/messages"

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'POST /v1/evaluations/:account_uid/:evaluation_candidate_uid/messages' do
    it 'creates a message for the evaluation candidate' do
      post "#{base_path}/messages", params: {
        message: {
          content: 'Minha resposta',
          entity: 1,
          metadata: { question_id: 123 }
        }
      }

      expect(response).to have_http_status(:created)
    end

    it 'returns 401 for invalid uid' do
      post "/v1/evaluations/#{account.uid}/invalid-uid/messages", params: {
        message: { content: 'test' }
      }

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
