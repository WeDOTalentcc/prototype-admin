# spec/requests/v1/users/applies_spec.rb
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Applies API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }

  let(:candidate) { create(:candidate, account: account) }
  let(:job) { create(:job, account: account, user: user) }
  let(:selective_process) { create(:selective_process, account: account) }

  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token', 'Content-Type' => 'application/json' } }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  describe 'GET /v1/users/applies' do
    before do
      create_list(:apply, 3)
      Apply.reindex
    end

    context 'when authenticated' do
      it 'returns all applies' do
        get '/v1/users/applies', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/applies', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with invalid token' do
      it 'returns unauthorized' do
        get '/v1/users/applies', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/applies/:id' do
    let!(:apply) { create(:apply) }

    context 'when authenticated' do
      it 'returns the apply' do
        get "/v1/users/applies/#{apply.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['id']).to eq(apply.id)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get "/v1/users/applies/#{apply.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/applies' do
    let(:valid_attributes) do
      {
        apply: {
          candidate_id: candidate.id,
          job_id: job.id,
          selective_process_id: selective_process.id
        }
      }
    end

    let(:invalid_attributes) do
      {
        apply: {
          candidate_id: nil,
          job_id: nil
        }
      }
    end

    context 'when authenticated with valid attributes' do
      it 'creates a new apply' do
        expect {
          post '/v1/users/applies', params: valid_attributes.to_json, headers: auth_headers(user)
        }.to change(Apply, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json['candidate_id']).to eq(candidate.id)
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/applies', params: invalid_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users/applies', params: valid_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/applies/:id' do
    let!(:apply) { create(:apply) }
    let(:new_attributes) { { apply: { is_deleted: true } } }

    context 'when authenticated' do
      it 'updates the apply' do
        put "/v1/users/applies/#{apply.id}", params: new_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        apply.reload
        expect(apply.is_deleted).to eq(true)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        put "/v1/users/applies/#{apply.id}", params: new_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/applies/:id' do
    let!(:apply) { create(:apply) }

    context 'when authenticated' do
      it 'soft deletes the apply' do
        delete "/v1/users/applies/#{apply.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:no_content)
        apply.reload
        expect(apply.is_deleted).to eq(true)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/applies/#{apply.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
