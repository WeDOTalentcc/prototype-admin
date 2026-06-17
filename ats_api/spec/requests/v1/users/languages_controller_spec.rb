require 'rails_helper'

RSpec.describe 'V1::Users::Languages API', type: :request do
  let(:admin) { create(:user, :admin) }
  let(:user) { create(:user) }
  let!(:language) { create(:language, name: 'English', acronym: 'EN', name_ptbr: 'Inglês') }

  describe 'GET /v1/users/languages' do
    before do
      Language.reindex
    end
    context 'when authenticated (user)' do
      it 'returns languages' do
        get '/v1/users/languages', headers: auth_headers(user)
        expect(response).to have_http_status(:ok)
        expect(json['data'].first['attributes']['name']).to eq('English')
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/v1/users/languages', headers: no_auth_headers
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /v1/users/languages/:id' do
    it 'returns a language' do
      get "/v1/users/languages/#{language.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['name']).to eq('English')
    end
  end

  describe 'POST /v1/users/languages' do
    context 'as admin' do
      it 'creates a language' do
        post '/v1/users/languages', params: { language: { name: 'Spanish', acronym: 'ES', name_ptbr: 'Espanhol' } }.to_json, headers: auth_headers(admin)
        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['acronym']).to eq('ES')
      end
    end

    context 'as normal user' do
      it 'forbids creation' do
        post '/v1/users/languages', params: { language: { name: 'Spanish', acronym: 'ES', name_ptbr: 'Espanhol' } }.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden).or have_http_status(:unauthorized)
      end
    end
  end

  describe 'PUT /v1/users/languages/:id' do
    context 'as admin' do
      it 'updates a language' do
        put "/v1/users/languages/#{language.id}", params: { language: { name_ptbr: 'Inglês Atualizado' } }.to_json, headers: auth_headers(admin)
        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name_ptbr']).to eq('Inglês Atualizado')
      end
    end

    context 'as normal user' do
      it 'forbids update' do
        put "/v1/users/languages/#{language.id}", params: { language: { name_ptbr: 'Inglês Atualizado' } }.to_json, headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden).or have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /v1/users/languages/:id' do
    context 'as admin' do
      it 'destroys a language' do
        delete "/v1/users/languages/#{language.id}", headers: auth_headers(admin)
        expect(response).to have_http_status(:ok)
      end
    end

    context 'as normal user' do
      it 'forbids destroy' do
        delete "/v1/users/languages/#{language.id}", headers: auth_headers(user)
        expect(response).to have_http_status(:forbidden).or have_http_status(:unauthorized)
      end
    end
  end
end
