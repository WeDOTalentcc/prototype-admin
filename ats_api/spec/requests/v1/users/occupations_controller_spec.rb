require 'rails_helper'

RSpec.describe V1::Users::OccupationsController, type: :request do
  let!(:account) { create(:account) }
  let!(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe 'GET /v1/users/occupations' do
    before do
      create(:occupation, account: account, is_deleted: false, name: 'Active', user: user)
      create(:occupation, account: account, is_deleted: true, name: 'Deleted', user: user)
      Occupation.reindex(refresh: true)
    end

    it 'returns only non-deleted occupations' do
      get '/v1/users/occupations', headers: headers

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data'].size).to eq(1)
      expect(json['data'].first['attributes']['name']).to eq('Active')
    end
  end

  describe 'GET /v1/users/occupations/:id' do
    let!(:occupation) { create(:occupation, account: account, user: user) }

    it 'returns the occupation' do
      get "/v1/users/occupations/#{occupation.id}", headers: headers

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data']['id']).to eq(occupation.id.to_s)
    end
  end

  describe 'POST /v1/users/occupations' do
    let(:params) do
      {
        occupation: {
          name: 'Developer',
          description: 'Software engineer'
        }
      }
    end

    it 'creates a new occupation' do
      expect {
        post '/v1/users/occupations', params: params, headers: headers
        Occupation.reindex(refresh: true)
      }.to change(Occupation, :count).by(1)

      expect(response).to have_http_status(:created)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']['name']).to eq('Developer')
    end
  end

  describe 'PUT /v1/users/occupations/:id' do
    let!(:occupation) { create(:occupation, account: account, user: user, name: 'Old') }

    it 'updates the occupation' do
      put "/v1/users/occupations/#{occupation.id}", params: {
        occupation: { name: 'Updated' }
      }, headers: headers

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']['name']).to eq('Updated')
    end
  end

  describe 'DELETE /v1/users/occupations/:id' do
    let!(:occupation) { create(:occupation, account: account, user: user) }

    it 'soft deletes the occupation' do
      delete "/v1/users/occupations/#{occupation.id}", headers: headers

      expect(response).to have_http_status(:ok)
      json = JSON.parse(response.body)
      expect(json['data']['attributes']['is_deleted']).to eq(true)
    end
  end
end
