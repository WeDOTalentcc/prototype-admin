require 'rails_helper'

RSpec.describe 'V1::Users::Skills API', type: :request do
  let(:account) { create(:account) }
  let(:user) { create(:user, account: account) }
  let(:skill_category) { create(:skill_category, :programming) }

  describe 'GET /v1/users/skills' do
    let!(:skill1) { create(:skill, name: 'Ruby', account: account, skill_category: skill_category) }
    let!(:skill2) { create(:skill, name: 'Python', account: account, skill_category: skill_category) }
    let!(:skill3) { create(:skill, name: 'JavaScript', account: account) }
    let!(:deleted_skill) { create(:skill, :deleted, account: account) }

    before do
      Skill.reindex
    end

    it 'returns all active skills for the account' do
      get '/v1/users/skills', headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data'].size).to be >= 3
      skill_names = json['data'].map { |s| s['attributes']['name'] }
      expect(skill_names).to include('Ruby', 'Python', 'JavaScript')
    end

    it 'does not return deleted skills' do
      get '/v1/users/skills', headers: auth_headers(user)

      expect(json['data'].map { |s| s['attributes']['id'] }).not_to include(deleted_skill.id)
    end

    it 'includes skill category information' do
      get '/v1/users/skills', headers: auth_headers(user)

      ruby_skill = json['data'].find { |s| s['attributes']['name'] == 'Ruby' }
      expect(ruby_skill['attributes']).to include(
        'skill_category_id' => skill_category.id,
        'skill_category_name' => skill_category.name,
        'skill_category_icon' => skill_category.icon,
        'skill_category_color' => skill_category.color
      )
    end

    it 'supports filtering by skill_category_id' do
      get '/v1/users/skills',
          params: { where: { skill_category_id: skill_category.id } },
          headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      json['data'].each do |skill_data|
        expect(skill_data['attributes']['skill_category_id']).to eq(skill_category.id)
      end
    end

    it 'supports search by term' do
      get '/v1/users/skills', params: { term: 'Ruby' }, headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data'].any? { |s| s['attributes']['name'].include?('Ruby') }).to be_truthy
    end

    it 'returns unauthorized without token' do
      get '/v1/users/skills', headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'GET /v1/users/skills/:id' do
    it 'returns a specific skill with category info' do
      get "/v1/users/skills/#{skill.id}", headers: auth_headers(user)

      expect(response).to have_http_status(:ok)
      expect(json['data']['attributes']['id']).to eq(skill.id)
      expect(json['data']['attributes']['name']).to eq('Ruby')
      expect(json['data']['attributes']['skill_category_name']).to eq(skill_category.name)
    end

    it 'returns not found for non-existent skill' do
      get '/v1/users/skills/99999', headers: auth_headers(user)

      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /v1/users/skills' do
    context 'with skill_category' do
      let(:valid_params) do
        {
          skill: {
            name: 'Go',
            skill_category_id: skill_category.id
          }
        }
      end

      it 'creates a new skill with category' do
        expect {
          post '/v1/users/skills',
               params: valid_params.to_json,
               headers: auth_headers(user)
        }.to change(Skill, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('Go')
        expect(json['data']['attributes']['skill_category_id']).to eq(skill_category.id)
      end
    end

    context 'without skill_category' do
      let(:valid_params) do
        {
          skill: {
            name: 'Rust'
          }
        }
      end

      it 'creates a new skill without category' do
        expect {
          post '/v1/users/skills',
               params: valid_params.to_json,
               headers: auth_headers(user)
        }.to change(Skill, :count).by(1)

        expect(response).to have_http_status(:created)
        expect(json['data']['attributes']['name']).to eq('Rust')
        expect(json['data']['attributes']['skill_category_id']).to be_nil
      end
    end

    it 'returns existing skill if name already exists for account' do
      existing_skill = create(:skill, name: 'Elixir', account: account)

      post '/v1/users/skills',
           params: { skill: { name: 'Elixir' } }.to_json,
           headers: auth_headers(user)

      expect(response).to have_http_status(:created)
      expect(json['data']['attributes']['id']).to eq(existing_skill.id)
    end

    it 'returns unauthorized without token' do
      post '/v1/users/skills',
           params: { skill: { name: 'Java' } }.to_json,
           headers: no_auth_headers

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'PUT /v1/users/skills/:id' do
    let(:other_category) { create(:skill_category, :backend) }

    context 'when user owns the skill' do
      it 'updates the skill' do
        put "/v1/users/skills/#{skill.id}",
            params: { skill: { name: 'Ruby on Rails' } }.to_json,
            headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['name']).to eq('Ruby on Rails')
      end

      it 'can update skill_category' do
        put "/v1/users/skills/#{skill.id}",
            params: { skill: { skill_category_id: other_category.id } }.to_json,
            headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['skill_category_id']).to eq(other_category.id)
      end

      it 'can remove skill_category' do
        put "/v1/users/skills/#{skill.id}",
            params: { skill: { skill_category_id: nil } }.to_json,
            headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(json['data']['attributes']['skill_category_id']).to be_nil
      end
    end

    context 'when user does not own the skill' do
      let(:other_account) { create(:account) }
      let(:other_skill) { create(:skill, account: other_account) }

      it 'returns forbidden' do
        put "/v1/users/skills/#{other_skill.id}",
            params: { skill: { name: 'Updated' } }.to_json,
            headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /v1/users/skills/:id' do
    context 'when user owns the skill' do
      it 'soft deletes the skill' do
        delete "/v1/users/skills/#{skill.id}", headers: auth_headers(user)

        expect(response).to have_http_status(:ok)
        expect(skill.reload.is_deleted).to be_truthy
      end
    end

    context 'when user does not own the skill' do
      let(:other_account) { create(:account) }
      let(:other_skill) { create(:skill, account: other_account) }

      it 'returns forbidden' do
        delete "/v1/users/skills/#{other_skill.id}", headers: auth_headers(user)

        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
