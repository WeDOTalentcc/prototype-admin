# spec/requests/v1/users/candidates_spec.rb
# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Candidates API', type: :request do
  let(:user) { create(:user) }
  let(:account) { user.account }
  let(:invalid_auth_headers) { { 'Authorization' => 'Bearer invalid_token', 'Content-Type' => 'application/json' } }
  let(:no_auth_headers) { { 'Content-Type' => 'application/json' } }

  describe 'GET /v1/users/candidates' do
    before do
      # Candidate.destroy_all
      # Candidate.reindex
      create_list(:candidate, 3, account: account)
      Candidate.reindex
    end

    context 'when authenticated' do
      it 'returns all candidates' do
        get '/v1/users/candidates', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(3)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/candidates', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with invalid token' do
      it 'returns unauthorized' do
        get '/v1/users/candidates', headers: invalid_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/candidates/:id' do
    let!(:candidate) { create(:candidate, account: user.account) }

    context 'when authenticated' do
      it 'returns the candidate' do
        get "/v1/users/candidates/#{candidate.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['id']).to eq(candidate.id)
        expect(json['data']['attributes']['email']).to eq(candidate.email)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get "/v1/users/candidates/#{candidate.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'POST /v1/users/candidates' do
    let(:valid_attributes) do
      {
        candidate: {
          name: 'John',
          email: 'john.doe@example.com'
        }
      }
    end

    let(:invalid_attributes) do
      {
        candidate: {
          name: '',
          email: ''
        }
      }
    end

    context 'when authenticated with valid attributes' do
      it 'creates a new candidate' do
        expect {
          post '/v1/users/candidates', params: valid_attributes.to_json, headers: auth_headers(user)
        }.to change(Candidate, :count).by(1)

        expect(response).to have_http_status(:created)
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['name']).to eq('John')
      end
    end

    context 'when authenticated with invalid attributes' do
      it 'returns unprocessable entity' do
        post '/v1/users/candidates', params: invalid_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:unprocessable_entity)
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        post '/v1/users/candidates', params: valid_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/candidates/:id' do
    let!(:candidate) { create(:candidate, account: user.account) }
    let(:new_attributes) { { candidate: { name: 'Updated Name' } } }

    context 'when authenticated' do
      it 'updates the candidate' do
        put "/v1/users/candidates/#{candidate.id}", params: new_attributes.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        candidate.reload
        expect(candidate.name).to eq('Updated Name')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        put "/v1/users/candidates/#{candidate.id}", params: new_attributes.to_json, headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/candidates/:id' do
    let!(:candidate) { create(:candidate, account: user.account) }

    context 'when authenticated' do
      it 'deletes the candidate' do
        expect {
          delete "/v1/users/candidates/#{candidate.id}", headers: auth_headers(user)
        }.to change(Candidate, :count).by(-1)
        expect(response).to have_http_status(:ok)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        delete "/v1/users/candidates/#{candidate.id}", headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end
end
