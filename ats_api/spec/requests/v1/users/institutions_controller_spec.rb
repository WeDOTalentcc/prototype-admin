# frozen_string_literal: true

require 'rails_helper'

RSpec.describe 'V1::Users::Institutions API', type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }

  let(:authentication_headers) { auth_headers(user) }
  let(:no_authentication_headers) { {} }

  describe 'GET /v1/users/institutions' do
    let!(:institutions) { create_list(:institution, 3, account: account) }
    let!(:other_institution) { create(:institution) } # Belongs to a different account

    before do
      Institution.reindex
      get '/v1/users/institutions', headers: authentication_headers
    end

    context 'when authenticated' do
      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns all institutions' do
        json = JSON.parse(response.body)
        expect(json['data'].size).to eq(4)
      end
    end
  end

  describe 'GET /v1/users/institutions/:id' do
    let!(:institution) { create(:institution, account: account) }

    context 'when authenticated' do
      before do
        get "/v1/users/institutions/#{institution.id}", headers: authentication_headers
      end

      it 'returns a successful response' do
        expect(response).to have_http_status(:ok)
      end

      it 'returns the institution data' do
        json = JSON.parse(response.body)
        expect(json['data']['id']).to eq(institution.id.to_s)
        expect(json['data']['attributes']['name']).to eq(institution.name)
      end
    end
  end

  describe 'POST /v1/users/institutions' do
    let(:valid_params) do
      {
        institution: {
          name: 'Universidade Nova',
          approved: true,
          account_id: account.id
        }
      }
    end

    context 'when authenticated with valid params' do
      it 'creates a new institution' do
        expect {
          post '/v1/users/institutions', params: valid_params, headers: authentication_headers, as: :json
        }.to change(Institution, :count).by(1)
        expect(response).to have_http_status(:created)
      end

      it 'returns the created institution data' do
        post '/v1/users/institutions', params: valid_params, headers: authentication_headers, as: :json
        json = JSON.parse(response.body)
        expect(json['data']['attributes']['name']).to eq('Universidade Nova')
        expect(json['data']['attributes']['account_id']).to eq(account.id)
      end
    end
  end

  describe 'PUT /v1/users/institutions/:id' do
    let!(:institution) { create(:institution, account: account) }
    let(:valid_params) do
      {
        institution: {
          name: 'Universidade Atualizada'
        }
      }
    end

    context 'when authenticated with valid params' do
      before do
        put "/v1/users/institutions/#{institution.id}", params: valid_params, headers: authentication_headers, as: :json
      end

      it 'updates the institution' do
        expect(response).to have_http_status(:ok)
        institution.reload
        expect(institution.name).to eq('Universidade Atualizada')
      end
    end
  end

  describe 'DELETE /v1/users/institutions/:id' do
    let!(:institution) { create(:institution, account: account) }

    context 'when authenticated' do
      it 'deletes the institution' do
        expect {
          delete "/v1/users/institutions/#{institution.id}", headers: authentication_headers
        }.to change(Institution, :count).by(-1)
        expect(response).to have_http_status(:ok)
      end
    end
  end
end
