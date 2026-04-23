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
    let!(:applies) { create_list(:apply, 3, account: user.account) }

    before do
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
    let!(:apply) { create(:apply, account: user.account) }

    context 'when authenticated' do
      it 'returns the apply' do
        get "/v1/users/applies/#{apply.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['id']).to eq(apply.id)
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

        expect(json['data']['attributes']['candidate_id']).to eq(candidate.id)
      end

      context 'when an apply already exists with is_deleted = false' do
        let!(:existing_apply) do
          create(
            :apply,
            candidate: candidate,
            job: job,
            account: account,
            selective_process: selective_process,
            selective_process_status: 'Candidato',
            is_deleted: false
          )
        end

        it 'returns the existing apply and updates it' do
          expect {
            post '/v1/users/applies', params: valid_attributes.to_json, headers: auth_headers(user)
          }.not_to change(Apply, :count)

          expect(response).to have_http_status(:created)
          json = JSON.parse(response.body)

          expect(json['data']['attributes']['id']).to eq(existing_apply.id)
          expect(json['data']['attributes']['candidate_id']).to eq(candidate.id)
          expect(json['data']['attributes']['job_id']).to eq(job.id)
        end
      end

      context 'when an apply exists with is_deleted = true' do
        let!(:deleted_apply) do
          create(
            :apply,
            candidate: candidate,
            job: job,
            account: account,
            selective_process: selective_process,
            is_deleted: true
          )
        end

        it 'reactivates the deleted apply instead of creating a new one' do
          expect {
            post '/v1/users/applies', params: valid_attributes.to_json, headers: auth_headers(user)
          }.not_to change(Apply, :count)

          expect(response).to have_http_status(:created)
          json = JSON.parse(response.body)

          expect(json['data']['attributes']['candidate_id']).to eq(candidate.id)
          expect(json['data']['attributes']['job_id']).to eq(job.id)
          expect(json['data']['attributes']['is_deleted']).to eq(false)

          deleted_apply.reload
          expect(deleted_apply.is_deleted).to eq(false)
        end
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/applies', params: invalid_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:unprocessable_content)
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
    let!(:apply) { create(:apply, account: user.account) }
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
    let!(:apply) { create(:apply, account: user.account) }

    context 'when authenticated' do
      it 'soft deletes the apply' do
        delete "/v1/users/applies/#{apply.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
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
