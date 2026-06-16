require 'rails_helper'

RSpec.describe 'V1::Users::SkillCategories API', type: :request do
  let(:account) { create(:account) }
  let(:regular_user) { create(:user, account: account) }
  let(:admin_user) { create(:user, :admin, account: account) }
  let(:user) { regular_user }

  describe 'GET /v1/users/skill_categories' do
    let!(:category1) { create(:skill_category, name: 'Backend Frameworks') }
    let!(:category2) { create(:skill_category, name: 'Frontend Frameworks') }
    let!(:deleted_category) { create(:skill_category, :deleted) }

    before do
      SkillCategory.reindex
    end

    it 'returns all active skill categories' do
      get '/v1/users/skill_categories', headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data'].size).to be >= 3
      expect(json['data'].map { |c| c['attributes']['name'] }).to include('Backend Frameworks', 'Frontend Frameworks')
    end

    it 'does not return deleted categories' do
      get '/v1/users/skill_categories', headers: auth_headers(user)

      expect(json['data'].map { |c| c['attributes']['id'] }).not_to include(deleted_category.id)
    end

    it 'supports search by term' do
      get '/v1/users/skill_categories', params: { term: 'Backend' }, headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data'].any? { |c| c['attributes']['name'].include?('Backend') }).to be_truthy
    end

    it 'supports pagination' do
      get '/v1/users/skill_categories', params: { page: 1, per_page: 2 }, headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['meta']).to include('total', 'page', 'per_page', 'total_pages')
      expect(json['data'].size).to be <= 2
    end

    it 'returns unauthorized without token' do
      get '/v1/users/skill_categories', headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'GET /v1/users/skill_categories/:id' do
    let(:skill_category) { create(:skill_category, :programming) }

    it 'returns a specific skill category' do
      get "/v1/users/skill_categories/#{skill_category.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(skill_category.id)
      expect(json['data']['attributes']['name']).to eq(skill_category.name)
      expect(json['data']['attributes']).to include('icon', 'color', 'description')
    end

    it 'returns not found for non-existent category' do
      get '/v1/users/skill_categories/99999', headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end

    it 'returns unauthorized without token' do
      get "/v1/users/skill_categories/#{skill_category.id}", headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'POST /v1/users/skill_categories' do
    let(:valid_params) do
      {
        skill_category: {
          name: 'Cloud Computing',
          description: 'Cloud platforms and services',
          icon: '☁️',
          color: '#06B6D4'
        }
      }
    end

    context 'as admin user' do
      it 'creates a new skill category' do
        expect {
          post '/v1/users/skill_categories',
               params: valid_params.to_json,
               headers: auth_headers(admin_user)
        }.to change(SkillCategory, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('Cloud Computing')
        expect(json['data']['attributes']['icon']).to eq('☁️')
        expect(json['data']['attributes']['color']).to eq('#06B6D4')
      end

      it 'returns error with invalid params' do
        post '/v1/users/skill_categories',
             params: { skill_category: { name: '' } }.to_json,
             headers: auth_headers(admin_user)

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json['errors']).to be_present
      end
    end

    context 'as regular user' do
      it 'returns forbidden' do
        post '/v1/users/skill_categories',
             params: valid_params.to_json,
             headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
        expect(json['error']).to include('administradores')
      end
    end

    it 'returns unauthorized without token' do
      post '/v1/users/skill_categories',
           params: valid_params.to_json,
           headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'PUT /v1/users/skill_categories/:id' do
    let(:update_params) do
      {
        skill_category: {
          name: 'Updated Name',
          description: 'Updated description'
        }
      }
    end

    context 'as admin user' do
      it 'updates the skill category' do
        put "/v1/users/skill_categories/#{skill_category.id}",
            params: update_params.to_json,
            headers: auth_headers(admin_user)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name']).to eq('Updated Name')
        expect(json['data']['attributes']['description']).to eq('Updated description')
      end

      it 'returns error with invalid params' do
        put "/v1/users/skill_categories/#{skill_category.id}",
            params: { skill_category: { name: '' } }.to_json,
            headers: auth_headers(admin_user)

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'as regular user' do
      it 'returns forbidden' do
        put "/v1/users/skill_categories/#{skill_category.id}",
            params: update_params.to_json,
            headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /v1/users/skill_categories/:id' do
    let(:skill_category) { create(:skill_category, :programming) }

    context 'as admin user' do
      it 'soft deletes the skill category' do
        delete "/v1/users/skill_categories/#{skill_category.id}",
               headers: auth_headers(admin_user)

        expect(response).to have_http_status(:ok)
        expect(json['message']).to include('removida')
        expect(skill_category.reload.is_deleted).to be_truthy
      end
    end

    context 'as regular user' do
      it 'returns forbidden' do
        delete "/v1/users/skill_categories/#{skill_category.id}",
               headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
