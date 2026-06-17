require 'rails_helper'

RSpec.describe 'V1::Users::BenefitRelationships API', type: :request do
  let(:user) { create(:user) }
  let(:benefit) { create(:benefit) }
  let(:job) { create(:job, user: user, account: user.account) }
  let!(:benefit_relationship) { create(:benefit_relationship, benefit: benefit, reference_type: 'Job', reference_id: job.id) }

  describe 'GET /v1/users/benefit_relationships' do
    before do
      BenefitRelationship.reindex
    end

    it 'returns benefit relationships when authenticated' do
      get '/v1/users/benefit_relationships', headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].first['attributes']['benefit_id']).to eq(benefit.id)
    end

    it 'returns unauthorized without token' do
      get '/v1/users/benefit_relationships', headers: no_auth_headers
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'GET /v1/users/benefit_relationships/:id' do
    it 'returns a benefit relationship' do
      get "/v1/users/benefit_relationships/#{benefit_relationship.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(benefit_relationship.id)
    end
  end

  describe 'POST /v1/users/benefit_relationships' do
    it 'creates a benefit relationship' do
      post '/v1/users/benefit_relationships', params: { benefit_relationship: { name: 'Custom Benefit', benefit_id: benefit.id, reference_type: 'Job', reference_id: job.id, days_of_month: 22 } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:created)
      expect(json['data']['attributes']['name']).to eq('Custom Benefit')
    end
  end

  describe 'PUT /v1/users/benefit_relationships/:id' do
    it 'updates a benefit relationship' do
      put "/v1/users/benefit_relationships/#{benefit_relationship.id}", params: { benefit_relationship: { is_company: true } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['is_company']).to eq(true)
    end
  end

  describe 'DELETE /v1/users/benefit_relationships/:id' do
    it 'destroys a benefit relationship' do
      delete "/v1/users/benefit_relationships/#{benefit_relationship.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
    end
  end
end
