# spec/requests/v1/users/remunerations_controller_spec.rb
require 'rails_helper'

RSpec.describe V1::Users::RemunerationsController, type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:headers) { auth_headers(user) }

  describe 'GET /v1/users/remunerations' do
    before do
      create(:remuneration, account: account, is_deleted: false, name: 'R1', user: user)
      create(:remuneration, account: account, is_deleted: true, name: 'R2', user: user)
      Remuneration.reindex(refresh: true)
    end

    it 'returns only non-deleted remunerations' do
      get '/v1/users/remunerations', headers: headers

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data'].size).to eq(1)
      expect(response_body['data'].first['attributes']['is_deleted']).to be false
    end
  end

  describe 'GET /v1/users/remunerations/:id' do
    let(:remuneration) { create(:remuneration, account: account) }

    it 'returns the remuneration' do
      get "/v1/users/remunerations/#{remuneration.id}", headers: headers

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['id']).to eq(remuneration.id.to_s)
    end
  end

  describe 'POST /v1/users/remunerations' do
    let(:params) do
      {
        remuneration: {
          name: 'PLR',
          description: 'Remuneração variável'
        }
      }
    end

    it 'creates a remuneration' do
      expect {
        post '/v1/users/remunerations', params: params.to_json, headers: headers
        Remuneration.reindex(refresh: true) # <- após a criação
      }.to change(Remuneration, :count).by(1)
      expect(response).to have_http_status(:created)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['attributes']['name']).to eq('PLR')
    end
  end

  describe 'PUT /v1/users/remunerations/:id' do
    let(:remuneration) { create(:remuneration, account: account, user: user, name: 'Old') }

    it 'updates the remuneration' do
      put "/v1/users/remunerations/#{remuneration.id}", params: {
        remuneration: { name: 'New Name' }
      }.to_json, headers: headers

      Remuneration.reindex(refresh: true)

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['attributes']['name']).to eq('New Name')
    end
  end

  describe 'DELETE /v1/users/remunerations/:id' do
    let(:remuneration) { create(:remuneration, account: account, user: user) }

    it 'soft deletes the remuneration' do
      delete "/v1/users/remunerations/#{remuneration.id}", headers: headers

      expect(response).to have_http_status(:ok)
      response_body = JSON.parse(response.body)
      expect(response_body['data']['attributes']['is_deleted']).to be true
    end
  end

  describe 'authorization' do
    let(:other_user) { create(:user, account: account) }
    let(:remuneration) { create(:remuneration, account: account, user: other_user) }

    it 'forbids update if not owner' do
      put "/v1/users/remunerations/#{remuneration.id}", params: {
        remuneration: { name: 'Changed' }
    }.to_json, headers: headers

      expect(response).to have_http_status(:forbidden)
    end

    it 'forbids delete if not owner' do
      delete "/v1/users/remunerations/#{remuneration.id}", headers: headers

      expect(response).to have_http_status(:forbidden)
    end
  end
end
