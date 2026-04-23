require 'rails_helper'

RSpec.describe 'V1::Users::LanguageRelationships API', type: :request do
  let(:user) { create(:user) }
  let(:language) { create(:language) }
  let!(:relationship) { create(:language_relationship, language: language) }

  describe 'GET /v1/users/language_relationships' do
    before do
      LanguageRelationship.reindex
    end

    it 'returns relationships when authenticated' do
      get '/v1/users/language_relationships', headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].first['attributes']['language_id']).to eq(language.id)
    end

    it 'returns unauthorized when no token' do
      get '/v1/users/language_relationships', headers: no_auth_headers
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'GET /v1/users/language_relationships/:id' do
    it 'returns a relationship' do
      get "/v1/users/language_relationships/#{relationship.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(relationship.id)
    end
  end

  describe 'POST /v1/users/language_relationships' do
    it 'creates a relationship' do
      job = create(:job, user: user, account: user.account)
      post '/v1/users/language_relationships', params: { language_relationship: { language_id: language.id, reference_type: 'Job', reference_id: job.id, min_value: 1, max_value: 5, priority: 2, level: 'fluente' } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:created)
      expect(json['data']['attributes']['priority']).to eq(2)
      expect(json['data']['attributes']['level']).to eq('fluente')
    end
  end

  describe 'PUT /v1/users/language_relationships/:id' do
    it 'updates a relationship' do
  put "/v1/users/language_relationships/#{relationship.id}", params: { language_relationship: { priority: 3, level: 'intermediario' } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['priority']).to eq(3)
  expect(json['data']['attributes']['level']).to eq('intermediario')
    end
  end

  describe 'DELETE /v1/users/language_relationships/:id' do
    it 'destroys a relationship' do
      delete "/v1/users/language_relationships/#{relationship.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
    end
  end
end
