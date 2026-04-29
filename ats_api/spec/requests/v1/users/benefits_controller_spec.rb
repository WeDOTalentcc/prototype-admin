require 'rails_helper'

RSpec.describe 'V1::Users::Benefits API', type: :request do
  let(:user) { create(:user) }

  describe 'GET /v1/users/benefits' do
    let!(:benefit) { create(:benefit, name: 'Gym Pass', category: 'lazer') }

    before do
      Benefit.reindex
    end

    it 'returns benefits when authenticated' do
      get '/v1/users/benefits', headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data'].first['attributes']['name']).to eq('Gym Pass')
    end

    it 'returns unauthorized without token' do
      get '/v1/users/benefits', headers: no_auth_headers
      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'GET /v1/users/benefits/:id' do
    let!(:benefit) { create(:benefit, name: 'Gym Pass', category: 'lazer') }

    it 'returns a benefit' do
      get "/v1/users/benefits/#{benefit.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(benefit.id)
    end

    it 'does not confuse ID route with collection routes' do
      get "/v1/users/benefits/#{benefit.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(benefit.id)
      expect(json['data']['attributes']['name']).to eq('Gym Pass')
    end
  end

  describe 'GET /v1/users/benefits/grouped_by_category' do
    let!(:health_benefit1) { create(:benefit, name: 'Plano de Saúde', category: 'saude') }
    let!(:health_benefit2) { create(:benefit, name: 'Plano Odontológico', category: 'saude') }
    let!(:food_benefit) { create(:benefit, name: 'Vale Refeição', category: 'alimentacao') }
    let!(:transport_benefit) { create(:benefit, name: 'Vale Transporte', category: 'transporte') }
    let!(:no_category_benefit) { create(:benefit, name: 'Sem Categoria', category: nil) }
    let!(:deleted_benefit) { create(:benefit, name: 'Deletado', category: 'saude', is_deleted: true) }

    it 'returns benefits grouped by category' do
      get '/v1/users/benefits/grouped_by_category', headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data']).to be_a(Hash)
    end

    it 'groups benefits correctly by category' do
      get '/v1/users/benefits/grouped_by_category', headers: auth_headers(user)

      data = json['data']

      expect(data['saude']).to be_an(Array)
      expect(data['saude'].length).to eq(2)
      expect(data['saude'].map { |b| b['name'] }).to contain_exactly('Plano de Saúde', 'Plano Odontológico')

      expect(data['alimentacao']).to be_an(Array)
      expect(data['alimentacao'].length).to eq(1)
      expect(data['alimentacao'].first['name']).to eq('Vale Refeição')

      expect(data['transporte']).to be_an(Array)
      expect(data['transporte'].length).to eq(1)
      expect(data['transporte'].first['name']).to eq('Vale Transporte')
    end

    it 'includes benefits with nil category' do
      get '/v1/users/benefits/grouped_by_category', headers: auth_headers(user)

      data = json['data']
      expect(data['']).to be_an(Array)
      expect(data[''].map { |b| b['name'] }).to include('Sem Categoria')
    end

    it 'excludes deleted benefits' do
      get '/v1/users/benefits/grouped_by_category', headers: auth_headers(user)

      data = json['data']
      all_benefit_names = data.values.flatten.map { |b| b['name'] }
      expect(all_benefit_names).not_to include('Deletado')
    end

    it 'returns category attribute for each benefit' do
      get '/v1/users/benefits/grouped_by_category', headers: auth_headers(user)

      data = json['data']
      saude_benefit = data['saude'].first

      expect(saude_benefit).to have_key('id')
      expect(saude_benefit).to have_key('name')
      expect(saude_benefit).to have_key('category')
      expect(saude_benefit['category']).to eq('saude')
    end

    it 'returns unauthorized without token' do
      get '/v1/users/benefits/grouped_by_category', headers: no_auth_headers
      expect(response).to have_http_status(:unauthorized)
    end

    it 'does not conflict with show action' do
      benefit_with_numeric_id = create(:benefit, name: 'Test Benefit', category: 'teste')

      get "/v1/users/benefits/#{benefit_with_numeric_id.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(benefit_with_numeric_id.id)

      get '/v1/users/benefits/grouped_by_category', headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']).to be_a(Hash)
    end
  end

  describe 'POST /v1/users/benefits' do
    it 'creates a benefit' do
      post '/v1/users/benefits', params: { benefit: { name: 'VR Alimentação', days_of_month: 22, types: [ 'meal' ] } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:created)
      expect(json['data']['attributes']['name']).to eq('VR Alimentação')
    end

    it 'creates a benefit with category' do
      post '/v1/users/benefits', params: { benefit: { name: 'Plano Dental', category: 'saude', days_of_month: 0, types: [] } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:created)
      expect(json['data']['attributes']['name']).to eq('Plano Dental')
      expect(json['data']['attributes']['category']).to eq('saude')
    end
  end

  describe 'PUT /v1/users/benefits/:id' do
    let!(:benefit) { create(:benefit, name: 'Gym Pass', category: 'fitness') }

    it 'updates a benefit' do
      put "/v1/users/benefits/#{benefit.id}", params: { benefit: { enable_value_editing: false } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['enable_value_editing']).to eq(false)
    end

    it 'updates benefit category' do
      put "/v1/users/benefits/#{benefit.id}", params: { benefit: { category: 'lazer' } }.to_json, headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['category']).to eq('lazer')
    end
  end

  describe 'DELETE /v1/users/benefits/:id' do
    let!(:benefit) { create(:benefit, name: 'Gym Pass', category: 'fitness') }

    it 'destroys a benefit' do
      delete "/v1/users/benefits/#{benefit.id}", headers: auth_headers(user)
      expect(response).to have_http_status(:ok)
    end
  end
end
